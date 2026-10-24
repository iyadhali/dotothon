<script setup lang="ts">
import { computed } from 'vue'
import type { MultimodalStore } from '../composables/useMultimodal'
import type { DestinationAccess } from '../../shared/routing/nearby'
import { formatClock, formatClockWithDay, formatDuration } from '../utils/format'

/**
 * Click an island on the map → the nearest facilities per service it can actually reach,
 * with door-to-door time, the resident fare, and whether the trip home works the same day.
 */
const props = defineProps<{ store: MultimodalStore }>()

const {
  selectedOrigin,
  categories,
  departureMinute,
  accessReport,
  accessReportLoading,
  accessReportError,
  overnightMvr,
  fares,
} = props.store

const labels = computed(() => new Map(categories.value.map((definition) => [definition.id, definition.label])))

const MODE_NAMES: Record<string, string> = {
  walk: 'Walk',
  road: 'Road',
  ferry: 'Ferry',
  sea: 'Boat',
  speedboat: 'Speedboat',
  air: 'Flight',
  ferry_transfer: 'Transfer',
}

function modes(destination: DestinationAccess): string {
  const list = destination.journey.modes.filter((mode) => mode !== 'walk')
  if (destination.journey.elapsedMinutes === 0) return 'On this island'
  return list.length ? list.map((mode) => MODE_NAMES[mode] ?? mode).join(' → ') : 'Walk'
}

function mvr(value: number): string {
  return `MVR ${Math.round(value).toLocaleString('en-US')}`
}

function oneWay(destination: DestinationAccess): string {
  if (destination.journey.elapsedMinutes === 0) return 'Free'
  const cost = destination.cost
  if (cost.knownMvr === 0 && !cost.complete) return 'Fare unknown'
  return `${mvr(cost.knownMvr)}${cost.complete ? '' : '+'}`
}

function roundTrip(destination: DestinationAccess): string {
  if (destination.journey.elapsedMinutes === 0) return 'Free'
  return `${mvr(destination.roundTripMvr)}${destination.roundTripPartial ? '+' : ''}`
}

function costConfidence(destination: DestinationAccess): string {
  const c = destination.cost.confidence
  if (c === 'free') return ''
  return c === 'sourced' ? 'Published fares' : c === 'estimated' ? 'Estimated fares' : 'Assumed fares'
}

function returnText(destination: DestinationAccess): string {
  if (destination.journey.elapsedMinutes === 0) return ''
  if (destination.sameDayReturn && destination.returnJourney) {
    return `Home by ${formatClock(destination.returnJourney.arrivalMinute)} the same day`
  }
  if (destination.returnJourney) {
    return `Overnight stay — earliest trip home arrives ${formatClockWithDay(destination.returnJourney.arrivalMinute)}`
  }
  return 'No trip home found in the timetable data (often a one-direction ferry record)'
}

const statusText: Record<string, string> = {
  not_reachable: 'No same-day connection from this island on the reference day.',
  no_origin_access: 'No transport link from this island in our data — a data gap, not proof there is no boat.',
  no_destination: 'No facility of this type in the data.',
}

const report = computed(() =>
  accessReport.value.map((row) => ({
    ...row,
    label: labels.value.get(row.category) ?? row.category,
  })),
)

const hasSeaFares = computed(() => Boolean(fares.value?.ferry))

function onOvernight(event: Event): void {
  const value = Number((event.target as HTMLInputElement).value)
  if (Number.isFinite(value) && value >= 0) overnightMvr.value = value
}
</script>

<template>
  <section class="mm-panel mm-access" aria-labelledby="mm-access-heading">
    <header class="mm-panel__head">
      <div>
        <h2 id="mm-access-heading" class="mm-panel__title">
          What can {{ selectedOrigin?.name ?? 'this island' }} reach?
        </h2>
        <p class="mm-panel__sub">
          Nearest facilities by service, leaving at {{ formatClock(departureMinute) }}. Click any island on the
          map to change the origin.
        </p>
      </div>
      <label class="mm-access__night">
        <span>Night away (MVR)</span>
        <input type="number" min="0" step="50" :value="overnightMvr" @change="onOvernight" />
      </label>
    </header>

    <div v-if="accessReportError" class="mm-notice mm-notice--warn" role="alert">{{ accessReportError }}</div>
    <div v-else-if="accessReportLoading && !report.length" class="mm-skeleton" role="status">
      <span class="mm-spinner" aria-hidden="true" /> Planning trips…
    </div>
    <div v-else-if="!selectedOrigin" class="mm-empty" role="status">Select an island on the map.</div>

    <div v-else class="mm-access__grid" :aria-busy="accessReportLoading">
      <article v-for="row in report" :key="row.category" class="mm-access__card">
        <h3 class="mm-subhead">{{ row.label }}</h3>
        <p v-if="!row.destinations.length" class="mm-access__status">
          {{ statusText[row.status] ?? 'No same-day trip.' }}
        </p>
        <ol v-else class="mm-access__list">
          <li v-for="destination in row.destinations" :key="destination.journey.destinationIslandId" class="mm-access__item">
            <div class="mm-access__top">
              <strong class="mm-access__place">{{ destination.journey.destinationIslandName }}</strong>
              <span class="mm-access__time">
                {{ destination.journey.elapsedMinutes === 0 ? 'Here' : formatDuration(destination.journey.elapsedMinutes) }}
              </span>
            </div>
            <p class="mm-access__facility">
              {{ destination.journey.destinationFacilityNames.slice(0, 2).join(' · ') || 'Facility on this island' }}
            </p>
            <p class="mm-access__route">
              {{ modes(destination) }}
              <template v-if="destination.journey.elapsedMinutes > 0">
                · arrive {{ formatClockWithDay(destination.journey.arrivalMinute) }}
                <span v-if="destination.journey.usesEstimatedAir" class="mm-tag">estimated flight times</span>
              </template>
            </p>
            <dl v-if="destination.journey.elapsedMinutes > 0" class="mm-access__costs">
              <div>
                <dt>One way</dt>
                <dd>{{ oneWay(destination) }}</dd>
              </div>
              <div>
                <dt>Round trip</dt>
                <dd>{{ roundTrip(destination) }}</dd>
              </div>
            </dl>
            <p
              v-if="destination.journey.elapsedMinutes > 0"
              class="mm-access__return"
              :class="destination.sameDayReturn ? 'is-ok' : 'is-warn'"
            >
              {{ returnText(destination) }}
            </p>
            <p v-if="costConfidence(destination)" class="mm-access__basis">{{ costConfidence(destination) }}</p>
          </li>
        </ol>
      </article>
    </div>

    <footer class="mm-access__foot">
      <p>
        Fares are full resident fares: RTL ferry gazette tariff, Maldivian domestic fares, Greater Malé taxi
        tariff.<span v-if="!hasSeaFares"> Ferry fares are not loaded yet.</span> A "+" means at least one leg
        has no fare data. Round trip adds a night away when the trip home is not possible the same day, after a
        2-hour appointment. Emergency transfers approved by Aasandha are free; people aged 65+, children under 3,
        and disabled people travel free on RTL ferries.
      </p>
    </footer>
  </section>
</template>
