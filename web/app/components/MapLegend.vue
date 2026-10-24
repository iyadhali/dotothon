<script setup lang="ts">
import { computed } from 'vue'
import {
  LEGEND_BANDS,
  patternBackground,
  type IslandBandInfo,
  type TravelBandKey,
} from '../utils/bands'

const props = defineProps<{
  bands: Record<string, IslandBandInfo>
  loading?: boolean
  filterActive?: boolean
}>()

const counts = computed<Partial<Record<TravelBandKey, number>>>(() => {
  const tally: Partial<Record<TravelBandKey, number>> = {}
  for (const info of Object.values(props.bands)) {
    tally[info.band] = (tally[info.band] ?? 0) + 1
  }
  return tally
})

function countLabel(key: TravelBandKey): string | null {
  const count = counts.value[key]
  if (!count) return null
  return `${count} island${count === 1 ? '' : 's'}`
}
</script>

<template>
  <div class="mm-legend" role="group" aria-label="Map band legend">
    <div class="mm-legend__head">
      <h3 class="mm-legend__title">Map legend</h3>
      <p class="mm-legend__note">
        Travel time from each origin island to its nearest eligible facility.
        <span v-if="filterActive" class="mm-legend__filter">Network filter active: “Not selected” is a user choice, not a coverage gap.</span>
        <span v-if="loading" class="mm-legend__loading" role="status">updating…</span>
      </p>
    </div>
    <ul class="mm-legend__list">
      <li v-for="band in LEGEND_BANDS" :key="band.key" class="mm-legend__item" :title="band.description">
        <span
          class="mm-swatch"
          aria-hidden="true"
          :style="{
            backgroundColor: band.color,
            backgroundImage: patternBackground(band.pattern),
            borderColor: band.pattern === 'none' ? 'transparent' : '#233d36',
          }"
        />
        <span class="mm-legend__label">
          {{ band.label }}
          <span v-if="countLabel(band.key)" class="mm-legend__count">{{ countLabel(band.key) }}</span>
        </span>
      </li>
    </ul>
    <p class="mm-legend__foot">
      Hatching marks coverage states, never travel times. Labels name every band, so colour
      is not the only signal.
    </p>
  </div>
</template>
