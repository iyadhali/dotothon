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
      <div>
        <strong>Loading the prepared network…</strong>
        <p>
          Looking for <code>/data/multimodal.json</code> and
          <code>/data/islands.geojson</code>. If they are not published yet, the bundled
          fixture network is used instead.
        </p>
      </div>
    </div>

    <div v-else-if="dataStatus === 'error'" class="mm-page-error" role="alert">
      <h2>The prototype could not load any network</h2>
      <p>{{ fatalError ?? 'Unknown data error.' }}</p>
      <p>Reload the page to retry, or check that the prepared data was published.</p>
    </div>

    <div v-else class="mm-shell">
      <aside class="mm-rail-column" aria-label="Model controls">
        <ControlRail :store="store" />
      </aside>

      <main class="mm-main">
        <div v-if="dataSource === 'fixture'" class="mm-banner mm-banner--fixture" role="status">
          <strong>Fixture data — no real-world claims.</strong>
          <span>
            The prepared network at <code>/data/multimodal.json</code> is not available, so the
            page is using the bundled sample network. Population, coverage and journey numbers
            here are test values, not national figures.
          </span>
          <details v-if="loadNote">
            <summary>Why the fallback happened</summary>
            <code>{{ loadNote }}</code>
          </details>
        </div>

        <div v-if="!engineReady" class="mm-banner mm-banner--engine" role="status">
          <strong>Routing engine not wired yet.</strong>
          <span>
            The network loaded, but journey planning and accessibility calculations are not
            registered in this build. The map shows coverage states and the controls are
            browsable; colours and metrics appear once the router is integrated.
          </span>
        </div>

        <div v-if="filterActive" class="mm-banner mm-banner--filter" role="status">
          <strong>Network filter active.</strong>
          <span>
            Islands removed by your Land/Sea/Air or route selection are labelled
            <em>Not selected by network filter</em>, separately from coverage gaps. The
            headline population figures include only the selected network.
          </span>
        </div>

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
            :data-source="dataSource === 'fixture' ? 'fixture' : 'live'"
            :geojson-loaded="geojsonLoaded"
            :load-note="loadNote ?? ''"
          />

          <HdxPanel class="mm-grid__wide" />
        </div>

        <footer class="mm-footer">
          <p>
            <strong>What this is.</strong> A working prototype of reference-day multimodal
            access to health and education facilities. It reports modelled physical access,
            not confirmed service availability, observed demand or a verified calendar.
          </p>
          <p>
            <strong>What it is not.</strong> MTCC passenger counts in the source data are
            synthetic; they are not observed demand. Missing coverage is not evidence that an
            island has no transport. Fares and fuel costs are out of scope.
          </p>
          <p>
            <strong>Publish and inspect.</strong> The pipeline exports QGIS-ready layers
            (islands, facilities, ferry and air routes, access edges, style) under
            <a href="/data/qgis/index.html">/data/qgis/</a>; if the link is missing, the export has
            not been published yet. To publish the same layers
            in Mapbox, upload the exported GeoJSON as a tileset in Mapbox Studio and point a
            Mapbox style at it. QGIS and Mapbox Studio are authoring tools only: this app reads
            <code>/data/multimodal.json</code> and <code>/data/islands.geojson</code> and does
            not require either tool at runtime.
          </p>
          <p class="mm-footer__meta">
            Island names are preserved from source records where possible. Times are integer
            minutes after midnight, Maldives time (UTC+5).
          </p>
        </footer>
      </main>
    </div>
  </div>
</template>
