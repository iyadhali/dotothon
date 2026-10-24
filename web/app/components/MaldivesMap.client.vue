<script setup lang="ts">
import type { FeatureCollection } from 'geojson'
import type { GeoJSONSource, Map as MapboxMap } from 'mapbox-gl'

// Pass prepared GeoJSON here when adding facilities/routes. No raw datasets are bundled.
const props = withDefaults(defineProps<{ data?: FeatureCollection }>(), {
  data: () => ({ type: 'FeatureCollection', features: [] }),
})
const config = useRuntimeConfig()
const container = ref<HTMLElement>()
const error = ref('')
const ready = ref(false)
let map: MapboxMap | undefined
let disposed = false

watch(() => props.data, (data) => {
  if (!map?.isStyleLoaded()) return
  const source = map.getSource('application-data') as GeoJSONSource | undefined
  source?.setData(data)
})

onMounted(async () => {
  if (!config.public.mapboxToken || !container.value) return
  try {
    const { default: mapboxgl } = await import('mapbox-gl')
    if (disposed || !container.value) return
    map = new mapboxgl.Map({
      container: container.value,
      accessToken: config.public.mapboxToken,
      style: config.public.mapboxStyle,
      bounds: [[72.45, -0.85], [74.0, 7.3]],
      fitBoundsOptions: { padding: 32 },
    })
    map.addControl(new mapboxgl.NavigationControl(), 'top-right')
    map.on('error', () => { error.value = 'Mapbox could not load. Check your token, allowed URLs and network connection.' })
    map.on('load', () => {
      if (!map) return
      map.addSource('application-data', { type: 'geojson', data: props.data })
      map.addLayer({ id: 'areas', source: 'application-data', type: 'fill', filter: ['==', ['geometry-type'], 'Polygon'], paint: { 'fill-color': '#287c6f', 'fill-opacity': 0.25 } })
      map.addLayer({ id: 'routes', source: 'application-data', type: 'line', filter: ['==', ['geometry-type'], 'LineString'], paint: { 'line-color': '#287c6f', 'line-width': 2 } })
      map.addLayer({ id: 'facilities', source: 'application-data', type: 'circle', filter: ['==', ['geometry-type'], 'Point'], paint: { 'circle-color': '#b36c48', 'circle-radius': 5, 'circle-stroke-color': '#fffdf8', 'circle-stroke-width': 1.5 } })
      ready.value = true
      error.value = ''
    })
  } catch {
    error.value = 'The map could not initialize. Check your browser supports WebGL and reload.'
  }
})

onBeforeUnmount(() => {
  disposed = true
  map?.remove()
  map = undefined
})
</script>

<template>
  <section class="map-shell" aria-label="Maldives map">
    <div ref="container" class="map-container" />
    <div v-if="!config.public.mapboxToken" class="map-placeholder">
      <UIcon name="i-lucide-map" class="map-placeholder-icon" />
      <h2>Your map starts here.</h2>
      <p>Add your public Mapbox token to connect the basemap.</p>
      <code>NUXT_PUBLIC_MAPBOX_TOKEN</code>
      <span>Configure it in web/.env, then restart the dev server.</span>
    </div>
    <p v-else-if="error" class="map-message" role="alert">{{ error }}</p>
    <p v-else-if="!ready" class="map-message" role="status">Loading the Maldives map…</p>
  </section>
</template>
