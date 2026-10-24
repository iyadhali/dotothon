/**
 * Single store for the multimodal prototype page.
 *
 * Responsibilities: load the prepared network (with fixture fallback), apply the
 * user's scenario, run the router through the late-bound engine boundary, debounce
 * recomputation, and expose derived map/journey/metrics data to the page.
 *
 * The router is only reachable through `utils/engine.ts`, so this file typechecks
 * and renders while `web/shared/routing/router.ts` is still being written.
 */
import { computed, nextTick, onMounted, onScopeDispose, ref, shallowRef, watch } from 'vue'
import { $fetch } from 'ofetch'
import type { FeatureCollection } from 'geojson'
import type {
  AccessibilityRequest,
  AccessibilityResult,
  AccessibilitySummary,
  CategoryDefinition,
  Facility,
  FrequencyService,
  Journey,
  JourneyRequest,
  MultimodalNetwork,
  NetworkSelection,
  OriginAccess,
  OriginAccessStatus,
  Scenario,
  TravelMode,
} from '../../shared/routing/types'
import fixtureNetwork from '#shared/routing/fixtures/sample-network.json'
import { getMultimodalEngine } from '../utils/engine'
import { classifyAccess, type AccessClass } from '../utils/classify'
import type { CategoryAccess } from '../../shared/routing/nearby'
import type { FareTable } from '../../shared/routing/cost'
import type { SitingResult } from '../../shared/routing/recommend'
import type { Traveller } from '../../shared/routing/cost'
import { disabledByEvidence, EVIDENCE_LAYERS, type EvidenceKey } from '#shared/routing/evidence'
import {
  buildAirportPoints,
  buildFacilityPoints,
  buildRoutePaths,
  buildRoutePatterns,
  buildServiceOptions,
  type AirportPoint,
  type FacilityPoint,
  type RoutePath,
  type RoutePatternOption,
  type ServiceOption,
} from '../utils/routes'
import { buildIslandBands, type IslandBandInfo } from '../utils/bands'
import {
  compareAccessibility,
  splitByRegion,
  type RegionSplit,
  type ScenarioComparison,
  type ThresholdMinutes,
} from '../utils/analysis'
import { MINUTES_PER_DAY, formatClock, parseClock } from '../utils/format'
import {
  PRESET_FLAGS,
  allowedModesFor,
  buildRouteCatalog,
  islandsWithInfrastructure,
  type ModeFlags,
  type NetworkPreset,
  type RouteCatalog,
  type RouteCatalogEntry,
} from '../utils/selection'
import {
  categoryGroupLabel,
  facilityCategories,
  groupCategories,
  isInterventionCategory,
  type CategoryGroup,
} from '../utils/categories'

export type DataSource = 'api' | 'static' | 'fixture'
export type DataStatus = 'loading' | 'ready' | 'error'
export type ScenarioMode =
  | 'baseline'
  | 'add_trip'
  | 'cancel_service'
  | 'delay_service'
  | 'add_facility'
  | 'add_sea_route'
  | 'add_land_link'

export const DELAY_MINUTES = 30
export const DEFAULT_DEPARTURE_MINUTE = 480
export const DEFAULT_ADDED_DEPARTURE_MINUTE = 360
export const DEFAULT_SEA_MINUTES = 45
export const DEFAULT_LAND_MINUTES = 10

export interface InterventionFacilityRow {
  facilityId: string
  facilityName: string
  islandId: string
  islandName: string
  atollName: string
  population: number
  reachable: boolean
  status: OriginAccessStatus | null
  minutes: number | null
  confidence: string | null
  sourceDate: string | null
  detail: string | null
  userAdded: boolean
}

interface ScenarioViewState {
  network: MultimodalNetwork | null
  active: boolean
  scenario: Scenario
  description: string
  error: string | null
}

function describeError(error: unknown): string {
  if (error instanceof Error) return error.message
  if (typeof error === 'string') return error
  try {
    return JSON.stringify(error)
  } catch {
    return 'Unknown error'
  }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null
}

function isNetworkShape(value: unknown): value is MultimodalNetwork {
  if (!isRecord(value)) return false
  return (
    isRecord(value.meta) &&
    Array.isArray(value.islands) &&
    Array.isArray(value.stops) &&
    Array.isArray(value.airports) &&
    Array.isArray(value.services) &&
    Array.isArray(value.facilities) &&
    Array.isArray(value.categories) &&
    value.categories.length > 0
  )
}

function isFeatureCollection(value: unknown): value is FeatureCollection {
  if (!isRecord(value)) return false
  if (value.type !== 'FeatureCollection' || !Array.isArray(value.features)) return false
  return value.features.every((feature) => {
    if (!isRecord(feature)) return false
    if (feature.type !== 'Feature') return false
    return feature.geometry == null || isRecord(feature.geometry)
  })
}

function hasScenarioContent(scenario: Scenario): boolean {
  return Boolean(
    scenario.addedTrips?.length ||
      scenario.addedFacilities?.length ||
      scenario.addedServices?.length ||
      scenario.addedAccessEdges?.length ||
      scenario.cancelledServiceIds?.length ||
      (scenario.delayMinutesByServiceId &&
        Object.keys(scenario.delayMinutesByServiceId).length > 0),
  )
}

function slugify(value: string): string {
  return (
    value
      .normalize('NFKD')
      .replace(/[\u0300-\u036f]/g, '')
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/^-|-$/g, '') || 'item'
  )
}

/** Core services listed in the island access report, nearest first. */
const ACCESS_REPORT_CATEGORIES = [
  'health_hospital',
  'health_regional_tertiary',
  'education_grade_11_12',
  'education_higher_ed',
]
/** Default lodging (MVR 700, typical Malé guesthouse) + meals (MVR 250) for one night away; see data/external/economics/value_of_time.json. Editable in the panel. */
const ACCESS_REPORT_OVERNIGHT_MVR = 950

export type MapView = 'access' | 'underserved' | 'recommended'
export type FacilityType = 'all' | 'health' | 'education'
/** A proposed site's service area: islands reaching it within this many minutes ... */
const SITE_AREA_MINUTES = 180
/** ... on the best of these departures (06:00, 08:00, 10:00, 14:00). */
const SITE_AREA_DEPARTURES = [360, 480, 600, 840]
export interface SiteRoute {
  originId: string
  originName: string
  journey: Journey | null
  /** Travel time to the new site. */
  minutes: number | null
  /** Travel time to the nearest existing facility before (null when not reachable). */
  beforeMinutes: number | null
  beforeStatus: OriginAccessStatus | null
  /** The new site is faster than every existing facility for this island. */
  improves?: boolean
}
export interface SiteRoutes {
  rank: number
  siteId: string
  routes: SiteRoute[]
}
export interface ImpactStep {
  label: string
  reachable: number
  within: number
  total: number
  /** Atoll residents (outside Greater Malé) reaching the category the same day. */
  atollReachable: number
  atollTotal: number
}

/** Report categories per facility type, nearest-first services that matter most. */
const TYPE_CATEGORIES: Record<FacilityType, string[]> = {
  all: ['health_hospital', 'health_regional_tertiary', 'education_grade_11_12', 'education_higher_ed'],
  health: ['health_any', 'health_hospital', 'health_regional_tertiary'],
  education: ['education_school', 'education_grade_11_12', 'education_higher_ed'],
}
export type UnderservedClass = AccessClass

export function useMultimodal() {
  // ---------------------------------------------------------------- data load
  const dataStatus = ref<DataStatus>('loading')
  const dataSource = ref<DataSource | null>(null)
  const loadNote = ref<string | null>(null)
  const fatalError = ref<string | null>(null)
  const network = shallowRef<MultimodalNetwork | null>(null)
  const fares = shallowRef<FareTable | null>(null)
  const accessReport = shallowRef<CategoryAccess[]>([])
  const accessReportLoading = ref(false)
  const accessReportError = ref<string | null>(null)
  /** Lodging and meals for one night away (MVR), used when the trip home is not same-day. */
  const overnightMvr = ref(ACCESS_REPORT_OVERNIGHT_MVR)
  /** Map story: current access, underserved residents, or recommended new sites. */
  const mapView = ref<MapView>('access')
  /** Facility type filter for the minimal map and the island access report. */
  const facilityType = ref<FacilityType>('all')
  /** Weekday the timetable is read for; MTCC trips only run on their published days. */
  const dayOfWeek = ref<string>('Sat')
  /** Evidence layers in use (RTL, MTCC 2023, observed boats, estimated flights, Malé ferry). */
  const evidenceLayers = ref<EvidenceKey[]>(EVIDENCE_LAYERS.map((layer) => layer.key))
  /** Fare rules: adult resident, 65+/disabled, student or approved emergency. */
  const traveller = ref<Traveller>('adult')
  const siting = shallowRef<SitingResult | null>(null)
  /** For each recommended site: the journey from every newly covered island, before vs after. */
  const sitingRoutes = shallowRef<SiteRoutes[]>([])
  /** What each mode adds: residents reaching the category by road only, + sea, + air. */
  const impact = shallowRef<ImpactStep[]>([])
  const sitingError = ref<string | null>(null)
  const islandsGeojson = shallowRef<FeatureCollection | null>(null)
  const geojsonLoaded = ref(false)
  const engineReady = ref(false)
  const controlsReady = ref(false)

  // ------------------------------------------------------------------ controls
  const originIslandId = ref('')
  const category = ref('')
  const departureMinute = ref(DEFAULT_DEPARTURE_MINUTE)
  const includeEstimatedAir = ref(true)
  const threshold = ref<ThresholdMinutes>(60)

  // ------------------------------------------------------------------ scenario
  const scenarioMode = ref<ScenarioMode>('baseline')
  const addedRouteId = ref('')
  const addedFirstDepartureMinute = ref(DEFAULT_ADDED_DEPARTURE_MINUTE)
  const cancelledServiceId = ref('')
  const delayedServiceId = ref('')

  // --------------------------------------------------------- network selection
  const networkPreset = ref<NetworkPreset>('multimodal')
  const landEnabled = ref(true)
  const seaEnabled = ref(true)
  const airEnabled = ref(true)
  const disabledFerryRouteIds = ref<string[]>([])
  const disabledAirPairIds = ref<string[]>([])

  // -------------------------------------------------------- intervention panel
  const interventionRows = shallowRef<InterventionFacilityRow[]>([])
  const interventionLoading = ref(false)
  const interventionError = ref<string | null>(null)

  // ------------------------------------------------------- user simulator form
  const newFacilityName = ref('')
  const newFacilityKind = ref<'health' | 'education'>('health')
  const newFacilityCategory = ref('')
  const newFacilityIslandId = ref('')
  const newSeaFromIslandId = ref('')
  const newSeaToIslandId = ref('')
  const newSeaDepartureMinute = ref(DEFAULT_DEPARTURE_MINUTE)
  const newSeaTripsPerDay = ref(2)
  const newSeaMinutes = ref(DEFAULT_SEA_MINUTES)
  const newLandFromIslandId = ref('')
  const newLandToIslandId = ref('')
  const newLandMinutes = ref(DEFAULT_LAND_MINUTES)

  // ------------------------------------------------------------------- results
  const baselineAccessibility = shallowRef<AccessibilityResult | null>(null)
  const scenarioAccessibility = shallowRef<AccessibilityResult | null>(null)
  const unfilteredAccessibility = shallowRef<AccessibilityResult | null>(null)
  const metricsLoading = ref(false)
  const metricsError = ref<string | null>(null)
  const journey = shallowRef<Journey | null>(null)
  const journeyStatus = ref<OriginAccessStatus | null>(null)
  const nextDayJourney = shallowRef<Journey | null>(null)
  const journeyLoading = ref(false)
  const journeyError = ref<string | null>(null)

  // -------------------------------------------------------------- static lists
  const origins = computed(() => {
    const list = network.value?.islands.filter((island) => island.isOrigin) ?? []
    return [...list].sort(
      (a, b) => a.atollName.localeCompare(b.atollName) || b.population - a.population,
    )
  })

  const originGroups = computed(() => {
    const groups = new Map<string, typeof origins.value>()
    for (const island of origins.value) {
      const key = island.atollName || island.atoll
      const existing = groups.get(key)
      if (existing) existing.push(island)
      else groups.set(key, [island])
    }
    return [...groups.entries()].map(([atollName, islands]) => ({ atollName, islands }))
  })

  const categories = computed(() => network.value?.categories ?? [])
  const categoryGroups = computed<CategoryGroup[]>(() => groupCategories(categories.value))
  const facilityCategoryOptions = computed<CategoryDefinition[]>(() =>
    facilityCategories(categories.value),
  )
  const routePatterns = computed<RoutePatternOption[]>(() =>
    network.value ? buildRoutePatterns(network.value) : [],
  )
  const serviceOptions = computed<ServiceOption[]>(() =>
    network.value ? buildServiceOptions(network.value) : [],
  )

  // --------------------------------------------------------- selection derived
  const routeCatalog = computed<RouteCatalog>(() => buildRouteCatalog(network.value))
  const modeFlags = computed(() => ({
    land: landEnabled.value,
    sea: seaEnabled.value,
    air: airEnabled.value,
  }))
  const allowedModes = computed<TravelMode[]>(() => allowedModesFor(modeFlags.value))
  const filterActive = computed(
    () =>
      !landEnabled.value ||
      !seaEnabled.value ||
      !airEnabled.value ||
      disabledFerryRouteIds.value.length > 0 ||
      disabledAirPairIds.value.length > 0,
  )
  const hasInfrastructure = computed(() => islandsWithInfrastructure(network.value))
  const disabledAirServiceIds = computed(() => {
    const ids: string[] = []
    for (const key of disabledAirPairIds.value) {
      const entry = routeCatalog.value.air.find((candidate) => candidate.key === key)
      if (entry) ids.push(...entry.serviceIds)
    }
    return ids
  })
  const disabledRouteIds = computed(() => [
    ...disabledFerryRouteIds.value,
    ...disabledAirServiceIds.value,
  ])
  const enabledRouteCount = computed(
    () =>
      routeCatalog.value.ferries.length -
      disabledFerryRouteIds.value.length +
      (routeCatalog.value.air.length - disabledAirPairIds.value.length),
  )
  const selectionKey = computed(
    () =>
      `${landEnabled.value}|${seaEnabled.value}|${airEnabled.value}|${disabledFerryRouteIds.value.join(',')}|${disabledAirPairIds.value.join(',')}|${dayOfWeek.value}|${evidenceLayers.value.join(',')}`,
  )
  const evidenceDisabledServiceIds = computed(() =>
    network.value ? disabledByEvidence(network.value, new Set(evidenceLayers.value)) : [],
  )
  const selectedOriginHasInfrastructure = computed(() =>
    hasInfrastructure.value.has(originIslandId.value),
  )
  const categoryIsIntervention = computed(
    () => Boolean(selectedCategory.value && isInterventionCategory(selectedCategory.value)),
  )
  const interventionCategories = computed(() =>
    categories.value.filter((definition) => isInterventionCategory(definition)),
  )

  function isRouteServiceEnabled(route: RoutePath): boolean {
    if (route.mode === 'air') {
      return !disabledAirServiceIds.value.includes(route.serviceId)
    }
    return !disabledFerryRouteIds.value.includes(route.routeId)
  }

  const selectedOrigin = computed(
    () => origins.value.find((island) => island.id === originIslandId.value) ?? null,
  )
  const selectedCategory = computed(
    () => categories.value.find((definition) => definition.id === category.value) ?? null,
  )

  const selectedRoutePattern = computed(
    () => routePatterns.value.find((pattern) => pattern.routeId === addedRouteId.value) ?? null,
  )

  /** First departure of the earliest timetabled service on the selected pattern. */
  const selectedRouteFirstDeparture = computed<{ minute: number; serviceId: string } | null>(() => {
    const net = network.value
    const pattern = selectedRoutePattern.value
    if (!net || !pattern) return null
    let best: { minute: number; serviceId: string } | null = null
    for (const service of net.services) {
      if (service.kind !== 'timetabled') continue
      if (!pattern.serviceIds.includes(service.id)) continue
      const first = service.stops[0]?.departure
      if (first == null) continue
      if (!best || first < best.minute) best = { minute: first, serviceId: service.id }
    }
    return best
  })

  function serviceLabel(serviceId: string): string {
    const net = network.value
    if (!net) return serviceId
    const service = net.services.find((candidate) => candidate.id === serviceId)
    if (!service) return serviceId
    if (service.kind === 'timetabled') {
      const first = service.stops[0]
      if (first) {
        return `${service.routeCode || service.routeId} · ${first.name} dep ${formatClock(first.departure)}`
      }
      return service.routeCode || service.routeId
    }
    return `${service.mode === 'air' ? 'Air' : service.mode === 'sea' ? 'Sea' : 'Ferry'} service ${service.id}`
  }

  function clamp(value: number, min: number, max: number): number {
    if (!Number.isFinite(value)) return min
    return Math.min(max, Math.max(min, Math.round(value)))
  }

  function buildSimulatorScenario(
    net: MultimodalNetwork,
  ): { scenario: Scenario; description: string } | null {
    if (scenarioMode.value === 'add_facility') {
      const name = newFacilityName.value.trim()
      const island = net.islands.find((candidate) => candidate.id === newFacilityIslandId.value)
      const definition = net.categories.find(
        (candidate) => candidate.id === newFacilityCategory.value,
      )
      if (!name || !island || !definition) return null
      const facility: Facility = {
        id: `scenario:facility:${slugify(island.id)}-${slugify(name)}-${slugify(definition.id)}`,
        name,
        islandId: island.id,
        kind: newFacilityKind.value,
        categories: [definition.id],
        precision: 'island',
        source:
          'User scenario — a hypothetical facility added in this prototype, not a verified facility record.',
        reviewed: false,
        userAdded: true,
      }
      return {
        scenario: { addedFacilities: [facility] },
        description: `User scenario: one hypothetical ${definition.label} facility added at ${island.name}. Island-level assumption — no building location, staffing or opening hours are modelled.`,
      }
    }

    if (scenarioMode.value === 'add_sea_route') {
      const from = net.islands.find((candidate) => candidate.id === newSeaFromIslandId.value)
      const to = net.islands.find((candidate) => candidate.id === newSeaToIslandId.value)
      if (!from || !to || from.id === to.id) return null
      const trips = clamp(newSeaTripsPerDay.value, 1, 12)
      const minutes = clamp(newSeaMinutes.value, 5, 600)
      const start = clamp(newSeaDepartureMinute.value, 0, MINUTES_PER_DAY - 1)
      const end = Math.min(start + 12 * 60, MINUTES_PER_DAY - 1)
      const departures =
        trips === 1
          ? [start]
          : Array.from({ length: trips }, (_, index) =>
              Math.round(start + (index * (end - start)) / (trips - 1)),
            )
      const id = `scenario:sea:${slugify(from.id)}-${slugify(to.id)}:${start}:${trips}`
      const service: FrequencyService = {
        id,
        kind: 'frequency',
        mode: 'sea',
        routeId: id,
        label: `${from.name} → ${to.name}`,
        fromNode: `island:${from.id}`,
        toNode: `island:${to.id}`,
        weeklyFrequency: trips * 7,
        departuresPerDay: trips,
        operatingWindow: { start, end },
        blockMinutes: minutes,
        departures,
        confidence: 'estimated_frequency',
        status: 'user_scenario',
        source:
          'User scenario — an assumed sea link with a user-entered schedule and crossing time, not a published timetable or observed service.',
      }
      return {
        scenario: { addedServices: [service] },
        description: `User scenario: assumed sea link ${from.name} → ${to.name}, ${trips} trip${trips === 1 ? '' : 's'}/day from ${formatClock(start)}, ${minutes} min crossing. This is a user assumption, not a sourced route.`,
      }
    }

    if (scenarioMode.value === 'add_land_link') {
      const from = net.islands.find((candidate) => candidate.id === newLandFromIslandId.value)
      const to = net.islands.find((candidate) => candidate.id === newLandToIslandId.value)
      if (!from || !to || from.id === to.id) return null
      const minutes = clamp(newLandMinutes.value, 1, 600)
      const basis = `User scenario: assumed direct land link between ${from.name} and ${to.name} taking ${minutes} minutes; no bridge, causeway or road is verified.`
      return {
        scenario: {
          addedAccessEdges: [
            {
              from: `island:${from.id}`,
              to: `island:${to.id}`,
              mode: 'road',
              minutes,
              confidence: 'assumption',
              basis,
              assumed: true,
            },
            {
              from: `island:${to.id}`,
              to: `island:${from.id}`,
              mode: 'road',
              minutes,
              confidence: 'assumption',
              basis,
              assumed: true,
            },
          ],
        },
        description: `User scenario: assumed ${minutes}-minute land link ${from.name} ↔ ${to.name}. No bridge or road is verified; this is an intervention hypothesis.`,
      }
    }

    return null
  }

  const scenarioView = computed<ScenarioViewState>(() => {
    const net = network.value
    const engine = getMultimodalEngine()
    const baseline: ScenarioViewState = {
      network: net,
      active: false,
      scenario: {},
      description: 'Baseline: the prepared reference-day services as published.',
      error: null,
    }
    if (!net || !engine) return baseline
    if (scenarioMode.value === 'baseline') return baseline

    try {
      let scenario: Scenario = {}
      let description = ''
      if (scenarioMode.value === 'add_trip') {
        if (!addedRouteId.value) return baseline
        const pattern = routePatterns.value.find((option) => option.routeId === addedRouteId.value)
        const id = `scenario:added:${addedRouteId.value}:${addedFirstDepartureMinute.value}`
        const added = engine.createServiceFromPattern(
          net,
          addedRouteId.value,
          addedFirstDepartureMinute.value,
          id,
        )
        scenario = { addedTrips: [added] }
        description = `User scenario: one extra morning departure on ${pattern?.label ?? addedRouteId.value} at ${formatClock(addedFirstDepartureMinute.value)}.`
      } else if (scenarioMode.value === 'cancel_service') {
        if (!cancelledServiceId.value) return baseline
        scenario = { cancelledServiceIds: [cancelledServiceId.value] }
        description = `User scenario: ${serviceLabel(cancelledServiceId.value)} is cancelled.`
      } else if (scenarioMode.value === 'delay_service') {
        if (!delayedServiceId.value) return baseline
        scenario = { delayMinutesByServiceId: { [delayedServiceId.value]: DELAY_MINUTES } }
        description = `User scenario: ${serviceLabel(delayedServiceId.value)} starts ${DELAY_MINUTES} minutes late.`
      } else {
        const simulated = buildSimulatorScenario(net)
        if (!simulated) return baseline
        scenario = simulated.scenario
        description = simulated.description
      }

      if (!hasScenarioContent(scenario)) return baseline
      return {
        network: engine.applyScenario(net, scenario),
        active: true,
        scenario,
        description,
        error: null,
      }
    } catch (error) {
      return {
        network: net,
        active: false,
        scenario: {},
        description: 'The scenario could not be applied; showing the baseline.',
        error: describeError(error),
      }
    }
  })

  const scenarioActive = computed(() => scenarioView.value.active)
  const scenarioError = computed(() => scenarioView.value.error)
  const scenarioDescription = computed(() => scenarioView.value.description)
  const activeNetwork = computed(() => scenarioView.value.network)

  const canResetScenario = computed(
    () => scenarioMode.value !== 'baseline' || scenarioActive.value,
  )

  // --------------------------------------------------------------- map/derived
  const displayAccessibility = computed<AccessibilityResult | null>(() => {
    if (scenarioActive.value) return scenarioAccessibility.value ?? baselineAccessibility.value
    return baselineAccessibility.value
  })

  const regionSplit = computed<RegionSplit | null>(() =>
    splitByRegion(displayAccessibility.value, network.value?.islands ?? []),
  )

  const islandBands = computed<Record<string, IslandBandInfo>>(() =>
    buildIslandBands(displayAccessibility.value, network.value?.islands ?? [], {
      filterActive: filterActive.value,
      hasInfrastructure: hasInfrastructure.value,
    }),
  )

  const routePaths = computed<RoutePath[]>(() => {
    const net = activeNetwork.value
    if (!net) return []
    return buildRoutePaths(net).filter((route) => isRouteServiceEnabled(route))
  })
  const airportPoints = computed<AirportPoint[]>(() =>
    activeNetwork.value ? buildAirportPoints(activeNetwork.value) : [],
  )
  const facilityPoints = computed<FacilityPoint[]>(() =>
    activeNetwork.value ? buildFacilityPoints(activeNetwork.value, category.value) : [],
  )

  const selectedOriginAccess = computed<OriginAccess | null>(() => {
    const access = displayAccessibility.value?.perOrigin[originIslandId.value]
    return access ?? null
  })

  const selectedOriginStatus = computed<OriginAccessStatus | null>(
    () => selectedOriginAccess.value?.status ?? null,
  )

  const selectedOriginFilteredOut = computed(
    () =>
      filterActive.value &&
      selectedOriginHasInfrastructure.value &&
      selectedOriginStatus.value === 'no_origin_access',
  )

  const baselineSummary = computed<AccessibilitySummary | null>(
    () => baselineAccessibility.value?.summary ?? null,
  )
  const scenarioSummary = computed<AccessibilitySummary | null>(
    () => scenarioAccessibility.value?.summary ?? null,
  )
  const unfilteredSummary = computed<AccessibilitySummary | null>(
    () => unfilteredAccessibility.value?.summary ?? null,
  )

  const comparison = computed<ScenarioComparison | null>(() => {
    if (!scenarioActive.value) return null
    const net = network.value
    const baseline = baselineAccessibility.value
    const scenario = scenarioAccessibility.value
    if (!net || !baseline || !scenario) return null
    return compareAccessibility(baseline, scenario, net.islands, threshold.value)
  })

  const meta = computed(() => network.value?.meta ?? null)
  const populationScope = computed(() => meta.value?.population ?? null)

  // ------------------------------------------------------------------- compute
  let metricsToken = 0
  let journeyToken = 0

  function selectionRequest(): NetworkSelection & { includeEstimatedAir: boolean } {
    return {
      allowedModes: allowedModes.value,
      disabledRouteIds: disabledRouteIds.value,
      disabledServiceIds: evidenceDisabledServiceIds.value,
      dayOfWeek: dayOfWeek.value,
      includeEstimatedAir: airEnabled.value,
    }
  }

  function accessibilityRequest(): AccessibilityRequest {
    return {
      departureMinute: departureMinute.value,
      category: category.value,
      ...selectionRequest(),
    }
  }

  async function recomputeMetrics(): Promise<void> {
    const engine = getMultimodalEngine()
    const baselineNetwork = network.value
    const cat = category.value
    if (!engine || !baselineNetwork || !cat) {
      baselineAccessibility.value = null
      scenarioAccessibility.value = null
      unfilteredAccessibility.value = null
      metricsLoading.value = false
      return
    }

    const token = ++metricsToken
    metricsLoading.value = true
    metricsError.value = null
    await nextTick()
    await new Promise<void>((resolve) => setTimeout(resolve, 0))
    if (token !== metricsToken) return

    try {
      const request = accessibilityRequest()
      const baseline = engine.computeAccessibility(baselineNetwork, request)
      const steps: { label: string; modes: TravelMode[] }[] = [
        { label: 'Road only', modes: ['land'] },
        { label: '+ Ferries & boats', modes: ['land', 'sea'] },
        { label: '+ Flights', modes: ['land', 'sea', 'air'] },
      ]
      impact.value = steps.map((step) => {
        const result = engine.computeAccessibility(baselineNetwork, {
          ...request,
          allowedModes: step.modes,
          includeEstimatedAir: step.modes.includes('air'),
        })
        const summary = result.summary
        const atolls = splitByRegion(result, baselineNetwork.islands)?.atolls
        return {
          label: step.label,
          reachable: summary.populationReachable,
          within: summary[`within${threshold.value}` as 'within60'],
          total: summary.populationTotal,
          atollReachable: atolls ? atolls.onIsland + atolls.byTransport : 0,
          atollTotal: atolls?.population ?? 0,
        }
      })
      const unfiltered = filterActive.value
        ? engine.computeAccessibility(baselineNetwork, {
            departureMinute: departureMinute.value,
            category: cat,
            allowedModes: ['land', 'sea', 'air'],
            disabledRouteIds: [],
            includeEstimatedAir: true,
          })
        : null
      let scenario: AccessibilityResult | null = null
      const active = activeNetwork.value
      if (scenarioActive.value && active) {
        scenario = engine.computeAccessibility(active, request)
      }
      if (token !== metricsToken) return
      baselineAccessibility.value = baseline
      scenarioAccessibility.value = scenario
      unfilteredAccessibility.value = unfiltered
    } catch (error) {
      if (token !== metricsToken) return
      baselineAccessibility.value = null
      scenarioAccessibility.value = null
      unfilteredAccessibility.value = null
      metricsError.value = describeError(error)
    } finally {
      if (token === metricsToken) metricsLoading.value = false
    }
  }

  async function recomputeJourney(): Promise<void> {
    const engine = getMultimodalEngine()
    const active = activeNetwork.value
    if (!engine || !active || !originIslandId.value || !category.value) {
      journey.value = null
      journeyStatus.value = null
      nextDayJourney.value = null
      journeyLoading.value = false
      return
    }

    const token = ++journeyToken
    journeyLoading.value = true
    journeyError.value = null
    await nextTick()
    await new Promise<void>((resolve) => setTimeout(resolve, 0))
    if (token !== journeyToken) return

    try {
      const request: JourneyRequest = {
        originIslandId: originIslandId.value,
        departureMinute: departureMinute.value,
        category: category.value,
        ...selectionRequest(),
      }
      let sameDay: Journey | null = null
      let status: OriginAccessStatus = 'not_reachable'
      if (engine.planJourneyWithStatus) {
        const plan = engine.planJourneyWithStatus(active, request)
        sameDay = plan.journey
        status = plan.status
      } else {
        sameDay = engine.planJourney(active, request)
        status = sameDay ? 'reachable' : (selectedOriginAccess.value?.status ?? 'not_reachable')
      }
      // A next-day search can only explain `not_reachable`; no physical access or no
      // destination in the category cannot be fixed by waiting 24 hours.
      let nextDay: Journey | null = null
      if (status === 'not_reachable') {
        nextDay = engine.planJourney(active, { ...request, allowNextDay: true })
      }
      if (token !== journeyToken) return
      journey.value = sameDay
      journeyStatus.value = status
      nextDayJourney.value = nextDay
    } catch (error) {
      if (token !== journeyToken) return
      journey.value = null
      journeyStatus.value = null
      nextDayJourney.value = null
      journeyError.value = describeError(error)
    } finally {
      if (token === journeyToken) journeyLoading.value = false
    }
  }

  let accessReportToken = 0

  /** Report categories: the core services, plus the selected category when it is a service. */
  function accessReportCategories(): string[] {
    const known = new Set(categories.value.map((definition) => definition.id))
    const list = TYPE_CATEGORIES[facilityType.value].filter((id) => known.has(id))
    if (facilityType.value === 'all' && category.value && known.has(category.value) && !list.includes(category.value)) {
      list.push(category.value)
    }
    return list
  }

  async function recomputeAccessReport(): Promise<void> {
    const engine = getMultimodalEngine()
    const active = activeNetwork.value
    if (!engine?.buildAccessReport || !active || !originIslandId.value) {
      accessReport.value = []
      accessReportLoading.value = false
      return
    }
    const token = ++accessReportToken
    accessReportLoading.value = true
    accessReportError.value = null
    await nextTick()
    await new Promise<void>((resolve) => setTimeout(resolve, 0))
    if (token !== accessReportToken) return
    try {
      const report = engine.buildAccessReport(active, fares.value, {
        originIslandId: originIslandId.value,
        departureMinute: departureMinute.value,
        categories: accessReportCategories(),
        allowedModes: allowedModes.value,
        disabledRouteIds: disabledRouteIds.value,
        disabledServiceIds: evidenceDisabledServiceIds.value,
        dayOfWeek: dayOfWeek.value,
        overnightMvr: overnightMvr.value,
        traveller: traveller.value,
      })
      if (token !== accessReportToken) return
      accessReport.value = report
    } catch (error) {
      if (token !== accessReportToken) return
      accessReport.value = []
      accessReportError.value = describeError(error)
    } finally {
      if (token === accessReportToken) accessReportLoading.value = false
    }
  }

  /** Greedy maximal-coverage ranking of new sites; only computed for the Recommended view. */
  function recomputeSiting(): void {
    const engine = getMultimodalEngine()
    const active = activeNetwork.value
    if (mapView.value !== 'recommended' || !engine?.buildTravelMatrix || !engine.recommendSites || !active || !category.value) {
      siting.value = null
      sitingRoutes.value = []
      return
    }
    try {
      const matrix = engine.buildTravelMatrix(active, {
        departureMinute: departureMinute.value,
        maxJourneyMinutes: threshold.value,
        allowedModes: allowedModes.value,
        disabledRouteIds: disabledRouteIds.value,
        disabledServiceIds: evidenceDisabledServiceIds.value,
        dayOfWeek: dayOfWeek.value,
      })
      siting.value = engine.recommendSites(active, matrix, {
        category: category.value,
        thresholdMinutes: threshold.value,
        picks: 5,
      })
      // Service area of each site: islands that can reach it within SITE_AREA_MINUTES on the best
      // of several departures (how people plan a hospital trip). `improves` marks islands for which
      // the new site beats every existing facility on the same best-of-day basis.
      const best = new Map<string, Map<string, { minutes: number; departure: number }>>()
      for (const departure of SITE_AREA_DEPARTURES) {
        const matrix = engine.buildTravelMatrix(active, {
          departureMinute: departure,
          maxJourneyMinutes: SITE_AREA_MINUTES,
          allowedModes: allowedModes.value,
          disabledRouteIds: disabledRouteIds.value,
          disabledServiceIds: evidenceDisabledServiceIds.value,
          dayOfWeek: dayOfWeek.value,
        })
        for (const [originId, row] of matrix) {
          const acc = best.get(originId) ?? new Map()
          for (const [islandId, minutes] of row) {
            const prev = acc.get(islandId)
            if (!prev || minutes < prev.minutes) acc.set(islandId, { minutes, departure })
          }
          best.set(originId, acc)
        }
      }
      const existing = [...new Set(active.facilities.filter((f) => f.categories.includes(category.value)).map((f) => f.islandId))]
      const names = new Map(active.islands.map((island) => [island.id, island.name]))
      sitingRoutes.value = engine.planIslandToIsland
        ? siting.value.sites.map((site) => ({
            rank: site.rank,
            siteId: site.islandId,
            routes: [...best.entries()]
              .filter(([originId, row]) => originId !== site.islandId && row.has(site.islandId))
              .map(([originId, row]) => {
                const target = row.get(site.islandId)!
                const was = Math.min(...existing.map((id) => row.get(id)?.minutes ?? Infinity))
                const journey = engine.planIslandToIsland!(active, {
                  fromIslandId: originId,
                  toIslandId: site.islandId,
                  departureMinute: target.departure,
                  allowedModes: allowedModes.value,
                  disabledRouteIds: disabledRouteIds.value,
                  disabledServiceIds: evidenceDisabledServiceIds.value,
                  dayOfWeek: dayOfWeek.value,
                })
                return {
                  originId,
                  originName: names.get(originId) ?? originId,
                  journey,
                  minutes: target.minutes,
                  beforeMinutes: Number.isFinite(was) ? was : null,
                  beforeStatus: Number.isFinite(was) ? ('reachable' as const) : null,
                  improves: target.minutes < was,
                }
              })
              .sort((a, b) => Number(b.improves) - Number(a.improves) || a.minutes - b.minutes),
          }))
        : []
      sitingError.value = null
    } catch (error) {
      siting.value = null
      sitingError.value = describeError(error)
    }
  }

  /** Underserved class per origin island relative to the selected threshold. */
  const underservedClasses = computed<Record<string, UnderservedClass>>(() => {
    const result = displayAccessibility.value
    const out: Record<string, UnderservedClass> = {}
    if (!result) return out
    for (const [islandId, access] of Object.entries(result.perOrigin)) {
      const cls = classifyAccess(access, threshold.value)
      if (cls) out[islandId] = cls
    }
    return out
  })

  async function loadFares(): Promise<void> {
    try {
      fares.value = await $fetch<FareTable>('/data/fares.json', { timeout: 15000 })
    } catch {
      fares.value = null
    }
  }

  let interventionToken = 0

  /**
   * Intervention evidence is per facility, while the router answers per origin and
   * category. To answer "can this origin reach this facility island?" we narrow the
   * network to one island's facilities at a time. Work is yielded in small chunks so
   * a large evidence table never blocks the control rail.
   */
  async function recomputeInterventions(): Promise<void> {
    const engine = getMultimodalEngine()
    const net = activeNetwork.value
    const definition = selectedCategory.value
    const origin = originIslandId.value
    if (
      !engine?.planJourneyWithStatus ||
      !net ||
      !definition ||
      !origin ||
      !categoryIsIntervention.value
    ) {
      interventionRows.value = []
      interventionLoading.value = false
      interventionError.value = null
      return
    }

    const token = ++interventionToken
    interventionLoading.value = true
    interventionError.value = null
    await nextTick()
    await new Promise<void>((resolve) => setTimeout(resolve, 0))
    if (token !== interventionToken) return

    try {
      const facilities = net.facilities.filter((facility) =>
        facility.categories.includes(definition.id),
      )
      const grouped = new Map<string, Facility[]>()
      for (const facility of facilities) {
        const list = grouped.get(facility.islandId)
        if (list) list.push(facility)
        else grouped.set(facility.islandId, [facility])
      }
      const islands = new Map(net.islands.map((island) => [island.id, island]))
      const rows: InterventionFacilityRow[] = []
      let processed = 0
      for (const [islandId, islandFacilities] of grouped) {
        const island = islands.get(islandId)
        if (island) {
          const plan = engine.planJourneyWithStatus(
            { ...net, facilities: islandFacilities },
            {
              originIslandId: origin,
              departureMinute: departureMinute.value,
              category: definition.id,
              ...selectionRequest(),
            },
          )
          for (const facility of islandFacilities) {
            const evidence = facility.serviceEvidence?.find(
              (candidate) => candidate.category === definition.id,
            )
            rows.push({
              facilityId: facility.id,
              facilityName: facility.name,
              islandId,
              islandName: island.name,
              atollName: island.atollName,
              population: island.population,
              reachable: plan.status === 'reachable' && plan.journey !== null,
              status: plan.status,
              minutes: plan.journey?.elapsedMinutes ?? null,
              confidence: evidence?.confidence ?? null,
              sourceDate: evidence?.sourceDate ?? facility.sourceDate ?? null,
              detail: evidence?.detail ?? facility.tier ?? facility.type ?? null,
              userAdded: Boolean(facility.userAdded),
            })
          }
        }
        processed += 1
        if (processed % 8 === 0) {
          await new Promise<void>((resolve) => setTimeout(resolve, 0))
          if (token !== interventionToken) return
        }
      }
      rows.sort((a, b) => {
        if (a.reachable !== b.reachable) return a.reachable ? -1 : 1
        return b.population - a.population || a.facilityName.localeCompare(b.facilityName)
      })
      if (token !== interventionToken) return
      interventionRows.value = rows
    } catch (error) {
      if (token !== interventionToken) return
      interventionRows.value = []
      interventionError.value = describeError(error)
    } finally {
      if (token === interventionToken) interventionLoading.value = false
    }
  }

  function debounce(fn: () => void, delay = 180): { run: () => void; cancel: () => void } {
    let timer: ReturnType<typeof setTimeout> | null = null
    const run = () => {
      if (timer) clearTimeout(timer)
      timer = setTimeout(() => {
        timer = null
        fn()
      }, delay)
    }
    const cancel = () => {
      if (timer) clearTimeout(timer)
      timer = null
    }
    onScopeDispose(cancel)
    return { run, cancel }
  }

  const scheduleMetrics = debounce(() => {
    void recomputeMetrics()
  })
  const scheduleJourney = debounce(() => {
    void recomputeJourney()
  })
  const scheduleAccessReport = debounce(() => {
    void recomputeAccessReport()
  })
  const scheduleSiting = debounce(() => {
    recomputeSiting()
  })
  const scheduleInterventions = debounce(() => {
    void recomputeInterventions()
  }, 260)

  // The radio group writes `scenarioMode` through v-model, not setScenarioMode,
  // so defaults must also be prepared from the ref itself.
  watch(scenarioMode, (mode) => {
    if (!controlsReady.value) return
    prepareScenarioMode(mode)
  })
  // Presets drive the three custom toggles; choosing a custom toggle switches the
  // preset label to custom without changing the other modes.
  watch(networkPreset, (preset) => {
    if (preset === 'custom') return
    const flags = PRESET_FLAGS[preset]
    landEnabled.value = flags.land
    seaEnabled.value = flags.sea
    airEnabled.value = flags.air
  })
  watch([category, departureMinute, selectionKey, scenarioView, threshold], () => {
    if (!controlsReady.value) return
    scheduleMetrics.run()
  })
  watch([originIslandId, category, departureMinute, selectionKey, scenarioView], () => {
    if (!controlsReady.value) return
    scheduleJourney.run()
  })
  watch([originIslandId, category, departureMinute, selectionKey, scenarioView, overnightMvr, fares, facilityType, traveller], () => {
    if (!controlsReady.value) return
    scheduleAccessReport.run()
  })
  watch([mapView, category, departureMinute, threshold, selectionKey, scenarioView], () => {
    if (!controlsReady.value) return
    scheduleSiting.run()
  })
  watch(
    [categoryIsIntervention, originIslandId, departureMinute, selectionKey, scenarioView],
    () => {
      if (!controlsReady.value) return
      scheduleInterventions.run()
    },
  )

  // ---------------------------------------------------------------- load logic
  async function loadGeojson(): Promise<void> {
    for (const url of ['/api/islands', '/data/islands.geojson']) {
      try {
        const raw = await $fetch<unknown>(url, { timeout: 15000 })
        if (isFeatureCollection(raw)) {
          islandsGeojson.value = raw
          geojsonLoaded.value = true
          return
        }
      } catch {
        // try the next source
      }
    }
    islandsGeojson.value = null
    geojsonLoaded.value = true
  }

  async function fetchNetwork(url: string): Promise<MultimodalNetwork> {
    const payload = await $fetch<unknown>(url, { timeout: 15000 })
    if (!isNetworkShape(payload)) {
      throw new Error(`${url} exists but its shape is invalid.`)
    }
    return payload
  }

  /** Timetabled services whose stop pattern includes a stop on this island. */
  function servicesServingIsland(net: MultimodalNetwork, islandId: string): Set<string> {
    const stopIds = new Set(
      net.stops.filter((stop) => stop.islandId === islandId).map((stop) => stop.id),
    )
    const ids = new Set<string>()
    for (const service of net.services) {
      if (service.kind !== 'timetabled') continue
      if (service.stops.some((stop) => stopIds.has(stop.stopId))) ids.add(service.id)
    }
    return ids
  }

  function defaultRoutePattern(net: MultimodalNetwork, islandId: string): string {
    const serving = servicesServingIsland(net, islandId)
    const patterns = buildRoutePatterns(net)
    const preferred = patterns.find((pattern) =>
      pattern.serviceIds.some((serviceId) => serving.has(serviceId)),
    )
    return preferred?.routeId ?? patterns[0]?.routeId ?? ''
  }

  function defaultServiceId(net: MultimodalNetwork, islandId: string): string {
    const serving = servicesServingIsland(net, islandId)
    const services = buildServiceOptions(net)
    const preferred = services.find((option) => serving.has(option.id))
    return preferred?.id ?? services[0]?.id ?? ''
  }

  function applyDefaults(net: MultimodalNetwork): void {
    const originList = net.islands.filter((island) => island.isOrigin)
    if (!originList.some((island) => island.id === originIslandId.value)) {
      // Prefer an inhabited outer island without a hospital so the first view shows a
      // real multimodal itinerary; fall back to Malé, then to the largest origin.
      const preferred = originList.find((island) => island.id === 'MV007007')
      const male = originList.find((island) => island.id === 'MV021001')
      const largest = [...originList].sort((a, b) => b.population - a.population)[0]
      originIslandId.value = preferred?.id ?? male?.id ?? largest?.id ?? ''
    }
    if (!net.categories.some((definition) => definition.id === category.value)) {
      const preferred =
        net.categories.find((definition) => definition.id === 'health_hospital') ??
        net.categories[0]
      category.value = preferred?.id ?? ''
    }
    // Scenario defaults should touch the selected origin, otherwise the first
    // comparison a user sees would be a change somewhere else in the country.
    const patterns = buildRoutePatterns(net)
    if (!patterns.some((pattern) => pattern.routeId === addedRouteId.value)) {
      addedRouteId.value = defaultRoutePattern(net, originIslandId.value)
    }
    const services = buildServiceOptions(net)
    if (!services.some((option) => option.id === cancelledServiceId.value)) {
      cancelledServiceId.value = defaultServiceId(net, originIslandId.value)
    }
    if (!services.some((option) => option.id === delayedServiceId.value)) {
      delayedServiceId.value = defaultServiceId(net, originIslandId.value)
    }

    // Simulator defaults are anchored to the selected origin so the first form is
    // immediately actionable, while every generated object is clearly labelled as
    // a user assumption.
    if (!originList.some((island) => island.id === newFacilityIslandId.value)) {
      newFacilityIslandId.value = originIslandId.value
    }
    if (!net.categories.some((definition) => definition.id === newFacilityCategory.value)) {
      newFacilityCategory.value = category.value
    }
    newFacilityKind.value = newFacilityCategory.value.startsWith('education')
      ? 'education'
      : 'health'
    const other = otherOriginId(net, originIslandId.value)
    if (!originList.some((island) => island.id === newSeaFromIslandId.value)) {
      newSeaFromIslandId.value = originIslandId.value
    }
    if (
      !originList.some((island) => island.id === newSeaToIslandId.value) ||
      newSeaToIslandId.value === newSeaFromIslandId.value
    ) {
      newSeaToIslandId.value = other
    }
    if (!originList.some((island) => island.id === newLandFromIslandId.value)) {
      newLandFromIslandId.value = originIslandId.value
    }
    if (
      !originList.some((island) => island.id === newLandToIslandId.value) ||
      newLandToIslandId.value === newLandFromIslandId.value
    ) {
      newLandToIslandId.value = other
    }
  }

  function otherOriginId(net: MultimodalNetwork, islandId: string): string {
    const candidates = net.islands.filter(
      (island) => island.isOrigin && island.id !== islandId,
    )
    return (
      candidates.find((island) => island.id === 'MV021001')?.id ??
      [...candidates].sort((a, b) => b.population - a.population)[0]?.id ??
      ''
    )
  }

  async function load(): Promise<void> {
    dataStatus.value = 'loading'
    fatalError.value = null
    let apiNote = ''
    try {
      network.value = await fetchNetwork('/api/network')
      dataSource.value = 'api'
      loadNote.value = null
    } catch (apiError) {
      apiNote = describeError(apiError)
      try {
        network.value = await fetchNetwork('/data/multimodal.json')
        dataSource.value = 'static'
        loadNote.value = `SQLite API unavailable (${apiNote}); using static prepared JSON.`
      } catch (staticError) {
        loadNote.value = `SQLite API: ${apiNote} Static JSON: ${describeError(staticError)}`
        const fixture: unknown = fixtureNetwork
        if (!isNetworkShape(fixture)) {
          dataStatus.value = 'error'
          fatalError.value = 'No prepared network and the bundled fixture network is invalid.'
          return
        }
        network.value = fixture
        dataSource.value = 'fixture'
      }
    }

    await loadGeojson()
    applyDefaults(network.value)
    dataStatus.value = 'ready'
    engineReady.value = getMultimodalEngine() !== null
    controlsReady.value = true
    // Deep link: ?view=underserved|recommended opens that map story (handy for demos).
    const requested = new URLSearchParams(window.location.search).get('view')
    if (requested === 'underserved' || requested === 'recommended') mapView.value = requested
    await loadFares()
    await Promise.all([recomputeMetrics(), recomputeJourney(), recomputeInterventions(), recomputeAccessReport()])
    recomputeSiting()
  }

  onMounted(() => {
    void load()
  })

  // ----------------------------------------------------------------- interfaces
  function selectOrigin(islandId: string): void {
    const island = origins.value.find((candidate) => candidate.id === islandId)
    if (!island) return
    originIslandId.value = island.id
  }

  function setDepartureFromInput(value: string): void {
    departureMinute.value = parseClock(value, departureMinute.value)
  }

  function setAddedDepartureFromInput(value: string): void {
    addedFirstDepartureMinute.value = parseClock(value, addedFirstDepartureMinute.value)
  }

  function resetScenario(): void {
    scenarioMode.value = 'baseline'
    scenarioAccessibility.value = null
  }

  function setScenarioMode(mode: ScenarioMode): void {
    scenarioMode.value = mode
    prepareScenarioMode(mode)
  }

  /** Pick defaults that actually touch the selected origin, without clobbering user input. */
  function prepareScenarioMode(mode: ScenarioMode): void {
    const net = network.value
    if (!net) return
    const serving = servicesServingIsland(net, originIslandId.value)
    const pattern = routePatterns.value.find((option) => option.routeId === addedRouteId.value)
    const patternTouchesOrigin =
      pattern?.serviceIds.some((serviceId) => serving.has(serviceId)) ?? false
    if (mode === 'add_trip') {
      if (!addedRouteId.value || !patternTouchesOrigin) {
        addedRouteId.value = defaultRoutePattern(net, originIslandId.value)
      }
      // A new first departure just after the requested time is the useful default:
      // it puts the added trip inside the modelled search window instead of before it.
      addedFirstDepartureMinute.value = Math.min(
        MINUTES_PER_DAY - 1,
        departureMinute.value + 15,
      )
    }
    const serviceTouchesOrigin =
      serving.has(cancelledServiceId.value) || serving.has(delayedServiceId.value)
    if (mode === 'cancel_service' && (!cancelledServiceId.value || !serviceTouchesOrigin)) {
      cancelledServiceId.value = defaultServiceId(net, originIslandId.value)
    }
    if (mode === 'delay_service' && (!delayedServiceId.value || !serviceTouchesOrigin)) {
      delayedServiceId.value = defaultServiceId(net, originIslandId.value)
    }
    if (mode === 'add_facility') {
      if (!newFacilityIslandId.value) newFacilityIslandId.value = originIslandId.value
      if (!newFacilityCategory.value) {
        newFacilityCategory.value = category.value || facilityCategoryOptions.value[0]?.id || ''
      }
      newFacilityKind.value = newFacilityCategory.value.startsWith('education')
        ? 'education'
        : 'health'
    }
    if (mode === 'add_sea_route') {
      if (!newSeaFromIslandId.value) newSeaFromIslandId.value = originIslandId.value
      if (!newSeaToIslandId.value || newSeaToIslandId.value === newSeaFromIslandId.value) {
        newSeaToIslandId.value = otherOriginId(net, newSeaFromIslandId.value)
      }
      newSeaDepartureMinute.value = Math.min(MINUTES_PER_DAY - 1, departureMinute.value + 15)
    }
    if (mode === 'add_land_link') {
      if (!newLandFromIslandId.value) newLandFromIslandId.value = originIslandId.value
      if (!newLandToIslandId.value || newLandToIslandId.value === newLandFromIslandId.value) {
        newLandToIslandId.value = otherOriginId(net, newLandFromIslandId.value)
      }
    }
  }

  // -------------------------------------------------------- network selection
  function setNetworkPreset(preset: NetworkPreset): void {
    networkPreset.value = preset
    if (preset === 'custom') return
    const flags = PRESET_FLAGS[preset]
    landEnabled.value = flags.land
    seaEnabled.value = flags.sea
    airEnabled.value = flags.air
  }

  function setModeEnabled(mode: keyof ModeFlags, enabled: boolean): void {
    if (mode === 'land') landEnabled.value = enabled
    else if (mode === 'sea') seaEnabled.value = enabled
    else airEnabled.value = enabled
    networkPreset.value = 'custom'
  }

  function setRouteEnabled(
    kind: RouteCatalogEntry['kind'],
    key: string,
    enabled: boolean,
  ): void {
    if (kind === 'ferry') {
      const next = new Set(disabledFerryRouteIds.value)
      if (enabled) next.delete(key)
      else next.add(key)
      disabledFerryRouteIds.value = [...next]
    } else {
      const next = new Set(disabledAirPairIds.value)
      if (enabled) next.delete(key)
      else next.add(key)
      disabledAirPairIds.value = [...next]
    }
  }

  function setAllRoutes(kind: RouteCatalogEntry['kind'], enabled: boolean): void {
    if (kind === 'ferry') {
      disabledFerryRouteIds.value = enabled ? [] : routeCatalog.value.ferries.map((entry) => entry.key)
    } else {
      disabledAirPairIds.value = enabled ? [] : routeCatalog.value.air.map((entry) => entry.key)
    }
  }

  function resetNetworkSelection(): void {
    networkPreset.value = 'multimodal'
    landEnabled.value = true
    seaEnabled.value = true
    airEnabled.value = true
    disabledFerryRouteIds.value = []
    disabledAirPairIds.value = []
  }

  const simulatorValidationError = computed<string | null>(() => {
    if (scenarioMode.value === 'add_facility') {
      if (!newFacilityName.value.trim()) return 'Enter a facility name to activate this scenario.'
      if (!newFacilityIslandId.value) return 'Choose an island for the proposed facility.'
      if (!newFacilityCategory.value) return 'Choose an existing category for the proposed facility.'
    }
    if (scenarioMode.value === 'add_sea_route') {
      if (!newSeaFromIslandId.value || !newSeaToIslandId.value) return 'Choose both islands for the sea link.'
      if (newSeaFromIslandId.value === newSeaToIslandId.value) return 'A sea link needs two different islands.'
    }
    if (scenarioMode.value === 'add_land_link') {
      if (!newLandFromIslandId.value || !newLandToIslandId.value) return 'Choose both islands for the land link.'
      if (newLandFromIslandId.value === newLandToIslandId.value) return 'A land link needs two different islands.'
    }
    return null
  })

  return {
    // data
    dataStatus,
    dataSource,
    loadNote,
    fatalError,
    network,
    meta,
    populationScope,
    islandsGeojson,
    geojsonLoaded,
    engineReady,
    // controls
    originIslandId,
    category,
    departureMinute,
    includeEstimatedAir,
    threshold,
    origins,
    originGroups,
    categories,
    selectedOrigin,
    selectedCategory,
    routePatterns,
    serviceOptions,
    selectedRoutePattern,
    selectedRouteFirstDeparture,
    categoryGroups,
    facilityCategoryOptions,
    interventionCategories,
    categoryIsIntervention,
    // network selection
    networkPreset,
    landEnabled,
    seaEnabled,
    airEnabled,
    disabledFerryRouteIds,
    disabledAirPairIds,
    modeFlags,
    routeCatalog,
    enabledRouteCount,
    filterActive,
    allowedModes,
    hasInfrastructure,
    selectedOriginHasInfrastructure,
    selectedOriginFilteredOut,
    setNetworkPreset,
    setModeEnabled,
    setRouteEnabled,
    setAllRoutes,
    resetNetworkSelection,
    // intervention evidence
    interventionRows,
    interventionLoading,
    interventionError,
    // scenario
    scenarioMode,
    addedRouteId,
    addedFirstDepartureMinute,
    cancelledServiceId,
    delayedServiceId,
    newFacilityName,
    newFacilityKind,
    newFacilityCategory,
    newFacilityIslandId,
    newSeaFromIslandId,
    newSeaToIslandId,
    newSeaDepartureMinute,
    newSeaTripsPerDay,
    newSeaMinutes,
    newLandFromIslandId,
    newLandToIslandId,
    newLandMinutes,
    simulatorValidationError,
    scenarioActive,
    scenarioError,
    scenarioDescription,
    canResetScenario,
    setScenarioMode,
    resetScenario,
    // results
    baselineAccessibility,
    scenarioAccessibility,
    displayAccessibility,
    selectedOriginAccess,
    selectedOriginStatus,
    journey,
    journeyStatus,
    nextDayJourney,
    journeyLoading,
    journeyError,
    metricsLoading,
    metricsError,
    baselineSummary,
    scenarioSummary,
    unfilteredSummary,
    comparison,
    // map
    islandBands,
    routePaths,
    airportPoints,
    facilityPoints,
    regionSplit,
    // map stories
    mapView,
    impact,
    sitingRoutes,
    facilityType,
    dayOfWeek,
    evidenceLayers,
    traveller,
    siting,
    sitingError,
    underservedClasses,
    // island access report
    fares,
    accessReport,
    accessReportLoading,
    accessReportError,
    overnightMvr,
    // actions
    selectOrigin,
    setDepartureFromInput,
    setAddedDepartureFromInput,
    serviceLabel,
    DELAY_MINUTES,
  }
}

export type MultimodalStore = ReturnType<typeof useMultimodal>
