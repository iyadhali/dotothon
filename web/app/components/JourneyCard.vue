<script setup lang="ts">
import { computed } from 'vue'
import type {
  CategoryDefinition,
  Island,
  Journey,
  OriginAccess,
  OriginAccessStatus,
} from '../../shared/routing/types'
import {
  formatClock,
  formatClockWithDay,
  formatDate,
  formatDuration,
  formatPopulation,
} from '../utils/format'

const props = defineProps<{
  origin: Island | null
  access: OriginAccess | null
  category: CategoryDefinition | null
  journey: Journey | null
  status?: OriginAccessStatus | null
  nextDayJourney: Journey | null
  loading: boolean
  error: string | null
  scenarioDescription: string
  scenarioActive: boolean
  referenceDay: string
  maxJourneyMinutes: number
  filteredOut?: boolean
}>()

const status = computed(() => props.status ?? props.access?.status ?? null)

const statusCopy = computed(() => {
  switch (status.value) {
    case 'no_origin_access':
      return props.filteredOut
        ? {
            title: 'No access under the current network selection',
            body: 'This island has physical access in the prepared network, but your Land/Sea/Air or route selection removes all of it. This is a user-selection state, not a coverage finding.',
            tone: 'info',
          }
        : {
            title: 'No physical access from this island',
            body: 'The prepared network has no walk, road, ferry-transfer or airport access edge from this origin island. This is a coverage gap, not proof that no transport exists.',
            tone: 'warn',
          }
    case 'no_destination':
      return {
        title: 'No destination in this category',
        body: 'No facility matching the selected category exists in the prepared data. Missing coverage is not zero access in the real world.',
        tone: 'info',
      }
    case 'not_reachable':
      return {
        title: 'No same-day itinerary',
        body: 'No connection reaches a listed destination island within the modelled day. The timetable, not geography alone, determines this.',
        tone: 'warn',
      }
    default:
      return null
  }
})

const journeyView = computed(() => props.journey ?? props.access?.journey ?? null)

const modeNames: Record<string, string> = {
  walk: 'Walk',
  road: 'Road',
  speedboat: 'Speedboat',
  ferry_transfer: 'Ferry transfer',
  ferry: 'Ferry',
  sea: 'Sea',
  air: 'Air',
}

function modeName(mode: string): string {
  return modeNames[mode] ?? mode
}

const breakdown = computed(() => {
  const entry = journeyView.value
  if (!entry) return []
  return [
    { key: 'access', label: 'Access', minutes: entry.accessMinutes, color: '#8a9a8c' },
    { key: 'wait', label: 'Wait', minutes: entry.waitMinutes, color: '#e3c477' },
    { key: 'ride', label: 'Ride', minutes: entry.rideMinutes, color: '#287c6f' },
    { key: 'transfer', label: 'Transfers', minutes: entry.transferMinutes, color: '#b36c48' },
  ].filter((part) => part.minutes > 0)
})

const totalBreakdownMinutes = computed(() =>
  breakdown.value.reduce((sum, part) => sum + part.minutes, 0),
)

function share(minutes: number): string {
  if (totalBreakdownMinutes.value <= 0) return '0%'
  return `${Math.max(2, Math.round((minutes / totalBreakdownMinutes.value) * 100))}%`
}

</script>

<template>
  <section class="mm-panel mm-journey" aria-labelledby="mm-journey-heading">
    <header class="mm-panel__head">
      <div>
        <h2 id="mm-journey-heading" class="mm-panel__title">
          Journey card
          <span v-if="scenarioActive" class="mm-tag mm-tag--scenario">Scenario</span>
        </h2>
        <p class="mm-panel__sub">
          Best itinerary from
          <strong>{{ origin?.name ?? '—' }}</strong>
          to the nearest
          <strong>{{ category?.label ?? 'destination' }}</strong>
          facility.
        </p>
      </div>
      <span
        v-if="journeyView"
        class="mm-confidence"
        :class="journeyView.serviceConfidence === 'verified' ? 'mm-confidence--verified' : 'mm-confidence--estimated'"
      >
        {{ journeyView.serviceConfidence === 'verified' ? 'Verified timetable' : 'Estimated service' }}
      </span>
    </header>

    <p v-if="scenarioActive && scenarioDescription" class="mm-notice mm-notice--scenario" role="note">
      Scenario in effect: {{ scenarioDescription }} User-defined scenarios are not observed
      services.
    </p>

    <div v-if="error" class="mm-notice mm-notice--warn" role="alert">
      Journey could not be computed: {{ error }}
    </div>

    <div v-else-if="loading" class="mm-skeleton" role="status">
      <span class="mm-spinner" aria-hidden="true" />
      <span>Computing the fastest itinerary…</span>
    </div>

    <div v-else-if="!origin" class="mm-empty" role="status">
      Choose an origin island to plan a journey.
    </div>

    <template v-else>
      <div v-if="statusCopy" class="mm-status" :class="`mm-status--${statusCopy.tone}`">
        <strong>{{ statusCopy.title }}</strong>
        <p>{{ statusCopy.body }}</p>
      </div>

      <div v-if="journeyView" class="mm-journey__summary">
        <div class="mm-journey__destination">
          <span class="mm-eyebrow">Destination</span>
          <h3>{{ journeyView.destinationIslandName }}</h3>
          <p v-if="journeyView.destinationFacilityNames.length > 0">
            {{ journeyView.destinationFacilityNames.join(', ') }}
          </p>
          <p v-else class="mm-muted">Facility names were not recorded for this destination.</p>
          <p class="mm-precision">
            Facilities are located at island level, not building level. This card reports
            physical access to a listed facility, not confirmed availability of its services.
          </p>
        </div>

        <dl class="mm-statgrid mm-statgrid--times">
          <div>
            <dt>Depart</dt>
            <dd>{{ formatClockWithDay(journeyView.departureMinute) }}</dd>
          </div>
          <div>
            <dt>Arrive</dt>
            <dd>{{ formatClockWithDay(journeyView.arrivalMinute) }}</dd>
          </div>
          <div>
            <dt>Elapsed</dt>
            <dd>{{ formatDuration(journeyView.elapsedMinutes) }}</dd>
          </div>
          <div>
            <dt>Transfers</dt>
            <dd>{{ journeyView.transfers }}</dd>
          </div>
          <div>
            <dt>Modes</dt>
            <dd>{{ journeyView.modes.map(modeName).join(' → ') || '—' }}</dd>
          </div>
          <div>
            <dt>Origin population</dt>
            <dd>{{ formatPopulation(origin.population) }}</dd>
          </div>
        </dl>
      </div>

      <p
        v-if="journeyView && journeyView.legs.length === 0"
        class="mm-notice mm-notice--info"
        role="note"
      >
        The origin island already hosts a facility in this category, so the modelled journey
        needs no travel: zero minutes. This is physical access to a listed facility, not a
        booking or a confirmed service.
      </p>

      <div v-if="journeyView" class="mm-breakdown">
        <h3 class="mm-subhead">Where the time goes</h3>
        <div class="mm-breakdown__bar" aria-hidden="true">
          <span
            v-for="part in breakdown"
            :key="part.key"
            :style="{ width: share(part.minutes), backgroundColor: part.color }"
            :title="`${part.label}: ${formatDuration(part.minutes)}`"
          />
        </div>
        <ul class="mm-breakdown__list">
          <li v-for="part in breakdown" :key="part.key">
            <span class="mm-dot" :style="{ backgroundColor: part.color }" aria-hidden="true" />
            <span>{{ part.label }}</span>
            <strong>{{ formatDuration(part.minutes) }}</strong>
          </li>
          <li class="mm-breakdown__total">
            <span>Total</span>
            <strong>{{ formatDuration(journeyView.elapsedMinutes) }}</strong>
          </li>
        </ul>
      </div>

      <div v-if="journeyView" class="mm-legs">
        <h3 class="mm-subhead">Legs</h3>
        <ol>
          <li v-for="(leg, index) in journeyView.legs" :key="`${leg.fromNode}-${leg.toNode}-${index}`" class="mm-leg">
            <div class="mm-leg__index" aria-hidden="true">{{ index + 1 }}</div>
            <div class="mm-leg__body">
              <div class="mm-leg__title">
                <span class="mm-mode">{{ modeName(leg.mode) }}</span>
                <span v-if="leg.routeCode" class="mm-route">{{ leg.routeCode }}</span>
                <span class="mm-leg__times">
                  {{ formatClock(leg.departureMinute) }} → {{ formatClockWithDay(leg.arrivalMinute) }}
                </span>
              </div>
              <p class="mm-leg__nodes">{{ leg.fromName }} → {{ leg.toName }}</p>
              <p class="mm-leg__meta">
                <span v-if="leg.rideMinutes > 0">Ride {{ formatDuration(leg.rideMinutes) }}</span>
                <span v-if="leg.waitMinutes > 0">Wait {{ formatDuration(leg.waitMinutes) }}</span>
                <span v-if="leg.basis">{{ leg.basis }}</span>
                <span v-if="leg.serviceConfidence">{{ leg.serviceConfidence }}</span>
              </p>
            </div>
          </li>
        </ol>
        <p v-if="journeyView.usesEstimatedAir" class="mm-notice mm-notice--warn" role="note">
          This journey uses an air leg from an estimated weekly-frequency model. MACL records
          do not establish domestic flight schedules; treat it as an estimate, not a bookable
          itinerary.
        </p>
        <p
          v-else-if="journeyView.serviceConfidence === 'estimated'"
          class="mm-notice mm-notice--info"
          role="note"
        >
          At least one leg uses an estimated frequency model. Only journeys whose transit legs
          are all timetabled are labelled verified.
        </p>
      </div>

      <div v-if="!journeyView && nextDayJourney" class="mm-nextday">
        <h3 class="mm-subhead">Next-day alternative (assumption)</h3>
        <p class="mm-muted">
          The same-day search returned no itinerary. Optional next-day search repeats the
          reference-day timetable once, 24 hours later. It is not a verified next-day
          calendar.
        </p>
        <dl class="mm-statgrid">
          <div>
            <dt>Depart</dt>
            <dd>{{ formatClockWithDay(nextDayJourney.departureMinute) }}</dd>
          </div>
          <div>
            <dt>Arrive</dt>
            <dd>{{ formatClockWithDay(nextDayJourney.arrivalMinute) }}</dd>
          </div>
          <div>
            <dt>Elapsed</dt>
            <dd>{{ formatDuration(nextDayJourney.elapsedMinutes) }}</dd>
          </div>
          <div>
            <dt>Destination</dt>
            <dd>{{ nextDayJourney.destinationIslandName }}</dd>
          </div>
          <div>
            <dt>Modes</dt>
            <dd>{{ nextDayJourney.modes.map(modeName).join(' → ') || '—' }}</dd>
          </div>
        </dl>
      </div>

      <p class="mm-panel__foot">
        Reference day: {{ formatDate(referenceDay) }}. Service calendars are unverified and
        assumed to repeat on that weekday; the search horizon is
        {{ formatDuration(maxJourneyMinutes) }} from the requested departure. Times use
        Maldives time (UTC+5).
      </p>
    </template>
  </section>
</template>
