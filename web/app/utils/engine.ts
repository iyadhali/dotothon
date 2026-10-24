/**
 * Late-binding boundary for the routing engine.
 *
 * The UI is built independently of `web/shared/routing/router.ts` so that the page
 * stays typecheckable and usable against the sample network while the router is in
 * progress. At integration time `web/app/plugins/routing-engine.client.ts` imports
 * the real router functions and registers them here — the composable never imports
 * the router directly, so absent router code cannot break the UI build.
 */
import type {
  AccessibilityRequest,
  AccessibilityResult,
  Journey,
  JourneyPlan,
  JourneyRequest,
  MultimodalNetwork,
  Scenario,
  TimetabledService,
} from '../../shared/routing/types'

export interface MultimodalEngine {
  planJourney: (network: MultimodalNetwork, request: JourneyRequest) => Journey | null
  /**
   * Optional additive helper from the real router. When present the UI can explain
   * `no_origin_access` / `no_destination` / `not_reachable` instead of guessing from a
   * null journey.
   */
  planJourneyWithStatus?: (
    network: MultimodalNetwork,
    request: JourneyRequest,
  ) => JourneyPlan
  computeAccessibility: (
    network: MultimodalNetwork,
    request: AccessibilityRequest,
  ) => AccessibilityResult
  applyScenario: (network: MultimodalNetwork, scenario: Scenario) => MultimodalNetwork
  createServiceFromPattern: (
    network: MultimodalNetwork,
    routeId: string,
    newFirstDepartureMinute: number,
    id?: string,
  ) => TimetabledService
}

let engine: MultimodalEngine | null = null

export function setMultimodalEngine(next: MultimodalEngine): void {
  engine = next
}

/** Null until the real router plugin has registered; the UI renders a clear notice. */
export function getMultimodalEngine(): MultimodalEngine | null {
  return engine
}
