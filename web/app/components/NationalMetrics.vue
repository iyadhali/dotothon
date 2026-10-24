<script setup lang="ts">
import { computed } from 'vue'
import type { AccessibilitySummary } from '../../shared/routing/types'
import type { ThresholdMinutes } from '../utils/analysis'
import {
  formatClock,
  formatDuration,
  formatPercent,
  formatPopulation,
} from '../utils/format'

const props = defineProps<{
  summary: AccessibilitySummary | null
  loading: boolean
  error: string | null
  threshold: ThresholdMinutes
  categoryLabel: string
  departureMinute: number
  scenarioActive?: boolean
  filterActive?: boolean
}>()

const thresholdKey = computed<keyof AccessibilitySummary>(() => {
  switch (props.threshold) {
    case 60:
      return 'within60'
    case 120:
      return 'within120'
    default:
      return 'within240'
  }
})

const thresholdLabel = computed(() => formatDuration(props.threshold))

const withinThreshold = computed(() => {
  if (!props.summary) return 0
  const value = props.summary[thresholdKey.value]
  return typeof value === 'number' ? value : 0
})

const withinShare = computed(() => {
  if (!props.summary || props.summary.populationTotal <= 0) return 0
  return withinThreshold.value / props.summary.populationTotal
})

const reachableShare = computed(() => {
  if (!props.summary || props.summary.populationTotal <= 0) return 0
  return props.summary.populationReachable / props.summary.populationTotal
})

const verifiedShare = computed(() => {
  if (!props.summary) return 0
  const reachable = props.summary.populationReachable
  if (reachable <= 0) return 0
  return props.summary.reachableVerifiedPopulation / reachable
})

const originTotal = computed(() => {
  if (!props.summary) return 0
  return (
    props.summary.originsReachable +
    props.summary.originsUnreachable +
    props.summary.originsNoAccess
  )
})

const coveragePct = computed(() =>
  props.summary ? formatPercent(props.summary.coverage) : '—',
)
</script>

<template>
  <section class="mm-panel" aria-labelledby="mm-metrics-heading">
    <header class="mm-panel__head">
      <div>
        <h2 id="mm-metrics-heading" class="mm-panel__title">National access metrics</h2>
        <p class="mm-panel__sub">
          Population that can reach a listed <strong>{{ categoryLabel }}</strong> facility
          departing at <strong>{{ formatClock(departureMinute) }}</strong>, same day.
        </p>
      </div>
      <span class="mm-tag" :class="scenarioActive ? 'mm-tag--scenario' : 'mm-tag--quiet'">
        {{ scenarioActive ? 'Scenario network' : 'Baseline network' }} · {{ thresholdLabel }}
      </span>
    </header>

    <div v-if="error" class="mm-notice mm-notice--warn" role="alert">
      Accessibility could not be computed: {{ error }}
    </div>

    <div v-else-if="loading" class="mm-skeleton-grid" role="status" aria-live="polite">
      <span class="mm-spinner" aria-hidden="true" />
      <span>Computing access for every origin island…</span>
    </div>

    <div v-else-if="!summary" class="mm-empty" role="status">
      Accessibility has not been computed yet.
    </div>

    <template v-else>
      <div class="mm-metric-hero">
        <div>
          <span class="mm-eyebrow">Within {{ thresholdLabel }}</span>
          <strong class="mm-metric-hero__value">{{ formatPopulation(withinThreshold) }}</strong>
          <span class="mm-metric-hero__share">{{ formatPercent(withinShare) }} of the origin population</span>
        </div>
        <div class="mm-metric-hero__coverage">
          <span class="mm-eyebrow">Coverage (any same-day access)</span>
          <strong>{{ coveragePct }}</strong>
          <span class="mm-muted">{{ formatPopulation(summary.populationReachable) }} residents</span>
        </div>
      </div>

      <div class="mm-metric-grid">
        <article class="mm-metric">
          <h3>Reachable population</h3>
          <p class="mm-metric__value">{{ formatPopulation(summary.populationReachable) }}</p>
          <p class="mm-muted">{{ formatPercent(reachableShare) }} of origin population</p>
        </article>

        <article class="mm-metric">
          <h3>Evidence mix (reachable)</h3>
          <div class="mm-stack" aria-hidden="true">
            <span
              class="mm-stack__verified"
              :style="{ width: formatPercent(verifiedShare) }"
            />
            <span class="mm-stack__estimated" :style="{ width: formatPercent(1 - verifiedShare) }" />
          </div>
          <ul class="mm-evidence-list">
            <li>
              <span class="mm-dot mm-dot--verified" aria-hidden="true" />
              Verified timetable
              <strong>{{ formatPopulation(summary.reachableVerifiedPopulation) }}</strong>
            </li>
            <li>
              <span class="mm-dot mm-dot--estimated" aria-hidden="true" />
              Estimated / mixed
              <strong>{{ formatPopulation(summary.reachableEstimatedPopulation) }}</strong>
            </li>
          </ul>
        </article>

        <article class="mm-metric">
          <h3>Unreachable on the reference day</h3>
          <p class="mm-metric__value">{{ formatPopulation(summary.unreachablePopulation) }}</p>
          <p class="mm-muted">
            {{ summary.originsUnreachable }} origin islands · missing timetable ≠ zero access
          </p>
        </article>

        <article class="mm-metric">
          <h3>{{ filterActive ? 'No access under current selection' : 'No origin access in prepared data' }}</h3>
          <p class="mm-metric__value">{{ formatPopulation(summary.noOriginAccessPopulation) }}</p>
          <p class="mm-muted">{{ summary.originsNoAccess }} origin islands · coverage gap</p>
        </article>

        <article class="mm-metric mm-metric--wide">
          <h3>Population within 1 h / 2 h / 4 h</h3>
          <div class="mm-three">
            <div>
              <span class="mm-muted">60 min</span>
              <strong>{{ formatPopulation(summary.within60) }}</strong>
            </div>
            <div>
              <span class="mm-muted">120 min</span>
              <strong>{{ formatPopulation(summary.within120) }}</strong>
            </div>
            <div>
              <span class="mm-muted">240 min</span>
              <strong>{{ formatPopulation(summary.within240) }}</strong>
            </div>
          </div>
        </article>

        <article class="mm-metric">
          <h3>Origin islands assessed</h3>
          <p class="mm-metric__value">{{ originTotal }}</p>
          <p class="mm-muted">
            {{ summary.originsReachable }} reachable · {{ summary.originsUnreachable }} unreachable ·
            {{ summary.originsNoAccess }} without access
          </p>
        </article>
      </div>

      <p v-if="filterActive" class="mm-alert mm-alert--info" role="note">
        A network filter is active. “No access under current selection” can include islands that
        have transport in the prepared network but were removed by your Land/Sea/Air or route
        selection; it is not a coverage finding. The map uses a separate “Not selected” band.
      </p>

      <p class="mm-panel__foot">
        Totals cover the 447,420-resident origin universe, not the 515,132 republic census
        total. Same-day itineraries only; next-day alternatives are shown in the journey card
        but are never counted as national access. See the coverage panel for omitted groups
        and facility precision.
      </p>
    </template>
  </section>
</template>
