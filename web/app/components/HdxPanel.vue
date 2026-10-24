<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { $fetch } from 'ofetch'

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
  const rows = nationalRows.value
  return [...rows].sort(
    (a, b) =>
      a.category.localeCompare(b.category) ||
      String(a.threshold).localeCompare(String(b.threshold), undefined, { numeric: true }),
  )
})

onMounted(async () => {
  try {
    const payload = await $fetch<unknown>('/data/heigit-baseline.json', { timeout: 12000 })
    if (!isHdxBaseline(payload)) {
      status.value = 'error'
      errorNote.value =
        'The HDX benchmark file exists but does not match the expected source / national / units schema, so it is not displayed.'
      return
    }
    baseline.value = payload
    status.value = 'ready'
  } catch (error) {
    status.value = 'missing'
    errorNote.value =
      error instanceof Error ? error.message : 'The HDX benchmark file could not be fetched.'
  }
})
</script>

<template>
  <section class="mm-panel mm-panel--wide mm-hdx" aria-labelledby="mm-hdx-title">
    <header class="mm-panel__head">
      <div>
        <p class="mm-eyebrow">External benchmark</p>
        <h2 id="mm-hdx-title" class="mm-panel__title">HDX / HeiGIT land-based comparison</h2>
      </div>
      <span class="mm-tag">Benchmark · not merged</span>
    </header>

    <p class="mm-panel__note">
      This panel compares against the published HDX/HeiGIT land-based benchmark. Education
      uses distance thresholds (5–50 km); hospitals and primary care use travel-time
      thresholds (10–120 min). It is shown as context only: it is <strong>not</strong> merged
      into this prototype's multimodal population denominators, and the app does not
      interpolate or recompute its values.
    </p>

    <p v-if="status === 'loading'" class="mm-loading-inline" role="status">
      <span class="mm-spinner mm-spinner--small" aria-hidden="true" /> Loading
      <code>/data/heigit-baseline.json</code>…
    </p>

    <template v-else-if="status === 'ready' && baseline">
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
            National benchmark rows as published. Shares are the source values; no
            interpolation or rounding beyond display.
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
              <td>{{ typeof row.threshold === 'number' ? `${row.threshold} km` : row.threshold }}</td>
              <td>{{ row.share.toFixed(1) }}%</td>
              <td>{{ row.population.toLocaleString('en-GB') }}</td>
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
        <p class="mm-hint">
          Unit summaries are descriptive only. They cover land/car access and do not establish
          multimodal access, service availability or a national population denominator.
        </p>
      </details>

      <p class="mm-panel__note">
        Known limits of the benchmark: it models <strong>land/car access only</strong>, not
        ferry or air travel; education is distance-based while hospitals and primary care are
        time-based; its population source is WorldPop rather than the 2022 census origin
        universe; and it excludes or aggregates some units. Treat it as a separate benchmark,
        not as a replacement or validation of the numbers above.
      </p>
    </template>

    <template v-else>
      <p v-if="status === 'error'" class="mm-panel__note">
        The HDX benchmark file could not be read as the expected schema, so no comparison is
        shown. Values are never inferred or back-filled.
      </p>
      <p v-else class="mm-panel__note">
        The HDX benchmark file is not published at
        <code>/data/heigit-baseline.json</code>, so no comparison can be shown. Values are
        never inferred or back-filled.
      </p>
      <p v-if="errorNote" class="mm-hint">{{ errorNote }}</p>
    </template>
  </section>
</template>
