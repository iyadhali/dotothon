<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useMultimodal, type FacilityType, type MapView } from '../composables/useMultimodal'
import type { DestinationAccess } from '../../shared/routing/nearby'
import { formatClock, formatClockWithDay, formatDuration, formatPopulation } from '../utils/format'
import { buildLandPaths, journeyPaths, type Destination, type FacilityIsland, type JourneyPath } from '../utils/routes'
import { ACCESS_CLASSES, accessClassLabel, type AccessClass } from '../utils/classify'
import { EVIDENCE_LAYERS, journeyEvidence } from '#shared/routing/evidence'
import { TRAVELLERS } from '#shared/routing/cost'

const store = useMultimodal()
const {
  dataStatus,
  network,
  origins,
  routePaths,
  accessReport,
  accessReportLoading,
  facilityType,
  mapView,
  category,
  departureMinute,
  threshold,
  underservedClasses,
  siting,
  selectOrigin,
  dayOfWeek,
  evidenceLayers,
  traveller,
  impact,
  sitingRoutes,
} = store

/** Where-to-build: the proposed site in focus (null = all five). */
const focusRank = ref<number | null>(null)
let siteDeepLinkUsed = false
watch(siting, () => {
  // Deep link: ?view=recommended&site=2 opens once with that site in focus.
  const site = import.meta.client ? Number(new URLSearchParams(window.location.search).get('site')) : NaN
  if (!siteDeepLinkUsed && Number.isInteger(site) && site > 0) {
    siteDeepLinkUsed = true
    focusRank.value = site
  } else {
    focusRank.value = null
  }
})

const focusSite = computed(() => siting.value?.sites.find((site) => site.rank === focusRank.value) ?? null)
const shownSiteRoutes = computed(() =>
  sitingRoutes.value.filter((site) => focusRank.value === null || site.rank === focusRank.value),
)

const siteRoutePaths = computed(() => {
  const net = network.value
  if (!net || mapView.value !== 'recommended') return []
  return shownSiteRoutes.value.flatMap((site) =>
    site.routes.flatMap((route) =>
      route.journey
        ? journeyPaths(net, route.journey)
            .filter((path) => path.mode !== 'walk')
            .map((path) => ({ rank: site.rank, mode: path.mode, points: path.points, improves: route.improves === true }))
        : [],
    ),
  )
})

function beforeText(route: { beforeMinutes: number | null; beforeStatus: string | null }): string {
  return route.beforeMinutes !== null ? formatDuration(route.beforeMinutes) : 'over 3 h'
}

const siteLabels = computed<Destination[]>(() => {
  const net = network.value
  if (!net || focusRank.value === null) return []
  return shownSiteRoutes.value.flatMap((site) =>
    site.routes.flatMap((route) => {
      const island = net.islands.find((candidate) => candidate.id === route.originId)
      if (!island || route.minutes === null || !route.improves) return []
      return [{ islandId: island.id, lon: island.lon, lat: island.lat, label: `${island.name}\n${beforeText(route)} → ${formatDuration(route.minutes)}` }]
    }),
  )
})

function catchmentSize(rank: number): number {
  return sitingRoutes.value.find((site) => site.rank === rank)?.routes.length ?? 0
}
function fasterCount(rank: number): number {
  return sitingRoutes.value.find((site) => site.rank === rank)?.routes.filter((route) => route.improves).length ?? 0
}

function toggleSite(rank: number): void {
  focusRank.value = focusRank.value === rank ? null : rank
}

const impactMax = computed(() => Math.max(1, ...impact.value.map((step) => step.atollTotal)))
const pct = (value: number, total: number) => (total > 0 ? `${Math.round((100 * value) / total)}%` : '—')

const DAYS = ['Sat', 'Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri']

/** Which route networks are drawn on the map (display only; routing uses the Data menu). */
const showRoutes = ref({ sea: true, air: true, land: true })
const ROUTE_TOGGLES = [
  { key: 'sea', label: 'Sea' },
  { key: 'air', label: 'Air' },
  { key: 'land', label: 'Land' },
] as const
const visibleRoutes = computed(() =>
  routePaths.value.filter((route) => (route.mode === 'air' ? showRoutes.value.air : showRoutes.value.sea)),
)
const landPaths = computed(() => (network.value && showRoutes.value.land ? buildLandPaths(network.value) : []))
const layersOpen = ref(false)
/** `?map=svg` forces the token-free fallback map (also used when Mapbox / WebGL fails). */
const forceSvg = ref(false)
onMounted(() => {
  forceSvg.value = new URLSearchParams(window.location.search).get('map') === 'svg'
  const island = new URLSearchParams(window.location.search).get('island')
  if (island) {
    const match = origins.value.find((candidate) => candidate.name.toLowerCase() === island.toLowerCase())
    if (match) select(match.id)
  }
})
watch(origins, (list) => {
  const island = import.meta.client ? new URLSearchParams(window.location.search).get('island') : null
  if (island && !selectedId.value) {
    const match = list.find((candidate) => candidate.name.toLowerCase() === island.toLowerCase())
    if (match) select(match.id)
  }
})
const useSvg = computed(() => forceSvg.value || mapFailed.value !== '')

function toggleLayer(key: (typeof EVIDENCE_LAYERS)[number]['key']): void {
  evidenceLayers.value = evidenceLayers.value.includes(key)
    ? evidenceLayers.value.filter((item) => item !== key)
    : [...evidenceLayers.value, key]
}

function evidenceTags(destination: DestinationAccess) {
  return network.value ? journeyEvidence(network.value, destination.journey) : []
}

/** null = nothing selected: show the whole network. */
const selectedId = ref<string | null>(null)
const search = ref('')
const mapFailed = ref('')

const TYPES: { key: FacilityType; label: string }[] = [
  { key: 'all', label: 'All' },
  { key: 'health', label: 'Health' },
  { key: 'education', label: 'Education' },
]
const VIEWS: { key: MapView; label: string }[] = [
  { key: 'access', label: 'Access' },
  { key: 'underserved', label: 'Underserved' },
  { key: 'recommended', label: 'Where to build' },
]
const DEPARTURES = [6 * 60, 8 * 60, 14 * 60]
const SHORT: Record<string, string> = {
  health_any: 'Health centre',
  health_hospital: 'Hospital',
  health_regional_tertiary: 'Regional hospital',
  education_school: 'School',
  education_grade_11_12: 'Grade 11–12',
  education_higher_ed: 'Higher education',
}
/** The service the Underserved / Where-to-build views are computed for. */
const VIEW_CATEGORY: Record<FacilityType, string> = {
  all: 'health_hospital',
  health: 'health_hospital',
  education: 'education_grade_11_12',
}

watch(
  facilityType,
  (type) => {
    category.value = VIEW_CATEGORY[type]
  },
  { immediate: true },
)

const selected = computed(() => network.value?.islands.find((island) => island.id === selectedId.value) ?? null)

function select(islandId: string | null): void {
  selectedId.value = islandId
  if (islandId) selectOrigin(islandId)
}

const searchOpen = ref(false)
const searchIndex = ref(0)

/** Islands matching the query by island or atoll name; largest first when the query is empty. */
const matches = computed(() => {
  const query = search.value.trim().toLowerCase()
  const list = query
    ? origins.value.filter(
        (island) => island.name.toLowerCase().includes(query) || island.atollName.toLowerCase().includes(query),
      )
    : [...origins.value].sort((a, b) => b.population - a.population)
  return [...list]
    .sort((a, b) => Number(b.name.toLowerCase().startsWith(query)) - Number(a.name.toLowerCase().startsWith(query)))
    .slice(0, 8)
})

watch(search, () => {
  searchIndex.value = 0
  searchOpen.value = true
})

function pick(islandId: string): void {
  select(islandId)
  search.value = ''
  searchOpen.value = false
}

function onSearchKey(event: KeyboardEvent): void {
  if (event.key === 'ArrowDown') {
    event.preventDefault()
    searchOpen.value = true
    searchIndex.value = Math.min(searchIndex.value + 1, matches.value.length - 1)
  } else if (event.key === 'ArrowUp') {
    event.preventDefault()
    searchIndex.value = Math.max(searchIndex.value - 1, 0)
  } else if (event.key === 'Enter') {
    event.preventDefault()
    const choice = matches.value[searchIndex.value]
    if (choice) pick(choice.id)
  } else if (event.key === 'Escape') {
    searchOpen.value = false
  }
}

function onSearchBlur(): void {
  // Let a click on an option land before the list closes.
  setTimeout(() => (searchOpen.value = false), 150)
}

const facilityIslands = computed<FacilityIsland[]>(() => {
  const net = network.value
  if (!net) return []
  const islands = new Map(net.islands.map((island) => [island.id, island]))
  // "All" highlights key services (hospitals; grade 11-12 or higher education) because almost
  // every island has a health centre and a school. Health / Education show every facility.
  const KEY_HEALTH = ['health_hospital', 'health_regional_tertiary']
  const KEY_EDUCATION = ['education_grade_11_12', 'education_higher_ed']
  const byIsland = new Map<string, { health: number; education: number; major: boolean }>()
  for (const facility of net.facilities) {
    if (facility.serviceCategories?.length && !facility.categories.some((c) => !c.startsWith('service:'))) continue
    if (facilityType.value !== 'all' && facility.kind !== facilityType.value) continue
    const key = facility.categories.some((c) => (facility.kind === 'health' ? KEY_HEALTH : KEY_EDUCATION).includes(c))
    if (facilityType.value === 'all' && !key) continue
    const entry = byIsland.get(facility.islandId) ?? { health: 0, education: 0, major: false }
    entry[facility.kind] += 1
    entry.major = entry.major || key
    byIsland.set(facility.islandId, entry)
  }
  return [...byIsland.entries()].flatMap(([islandId, counts]) => {
    const island = islands.get(islandId)
    if (!island) return []
    const kind: FacilityIsland['kind'] = counts.health && counts.education ? 'both' : counts.health ? 'health' : 'education'
    return [{ islandId, lon: island.lon, lat: island.lat, kind, count: counts.health + counts.education, major: counts.major }]
  })
})

/** Nearest destination per service for the selected island. */
const rows = computed(() => {
  if (!selectedId.value) return []
  return accessReport.value.map((row) => ({
    category: row.category,
    label: SHORT[row.category] ?? row.category,
    status: row.status,
    best: row.destinations[0] ?? null,
  }))
})

const journeys = computed<JourneyPath[]>(() => {
  const net = network.value
  if (!net) return []
  return rows.value.flatMap((row) => (row.best && row.best.journey.elapsedMinutes > 0 ? journeyPaths(net, row.best.journey) : []))
})

const destinations = computed<Destination[]>(() => {
  const net = network.value
  if (!net) return []
  const merged = new Map<string, { labels: string[]; minutes: number }>()
  for (const row of rows.value) {
    const journey = row.best?.journey
    if (!journey || journey.elapsedMinutes === 0) continue
    const entry = merged.get(journey.destinationIslandId) ?? { labels: [], minutes: journey.elapsedMinutes }
    entry.labels.push(row.label)
    merged.set(journey.destinationIslandId, entry)
  }
  return [...merged.entries()].flatMap(([islandId, entry]) => {
    const island = net.islands.find((candidate) => candidate.id === islandId)
    if (!island) return []
    return [{ islandId, lon: island.lon, lat: island.lat, label: `${island.name}\n${entry.labels.join(' · ')} · ${formatDuration(entry.minutes)}` }]
  })
})

const facilityCount = computed(() => facilityIslands.value.reduce((sum, item) => sum + item.count, 0))

const underservedLegend = computed(() => {
  const totals: Record<AccessClass, number> = { served: 0, over_threshold: 0, no_trip: 0, no_data: 0 }
  for (const island of network.value?.islands ?? []) {
    const cls = underservedClasses.value[island.id]
    if (island.isOrigin && cls) totals[cls] += island.population
  }
  return ACCESS_CLASSES.map((key) => ({ key, label: accessClassLabel(key, threshold.value), value: totals[key] }))
})

function fare(destination: DestinationAccess): string {
  if (destination.journey.elapsedMinutes === 0) return 'On island'
  const value = destination.cost.knownMvr
  if (value === 0 && !destination.cost.complete) return 'Fare n/a'
  return `MVR ${Math.round(value).toLocaleString('en-US')}${destination.cost.complete ? '' : '+'}`
}

function modes(destination: DestinationAccess): string {
  const names: Record<string, string> = { ferry: 'Ferry', sea: 'Boat', air: 'Flight', road: 'Road', speedboat: 'Speedboat' }
  const list = destination.journey.modes.filter((mode) => mode !== 'walk').map((mode) => names[mode] ?? mode)
  return list.length ? list.join(' → ') : 'Walk'
}

function homeText(destination: DestinationAccess): string {
  if (destination.journey.elapsedMinutes === 0) return ''
  if (destination.sameDayReturn && destination.returnJourney) return `Home by ${formatClock(destination.returnJourney.arrivalMinute)}`
  return destination.returnJourney ? 'Overnight stay needed' : 'No return trip in data'
}
</script>

<template>
  <div class="am-app">
    <header class="am-bar">
      <div class="am-brand">
        <strong>Island Access Atlas</strong>
        <span>Maldives · health &amp; education access by ferry, boat and air</span>
      </div>
      <div class="am-controls">
        <div class="am-seg" role="group" aria-label="Facility type">
          <button
            v-for="item in TYPES"
            :key="item.key"
            type="button"
            :class="{ 'is-on': facilityType === item.key }"
            @click="facilityType = item.key"
          >
            {{ item.label }}
          </button>
        </div>
        <select v-model="dayOfWeek" class="am-select" aria-label="Day of week">
          <option v-for="day in DAYS" :key="day" :value="day">{{ day }}</option>
        </select>
        <select v-model.number="departureMinute" class="am-select" aria-label="Departure time">
          <option v-for="minute in DEPARTURES" :key="minute" :value="minute">Leave {{ formatClock(minute) }}</option>
        </select>
        <select v-model="traveller" class="am-select" aria-label="Traveller">
          <option v-for="item in TRAVELLERS" :key="item.key" :value="item.key">{{ item.label }}</option>
        </select>
        <div class="am-layers">
          <button type="button" class="am-select am-layers__btn" :aria-expanded="layersOpen" @click="layersOpen = !layersOpen">
            Data {{ evidenceLayers.length }}/{{ EVIDENCE_LAYERS.length }}
          </button>
          <div v-if="layersOpen" class="am-layers__menu">
            <label v-for="layer in EVIDENCE_LAYERS" :key="layer.key">
              <input type="checkbox" :checked="evidenceLayers.includes(layer.key)" @change="toggleLayer(layer.key)" />
              <span>{{ layer.label }}</span>
            </label>
            <p>Precedence: RTL, then MTCC 2023 where RTL does not run, then observed boats where no timetable exists.</p>
          </div>
        </div>
        <div class="am-search">
          <input
            v-model="search"
            type="search"
            placeholder="Find an island"
            aria-label="Find an island"
            role="combobox"
            aria-autocomplete="list"
            aria-controls="am-search-list"
            :aria-expanded="searchOpen && matches.length > 0"
            autocomplete="off"
            @focus="searchOpen = true"
            @blur="onSearchBlur"
            @keydown="onSearchKey"
          />
          <ul v-if="searchOpen && matches.length" id="am-search-list" class="am-search__list" role="listbox">
            <li
              v-for="(island, index) in matches"
              :key="island.id"
              role="option"
              :aria-selected="index === searchIndex"
              :class="{ 'is-active': index === searchIndex }"
              @mousedown.prevent="pick(island.id)"
              @mouseenter="searchIndex = index"
            >
              <span>{{ island.name }}</span>
              <small>{{ island.atollName }} · {{ formatPopulation(island.population) }}</small>
            </li>
          </ul>
        </div>
        <NuxtLink to="/details" class="am-link">Full analysis</NuxtLink>
      </div>
    </header>

    <main class="am-stage">
      <div v-if="dataStatus === 'loading'" class="am-loading">Loading network…</div>
      <ClientOnly v-else>
        <FallbackMap
          v-if="useSvg"
          :islands="network?.islands ?? []"
          :routes="visibleRoutes"
          :land-routes="landPaths"
          :facilities="facilityIslands"
          :selected-island-id="mapView === 'access' ? selectedId : null"
          :journeys="mapView === 'access' ? journeys : []"
          :destinations="mapView === 'access' ? destinations : []"
          :view="mapView"
          :underserved="underservedClasses"
          :sites="siting?.sites ?? []"
          :site-routes="siteRoutePaths"
          :site-labels="siteLabels"
          :focus-site-id="focusSite?.islandId ?? null"
          @select="select"
        />
        <MinimalMap
          v-else
          :islands="network?.islands ?? []"
          :routes="visibleRoutes"
          :land-routes="landPaths"
          :facilities="facilityIslands"
          :selected-island-id="mapView === 'access' ? selectedId : null"
          :journeys="mapView === 'access' ? journeys : []"
          :destinations="mapView === 'access' ? destinations : []"
          :view="mapView"
          :underserved="underservedClasses"
          :sites="siting?.sites ?? []"
          :site-routes="siteRoutePaths"
          :site-labels="siteLabels"
          :focus-site-id="focusSite?.islandId ?? null"
          @select="select"
          @fallback="(reason) => (mapFailed = reason)"
        />
      </ClientOnly>
      <p v-if="mapFailed" class="am-error">Basemap unavailable ({{ mapFailed }}); showing the offline map.</p>

      <div class="am-routes" role="group" aria-label="Show routes">
        <span>Show routes</span>
        <button
          v-for="item in ROUTE_TOGGLES"
          :key="item.key"
          type="button"
          :aria-pressed="showRoutes[item.key]"
          :class="[`is-${item.key}`, { 'is-on': showRoutes[item.key] }]"
          @click="showRoutes[item.key] = !showRoutes[item.key]"
        >
          <i aria-hidden="true" /> {{ item.label }}
        </button>
      </div>

      <div class="am-views" role="tablist" aria-label="Map view">
        <button
          v-for="item in VIEWS"
          :key="item.key"
          type="button"
          role="tab"
          :aria-selected="mapView === item.key"
          :class="{ 'is-on': mapView === item.key }"
          @click="mapView = item.key"
        >
          {{ item.label }}
        </button>
      </div>

      <!-- Legend / context, bottom-left -->
      <div class="am-legend">
        <template v-if="mapView === 'access'">
          <template v-if="facilityType === 'all'">
            <span><i class="dot health" /> Hospital</span>
            <span><i class="dot education" /> Grade 11–12 / higher ed</span>
            <span><i class="dot both" /> Both</span>
          </template>
          <span v-else-if="facilityType === 'health'"><i class="dot health" /> Health facility (large = hospital)</span>
          <span v-else><i class="dot education" /> School (large = grade 11–12 / higher ed)</span>
          <span v-if="showRoutes.sea"><i class="line ferry" /> Ferry / boat</span>
          <span v-if="showRoutes.air"><i class="line air" /> Flight</span>
          <span v-if="showRoutes.land"><i class="line land" /> Road link</span>
        </template>
        <template v-else-if="mapView === 'underserved'">
          <strong class="am-legend__title">{{ SHORT[category] ?? 'Facility' }}, leaving {{ formatClock(departureMinute) }}</strong>
          <span v-for="item in underservedLegend" :key="item.key">
            <i class="dot" :class="item.key" /> {{ item.label }} <b>{{ formatPopulation(item.value) }}</b>
          </span>
        </template>
        <template v-else>
          <span><i class="dot site" /> Proposed site</span>
          <span><i class="line route-new" /> Faster than today</span>
          <span><i class="line route-same" /> Could also use it</span>
        </template>
      </div>

      <!-- Right panel -->
      <aside v-if="mapView === 'access' && selected" class="am-panel" aria-live="polite">
        <div class="am-panel__head">
          <div>
            <h2>{{ selected.name }}</h2>
            <p>{{ selected.atollName }} · {{ formatPopulation(selected.population) }} residents</p>
          </div>
          <button type="button" class="am-close" aria-label="Clear selection" @click="select(null)">×</button>
        </div>
        <p v-if="accessReportLoading && !rows.length" class="am-muted">Planning trips…</p>
        <ul class="am-list">
          <li v-for="row in rows" :key="row.category">
            <div class="am-row__top">
              <span class="am-row__label">{{ row.label }}</span>
              <span v-if="row.best" class="am-row__time">
                {{ row.best.journey.elapsedMinutes === 0 ? 'Here' : formatDuration(row.best.journey.elapsedMinutes) }}
              </span>
            </div>
            <template v-if="row.best">
              <div class="am-row__place">{{ row.best.journey.destinationIslandName }}</div>
              <div v-if="row.best.journey.elapsedMinutes > 0" class="am-row__meta">
                {{ modes(row.best) }} · arrive {{ formatClockWithDay(row.best.journey.arrivalMinute) }}
              </div>
              <div class="am-row__facts">
                <span>{{ fare(row.best) }}</span>
                <span v-if="homeText(row.best)" :class="row.best.sameDayReturn ? 'ok' : 'warn'">{{ homeText(row.best) }}</span>
              </div>
              <div v-if="evidenceTags(row.best).length" class="am-row__tags">
                <span v-for="tag in evidenceTags(row.best)" :key="tag.key" :class="tag.verified ? 'is-verified' : 'is-estimated'">
                  {{ tag.tag }}
                </span>
              </div>
            </template>
            <div v-else class="am-row__meta">
              {{ row.status === 'no_origin_access' ? 'No transport data for this island' : 'No same-day connection' }}
            </div>
          </li>
        </ul>
        <p class="am-foot">
          One-way fares for {{ TRAVELLERS.find((t) => t.key === traveller)?.label.toLowerCase() }}
          ({{ TRAVELLERS.find((t) => t.key === traveller)?.note.toLowerCase() }}). {{ dayOfWeek }} timetable. Transfers allow 15 min
          to board a ferry, 45 min to check in (60 at Velana) and 10 min to change mode.
        </p>
      </aside>

      <aside v-else-if="mapView === 'access'" class="am-hint">
        <strong class="am-hint__title">What boats and flights add</strong>
        <span class="am-hint__sub">
          Atoll residents (outside Greater Malé) who can reach a
          {{ (SHORT[category] ?? 'facility').toLowerCase() }} the same day · {{ dayOfWeek }}, leave
          {{ formatClock(departureMinute) }}
        </span>
        <ul class="am-impact">
          <li v-for="step in impact" :key="step.label">
            <span class="am-impact__label">{{ step.label }}</span>
            <span class="am-impact__bar"><i :style="{ width: `${(100 * step.atollReachable) / impactMax}%` }" /></span>
            <span class="am-impact__value">{{ pct(step.atollReachable, step.atollTotal) }}</span>
          </li>
        </ul>
        <span v-if="impact.length === 3" class="am-hint__sub">
          +{{ formatPopulation(impact[2]!.atollReachable - impact[0]!.atollReachable) }} atoll residents reached beyond
          road-only (national {{ pct(impact[0]!.reachable, impact[0]!.total) }} →
          {{ pct(impact[2]!.reachable, impact[2]!.total) }}). Click an island to see its routes, time and fare.
        </span>
      </aside>

      <aside v-else-if="mapView === 'recommended'" class="am-panel">
        <div class="am-panel__head">
          <div>
            <h2>Where to build next</h2>
            <p>New {{ (SHORT[category] ?? 'facility').toLowerCase() }}: most residents brought within {{ threshold }} min</p>
          </div>
        </div>
        <ol v-if="siting" class="am-sites">
          <li v-for="site in siting.sites" :key="site.islandId" :class="{ 'is-focus': focusRank === site.rank }">
            <button type="button" class="am-site__btn" :aria-pressed="focusRank === site.rank" @click="toggleSite(site.rank)">
              <span class="am-rank">{{ site.rank }}</span>
              <span class="am-site__name">{{ site.name }}<small>{{ site.atollName }} · reached from {{ catchmentSize(site.rank) }} island{{ catchmentSize(site.rank) === 1 ? '' : 's' }}, faster for {{ fasterCount(site.rank) }}</small></span>
              <span class="am-site__gain">+{{ formatPopulation(site.gainPopulation) }}</span>
            </button>
            <ul v-if="focusRank === site.rank" class="am-site__routes">
              <li
                v-for="route in sitingRoutes.find((s) => s.rank === site.rank)?.routes ?? []"
                :key="route.originId"
                :class="{ 'is-same': !route.improves }"
              >
                <span>{{ route.originName }}</span>
                <span class="am-site__change">
                  <template v-if="route.improves">
                    <s>{{ beforeText(route) }}</s> → <b>{{ formatDuration(route.minutes ?? 0) }}</b>
                  </template>
                  <template v-else>{{ formatDuration(route.minutes ?? 0) }} · already {{ beforeText(route) }}</template>
                </span>
              </li>
            </ul>
          </li>
        </ol>
        <p v-if="siting && focusRank === null" class="am-muted">
          Green routes: islands that could reach each new site within 3 h (best departure of the day). Bright = faster than any
          hospital today. Click a site to fly to it.
        </p>
        <p v-if="siting" class="am-foot">
          {{ formatPopulation(siting.coveredBefore) }} →
          {{ formatPopulation(siting.sites.at(-1)?.coveredAfter ?? siting.coveredBefore) }} residents within
          {{ threshold }} min. Capacity and cost not modelled.
        </p>
      </aside>
    </main>
  </div>
</template>

<style>
.am-app {
  --am-text: #0f172a;
  --am-muted: #64748b;
  --am-line: #e2e8f0;
  --am-accent: #2563eb;
  position: fixed;
  inset: 0;
  display: flex;
  flex-direction: column;
  background: #ffffff;
  color: var(--am-text);
  font-family: Inter, ui-sans-serif, system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif;
  font-size: 14px;
}
.am-app h2 {
  font-family: inherit;
}
.am-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 10px 20px;
  border-bottom: 1px solid var(--am-line);
  flex-wrap: wrap;
}
.am-brand strong {
  display: block;
  font-size: 15px;
  font-weight: 600;
  letter-spacing: -0.01em;
}
.am-brand span {
  font-size: 12px;
  color: var(--am-muted);
}
.am-controls {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}
.am-seg,
.am-views {
  display: inline-flex;
  padding: 3px;
  border: 1px solid var(--am-line);
  border-radius: 8px;
  background: #f8fafc;
}
.am-seg button,
.am-views button {
  border: 0;
  background: transparent;
  padding: 5px 12px;
  border-radius: 6px;
  font: inherit;
  font-size: 13px;
  color: var(--am-muted);
  cursor: pointer;
}
.am-seg button.is-on,
.am-views button.is-on {
  background: #ffffff;
  color: var(--am-text);
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.12);
}
.am-select,
.am-search input {
  height: 32px;
  border: 1px solid var(--am-line);
  border-radius: 8px;
  padding: 0 10px;
  font: inherit;
  font-size: 13px;
  color: var(--am-text);
  background: #ffffff;
}
.am-search {
  position: relative;
}
.am-search input {
  width: 200px;
}
.am-search__list {
  position: absolute;
  top: calc(100% + 4px);
  right: 0;
  z-index: 20;
  width: 260px;
  margin: 0;
  padding: 4px;
  list-style: none;
  background: #ffffff;
  border: 1px solid var(--am-line);
  border-radius: 8px;
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.12);
}
.am-search__list li {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: 8px;
  padding: 7px 9px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
}
.am-search__list li small {
  font-size: 11px;
  color: var(--am-muted);
  white-space: nowrap;
}
.am-search__list li.is-active {
  background: #f1f5f9;
}
.am-layers {
  position: relative;
}
.am-layers__btn {
  cursor: pointer;
}
.am-layers__menu {
  position: absolute;
  top: calc(100% + 4px);
  right: 0;
  z-index: 20;
  width: 280px;
  padding: 10px 12px;
  background: #ffffff;
  border: 1px solid var(--am-line);
  border-radius: 8px;
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.12);
}
.am-layers__menu label {
  display: flex;
  gap: 8px;
  align-items: center;
  padding: 4px 0;
  font-size: 13px;
}
.am-layers__menu p {
  margin: 8px 0 0;
  font-size: 11px;
  color: var(--am-muted);
}
.am-row__tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-top: 6px;
}
.am-row__tags span {
  font-size: 10.5px;
  padding: 1px 6px;
  border-radius: 999px;
  border: 1px solid var(--am-line);
}
.am-row__tags .is-verified {
  color: #0369a1;
  border-color: #bae6fd;
  background: #f0f9ff;
}
.am-row__tags .is-estimated {
  color: #92400e;
  border-color: #fde68a;
  background: #fffbeb;
}
.am-link {
  font-size: 13px;
  color: var(--am-accent);
  text-decoration: none;
}
.am-link:hover {
  text-decoration: underline;
}
.am-stage {
  position: relative;
  flex: 1;
  min-height: 0;
  margin: 0;
  padding: 0;
  max-width: none;
}
.am-map {
  position: absolute;
  inset: 0;
}
.am-loading,
.am-error {
  position: absolute;
  top: 16px;
  left: 16px;
  margin: 0;
  color: var(--am-muted);
}
.am-views {
  position: absolute;
  top: 16px;
  left: 16px;
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.1);
  background: #ffffff;
}
.am-legend {
  position: absolute;
  left: 16px;
  bottom: 24px;
  display: flex;
  flex-direction: column;
  gap: 5px;
  padding: 10px 12px;
  background: rgba(255, 255, 255, 0.94);
  border: 1px solid var(--am-line);
  border-radius: 8px;
  font-size: 12px;
  color: var(--am-muted);
}
.am-legend b {
  color: var(--am-text);
  font-weight: 600;
  margin-left: 4px;
  font-variant-numeric: tabular-nums;
}
.am-legend__title {
  color: var(--am-text);
  font-weight: 600;
  margin-bottom: 2px;
}
.am-legend span {
  display: flex;
  align-items: center;
  gap: 7px;
}
.dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  display: inline-block;
  border: 1px solid #ffffff;
  box-shadow: 0 0 0 1px rgba(15, 23, 42, 0.15);
}
.dot.health { background: #e11d48; }
.dot.education { background: #2563eb; }
.dot.both { background: #7c3aed; }
.dot.served { background: #cbd5e1; }
.dot.over_threshold { background: #f59e0b; }
.dot.no_trip { background: #dc2626; }
.dot.no_data { background: #ffffff; box-shadow: 0 0 0 1.4px #64748b; }
.dot.site { background: #0f172a; }
.dot.covered { background: #16a34a; }
.line {
  width: 18px;
  height: 0;
  display: inline-block;
  border-top: 2px solid #94a3b8;
}
.line.air {
  border-top: 2px dashed #a5b4fc;
}
.line.route-new {
  border-top: 3px solid #16a34a;
  box-shadow: 0 0 6px rgba(22, 163, 74, 0.6);
}
.line.route-same {
  border-top: 2px solid #86efac;
}
.line.land {
  border-top: 2.5px solid #334155;
}
.am-routes {
  position: absolute;
  top: 60px;
  left: 16px;
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 3px 4px 3px 10px;
  background: #ffffff;
  border: 1px solid var(--am-line);
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.1);
  font-size: 12px;
  color: var(--am-muted);
}
.am-routes button {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  border: 0;
  background: transparent;
  padding: 4px 9px;
  border-radius: 6px;
  font: inherit;
  font-size: 12px;
  color: var(--am-muted);
  cursor: pointer;
}
.am-routes button i {
  width: 14px;
  height: 0;
  border-top: 2px solid currentColor;
  opacity: 0.5;
}
.am-routes button.is-sea i { border-top-color: #0284c7; }
.am-routes button.is-air i { border-top: 2px dashed #7c3aed; }
.am-routes button.is-land i { border-top: 2.5px solid #334155; }
.am-routes button.is-on {
  background: #f1f5f9;
  color: var(--am-text);
}
.am-routes button.is-on i {
  opacity: 1;
}
.am-panel,
.am-hint {
  position: absolute;
  top: 16px;
  right: 16px;
  width: 340px;
  max-height: calc(100% - 32px);
  overflow-y: auto;
  background: #ffffff;
  border: 1px solid var(--am-line);
  border-radius: 10px;
  box-shadow: 0 4px 16px rgba(15, 23, 42, 0.08);
}
.am-hint {
  padding: 12px 14px;
  font-size: 13px;
  color: var(--am-text);
}
.am-hint__title {
  display: block;
  font-size: 13px;
  font-weight: 600;
}
.am-hint__sub {
  display: block;
  margin-top: 4px;
  font-size: 12px;
  color: var(--am-muted);
}
.am-impact {
  list-style: none;
  margin: 10px 0 6px;
  padding: 0;
  display: grid;
  gap: 6px;
}
.am-impact li {
  display: grid;
  grid-template-columns: 112px 1fr 38px;
  align-items: center;
  gap: 8px;
  font-size: 12px;
}
.am-impact__bar {
  height: 8px;
  background: #f1f5f9;
  border-radius: 999px;
  overflow: hidden;
}
.am-impact__bar i {
  display: block;
  height: 100%;
  background: var(--am-accent);
  border-radius: 999px;
}
.am-impact__value {
  text-align: right;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
}
.am-panel__head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 14px 16px 10px;
  border-bottom: 1px solid var(--am-line);
}
.am-panel__head h2 {
  margin: 0;
  font-size: 17px;
  font-weight: 600;
  letter-spacing: -0.01em;
}
.am-panel__head p {
  margin: 2px 0 0;
  font-size: 12px;
  color: var(--am-muted);
}
.am-close {
  border: 0;
  background: transparent;
  font-size: 20px;
  line-height: 1;
  color: var(--am-muted);
  cursor: pointer;
}
.am-list,
.am-sites {
  list-style: none;
  margin: 0;
  padding: 0;
}
.am-list li {
  padding: 11px 16px;
  border-bottom: 1px solid var(--am-line);
}
.am-row__top {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
}
.am-row__label {
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  color: var(--am-muted);
}
.am-row__time {
  font-weight: 600;
  font-variant-numeric: tabular-nums;
}
.am-row__place {
  margin-top: 2px;
  font-weight: 600;
}
.am-row__meta {
  margin-top: 2px;
  font-size: 12px;
  color: var(--am-muted);
}
.am-row__facts {
  display: flex;
  gap: 10px;
  margin-top: 6px;
  font-size: 12px;
  font-variant-numeric: tabular-nums;
}
.am-row__facts .ok { color: #15803d; }
.am-row__facts .warn { color: #b45309; }
.am-foot,
.am-muted {
  margin: 0;
  padding: 10px 16px 14px;
  font-size: 11px;
  color: var(--am-muted);
}
.am-sites > li {
  border-bottom: 1px solid var(--am-line);
}
.am-sites > li.is-focus {
  background: #f0fdf4;
}
.am-site__btn {
  width: 100%;
  display: grid;
  grid-template-columns: 26px 1fr auto;
  align-items: center;
  gap: 10px;
  padding: 9px 16px;
  border: 0;
  background: transparent;
  font: inherit;
  color: inherit;
  text-align: left;
  cursor: pointer;
}
.am-site__btn:hover {
  background: #f8fafc;
}
.am-site__routes {
  list-style: none;
  margin: 0;
  padding: 0 16px 10px 52px;
  display: grid;
  gap: 4px;
  font-size: 12px;
}
.am-site__routes li {
  display: flex;
  justify-content: space-between;
  gap: 8px;
}
.am-site__change {
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}
.am-site__change s {
  color: var(--am-muted);
}
.am-site__change b {
  color: #15803d;
}
.am-site__routes li.is-same {
  color: var(--am-muted);
}
.am-rank {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: #0f172a;
  color: #ffffff;
  display: grid;
  place-items: center;
  font-size: 12px;
  font-weight: 600;
}
.am-site__name small {
  display: block;
  font-size: 11px;
  color: var(--am-muted);
}
.am-site__gain {
  font-weight: 600;
  color: #15803d;
  font-variant-numeric: tabular-nums;
}
.am-popup .mapboxgl-popup-content {
  padding: 6px 9px;
  border-radius: 6px;
  font: 12px Inter, ui-sans-serif, system-ui, sans-serif;
  color: #0f172a;
  box-shadow: 0 2px 8px rgba(15, 23, 42, 0.15);
}
.am-popup strong {
  display: block;
}
.am-popup span {
  color: #64748b;
}
@media (max-width: 760px) {
  .am-panel,
  .am-hint {
    top: auto;
    bottom: 12px;
    left: 12px;
    right: 12px;
    width: auto;
    max-height: 55%;
  }
  .am-legend {
    display: none;
  }
  .am-search input {
    width: 140px;
  }
}
</style>
