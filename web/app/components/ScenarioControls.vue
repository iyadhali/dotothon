<script setup lang="ts">
import { computed } from 'vue'
import type { MultimodalStore } from '../composables/useMultimodal'
import { formatClock, parseClock } from '../utils/format'
import { DELAY_MINUTES } from '../composables/useMultimodal'

const props = defineProps<{
  store: MultimodalStore
  disabled?: boolean
}>()

const {
  scenarioMode,
  addedRouteId,
  addedFirstDepartureMinute,
  cancelledServiceId,
  delayedServiceId,
  routePatterns,
  serviceOptions,
  selectedRouteFirstDeparture,
  canResetScenario,
  scenarioError,
  scenarioDescription,
  resetScenario,
} = props.store

const TIMETABLE_MODES = [
  { value: 'baseline', label: 'Baseline', hint: 'Prepared reference day' },
  { value: 'add_trip', label: 'Add morning trip', hint: 'Extra departure' },
  { value: 'cancel_service', label: 'Cancel service', hint: 'Remove one trip' },
  { value: 'delay_service', label: 'Delay service', hint: `${DELAY_MINUTES} minutes late` },
] as const

const isTimetableMode = computed(
  () =>
    scenarioMode.value === 'baseline' ||
    scenarioMode.value === 'add_trip' ||
    scenarioMode.value === 'cancel_service' ||
    scenarioMode.value === 'delay_service',
)

const addedTime = computed({
  get: () => formatClock(addedFirstDepartureMinute.value),
  set: (value: string) => {
    addedFirstDepartureMinute.value = parseClock(value, addedFirstDepartureMinute.value)
  },
})

const selectedPatternLabel = computed(
  () => routePatterns.value.find((pattern) => pattern.routeId === addedRouteId.value)?.label ?? '',
)
</script>

<template>
  <section class="mm-rail__section" aria-labelledby="mm-scenario-title">
    <h2 id="mm-scenario-title" class="mm-rail__title mm-rail__title--small">Scenario</h2>
    <p class="mm-hint">
      Baseline uses the prepared reference-day services. Scenarios are hypothetical user changes,
      not observed operations or demand forecasts.
    </p>

    <fieldset class="mm-fieldset">
      <legend class="mm-label">Timetable scenario</legend>
      <div class="mm-seg mm-seg--four" role="radiogroup" aria-label="Timetable scenario type">
        <label v-for="mode in TIMETABLE_MODES" :key="mode.value" class="mm-seg__item">
          <input
            v-model="scenarioMode"
            type="radio"
            name="mm-scenario-mode"
            :value="mode.value"
            :disabled="disabled"
          />
          <span class="mm-seg__label">
            {{ mode.label }}
            <span class="mm-seg__hint">{{ mode.hint }}</span>
          </span>
        </label>
      </div>
    </fieldset>

    <div v-if="isTimetableMode" class="mm-scenario__form">
      <template v-if="scenarioMode === 'add_trip'">
        <label class="mm-field">
          <span class="mm-label">Route pattern</span>
          <select v-model="addedRouteId" class="mm-input" :disabled="disabled">
            <option v-for="pattern in routePatterns" :key="pattern.routeId" :value="pattern.routeId">
              {{ pattern.label }}
            </option>
          </select>
        </label>
        <label class="mm-field">
          <span class="mm-label">New first departure</span>
          <input v-model="addedTime" class="mm-input" type="time" step="60" :disabled="disabled" />
          <span class="mm-hint">
            Repeats the same stop pattern with its first departure at
            {{ formatClock(addedFirstDepartureMinute) }}.
            <template v-if="selectedRouteFirstDeparture">
              The earliest existing departure is
              {{ formatClock(selectedRouteFirstDeparture.minute) }}.
            </template>
            <template v-if="selectedPatternLabel"> Pattern: {{ selectedPatternLabel }}.</template>
          </span>
        </label>
      </template>

      <template v-else-if="scenarioMode === 'cancel_service'">
        <label class="mm-field">
          <span class="mm-label">Service to cancel</span>
          <select v-model="cancelledServiceId" class="mm-input" :disabled="disabled">
            <option v-for="service in serviceOptions" :key="service.id" :value="service.id">
              {{ service.label }}
            </option>
          </select>
        </label>
        <p class="mm-hint">
          Removes exactly one timetabled trip. It does not cancel the whole route or imply a
          real-world disruption.
        </p>
      </template>

      <template v-else-if="scenarioMode === 'delay_service'">
        <label class="mm-field">
          <span class="mm-label">Service to delay</span>
          <select v-model="delayedServiceId" class="mm-input" :disabled="disabled">
            <option v-for="service in serviceOptions" :key="service.id" :value="service.id">
              {{ service.label }}
            </option>
          </select>
        </label>
        <p class="mm-hint">
          Delays every stop on the trip by {{ DELAY_MINUTES }} minutes. Later trips are unchanged.
        </p>
      </template>

      <p v-if="scenarioError" class="mm-alert mm-alert--warn" role="alert">{{ scenarioError }}</p>
      <p v-else-if="scenarioMode !== 'baseline'" class="mm-hint">
        {{ scenarioDescription }}
      </p>

      <div class="mm-actions">
        <button
          type="button"
          class="mm-btn mm-btn--ghost"
          :disabled="disabled || !canResetScenario"
          @click="resetScenario"
        >
          Reset scenario
        </button>
      </div>
    </div>
    <p v-else class="mm-hint mm-hint--tight">
      A timetable change is not active. Select Baseline, Add morning trip, Cancel service or
      Delay service to edit one.
    </p>
  </section>
</template>
