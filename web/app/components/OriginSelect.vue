<script setup lang="ts">
/**
 * Searchable single-select for the 191 origin islands, grouped by atoll with
 * population shown. Implements the ARIA combobox/listbox keyboard interaction
 * because a native <select> cannot be filtered by typing.
 */
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import type { Island } from '../../shared/routing/types'
import { formatPopulation } from '../utils/format'

const props = defineProps<{
  modelValue: string
  origins: Island[]
  disabled?: boolean
}>()

const emit = defineEmits<{ 'update:modelValue': [value: string] }>()

const root = ref<HTMLElement | null>(null)
const input = ref<HTMLInputElement | null>(null)
const query = ref('')
const open = ref(false)
const activeIndex = ref(0)

const selectedIsland = computed(
  () => props.origins.find((island) => island.id === props.modelValue) ?? null,
)

const filtered = computed(() => {
  const q = query.value.trim().toLowerCase()
  if (!q) return props.origins
  return props.origins.filter(
    (island) =>
      island.name.toLowerCase().includes(q) ||
      island.atollName.toLowerCase().includes(q) ||
      island.atoll.toLowerCase().includes(q),
  )
})

const selectedLabel = computed(() =>
  open.value ? `Search ${props.origins.length} islands` : 'Search island or atoll',
)

watch(filtered, () => {
  activeIndex.value = 0
})

watch(activeIndex, async (index) => {
  await nextTick()
  const island = filtered.value[index]
  if (!island) return
  document.getElementById(optionId(island.id))?.scrollIntoView({ block: 'nearest' })
})

function optionId(islandId: string): string {
  return `mm-origin-option-${islandId}`
}

function choose(island: Island): void {
  emit('update:modelValue', island.id)
  open.value = false
  query.value = ''
}

function onInput(event: Event): void {
  if (!(event.target instanceof HTMLInputElement)) return
  query.value = event.target.value
  open.value = true
  activeIndex.value = 0
}

function onFocus(): void {
  if (props.disabled) return
  open.value = true
}

function onKeydown(event: KeyboardEvent): void {
  if (props.disabled) return
  if (!open.value && (event.key === 'ArrowDown' || event.key === 'ArrowUp')) {
    event.preventDefault()
    open.value = true
    return
  }
  switch (event.key) {
    case 'ArrowDown':
      event.preventDefault()
      activeIndex.value = Math.min(activeIndex.value + 1, filtered.value.length - 1)
      break
    case 'ArrowUp':
      event.preventDefault()
      activeIndex.value = Math.max(activeIndex.value - 1, 0)
      break
    case 'Home':
      event.preventDefault()
      activeIndex.value = 0
      break
    case 'End':
      event.preventDefault()
      activeIndex.value = Math.max(filtered.value.length - 1, 0)
      break
    case 'Enter': {
      if (!open.value) break
      event.preventDefault()
      const island = filtered.value[activeIndex.value]
      if (island) choose(island)
      break
    }
    case 'Escape':
      open.value = false
      break
    default:
      break
  }
}

function onDocumentPointer(event: PointerEvent): void {
  if (!root.value) return
  if (event.target instanceof Node && root.value.contains(event.target)) return
  open.value = false
}

onMounted(() => {
  document.addEventListener('pointerdown', onDocumentPointer)
})
onBeforeUnmount(() => {
  document.removeEventListener('pointerdown', onDocumentPointer)
})
</script>

<template>
  <div ref="root" class="mm-origin">
    <label for="mm-origin-input" class="mm-label">Origin island</label>

    <div class="mm-origin__selection" aria-live="polite">
      <strong>{{ selectedIsland?.name ?? 'No origin selected' }}</strong>
      <span v-if="selectedIsland">
        {{ selectedIsland.atollName }} · {{ formatPopulation(selectedIsland.population) }} residents
      </span>
    </div>

    <div class="mm-origin__field">
      <input
        id="mm-origin-input"
        ref="input"
        class="mm-input"
        type="text"
        role="combobox"
        :aria-expanded="open"
        aria-controls="mm-origin-list"
        :aria-activedescendant="open ? optionId(filtered[activeIndex]?.id ?? '') : undefined"
        aria-autocomplete="list"
        :value="query"
        :placeholder="selectedLabel"
        :disabled="disabled"
        autocomplete="off"
        spellcheck="false"
        @input="onInput"
        @focus="onFocus"
        @keydown="onKeydown"
      />
      <span class="mm-origin__count" aria-hidden="true">{{ filtered.length }}</span>
    </div>

    <ul v-if="open" id="mm-origin-list" class="mm-origin__list" role="listbox" aria-label="Matching origin islands">
      <template v-for="(island, index) in filtered" :key="island.id">
        <li
          v-if="index === 0 || filtered[index - 1]?.atollName !== island.atollName"
          role="presentation"
          class="mm-origin__group"
        >
          {{ island.atollName }}
        </li>
        <li
          :id="optionId(island.id)"
          role="option"
          :aria-selected="island.id === modelValue"
          :class="[
            'mm-origin__option',
            { 'is-active': index === activeIndex, 'is-selected': island.id === modelValue },
          ]"
          @pointerdown.prevent="choose(island)"
          @pointerenter="activeIndex = index"
        >
          <span class="mm-origin__name">{{ island.name }}</span>
          <span class="mm-origin__meta">{{ formatPopulation(island.population) }} residents</span>
        </li>
      </template>
      <li v-if="filtered.length === 0" role="presentation" class="mm-origin__empty">
        No island or atoll matches “{{ query }}”.
      </li>
    </ul>

    <p class="mm-hint">
      Search by island or atoll. {{ origins.length }} inhabited origin islands are modelled.
    </p>
  </div>
</template>
