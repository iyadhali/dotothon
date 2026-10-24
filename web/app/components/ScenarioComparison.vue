<script setup lang="ts">
import { computed } from 'vue'
import { BAND_BY_KEY } from '../utils/bands'
import type { ScenarioComparison, ThresholdMinutes } from '../utils/analysis'
import {
  formatDuration,
  formatPopulation,
  formatSignedNumber,
} from '../utils/format'

const props = defineProps<{
  scenarioActive: boolean
  scenarioDescription: string
  comparison: ScenarioComparison | null
  threshold: ThresholdMinutes
  loading: boolean
}>()

const visibleChanges = computed(() => (props.comparison?.changes ?? []).slice(0, 6))

function bandLabel(key: string): string {
  return BAND_BY_KEY[key as keyof typeof BAND_BY_KEY]?.shortLabel ?? key
}

const withinDelta = computed(() => props.comparison?.withinDeltas[props.threshold] ?? 0)
</script>

<template>
  <section class="mm-panel" aria-labelledby="mm-scenario-heading">
    <header class="mm-panel__head">
      <div>
        <h2 id="mm-scenario-heading" class="mm-panel__title">Scenario comparison</h2>
        <p class="mm-panel__sub">
          User-defined change versus baseline; scenarios are hypothetical.
        </p>
      </div>
      <span class="mm-tag mm-tag--scenario">{{ scenarioActive ? 'Scenario active' : 'Baseline' }}</span>
    </header>

    <div v-if="!scenarioActive" class="mm-empty" role="status">
      <p>
        The baseline model is shown. Add a timetable change or simulate an intervention in the
        control rail to compare access against this baseline.
      </p>
    </div>

    <div v-else-if="loading" class="mm-skeleton" role="status">
      <span class="mm-spinner" aria-hidden="true" />
      <span>Applying the scenario and recomputing both networks…</span>
    </div>

    <div v-else-if="!comparison" class="mm-empty" role="status">
      The scenario result is not available. Check the scenario controls for an error.
    </div>

    <template v-else>
      <p class="mm-scenario-desc">{{ scenarioDescription }}</p>

      <div class="mm-delta-grid">
        <div>
          <span class="mm-eyebrow">Newly reachable people</span>
          <strong>{{ formatPopulation(comparison.newlyReachablePopulation) }}</strong>
          <span class="mm-muted">residents gaining any same-day access</span>
        </div>
        <div>
          <span class="mm-eyebrow">Reachable population change</span>
          <strong>{{ formatSignedNumber(comparison.reachableDelta) }}</strong>
          <span class="mm-muted">residents vs baseline</span>
        </div>
        <div>
          <span class="mm-eyebrow">Within {{ formatDuration(threshold) }} change</span>
          <strong>{{ formatSignedNumber(withinDelta) }}</strong>
          <span class="mm-muted">residents crossing the threshold</span>
        </div>
        <div>
          <span class="mm-eyebrow">Origin islands changed</span>
          <strong>{{ comparison.originsChanged }}</strong>
          <span class="mm-muted">{{ comparison.originsRetimed }} more retimed within a band</span>
        </div>
      </div>

      <div v-if="comparison.newlyCovered.length > 0" class="mm-newly-covered">
        <h3 class="mm-subhead">Newly covered origins</h3>
        <p class="mm-muted">
          Islands with no same-day reachable facility in the baseline that become reachable
          under this user scenario.
        </p>
        <ul>
          <li v-for="origin in comparison.newlyCovered.slice(0, 8)" :key="origin.islandId">
            <strong>{{ origin.name }}</strong>
            <span class="mm-muted">{{ origin.atollName }} · {{ formatPopulation(origin.population) }} residents</span>
            <span v-if="origin.minutes !== null" class="mm-tag mm-tag--good">
              {{ formatDuration(origin.minutes) }}
            </span>
          </li>
        </ul>
        <p v-if="comparison.newlyCovered.length > 8" class="mm-muted">
          Showing 8 of {{ comparison.newlyCovered.length }} newly covered origins by population.
        </p>
      </div>

      <div v-if="visibleChanges.length > 0" class="mm-changes">
        <h3 class="mm-subhead">Origins that changed band</h3>
        <ul>
          <li v-for="change in visibleChanges" :key="change.islandId">
            <div class="mm-change__who">
              <strong>{{ change.name }}</strong>
              <span class="mm-muted">{{ change.atollName }} · {{ formatPopulation(change.population) }}</span>
            </div>
            <div class="mm-change__route">
              <span class="mm-bandchip">{{ bandLabel(change.beforeBand) }}</span>
              <span aria-hidden="true" class="mm-arrow">→</span>
              <span class="mm-bandchip">{{ bandLabel(change.afterBand) }}</span>
            </div>
            <span
              class="mm-tag"
              :class="change.direction === 'improved' ? 'mm-tag--good' : 'mm-tag--warn'"
            >
              {{ change.direction === 'improved' ? 'Faster' : 'Slower' }}
            </span>
          </li>
        </ul>
        <p v-if="comparison.changes.length > visibleChanges.length" class="mm-muted">
          Showing {{ visibleChanges.length }} of {{ comparison.changes.length }} changed islands,
          largest and most improved first.
        </p>
      </div>

      <p v-else class="mm-empty" role="status">
        No origin island changed travel-time band under this scenario. Retimed journeys inside
        the same band are not listed.
      </p>

      <p class="mm-panel__foot">
        Added trips, cancellations, delays, facilities, sea links and land links are user
        scenarios applied to a copy of the network for comparison. They are not observed
        demand, proposed policy or confirmed service changes. Verified and estimated labels
        describe the base data only.
      </p>
    </template>
  </section>
</template>
