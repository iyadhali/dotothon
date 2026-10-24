import {
  applyScenario,
  computeAccessibility,
  createServiceFromPattern,
  planJourney,
  planJourneyWithStatus,
} from '../../shared/routing/router'
import { buildAccessReport } from '../../shared/routing/nearby'
import { setMultimodalEngine } from '../utils/engine'

/**
 * Registers the real timetable router with the UI's late-binding engine boundary.
 * Client-only: the page loads the network and computes journeys after mount.
 */
export default defineNuxtPlugin(() => {
  setMultimodalEngine({
    planJourney,
    planJourneyWithStatus,
    computeAccessibility,
    applyScenario,
    createServiceFromPattern,
    buildAccessReport,
  })
})
