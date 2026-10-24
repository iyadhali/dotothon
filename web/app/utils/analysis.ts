/**
 * Scenario comparison derived from two accessibility results.
 *
 * This is deliberately honest about what a user scenario means: added trips and
 * cancelled services are hypothetical inputs, not observed operations. Only
 * differences are reported; unchanged origins are not re-listed.
 */
import type {
  AccessibilityResult,
  Island,
  OriginAccess,
  OriginAccessStatus,
} from '../../shared/routing/types'
import { bandForStatus, bandOrderIndex, type TravelBandKey } from './bands'

export type ThresholdMinutes = 60 | 120 | 240

export type ChangeDirection = 'improved' | 'worsened'

export interface OriginBandChange {
  islandId: string
  name: string
  atollName: string
  population: number
  beforeStatus: OriginAccessStatus | null
  afterStatus: OriginAccessStatus | null
  beforeBand: TravelBandKey
  afterBand: TravelBandKey
  beforeMinutes: number | null
  afterMinutes: number | null
  direction: ChangeDirection
}

export interface NewlyCoveredOrigin {
  islandId: string
  name: string
  atollName: string
  population: number
  minutes: number | null
}

export interface ScenarioComparison {
  threshold: ThresholdMinutes
  /** Origin population that had no itinerary before and has one after. */
  newlyReachablePopulation: number
  /** Origins that gained their first same-day itinerary under the scenario. */
  newlyCovered: NewlyCoveredOrigin[]
  /** Net change in reachable population (can be negative). */
  reachableDelta: number
  withinDeltas: Record<ThresholdMinutes, number>
  /** Origins whose status or travel-time band actually changed. */
  originsChanged: number
  /** Origins that stayed in the same band but whose travel time changed. */
  originsRetimed: number
  changes: OriginBandChange[]
}

function bandOf(access: OriginAccess | undefined): {
  band: TravelBandKey
  minutes: number | null
  status: OriginAccessStatus | null
} {
  if (!access) return { band: 'not_computed', minutes: null, status: null }
  const minutes = access.status === 'reachable' ? (access.journey?.elapsedMinutes ?? null) : null
  return {
    band: bandForStatus(access.status, minutes),
    minutes,
    status: access.status,
  }
}

/** Compare a scenario accessibility result against the baseline for the same inputs. */
export function compareAccessibility(
  baseline: AccessibilityResult,
  scenario: AccessibilityResult,
  islands: readonly Island[],
  threshold: ThresholdMinutes,
): ScenarioComparison {
  const changes: OriginBandChange[] = []
  const newlyCovered: NewlyCoveredOrigin[] = []
  let newlyReachablePopulation = 0
  let originsRetimed = 0

  for (const island of islands) {
    if (!island.isOrigin) continue
    const before: OriginAccess | undefined = baseline.perOrigin[island.id]
    const after: OriginAccess | undefined = scenario.perOrigin[island.id]
    if (!before || !after) continue

    if (before.status !== 'reachable' && after.status === 'reachable') {
      newlyReachablePopulation += island.population
      newlyCovered.push({
        islandId: island.id,
        name: island.name,
        atollName: island.atollName,
        population: island.population,
        minutes: after.journey?.elapsedMinutes ?? null,
      })
    }

    const beforeBandInfo = bandOf(before)
    const afterBandInfo = bandOf(after)

    if (beforeBandInfo.band === afterBandInfo.band) {
      if (
        before.status === 'reachable' &&
        after.status === 'reachable' &&
        beforeBandInfo.minutes !== null &&
        afterBandInfo.minutes !== null &&
        beforeBandInfo.minutes !== afterBandInfo.minutes
      ) {
        originsRetimed += 1
      }
      continue
    }

    const direction: ChangeDirection =
      bandOrderIndex(afterBandInfo.band) < bandOrderIndex(beforeBandInfo.band)
        ? 'improved'
        : 'worsened'

    changes.push({
      islandId: island.id,
      name: island.name,
      atollName: island.atollName,
      population: island.population,
      beforeStatus: beforeBandInfo.status,
      afterStatus: afterBandInfo.status,
      beforeBand: beforeBandInfo.band,
      afterBand: afterBandInfo.band,
      beforeMinutes: beforeBandInfo.minutes,
      afterMinutes: afterBandInfo.minutes,
      direction,
    })
  }

  changes.sort((a, b) => {
    if (a.direction !== b.direction) return a.direction === 'improved' ? -1 : 1
    return b.population - a.population || a.name.localeCompare(b.name)
  })
  newlyCovered.sort((a, b) => b.population - a.population || a.name.localeCompare(b.name))

  return {
    threshold,
    newlyReachablePopulation,
    newlyCovered,
    reachableDelta: scenario.summary.populationReachable - baseline.summary.populationReachable,
    withinDeltas: {
      60: scenario.summary.within60 - baseline.summary.within60,
      120: scenario.summary.within120 - baseline.summary.within120,
      240: scenario.summary.within240 - baseline.summary.within240,
    },
    originsChanged: changes.length,
    originsRetimed,
    changes,
  }
}

/** Greater Malé origin islands (census city/ward rows). */
export const GREATER_MALE_NAMES = new Set(['Maale', 'Hulhumaale', 'Hulhule', "Vilin'gili"])

export interface RegionAccess {
  population: number
  /** Facility on the home island: no travel needed. */
  onIsland: number
  /** Reached by travelling on the network the same day. */
  byTransport: number
  /** Has transport data but no same-day connection. */
  unreachable: number
  /** No transport data for the island (coverage gap). */
  noData: number
}

export interface RegionSplit {
  greaterMale: RegionAccess
  atolls: RegionAccess
}

/**
 * Split an accessibility result into Greater Malé and the atolls. Greater Malé holds about
 * 47% of residents and has every service, so the national figure hides the atoll picture.
 */
export function splitByRegion(result: AccessibilityResult | null, islands: Island[]): RegionSplit | null {
  if (!result) return null
  const empty = (): RegionAccess => ({ population: 0, onIsland: 0, byTransport: 0, unreachable: 0, noData: 0 })
  const split: RegionSplit = { greaterMale: empty(), atolls: empty() }
  for (const island of islands) {
    if (!island.isOrigin) continue
    const access = result.perOrigin[island.id]
    if (!access) continue
    const bucket = GREATER_MALE_NAMES.has(island.name) ? split.greaterMale : split.atolls
    bucket.population += island.population
    if (access.status === 'reachable') {
      if (access.journey && access.journey.elapsedMinutes > 0) bucket.byTransport += island.population
      else bucket.onIsland += island.population
    } else if (access.status === 'no_origin_access') {
      bucket.noData += island.population
    } else {
      bucket.unreachable += island.population
    }
  }
  return split
}
