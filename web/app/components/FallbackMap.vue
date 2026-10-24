<script setup lang="ts">
import { computed } from 'vue'
import type { Island } from '../../shared/routing/types'
import type { Destination, FacilityIsland, JourneyPath, RoutePath } from '../utils/routes'
import { ACCESS_CLASS_COLORS } from '../utils/classify'

/**
 * Token-free SVG version of the minimal map, used when Mapbox or WebGL is unavailable.
 * Same props and the same three stories; classes and colours come from utils/classify.
 */
const props = defineProps<{
  islands: Island[]
  routes: RoutePath[]
  landRoutes: { id: string; points: [number, number][] }[]
  facilities: FacilityIsland[]
  selectedIslandId: string | null
  journeys: JourneyPath[]
  destinations: Destination[]
  view: 'access' | 'underserved' | 'recommended'
  underserved: Record<string, string>
  sites: { rank: number; islandId: string; newlyCoveredIslandIds: string[] }[]
  siteRoutes: { rank: number; mode: string; points: [number, number][]; improves?: boolean }[]
  siteLabels: Destination[]
  focusSiteId: string | null
}>()

const emit = defineEmits<{ select: [islandId: string | null] }>()

const W = 1000
const H = 1000
const PAD = 40

const bounds = computed(() => {
  const lons = props.islands.map((island) => island.lon)
  const lats = props.islands.map((island) => island.lat)
  return {
    minLon: Math.min(...lons),
    maxLon: Math.max(...lons),
    minLat: Math.min(...lats),
    maxLat: Math.max(...lats),
  }
})

/** Equirectangular projection fitted to the islands, preserving aspect ratio. */
const scale = computed(() => {
  const b = bounds.value
  const sx = (W - 2 * PAD) / Math.max(b.maxLon - b.minLon, 0.01)
  const sy = (H - 2 * PAD) / Math.max(b.maxLat - b.minLat, 0.01)
  return Math.min(sx, sy)
})

function project(lon: number, lat: number): [number, number] {
  const b = bounds.value
  const s = scale.value
  const offsetX = (W - (b.maxLon - b.minLon) * s) / 2
  return [offsetX + (lon - b.minLon) * s, PAD + (b.maxLat - lat) * s]
}

const path = (points: [number, number][]) =>
  points.map(([lon, lat], i) => `${i ? 'L' : 'M'}${project(lon, lat).join(',')}`).join(' ')

const covered = computed(() => new Set(props.sites.flatMap((site) => site.newlyCoveredIslandIds)))

/** Zoom to the focused site's routes, or the selected island's journeys; otherwise the whole chain. */
const viewBox = computed(() => {
  const focusPoints: [number, number][] = []
  if (props.view === 'recommended' && props.focusSiteId) {
    const site = props.islands.find((island) => island.id === props.focusSiteId)
    if (site) focusPoints.push([site.lon, site.lat])
    for (const route of props.siteRoutes) focusPoints.push(...route.points)
  } else if (props.view === 'access' && props.selectedIslandId) {
    const origin = props.islands.find((island) => island.id === props.selectedIslandId)
    if (origin) focusPoints.push([origin.lon, origin.lat])
    for (const journey of props.journeys) focusPoints.push(...journey.points)
    for (const destination of props.destinations) focusPoints.push([destination.lon, destination.lat])
  }
  if (focusPoints.length < 2) return `0 0 ${W} ${H}`
  const projected = focusPoints.map(([lon, lat]) => project(lon, lat))
  const xs = projected.map(([x]) => x)
  const ys = projected.map(([, y]) => y)
  const size = Math.max(Math.max(...xs) - Math.min(...xs), Math.max(...ys) - Math.min(...ys), 60) * 1.6
  const cx = (Math.max(...xs) + Math.min(...xs)) / 2
  const cy = (Math.max(...ys) + Math.min(...ys)) / 2
  return `${cx - size / 2} ${cy - size / 2} ${size} ${size}`
})
const byId = computed(() => new Map(props.islands.map((island) => [island.id, island])))

function fill(island: Island): string {
  if (props.view === 'underserved') return ACCESS_CLASS_COLORS[props.underserved[island.id] as keyof typeof ACCESS_CLASS_COLORS] ?? '#cbd5e1'
  if (props.view === 'recommended' && covered.value.has(island.id)) return '#16a34a'
  return '#cbd5e1'
}

const radius = (island: Island) => 2.5 + Math.sqrt(island.population) * 0.035

const FACILITY_COLOR = { health: '#e11d48', education: '#2563eb', both: '#7c3aed' }
const JOURNEY_COLOR: Record<string, string> = { ferry: '#0284c7', sea: '#0284c7', air: '#7c3aed' }
const focused = computed(() => props.view === 'access' && props.selectedIslandId !== null)
</script>

<template>
  <svg class="am-fallback" :viewBox="viewBox" preserveAspectRatio="xMidYMid meet" role="img" aria-label="Maldives islands map" @click.self="emit('select', null)">
    <g :opacity="focused ? 0.15 : view === 'access' ? 0.6 : 0.2">
      <path
        v-for="route in routes"
        :key="route.serviceId"
        :d="path(route.points)"
        fill="none"
        :stroke="route.mode === 'air' ? '#a5b4fc' : '#94a3b8'"
        stroke-width="1"
        :stroke-dasharray="route.mode === 'air' ? '4 3' : undefined"
      />
    </g>
    <g :opacity="focused ? 0.3 : view === 'access' ? 0.9 : 0.25">
      <path v-for="road in landRoutes" :key="road.id" :d="path(road.points)" fill="none" stroke="#334155" stroke-width="2.5" stroke-linecap="round" />
    </g>
    <circle
      v-for="island in islands.filter((i) => i.isOrigin)"
      :key="island.id"
      :cx="project(island.lon, island.lat)[0]"
      :cy="project(island.lon, island.lat)[1]"
      :r="radius(island)"
      :fill="fill(island)"
      :stroke="view === 'underserved' && underserved[island.id] === 'no_data' ? '#64748b' : '#ffffff'"
      stroke-width="1"
      class="am-fallback__island"
      @click.stop="emit('select', island.id)"
    >
      <title>{{ island.name }}, {{ island.atollName }}</title>
    </circle>
    <template v-if="view === 'access'">
      <circle
        v-for="facility in facilities"
        :key="`f-${facility.islandId}`"
        :cx="project(facility.lon, facility.lat)[0]"
        :cy="project(facility.lon, facility.lat)[1]"
        :r="facility.major ? 5 : 3"
        :fill="FACILITY_COLOR[facility.kind]"
        :opacity="focused ? 0.35 : 0.95"
        stroke="#ffffff"
        stroke-width="0.8"
        pointer-events="none"
      />
      <path
        v-for="(journey, index) in journeys"
        :key="`j-${index}`"
        :d="path(journey.points)"
        fill="none"
        :stroke="JOURNEY_COLOR[journey.mode] ?? '#475569'"
        stroke-width="3"
        stroke-linecap="round"
        :stroke-dasharray="journey.mode === 'air' ? '6 4' : undefined"
      />
      <g v-for="destination in destinations" :key="`d-${destination.islandId}`">
        <circle :cx="project(destination.lon, destination.lat)[0]" :cy="project(destination.lon, destination.lat)[1]" r="6" fill="#ffffff" stroke="#0f172a" stroke-width="2.5" />
        <text :x="project(destination.lon, destination.lat)[0] + 10" :y="project(destination.lon, destination.lat)[1] + 4" class="am-fallback__label">
          {{ destination.label.replace('\n', ' · ') }}
        </text>
      </g>
      <circle
        v-if="selectedIslandId && byId.get(selectedIslandId)"
        :cx="project(byId.get(selectedIslandId)!.lon, byId.get(selectedIslandId)!.lat)[0]"
        :cy="project(byId.get(selectedIslandId)!.lon, byId.get(selectedIslandId)!.lat)[1]"
        r="7"
        fill="#0f172a"
        stroke="#ffffff"
        stroke-width="2.5"
      />
    </template>
    <template v-if="view === 'recommended'">
      <g :key="`routes-${focusSiteId ?? 'all'}-${siteRoutes.length}`">
        <path
          v-for="(route, index) in siteRoutes"
          :key="`sr-${index}`"
          :d="path(route.points)"
          pathLength="1"
          class="am-fallback__site-route"
          :class="{ 'is-same': !route.improves }"
          :style="{ animationDelay: `${(index % 12) * 60}ms` }"
        />
      </g>
      <g v-for="label in siteLabels" :key="`sl-${label.islandId}`">
        <text :x="project(label.lon, label.lat)[0] + 8" :y="project(label.lon, label.lat)[1] + 16" class="am-fallback__site-label">
          {{ label.label.replace('\n', ' · ') }}
        </text>
      </g>
      <g v-for="site in sites" :key="`s-${site.islandId}`">
        <template v-if="byId.get(site.islandId)">
          <circle :cx="project(byId.get(site.islandId)!.lon, byId.get(site.islandId)!.lat)[0]" :cy="project(byId.get(site.islandId)!.lon, byId.get(site.islandId)!.lat)[1]" r="11" fill="#0f172a" stroke="#ffffff" stroke-width="2" />
          <text :x="project(byId.get(site.islandId)!.lon, byId.get(site.islandId)!.lat)[0]" :y="project(byId.get(site.islandId)!.lon, byId.get(site.islandId)!.lat)[1] + 4" text-anchor="middle" class="am-fallback__rank">{{ site.rank }}</text>
        </template>
      </g>
    </template>
  </svg>
</template>

<style>
.am-fallback {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  background: #f8fafc;
}
.am-fallback__island {
  cursor: pointer;
}
.am-fallback__label {
  font: 600 13px Inter, ui-sans-serif, system-ui, sans-serif;
  fill: #0f172a;
  paint-order: stroke;
  stroke: #ffffff;
  stroke-width: 3px;
}
.am-fallback__site-route {
  fill: none;
  stroke: #16a34a;
  stroke-width: 3;
  stroke-linecap: round;
  stroke-dasharray: 1;
  stroke-dashoffset: 1;
  filter: drop-shadow(0 0 4px rgba(22, 163, 74, 0.55));
  animation: am-draw 1.4s cubic-bezier(0.22, 1, 0.36, 1) forwards;
}
.am-fallback__site-route.is-same {
  stroke: #86efac;
  stroke-width: 1.6;
  filter: none;
}
@keyframes am-draw {
  to {
    stroke-dashoffset: 0;
  }
}
.am-fallback__site-label {
  font: 600 12px Inter, ui-sans-serif, system-ui, sans-serif;
  fill: #14532d;
  paint-order: stroke;
  stroke: #ffffff;
  stroke-width: 3px;
}
.am-fallback__rank {
  font: 600 12px Inter, ui-sans-serif, system-ui, sans-serif;
  fill: #ffffff;
  pointer-events: none;
}
</style>
