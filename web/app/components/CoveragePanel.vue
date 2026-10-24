<script setup lang="ts">
import { computed } from 'vue'
import type { NetworkMeta } from '../../shared/routing/types'
import { formatDate, formatPopulation } from '../utils/format'

const props = defineProps<{
  meta: NetworkMeta | null
  dataSource: 'live' | 'fixture'
  geojsonLoaded: boolean
  loadNote: string
}>()

// From the readiness plan: these residents are outside the 191-origin universe.
const HARBOUR_RESIDENTS = 1399
const NON_ADMIN_RESIDENTS = 66313

const isLive = computed(() => props.dataSource === 'live')

const population = computed(() => props.meta?.population ?? null)

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

const counts = computed(() => props.meta?.counts ?? null)

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
  <section class="mm-panel mm-coverage" aria-labelledby="mm-coverage-heading">
    <header class="mm-panel__head">
      <div>
        <h2 id="mm-coverage-heading" class="mm-panel__title">Coverage &amp; assumptions</h2>
        <p class="mm-panel__sub">
          What this prototype knows, what it estimates and what it deliberately leaves out.
        </p>
      </div>
      <span class="mm-tag" :class="isLive ? 'mm-tag--good' : 'mm-tag--warn'">
        {{ isLive ? 'Prepared data' : 'Fixture data' }}
      </span>
    </header>

    <div v-if="!meta" class="mm-empty" role="status">
      No network metadata is available yet.
    </div>

    <template v-else>
      <div class="mm-coverage-grid">
        <article class="mm-coverage-card">
          <h3>Population scope</h3>
          <template v-if="population">
            <p class="mm-coverage-card__value">
              {{ formatPopulation(population.origins) }}
              <span v-if="isLive">of {{ formatPopulation(population.republic2022) }}</span>
            </p>
            <p class="mm-muted" v-if="isLive">
              residents on {{ population.originCount }} origin islands, out of the
              {{ formatPopulation(population.republic2022) }} republic census total.
              {{ formatPopulation(omittedResidents) }} people outside administrative island
              rows are omitted from routing.
            </p>
            <p class="mm-muted" v-else>
              Fixture population, not the national {{ formatPopulation(515132) }} scope. The
              fixture exists to exercise the interface and router; it makes no real-world
              claims.
            </p>
            <p class="mm-muted">{{ populationNote }}</p>
          </template>
          <p v-else class="mm-muted">Population scope is not recorded in the metadata.</p>
        </article>

        <article class="mm-coverage-card">
          <h3>Facility precision</h3>
          <p>
            Island-level only (<code>location_precision = island</code>). The app reports
            physical access to a listed facility's island, not building coordinates, clinical
            services, opening hours, bed capacity or enrolment.
          </p>
          <p class="mm-muted">
            A facility dot marks an island centroid. Do not read it as a building location or
            catchment.
          </p>
        </article>

        <article class="mm-coverage-card">
          <h3>Reference-day assumption</h3>
          <p>
            Reference day <strong>{{ formatDate(meta.referenceDay) }}</strong>.
            {{ serviceDayAssumption }}
          </p>
          <p class="mm-muted">
            The optional next-day alternative repeats the same timetable once, 24 hours later.
            It is an assumption, never a date-specific calendar claim.
          </p>
        </article>

        <article class="mm-coverage-card">
          <h3>Sources &amp; snapshot</h3>
          <p>
            Prepared {{ formatDate(meta.generatedAt) }} · {{ meta.timezone }} · schema v{{ meta.schemaVersion }}.
            Timetables come from operator releases where available; air services use an
            estimated weekly-frequency model.
          </p>
          <p class="mm-muted" v-if="counts">
            {{ counts.islands }} islands · {{ counts.origins }} origins · {{ counts.stops }} stops
            · {{ counts.airports }} airports · {{ counts.ferryTrips }} ferry trips ·
            {{ counts.airServices }} air services · {{ counts.facilities }} facilities ·
            {{ counts.categories }} categories.
          </p>
          <p class="mm-muted" v-if="!geojsonLoaded">
            Island polygons were unavailable; the schematic uses projected centroids only.
          </p>
        </article>
      </div>

      <div class="mm-omitted" v-if="isLive && population">
        <h3>Who is outside the denominator</h3>
        <ul>
          <li>
            <strong>{{ formatPopulation(HARBOUR_RESIDENTS) }}</strong> harbour-area residents.
          </li>
          <li>
            <strong>{{ formatPopulation(NON_ADMIN_RESIDENTS) }}</strong> people on
            non-administrative islands.
          </li>
          <li>
            Census city total (211,908) includes wards that are not added on top of the four
            Greater Malé origin rows, avoiding double counting.
          </li>
        </ul>
        <p class="mm-muted">
          Missing coverage is not zero access. An island absent from this network may still
          have transport in reality.
        </p>
      </div>

      <details class="mm-assumptions" open>
        <summary>Model assumptions ({{ meta.assumptions.length }})</summary>
        <ul>
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

      <div v-if="meta.coverageNotes?.length" class="mm-notice mm-notice--info" role="note">
        <strong>Coverage notes</strong>
        <ul>
          <li v-for="note in meta.coverageNotes" :key="note">{{ note }}</li>
        </ul>
      </div>

      <p v-if="loadNote" class="mm-muted">{{ loadNote }}</p>
    </template>
  </section>
</template>
