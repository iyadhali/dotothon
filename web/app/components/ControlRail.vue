<script setup lang="ts">
import { computed } from 'vue'
import type { MultimodalStore } from '../composables/useMultimodal'
import { formatClock, parseClock } from '../utils/format'

const props = defineProps<{ store: MultimodalStore }>()
const store = props.store

const {
  originIslandId,
  category,
  departureMinute,
  threshold,
  origins,
  categoryGroups,
  selectedCategory,
  engineReady,
  filterActive,
  landEnabled,
  seaEnabled,
  airEnabled,
  networkPreset,
  enabledRouteCount,
  scenarioMode,
} = props.store

const thresholds = [60, 120, 240] as const

const departureTime = computed({
  get: () => formatClock(departureMinute.value),
  set: (value: string) => {
    departureMinute.value = parseClock(value, departureMinute.value)
  },
})

const thresholdLabel = computed(() => `${threshold.value} minutes`)

const airModelNote = computed(() =>
  airEnabled.value
    ? 'Air links use documented weekly frequency and operating windows, not a published flight schedule.'
    : 'Air is excluded from the modelled network. Islands reachable only by air show as not selected or not reachable under this selection.',
)

const networkFact = computed(() => {
  const modes: string[] = []
  if (landEnabled.value) modes.push('Land')
  if (seaEnabled.value) modes.push('Sea')
  if (airEnabled.value) modes.push('Air')
  return `${modes.length ? modes.join(' + ') : 'No modes'} · ${enabledRouteCount.value} routes`
})
</script>

<template>
  <div class="mm-rail">
    <section class="mm-rail__section" aria-labelledby="mm-controls-title">
      <h2 id="mm-controls-title" class="mm-rail__title">Explore</h2>
      <p class="mm-hint">Pick an island (or click it on the map), a service and a departure time.</p>

      <OriginSelect v-model="originIslandId" :origins="origins" />

      <label class="mm-field">
        <span class="mm-label">Service shown on the map</span>
        <select v-model="category" class="mm-input">
          <optgroup v-for="group in categoryGroups" :key="group.label" :label="group.label">
            <option v-for="definition in group.categories" :key="definition.id" :value="definition.id">
              {{ definition.label }} ({{ definition.islandCount }} islands)
            </option>
          </optgroup>
        </select>
      </label>
      <p v-if="selectedCategory" class="mm-hint">
        {{ selectedCategory.facilityCount }} facilities on {{ selectedCategory.islandCount }} islands.
      </p>

      <label class="mm-field">
        <span class="mm-label">Departure time</span>
        <input v-model="departureTime" class="mm-input" type="time" step="60" />
        <span class="mm-hint">Maldives time. Ferry departures decide most results, so try 06:00 and 14:00.</span>
      </label>

      <fieldset class="mm-fieldset">
        <legend class="mm-label">National metric: within</legend>
        <div class="mm-seg mm-seg--three" role="radiogroup" aria-label="Travel-time threshold">
          <label v-for="value in thresholds" :key="value" class="mm-seg__item">
            <input v-model="threshold" type="radio" name="mm-threshold" :value="value" />
            <span class="mm-seg__label">{{ value }} min</span>
          </label>
        </div>
        
      </fieldset>

      <p v-if="!engineReady" class="mm-alert mm-alert--info" role="status">
        The routing engine is not configured yet. Map colours and metrics appear once the
        router is integrated; the prepared network and controls are still browsable.
      </p>
    </section>

    <details class="mm-advanced">
      <summary>
        <div>
          Network &amp; scenario tools
          <span>Switch modes and routes, add a ferry trip or a facility</span>
        </div>
      </summary>
      <div class="mm-advanced__body">
        <p class="mm-hint" role="note">Air model: {{ airModelNote }}</p>
        <NetworkControls :store="store" :disabled="!engineReady" />

    <ScenarioControls :store="store" :disabled="!engineReady" />

    <SimulatorPanel :store="store" :disabled="!engineReady" />

    <section class="mm-rail__section" aria-labelledby="mm-current-title">
      <h2 id="mm-current-title" class="mm-rail__meta-title">Current model run</h2>
      <dl class="mm-facts">
        <div>
          <dt>Departure</dt>
          <dd>{{ formatClock(departureMinute) }} · Maldives time (UTC+5)</dd>
        </div>
        <div>
          <dt>Network</dt>
          <dd>{{ networkFact }}</dd>
        </div>
        <div>
          <dt>Threshold</dt>
          <dd>{{ thresholdLabel }}</dd>
        </div>
        <div>
          <dt>Scenario</dt>
          <dd>
            {{ scenarioMode === 'baseline' ? 'Baseline' : 'User scenario active' }}
            <span v-if="filterActive" class="mm-tag mm-tag--accent">filtered</span>
          </dd>
        </div>
        <div v-if="networkPreset === 'custom'">
          <dt>Preset</dt>
          <dd>Custom</dd>
        </div>
      </dl>
    </section>
      </div>
    </details>
  </div>
</template>
