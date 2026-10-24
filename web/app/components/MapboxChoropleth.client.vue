<script setup lang="ts">
/**
 * Mapbox GL choropleth view (only instantiated when NUXT_PUBLIC_MAPBOX_TOKEN exists).
 *
 * Layer strategy: one GeoJSON source per travel-time band with a constant paint
 * colour. Constant colours avoid style-expression typing and make it impossible to
 * conflate bands. Any fatal style/token error emits `fallback`, and the parent
 * swaps in the token-free schematic map.
 */
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import {
  Map as MapboxMap,
  Marker as MapboxMarker,
  NavigationControl,
} from 'mapbox-gl'
import type { Feature, FeatureCollection, LineString, Point, Polygon } from 'geojson'
import type { Island } from '../../shared/routing/types'
import { BAND_BY_KEY, LEGEND_BANDS, type IslandBandInfo } from '../utils/bands'
import type { AirportPoint, FacilityPoint, MapHighlight, RoutePath } from '../utils/routes'
import { formatDuration, formatPopulation } from '../utils/format'
import { featureIslandId } from '../utils/geo'

const props = defineProps<{
  islands: Island[]
  bands: Record<string, IslandBandInfo>
  routes: RoutePath[]
  airports: AirportPoint[]
  facilities: FacilityPoint[]
  originIslandId: string
  categoryLabel: string
  /** Island polygons from islands.geojson; drawn as the actual choropleth. */
  geojson: FeatureCollection | null
  /** Nearest facility per service for the selected origin, drawn as lines + labels. */
  highlights?: MapHighlight[]
}>()


const emit = defineEmits<{
  'select-origin': [islandId: string]
  fallback: [reason: string]
}>()

const SOURCE_BAND_PREFIX = 'mm-band-'
const SOURCE_POLYGONS = 'mm-polygons'
const SOURCE_POLYGON_PREFIX = 'mm-poly-band-'
const SOURCE_CONTEXT = 'mm-context'
const SOURCE_ROUTES_VERIFIED = 'mm-routes-verified'
const SOURCE_ROUTES_ESTIMATED = 'mm-routes-estimated'
const SOURCE_ROUTES_AIR = 'mm-routes-air'
const SOURCE_FACILITIES = 'mm-facilities'
const SOURCE_ORIGIN = 'mm-origin'
const SOURCE_HIGHLIGHT_LINES = 'mm-highlight-lines'
const SOURCE_HIGHLIGHT_POINTS = 'mm-highlight-points'
const LAYER_HIGHLIGHT_LABELS = 'mm-highlight-labels'
/** Circle radius grows with the square root of population and with zoom. */
const POPULATION_RADIUS = [
  'interpolate',
  ['linear'],
  ['zoom'],
  5,
  ['+', 2.5, ['*', 0.03, ['sqrt', ['get', 'population']]]],
  9,
  ['+', 5, ['*', 0.07, ['sqrt', ['get', 'population']]]],
] as unknown as number

const container = ref<HTMLDivElement | null>(null)
const errorMessage = ref('')
const hovered = ref<{ name: string; atollName: string; population: number; description: string } | null>(null)

const runtimeConfig = useRuntimeConfig()
const accessToken = String(runtimeConfig.public.mapboxToken ?? '')
const styleUrl = String(runtimeConfig.public.mapboxStyle ?? 'mapbox://styles/mapbox/light-v11')

let map: MapboxMap | null = null
let mapReady = false
let airportMarkers: MapboxMarker[] = []
let originLayerIds: string[] = []
let disposed = false

function featureIsland(island: Island): Feature<Point> {
  const band = props.bands[island.id]
  return {
    type: 'Feature',
    geometry: { type: 'Point', coordinates: [island.lon, island.lat] },
    properties: {
      islandId: island.id,
      name: island.name,
      atollName: island.atollName,
      population: island.population,
      isOrigin: island.isOrigin,
      band: band?.band ?? 'not_computed',
      minutes: band?.minutes ?? null,
    },
  }
}

function routeFeature(route: RoutePath): Feature<LineString> {
  return {
    type: 'Feature',
    geometry: { type: 'LineString', coordinates: route.points },
    properties: { label: route.label, confidence: route.confidence, mode: route.mode },
  }
}

function collection(features: Feature[]): FeatureCollection {
  return { type: 'FeatureCollection', features }
}

function removeLayerAndSource(id: string): void {
  if (!map) return
  const layerId = `${id}-layer`
  if (map.getLayer(layerId)) map.removeLayer(layerId)
  if (map.getSource(id)) map.removeSource(id)
}

function clearRendered(): void {
  if (!map) return
  for (const band of LEGEND_BANDS) {
    removeLayerAndSource(`${SOURCE_BAND_PREFIX}${band.key}`)
    removeLayerAndSource(`${SOURCE_POLYGON_PREFIX}${band.key}`)
  }
  for (const id of [
    SOURCE_CONTEXT,
    SOURCE_POLYGONS,
    SOURCE_ROUTES_VERIFIED,
    SOURCE_ROUTES_ESTIMATED,
    SOURCE_ROUTES_AIR,
    SOURCE_FACILITIES,
    SOURCE_ORIGIN,
    SOURCE_HIGHLIGHT_LINES,
  ]) {
    removeLayerAndSource(id)
  }
  if (map.getLayer(LAYER_HIGHLIGHT_LABELS)) map.removeLayer(LAYER_HIGHLIGHT_LABELS)
  removeLayerAndSource(SOURCE_HIGHLIGHT_POINTS)
  for (const marker of airportMarkers) marker.remove()
  airportMarkers = []
  originLayerIds = []
}

function addRouteLayer(id: string, features: Feature<LineString>[], color: string, dash?: number[]): void {
  if (!map || features.length === 0) return
  map.addSource(id, { type: 'geojson', data: collection(features) })
  map.addLayer({
    id: `${id}-layer`,
    type: 'line',
    source: id,
    layout: { 'line-join': 'round', 'line-cap': 'round' },
    paint: {
      'line-color': color,
      'line-width': 2,
      'line-opacity': 0.68,
      ...(dash ? { 'line-dasharray': dash } : {}),
    },
  })
}

function polygonFeature(feature: Feature): Feature<Polygon> | null {
  if (!feature.geometry || feature.geometry.type !== 'Polygon') return null
  const islandId = featureIslandId(feature.properties)
  if (!islandId) return null
  const island = props.islands.find((entry) => entry.id === islandId)
  if (!island) return null
  const band = props.bands[island.id]
  return {
    type: 'Feature',
    geometry: feature.geometry,
    properties: {
      islandId: island.id,
      name: island.name,
      atollName: island.atollName,
      population: island.population,
      isOrigin: island.isOrigin,
      band: band?.band ?? 'not_computed',
      minutes: band?.minutes ?? null,
    },
  }
}

function render(): void {
  if (!map || !mapReady || disposed) return
  clearRendered()

  // Island polygons: the choropleth itself. One fill source per band, constant colour.
  if (props.geojson) {
    const polygons = props.geojson.features
      .map(polygonFeature)
      .filter((feature): feature is Feature<Polygon> => feature !== null)
    for (const band of LEGEND_BANDS) {
      const features = polygons.filter(
        (feature) => feature.properties?.isOrigin === true && feature.properties?.band === band.key,
      )
      if (features.length === 0) continue
      const id = `${SOURCE_POLYGON_PREFIX}${band.key}`
      map.addSource(id, { type: 'geojson', data: collection(features) })
      map.addLayer({
        id: `${id}-layer`,
        type: 'fill',
        source: id,
        paint: {
          'fill-color': band.color,
          'fill-opacity': 0.74,
          'fill-outline-color': band.ink,
        },
      })
      originLayerIds.push(`${id}-layer`)
    }
    const contextPolygons = polygons.filter((feature) => feature.properties?.isOrigin !== true)
    if (contextPolygons.length > 0) {
      map.addSource(SOURCE_POLYGONS, { type: 'geojson', data: collection(contextPolygons) })
      map.addLayer({
        id: `${SOURCE_POLYGONS}-layer`,
        type: 'fill',
        source: SOURCE_POLYGONS,
        paint: {
          'fill-color': '#e8e1d0',
          'fill-opacity': 0.6,
          'fill-outline-color': '#233d36',
        },
      })
    }
  }

  // Origin island points, split into one source/layer per band.
  for (const band of LEGEND_BANDS) {
    const features = props.islands
      .filter((island) => island.isOrigin && (props.bands[island.id]?.band ?? 'not_computed') === band.key)
      .map(featureIsland)
    if (features.length === 0) continue
    const id = `${SOURCE_BAND_PREFIX}${band.key}`
    map.addSource(id, { type: 'geojson', data: collection(features) })
    map.addLayer({
      id: `${id}-layer`,
      type: 'circle',
      source: id,
      paint: {
        'circle-color': band.color,
        'circle-radius': POPULATION_RADIUS,
        'circle-stroke-color': band.ink,
        'circle-stroke-width': 1,
        'circle-stroke-opacity': 0.7,
      },
    })
    originLayerIds.push(`${id}-layer`)
  }

  // Islands that are not origins stay visible for context only.
  const contextFeatures = props.islands.filter((island) => !island.isOrigin).map(featureIsland)
  if (contextFeatures.length > 0) {
    map.addSource(SOURCE_CONTEXT, { type: 'geojson', data: collection(contextFeatures) })
    map.addLayer({
      id: `${SOURCE_CONTEXT}-layer`,
      type: 'circle',
      source: SOURCE_CONTEXT,
      paint: {
        'circle-color': '#f3f0e7',
        'circle-radius': 3,
        'circle-stroke-color': '#233d36',
        'circle-stroke-width': 0.8,
        'circle-stroke-opacity': 0.4,
      },
    })
  }

  // Routes split by confidence/mode so the line style carries the evidence level.
  addRouteLayer(
    SOURCE_ROUTES_VERIFIED,
    props.routes.filter((route) => route.mode === 'ferry' && !route.dashed).map(routeFeature),
    '#233d36',
  )
  addRouteLayer(
    SOURCE_ROUTES_ESTIMATED,
    props.routes.filter((route) => route.mode === 'ferry' && route.dashed).map(routeFeature),
    '#287c6f',
    [6, 4],
  )
  addRouteLayer(
    SOURCE_ROUTES_AIR,
    props.routes.filter((route) => route.mode === 'air').map(routeFeature),
    '#b36c48',
    [3, 5],
  )

  // Facilities of the selected category, island-level precision.
  if (props.facilities.length > 0) {
    map.addSource(SOURCE_FACILITIES, {
      type: 'geojson',
      data: collection(
        props.facilities.map<Feature<Point>>((facility) => ({
          type: 'Feature',
          geometry: { type: 'Point', coordinates: [facility.lon, facility.lat] },
          properties: {
            islandId: facility.islandId,
            count: facility.count,
            names: facility.names.join(', '),
          },
        })),
      ),
    })
    map.addLayer({
      id: `${SOURCE_FACILITIES}-layer`,
      type: 'circle',
      source: SOURCE_FACILITIES,
      paint: {
        'circle-color': '#b36c48',
        'circle-radius': 4.5,
        'circle-stroke-color': '#faf9f5',
        'circle-stroke-width': 1.5,
      },
    })
  }

  // Airport markers with labels (HTML markers keep the text legible).
  for (const airport of props.airports) {
    if (!map) break
    const element = document.createElement('div')
    element.className = 'mm-mapbox-airport'
    element.textContent = airport.iata
    element.title = `${airport.iata} · ${airport.name} (${airport.islandName})`
    const marker = new MapboxMarker({ element, anchor: 'center' })
      .setLngLat([airport.lon, airport.lat])
      .addTo(map)
    airportMarkers.push(marker)
  }

  // Selected origin highlight ring.
  const origin = props.islands.find((island) => island.id === props.originIslandId)
  if (origin) {
    map.addSource(SOURCE_ORIGIN, {
      type: 'geojson',
      data: collection([
        {
          type: 'Feature',
          geometry: { type: 'Point', coordinates: [origin.lon, origin.lat] },
          properties: { islandId: origin.id },
        },
      ]),
    })
    map.addLayer({
      id: `${SOURCE_ORIGIN}-layer`,
      type: 'circle',
      source: SOURCE_ORIGIN,
      paint: {
        'circle-color': 'rgba(0, 0, 0, 0)',
        'circle-radius': 13,
        'circle-stroke-color': '#b36c48',
        'circle-stroke-width': 2.5,
      },
    })

    // Nearest facility per service: a line from the origin and a labelled destination.
    const highlights = (props.highlights ?? []).filter((item) => item.islandId !== origin.id)
    if (highlights.length > 0) {
      map.addSource(SOURCE_HIGHLIGHT_LINES, {
        type: 'geojson',
        data: collection(
          highlights.map((item) => ({
            type: 'Feature',
            geometry: { type: 'LineString', coordinates: [[origin.lon, origin.lat], [item.lon, item.lat]] },
            properties: {},
          })),
        ),
      })
      map.addLayer({
        id: `${SOURCE_HIGHLIGHT_LINES}-layer`,
        type: 'line',
        source: SOURCE_HIGHLIGHT_LINES,
        paint: { 'line-color': '#b36c48', 'line-width': 1.8, 'line-dasharray': [2, 1.5], 'line-opacity': 0.85 },
      })
      map.addSource(SOURCE_HIGHLIGHT_POINTS, {
        type: 'geojson',
        data: collection(
          highlights.map((item) => ({
            type: 'Feature',
            geometry: { type: 'Point', coordinates: [item.lon, item.lat] },
            properties: { label: item.label },
          })),
        ),
      })
      map.addLayer({
        id: `${SOURCE_HIGHLIGHT_POINTS}-layer`,
        type: 'circle',
        source: SOURCE_HIGHLIGHT_POINTS,
        paint: {
          'circle-color': '#fffdf8',
          'circle-radius': 6,
          'circle-stroke-color': '#b36c48',
          'circle-stroke-width': 2.5,
        },
      })
      map.addLayer({
        id: LAYER_HIGHLIGHT_LABELS,
        type: 'symbol',
        source: SOURCE_HIGHLIGHT_POINTS,
        layout: {
          'text-field': ['get', 'label'],
          'text-size': 12,
          'text-offset': [0, 1.3],
          'text-anchor': 'top',
          'text-allow-overlap': false,
          'text-max-width': 14,
        },
        paint: { 'text-color': '#233d36', 'text-halo-color': '#fffdf8', 'text-halo-width': 1.6 },
      })
    }
  }
}

function fitToIslands(): void {
  if (!map) return
  const points = props.islands.map((island) => [island.lon, island.lat] as [number, number])
  if (points.length < 2) return
  let minLon = Infinity
  let maxLon = -Infinity
  let minLat = Infinity
  let maxLat = -Infinity
  for (const [lon, lat] of points) {
    minLon = Math.min(minLon, lon)
    maxLon = Math.max(maxLon, lon)
    minLat = Math.min(minLat, lat)
    maxLat = Math.max(maxLat, lat)
  }
  map.fitBounds(
    [
      [minLon, minLat],
      [maxLon, maxLat],
    ],
    { padding: { top: 48, bottom: 48, left: 48, right: 48 }, duration: 0, maxZoom: 9 },
  )
}

function describeHover(feature: Feature | undefined): void {
  if (!feature) {
    hovered.value = null
    return
  }
  const properties = feature.properties ?? {}
  const islandId = String(properties.islandId ?? '')
  const island = props.islands.find((entry) => entry.id === islandId)
  if (!island) {
    hovered.value = null
    return
  }
  const band = props.bands[island.id]
  const bandLabel = band ? BAND_BY_KEY[band.band].label : 'Not computed'
  const minutes = band?.minutes
  hovered.value = {
    name: island.name,
    atollName: island.atollName,
    population: island.population,
    description:
      minutes != null
        ? `${bandLabel} · ${formatDuration(minutes)} to nearest ${props.categoryLabel}`
        : `${bandLabel} for ${props.categoryLabel}`,
  }
}

function onCanvasMove(event: { point: { x: number; y: number } }): void {
  if (!map) return
  const features = originLayerIds.length
    ? map.queryRenderedFeatures([event.point.x, event.point.y], { layers: originLayerIds })
    : []
  const canvas = map.getCanvas()
  if (features.length > 0) canvas.style.cursor = 'pointer'
  else canvas.style.cursor = ''
  describeHover(features[0])
}

function onCanvasClick(event: { point: { x: number; y: number } }): void {
  if (!map) return
  const features = originLayerIds.length
    ? map.queryRenderedFeatures([event.point.x, event.point.y], { layers: originLayerIds })
    : []
  const islandId = features[0]?.properties?.islandId
  if (typeof islandId === 'string' && islandId.length > 0) emit('select-origin', islandId)
}

onMounted(() => {
  if (!container.value) return
  if (!accessToken) {
    emit('fallback', 'No Mapbox token configured.')
    return
  }
  try {
    map = new MapboxMap({
      accessToken,
      container: container.value,
      style: styleUrl,
      center: [73.5, 3.2],
      zoom: 6,
      attributionControl: true,
    })
    map.addControl(new NavigationControl({ showCompass: false }), 'top-right')
    map.on('load', () => {
      if (disposed || !map) return
      mapReady = true
      fitToIslands()
      render()
    })
    map.on('click', onCanvasClick)
    map.on('mousemove', onCanvasMove)
    map.on('error', (event: { error?: Error }) => {
      const message = event?.error?.message ?? 'Mapbox failed to load.'
      errorMessage.value = message
      if (map && !map.isStyleLoaded()) emit('fallback', message)
    })
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Mapbox failed to initialise.'
    errorMessage.value = message
    emit('fallback', message)
  }
})

watch(
  () => [
    props.islands,
    props.bands,
    props.routes,
    props.airports,
    props.facilities,
    props.originIslandId,
    props.geojson,
    props.highlights,
  ],
  () => {
    if (mapReady) render()
  },
)

onBeforeUnmount(() => {
  disposed = true
  clearRendered()
  if (map) {
    map.off('click', onCanvasClick)
    map.off('mousemove', onCanvasMove)
    map.remove()
    map = null
  }
})
</script>

<template>
  <div class="mm-mapbox">
    <div ref="container" class="mm-mapbox__canvas" />

    <div v-if="hovered" class="mm-mapbox__hover" role="status">
      <strong>{{ hovered.name }} · {{ hovered.atollName }}</strong>
      <span>{{ formatPopulation(hovered.population) }} residents</span>
      <span>{{ hovered.description }}</span>
    </div>

    <p v-if="errorMessage" class="mm-mapbox__error" role="alert">
      Mapbox reported: {{ errorMessage }}. If the style cannot load, use the schematic view.
    </p>

    <p class="mm-mapbox__hint">
      Click an island to set the origin. Keyboard users can use the origin picker in the
      control rail; this canvas is not part of the tab order.
    </p>
  </div>
</template>
