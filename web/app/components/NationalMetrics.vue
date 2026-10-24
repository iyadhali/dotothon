<script setup lang="ts">
import { computed } from 'vue'
import type { AccessibilitySummary } from '../../shared/routing/types'
import type { RegionAccess, RegionSplit, ThresholdMinutes } from '../utils/analysis'
import { formatClock, formatDuration, formatPercent, formatPopulation } from '../utils/format'

const props = defineProps<{
  summary: AccessibilitySummary | null
  split?: RegionSplit | null
  loading: boolean
  error: string | null
  threshold: ThresholdMinutes
  categoryLabel: string
  departureMinute: number
  scenarioActive?: boolean
  filterActive?: boolean
}>()

const thresholdLabel = computed(() => formatDuration(props.threshold))

function share(part: number, region: RegionAccess): string {
  return region.population > 0 ? formatPercent(part / region.population) : '—'
}

const regionRows = computed(() => {
  if (!props.split) return []
  return [
    { key: 'atolls', label: 'Atoll islands', region: props.split.atolls },
    { key: 'greater-male', label: 'Greater Malé', region: props.split.greaterMale },
  ]
})

const withinThreshold = computed(() => {
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

const coverageShare = computed(() => {
  if (!props.summary || props.summary.populationTotal <= 0) return 0
  return props.summary.populationReachable / props.summary.populationTotal
})

const verifiedShare = computed(() => {
  if (!props.summary || props.summary.populationReachable <= 0) return 0
  return props.summary.reachableVerifiedPopulation / props.summary.populationReachable
})

const originTotal = computed(() => {
  if (!props.summary) return 0
  return (
    props.summary.originsReachable +
    props.summary.originsUnreachable +
    props.summary.originsNoAccess
  )
})

const thresholdRows = computed(() => {
  if (!props.summary) return []
  const total = props.summary.populationTotal || 1
  return [
    { key: 60 as const, label: '60 min', value: props.summary.within60 },
    { key: 120 as const, label: '120 min', value: props.summary.within120 },
    { key: 240 as const, label: '240 min', value: props.summary.within240 },
  ].map((row) => ({
    ...row,
    selected: row.key === props.threshold,
    share: row.value / total,
  }))
})

const originSegments = computed(() => {
  if (!props.summary) return []
  const total = originTotal.value || 1
  return [
    {
      key: 'reachable',
      label: 'Reachable',
      count: props.summary.originsReachable,
      share: props.summary.originsReachable / total,
    },
    {
      key: 'unreachable',
      label: 'Unreachable',
      count: props.summary.originsUnreachable,
      share: props.summary.originsUnreachable / total,
    },
    {
      key: 'no_access',
      label: 'No access',
      count: props.summary.originsNoAccess,
      share: props.summary.originsNoAccess / total,
    },
  ]
})

function donutStyle(share: number): Record<string, string> {
  const pct = Math.max(0, Math.min(100, share * 100))
  return {
    background: `conic-gradient(var(--mm-accent) 0 ${pct}%, #e7e2d5 ${pct}% 100%)`,
  }
}

function widthStyle(share: number): Record<string, string> {
  return { width: `${Math.max(0, Math.min(100, share * 100))}%` }
}
</script>

<template>
  <section class="mm-panel mm-metrics" aria-labelledby="mm-metrics-heading">
    <header class="mm-panel__head">
      <div>
        <h2 id="mm-metrics-heading" class="mm-panel__title">Access metrics</h2>
        <p class="mm-panel__sub mm-one-line">
          Same-day {{ categoryLabel }} at {{ formatClock(departureMinute) }} · selected threshold
          {{ thresholdLabel }}
        </p>
      </div>
      <span class="mm-tag" :class="scenarioActive ? 'mm-tag--scenario' : 'mm-tag--quiet'">
        {{ scenarioActive ? 'Scenario' : 'Baseline' }}
      </span>
    </header>

    <div v-if="error" class="mm-notice mm-notice--warn" role="alert">
      Accessibility could not be computed: {{ error }}
    </div>

    <div v-else-if="loading" class="mm-skeleton-grid" role="status" aria-live="polite">
      <span class="mm-spinner" aria-hidden="true" />
      <span>Computing every origin island…</span>
    </div>

    <div v-else-if="!summary" class="mm-empty" role="status">
      Waiting for the accessibility summary.
    </div>

    <template v-else>
      <div class="mm-widgets">
        <article class="mm-widget mm-widget--coverage">
          <h3 class="mm-widget__title">Any same-day access</h3>
          <div class="mm-widget__donut-row">
            <div
              class="mm-donut"
              :style="donutStyle(coverageShare)"
              role="img"
              :aria-label="`${formatPercent(coverageShare)} of the origin population has any same-day access: ${formatPopulation(summary.populationReachable)} residents`"
            >
              <span class="mm-donut__value">{{ formatPercent(coverageShare) }}</span>
              <span class="mm-donut__sub">{{ formatPopulation(summary.populationReachable) }}</span>
            </div>
            <ul class="mm-legend-list">
              <li>
                <span class="mm-dot mm-dot--verified" aria-hidden="true" />
                Reachable
                <strong>{{ formatPopulation(summary.populationReachable) }}</strong>
              </li>
              <li>
                <span class="mm-dot mm-dot--unreachable" aria-hidden="true" />
                Unreachable
                <strong>{{ formatPopulation(summary.unreachablePopulation) }}</strong>
              </li>
              <li>
                <span class="mm-dot mm-dot--noaccess" aria-hidden="true" />
                No access
                <strong>{{ formatPopulation(summary.noOriginAccessPopulation) }}</strong>
              </li>
            </ul>
          </div>
        </article>

        <article class="mm-widget">
          <h3 class="mm-widget__title">Evidence mix</h3>
          <p class="mm-widget__big">
            {{ formatPercent(verifiedShare) }}
            <span>verified share of reachable residents</span>
          </p>
          <div
            class="mm-stack"
            role="img"
            :aria-label="`Verified ${formatPopulation(summary.reachableVerifiedPopulation)} residents; estimated or mixed ${formatPopulation(summary.reachableEstimatedPopulation)} residents`"
          >
            <span class="mm-stack__verified" :style="widthStyle(verifiedShare)" />
            <span class="mm-stack__estimated" :style="widthStyle(1 - verifiedShare)" />
          </div>
          <ul class="mm-legend-list mm-legend-list--inline">
            <li>
              <span class="mm-dot mm-dot--verified" aria-hidden="true" />
              Verified
              <strong>{{ formatPopulation(summary.reachableVerifiedPopulation) }}</strong>
            </li>
            <li>
              <span class="mm-dot mm-dot--estimated" aria-hidden="true" />
              Estimated / mixed
              <strong>{{ formatPopulation(summary.reachableEstimatedPopulation) }}</strong>
            </li>
          </ul>
        </article>

        <article class="mm-widget mm-widget--thresholds">
          <h3 class="mm-widget__title">Population within threshold</h3>
          <div
            v-for="row in thresholdRows"
            :key="row.key"
            class="mm-threshold-row"
            :class="{ 'is-selected': row.selected }"
            :aria-current="row.selected ? 'true' : undefined"
          >
            <span class="mm-threshold-row__label">{{ row.label }}</span>
            <strong class="mm-threshold-row__value">{{ formatPopulation(row.value) }}</strong>
            <span class="mm-threshold-row__share">{{ formatPercent(row.share) }}</span>
            <span class="mm-bar mm-bar--threshold" aria-hidden="true">
              <span :style="widthStyle(row.share)" />
            </span>
          </div>
        </article>

        <article class="mm-widget">
          <h3 class="mm-widget__title">Origin islands assessed</h3>
          <p class="mm-widget__big">
            {{ originTotal }}
            <span>origin islands · {{ formatPopulation(summary.populationTotal) }} residents</span>
          </p>
          <div
            class="mm-seg-bar"
            role="img"
            :aria-label="`${summary.originsReachable} reachable, ${summary.originsUnreachable} unreachable, ${summary.originsNoAccess} without access`"
          >
            <span
              v-for="segment in originSegments"
              :key="segment.key"
              class="mm-seg-bar__part"
              :class="`mm-seg-bar__part--${segment.key}`"
              :style="widthStyle(segment.share)"
            />
          </div>
          <ul class="mm-legend-list mm-legend-list--inline">
            <li v-for="segment in originSegments" :key="segment.key">
              <span class="mm-dot" :class="`mm-dot--${segment.key}`" aria-hidden="true" />
              {{ segment.label }}
              <strong>{{ segment.count }}</strong>
            </li>
          </ul>
        </article>
      </div>

      <p v-if="filterActive" class="mm-metric-note" role="note">
        <span class="mm-chip mm-chip--filter">filter</span>
        No-access includes islands excluded by your network selection.
      </p>

      <div v-if="regionRows.length" class="mm-region">
        <h3 class="mm-subhead">Where the national figure comes from</h3>
        <table class="mm-region__table">
          <thead>
            <tr>
              <th scope="col">Region</th>
              <th scope="col">Residents</th>
              <th scope="col">On island</th>
              <th scope="col">By travel</th>
              <th scope="col">No trip</th>
              <th scope="col">No data</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in regionRows" :key="row.key">
              <th scope="row">{{ row.label }}</th>
              <td>{{ formatPopulation(row.region.population) }}</td>
              <td>{{ share(row.region.onIsland, row.region) }}</td>
              <td>{{ share(row.region.byTransport, row.region) }}</td>
              <td>{{ share(row.region.unreachable, row.region) }}</td>
              <td>{{ share(row.region.noData, row.region) }}</td>
            </tr>
          </tbody>
        </table>
        <p class="mm-muted mm-region__note">
          Greater Malé has every listed service, so the national share mostly reflects it. The atoll row
          shows how many people depend on boats and flights.
        </p>
      </div>

      <details class="mm-method">
        <summary>Method &amp; denominator</summary>
        <p>
          Totals cover the 447,420-resident origin universe, not the 515,132 republic census
          total. Same-day itineraries only; next-day alternatives appear in the journey card and
          are never counted as national access.
        </p>
        <p v-if="filterActive">
          A network filter is active: “No access” can include islands with transport in the
          prepared network that your Land/Sea/Air or route selection removed. The map labels that
          state “Not selected”.
        </p>
        <p>
          Verified means every transit leg has a published timetable and no air leg is used; all
          other reachable residents are estimated or mixed. See Data &amp; coverage for omitted
          groups and facility precision.
        </p>
      </details>
    </template>
  </section>
</template>
