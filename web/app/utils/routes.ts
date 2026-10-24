/**
 * Geometry/label derivation for services, airports and facilities.
 *
 * Everything here is a straight read of the prepared network: no routing and no
 * invented coordinates. Islands without coordinates simply do not produce markers.
 */
import type {
  Airport,
  FrequencyService,
  MultimodalNetwork,
  TimetabledService,
} from '../../shared/routing/types'
import type { LonLat } from './geo'

/**
 * Contract node prefixes, duplicated locally as string constants so the browser
 * bundle does not take a runtime dependency on the type-only `shared/routing/types.ts`
 * module. The values must match `NODE_PREFIX` in that contract file.
 */
const NODE_PREFIX = {
  island: 'island:',
  stop: 'stop:',
  airport: 'airport:',
} as const

export interface RoutePath {
  serviceId: string
  /** Timetabled routeId, or the service's grouping id for frequency services. */
  routeId: string
  label: string
  mode: 'ferry' | 'air' | 'sea'
  /** `verified` for timetabled ferries, `estimated` for frequency-only services. */
  confidence: 'verified' | 'estimated'
  dashed: boolean
  points: LonLat[]
  fromName: string
  toName: string
}

export interface FacilityPoint {
  islandId: string
  islandName: string
  lon: number
  lat: number
  count: number
  names: string[]
}

export interface AirportPoint {
  iata: string
  name: string
  islandName: string
  lon: number
  lat: number
}

function findIsland(network: MultimodalNetwork, nodeId: string) {
  if (!nodeId.startsWith(NODE_PREFIX.island)) return undefined
  const id = nodeId.slice(NODE_PREFIX.island.length)
  return network.islands.find((island) => island.id === id)
}

function findStop(network: MultimodalNetwork, nodeId: string) {
  if (!nodeId.startsWith(NODE_PREFIX.stop)) return undefined
  const id = nodeId.slice(NODE_PREFIX.stop.length)
  return network.stops.find((stop) => stop.id === id)
}

function findAirport(network: MultimodalNetwork, nodeId: string): Airport | undefined {
  if (!nodeId.startsWith(NODE_PREFIX.airport)) return undefined
  const iata = nodeId.slice(NODE_PREFIX.airport.length)
  return network.airports.find((airport) => airport.iata === iata)
}

/** Lon/lat for any router node id, or null when the node has no coordinates. */
export function nodeCoordinate(network: MultimodalNetwork, nodeId: string): LonLat | null {
  const island = findIsland(network, nodeId)
  if (island) return [island.lon, island.lat]
  const stop = findStop(network, nodeId)
  if (stop) return [stop.lon, stop.lat]
  const airport = findAirport(network, nodeId)
  if (airport) return [airport.lon, airport.lat]
  return null
}

/** Human label for any router node id. */
export function nodeLabel(network: MultimodalNetwork, nodeId: string): string {
  const island = findIsland(network, nodeId)
  if (island) return island.name
  const stop = findStop(network, nodeId)
  if (stop) return stop.name
  const airport = findAirport(network, nodeId)
  if (airport) return `${airport.iata} · ${airport.name}`
  return nodeId
}

function isLonLat(point: LonLat | null): point is LonLat {
  return point !== null
}

function frequencyPath(network: MultimodalNetwork, service: FrequencyService): RoutePath | null {
  const from = nodeCoordinate(network, service.fromNode)
  const to = nodeCoordinate(network, service.toNode)
  if (!from || !to) return null
  const fromName = nodeLabel(network, service.fromNode)
  const toName = nodeLabel(network, service.toNode)
  const prefix =
    service.mode === 'air'
      ? (service.airline ?? 'Air service')
      : service.mode === 'sea'
        ? 'Sea'
        : 'Ferry'
  return {
    serviceId: service.id,
    routeId: service.routeId ?? service.id,
    label: `${prefix} · ${fromName} → ${toName}`,
    mode: service.mode,
    confidence: 'estimated',
    dashed: true,
    points: [from, to],
    fromName,
    toName,
  }
}

/** All service paths with at least two resolvable points. */
export function buildRoutePaths(network: MultimodalNetwork): RoutePath[] {
  const stopCoordinates = new Map(network.stops.map((stop) => [stop.id, [stop.lon, stop.lat] as LonLat]))
  const paths: RoutePath[] = []
  for (const service of network.services) {
    if (service.kind === 'timetabled') {
      const points = service.stops
        .map((stop) => stopCoordinates.get(stop.stopId) ?? null)
        .filter(isLonLat)
      if (points.length < 2) continue
      const fromName = service.stops[0]?.name ?? 'Unknown'
      const toName = service.stops[service.stops.length - 1]?.name ?? 'Unknown'
      paths.push({
        serviceId: service.id,
        routeId: service.routeId,
        label: `${service.routeCode || service.routeId} · ${fromName} → ${toName}`,
        mode: 'ferry',
        confidence: 'verified',
        dashed: false,
        points,
        fromName,
        toName,
      })
    } else {
      const path = frequencyPath(network, service)
      if (path) paths.push(path)
    }
  }
  return paths
}

/** Airports with resolved island context, for markers. */
export function buildAirportPoints(network: MultimodalNetwork): AirportPoint[] {
  const islands = new Map(network.islands.map((island) => [island.id, island]))
  return network.airports.map((airport) => ({
    iata: airport.iata,
    name: airport.name,
    islandName: islands.get(airport.islandId)?.name ?? airport.islandId,
    lon: airport.lon,
    lat: airport.lat,
  }))
}

/** Facilities of one category, grouped by island (island-level precision is preserved). */
export function buildFacilityPoints(
  network: MultimodalNetwork,
  categoryId: string | null,
): FacilityPoint[] {
  if (!categoryId) return []
  const islands = new Map(network.islands.map((island) => [island.id, island]))
  const grouped = new Map<string, FacilityPoint>()
  for (const facility of network.facilities) {
    if (!facility.categories.includes(categoryId)) continue
    const island = islands.get(facility.islandId)
    if (!island) continue
    const existing = grouped.get(facility.islandId)
    if (existing) {
      existing.count += 1
      existing.names.push(facility.name)
    } else {
      grouped.set(facility.islandId, {
        islandId: facility.islandId,
        islandName: island.name,
        lon: island.lon,
        lat: island.lat,
        count: 1,
        names: [facility.name],
      })
    }
  }
  return [...grouped.values()].sort((a, b) => b.count - a.count || a.islandName.localeCompare(b.islandName))
}

/** Distinct route patterns (route ids), used by the "add morning trip" scenario control. */
export interface RoutePatternOption {
  routeId: string
  label: string
  serviceIds: string[]
}

export function buildRoutePatterns(network: MultimodalNetwork): RoutePatternOption[] {
  const byRoute = new Map<string, RoutePatternOption>()
  for (const service of network.services) {
    if (service.kind !== 'timetabled') continue
    const routeId = service.routeId
    const existing = byRoute.get(routeId)
    if (existing) {
      existing.serviceIds.push(service.id)
    } else {
      const first = service.stops[0]?.name ?? 'Unknown'
      const last = service.stops[service.stops.length - 1]?.name ?? 'Unknown'
      byRoute.set(routeId, {
        routeId,
        label: `${service.routeCode || routeId} · ${first} → ${last}`,
        serviceIds: [service.id],
      })
    }
  }
  return [...byRoute.values()].sort((a, b) => a.label.localeCompare(b.label))
}

/** Service options for cancel/delay scenario controls. */
export interface ServiceOption {
  id: string
  label: string
  confidence: 'verified' | 'estimated'
}

export function buildServiceOptions(network: MultimodalNetwork): ServiceOption[] {
  return network.services
    .filter((service) => service.kind === 'timetabled')
    .map((service) => {
      const first = service.stops[0]?.name ?? 'Unknown'
      const departure = service.stops[0]?.departure
      return {
        id: service.id,
        label: `${service.routeCode || service.routeId} · ${first} · ${formatDeparture(departure)}`,
        confidence: 'verified' as const,
      }
    })
    .sort((a, b) => a.label.localeCompare(b.label))
}

function formatDeparture(minute: number | undefined): string {
  if (minute == null || !Number.isFinite(minute)) return '—'
  const normalised = ((Math.round(minute) % 1440) + 1440) % 1440
  return `${String(Math.floor(normalised / 60)).padStart(2, '0')}:${String(normalised % 60).padStart(2, '0')}`
}
