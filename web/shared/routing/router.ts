/**
 * Timetable-aware multimodal router.
 *
 * This module is the single TypeScript routing implementation used by the Nuxt app and
 * by the Node CLI (`web/scripts/check-routing.ts`). It has no runtime dependencies and
 * is browser-safe; all imports from `./types` are type-only and are erased.
 *
 * ## Model (see MULTIMODAL_IMPLEMENTATION.md §4)
 *
 * - Earliest-arrival Dijkstra over `(node, lastRideMode)` labels. Nodes are the
 *   contract node ids: `island:<id>`, `stop:<id>`, `airport:<iata>`.
 * - Access and road edges are physical links and are traversable in both directions
 *   with a fixed duration. They do not change `lastRideMode`.
 * - A timetabled service can be boarded at any stop index `i` whose `departure` is at
 *   least `ready + boardMinutes`. A traveller who stays on board through intermediate
 *   stops pays nothing; a journey may alight at any later stop `j` at its scheduled
 *   `arrival`. Stop sequences, never route-level summaries, drive this.
 * - A frequency service (`frequency` kind, air or ferry) can be boarded at its
 *   `fromNode`; the first departure at or after `ready + buffer` is taken and the
 *   arrival is `departure + blockMinutes`. These legs are always `estimated`.
 * - `ready` is the label time (arrival + alight overhead already paid) plus:
 *   `transferPenaltyMinutes` when the boarded mode differs from the previous ride
 *   mode, and `additionalBoardPenaltyMinutes` for every boarding after the first.
 *   Those overheads are counted in `transferMinutes`, never in `waitMinutes`.
 * - `waitMinutes` for a leg is `departure - previousArrival - transferOverhead`;
 *   for the first transit leg this naturally contains the boarding buffer.
 * - Every journey total is built from the legs, so
 *   `access + wait + ride + transfer === arrival - departure === elapsed`.
 *
 * Destination = an island node that hosts at least one facility whose `categories`
 * includes the requested category id. An origin that already hosts one returns a
 * zero-minute journey (no legs).
 *
 * ## Transport scope (v2, MULTIMODAL_IMPLEMENTATION.md §10)
 *
 * `allowedModes` filters physical access edges and services: walk/road are `land`,
 * speedboat/ferry_transfer and every ferry/sea service are `sea`, air services are `air`.
 * `disabledRouteIds`/`disabledServiceIds` remove services. The selection is part of the
 * graph cache key. `includeEstimatedAir` remains as the legacy v1 switch (false = no air)
 * and is ignored when `allowedModes` is present. Frequency services with `mode: "sea"`
 * are routed exactly like ferries (ferry buffers) but reported as `sea` legs; transfer
 * penalties compare the coarse ride mode, so ferry and sea share one mode.
 */

import type {
  AccessibilityRequest,
  AccessibilityResult,
  AccessibilitySummary,
  AccessEdge,
  AccessMode,
  Confidence,
  Facility,
  FrequencyService,
  Island,
  Journey,
  JourneyPlan,
  OriginAccessStatus,
  JourneyLeg,
  JourneyRequest,
  MultimodalNetwork,
  NetworkSelection,
  OriginAccess,
  RoutingDefaults,
  Scenario,
  Service,
  ServiceConfidence,
  StopTime,
  TimetabledService,
  TravelMode,
} from './types'

/* -------------------------------------------------------------------------------------------------
 * Node ids (mirrors `NODE_PREFIX` helpers in types.ts, kept local so this module has no runtime
 * import; type-only imports are erased by both Node's type stripping and the bundler).
 * ---------------------------------------------------------------------------------------------- */

export const ISLAND_NODE_PREFIX = 'island:'
export const STOP_NODE_PREFIX = 'stop:'
export const AIRPORT_NODE_PREFIX = 'airport:'

export function toIslandNode(islandId: string): string {
  return `${ISLAND_NODE_PREFIX}${islandId}`
}

export function toStopNode(stopId: string): string {
  return `${STOP_NODE_PREFIX}${stopId}`
}

export function toAirportNode(iata: string): string {
  return `${AIRPORT_NODE_PREFIX}${iata}`
}

function islandIdFromNode(nodeId: string): string | null {
  return nodeId.startsWith(ISLAND_NODE_PREFIX) ? nodeId.slice(ISLAND_NODE_PREFIX.length) : null
}

function isAirportNode(nodeId: string): boolean {
  return nodeId.startsWith(AIRPORT_NODE_PREFIX)
}

const NEXT_DAY_MINUTES = 1440

/** Fallbacks used if `meta.routingDefaults` is missing or incomplete. */
const FALLBACK_ROUTING_DEFAULTS: RoutingDefaults = {
  ferryBoardMinutes: 15,
  ferryAlightMinutes: 2,
  airBoardMinutes: 45,
  airBoardMinutesMle: 60,
  airAlightMinutes: 15,
  transferPenaltyMinutes: 10,
  additionalBoardPenaltyMinutes: 5,
  maxJourneyMinutes: 1440,
}

const SUMMARY_THRESHOLDS = [60, 120, 240] as const

/** Coarse ride category used for transfer penalties: every sea service shares one mode. */
type RideMode = 'sea' | 'air'

/** Display/leg mode of one transit service. */
type TransitMode = 'ferry' | 'air' | 'sea'

const TRAVEL_MODES: readonly TravelMode[] = ['land', 'sea', 'air']

/** Access modes belong to the coarse contract scope selected by the user. */
const ACCESS_TRAVEL_MODE: Record<AccessMode, TravelMode> = {
  walk: 'land',
  road: 'land',
  speedboat: 'sea',
  ferry_transfer: 'sea',
}

function rideModeOf(mode: TransitMode): RideMode {
  return mode === 'air' ? 'air' : 'sea'
}

/* -------------------------------------------------------------------------------------------------
 * Public helper types
 * ---------------------------------------------------------------------------------------------- */

/** Re-export the shared plan result type (declared in types.ts). */
export type { JourneyPlan }

/** One addable route pattern, as found in the network's timetabled services. */
export interface RoutePattern {
  serviceId: string
  routeId: string
  routeCode: string
  firstDeparture: number
  stopCount: number
  firstStopName: string
  firstStopIslandId: string | null
  lastStopName: string
  lastStopIslandId: string | null
}

/* -------------------------------------------------------------------------------------------------
 * Routing graph (built once per network + option combination)
 * ---------------------------------------------------------------------------------------------- */

interface FixedNeighbour {
  to: string
  mode: AccessMode
  minutes: number
  confidence: Confidence
  basis?: string
  distanceKm?: number
}

interface BoardingOption {
  serviceId: string
  routeCode: string
  mode: TransitMode
  /** 0 for the reference day, 1440 for the repeated next-day copy. */
  shift: number
  /** Full, sequence-sorted stop list of the service (shared between options). */
  stops: StopTime[]
  index: number
}

interface FrequencyOption {
  service: FrequencyService
  departures: number[]
  /** Shifts that may be offered at the fromNode (0, and 1440 when allowNextDay is on). */
  shifts: number[]
}

interface RoutingGraph {
  defaults: RoutingDefaults
  allowNextDay: boolean
  fixed: Map<string, FixedNeighbour[]>
  boardsByStop: Map<string, BoardingOption[]>
  frequencyByNode: Map<string, FrequencyOption[]>
  nodeNames: Map<string, string>
  islandsById: Map<string, Island>
  /** category -> islandId -> facilities on that island for the category. */
  destinationFacilities: Map<string, Map<string, Facility[]>>
  /** Island nodes with at least one physical edge or a service leaving from the island node. */
  islandsWithOutgoingConnectivity: Set<string>
}

interface GraphOptions {
  allowedModes: TravelMode[]
  disabledRouteIds: string[]
  disabledServiceIds: string[]
  allowNextDay: boolean
}

interface ResolvedSelection {
  allowedModes: TravelMode[]
  disabledRouteIds: string[]
  disabledServiceIds: string[]
}

const graphCache = new WeakMap<MultimodalNetwork, Map<string, RoutingGraph>>()

function graphCacheKey(options: GraphOptions): string {
  const modes = options.allowedModes.slice().sort().join(',')
  const routes = options.disabledRouteIds.slice().sort().join(',')
  const services = options.disabledServiceIds.slice().sort().join(',')
  return `m:${modes}|r:${routes}|s:${services}|${options.allowNextDay ? 'nextday' : 'sameday'}`
}

/**
 * Resolve a request selection. `allowedModes` wins when present; otherwise the legacy
 * `includeEstimatedAir` switch removes air for v1 callers. Omitted means every mode.
 */
function resolveSelection(request: NetworkSelection & { includeEstimatedAir?: boolean }): ResolvedSelection {
  const explicit = Array.isArray(request.allowedModes)
  const allowedModes: TravelMode[] = explicit
    ? TRAVEL_MODES.filter((mode) => request.allowedModes!.includes(mode))
    : request.includeEstimatedAir === false
      ? ['land', 'sea']
      : ['land', 'sea', 'air']
  return {
    allowedModes,
    disabledRouteIds: (request.disabledRouteIds ?? []).filter((id) => typeof id === 'string' && id.length > 0),
    disabledServiceIds: (request.disabledServiceIds ?? []).filter((id) => typeof id === 'string' && id.length > 0),
  }
}

/**
 * A service is removed when its exact id is in `disabledServiceIds` (that wins), or when
 * its route id is in `disabledRouteIds`. For frequency services the route id defaults to
 * the service id, and a new-style `routeId` grouping is honoured as well.
 */
function isServiceDisabled(service: Service, disabledRouteIds: Set<string>, disabledServiceIds: Set<string>): boolean {
  if (disabledServiceIds.has(service.id)) return true
  if (isTimetabledService(service)) return disabledRouteIds.has(service.routeId)
  if (disabledRouteIds.has(service.id)) return true
  return service.routeId !== undefined && disabledRouteIds.has(service.routeId)
}

/* -------------------------------------------------------------------------------------------------
 * Defaults / small utilities
 * ---------------------------------------------------------------------------------------------- */

/** Merge `meta.routingDefaults` over the contract fallbacks, ignoring non-numeric values. */
export function getRoutingDefaults(network: MultimodalNetwork): RoutingDefaults {
  const merged: RoutingDefaults = { ...FALLBACK_ROUTING_DEFAULTS }
  const provided = network.meta?.routingDefaults
  if (!provided) return merged
  for (const key of Object.keys(merged) as Array<keyof RoutingDefaults>) {
    const value = provided[key]
    if (typeof value === 'number' && Number.isFinite(value)) merged[key] = value
  }
  return merged
}

function isTimetabledService(service: Service): service is TimetabledService {
  return service.kind === 'timetabled'
}

function sortedStops(service: TimetabledService): StopTime[] {
  return service.stops.slice().sort((a, b) => a.sequence - b.sequence)
}

function sortFacilities(facilities: Facility[]): Facility[] {
  return facilities.slice().sort((a, b) => (a.id < b.id ? -1 : a.id > b.id ? 1 : 0))
}

function boardBufferMinutes(mode: RideMode, node: string, defaults: RoutingDefaults): number {
  if (mode === 'air') {
    // Air: 60 minutes when leaving Velana International (MLE), 45 elsewhere.
    return node === toAirportNode('MLE') ? defaults.airBoardMinutesMle : defaults.airBoardMinutes
  }
  // Ferry and sea frequency services share the ferry boarding buffer.
  return defaults.ferryBoardMinutes
}

function alightMinutes(mode: RideMode, defaults: RoutingDefaults): number {
  // Ferry and sea frequency services share the ferry alighting buffer.
  return mode === 'air' ? defaults.airAlightMinutes : defaults.ferryAlightMinutes
}

/* -------------------------------------------------------------------------------------------------
 * Graph construction
 * ---------------------------------------------------------------------------------------------- */

function buildGraph(network: MultimodalNetwork, options: GraphOptions): RoutingGraph {
  const defaults = getRoutingDefaults(network)
  const allowedModes = new Set<TravelMode>(options.allowedModes)
  const disabledRouteIds = new Set(options.disabledRouteIds)
  const disabledServiceIds = new Set(options.disabledServiceIds)
  const nodeNames = new Map<string, string>()
  const islandsById = new Map<string, Island>()
  const islandsWithOutgoingConnectivity = new Set<string>()

  for (const island of network.islands) {
    islandsById.set(island.id, island)
    nodeNames.set(toIslandNode(island.id), island.name)
  }
  for (const stop of network.stops) {
    nodeNames.set(toStopNode(stop.id), stop.name)
  }
  for (const airport of network.airports) {
    nodeNames.set(toAirportNode(airport.iata), airport.name)
  }

  // Physical links: one recorded edge is traversable both ways.
  const fixed = new Map<string, FixedNeighbour[]>()
  const addFixed = (from: string, neighbour: FixedNeighbour): void => {
    const list = fixed.get(from)
    if (list) list.push(neighbour)
    else fixed.set(from, [neighbour])
  }
  for (const edge of network.accessEdges) {
    if (edge.from === edge.to) continue
    if (!allowedModes.has(ACCESS_TRAVEL_MODE[edge.mode])) continue
    const forward: FixedNeighbour = {
      to: edge.to,
      mode: edge.mode,
      minutes: edge.minutes,
      confidence: edge.confidence,
      basis: edge.basis,
      distanceKm: edge.distanceKm,
    }
    const backward: FixedNeighbour = { ...forward, to: edge.from }
    addFixed(edge.from, forward)
    addFixed(edge.to, backward)
    const fromIsland = islandIdFromNode(edge.from)
    const toIsland = islandIdFromNode(edge.to)
    if (fromIsland) islandsWithOutgoingConnectivity.add(toIslandNode(fromIsland))
    if (toIsland) islandsWithOutgoingConnectivity.add(toIslandNode(toIsland))
  }

  // Timetabled services are indexed per stop so a journey can start at any stop and end at
  // any later stop of the same trip (staying on board costs nothing).
  const boardsByStop = new Map<string, BoardingOption[]>()
  for (const service of network.services) {
    if (!isTimetabledService(service)) continue
    if (!allowedModes.has('sea')) continue
    if (isServiceDisabled(service, disabledRouteIds, disabledServiceIds)) continue
    const stops = sortedStops(service)
    if (stops.length < 2) continue
    const shifts = options.allowNextDay ? [0, NEXT_DAY_MINUTES] : [0]
    for (let index = 0; index < stops.length; index += 1) {
      const stop = stops[index]
      if (!stop) continue
      const node = toStopNode(stop.stopId)
      for (const shift of shifts) {
        const option: BoardingOption = {
          serviceId: service.id,
          routeCode: service.routeCode,
          mode: service.mode,
          shift,
          stops,
          index,
        }
        const list = boardsByStop.get(node)
        if (list) list.push(option)
        else boardsByStop.set(node, [option])
      }
    }
  }

  // Frequency services are indexed by their departure node. The air toggle removes air
  // services from routing entirely; published frequent ferries remain (they are still
  // estimated and therefore never reported as verified).
  const frequencyByNode = new Map<string, FrequencyOption[]>()
  for (const service of network.services) {
    if (service.kind !== 'frequency') continue
    const travelMode: TravelMode = service.mode === 'air' ? 'air' : 'sea'
    if (!allowedModes.has(travelMode)) continue
    if (isServiceDisabled(service, disabledRouteIds, disabledServiceIds)) continue
    const departures = service.departures.slice().sort((a, b) => a - b)
    const option: FrequencyOption = {
      service,
      departures,
      shifts: options.allowNextDay ? [0, NEXT_DAY_MINUTES] : [0],
    }
    const list = frequencyByNode.get(service.fromNode)
    if (list) list.push(option)
    else frequencyByNode.set(service.fromNode, [option])
    const fromIsland = islandIdFromNode(service.fromNode)
    if (fromIsland) islandsWithOutgoingConnectivity.add(toIslandNode(fromIsland))
  }

  // Facilities are island-level; a category destination set is every island hosting one.
  const destinationFacilities = new Map<string, Map<string, Facility[]>>()
  for (const facility of network.facilities) {
    for (const category of facility.categories) {
      let byIsland = destinationFacilities.get(category)
      if (!byIsland) {
        byIsland = new Map<string, Facility[]>()
        destinationFacilities.set(category, byIsland)
      }
      const existing = byIsland.get(facility.islandId)
      if (existing) existing.push(facility)
      else byIsland.set(facility.islandId, [facility])
    }
  }
  for (const [category, byIsland] of destinationFacilities) {
    const sorted = new Map<string, Facility[]>()
    for (const [islandId, facilities] of byIsland) sorted.set(islandId, sortFacilities(facilities))
    destinationFacilities.set(category, sorted)
  }

  return {
    defaults,
    allowNextDay: options.allowNextDay,
    fixed,
    boardsByStop,
    frequencyByNode,
    nodeNames,
    islandsById,
    destinationFacilities,
    islandsWithOutgoingConnectivity,
  }
}

function getGraph(network: MultimodalNetwork, options: GraphOptions): RoutingGraph {
  let perNetwork = graphCache.get(network)
  if (!perNetwork) {
    perNetwork = new Map<string, RoutingGraph>()
    graphCache.set(network, perNetwork)
  }
  const key = graphCacheKey(options)
  const cached = perNetwork.get(key)
  if (cached) return cached
  const graph = buildGraph(network, options)
  perNetwork.set(key, graph)
  return graph
}

/* -------------------------------------------------------------------------------------------------
 * Dijkstra
 * ---------------------------------------------------------------------------------------------- */

interface Label {
  key: string
  node: string
  lastRideMode: RideMode | null
  boardCount: number
  /** Earliest time the traveller is ready at this node (arrival + any alight overhead). */
  time: number
  usedNextDay: boolean
  prev: Label | null
  leg: JourneyLeg | null
  waitMinutes: number
  rideMinutes: number
  accessMinutes: number
  transferMinutes: number
}

interface HeapEntry {
  time: number
  sequence: number
  label: Label
}

class BinaryHeap<T> {
  private readonly items: T[] = []
  private readonly compareFn: (a: T, b: T) => number

  constructor(compareFn: (a: T, b: T) => number) {
    this.compareFn = compareFn
  }

  get size(): number {
    return this.items.length
  }

  push(item: T): void {
    this.items.push(item)
    let index = this.items.length - 1
    while (index > 0) {
      const parent = (index - 1) >> 1
      if (this.compareFn(this.items[index]!, this.items[parent]!) >= 0) break
      const swap = this.items[index]!
      this.items[index] = this.items[parent]!
      this.items[parent] = swap
      index = parent
    }
  }

  pop(): T | undefined {
    const items = this.items
    if (items.length === 0) return undefined
    const top = items[0]!
    const last = items.pop()!
    if (items.length > 0) {
      items[0] = last
      let index = 0
      for (;;) {
        const left = 2 * index + 1
        const right = left + 1
        let smallest = index
        if (left < items.length && this.compareFn(items[left]!, items[smallest]!) < 0) smallest = left
        if (right < items.length && this.compareFn(items[right]!, items[smallest]!) < 0) smallest = right
        if (smallest === index) break
        const swap = items[index]!
        items[index] = items[smallest]!
        items[smallest] = swap
        index = smallest
      }
    }
    return top
  }
}

function labelKey(node: string, lastRideMode: RideMode | null): string {
  return `${node}|${lastRideMode ?? ''}`
}

function boardingOverhead(label: Label, mode: RideMode, defaults: RoutingDefaults): number {
  let extra = label.boardCount > 0 ? defaults.additionalBoardPenaltyMinutes : 0
  if (label.lastRideMode !== null && label.lastRideMode !== mode) extra += defaults.transferPenaltyMinutes
  return extra
}

interface DestinationSearch {
  originNode: string
  originIslandId: string
  category: string
  departureMinute: number
  maxArrivalMinute: number
  /** When set, these islands are the destinations instead of the category's facilities. */
  targetIslands?: Set<string>
}

function findEarliestDestination(graph: RoutingGraph, search: DestinationSearch): Label | null {
  return searchDestinations(graph, search, 1)[0] ?? null
}

/**
 * Earliest-arrival labels for up to `limit` distinct destination islands, in arrival order.
 * The search keeps expanding past a found destination, so a later island reached through an
 * earlier one is still found.
 */
function searchDestinations(graph: RoutingGraph, search: DestinationSearch, limit: number): Label[] {
  const found: Label[] = []
  const foundIslands = new Set<string>()
  const destinationIslands: { has(islandId: string): boolean } | undefined =
    search.targetIslands ?? graph.destinationFacilities.get(search.category)
  const defaults = graph.defaults
  const startKey = labelKey(search.originNode, null)
  const start: Label = {
    key: startKey,
    node: search.originNode,
    lastRideMode: null,
    boardCount: 0,
    time: search.departureMinute,
    usedNextDay: false,
    prev: null,
    leg: null,
    waitMinutes: 0,
    rideMinutes: 0,
    accessMinutes: 0,
    transferMinutes: 0,
  }

  const labels = new Map<string, Label>([[startKey, start]])
  const heap = new BinaryHeap<HeapEntry>((a, b) => a.time - b.time || a.sequence - b.sequence)
  let sequence = 0
  heap.push({ time: start.time, sequence, label: start })

  const relax = (
    label: Label,
    time: number,
    node: string,
    lastRideMode: RideMode | null,
    leg: JourneyLeg,
    costs: { wait: number; ride: number; access: number; transfer: number },
    ridesNextDay: boolean,
  ): void => {
    if (time > search.maxArrivalMinute) return
    const key = labelKey(node, lastRideMode)
    const existing = labels.get(key)
    if (existing && existing.time <= time) return
    const next: Label = {
      key,
      node,
      lastRideMode,
      boardCount: label.boardCount,
      time,
      usedNextDay: label.usedNextDay || ridesNextDay,
      prev: label,
      leg,
      waitMinutes: label.waitMinutes + costs.wait,
      rideMinutes: label.rideMinutes + costs.ride,
      accessMinutes: label.accessMinutes + costs.access,
      transferMinutes: label.transferMinutes + costs.transfer,
    }
    labels.set(key, next)
    sequence += 1
    heap.push({ time, sequence, label: next })
  }

  while (heap.size > 0) {
    const entry = heap.pop()
    if (!entry) break
    const label = entry.label
    if (labels.get(label.key) !== label) continue
    if (label.time > search.maxArrivalMinute) break

    // Dijkstra pops labels in non-decreasing time, so the first destination island is the
    // earliest-arriving one. The origin cannot appear here (it is handled before the search).
    const nodeIslandId = islandIdFromNode(label.node)
    if (
      nodeIslandId &&
      nodeIslandId !== search.originIslandId &&
      destinationIslands?.has(nodeIslandId) &&
      !foundIslands.has(nodeIslandId)
    ) {
      foundIslands.add(nodeIslandId)
      found.push(label)
      if (found.length >= limit) return found
    }

    // 1) Physical access / road edges (undirected, fixed minutes).
    const neighbours = graph.fixed.get(label.node)
    if (neighbours) {
      for (const neighbour of neighbours) {
        const arrival = label.time + neighbour.minutes
        const leg: JourneyLeg = {
          kind: neighbour.mode === 'road' ? 'road' : 'access',
          mode: neighbour.mode,
          fromNode: label.node,
          toNode: neighbour.to,
          fromName: graph.nodeNames.get(label.node) ?? label.node,
          toName: graph.nodeNames.get(neighbour.to) ?? neighbour.to,
          departureMinute: label.time,
          arrivalMinute: arrival,
          waitMinutes: 0,
          rideMinutes: neighbour.minutes,
          distanceKm: neighbour.distanceKm,
          basis: neighbour.basis,
        }
        relax(
          label,
          arrival,
          neighbour.to,
          label.lastRideMode,
          leg,
          { wait: 0, ride: 0, access: neighbour.minutes, transfer: 0 },
          false,
        )
      }
    }

    // 2) Timetabled services boardable at this stop, alighting at any later stop.
    const boardings = graph.boardsByStop.get(label.node)
    if (boardings) {
      for (const option of boardings) {
        const boardStop = option.stops[option.index]
        if (!boardStop) continue
        const rideMode = rideModeOf(option.mode)
        const overhead = boardingOverhead(label, rideMode, defaults)
        const departure = boardStop.departure + option.shift
        const buffer = boardBufferMinutes(rideMode, label.node, defaults)
        if (departure < label.time + overhead + buffer) continue
        const wait = departure - label.time - overhead
        const alight = alightMinutes(rideMode, defaults)
        for (let index = option.index + 1; index < option.stops.length; index += 1) {
          const alightStop = option.stops[index]
          if (!alightStop) continue
          const arrival = alightStop.arrival + option.shift
          const ready = arrival + alight
          if (ready > search.maxArrivalMinute) continue
          const ride = arrival - departure
          const leg: JourneyLeg = {
            kind: option.mode,
            mode: option.mode,
            fromNode: label.node,
            toNode: toStopNode(alightStop.stopId),
            fromName: boardStop.name,
            toName: alightStop.name,
            departureMinute: departure,
            arrivalMinute: arrival,
            waitMinutes: wait,
            rideMinutes: ride,
            serviceId: option.serviceId,
            routeCode: option.routeCode,
            serviceConfidence: 'verified',
          }
          const next: Label = {
            key: labelKey(toStopNode(alightStop.stopId), rideMode),
            node: toStopNode(alightStop.stopId),
            lastRideMode: rideMode,
            boardCount: label.boardCount + 1,
            time: ready,
            usedNextDay: label.usedNextDay || option.shift > 0,
            prev: label,
            leg,
            waitMinutes: label.waitMinutes + wait,
            rideMinutes: label.rideMinutes + ride,
            accessMinutes: label.accessMinutes,
            transferMinutes: label.transferMinutes + alight + overhead,
          }
          const existing = labels.get(next.key)
          if (existing && existing.time <= ready) continue
          labels.set(next.key, next)
          sequence += 1
          heap.push({ time: ready, sequence, label: next })
        }
      }
    }

    // 3) Frequency services leaving this node (air / published frequent ferry).
    const frequencies = graph.frequencyByNode.get(label.node)
    if (frequencies) {
      for (const option of frequencies) {
        const service = option.service
        const mode: TransitMode = service.mode
        const rideMode = rideModeOf(mode)
        const overhead = boardingOverhead(label, rideMode, defaults)
        const ready = label.time + overhead
        const buffer = boardBufferMinutes(rideMode, label.node, defaults)
        let bestDeparture: number | null = null
        for (const shift of option.shifts) {
          for (const departure of option.departures) {
            const absolute = departure + shift
            if (absolute >= ready + buffer) {
              if (bestDeparture === null || absolute < bestDeparture) bestDeparture = absolute
              break
            }
          }
        }
        if (bestDeparture === null) continue
        const departure = bestDeparture
        const arrival = departure + service.blockMinutes
        const alight = alightMinutes(rideMode, defaults)
        const leg: JourneyLeg = {
          kind: service.mode === 'sea' ? 'sea' : service.mode,
          mode: service.mode,
          fromNode: label.node,
          toNode: service.toNode,
          fromName: graph.nodeNames.get(label.node) ?? label.node,
          toName: graph.nodeNames.get(service.toNode) ?? service.toNode,
          departureMinute: departure,
          arrivalMinute: arrival,
          waitMinutes: departure - label.time - overhead,
          rideMinutes: service.blockMinutes,
          serviceId: service.id,
          serviceConfidence: 'estimated',
        }
        const nextTime = arrival + alight
        if (nextTime > search.maxArrivalMinute) continue
        relax(
          label,
          nextTime,
          service.toNode,
          rideMode,
          leg,
          {
            wait: departure - label.time - overhead,
            ride: service.blockMinutes,
            access: 0,
            transfer: alight + overhead,
          },
          departure >= NEXT_DAY_MINUTES,
        )
      }
    }
  }

  return found
}

/* -------------------------------------------------------------------------------------------------
 * Journey assembly
 * ---------------------------------------------------------------------------------------------- */

function buildJourney(graph: RoutingGraph, request: { originIslandId: string; category: string; departureMinute: number }, label: Label, destinationIslandId: string): Journey {
  const legs: JourneyLeg[] = []
  let cursor: Label | null = label
  while (cursor && cursor.leg) {
    legs.push(cursor.leg)
    cursor = cursor.prev
  }
  legs.reverse()

  const originIsland = graph.islandsById.get(request.originIslandId)
  const destinationIsland = graph.islandsById.get(destinationIslandId)
  const destinationFacilities = graph.destinationFacilities.get(request.category)?.get(destinationIslandId) ?? []

  const transitLegs = legs.filter((leg) => leg.kind === 'ferry' || leg.kind === 'air' || leg.kind === 'sea')
  const serviceConfidence: ServiceConfidence =
    transitLegs.length === 0
      ? 'verified'
      : transitLegs.every((leg) => leg.serviceConfidence === 'verified')
        ? 'verified'
        : 'estimated'

  const modes: string[] = []
  for (const leg of legs) {
    if (!modes.includes(leg.mode)) modes.push(leg.mode)
  }

  return {
    originIslandId: request.originIslandId,
    originIslandName: originIsland?.name ?? request.originIslandId,
    destinationIslandId,
    destinationIslandName: destinationIsland?.name ?? destinationIslandId,
    destinationFacilityIds: destinationFacilities.map((facility) => facility.id),
    destinationFacilityNames: destinationFacilities.map((facility) => facility.name),
    category: request.category,
    departureMinute: request.departureMinute,
    arrivalMinute: label.time,
    elapsedMinutes: label.time - request.departureMinute,
    dayOffset: label.usedNextDay ? 1 : 0,
    waitMinutes: label.waitMinutes,
    rideMinutes: label.rideMinutes,
    accessMinutes: label.accessMinutes,
    transferMinutes: label.transferMinutes,
    transfers: Math.max(0, transitLegs.length - 1),
    modes,
    legs,
    serviceConfidence,
    usesEstimatedAir: transitLegs.some((leg) => leg.kind === 'air'),
  }
}

function zeroJourney(graph: RoutingGraph, request: { originIslandId: string; category: string; departureMinute: number }): Journey {
  const island = graph.islandsById.get(request.originIslandId)
  const facilities = graph.destinationFacilities.get(request.category)?.get(request.originIslandId) ?? []
  return {
    originIslandId: request.originIslandId,
    originIslandName: island?.name ?? request.originIslandId,
    destinationIslandId: request.originIslandId,
    destinationIslandName: island?.name ?? request.originIslandId,
    destinationFacilityIds: facilities.map((facility) => facility.id),
    destinationFacilityNames: facilities.map((facility) => facility.name),
    category: request.category,
    departureMinute: request.departureMinute,
    arrivalMinute: request.departureMinute,
    elapsedMinutes: 0,
    dayOffset: 0,
    waitMinutes: 0,
    rideMinutes: 0,
    accessMinutes: 0,
    transferMinutes: 0,
    transfers: 0,
    modes: [],
    legs: [],
    serviceConfidence: 'verified',
    usesEstimatedAir: false,
  }
}

/* -------------------------------------------------------------------------------------------------
 * Planning entry points
 * ---------------------------------------------------------------------------------------------- */

interface PlanningInput {
  graph: RoutingGraph
  originIslandId: string
  departureMinute: number
  category: string
  maxJourneyMinutes: number
}

function planWithGraph(input: PlanningInput): JourneyPlan {
  const { graph, originIslandId, departureMinute, category } = input
  const destinationIslands = graph.destinationFacilities.get(category)
  if (!destinationIslands || destinationIslands.size === 0) {
    return { status: 'no_destination', journey: null }
  }

  const request = { originIslandId, category, departureMinute }

  // Already at a listed facility: no travel required.
  const originFacilities = destinationIslands.get(originIslandId)
  if (originFacilities && originFacilities.length > 0) {
    return { status: 'reachable', journey: zeroJourney(graph, request) }
  }

  const originNode = toIslandNode(originIslandId)
  // `no_origin_access` means the island has no way out in the model at all: no physical
  // edge and no service leaving the island node. It is a coverage state, not a travel time.
  if (!graph.islandsWithOutgoingConnectivity.has(originNode)) {
    return { status: 'no_origin_access', journey: null }
  }

  const maxArrivalMinute = departureMinute + input.maxJourneyMinutes
  const label = findEarliestDestination(graph, {
    originNode,
    originIslandId,
    category,
    departureMinute,
    maxArrivalMinute,
  })
  if (!label) return { status: 'not_reachable', journey: null }
  const destinationIslandId = islandIdFromNode(label.node)
  if (!destinationIslandId) return { status: 'not_reachable', journey: null }
  return { status: 'reachable', journey: buildJourney(graph, request, label, destinationIslandId) }
}

/** Result of a nearest-destinations plan: the status plus up to `limit` journeys. */
export interface NearestPlan {
  status: OriginAccessStatus
  journeys: Journey[]
}

/**
 * Journeys to the `limit` earliest-reachable destination islands for one category, in
 * arrival order. When the origin itself hosts a facility, the 0-minute journey comes first.
 */
export function planNearestDestinations(
  network: MultimodalNetwork,
  request: JourneyRequest,
  limit = 3,
): NearestPlan {
  if (!Number.isFinite(request.departureMinute)) {
    throw new TypeError('departureMinute must be a finite number of minutes after midnight')
  }
  const defaults = getRoutingDefaults(network)
  const effectiveNetwork: MultimodalNetwork = request.scenario ? applyScenario(network, request.scenario) : network
  const selection = resolveSelection(request)
  const graph = getGraph(effectiveNetwork, { ...selection, allowNextDay: request.allowNextDay === true })
  const destinationIslands = graph.destinationFacilities.get(request.category)
  if (!destinationIslands || destinationIslands.size === 0) return { status: 'no_destination', journeys: [] }

  const base = {
    originIslandId: request.originIslandId,
    category: request.category,
    departureMinute: request.departureMinute,
  }
  const journeys: Journey[] = []
  if ((destinationIslands.get(request.originIslandId)?.length ?? 0) > 0) journeys.push(zeroJourney(graph, base))
  const remaining = limit - journeys.length
  const originNode = toIslandNode(request.originIslandId)
  if (remaining > 0 && graph.islandsWithOutgoingConnectivity.has(originNode)) {
    const labels = searchDestinations(
      graph,
      {
        originNode,
        originIslandId: request.originIslandId,
        category: request.category,
        departureMinute: request.departureMinute,
        maxArrivalMinute: request.departureMinute + (request.maxJourneyMinutes ?? defaults.maxJourneyMinutes),
      },
      remaining,
    )
    for (const label of labels) {
      const islandId = islandIdFromNode(label.node)
      if (islandId) journeys.push(buildJourney(graph, base, label, islandId))
    }
  }
  if (journeys.length > 0) return { status: 'reachable', journeys }
  return {
    status: graph.islandsWithOutgoingConnectivity.has(originNode) ? 'not_reachable' : 'no_origin_access',
    journeys: [],
  }
}

/**
 * Earliest journey from one island to another specific island (e.g. the trip home from a
 * facility). Returns `null` when no itinerary arrives within `maxJourneyMinutes`.
 */
export function planIslandToIsland(
  network: MultimodalNetwork,
  request: NetworkSelection & {
    fromIslandId: string
    toIslandId: string
    departureMinute: number
    allowNextDay?: boolean
    scenario?: Scenario
    maxJourneyMinutes?: number
  },
): Journey | null {
  const defaults = getRoutingDefaults(network)
  const effectiveNetwork: MultimodalNetwork = request.scenario ? applyScenario(network, request.scenario) : network
  const selection = resolveSelection(request)
  const graph = getGraph(effectiveNetwork, { ...selection, allowNextDay: request.allowNextDay === true })
  const base = { originIslandId: request.fromIslandId, category: `island:${request.toIslandId}`, departureMinute: request.departureMinute }
  if (request.fromIslandId === request.toIslandId) return zeroJourney(graph, base)
  const originNode = toIslandNode(request.fromIslandId)
  if (!graph.islandsWithOutgoingConnectivity.has(originNode)) return null
  const [label] = searchDestinations(
    graph,
    {
      originNode,
      originIslandId: request.fromIslandId,
      category: base.category,
      departureMinute: request.departureMinute,
      maxArrivalMinute: request.departureMinute + (request.maxJourneyMinutes ?? defaults.maxJourneyMinutes),
      targetIslands: new Set([request.toIslandId]),
    },
    1,
  )
  return label ? buildJourney(graph, base, label, request.toIslandId) : null
}

/** Plan a journey, or `null` when the category/origin cannot produce one. */
export function planJourney(network: MultimodalNetwork, request: JourneyRequest): Journey | null {
  return planJourneyWithStatus(network, request).journey
}

/**
 * Plan a journey and keep the origin-access status. This is an additive helper for the UI:
 * `Journey` (types.ts) has no status field, so `planJourney` alone cannot explain `null`.
 */
export function planJourneyWithStatus(network: MultimodalNetwork, request: JourneyRequest): JourneyPlan {
  if (!Number.isFinite(request.departureMinute)) {
    throw new TypeError('departureMinute must be a finite number of minutes after midnight')
  }
  const defaults = getRoutingDefaults(network)
  const effectiveNetwork: MultimodalNetwork = request.scenario ? applyScenario(network, request.scenario) : network
  const selection = resolveSelection(request)
  const graph = getGraph(effectiveNetwork, { ...selection, allowNextDay: request.allowNextDay === true })
  const maxJourneyMinutes = request.maxJourneyMinutes ?? defaults.maxJourneyMinutes
  return planWithGraph({
    graph,
    originIslandId: request.originIslandId,
    departureMinute: request.departureMinute,
    category: request.category,
    maxJourneyMinutes,
  })
}

/**
 * National accessibility for one category and departure time.
 *
 * Population totals come from `islands[].population` for `isOrigin` islands — never from
 * `meta.population`, which is context only.
 */
export function computeAccessibility(network: MultimodalNetwork, request: AccessibilityRequest): AccessibilityResult {
  if (!Number.isFinite(request.departureMinute)) {
    throw new TypeError('departureMinute must be a finite number of minutes after midnight')
  }
  const defaults = getRoutingDefaults(network)
  const maxJourneyMinutes = request.maxJourneyMinutes ?? defaults.maxJourneyMinutes
  const effectiveNetwork: MultimodalNetwork = request.scenario ? applyScenario(network, request.scenario) : network
  const selection = resolveSelection(request)
  const graph = getGraph(effectiveNetwork, { ...selection, allowNextDay: request.allowNextDay === true })

  const origins = network.islands.filter((island) => island.isOrigin)
  const perOrigin: Record<string, OriginAccess> = {}

  let populationTotal = 0
  let populationReachable = 0
  let within60 = 0
  let within120 = 0
  let within240 = 0
  let unreachablePopulation = 0
  let noOriginAccessPopulation = 0
  let reachableVerifiedPopulation = 0
  let reachableEstimatedPopulation = 0
  let originsReachable = 0
  let originsUnreachable = 0
  let originsNoAccess = 0
  let originsNoDestination = 0
  let noDestinationPopulation = 0

  for (const island of origins) {
    const population = Number.isFinite(island.population) ? island.population : 0
    populationTotal += population
    const plan = planWithGraph({
      graph,
      originIslandId: island.id,
      departureMinute: request.departureMinute,
      category: request.category,
      maxJourneyMinutes,
    })
    perOrigin[island.id] = { originIslandId: island.id, category: request.category, status: plan.status, journey: plan.journey }

    if (plan.status === 'reachable' && plan.journey) {
      originsReachable += 1
      populationReachable += population
      const elapsed = plan.journey.elapsedMinutes
      const thresholds = SUMMARY_THRESHOLDS
      if (elapsed <= thresholds[0]) within60 += population
      if (elapsed <= thresholds[1]) within120 += population
      if (elapsed <= thresholds[2]) within240 += population
      if (plan.journey.serviceConfidence === 'verified') reachableVerifiedPopulation += population
      else reachableEstimatedPopulation += population
    } else if (plan.status === 'not_reachable') {
      originsUnreachable += 1
      unreachablePopulation += population
    } else if (plan.status === 'no_origin_access') {
      originsNoAccess += 1
      noOriginAccessPopulation += population
    } else if (plan.status === 'no_destination') {
      originsNoDestination += 1
      noDestinationPopulation += population
    }
  }

  const summary: AccessibilitySummary = {
    category: request.category,
    populationTotal,
    populationReachable,
    within60,
    within120,
    within240,
    unreachablePopulation,
    noOriginAccessPopulation,
    noDestinationPopulation,
    coverage: populationTotal > 0 ? populationReachable / populationTotal : 0,
    reachableVerifiedPopulation,
    reachableEstimatedPopulation,
    originsReachable,
    originsUnreachable,
    originsNoAccess,
    originsNoDestination,
  }

  return { perOrigin, summary }
}

/* -------------------------------------------------------------------------------------------------
 * Scenarios
 * ---------------------------------------------------------------------------------------------- */

function cloneMeta(network: MultimodalNetwork): MultimodalNetwork['meta'] {
  const meta = network.meta
  return {
    ...meta,
    population: { ...meta.population },
    assumptions: meta.assumptions.map((assumption) => ({ ...assumption })),
    counts: { ...meta.counts },
    routingDefaults: { ...meta.routingDefaults },
    excludedAirRoutes: meta.excludedAirRoutes?.map((route) => ({ ...route })),
    coverageNotes: meta.coverageNotes?.slice(),
  }
}

function cloneTimetabled(service: TimetabledService, delayMinutes: number): TimetabledService {
  return {
    ...service,
    stops: service.stops.map((stop) => ({
      ...stop,
      arrival: stop.arrival + delayMinutes,
      departure: stop.departure + delayMinutes,
    })),
  }
}

function cloneFrequency(service: FrequencyService, delayMinutes: number): FrequencyService {
  return {
    ...service,
    operatingWindow: { ...service.operatingWindow },
    departures: service.departures.map((departure) => departure + delayMinutes),
  }
}

function cloneService(service: Service, delayMinutes: number): Service {
  if (service.kind === 'timetabled') return cloneTimetabled(service, delayMinutes)
  return cloneFrequency(service, delayMinutes)
}

function cloneAccessEdge(edge: AccessEdge): AccessEdge {
  return { ...edge }
}

function cloneFacility(facility: Facility): Facility {
  return {
    ...facility,
    categories: facility.categories.slice(),
    serviceCategories: facility.serviceCategories?.slice(),
    serviceEvidence: facility.serviceEvidence?.map((row) => ({ ...row })),
  }
}

/**
 * Apply a user scenario to a copy of the network. The input is never mutated.
 *
 * - `cancelledServiceIds` removes services (including added ones with the same id).
 * - `delayMinutesByServiceId` shifts every recorded time of the named base service.
 * - `addedTrips`, `addedServices`, `addedAccessEdges` and `addedFacilities` are appended
 *   as clones; the base arrays and objects are never mutated. Added access edges are
 *   traversable both ways, exactly like a source edge.
 */
export function applyScenario(network: MultimodalNetwork, scenario: Scenario): MultimodalNetwork {
  const cancelled = new Set(scenario.cancelledServiceIds ?? [])
  const delays = scenario.delayMinutesByServiceId ?? {}
  const services: Service[] = []
  for (const service of network.services) {
    if (cancelled.has(service.id)) continue
    services.push(cloneService(service, delays[service.id] ?? 0))
  }
  for (const trip of scenario.addedTrips ?? []) {
    if (cancelled.has(trip.id)) continue
    services.push(cloneTimetabled(trip, 0))
  }
  for (const service of scenario.addedServices ?? []) {
    if (cancelled.has(service.id)) continue
    services.push(cloneService(service, 0))
  }
  return {
    meta: cloneMeta(network),
    islands: network.islands.map((island) => ({ ...island })),
    stops: network.stops.map((stop) => ({ ...stop })),
    airports: network.airports.map((airport) => ({ ...airport })),
    accessEdges: [
      ...network.accessEdges.map(cloneAccessEdge),
      ...(scenario.addedAccessEdges ?? []).map(cloneAccessEdge),
    ],
    services,
    facilities: [
      ...network.facilities.map(cloneFacility),
      ...(scenario.addedFacilities ?? []).map(cloneFacility),
    ],
    categories: network.categories.map((category) => ({ ...category })),
  }
}

/* -------------------------------------------------------------------------------------------------
 * Route patterns (scenario "add a morning trip")
 * ---------------------------------------------------------------------------------------------- */

function firstStopOf(service: TimetabledService): StopTime | null {
  const stops = sortedStops(service)
  return stops[0] ?? null
}

/** List addable route patterns, ordered by route code then first departure. */
export function listRoutePatterns(network: MultimodalNetwork): RoutePattern[] {
  const stopIsland = new Map(network.stops.map((stop) => [stop.id, stop.islandId]))
  const patterns: RoutePattern[] = []
  for (const service of network.services) {
    if (!isTimetabledService(service)) continue
    const stops = sortedStops(service)
    const first = stops[0]
    const last = stops[stops.length - 1]
    if (!first || !last) continue
    patterns.push({
      serviceId: service.id,
      routeId: service.routeId,
      routeCode: service.routeCode,
      firstDeparture: first.departure,
      stopCount: stops.length,
      firstStopName: first.name,
      firstStopIslandId: stopIsland.get(first.stopId) ?? null,
      lastStopName: last.name,
      lastStopIslandId: stopIsland.get(last.stopId) ?? null,
    })
  }
  return patterns.sort((a, b) => a.routeCode.localeCompare(b.routeCode) || a.firstDeparture - b.firstDeparture || a.serviceId.localeCompare(b.serviceId))
}

function findPattern(network: MultimodalNetwork, routeId: string): TimetabledService {
  const timetabled = network.services.filter(isTimetabledService)
  // A full service id also selects one exact pattern (useful when a route id covers both
  // directions); otherwise the earliest first departure of the route is the pattern.
  const byServiceId = timetabled.find((service) => service.id === routeId)
  if (byServiceId) return byServiceId
  const matches = timetabled
    .filter((service) => service.routeId === routeId)
    .slice()
    .sort((a, b) => {
      const aFirst = firstStopOf(a)
      const bFirst = firstStopOf(b)
      const aDeparture = aFirst ? aFirst.departure : Number.POSITIVE_INFINITY
      const bDeparture = bFirst ? bFirst.departure : Number.POSITIVE_INFINITY
      return aDeparture - bDeparture || a.id.localeCompare(b.id)
    })
  const pattern = matches[0]
  if (!pattern) throw new Error(`createServiceFromPattern: no timetabled service with routeId "${routeId}"`)
  return pattern
}

/**
 * Shift an existing route pattern so its first departure equals `newFirstDepartureMinute`.
 * Leg durations (and every intermediate dwell) are preserved by shifting all stop times by
 * the same delta. The returned service is a new object; the network is not mutated.
 *
 * `routeId` may be a route id (the earliest first departure of that route is used) or an
 * exact service id (unambiguous when a route covers both directions).
 */
export function createServiceFromPattern(network: MultimodalNetwork, routeId: string, newFirstDepartureMinute: number, id?: string): TimetabledService {
  if (!Number.isFinite(newFirstDepartureMinute)) {
    throw new TypeError('newFirstDepartureMinute must be a finite number of minutes after midnight')
  }
  const pattern = findPattern(network, routeId)
  const stops = sortedStops(pattern)
  const first = stops[0]
  if (!first) throw new Error(`createServiceFromPattern: service "${pattern.id}" has no stops`)
  const delta = newFirstDepartureMinute - first.departure
  return {
    ...pattern,
    id: id ?? `${pattern.id}:added:${newFirstDepartureMinute}`,
    stops: stops.map((stop) => ({
      ...stop,
      arrival: stop.arrival + delta,
      departure: stop.departure + delta,
    })),
  }
}
