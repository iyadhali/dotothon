<script setup lang="ts">
import { computed, ref } from 'vue'
import type { MultimodalStore } from '../composables/useMultimodal'
import { MODE_OPTIONS, PRESET_OPTIONS } from '../utils/selection'
import { formatPopulation } from '../utils/format'

const props = defineProps<{
  store: MultimodalStore
  disabled?: boolean
}>()

const {
  networkPreset,
  landEnabled,
  seaEnabled,
  airEnabled,
  disabledFerryRouteIds,
  disabledAirPairIds,
  routeCatalog,
  enabledRouteCount,
  filterActive,
  modeFlags,
  meta,
  setModeEnabled,
  setRouteEnabled,
  setAllRoutes,
  resetNetworkSelection,
} = props.store

const routeQuery = ref('')

const ferryEnabled = computed(
  () => routeCatalog.value.ferries.length - disabledFerryRouteIds.value.length,
)
const airRoutesEnabled = computed(
  () => routeCatalog.value.air.length - disabledAirPairIds.value.length,
)

const query = computed(() => routeQuery.value.trim().toLowerCase())

const visibleFerries = computed(() =>
  routeCatalog.value.ferries.filter(
    (entry) => !query.value || entry.searchText.includes(query.value),
  ),
)
const visibleAir = computed(() =>
  routeCatalog.value.air.filter(
    (entry) => !query.value || entry.searchText.includes(query.value),
  ),
)

const activeModesLabel = computed(() => {
  const flags = modeFlags.value
  const names: string[] = []
  if (flags.land) names.push('Land')
  if (flags.sea) names.push('Sea')
  if (flags.air) names.push('Air')
  return names.length ? names.join(' + ') : 'No modes selected'
})

function routeChecked(kind: 'ferry' | 'air', key: string): boolean {
  return kind === 'ferry'
    ? !disabledFerryRouteIds.value.includes(key)
    : !disabledAirPairIds.value.includes(key)
}

function onModeChange(mode: 'land' | 'sea' | 'air', event: Event): void {
  const target = event.target as HTMLInputElement | null
  setModeEnabled(mode, target?.checked ?? false)
}

function onRouteChange(
  kind: 'ferry' | 'air',
  key: string,
  event: Event,
): void {
  const target = event.target as HTMLInputElement | null
  setRouteEnabled(kind, key, target?.checked ?? false)
}
</script>

<template>
  <section class="mm-rail__section mm-network" aria-labelledby="mm-network-title">
    <h2 id="mm-network-title" class="mm-rail__title mm-rail__title--small">Transport network</h2>
    <p class="mm-hint">
      Choose which modelled modes and routes count as available. This is a user selection:
      excluding a route removes supply from the model, it does not erase the island's physical
      infrastructure.
    </p>

    <fieldset class="mm-fieldset">
      <legend class="mm-label">Preset</legend>
      <div class="mm-seg mm-seg--network" role="radiogroup" aria-label="Network preset">
        <label v-for="preset in PRESET_OPTIONS" :key="preset.key" class="mm-seg__item">
          <input v-model="networkPreset" type="radio" name="mm-network-preset" :value="preset.key" />
          <span class="mm-seg__label">{{ preset.shortLabel }}</span>
        </label>
      </div>
      <p class="mm-hint">
        <template v-if="networkPreset === 'custom'">Custom: {{ activeModesLabel }}.</template>
        <template v-else>
          {{ PRESET_OPTIONS.find((preset) => preset.key === networkPreset)?.description }}
        </template>
      </p>
    </fieldset>

    <fieldset class="mm-fieldset">
      <legend class="mm-label">Custom modes</legend>
      <div class="mm-mode-list">
        <label v-for="mode in MODE_OPTIONS" :key="mode.key" class="mm-mode">
          <input
            type="checkbox"
            :value="mode.key"
            :checked="
              mode.key === 'land' ? landEnabled : mode.key === 'sea' ? seaEnabled : airEnabled
            "
            :disabled="disabled"
            @change="onModeChange(mode.key, $event)"
          />
          <span class="mm-mode__text">
            <span class="mm-mode__label">{{ mode.label }}</span>
            <span class="mm-hint mm-hint--tight">{{ mode.description }}</span>
          </span>
        </label>
      </div>
      <p v-if="!landEnabled && !seaEnabled && !airEnabled" class="mm-alert mm-alert--warn" role="alert">
        No transport modes are selected. Every origin island will be reported as not selected
        rather than unreachable; the baseline has not become zero access.
      </p>
    </fieldset>

    <details class="mm-routes">
      <summary class="mm-routes__summary">
        <span>Route checklist</span>
        <span class="mm-routes__count">
          {{ enabledRouteCount }} enabled · {{ ferryEnabled }}/{{ routeCatalog.ferries.length }} ferry ·
          {{ airRoutesEnabled }}/{{ routeCatalog.air.length }} air pairs
        </span>
      </summary>

      <div class="mm-routes__body">
        <label class="mm-field">
          <span class="mm-label">Filter routes</span>
          <input
            v-model="routeQuery"
            class="mm-input"
            type="search"
            placeholder="Search route, island or code"
            autocomplete="off"
          />
        </label>

        <div class="mm-routes__group" role="group" aria-labelledby="mm-routes-ferry">
          <div class="mm-routes__head">
            <h3 id="mm-routes-ferry" class="mm-routes__title">
              Ferry routes <span>{{ ferryEnabled }}/{{ routeCatalog.ferries.length }}</span>
            </h3>
            <div class="mm-routes__actions">
              <button type="button" class="mm-linkbtn" @click="setAllRoutes('ferry', true)">
                All
              </button>
              <button type="button" class="mm-linkbtn" @click="setAllRoutes('ferry', false)">
                None
              </button>
            </div>
          </div>
          <ul class="mm-routes__list">
            <li v-for="entry in visibleFerries" :key="entry.key">
              <label class="mm-route">
                <input
                  type="checkbox"
                  :checked="routeChecked('ferry', entry.key)"
                  @change="onRouteChange('ferry', entry.key, $event)"
                />
                <span>{{ entry.label }}</span>
                <span class="mm-route__meta">{{ entry.serviceIds.length }} trip{{ entry.serviceIds.length === 1 ? '' : 's' }}</span>
              </label>
            </li>
            <li v-if="visibleFerries.length === 0" class="mm-hint">No ferry route matches this filter.</li>
          </ul>
        </div>

        <div class="mm-routes__group" role="group" aria-labelledby="mm-routes-air">
          <div class="mm-routes__head">
            <h3 id="mm-routes-air" class="mm-routes__title">
              Air pairs <span>{{ airRoutesEnabled }}/{{ routeCatalog.air.length }}</span>
            </h3>
            <div class="mm-routes__actions">
              <button type="button" class="mm-linkbtn" @click="setAllRoutes('air', true)">
                All
              </button>
              <button type="button" class="mm-linkbtn" @click="setAllRoutes('air', false)">
                None
              </button>
            </div>
          </div>
          <p class="mm-hint mm-hint--tight">
            Both directions are toggled together. Air is an estimated frequency model, not a
            published flight schedule.
          </p>
          <ul class="mm-routes__list">
            <li v-for="entry in visibleAir" :key="entry.key">
              <label class="mm-route">
                <input
                  type="checkbox"
                  :checked="routeChecked('air', entry.key)"
                  @change="onRouteChange('air', entry.key, $event)"
                />
                <span>{{ entry.label }}</span>
                <span class="mm-route__meta">{{ entry.serviceIds.length }} dir.</span>
              </label>
            </li>
            <li v-if="visibleAir.length === 0" class="mm-hint">No air pair matches this filter.</li>
          </ul>
        </div>

        <p class="mm-hint">
          Unchecked routes are <strong>not selected</strong>; an island whose access depended only
          on them is labelled "not selected", not "no access". Islands with no infrastructure in
          the prepared network stay "no origin access".
          <span v-if="filterActive" class="mm-hint__meta">
            Active filter: {{ activeModesLabel }}; {{ enabledRouteCount }} routes enabled.
          </span>
        </p>
        <button type="button" class="mm-btn mm-btn--ghost" @click="resetNetworkSelection">
          Reset network selection
        </button>
      </div>
    </details>

    <p class="mm-facts__inline">
      <span>{{ formatPopulation(meta?.counts.origins ?? 0) }} origin islands in scope</span>
      <span v-if="filterActive" class="mm-tag mm-tag--accent">Filter active</span>
    </p>
  </section>
</template>
