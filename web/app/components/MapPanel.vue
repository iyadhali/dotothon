<script setup lang="ts">
import type { MapHighlight } from '../utils/routes'
import type { SitingResult } from '../../shared/routing/recommend'
import { computed, ref } from 'vue'
import type { FeatureCollection } from 'geojson'
import type { Island } from '../../shared/routing/types'
import type { IslandBandInfo } from '../utils/bands'
import type { AirportPoint, FacilityPoint, RoutePath } from '../utils/routes'
import { formatClock, formatDuration, formatPopulation } from '../utils/format'
import { pluralise } from '../utils/format'

const props = defineProps<{
  islands: Island[]
  bands: Record<string, IslandBandInfo>
  routes: RoutePath[]
  airports: AirportPoint[]
  facilities: FacilityPoint[]
  originIslandId: string
  originName: string
  categoryLabel: string
  departureMinute: number
  geojson: FeatureCollection | null
  metricsLoading: boolean
  hasMapboxToken: boolean
  filterActive?: boolean
  highlights?: MapHighlight[]
  mapView?: 'access' | 'underserved' | 'recommended'
  underserved?: Record<string, string>
  siting?: SitingResult | null
  thresholdMinutes?: number
}>()

const emit = defineEmits<{
  'select-origin': [islandId: string]
  'set-view': [view: 'access' | 'underserved' | 'recommended']
}>()

const STORIES = [
  { key: 'access', title: 'Current access', hint: 'Travel time to the nearest facility' },
  { key: 'underserved', title: 'Underserved', hint: 'Who is outside the threshold' },
  { key: 'recommended', title: 'Recommended sites', hint: 'Where a new facility helps most' },
] as const

const currentView = computed(() => props.mapView ?? 'access')

const UNDERSERVED_LEGEND = [
  { key: 'served', label: 'Within threshold', color: '#c9d6cf' },
  { key: 'over_threshold', label: 'Reachable, but slower', color: '#e0a03a' },
  { key: 'no_trip', label: 'No same-day trip', color: '#a8325e' },
  { key: 'no_data', label: 'No transport data', color: '#ffffff' },
] as const

const underservedTotals = computed(() => {
  const totals: Record<string, { islands: number; people: number }> = {}
  for (const island of props.islands) {
    if (!island.isOrigin) continue
    const cls = props.underserved?.[island.id]
    if (!cls) continue
    const entry = totals[cls] ?? { islands: 0, people: 0 }
    entry.islands += 1
    entry.people += island.population
    totals[cls] = entry
  }
  return totals
})

const outsidePeople = computed(() =>
  ['over_threshold', 'no_trip', 'no_data'].reduce((sum, key) => sum + (underservedTotals.value[key]?.people ?? 0), 0),
)

const view = ref<'mapbox' | 'schematic'>(props.hasMapboxToken ? 'mapbox' : 'schematic')
const fallbackReason = ref('')

function onFallback(reason: string): void {
  fallbackReason.value = reason
  view.value = 'schematic'
}

function onSelectOrigin(islandId: string): void {
  emit('select-origin', islandId)
}

const facilityPopulation = computed(() =>
  props.facilities.length === 0
    ? 'No facilities of this category'
    : `${pluralise(props.facilities.length, 'island')} · ${pluralise(
        props.facilities.reduce((sum, facility) => sum + facility.count, 0),
        'facility',
        'facilities',
      )} · island-level precision`,
)
</script>

<template>
  <section class="mm-panel mm-map-panel" aria-labelledby="mm-map-heading">
    <header class="mm-panel__head mm-map-panel__head">
      <div>
        <h2 id="mm-map-heading" class="mm-panel__title">Island access map</h2>
        <p v-if="currentView === 'underserved'" class="mm-panel__sub">
          <strong>{{ formatPopulation(outsidePeople) }}</strong> residents cannot reach a
          <strong>{{ categoryLabel }}</strong> within {{ thresholdMinutes }} min, leaving at
          <strong>{{ formatClock(departureMinute) }}</strong>. Circle size is population.
        </p>
        <p v-else-if="currentView === 'recommended'" class="mm-panel__sub">
          Islands where a new <strong>{{ categoryLabel }}</strong> would bring the most residents within
          {{ thresholdMinutes }} min, chosen one at a time.
        </p>
        <p v-else class="mm-panel__sub">
          <strong>{{ originName || 'Selected origin' }}</strong> →
          nearest <strong>{{ categoryLabel }}</strong> · departure
          <strong>{{ formatClock(departureMinute) }}</strong> · {{ facilityPopulation }}
        </p>
      </div>
      <div class="mm-map-panel__tools">
        <span v-if="view === 'mapbox'" class="mm-tag mm-tag--map">Mapbox basemap</span>
        <span v-else class="mm-tag mm-tag--schematic">Schematic</span>
        <div v-if="hasMapboxToken" class="mm-seg mm-seg--small" role="group" aria-label="Map renderer">
          <button
            type="button"
            class="mm-seg__btn"
            :class="{ 'is-active': view === 'mapbox' }"
            :aria-pressed="view === 'mapbox'"
            @click="view = 'mapbox'"
          >
            Basemap
          </button>
          <button
            type="button"
            class="mm-seg__btn"
            :class="{ 'is-active': view === 'schematic' }"
            :aria-pressed="view === 'schematic'"
            @click="view = 'schematic'"
          >
            Schematic
          </button>
        </div>
      </div>
    </header>

    <div class="mm-stories" role="tablist" aria-label="Map story">
      <button
        v-for="story in STORIES"
        :key="story.key"
        type="button"
        role="tab"
        class="mm-stories__tab"
        :class="{ 'is-active': currentView === story.key }"
        :aria-selected="currentView === story.key"
        @click="emit('set-view', story.key)"
      >
        <strong>{{ story.title }}</strong>
        <span>{{ story.hint }}</span>
      </button>
    </div>
    <p v-if="currentView !== 'access' && view === 'schematic'" class="mm-notice mm-notice--info" role="note">
      This story is drawn on the basemap view. Switch to Basemap to see it.
    </p>

    <p v-if="fallbackReason" class="mm-notice mm-notice--warn" role="alert">
      The basemap could not be drawn ({{ fallbackReason }}). Showing the token-free
      schematic map instead; travel-time colours and click-to-select origin still work.
    </p>

    <div class="mm-map-panel__frame">
      <ClientOnly>
        <MapboxChoropleth
          v-if="view === 'mapbox'"
          :islands="islands"
          :bands="bands"
          :routes="routes"
          :airports="airports"
          :facilities="facilities"
          :origin-island-id="originIslandId"
          :category-label="categoryLabel"
          :geojson="geojson"
          :highlights="highlights"
          :map-view="currentView"
          :underserved="underserved"
          :sites="siting?.sites ?? []"
          @select-origin="onSelectOrigin"
          @fallback="onFallback"
        />
        <template #fallback>
          <div class="mm-map-empty mm-map-empty--loading" role="status">
            Preparing the basemap…
          </div>
        </template>
      </ClientOnly>

      <SchematicMap
        v-if="view === 'schematic'"
        :islands="islands"
        :bands="bands"
        :routes="routes"
        :airports="airports"
        :facilities="facilities"
        :origin-island-id="originIslandId"
        :geojson="geojson"
        :category-label="categoryLabel"
        @select-origin="onSelectOrigin"
      />

      <div v-if="metricsLoading" class="mm-map-loading" role="status" aria-live="polite">
        <span class="mm-spinner" aria-hidden="true" />
        <div>
          <strong>Computing accessibility…</strong>
          <span>
            Travel times and bands update for every origin island. Map stays interactive.
          </span>
        </div>
      </div>
    </div>

    <MapLegend
      v-if="currentView === 'access'"
      :filter-active="filterActive" :bands="bands" :loading="metricsLoading" />

    <ul v-else-if="currentView === 'underserved'" class="mm-story-legend">
      <li v-for="item in UNDERSERVED_LEGEND" :key="item.key">
        <span class="mm-story-legend__swatch" :class="`is-${item.key}`" :style="{ backgroundColor: item.color }" />
        <span class="mm-story-legend__label">{{ item.label }}</span>
        <strong>{{ formatPopulation(underservedTotals[item.key]?.people ?? 0) }}</strong>
        <span class="mm-muted">{{ underservedTotals[item.key]?.islands ?? 0 }} islands</span>
      </li>
    </ul>

    <div v-else class="mm-sites">
      <p v-if="!siting" class="mm-muted">Ranking candidate islands…</p>
      <template v-else>
        <p class="mm-sites__summary">
          Today {{ formatPopulation(siting.coveredBefore) }} of {{ formatPopulation(siting.populationTotal) }}
          residents are within {{ siting.thresholdMinutes }} min.
          <template v-if="siting.sites.length">
            Five new sites would raise that to
            <strong>{{ formatPopulation(siting.sites.at(-1)?.coveredAfter ?? siting.coveredBefore) }}</strong>.
          </template>
          <template v-else>No single new site brings anyone else within the threshold.</template>
        </p>
        <ol class="mm-sites__list">
          <li v-for="site in siting.sites" :key="site.islandId">
            <button type="button" class="mm-sites__item" @click="onSelectOrigin(site.islandId)">
              <span class="mm-sites__rank">{{ site.rank }}</span>
              <span class="mm-sites__name">
                <strong>{{ site.name }}</strong>
                <span>{{ site.atollName }} · serves {{ site.newlyCoveredIslandIds.length }}
                  {{ site.newlyCoveredIslandIds.length === 1 ? 'island' : 'islands' }}</span>
              </span>
              <span class="mm-sites__gain">+{{ formatPopulation(site.gainPopulation) }}</span>
            </button>
          </li>
        </ol>
        <p class="mm-muted mm-sites__note">
          Greedy maximal coverage on the modelled network: each pick is the island that adds the most
          residents within the threshold, given the picks before it. Capacity, cost and staffing are not
          modelled. Green circles are islands newly covered.
        </p>
      </template>
    </div>

    <p class="mm-panel__foot">
      Reachable means a published or modelled connection to a listed facility's island on
      the reference day — not confirmed opening hours, available beds or enrolment.
      {{ formatPopulation(islands.filter((island) => island.isOrigin).length) }} origin
      islands shown.
    </p>
  </section>
</template>
