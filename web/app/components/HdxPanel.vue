<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { $fetch } from 'ofetch'
import type { AccessibilitySummary } from '../../shared/routing/types'
import type { ThresholdMinutes } from '../utils/analysis'
import { formatDuration, formatPercent, formatPopulation } from '../utils/format'

interface HdxNationalRow {
  category: string
  threshold: string | number
  share: number
  population: number
}

interface HdxUnitRow {
  admLevel: string
  name: string
  category: string
  within5km?: number | null
}

interface HdxBaseline {
  source: string
  method: string
  warning: string
  national: HdxNationalRow[]
  units?: HdxUnitRow[]
}

const props = defineProps<{
  summary: AccessibilitySummary | null
  threshold: ThresholdMinutes
}>()

type HdxStatus = 'loading' | 'ready' | 'missing' | 'error'

const status = ref<HdxStatus>('loading')
const baseline = ref<HdxBaseline | null>(null)
const errorNote = ref('')

function isHdxBaseline(value: unknown): value is HdxBaseline {
  if (!value || typeof value !== 'object') return false
  const record = value as Record<string, unknown>
  if (typeof record.source !== 'string' || typeof record.method !== 'string') return false
  if (typeof record.warning !== 'string') return false
  if (!Array.isArray(record.national)) return false
  return record.national.every((row) => {
    if (!row || typeof row !== 'object') return false
    const entry = row as Record<string, unknown>
    return (
      typeof entry.category === 'string' &&
      (typeof entry.threshold === 'number' || typeof entry.threshold === 'string') &&
      typeof entry.share === 'number' &&
      typeof entry.population === 'number'
    )
  })
}

function categoryLabel(value: string): string {
  return value
    .split(/[_\s-]+/)
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ')
}

function thresholdText(value: string | number): string {
  return String(value)
}

function findRow(category: string, threshold: string): HdxNationalRow | undefined {
  return baseline.value?.national.find(
    (row) =>
      row.category === category &&
      thresholdText(row.threshold).trim().toLowerCase() === threshold.toLowerCase(),
  )
}

const tileRows = computed(() => [
  {
    key: 'education',
    label: 'Education',
    context: 'within 5 km',
    row: findRow('education', '5 km'),
  },
  {
    key: 'hospital',
    label: 'Hospital',
    context: 'within 60 min',
    row: findRow('hospitals', '60 min'),
  },
  {
    key: 'primary',
    label: 'Primary care',
    context: 'within 60 min',
    row: findRow('primary_healthcare', '60 min'),
  },
])

const hospital60 = computed(() => findRow('hospitals', '60 min'))

const multimodalShare = computed(() => {
  if (!props.summary || props.summary.populationTotal <= 0) return null
  const within =
    props.threshold === 60
      ? props.summary.within60
      : props.threshold === 120
        ? props.summary.within120
        : props.summary.within240
  return (within / props.summary.populationTotal) * 100
})

const comparison = computed(() => {
  if (multimodalShare.value === null || !hospital60.value) return null
  return {
    multimodal: multimodalShare.value,
    benchmark: hospital60.value.share,
    delta: multimodalShare.value - hospital60.value.share,
  }
})

const nationalRows = computed(() => baseline.value?.national ?? [])

const unitGroups = computed(() => {
  const units = baseline.value?.units ?? []
  const groups = new Map<string, { count: number; withDistance: number; sum: number }>()
  for (const unit of units) {
    const key = `${unit.admLevel} · ${unit.category}`
    const current = groups.get(key) ?? { count: 0, withDistance: 0, sum: 0 }
    current.count += 1
    if (typeof unit.within5km === 'number' && Number.isFinite(unit.within5km)) {
      current.withDistance += 1
      current.sum += unit.within5km
    }
    groups.set(key, current)
  }
  return [...groups.entries()]
    .map(([key, value]) => ({
      key,
      count: value.count,
      withDistance: value.withDistance,
      average: value.withDistance ? value.sum / value.withDistance : null,
    }))
    .sort((a, b) => b.count - a.count || a.key.localeCompare(b.key))
})

const nationalByThreshold = computed(() => {
  return [...nationalRows.value].sort(
    (a, b) =>
      a.category.localeCompare(b.category) ||
      String(a.threshold).localeCompare(String(b.threshold), undefined, { numeric: true }),
  )
})

function barStyle(share: number): Record<string, string> {
  return { width: `${Math.max(0, Math.min(100, share))}%` }
}

onMounted(async () => {
  const notes: string[] = []
  for (const url of ['/api/hdx', '/data/heigit-baseline.json']) {
    try {
      const payload = await $fetch<unknown>(url, { timeout: 12000 })
      if (!isHdxBaseline(payload)) {
        notes.push(`${url} returned an unexpected schema`)
        continue
      }
      baseline.value = payload
      status.value = 'ready'
      return
    } catch (error) {
      notes.push(`${url}: ${error instanceof Error ? error.message : String(error)}`)
    }
  }
  status.value = 'missing'
  errorNote.value = notes.join(' · ') || 'The HDX benchmark file could not be fetched.'
})
</script>

<template>
  <section class="mm-panel mm-hdx" aria-labelledby="mm-hdx-title">
    <header class="mm-panel__head">
      <div>
        <h2 id="mm-hdx-title" class="mm-panel__title">External benchmark</h2>
        <p class="mm-panel__sub mm-one-line">
          HDX/HeiGIT land–car access · separate population universe
        </p>
      </div>
      <span class="mm-tag mm-tag--warn">Land-only · not merged</span>
    </header>

    <p v-if="status === 'loading'" class="mm-loading-inline" role="status">
      <span class="mm-spinner mm-spinner--small" aria-hidden="true" /> Loading benchmark…
    </p>

    <template v-else-if="status === 'ready' && baseline">
      <div class="mm-hdx__tiles">
        <article v-for="tile in tileRows" :key="tile.key" class="mm-hdx__tile">
          <span class="mm-hdx__tile-label">{{ tile.label }}</span>
          <strong class="mm-hdx__tile-value">
            {{ tile.row ? `${tile.row.share.toFixed(1)}%` : '—' }}
          </strong>
          <span class="mm-hdx__tile-context">{{ tile.context }}</span>
          <span class="mm-bar mm-bar--hdx" aria-hidden="true">
            <span v-if="tile.row" :style="barStyle(tile.row.share)" />
          </span>
          <span class="mm-hdx__tile-pop">
            {{ tile.row ? `${formatPopulation(tile.row.population)} residents` : 'Not published' }}
          </span>
        </article>
      </div>

      <article v-if="comparison" class="mm-hdx__insight">
        <span class="mm-chip mm-chip--derived">derived · not like-for-like</span>
        <p>
          This atlas
          <strong>{{ formatPercent(comparison.multimodal / 100) }}</strong> within
          {{ formatDuration(threshold) }} · HDX hospital ≤60 min
          <strong>{{ comparison.benchmark.toFixed(1) }}%</strong>
          <span class="mm-hdx__delta">
            {{ comparison.delta >= 0 ? '+' : '' }}{{ comparison.delta.toFixed(1) }} pts
          </span>
        </p>
        <span class="mm-hdx__insight-note">
          Different populations, modes and definitions. Shown for orientation only — not causal,
          not a validation.
        </span>
      </article>

      <details class="mm-data-details mm-hdx__more">
        <summary>
          National rows ({{ nationalRows.length }}) · source, units &amp; limits
        </summary>
        <dl class="mm-hdx__source">
          <div>
            <dt>Source</dt>
            <dd>{{ baseline.source }}</dd>
          </div>
          <div>
            <dt>Method</dt>
            <dd>{{ baseline.method }}</dd>
          </div>
          <div>
            <dt>Caution</dt>
            <dd>{{ baseline.warning }}</dd>
          </div>
        </dl>

        <div class="mm-hdx__table-wrap">
          <table class="mm-hdx__table">
            <caption class="mm-hdx__caption">
              National benchmark rows as published; shares are the source values, no interpolation.
            </caption>
            <thead>
              <tr>
                <th scope="col">Category</th>
                <th scope="col">Threshold</th>
                <th scope="col">Share</th>
                <th scope="col">Population</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in nationalByThreshold" :key="`${row.category}-${row.threshold}`">
                <th scope="row">{{ categoryLabel(row.category) }}</th>
                <td>{{ thresholdText(row.threshold) }}</td>
                <td>{{ row.share.toFixed(1) }}%</td>
                <td>{{ formatPopulation(row.population) }}</td>
              </tr>
            </tbody>
          </table>
        </div>

        <details v-if="unitGroups.length" class="mm-hdx__units">
          <summary>Unit-level summary ({{ baseline.units?.length ?? 0 }} rows)</summary>
          <ul>
            <li v-for="group in unitGroups" :key="group.key">
              {{ group.key }}: {{ group.count }} units
              <template v-if="group.average !== null">
                · mean within-5 km share {{ group.average.toFixed(1) }}%
                ({{ group.withDistance }} with distance values).
              </template>
              <template v-else>· time-threshold units; no within-5 km value.</template>
            </li>
          </ul>
        </details>

        <p class="mm-hint">
          Land/car access only; education distance-based, hospitals and primary care time-based;
          WorldPop population, not the 2022 census origin universe; some units excluded or
          aggregated. A separate benchmark, not a replacement or validation.
        </p>
      </details>
    </template>

    <template v-else>
      <p class="mm-panel__note">
        Benchmark not published at <code>/data/heigit-baseline.json</code>; values are never
        inferred or back-filled.
      </p>
      <details v-if="errorNote" class="mm-data-details">
        <summary>Fetch detail</summary>
        <p class="mm-muted">{{ errorNote }}</p>
      </details>
    </template>
  </section>
</template>
