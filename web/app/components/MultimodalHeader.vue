<script setup lang="ts">
import { computed } from 'vue'
import { formatDate } from '../utils/format'

const props = defineProps<{
  dataSource: 'api' | 'static' | 'fixture' | null
  dataStatus: 'loading' | 'ready' | 'error'
  referenceDay: string | null
  generatedAt: string | null
}>()

const sourceLabel = computed(() => {
  if (props.dataStatus === 'loading') return 'Loading prepared network…'
  if (props.dataSource === 'fixture') return 'Fixture data'
  if (props.dataSource === 'static') return 'Static fallback'
  if (props.dataSource === 'api') return 'SQLite API'
  return 'Prepared network'
})
</script>

<template>
  <header class="mm-header">
    <div class="mm-header__main">
      <div class="mm-brand">
        <span class="mm-brand__mark" aria-hidden="true">
          <svg viewBox="0 0 44 44" width="44" height="44" role="presentation">
            <circle cx="22" cy="22" r="21" fill="#233d36" />
            <path
              d="M8 25c4-5 8-5 12 0s8 5 12 0"
              fill="none"
              stroke="#ffffff"
              stroke-width="2.2"
              stroke-linecap="round"
            />
            <circle cx="15" cy="16" r="2.1" fill="#e3c477" />
            <circle cx="25" cy="13" r="1.6" fill="#9dbf8f" />
            <circle cx="32" cy="17" r="1.3" fill="#d78f60" />
          </svg>
        </span>
        <div class="mm-brand__text">
          <p class="mm-eyebrow">Maldives · multimodal accessibility prototype</p>
          <h1>Island Access Atlas</h1>
          <p class="mm-lede">
            Ferry + air access to health and education, modelled on one reference day.
          </p>
        </div>
      </div>

      <div class="mm-header__status">
        <span class="mm-badge mm-badge--day">
          Reference day
          <strong>{{ referenceDay ? formatDate(referenceDay) : 'not loaded' }}</strong>
        </span>
        <span class="mm-badge mm-badge--warn">Calendar unverified</span>
        <span
          v-if="dataSource === 'fixture'"
          class="mm-badge mm-badge--fixture"
          title="The page is using the bundled sample network, not prepared real data."
        >
          Fixture data — no real-world claims
        </span>
        <span v-else class="mm-badge mm-badge--ok">{{ sourceLabel }}</span>
        <span v-if="generatedAt" class="mm-header__generated">
          Prepared {{ formatDate(generatedAt) }}
        </span>
      </div>
    </div>

    <div class="mm-confidence-key" role="group" aria-label="Confidence legend">
      <span class="mm-confidence__title">Confidence</span>
      <span class="mm-confidence__item">
        <i class="mm-line mm-line--verified" aria-hidden="true" /> Verified timetable
      </span>
      <span class="mm-confidence__item">
        <i class="mm-line mm-line--estimated" aria-hidden="true" /> Estimated air / frequency
      </span>
      <span class="mm-confidence__item">
        <i class="mm-line mm-line--scenario" aria-hidden="true" /> User scenario
      </span>
      <span class="mm-confidence__item">
        <i class="mm-line mm-line--assumption" aria-hidden="true" /> Assumption
      </span>
      <span
        class="mm-confidence__note"
        title="Verified means every transit leg is timetabled and no air leg is used."
      >
        Verified = timetabled, no air leg.
      </span>
    </div>
  </header>
</template>
