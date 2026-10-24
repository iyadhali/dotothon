<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { LngLatBounds, Map as MapboxMap, NavigationControl, Popup } from 'mapbox-gl'
import type { Feature, FeatureCollection } from 'geojson'
import type { Island } from '../../shared/routing/types'
import type { Destination, FacilityIsland, JourneyPath, RoutePath } from '../utils/routes'
import { formatPopulation } from '../utils/format'

const props = defineProps<{
  islands: Island[]
  routes: RoutePath[]
  facilities: FacilityIsland[]
  selectedIslandId: string | null
  journeys: JourneyPath[]
  destinations: Destination[]
  view: 'access' | 'underserved' | 'recommended'
  underserved: Record<string, string>
  sites: { rank: number; islandId: string; newlyCoveredIslandIds: string[] }[]
}>()

const emit = defineEmits<{ select: [islandId: string | null]; fallback: [reason: string] }>()

const runtime = useRuntimeConfig()
const container = ref<HTMLDivElement | null>(null)
let map: MapboxMap | null = null
let ready = false
const popup = new Popup({ closeButton: false, closeOnClick: false, offset: 10, className: 'am-popup' })

const COLORS = {
  island: '#cbd5e1',
  ferry: '#94a3b8',
  air: '#a5b4fc',
  health: '#e11d48',
  education: '#2563eb',
  both: '#7c3aed',
  journeyFerry: '#0284c7',
  journeyAir: '#7c3aed',
  journeyOther: '#475569',
  served: '#cbd5e1',
  over_threshold: '#f59e0b',
  no_trip: '#dc2626',
  no_data: '#ffffff',
  covered: '#16a34a',
}

const RADIUS = [
  'interpolate', ['linear'], ['zoom'],
  5, ['+', 2, ['*', 0.025, ['sqrt', ['get', 'population']]]],
  9, ['+', 4, ['*', 0.06, ['sqrt', ['get', 'population']]]],
] as unknown as number

const fc = (features: Feature[]): FeatureCollection => ({ type: 'FeatureCollection', features })

function islandFeatures(): FeatureCollection {
  const covered = new Set(props.sites.flatMap((site) => site.newlyCoveredIslandIds))
  return fc(
    props.islands
      .filter((island) => island.isOrigin)
      .map((island) => ({
        type: 'Feature',
        geometry: { type: 'Point', coordinates: [island.lon, island.lat] },
        properties: {
          islandId: island.id,
          name: island.name,
          atoll: island.atollName,
          population: island.population,
          cls:
            props.view === 'underserved'
              ? (props.underserved[island.id] ?? 'served')
              : props.view === 'recommended' && covered.has(island.id)
                ? 'covered'
                : 'island',
        },
      })),
  )
}

function routeFeatures(): FeatureCollection {
  return fc(
    props.routes.map((route) => ({
      type: 'Feature',
      geometry: { type: 'LineString', coordinates: route.points },
      properties: { mode: route.mode },
    })),
  )
}

function facilityFeatures(): FeatureCollection {
  return fc(
    props.facilities.map((facility) => ({
      type: 'Feature',
      geometry: { type: 'Point', coordinates: [facility.lon, facility.lat] },
      properties: { kind: facility.kind, count: facility.count },
    })),
  )
}

function journeyFeatures(): FeatureCollection {
  return fc(
    props.journeys.map((path) => ({
      type: 'Feature',
      geometry: { type: 'LineString', coordinates: path.points },
      properties: { mode: path.mode },
    })),
  )
}

function pointFeatures(points: { lon: number; lat: number; label?: string; rank?: number }[]): FeatureCollection {
  return fc(
    points.map((point) => ({
      type: 'Feature',
      geometry: { type: 'Point', coordinates: [point.lon, point.lat] },
      properties: { label: point.label ?? '', rank: point.rank !== undefined ? String(point.rank) : '' },
    })),
  )
}

function setData(id: string, data: FeatureCollection): void {
  const source = map?.getSource(id) as { setData?: (d: FeatureCollection) => void } | undefined
  source?.setData?.(data)
}

function refresh(): void {
  if (!map || !ready) return
  const selected = props.islands.find((island) => island.id === props.selectedIslandId) ?? null
  const byId = new Map(props.islands.map((island) => [island.id, island]))
  setData('am-islands', islandFeatures())
  setData('am-routes', routeFeatures())
  setData('am-facilities', facilityFeatures())
  setData('am-journey', journeyFeatures())
  setData('am-selected', pointFeatures(selected ? [selected] : []))
  setData('am-destinations', pointFeatures(props.destinations))
  setData(
    'am-sites',
    pointFeatures(
      props.view === 'recommended'
        ? props.sites.flatMap((site) => {
            const island = byId.get(site.islandId)
            return island ? [{ lon: island.lon, lat: island.lat, rank: site.rank }] : []
          })
        : [],
    ),
  )

  const access = props.view === 'access'
  const focused = access && selected !== null
  map.setPaintProperty('am-routes-ferry', 'line-opacity', focused ? 0.12 : access ? 0.55 : 0.15)
  map.setPaintProperty('am-routes-air', 'line-opacity', focused ? 0.1 : access ? 0.5 : 0.12)
  map.setLayoutProperty('am-facilities', 'visibility', access ? 'visible' : 'none')
  map.setPaintProperty('am-facilities', 'circle-opacity', focused ? 0.35 : 0.95)
}

function fitToSelection(): void {
  if (!map || !ready) return
  const selected = props.islands.find((island) => island.id === props.selectedIslandId)
  if (!selected) return
  const bounds = new LngLatBounds([selected.lon, selected.lat], [selected.lon, selected.lat])
  for (const destination of props.destinations) bounds.extend([destination.lon, destination.lat])
  for (const path of props.journeys) for (const point of path.points) bounds.extend(point as [number, number])
  map.fitBounds(bounds, { padding: { top: 80, bottom: 80, left: 80, right: 420 }, maxZoom: 10, duration: 700 })
}

function fitAll(): void {
  if (!map) return
  const bounds = new LngLatBounds()
  for (const island of props.islands) bounds.extend([island.lon, island.lat])
  if (!bounds.isEmpty()) map.fitBounds(bounds, { padding: 48, duration: 0, maxZoom: 9 })
}

function addLayers(): void {
  if (!map) return
  for (const id of ['am-islands', 'am-routes', 'am-facilities', 'am-journey', 'am-selected', 'am-destinations', 'am-sites']) {
    map.addSource(id, { type: 'geojson', data: fc([]) })
  }
  map.addLayer({
    id: 'am-routes-ferry',
    type: 'line',
    source: 'am-routes',
    filter: ['!=', ['get', 'mode'], 'air'],
    paint: { 'line-color': COLORS.ferry, 'line-width': 1.2, 'line-opacity': 0.55 },
  })
  map.addLayer({
    id: 'am-routes-air',
    type: 'line',
    source: 'am-routes',
    filter: ['==', ['get', 'mode'], 'air'],
    paint: { 'line-color': COLORS.air, 'line-width': 1, 'line-dasharray': [3, 2], 'line-opacity': 0.5 },
  })
  map.addLayer({
    id: 'am-islands',
    type: 'circle',
    source: 'am-islands',
    paint: {
      'circle-color': ['match', ['get', 'cls'], 'island', COLORS.island, 'served', COLORS.served,
        'over_threshold', COLORS.over_threshold, 'no_trip', COLORS.no_trip, 'no_data', COLORS.no_data,
        'covered', COLORS.covered, COLORS.island] as unknown as string,
      'circle-radius': RADIUS,
      'circle-stroke-color': ['match', ['get', 'cls'], 'no_data', '#64748b', '#ffffff'] as unknown as string,
      'circle-stroke-width': ['match', ['get', 'cls'], 'no_data', 1.4, 1] as unknown as number,
    },
  })
  map.addLayer({
    id: 'am-facilities',
    type: 'circle',
    source: 'am-facilities',
    paint: {
      'circle-color': ['match', ['get', 'kind'], 'health', COLORS.health, 'education', COLORS.education,
        COLORS.both] as unknown as string,
      'circle-radius': ['interpolate', ['linear'], ['zoom'], 5, 3, 9, 6] as unknown as number,
      'circle-stroke-color': '#ffffff',
      'circle-stroke-width': 1,
      'circle-opacity': 0.95,
    },
  })
  map.addLayer({
    id: 'am-journey',
    type: 'line',
    source: 'am-journey',
    filter: ['!=', ['get', 'mode'], 'air'],
    layout: { 'line-cap': 'round', 'line-join': 'round' },
    paint: {
      'line-color': ['match', ['get', 'mode'], 'ferry', COLORS.journeyFerry, 'sea', COLORS.journeyFerry,
        COLORS.journeyOther] as unknown as string,
      'line-width': 3,
    },
  })
  map.addLayer({
    id: 'am-journey-air',
    type: 'line',
    source: 'am-journey',
    filter: ['==', ['get', 'mode'], 'air'],
    paint: { 'line-color': COLORS.journeyAir, 'line-width': 3, 'line-dasharray': [2, 1.5] },
  })
  map.addLayer({
    id: 'am-selected',
    type: 'circle',
    source: 'am-selected',
    paint: { 'circle-color': '#0f172a', 'circle-radius': 7, 'circle-stroke-color': '#ffffff', 'circle-stroke-width': 2.5 },
  })
  map.addLayer({
    id: 'am-destinations',
    type: 'circle',
    source: 'am-destinations',
    paint: { 'circle-color': '#ffffff', 'circle-radius': 6, 'circle-stroke-color': '#0f172a', 'circle-stroke-width': 2.5 },
  })
  map.addLayer({
    id: 'am-destination-labels',
    type: 'symbol',
    source: 'am-destinations',
    layout: {
      'text-field': ['get', 'label'],
      'text-size': 12,
      'text-offset': [0, 1.2],
      'text-anchor': 'top',
      'text-max-width': 16,
    },
    paint: { 'text-color': '#0f172a', 'text-halo-color': '#ffffff', 'text-halo-width': 1.6 },
  })
  map.addLayer({
    id: 'am-sites',
    type: 'circle',
    source: 'am-sites',
    paint: { 'circle-color': '#0f172a', 'circle-radius': 11, 'circle-stroke-color': '#ffffff', 'circle-stroke-width': 2 },
  })
  map.addLayer({
    id: 'am-site-labels',
    type: 'symbol',
    source: 'am-sites',
    layout: { 'text-field': ['get', 'rank'], 'text-size': 12, 'text-allow-overlap': true },
    paint: { 'text-color': '#ffffff' },
  })
}

function islandAt(point: { x: number; y: number }) {
  if (!map) return null
  const features = map.queryRenderedFeatures(
    [
      [point.x - 6, point.y - 6],
      [point.x + 6, point.y + 6],
    ],
    { layers: ['am-islands'] },
  )
  return features[0] ?? null
}

onMounted(() => {
  const token = runtime.public.mapboxToken as string
  if (!container.value || !token) {
    emit('fallback', 'No Mapbox token configured.')
    return
  }
  map = new MapboxMap({
    accessToken: token,
    container: container.value,
    style: (runtime.public.mapboxStyle as string) || 'mapbox://styles/mapbox/light-v11',
    center: [73.4, 3.6],
    zoom: 5.6,
    attributionControl: true,
  })
  map.addControl(new NavigationControl({ showCompass: false }), 'bottom-right')
  map.on('load', () => {
    if (!map) return
    try {
      addLayers()
    } catch (error) {
      console.error('[atlas] map layers failed', error)
      emit('fallback', error instanceof Error ? error.message : 'Map layers failed to load.')
      return
    }
    ready = true
    fitAll()
    refresh()
    fitToSelection()
  })
  map.on('click', (event) => {
    const feature = islandAt(event.point)
    emit('select', (feature?.properties?.islandId as string | undefined) ?? null)
  })
  map.on('mousemove', (event) => {
    if (!map) return
    const feature = islandAt(event.point)
    map.getCanvas().style.cursor = feature ? 'pointer' : ''
    if (!feature) {
      popup.remove()
      return
    }
    const p = feature.properties ?? {}
    popup
      .setLngLat(event.lngLat)
      .setHTML(`<strong>${p.name}</strong><span>${p.atoll} · ${formatPopulation(Number(p.population))} residents</span>`)
      .addTo(map)
  })
  map.on('mouseout', () => popup.remove())
  map.on('error', (event: { error?: Error }) => {
    if (map && !map.isStyleLoaded()) emit('fallback', event?.error?.message ?? 'Mapbox failed to load.')
  })
})

watch(
  () => [props.islands, props.routes, props.facilities, props.journeys, props.destinations, props.view, props.underserved, props.sites],
  () => refresh(),
)
watch(
  () => [props.selectedIslandId, props.destinations],
  () => {
    refresh()
    if (props.selectedIslandId) fitToSelection()
  },
)

onBeforeUnmount(() => {
  popup.remove()
  map?.remove()
  map = null
})
</script>

<template>
  <div ref="container" class="am-map" />
</template>
