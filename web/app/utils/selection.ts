/**
 * Transport-scope helpers for the network selection controls.
 *
 * The prepared network is not the same thing as the user's selected network:
 * unchecking a mode or a route removes modelled supply, but it does not erase
 * the physical infrastructure recorded in the dataset. The UI keeps those two
 * ideas separate and labels filtered-out islands "not selected", never "no
 * access".
 */
import type {
  FrequencyService,
  MultimodalNetwork,
  Service,
  TimetabledService,
  TravelMode,
} from '../../shared/routing/types'

export type NetworkPreset = 'multimodal' | 'land_sea' | 'land_only' | 'custom'

export interface ModeFlags {
  land: boolean
  sea: boolean
  air: boolean
}

export const PRESET_FLAGS: Record<Exclude<NetworkPreset, 'custom'>, ModeFlags> = {
  multimodal: { land: true, sea: true, air: true },
  land_sea: { land: true, sea: true, air: false },
  land_only: { land: true, sea: false, air: false },
}

export const PRESET_OPTIONS: ReadonlyArray<{
  key: Exclude<NetworkPreset, 'custom'>
  label: string
  shortLabel: string
  description: string
}> = [
  {
    key: 'multimodal',
    label: 'Multimodal',
    shortLabel: 'All modes',
    description: 'Walk and road access, ferries and sea links, and estimated air services.',
  },
  {
    key: 'land_sea',
    label: 'Land + sea',
    shortLabel: 'No air',
    description: 'Walk, road, ferry and sea links only. Estimated domestic air is excluded.',
  },
  {
    key: 'land_only',
    label: 'Land only',
    shortLabel: 'Land only',
    description: 'Walk and road access only. Islands without a land route show as not selected.',
  },
]

export const MODE_OPTIONS: ReadonlyArray<{
  key: keyof ModeFlags
  label: string
  description: string
}> = [
  {
    key: 'land',
    label: 'Land',
    description: 'Walk and road access edges between an island, its stop or its airport.',
  },
  {
    key: 'sea',
    label: 'Sea',
    description: 'Timetabled ferries, estimated ferry frequencies and speedboat access edges.',
  },
  {
    key: 'air',
    label: 'Air',
    description: 'Estimated domestic air services (frequency model, not a published timetable).',
  },
]

export interface RouteCatalogEntry {
  /** Stable checklist id: ferry routeId, or a sorted airport-pair key for air. */
  key: string
  kind: 'ferry' | 'air'
  label: string
  fromName: string
  toName: string
  routeId: string
  serviceIds: string[]
  searchText: string
}

export interface RouteCatalog {
  ferries: RouteCatalogEntry[]
  air: RouteCatalogEntry[]
}

function islandName(network: MultimodalNetwork, islandId: string | null): string {
  if (!islandId) return 'Unknown island'
  return network.islands.find((island) => island.id === islandId)?.name ?? islandId
}

function airportPairKey(service: FrequencyService): string {
  const from = service.fromAirport ?? service.fromNode.replace(/^airport:/, '')
  const to = service.toAirport ?? service.toNode.replace(/^airport:/, '')
  return [from, to].sort().join('-')
}

function serviceSearchText(entry: Omit<RouteCatalogEntry, 'searchText'>): string {
  return `${entry.label} ${entry.fromName} ${entry.toName} ${entry.key}`.toLowerCase()
}

/**
 * Groups services into human-scale routes for the checklist: 49 ferry routes and
 * 31 undirected air pairs on the published network. Both directions of an air
 * pair are disabled together so the checklist cannot create a one-way artefact.
 */
export function buildRouteCatalog(network: MultimodalNetwork | null): RouteCatalog {
  const ferries: RouteCatalogEntry[] = []
  const air: RouteCatalogEntry[] = []
  if (!network) return { ferries, air }

  const ferryByRoute = new Map<string, RouteCatalogEntry>()
  const airByPair = new Map<string, RouteCatalogEntry>()

  for (const service of network.services) {
    if (service.kind === 'timetabled') {
      const first = service.stops[0]
      const last = service.stops[service.stops.length - 1]
      const entry: RouteCatalogEntry = {
        key: service.routeId,
        kind: 'ferry',
        label: `${service.routeCode || service.routeId} · ${first?.name ?? 'Unknown'} → ${last?.name ?? 'Unknown'}`,
        fromName: first?.name ?? 'Unknown',
        toName: last?.name ?? 'Unknown',
        routeId: service.routeId,
        serviceIds: [service.id],
        searchText: '',
      }
      entry.searchText = serviceSearchText(entry)
      const existing = ferryByRoute.get(entry.key)
      if (existing) {
        existing.serviceIds.push(service.id)
      } else {
        ferryByRoute.set(entry.key, entry)
      }
      continue
    }

    if (service.mode !== 'air') continue
    const key = service.routeId ?? airportPairKey(service)
    const fromName = islandName(
      network,
      network.airports.find((airport) => airport.iata === service.fromAirport)?.islandId ??
        null,
    )
    const toName = islandName(
      network,
      network.airports.find((airport) => airport.iata === service.toAirport)?.islandId ?? null,
    )
    const entry: RouteCatalogEntry = {
      key,
      kind: 'air',
      label: `${service.fromAirport ?? '?'} ↔ ${service.toAirport ?? '?'} · ${fromName} ↔ ${toName}`,
      fromName,
      toName,
      routeId: key,
      serviceIds: [service.id],
      searchText: '',
    }
    entry.searchText = serviceSearchText(entry)
    const existing = airByPair.get(key)
    if (existing) {
      existing.serviceIds.push(service.id)
    } else {
      airByPair.set(key, entry)
    }
  }

  ferries.push(
    ...[...ferryByRoute.values()].sort((a, b) => a.label.localeCompare(b.label)),
  )
  air.push(
    ...[...airByPair.values()].sort((a, b) => a.label.localeCompare(b.label)),
  )
  return { ferries, air }
}

/** Islands with at least one outgoing physical access edge in the prepared network. */
export function islandsWithInfrastructure(network: MultimodalNetwork | null): ReadonlySet<string> {
  const result = new Set<string>()
  if (!network) return result
  for (const edge of network.accessEdges) {
    if (edge.from.startsWith('island:')) result.add(edge.from.slice('island:'.length))
  }
  return result
}

/** Timetabled service ids grouped by route, for map filtering. */
export function serviceRouteLookup(network: MultimodalNetwork | null): Map<string, string> {
  const lookup = new Map<string, string>()
  if (!network) return lookup
  for (const service of network.services) {
    lookup.set(service.id, service.kind === 'timetabled' ? service.routeId : (service.routeId ?? service.id))
  }
  return lookup
}

export function isFrequencyService(service: Service | undefined): service is FrequencyService {
  return service?.kind === 'frequency'
}

export function isTimetabledService(
  service: Service | undefined,
): service is TimetabledService {
  return service?.kind === 'timetabled'
}

/** Explicit mode list for requests; always supplied so the router never has to guess. */
export function allowedModesFor(flags: ModeFlags): TravelMode[] {
  const modes: TravelMode[] = []
  if (flags.land) modes.push('land')
  if (flags.sea) modes.push('sea')
  if (flags.air) modes.push('air')
  return modes
}
