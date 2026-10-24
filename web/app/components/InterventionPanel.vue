<script setup lang="ts">
import { computed } from 'vue'
import type { MultimodalStore } from '../composables/useMultimodal'
import { formatDuration, formatPercent } from '../utils/format'

const props = defineProps<{ store: MultimodalStore }>()

const {
  categoryIsIntervention,
  selectedCategory,
  interventionRows,
  interventionLoading,
  interventionError,
  interventionCategories,
  selectedOrigin,
} = props.store

const reachableCount = computed(() => interventionRows.value.filter((row) => row.reachable).length)

const groupedCount = computed(
  () => new Set(interventionRows.value.map((row) => row.islandId)).size,
)

const reachableShare = computed(() =>
  interventionRows.value.length > 0 ? reachableCount.value / interventionRows.value.length : 0,
)

const originLabel = computed(() => selectedOrigin.value?.name ?? 'the selected origin')

const claimLabel = computed(() => selectedCategory.value?.label ?? 'claims')

const rowsByIsland = computed(() => {
  const map = new Map<string, typeof interventionRows.value>()
  for (const row of interventionRows.value) {
    const current = map.get(row.islandId) ?? []
    current.push(row)
    map.set(row.islandId, current)
  }
  return [...map.entries()].map(([islandId, rows]) => ({
    islandId,
    islandName: rows[0]?.islandName ?? islandId,
    atollName: rows[0]?.atollName ?? '',
    population: rows[0]?.population ?? 0,
    reachable: rows.some((row) => row.reachable),
    minutes: rows.find((row) => row.reachable)?.minutes ?? null,
    rows,
  }))
})
</script>

<template>
  <section class="mm-panel mm-panel--wide mm-interventions" aria-labelledby="mm-interventions-title">
    <header class="mm-panel__head">
      <div>
        <h2 id="mm-interventions-title" class="mm-panel__title">
          {{ selectedCategory?.label ?? 'Intervention coverage' }}
        </h2>
        <p class="mm-panel__sub mm-one-line">
          <template v-if="categoryIsIntervention">
            Claims on islands reachable from {{ originLabel }}
          </template>
          <template v-else>Facility category · intervention evidence available separately</template>
        </p>
      </div>
      <span v-if="categoryIsIntervention" class="mm-tag mm-tag--accent">
        {{ reachableCount }} / {{ interventionRows.length }} reachable
      </span>
    </header>

    <template v-if="!categoryIsIntervention">
      <p class="mm-data__line">
        This is a facility category. Intervention coverage appears for evidence categories such as
        dialysis or dental.
      </p>
      <details v-if="interventionCategories.length" class="mm-data-details">
        <summary>{{ interventionCategories.length }} intervention categories published</summary>
        <p class="mm-interventions__categories">
          <span v-for="definition in interventionCategories" :key="definition.id" class="mm-chip">
            {{ definition.label }} ({{ definition.facilityCount }})
          </span>
        </p>
      </details>
      <p v-else class="mm-data__line">No intervention categories are published yet.</p>
    </template>

    <template v-else>
      <p v-if="interventionLoading" class="mm-loading-inline" role="status">
        <span class="mm-spinner mm-spinner--small" aria-hidden="true" /> Checking islands…
      </p>
      <p v-else-if="interventionError" class="mm-alert mm-alert--warn" role="alert">
        {{ interventionError }}
      </p>

      <template v-else-if="interventionRows.length">
        <div class="mm-interventions__kpis">
          <div class="mm-mini-stat">
            <strong>{{ interventionRows.length }}</strong>
            <span>facility claims</span>
          </div>
          <div class="mm-mini-stat">
            <strong>{{ groupedCount }}</strong>
            <span>islands</span>
          </div>
          <div class="mm-mini-stat">
            <strong>{{ reachableCount }}</strong>
            <span>reachable</span>
          </div>
          <div class="mm-mini-stat mm-mini-stat--wide">
            <strong>{{ formatPercent(reachableShare) }}</strong>
            <span>of claims reachable from {{ originLabel }}</span>
          </div>
        </div>

        <p class="mm-insight-line">
          <span class="mm-chip mm-chip--derived">network access</span>
          {{ reachableCount }} of {{ interventionRows.length }} {{ claimLabel }} claims reachable
          from {{ originLabel }}.
        </p>

        <div
          class="mm-seg-bar mm-seg-bar--intervention"
          role="img"
          :aria-label="`${reachableCount} reachable claims and ${interventionRows.length - reachableCount} not reachable`"
        >
          <span class="mm-seg-bar__part mm-seg-bar__part--reachable" :style="{ width: `${reachableShare * 100}%` }" />
          <span
            class="mm-seg-bar__part mm-seg-bar__part--unreachable"
            :style="{ width: `${(1 - reachableShare) * 100}%` }"
          />
        </div>

        <details class="mm-data-details">
          <summary>How reachability is defined</summary>
          <p class="mm-muted">
            Physical network access from {{ originLabel }} to the island under the current network
            and scenario. Island level only — not confirmation that a service is open, staffed or
            bookable. Resorts and guest-only claims are excluded upstream.
          </p>
        </details>

        <div class="mm-interventions__list">
          <article
            v-for="group in rowsByIsland"
            :key="group.islandId"
            class="mm-intervention"
            :class="{ 'mm-intervention--unreachable': !group.reachable }"
          >
            <div class="mm-intervention__head">
              <h3 class="mm-intervention__island">{{ group.islandName }}</h3>
              <span class="mm-chip">{{ group.atollName }}</span>
              <span class="mm-chip">{{ group.population }} residents</span>
              <span v-if="group.reachable" class="mm-tag mm-tag--good">
                {{ group.minutes !== null ? formatDuration(group.minutes) : 'Reachable' }}
              </span>
              <span v-else class="mm-tag mm-tag--muted">No same-day trip</span>
            </div>
            <ul class="mm-intervention__facilities">
              <li v-for="row in group.rows" :key="row.facilityId" class="mm-intervention__facility">
                <span class="mm-intervention__name">{{ row.facilityName }}</span>
                <span class="mm-intervention__meta">
                  <span class="mm-chip">{{ row.confidence ?? 'evidence' }}</span>
                  <span v-if="row.sourceDate" class="mm-chip">{{ row.sourceDate }}</span>
                  <span v-if="row.userAdded" class="mm-chip mm-chip--accent">user-added</span>
                </span>
                <span v-if="row.detail" class="mm-intervention__detail" :title="row.detail">
                  {{ row.detail }}
                </span>
              </li>
            </ul>
          </article>
        </div>
      </template>

      <p v-else class="mm-data__line">
        No facility claims this intervention. A data-coverage statement, not evidence the service
        is unavailable.
      </p>
    </template>
  </section>
</template>
