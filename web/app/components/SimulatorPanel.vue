<script setup lang="ts">
import { computed } from 'vue'
import type { MultimodalStore } from '../composables/useMultimodal'
import type { Island } from '../../shared/routing/types'
import { formatClock, parseClock } from '../utils/format'

const props = defineProps<{
  store: MultimodalStore
  disabled?: boolean
}>()

const {
  scenarioMode,
  newFacilityName,
  newFacilityKind,
  newFacilityCategory,
  newFacilityIslandId,
  newSeaFromIslandId,
  newSeaToIslandId,
  newSeaDepartureMinute,
  newSeaTripsPerDay,
  newSeaMinutes,
  newLandFromIslandId,
  newLandToIslandId,
  newLandMinutes,
  categories,
  origins,
  simulatorValidationError,
  scenarioDescription,
  scenarioError,
  canResetScenario,
  resetScenario,
  selectedOrigin,
} = props.store

const SIMULATOR_MODES = [
  { value: 'add_facility', label: 'Add facility', hint: 'Hypothetical facility' },
  { value: 'add_sea_route', label: 'Add sea route', hint: 'Assumed scheduled link' },
  { value: 'add_land_link', label: 'Add land link', hint: 'Assumed road or bridge' },
] as const

const isSimulatorMode = computed(
  () => scenarioMode.value.startsWith('add_') && scenarioMode.value !== 'add_trip',
)

const seaDepartureTime = computed({
  get: () => formatClock(newSeaDepartureMinute.value),
  set: (value: string) => {
    newSeaDepartureMinute.value = parseClock(value, newSeaDepartureMinute.value)
  },
})

function originName(islandId: string): string {
  return origins.value.find((island: Island) => island.id === islandId)?.name ?? islandId
}

const seaArrival = computed(() => {
  const arrival = newSeaDepartureMinute.value + Math.max(1, newSeaMinutes.value)
  return arrival >= 1440 ? `${formatClock(arrival)} (+1 day)` : formatClock(arrival)
})
</script>

<template>
  <section class="mm-rail__section mm-simulator" aria-labelledby="mm-simulator-title">
    <h2 id="mm-simulator-title" class="mm-rail__title mm-rail__title--small">
      Intervention simulator
    </h2>
    <p class="mm-hint">
      Simulate one user-defined intervention, then read the baseline-versus-scenario comparison.
      These are assumptions, not observed services or proposed policy.
    </p>

    <fieldset class="mm-fieldset">
      <legend class="mm-label">Intervention type</legend>
      <div class="mm-seg mm-seg--three" role="radiogroup" aria-label="Intervention simulator type">
        <label v-for="mode in SIMULATOR_MODES" :key="mode.value" class="mm-seg__item">
          <input
            v-model="scenarioMode"
            type="radio"
            name="mm-simulator-mode"
            :value="mode.value"
            :disabled="disabled"
          />
          <span class="mm-seg__label">
            {{ mode.label }}
            <span class="mm-seg__hint">{{ mode.hint }}</span>
          </span>
        </label>
      </div>
      <p v-if="!isSimulatorMode" class="mm-hint mm-hint--tight">
        Choose an intervention type to open its form. Timetable changes remain available in the
        Scenario section below.
      </p>
    </fieldset>

    <div v-if="isSimulatorMode" class="mm-simulator__form">
      <template v-if="scenarioMode === 'add_facility'">
        <p class="mm-notice mm-notice--assumption" role="note">
          <strong>Assumption.</strong> The facility is placed at island level. No building
          location, staffing, opening hours or service availability is modelled.
        </p>
        <label class="mm-field">
          <span class="mm-label">Facility name</span>
          <input
            v-model="newFacilityName"
            class="mm-input"
            type="text"
            placeholder="e.g. Proposed health centre"
            :disabled="disabled"
          />
        </label>
        <div class="mm-field-row">
          <label class="mm-field">
            <span class="mm-label">Kind</span>
            <select v-model="newFacilityKind" class="mm-input" :disabled="disabled">
              <option value="health">Health</option>
              <option value="education">Education</option>
            </select>
          </label>
          <label class="mm-field">
            <span class="mm-label">Island</span>
            <select v-model="newFacilityIslandId" class="mm-input" :disabled="disabled">
              <option v-for="island in origins" :key="island.id" :value="island.id">
                {{ island.name }} · {{ island.atollName }} · {{ island.population }} residents
              </option>
            </select>
          </label>
        </div>
        <label class="mm-field">
          <span class="mm-label">Category</span>
          <select v-model="newFacilityCategory" class="mm-input" :disabled="disabled">
            <option v-for="definition in categories" :key="definition.id" :value="definition.id">
              {{ definition.label }}
            </option>
          </select>
          <span class="mm-hint">
            Intervention categories (e.g. dialysis) can also be simulated. A user-added facility
            is never merged into the source facility master.
          </span>
        </label>
        <p class="mm-hint">
          The facility joins the selected category at {{ originName(newFacilityIslandId) }}. It
          is appended as a user-added record and never merged into the source facility master.
        </p>
      </template>

      <template v-else-if="scenarioMode === 'add_sea_route'">
        <p class="mm-notice mm-notice--assumption" role="note">
          <strong>Assumption.</strong> The crossing time and schedule are user-entered. Sea links
          use ferry boarding buffers but no published timetable or observed demand.
        </p>
        <div class="mm-field-row">
          <label class="mm-field">
            <span class="mm-label">From island</span>
            <select v-model="newSeaFromIslandId" class="mm-input" :disabled="disabled">
              <option v-for="island in origins" :key="island.id" :value="island.id">
                {{ island.name }} · {{ island.atollName }}
              </option>
            </select>
          </label>
          <label class="mm-field">
            <span class="mm-label">To island</span>
            <select v-model="newSeaToIslandId" class="mm-input" :disabled="disabled">
              <option v-for="island in origins" :key="island.id" :value="island.id">
                {{ island.name }} · {{ island.atollName }}
              </option>
            </select>
          </label>
        </div>
        <div class="mm-field-row mm-field-row--three">
          <label class="mm-field">
            <span class="mm-label">First departure</span>
            <input v-model="seaDepartureTime" class="mm-input" type="time" step="60" :disabled="disabled" />
          </label>
          <label class="mm-field">
            <span class="mm-label">Trips/day</span>
            <input v-model.number="newSeaTripsPerDay" class="mm-input" type="number" min="1" max="12" :disabled="disabled" />
          </label>
          <label class="mm-field">
            <span class="mm-label">Crossing (min)</span>
            <input v-model.number="newSeaMinutes" class="mm-input" type="number" min="5" max="600" step="5" :disabled="disabled" />
          </label>
        </div>
        <p class="mm-hint">
          {{ newSeaTripsPerDay }} trip(s)/day spread across a 12-hour window from
          {{ formatClock(newSeaDepartureMinute) }}; last arrival about {{ seaArrival }}.
          Direction: {{ originName(newSeaFromIslandId) }} → {{ originName(newSeaToIslandId) }}.
        </p>
      </template>

      <template v-else>
        <p class="mm-notice mm-notice--assumption" role="note">
          <strong>Assumption.</strong> The link is a direct bidirectional land connection. No
          bridge, causeway or road is verified by this record.
        </p>
        <div class="mm-field-row">
          <label class="mm-field">
            <span class="mm-label">From island</span>
            <select v-model="newLandFromIslandId" class="mm-input" :disabled="disabled">
              <option v-for="island in origins" :key="island.id" :value="island.id">
                {{ island.name }} · {{ island.atollName }}
              </option>
            </select>
          </label>
          <label class="mm-field">
            <span class="mm-label">To island</span>
            <select v-model="newLandToIslandId" class="mm-input" :disabled="disabled">
              <option v-for="island in origins" :key="island.id" :value="island.id">
                {{ island.name }} · {{ island.atollName }}
              </option>
            </select>
          </label>
        </div>
        <label class="mm-field">
          <span class="mm-label">Travel time (minutes)</span>
          <input v-model.number="newLandMinutes" class="mm-input" type="number" min="1" max="600" :disabled="disabled" />
        </label>
        <p class="mm-hint">
          Adds a bidirectional road edge between {{ originName(newLandFromIslandId) }} and
          {{ originName(newLandToIslandId) }}. Both endpoint islands must already be in the
          prepared network.
        </p>
      </template>

      <p v-if="simulatorValidationError" class="mm-alert mm-alert--info" role="status">
        {{ simulatorValidationError }}
      </p>
      <p v-else-if="scenarioError" class="mm-alert mm-alert--warn" role="alert">
        {{ scenarioError }}
      </p>
      <p v-else-if="scenarioDescription && scenarioMode !== 'baseline'" class="mm-hint">
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
        <span class="mm-hint mm-hint--tight">
          Origin for journey card: {{ selectedOrigin?.name ?? '—' }}.
        </span>
      </div>
    </div>
  </section>
</template>
