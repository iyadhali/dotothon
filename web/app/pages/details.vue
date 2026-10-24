<script setup lang="ts">
import { computed } from 'vue'
import { useMultimodal } from '../composables/useMultimodal'
import { formatDuration } from '../utils/format'
import type { MapHighlight } from '../utils/routes'

const store = useMultimodal()

const {
  dataStatus,
  dataSource,
  loadNote,
  fatalError,
  network,
  meta,
  islandsGeojson,
  geojsonLoaded,
  engineReady,
  originIslandId,
  departureMinute,
  threshold,
  selectedOrigin,
  selectedCategory,
  journey,
  journeyStatus,
  nextDayJourney,
  journeyLoading,
  journeyError,
  metricsLoading,
  metricsError,
  baselineSummary,
  scenarioSummary,
  unfilteredSummary,
  scenarioActive,
  scenarioDescription,
  comparison,
  islandBands,
  routePaths,
  airportPoints,
  facilityPoints,
  selectedOriginAccess,
  selectedOriginFilteredOut,
  filterActive,
  selectOrigin,
  regionSplit,
  accessReport,
  mapView,
  siting,
  underservedClasses,
} = store

const SHORT_LABELS: Record<string, string> = {
  health_hospital: 'Hospital',
  health_regional_tertiary: 'Regional hospital',
  education_grade_11_12: 'Grade 11–12',
  education_higher_ed: 'Higher education',
}

/** Nearest destination per service for the selected island, merged by island for the map. */
const mapHighlights = computed<MapHighlight[]>(() => {
  const net = network.value
  if (!net) return []
  const byIsland = new Map<string, { labels: string[]; minutes: number }>()
  for (const row of accessReport.value) {
    const first = row.destinations[0]
    if (!first || first.journey.elapsedMinutes === 0) continue
    const label = SHORT_LABELS[row.category] ?? net.categories.find((c) => c.id === row.category)?.label ?? row.category
    const entry = byIsland.get(first.journey.destinationIslandId) ?? { labels: [], minutes: first.journey.elapsedMinutes }
    entry.labels.push(label)
    byIsland.set(first.journey.destinationIslandId, entry)
  }
  const islandsById = new Map(net.islands.map((island) => [island.id, island]))
  return [...byIsland.entries()].flatMap(([islandId, entry]) => {
    const island = islandsById.get(islandId)
    if (!island) return []
    return [{ islandId, lon: island.lon, lat: island.lat, label: `${island.name}
${entry.labels.join(', ')} · ${formatDuration(entry.minutes)}` }]
  })
})

const runtimeConfig = useRuntimeConfig()

const hasMapboxToken = computed(() => Boolean(runtimeConfig.public.mapboxToken))

const islands = computed(() => network.value?.islands ?? [])

const referenceDay = computed(() => meta.value?.referenceDay ?? '')

const generatedAt = computed(() => meta.value?.generatedAt ?? null)

const categoryLabel = computed(() => selectedCategory.value?.label ?? 'selected category')

const originName = computed(() => selectedOrigin.value?.name ?? '')

const maxJourneyMinutes = computed(
  () => meta.value?.routingDefaults.maxJourneyMinutes ?? 1440,
)

const displaySummary = computed(() =>
  scenarioActive.value ? (scenarioSummary.value ?? baselineSummary.value) : baselineSummary.value,
)
</script>

<template>
  <div class="mm-page">
    <MultimodalHeader
      :data-source="dataSource"
      :data-status="dataStatus"
      :reference-day="referenceDay"
      :generated-at="generatedAt"
    />

    <div v-if="dataStatus === 'loading'" class="mm-page-loading" role="status" aria-live="polite">
      <span class="mm-spinner" aria-hidden="true" />
      <strong>Loading the prepared network…</strong>
    </div>

    <div v-else-if="dataStatus === 'error'" class="mm-page-error" role="alert">
      <h2>No network loaded</h2>
      <p>{{ fatalError ?? 'Unknown data error.' }}</p>
      <p>Reload to retry, or check that the prepared data was published.</p>
    </div>

    <div v-else class="mm-shell">
      <aside class="mm-rail-column" aria-label="Model controls">
        <ControlRail :store="store" />
      </aside>

      <main class="mm-main">
        <div v-if="dataSource === 'fixture'" class="mm-banner mm-banner--fixture" role="status">
          <strong>Fixture data — test values.</strong>
          <span>Bundled sample network; no national claims.</span>
          <details v-if="loadNote">
            <summary>Why</summary>
            <code>{{ loadNote }}</code>
          </details>
        </div>

        <div v-else-if="dataSource === 'static'" class="mm-banner mm-banner--fixture" role="status">
          <strong>Static fallback.</strong>
          <span>Same prepared network, served as JSON; results are unchanged.</span>
          <details v-if="loadNote">
            <summary>Why</summary>
            <code>{{ loadNote }}</code>
          </details>
        </div>

        <div v-if="!engineReady" class="mm-banner mm-banner--engine" role="status">
          <strong>Routing engine not wired.</strong>
          <span>Map states render; journeys and metrics need the router.</span>
        </div>

        <div v-if="filterActive" class="mm-banner mm-banner--filter" role="status">
          <strong>Network filter active.</strong>
          <span>Not selected ≠ no infrastructure.</span>
          <details>
            <summary>What this means</summary>
            <p>
              Islands removed by your Land/Sea/Air or route selection are labelled “Not selected by
              network filter”. Headline figures include only the selected network.
            </p>
          </details>
        </div>

        <KpiStrip
          :summary="displaySummary"
          :threshold="threshold"
          :loading="metricsLoading"
          :error="metricsError"
          :scenario-active="scenarioActive"
          :filter-active="filterActive"
        />

        <InsightStrip
          :summary="displaySummary"
          :unfiltered-summary="unfilteredSummary"
          :comparison="comparison"
          :threshold="threshold"
          :filter-active="filterActive"
          :scenario-active="scenarioActive"
          :loading="metricsLoading"
        />

        <div class="mm-hero">
          <MapPanel
            :islands="islands"
            :bands="islandBands"
            :routes="routePaths"
            :airports="airportPoints"
            :facilities="facilityPoints"
            :origin-island-id="originIslandId"
            :origin-name="originName"
            :category-label="categoryLabel"
            :departure-minute="departureMinute"
            :geojson="islandsGeojson"
            :metrics-loading="metricsLoading"
            :has-mapbox-token="hasMapboxToken"
            :filter-active="filterActive"
            :highlights="mapHighlights"
            :map-view="mapView"
            :underserved="underservedClasses"
            :siting="siting"
            :threshold-minutes="threshold"
            @select-origin="selectOrigin"
            @set-view="(next) => (mapView = next)"
          />

          <IslandAccessPanel class="mm-hero__panel" :store="store" />
        </div>

        <div class="mm-grid">
          <JourneyCard
            :origin="selectedOrigin"
            :access="selectedOriginAccess"
            :category="selectedCategory"
            :journey="journey"
            :status="journeyStatus"
            :next-day-journey="nextDayJourney"
            :loading="journeyLoading"
            :error="journeyError"
            :scenario-description="scenarioDescription"
            :scenario-active="scenarioActive"
            :reference-day="referenceDay"
            :max-journey-minutes="maxJourneyMinutes"
            :filtered-out="selectedOriginFilteredOut"
          />

          <NationalMetrics
            :summary="displaySummary"
            :split="regionSplit"
            :loading="metricsLoading"
            :error="metricsError"
            :threshold="threshold"
            :category-label="categoryLabel"
            :departure-minute="departureMinute"
            :scenario-active="scenarioActive"
            :filter-active="filterActive"
          />

          <ScenarioComparison
            :scenario-active="scenarioActive"
            :scenario-description="scenarioDescription"
            :comparison="comparison"
            :threshold="threshold"
            :loading="metricsLoading"
          />

          <InterventionPanel class="mm-grid__wide" :store="store" />

          <CoveragePanel
            class="mm-grid__wide"
            :meta="meta"
            :data-source="dataSource ?? 'api'"
            :geojson-loaded="geojsonLoaded"
            :load-note="loadNote ?? ''"
          />

          <HdxPanel
            class="mm-grid__wide"
            :summary="displaySummary"
            :threshold="threshold"
          />
        </div>

        <footer class="mm-footer">
          <p class="mm-footer__line">
            <strong>Prototype.</strong> Modelled physical access on one reference day — not
            confirmed services, demand or a verified calendar.
          </p>
          <details class="mm-footer__more">
            <summary>Caveats, sources & publishing</summary>
            <p>
              MTCC passenger counts are synthetic, not observed demand. Missing coverage is not
              evidence that an island has no transport. Fares are full resident fares from published tariffs (estimated where labelled); fuel and charter costs are out of scope. Island
              names follow source records; times are integer minutes after midnight, Maldives time
              (UTC+5).
            </p>
            <p>
              QGIS-ready layers are exported to <a href="/data/qgis/">/data/qgis/</a> when the
              pipeline publishes them; a missing link means the export is not published. To publish
              in Mapbox, upload the exported GeoJSON as a tileset in Mapbox Studio and point a style
              at it. QGIS and Mapbox Studio are authoring tools only — this app reads
              <code>/data/multimodal.json</code> and <code>/data/islands.geojson</code> at runtime.
            </p>
          </details>
        </footer>
      </main>
    </div>
  </div>
</template>
