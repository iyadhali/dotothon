<script setup lang="ts">
import type { MapHighlight } from '../utils/routes'
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
}>()

const emit = defineEmits<{ 'select-origin': [islandId: string] }>()

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
        <p class="mm-panel__sub">
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
          :filter-active="filterActive" :bands="bands" :loading="metricsLoading" />

    <p class="mm-panel__foot">
      Reachable means a published or modelled connection to a listed facility's island on
      the reference day — not confirmed opening hours, available beds or enrolment.
      {{ formatPopulation(islands.filter((island) => island.isOrigin).length) }} origin
      islands shown.
    </p>
  </section>
</template>
