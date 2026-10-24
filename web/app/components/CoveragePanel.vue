<script setup lang="ts">
import { computed } from 'vue'
import type { NetworkMeta } from '../../shared/routing/types'
import { formatDate, formatPopulation } from '../utils/format'

const props = defineProps<{
  meta: NetworkMeta | null
  dataSource: 'api' | 'static' | 'fixture'
  geojsonLoaded: boolean
  loadNote: string
}>()

const HARBOUR_RESIDENTS = 1399
const NON_ADMIN_RESIDENTS = 66313

const isLive = computed(() => props.dataSource === 'api' || props.dataSource === 'static')
const population = computed(() => props.meta?.population ?? null)
const counts = computed(() => props.meta?.counts ?? null)

const omittedResidents = computed(() => {
  if (!population.value) return 0
  return population.value.republic2022 - population.value.origins
})

const populationNote = computed(
  () =>
    population.value?.note ??
    'Origin islands only; the republic census total is not the routing denominator.',
)

const serviceDayAssumption = computed(
  () =>
    props.meta?.serviceDayAssumption ??
    'Timetables are assumed to repeat on the reference weekday; date-specific calendars are unavailable.',
)

function confidenceTone(confidence: string): string {
  switch (confidence) {
    case 'source':
      return 'mm-confidence--verified'
    case 'estimated':
      return 'mm-confidence--estimated'
    default:
      return 'mm-confidence--assumption'
  }
}
</script>

<template>
  <section class="mm-panel mm-data" aria-labelledby="mm-coverage-heading">
    <header class="mm-panel__head">
      <div>
        <h2 id="mm-coverage-heading" class="mm-panel__title">Data &amp; coverage</h2>
        <p class="mm-panel__sub mm-one-line">
          {{ isLive ? 'Prepared network' : 'Bundled fixture' }} · island-level precision
        </p>
      </div>
      <span class="mm-tag" :class="isLive ? 'mm-tag--good' : 'mm-tag--warn'">
        {{ isLive ? 'Prepared data' : 'Fixture data' }}
      </span>
    </header>

    <div v-if="!meta" class="mm-empty" role="status">No network metadata yet.</div>

    <template v-else>
      <div class="mm-chip-row" aria-label="Coverage snapshot">
        <span class="mm-chip mm-chip--strong">
          {{ population ? formatPopulation(population.origins) : '—' }} routed residents
        </span>
        <span v-if="population" class="mm-chip">
          {{ population.originCount }} origin islands
        </span>
        <span v-if="counts" class="mm-chip">{{ counts.facilities }} facilities</span>
        <span v-if="counts" class="mm-chip">{{ counts.islands }} islands</span>
        <span class="mm-chip">ref {{ formatDate(meta.referenceDay) }}</span>
        <span class="mm-chip">island precision</span>
      </div>

      <p class="mm-data__line">
        <template v-if="isLive && population">
          {{ formatPopulation(omittedResidents) }} residents outside administrative island rows
          are omitted · missing coverage is not zero access.
        </template>
        <template v-else>
          Fixture values exercise the interface; they are not national figures.
        </template>
      </p>

      <div class="mm-details-grid">
        <details class="mm-data-details">
          <summary>Population scope</summary>
          <template v-if="population">
            <p>
              <strong>{{ formatPopulation(population.origins) }}</strong> residents on
              {{ population.originCount }} origin islands<template v-if="isLive">
                of the {{ formatPopulation(population.republic2022) }} republic census total</template
              >.
            </p>
            <p class="mm-muted">{{ populationNote }}</p>
            <p v-if="isLive" class="mm-muted">
              Omitted from routing: {{ formatPopulation(HARBOUR_RESIDENTS) }} harbour-area
              residents; {{ formatPopulation(NON_ADMIN_RESIDENTS) }} people on non-administrative
              islands. Census city total (211,908) includes wards not added on top of the four
              Greater Malé origin rows, avoiding double counting.
            </p>
            <p v-else class="mm-muted">
              Fixture population, not the national {{ formatPopulation(515132) }} scope.
            </p>
          </template>
          <p v-else class="mm-muted">Population scope is not recorded in the metadata.</p>
        </details>

        <details class="mm-data-details">
          <summary>Facilities, sources &amp; snapshot</summary>
          <p>
            Facilities are island-level only (<code>location_precision = island</code>): the app
            reports physical access to a listed facility's island, not building coordinates,
            clinical services, opening hours, bed capacity or enrolment. A dot marks an island
            centroid, not a building.
          </p>
          <p class="mm-muted">
            Prepared {{ formatDate(meta.generatedAt) }} · {{ meta.timezone }} · schema v{{
              meta.schemaVersion
            }}. Timetables come from operator releases where available; air services use an
            estimated weekly-frequency model.
          </p>
          <p v-if="counts" class="mm-muted">
            {{ counts.islands }} islands · {{ counts.origins }} origins · {{ counts.stops }} stops ·
            {{ counts.airports }} airports · {{ counts.ferryTrips }} ferry trips ·
            {{ counts.airServices }} air services · {{ counts.facilities }} facilities ·
            {{ counts.categories }} categories.
          </p>
          <p v-if="!geojsonLoaded" class="mm-muted">
            Island polygons were unavailable; the schematic uses projected centroids only.
          </p>
        </details>

        <details class="mm-data-details">
          <summary>Reference-day assumption</summary>
          <p>
            Reference day <strong>{{ formatDate(meta.referenceDay) }}</strong>.
            {{ serviceDayAssumption }}
          </p>
          <p class="mm-muted">
            The optional next-day alternative repeats the same timetable once, 24 hours later. It
            is an assumption, never a date-specific calendar claim.
          </p>
        </details>

        <details class="mm-data-details">
          <summary>Model assumptions ({{ meta.assumptions.length }})</summary>
          <ul class="mm-assumption-list">
            <li v-for="assumption in meta.assumptions" :key="assumption.id">
              <div class="mm-assumption__head">
                <code>{{ assumption.id }}</code>
                <span class="mm-confidence" :class="confidenceTone(assumption.confidence)">
                  {{ assumption.confidence }}
                </span>
              </div>
              <p>{{ assumption.value }}</p>
              <p class="mm-muted">Source: {{ assumption.source }}</p>
              <p v-if="assumption.note" class="mm-muted">{{ assumption.note }}</p>
            </li>
          </ul>
        </details>

        <details v-if="meta.coverageNotes?.length" class="mm-data-details mm-data-details--wide">
          <summary>Coverage notes ({{ meta.coverageNotes.length }})</summary>
          <ul class="mm-note-list">
            <li v-for="note in meta.coverageNotes" :key="note">{{ note }}</li>
          </ul>
        </details>

        <details v-if="loadNote" class="mm-data-details mm-data-details--wide">
          <summary>Data source note</summary>
          <p class="mm-muted">{{ loadNote }}</p>
        </details>
      </div>
    </template>
  </section>
</template>
