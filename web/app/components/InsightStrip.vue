<script setup lang="ts">
import { computed } from 'vue'
import type { AccessibilitySummary } from '../../shared/routing/types'
import type { ScenarioComparison, ThresholdMinutes } from '../utils/analysis'
import { formatDuration, formatPercent, formatPopulation, formatSignedNumber } from '../utils/format'

const props = defineProps<{
  summary: AccessibilitySummary | null
  unfilteredSummary: AccessibilitySummary | null
  comparison: ScenarioComparison | null
  threshold: ThresholdMinutes
  filterActive?: boolean
  scenarioActive?: boolean
  loading: boolean
}>()

interface Insight {
  key: string
  chip: string
  chipTone: 'estimated' | 'scenario' | 'filter' | 'derived'
  value: string
  label: string
  detail: string
}

const thresholdLabel = computed(() => formatDuration(props.threshold))

const assessedOrigins = computed(() => {
  if (!props.summary) return 0
  return (
    props.summary.originsReachable +
    props.summary.originsUnreachable +
    props.summary.originsNoAccess
  )
})

const within = computed(() => {
  if (!props.summary) return 0
  switch (props.threshold) {
    case 60:
      return props.summary.within60
    case 120:
      return props.summary.within120
    default:
      return props.summary.within240
  }
})

const estimatedShare = computed(() => {
  if (!props.summary || props.summary.populationReachable <= 0) return 0
  return props.summary.reachableEstimatedPopulation / props.summary.populationReachable
})

const filterRemoved = computed(() => {
  if (!props.summary || !props.unfilteredSummary) return null
  return Math.max(
    0,
    props.unfilteredSummary.populationReachable - props.summary.populationReachable,
  )
})

const topNewlyCovered = computed(() => props.comparison?.newlyCovered[0] ?? null)
const scenarioWithinGain = computed(() =>
  props.comparison ? props.comparison.withinDeltas[props.threshold] : 0,
)
const firstChanged = computed(() => props.comparison?.changes[0] ?? null)

const insights = computed<Insight[]>(() => {
  if (!props.summary) return []
  const rows: Insight[] = []
  const noAccess = props.summary.originsNoAccess
  rows.push({
    key: 'gap',
    chip: 'coverage',
    chipTone: 'derived',
    value: `${noAccess}/${assessedOrigins.value}`,
    label: 'origin islands with no route',
    detail: `${formatPercent(assessedOrigins.value > 0 ? noAccess / assessedOrigins.value : 0)} of assessed origins start with no access edge`,
  })
  rows.push({
    key: 'estimated',
    chip: 'estimated',
    chipTone: 'estimated',
    value: formatPercent(estimatedShare.value),
    label: 'reachable residents on estimated/mixed evidence',
    detail: `${formatPopulation(props.summary.reachableEstimatedPopulation)} of ${formatPopulation(props.summary.populationReachable)} reachable residents`,
  })
  rows.push({
    key: 'threshold',
    chip: 'threshold',
    chipTone: 'derived',
    value: formatPopulation(Math.max(0, props.summary.populationTotal - within.value)),
    label: `residents outside ${thresholdLabel.value}`,
    detail: `${formatPercent(props.summary.populationTotal > 0 ? within.value / props.summary.populationTotal : 0)} within ${thresholdLabel.value} · same-day only`,
  })
  if (props.filterActive && filterRemoved.value !== null) {
    rows.push({
      key: 'filter',
      chip: 'filter',
      chipTone: 'filter',
      value: formatPopulation(filterRemoved.value),
      label: 'reachable residents removed by the active filter',
      detail: `Unfiltered prepared network: ${formatPopulation(props.unfilteredSummary?.populationReachable ?? 0)} reachable`,
    })
  }
  if (props.scenarioActive) {
    const newlyCovered = props.comparison?.newlyReachablePopulation ?? 0
    rows.push({
      key: 'scenario',
      chip: 'scenario',
      chipTone: 'scenario',
      value: formatPopulation(newlyCovered),
      label: 'residents newly covered by this scenario',
      detail: topNewlyCovered.value
        ? `Top island: ${topNewlyCovered.value.name} · ${formatPopulation(topNewlyCovered.value.population)} residents`
        : props.loading
          ? 'Updating scenario comparison…'
          : `${formatSignedNumber(scenarioWithinGain.value)} within ${thresholdLabel.value} · ${props.comparison?.originsChanged ?? 0} origins changed${firstChanged.value ? ` · ${firstChanged.value.name}` : ''}`,
    })
  }
  return rows
})
</script>

<template>
  <section class="mm-insights" aria-labelledby="mm-insights-title">
    <div class="mm-insights__head">
      <h2 id="mm-insights-title" class="mm-insights__title">Insights</h2>
      <span class="mm-insights__note">derived from the current run</span>
    </div>
    <p v-if="loading && !summary" class="mm-insights__state" role="status">
      <span class="mm-spinner mm-spinner--small" aria-hidden="true" /> Deriving insights…
    </p>
    <div v-else-if="insights.length" class="mm-insights__grid">
      <article v-for="insight in insights" :key="insight.key" class="mm-insight">
        <span class="mm-chip" :class="`mm-chip--${insight.chipTone}`">{{ insight.chip }}</span>
        <strong class="mm-insight__value">{{ insight.value }}</strong>
        <span class="mm-insight__label">{{ insight.label }}</span>
        <span class="mm-insight__detail">{{ insight.detail }}</span>
      </article>
    </div>
    <p v-else class="mm-insights__state" role="status">Insights appear when the summary loads.</p>
  </section>
</template>
