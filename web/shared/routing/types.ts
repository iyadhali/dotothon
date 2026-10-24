/**
 * Shared types for the multimodal network and router.
 *
 * These types are the contract between the Python data pipeline
 * (`scripts/multimodal/build_network.py`), the router (`router.ts`) and the Nuxt UI.
 * Keep them in sync with `MULTIMODAL_IMPLEMENTATION.md` §3–4.
 *
 * Times are integer minutes after midnight in `Indian/Maldives` (UTC+5).
 * Node ids are prefixed: `island:<islandId>`, `stop:<stopId>`, `airport:<iata>`.
 */

export type NodeKind = 'island' | 'stop' | 'airport'

export type Confidence = 'verified_timetable' | 'estimated_frequency' | 'estimated_access' | 'assumption'

export type ServiceConfidence = 'verified' | 'estimated'

/** Coarse transport scope selected by the user. Land covers walk/road access. */
export type TravelMode = 'land' | 'sea' | 'air'

/** Optional network selection carried by journey/accessibility requests. */
export interface NetworkSelection {
  /** Modes the user allows. Omitted means every mode. */
  allowedModes?: TravelMode[]
  /** Timetabled route ids or frequency service ids to remove. */
  disabledRouteIds?: string[]
  /** Exact service ids to remove (wins over route exclusions). */
  disabledServiceIds?: string[]
}

export interface Assumption {
  id: string
  value: string
  confidence: 'source' | 'assumption' | 'estimated'
  source: string
  note?: string
}

export interface RoutingDefaults {
  ferryBoardMinutes: number
  ferryAlightMinutes: number
  airBoardMinutes: number
  airBoardMinutesMle: number
  airAlightMinutes: number
  transferPenaltyMinutes: number
  additionalBoardPenaltyMinutes: number
  maxJourneyMinutes: number
}

export interface PopulationScope {
  /** Sum of `pop2022` over the 191 origin islands. */
  origins: number
  /** Census 2022 republic total, for context. */
  republic2022: number
  originCount: number
  /** Human-readable statement of the non-overlapping scope and omitted groups. */
  note: string
}

export interface NetworkCounts {
  islands: number
  origins: number
  stops: number
  airports: number
  ferryTrips: number
  airServices: number
  facilities: number
  categories: number
}

export interface NetworkMeta {
  schemaVersion: 1
  generatedAt: string
  timezone: 'Indian/Maldives' | string
  referenceDay: string
  serviceDayAssumption: string
  population: PopulationScope
  assumptions: Assumption[]
  counts: NetworkCounts
  routingDefaults: RoutingDefaults
  /** Routes excluded from the estimated air layer (status not "operating"). */
  excludedAirRoutes?: Array<{ from: string; to: string; status: string; reason: string }>
  /** Notes about coverage gaps discovered while building the network. */
  coverageNotes?: string[]
  /** Provenance for the optional intervention/service evidence layer. */
  serviceData?: {
    source: string
    note: string
    rowsRead: number
    rowsExcludedResort: number
    rowsExcludedUnresolvedIsland: number
    categories: number
    facilities: number
    confidenceNote: string
  }
}

export interface Island {
  id: string
  name: string
  atoll: string
  atollName: string
  lat: number
  lon: number
  population: number
  status: 'inhabited' | 'airport' | 'resort' | 'uninhabited_or_unknown' | string
  isOrigin: boolean
  airportIata?: string | null
}

export interface Stop {
  id: string
  code: string
  name: string
  islandId: string
  lat: number
  lon: number
  scheduled: boolean
}

export interface Airport {
  id: string
  iata: string
  name: string
  islandId: string
  lat: number
  lon: number
}

export type AccessMode = 'walk' | 'road' | 'speedboat' | 'ferry_transfer'

export interface AccessEdge {
  from: string
  to: string
  mode: AccessMode
  minutes: number
  confidence: Confidence
  basis: string
  distanceKm?: number
  /** True when the edge is a user/scenario assumption rather than sourced or derived. */
  assumed?: boolean
}

export interface StopTime {
  stopId: string
  name: string
  sequence: number
  arrival: number
  departure: number
}

export interface TimetabledService {
  id: string
  kind: 'timetabled'
  mode: 'ferry'
  operator: string
  routeId: string
  routeCode: string
  zone: string
  confidence: 'verified_timetable'
  calendar: string
  source: string
  stops: StopTime[]
}

export interface FrequencyService {
  id: string
  kind: 'frequency'
  mode: 'air' | 'ferry' | 'sea'
  /** Optional grouping id for the route checklist; defaults to the service id. */
  routeId?: string
  label?: string
  fromNode: string
  toNode: string
  fromAirport?: string
  toAirport?: string
  fromStopId?: string
  toStopId?: string
  airline?: string
  weeklyFrequency: number
  departuresPerDay: number
  operatingWindow: { start: number; end: number }
  blockMinutes: number
  departures: number[]
  confidence: 'estimated_frequency'
  status: string
  source: string
}

export type Service = TimetabledService | FrequencyService

export interface FacilityServiceEvidence {
  category: string
  detail?: string
  confidence: 'high' | 'medium' | 'low' | string
  source: string
  sourceDate?: string
}

export interface Facility {
  id: string
  name: string
  islandId: string
  kind: 'health' | 'education'
  categories: string[]
  tier?: string
  type?: string
  precision: 'island' | 'building' | 'approx'
  source: string
  sourceDate?: string
  /** False when the island join was fuzzy/uncertain and needs manual review. */
  reviewed: boolean
  /** Service/intervention categories claimed by this facility (subset of `categories`). */
  serviceCategories?: string[]
  /** One evidence row per claimed service category. */
  serviceEvidence?: FacilityServiceEvidence[]
  /** True for a facility added by a user scenario, not a source dataset. */
  userAdded?: boolean
}

export interface CategoryDefinition {
  id: string
  label: string
  definition: string
  facilityCount: number
  islandCount: number
  confidenceNote: string
  /** `intervention` categories come from the service evidence tables, not the facility master. */
  kind?: 'facility' | 'intervention'
  /** UI grouping label, e.g. "Health facilities", "Education", "Diagnostics & procedures". */
  group?: string
  source?: string
}

export interface MultimodalNetwork {
  meta: NetworkMeta
  islands: Island[]
  stops: Stop[]
  airports: Airport[]
  accessEdges: AccessEdge[]
  services: Service[]
  facilities: Facility[]
  categories: CategoryDefinition[]
}

export type OriginAccessStatus = 'reachable' | 'not_reachable' | 'no_origin_access' | 'no_destination'

export interface JourneyLeg {
  kind: 'access' | 'road' | 'ferry' | 'air' | 'sea'
  mode: AccessMode | 'ferry' | 'air' | 'sea'
  fromNode: string
  toNode: string
  fromName: string
  toName: string
  departureMinute: number
  arrivalMinute: number
  waitMinutes: number
  rideMinutes: number
  serviceId?: string
  routeCode?: string
  serviceConfidence?: ServiceConfidence
  distanceKm?: number
  basis?: string
}

export interface LegTotals {
  accessMinutes: number
  waitMinutes: number
  rideMinutes: number
  transferMinutes: number
  totalMinutes: number
}

export interface Journey {
  originIslandId: string
  originIslandName: string
  destinationIslandId: string
  destinationIslandName: string
  destinationFacilityIds: string[]
  destinationFacilityNames: string[]
  category: string
  departureMinute: number
  arrivalMinute: number
  elapsedMinutes: number
  dayOffset: number
  waitMinutes: number
  rideMinutes: number
  accessMinutes: number
  transferMinutes: number
  transfers: number
  modes: string[]
  legs: JourneyLeg[]
  serviceConfidence: ServiceConfidence
  /** True when the journey uses an estimated air service. */
  usesEstimatedAir: boolean
}

/** Result of a single-origin plan, including why no journey was returned. */
export interface JourneyPlan {
  status: OriginAccessStatus
  journey: Journey | null
}

export interface OriginAccess {
  originIslandId: string
  category: string
  status: OriginAccessStatus
  journey: Journey | null
}

export interface AccessibilitySummary {
  category: string
  populationTotal: number
  populationReachable: number
  within60: number
  within120: number
  within240: number
  unreachablePopulation: number
  noOriginAccessPopulation: number
  noDestinationPopulation: number
  /** populationReachable / populationTotal */
  coverage: number
  /** Population whose best journey uses verified timetable legs only. */
  reachableVerifiedPopulation: number
  reachableEstimatedPopulation: number
  originsReachable: number
  originsUnreachable: number
  originsNoAccess: number
  originsNoDestination: number
}

export interface AccessibilityResult {
  perOrigin: Record<string, OriginAccess>
  summary: AccessibilitySummary
}

export interface Scenario {
  addedTrips?: TimetabledService[]
  /** New frequency sea/air links (e.g. a user-proposed island service). */
  addedServices?: Service[]
  /** New physical links such as a road/bridge or a transfer. */
  addedAccessEdges?: AccessEdge[]
  /** New facilities (school, health centre, hospital, intervention site). */
  addedFacilities?: Facility[]
  cancelledServiceIds?: string[]
  delayMinutesByServiceId?: Record<string, number>
}

export interface JourneyRequest extends NetworkSelection {
  originIslandId: string
  departureMinute: number
  category: string
  /**
   * Legacy switch retained for callers from the first slice. Omitted means true.
   * When `allowedModes` is supplied, that selection takes precedence.
   */
  includeEstimatedAir?: boolean
  allowNextDay?: boolean
  scenario?: Scenario
  maxJourneyMinutes?: number
}

export interface AccessibilityRequest extends NetworkSelection {
  departureMinute: number
  category: string
  /** Legacy switch retained for callers from the first slice. Omitted means true. */
  includeEstimatedAir?: boolean
  allowNextDay?: boolean
  scenario?: Scenario
  maxJourneyMinutes?: number
}

export const NODE_PREFIX = {
  island: 'island:',
  stop: 'stop:',
  airport: 'airport:',
} as const

export function islandNode(id: string): string {
  return `${NODE_PREFIX.island}${id}`
}

export function stopNode(id: string): string {
  return `${NODE_PREFIX.stop}${id}`
}

export function airportNode(iata: string): string {
  return `${NODE_PREFIX.airport}${iata}`
}

export function nodeIslandId(nodeId: string): string | null {
  return nodeId.startsWith(NODE_PREFIX.island) ? nodeId.slice(NODE_PREFIX.island.length) : null
}
