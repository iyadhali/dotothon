/**
 * Where should the next facility go? Greedy maximal-coverage siting on the multimodal
 * network: pick the inhabited island that brings the most residents within the travel-time
 * threshold, add it, and repeat. Pure and browser-safe.
 *
 * The travel-time matrix (one same-day search per origin island) is computed once; every
 * candidate is then scored by lookup, so ranking all islands is instant.
 */
import { travelTimesFrom } from './router.ts'
import type { MultimodalNetwork, NetworkSelection } from './types'

/** origin island id → (island id → same-day travel minutes). */
export type TravelMatrix = Map<string, Map<string, number>>

export interface RecommendedSite {
  rank: number
  islandId: string
  name: string
  atollName: string
  /** Residents newly within the threshold if this island gets the facility. */
  gainPopulation: number
  /** Origin islands that newly come within the threshold. */
  newlyCoveredIslandIds: string[]
  /** Residents within the threshold after this and all earlier picks. */
  coveredAfter: number
}

export interface SitingResult {
  category: string
  thresholdMinutes: number
  populationTotal: number
  coveredBefore: number
  sites: RecommendedSite[]
}

export function buildTravelMatrix(
  network: MultimodalNetwork,
  options: NetworkSelection & {
    departureMinute: number
    /** Search horizon; only times up to the largest threshold you will rank with matter. */
    maxJourneyMinutes: number
  },
): TravelMatrix {
  const matrix: TravelMatrix = new Map()
  for (const island of network.islands) {
    if (!island.isOrigin) continue
    matrix.set(
      island.id,
      travelTimesFrom(network, {
        originIslandId: island.id,
        departureMinute: options.departureMinute,
        maxJourneyMinutes: options.maxJourneyMinutes,
        allowedModes: options.allowedModes,
        disabledRouteIds: options.disabledRouteIds,
        disabledServiceIds: options.disabledServiceIds,
        dayOfWeek: options.dayOfWeek,
      }),
    )
  }
  return matrix
}

export function recommendSites(
  network: MultimodalNetwork,
  matrix: TravelMatrix,
  options: { category: string; thresholdMinutes: number; picks?: number },
): SitingResult {
  const origins = network.islands.filter((island) => island.isOrigin)
  const facilityIslands = new Set(
    network.facilities.filter((f) => f.categories.includes(options.category)).map((f) => f.islandId),
  )
  const within = (originId: string, siteId: string): boolean =>
    (matrix.get(originId)?.get(siteId) ?? Infinity) <= options.thresholdMinutes

  const covered = new Set<string>()
  for (const origin of origins) {
    for (const site of facilityIslands) {
      if (within(origin.id, site)) {
        covered.add(origin.id)
        break
      }
    }
  }
  const populationOf = new Map(origins.map((o) => [o.id, o.population]))
  const sumPopulation = (ids: Iterable<string>) => [...ids].reduce((sum, id) => sum + (populationOf.get(id) ?? 0), 0)
  const coveredBefore = sumPopulation(covered)

  const candidates = origins.filter((o) => !facilityIslands.has(o.id))
  const sites: RecommendedSite[] = []
  for (let rank = 1; rank <= (options.picks ?? 5); rank += 1) {
    let best: { island: (typeof origins)[number]; gain: number; ids: string[] } | null = null
    for (const candidate of candidates) {
      if (sites.some((site) => site.islandId === candidate.id)) continue
      const ids = origins.filter((o) => !covered.has(o.id) && within(o.id, candidate.id)).map((o) => o.id)
      const gain = sumPopulation(ids)
      if (gain > 0 && (!best || gain > best.gain)) best = { island: candidate, gain, ids }
    }
    if (!best) break
    for (const id of best.ids) covered.add(id)
    sites.push({
      rank,
      islandId: best.island.id,
      name: best.island.name,
      atollName: best.island.atollName,
      gainPopulation: best.gain,
      newlyCoveredIslandIds: best.ids,
      coveredAfter: sumPopulation(covered),
    })
  }
  return {
    category: options.category,
    thresholdMinutes: options.thresholdMinutes,
    populationTotal: sumPopulation(origins.map((o) => o.id)),
    coveredBefore,
    sites,
  }
}
