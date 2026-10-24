<script setup lang="ts">
import { computed } from 'vue'
import { useMultimodal } from '../composables/useMultimodal'

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
} = store

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

        <div class="mm-grid">
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
            @select-origin="selectOrigin"
          />

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
              evidence that an island has no transport. Fares and fuel are out of scope. Island
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
