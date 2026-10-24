<script setup lang="ts">
import { computed } from 'vue'
import type { AccessibilitySummary } from '../../shared/routing/types'
import type { ThresholdMinutes } from '../utils/analysis'
import { formatDuration, formatPercent, formatPopulation } from '../utils/format'

const props = defineProps<{
  summary: AccessibilitySummary | null
  threshold: ThresholdMinutes
  loading: boolean
  error: string | null
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

const within = computed(() => {
  const value = props.summary?.[thresholdKey.value]
  return typeof value === 'number' ? value : 0
})

const total = computed(() => props.summary?.populationTotal ?? 0)

const withinShare = computed(() => (total.value > 0 ? within.value / total.value : 0))

const outside = computed(() => Math.max(0, total.value - within.value))

const coverageShare = computed(() =>
  total.value > 0 ? (props.summary?.populationReachable ?? 0) / total.value : 0,
)

const unreachableShare = computed(() =>
  total.value > 0 ? (props.summary?.unreachablePopulation ?? 0) / total.value : 0,
)

const noAccessShare = computed(() =>
  total.value > 0 ? (props.summary?.noOriginAccessPopulation ?? 0) / total.value : 0,
)

const assessedOrigins = computed(() => {
  if (!props.summary) return 0
  return (
    props.summary.originsReachable +
    props.summary.originsUnreachable +
    props.summary.originsNoAccess
  )
})

const withinInsight = computed(() => {
  if (!props.summary || withinShare.value <= 0) return `No residents within ${thresholdLabel.value}`
  if (withinShare.value >= 0.995) return `Everyone is within ${thresholdLabel.value}`
  const oneIn = Math.max(2, Math.round(1 / Math.max(0.001, 1 - withinShare.value)))
  return `1 in ${oneIn} residents outside ${thresholdLabel.value}`
})

const coverageInsight = computed(() => {
  if (!props.summary) return 'No summary loaded'
  return `${props.summary.originsReachable} of ${assessedOrigins.value} origin islands have access`
})

const unreachableInsight = computed(() => {
  if (!props.summary) return 'No summary loaded'
  return `${props.summary.originsUnreachable} islands have no same-day itinerary`
})

const noAccessInsight = computed(() => {
  if (!props.summary) return 'No summary loaded'
  return props.filterActive
    ? `${props.summary.originsNoAccess} islands with no route in this selection`
    : `${props.summary.originsNoAccess} islands start with no route`
})

function ringStyle(share: number): Record<string, string> {
  const pct = Math.max(0, Math.min(100, share * 100))
  return {
    background: `conic-gradient(var(--mm-accent) 0 ${pct}%, #e7e2d5 ${pct}% 100%)`,
  }
}

function barStyle(share: number): Record<string, string> {
  return { width: `${Math.max(0, Math.min(100, share * 100))}%` }
}
</script>

<template>
  <section class="mm-kpis" aria-labelledby="mm-kpis-title">
    <div class="mm-kpis__head">
      <h2 id="mm-kpis-title" class="mm-kpis__title">
        {{ scenarioActive ? 'Scenario snapshot' : 'Reference-day snapshot' }}
      </h2>
      <span v-if="scenarioActive" class="mm-chip mm-chip--accent">scenario</span>
      <span v-if="filterActive" class="mm-chip mm-chip--accent">filtered</span>
      <span class="mm-kpis__threshold">within {{ thresholdLabel }}</span>
    </div>

    <p v-if="error" class="mm-kpis__state" role="alert">
      Accessibility could not be computed: {{ error }}
    </p>
    <p v-else-if="loading" class="mm-kpis__state" role="status" aria-live="polite">
      <span class="mm-spinner mm-spinner--small" aria-hidden="true" /> Updating…
    </p>

    <div v-else-if="!summary" class="mm-kpis__state" role="status">
      Waiting for the accessibility summary.
    </div>

    <div v-else class="mm-kpis__grid">
      <article
        class="mm-kpi"
        :aria-label="`Within ${thresholdLabel}: ${formatPopulation(within)} residents, ${formatPercent(withinShare)} of the origin population`"
      >
        <span class="mm-kpi__visual">
          <span class="mm-ring" :style="ringStyle(withinShare)">
            <span>{{ formatPercent(withinShare, 0) }}</span>
          </span>
        </span>
        <div class="mm-kpi__body">
          <span class="mm-kpi__label">Within {{ thresholdLabel }}</span>
          <strong class="mm-kpi__value">{{ formatPopulation(within) }}</strong>
          <span class="mm-kpi__insight">{{ withinInsight }}</span>
        </div>
      </article>

      <article
        class="mm-kpi"
        :aria-label="`Any same-day access: ${formatPopulation(summary.populationReachable)} residents, ${formatPercent(coverageShare)} of the origin population`"
      >
        <span class="mm-kpi__visual">
          <span class="mm-ring mm-ring--coverage" :style="ringStyle(coverageShare)">
            <span>{{ formatPercent(coverageShare, 0) }}</span>
          </span>
        </span>
        <div class="mm-kpi__body">
          <span class="mm-kpi__label">Any same-day access</span>
          <strong class="mm-kpi__value">{{ formatPopulation(summary.populationReachable) }}</strong>
          <span class="mm-kpi__insight">{{ coverageInsight }}</span>
        </div>
      </article>

      <article
        class="mm-kpi"
        :aria-label="`Unreachable on the reference day: ${formatPopulation(summary.unreachablePopulation)} residents, ${formatPercent(unreachableShare)} of the origin population`"
      >
        <span class="mm-kpi__visual" aria-hidden="true">
          <span class="mm-bar mm-bar--warn"><span :style="barStyle(unreachableShare)" /></span>
        </span>
        <div class="mm-kpi__body">
          <span class="mm-kpi__label">Unreachable on reference day</span>
          <strong class="mm-kpi__value">{{ formatPopulation(summary.unreachablePopulation) }}</strong>
          <span class="mm-kpi__insight">{{ unreachableInsight }}</span>
        </div>
      </article>

      <article
        class="mm-kpi"
        :aria-label="`No transport data: ${formatPopulation(summary.noOriginAccessPopulation)} residents, ${formatPercent(noAccessShare)} of the origin population`"
      >
        <span class="mm-kpi__visual" aria-hidden="true">
          <span class="mm-bar mm-bar--gap"><span :style="barStyle(noAccessShare)" /></span>
        </span>
        <div class="mm-kpi__body">
          <span class="mm-kpi__label">No transport data</span>
          <strong class="mm-kpi__value">{{ formatPopulation(summary.noOriginAccessPopulation) }}</strong>
          <span class="mm-kpi__insight">{{ noAccessInsight }}</span>
        </div>
      </article>
    </div>

    <p v-if="summary" class="mm-kpis__foot">
      <span>{{ formatPopulation(outside) }} residents outside {{ thresholdLabel }}</span>
      <span>Same-day only · next-day alternatives are not counted</span>
    </p>
  </section>
</template>
