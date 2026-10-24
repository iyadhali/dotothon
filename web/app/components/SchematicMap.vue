<script setup lang="ts">
/**
 * Token-free schematic map.
 *
 * Islands are drawn as projected centroids sized by population, with optional
 * coastline-ish polygons from `islands.geojson` underneath for context. This is a
 * diagram, not a geographic basemap: it does not imply physical island area,
 * building locations or service catchments. Keyboard and pointer selection both work.
 */
import { computed, ref } from 'vue'
import type { FeatureCollection } from 'geojson'
import type { Island } from '../../shared/routing/types'
import {
  BAND_BY_KEY,
  type IslandBandInfo,
  type TravelBandKey,
} from '../utils/bands'
import type { AirportPoint, FacilityPoint, RoutePath } from '../utils/routes'
import {
  collectGeoCoordinates,
  createProjector,
  featureIslandId,
  geometryToPath,
  type LonLat,
} from '../utils/geo'
import { formatDuration, formatPopulation } from '../utils/format'

const props = defineProps<{
  islands: Island[]
  bands: Record<string, IslandBandInfo>
  routes: RoutePath[]
  airports: AirportPoint[]
  facilities: FacilityPoint[]
  originIslandId: string
  geojson: FeatureCollection | null
  categoryLabel: string
}>()

const emit = defineEmits<{ 'select-origin': [islandId: string] }>()

const WIDTH = 1000
const HEIGHT = 1320
const PADDING = 74

interface PlottedIsland {
  island: Island
  x: number
  y: number
  radius: number
  band: IslandBandInfo
  tooltip: string
  ariaLabel: string
}

const hovered = ref<PlottedIsland | null>(null)
const view = ref<'all' | 'focus'>('all')

const coordinates = computed<LonLat[]>(() => {
  const points: LonLat[] = props.islands.map((island) => [island.lon, island.lat])
  for (const point of collectGeoCoordinates(props.geojson)) points.push(point)
  return points
})

const projector = computed(() => createProjector(coordinates.value, WIDTH, HEIGHT, PADDING))

function describeBand(island: Island, band: IslandBandInfo): string {
  if (!island.isOrigin) return 'Included for context; not an origin island'
  switch (band.status) {
    case 'reachable':
      return band.minutes == null
        ? `Reachable, travel time not recorded for ${props.categoryLabel}`
        : `${formatDuration(band.minutes)} to the nearest ${props.categoryLabel} facility`
    case 'not_reachable':
      return `No itinerary to a ${props.categoryLabel} facility under the reference-day assumption`
    case 'no_origin_access':
      return 'No physical access edge from this island in the prepared network; a coverage gap'
    case 'no_destination':
      return `No ${props.categoryLabel} facility in the prepared data`
    default:
      return 'Accessibility not computed yet'
  }
}

const plotted = computed<PlottedIsland[]>(() => {
  const result: PlottedIsland[] = []
  for (const island of props.islands) {
    const [x, y] = projector.value.project(island.lon, island.lat)
    if (!Number.isFinite(x) || !Number.isFinite(y)) continue
    if (x < -40 || x > WIDTH + 40 || y < -40 || y > HEIGHT + 40) continue
    const band = props.bands[island.id] ?? {
      islandId: island.id,
      band: 'not_computed' as TravelBandKey,
      minutes: null,
      status: null,
      population: island.population,
    }
    const radius = island.isOrigin
      ? Math.max(4.5, Math.min(14, 3 + Math.sqrt(Math.max(island.population, 1)) / 18))
      : 3
    const description = describeBand(island, band)
    result.push({
      island,
      x,
      y,
      radius,
      band,
      tooltip: description,
      ariaLabel: `${island.name}, ${island.atollName}. Population ${formatPopulation(island.population)}. ${description}.${island.isOrigin ? ' Press Enter to use as origin.' : ''}`,
    })
  }
  return result.sort((a, b) => a.island.population - b.island.population)
})

const focusOrigin = computed(
  () => plotted.value.find((entry) => entry.island.id === props.originIslandId) ?? null,
)

const viewBox = computed(() => {
  if (view.value === 'all' || !focusOrigin.value) return `0 0 ${WIDTH} ${HEIGHT}`
  const width = 560
  const height = 740
  const x = Math.min(Math.max(focusOrigin.value.x - width / 2, 0), WIDTH - width)
  const y = Math.min(Math.max(focusOrigin.value.y - height / 2, 0), HEIGHT - height)
  return `${x} ${y} ${width} ${height}`
})

const polygons = computed(() => {
  const geo = props.geojson
  if (!geo) return []
  return geo.features
    .map((feature, index) => ({
      key: `${featureIslandId(feature.properties) ?? 'feature'}-${index}`,
      islandId: featureIslandId(feature.properties),
      path: geometryToPath(feature.geometry, projector.value.project),
    }))
    .filter((polygon) => polygon.path.length > 0)
})

function linePath(points: LonLat[]): string {
  const project = projector.value.project
  return points
    .map(([lon, lat], index) => {
      const [x, y] = project(lon, lat)
      return `${index === 0 ? 'M' : 'L'}${x.toFixed(1)},${y.toFixed(1)}`
    })
    .join(' ')
}

const routeLines = computed(() =>
  props.routes
    .map((route) => ({
      route,
      d: linePath(route.points),
    }))
    .filter((entry) => entry.d.length > 0),
)

const facilityMarkers = computed(() =>
  props.facilities.map((facility) => {
    const [x, y] = projector.value.project(facility.lon, facility.lat)
    return { facility, x, y, radius: 3.2 + Math.min(facility.count, 4) }
  }),
)

const airportMarkers = computed(() =>
  props.airports.map((airport) => {
    const [x, y] = projector.value.project(airport.lon, airport.lat)
    return { airport, x, y }
  }),
)

interface AtollLabel {
  name: string
  y: number
}

const atollLabels = computed<AtollLabel[]>(() => {
  const groups = new Map<string, number[]>()
  for (const entry of plotted.value) {
    const name = entry.island.atollName
    if (!name) continue
    const values = groups.get(name)
    if (values) values.push(entry.y)
    else groups.set(name, [entry.y])
  }
  const labels: AtollLabel[] = [...groups.entries()].map(([name, ys]) => ({
    name,
    y: ys.reduce((sum, value) => sum + value, 0) / ys.length,
  }))
  labels.sort((a, b) => a.y - b.y)
  let previous = -Infinity
  for (const label of labels) {
    label.y = Math.max(label.y, previous + 26)
    previous = label.y
  }
  return labels
})

function patternFor(band: TravelBandKey): string | null {
  switch (band) {
    case 'not_reachable':
      return 'url(#mm-pat-not-reachable)'
    case 'no_origin_access':
      return 'url(#mm-pat-no-origin-access)'
    case 'no_destination':
      return 'url(#mm-pat-no-destination)'
    case 'not_selected':
      return 'url(#mm-pat-not-selected)'
    default:
      return null
  }
}

function select(island: Island): void {
  if (!island.isOrigin) return
  emit('select-origin', island.id)
}

function bandColor(entry: PlottedIsland): string {
  return BAND_BY_KEY[entry.band.band].color
}

function bandInk(entry: PlottedIsland): string {
  return BAND_BY_KEY[entry.band.band].ink
}

const readout = computed(() => {
  const entry = hovered.value
  if (!entry) {
    return {
      title: 'Hover or focus an island for details',
      lines: ['Select any origin island to make it the journey origin.'],
    }
  }
  const band = BAND_BY_KEY[entry.band.band]
  return {
    title: `${entry.island.name} · ${entry.island.atollName}`,
    lines: [
      `${band.label}${entry.band.minutes != null ? ` · ${formatDuration(entry.band.minutes)}` : ''}`,
      `${formatPopulation(entry.island.population)} residents`,
      entry.tooltip,
    ],
  }
})
</script>

<template>
  <div class="mm-schematic">
    <div v-if="plotted.length === 0" class="mm-map-empty" role="status">
      No island coordinates are available in the prepared network, so the schematic
      cannot be drawn.
    </div>

    <template v-else>
      <div class="mm-mapviews" role="group" aria-label="Schematic view">
        <button
          type="button"
          class="mm-mapviews__btn"
          :class="{ 'is-active': view === 'all' }"
          :aria-pressed="view === 'all'"
          @click="view = 'all'"
        >
          All islands
        </button>
        <button
          type="button"
          class="mm-mapviews__btn"
          :class="{ 'is-active': view === 'focus' }"
          :aria-pressed="view === 'focus'"
          :disabled="!focusOrigin"
          @click="view = 'focus'"
        >
          Focus origin
        </button>
      </div>

      <svg
        class="mm-schematic__svg"
        :viewBox="viewBox"
        role="group"
        aria-label="Schematic map of Maldives islands coloured by travel time"
        preserveAspectRatio="xMidYMid meet"
      >
        <defs>
          <linearGradient id="mm-ocean" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stop-color="#f3f0e5" />
            <stop offset="100%" stop-color="#eae6d8" />
          </linearGradient>
          <pattern id="mm-pat-not-reachable" width="8" height="8" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
            <rect width="8" height="8" fill="#b9bcb4" />
            <line x1="0" y1="0" x2="0" y2="8" stroke="#233d36" stroke-opacity="0.4" stroke-width="1.3" />
          </pattern>
          <pattern id="mm-pat-no-origin-access" width="7" height="7" patternUnits="userSpaceOnUse">
            <rect width="7" height="7" fill="#efe9dd" />
            <circle cx="1.8" cy="1.8" r="0.9" fill="#233d36" fill-opacity="0.45" />
            <circle cx="5.2" cy="5.2" r="0.9" fill="#233d36" fill-opacity="0.45" />
          </pattern>
          <pattern id="mm-pat-not-selected" width="9" height="9" patternUnits="userSpaceOnUse">
            <rect width="9" height="9" fill="#dfe8ec" />
            <path d="M0 9L9 0" stroke="#2d3f47" stroke-width="1" stroke-opacity="0.28" />
            <path d="M0 0L9 9" stroke="#2d3f47" stroke-width="1" stroke-opacity="0.28" />
          </pattern>
          <pattern id="mm-pat-no-destination" width="8" height="8" patternUnits="userSpaceOnUse">
            <rect width="8" height="8" fill="#e4deea" />
            <path d="M0,0 L8,8 M8,0 L0,8" stroke="#4b3f5a" stroke-opacity="0.35" stroke-width="1" />
          </pattern>
        </defs>

        <rect :width="WIDTH" :height="HEIGHT" fill="url(#mm-ocean)" rx="18" />

        <g class="mm-schematic__polygons" aria-hidden="true">
          <path
            v-for="polygon in polygons"
            :key="polygon.key"
            :d="polygon.path"
            fill="#e6e0cf"
            stroke="#233d36"
            stroke-opacity="0.16"
            stroke-width="1"
          />
        </g>

        <g class="mm-schematic__routes" aria-hidden="true">
          <path
            v-for="entry in routeLines"
            :key="entry.route.serviceId"
            :d="entry.d"
            fill="none"
            :stroke="entry.route.mode === 'air' ? '#b36c48' : '#233d36'"
            :stroke-width="entry.route.dashed ? 1.7 : 2.1"
            :stroke-dasharray="entry.route.mode === 'air' ? '3 5' : entry.route.dashed ? '7 5' : undefined"
            stroke-opacity="0.62"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
            <title>{{ entry.route.label }} ({{ entry.route.confidence }})</title>
          </path>
        </g>

        <g class="mm-schematic__atolls" aria-hidden="true">
          <text
            v-for="label in atollLabels"
            :key="label.name"
            :x="WIDTH - 18"
            :y="label.y"
            text-anchor="end"
            font-size="12.5"
            fill="#5b685e"
            stroke="#f4f1e7"
            stroke-width="4"
            paint-order="stroke"
          >
            {{ label.name }}
          </text>
        </g>

        <g class="mm-schematic__facilities">
          <circle
            v-for="marker in facilityMarkers"
            :key="`facility-${marker.facility.islandId}`"
            :cx="marker.x"
            :cy="marker.y"
            :r="marker.radius"
            fill="#b36c48"
            stroke="#faf9f5"
            stroke-width="1.6"
          >
            <title>
              {{ marker.facility.count }}
              {{ categoryLabel }} facilit{{ marker.facility.count === 1 ? 'y' : 'ies' }} on
              {{ marker.facility.islandName }}: {{ marker.facility.names.join(', ') }}
            </title>
          </circle>
        </g>

        <g class="mm-schematic__airports">
          <g v-for="marker in airportMarkers" :key="`airport-${marker.airport.iata}`">
            <rect
              :x="marker.x - 4.5"
              :y="marker.y - 4.5"
              width="9"
              height="9"
              transform-origin="center"
              :transform="`rotate(45 ${marker.x} ${marker.y})`"
              fill="#233d36"
              stroke="#faf9f5"
              stroke-width="1.4"
            >
              <title>{{ marker.airport.iata }} · {{ marker.airport.name }} ({{ marker.airport.islandName }})</title>
            </rect>
            <text
              :x="marker.x + 9"
              :y="marker.y + 4"
              font-size="10"
              fill="#233d36"
              stroke="#f4f1e7"
              stroke-width="3"
              paint-order="stroke"
            >
              {{ marker.airport.iata }}
            </text>
          </g>
        </g>

        <g class="mm-schematic__islands">
          <g
            v-for="entry in plotted"
            :key="entry.island.id"
            class="mm-svg-island"
            :class="{
              'is-selected': entry.island.id === originIslandId,
              'is-context': !entry.island.isOrigin,
            }"
            :tabindex="entry.island.isOrigin ? 0 : undefined"
            :role="entry.island.isOrigin ? 'button' : undefined"
            :aria-label="entry.ariaLabel"
            :aria-pressed="entry.island.isOrigin ? entry.island.id === originIslandId : undefined"
            @click="select(entry.island)"
            @keydown.enter.prevent="select(entry.island)"
            @keydown.space.prevent="select(entry.island)"
            @pointerenter="hovered = entry"
            @pointerleave="hovered = null"
            @focus="hovered = entry"
            @blur="hovered = null"
          >
            <title>{{ entry.island.name }} — {{ entry.tooltip }}</title>
            <circle
              v-if="entry.island.id === originIslandId"
              :cx="entry.x"
              :cy="entry.y"
              :r="entry.radius + 7"
              fill="none"
              stroke="#faf9f5"
              stroke-width="5"
              aria-hidden="true"
            />
            <circle
              v-if="entry.island.id === originIslandId"
              :cx="entry.x"
              :cy="entry.y"
              :r="entry.radius + 7"
              fill="none"
              stroke="#b36c48"
              stroke-width="2.6"
              stroke-dasharray="2 4"
              aria-hidden="true"
            />
            <circle
              :cx="entry.x"
              :cy="entry.y"
              :r="entry.radius"
              :fill="patternFor(entry.band.band) ?? bandColor(entry)"
              :stroke="bandInk(entry)"
              :stroke-width="entry.island.isOrigin ? 1.1 : 0.8"
              :stroke-opacity="entry.island.isOrigin ? 0.75 : 0.4"
              vector-effect="non-scaling-stroke"
            />
          </g>
        </g>
      </svg>

      <div class="mm-schematic__readout" role="status" aria-live="polite">
        <strong>{{ readout.title }}</strong>
        <span v-for="line in readout.lines" :key="line">{{ line }}</span>
      </div>

      <p class="mm-schematic__caption">
        Schematic Mercator projection. Markers are projected island centroids sized by
        population, not physical island area; facility dots sit on the island centroid at
        island-level precision.
      </p>
    </template>
  </div>
</template>
