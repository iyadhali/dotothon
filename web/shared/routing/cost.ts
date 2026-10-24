/**
 * Out-of-pocket fare estimate for a planned journey.
 *
 * Pure and browser-safe. Fares come from `/data/fares.json` (built by
 * `scripts/multimodal/build_fares.py`); every leg carries its basis and confidence, and a
 * leg with no fare data is reported as unknown rather than priced at zero. Walking is free.
 * Emergency transport approved by Aasandha is free to the patient, so this models a
 * non-emergency trip paid at the normal resident fare.
 */
import type { Journey, JourneyLeg, MultimodalNetwork } from './types'

export type FareConfidence = 'sourced' | 'estimated' | 'assumption'

/** Fare as `a + b × km`, or a flat amount when `b` is 0. */
export interface FareModel {
  aMvr: number
  bMvrPerKm: number
  basis: string
  confidence: FareConfidence
  source?: string
}

export interface AirRouteFare {
  /** Typical resident one-way fare in MVR. */
  mvr: number
  /** Lowest published (promotional) resident one-way fare, when known. */
  lowestMvr?: number
  basis: string
  confidence: FareConfidence
  source?: string
}

export interface FareTable {
  schemaVersion: 1
  currency: 'MVR'
  usdMvr: number
  generatedAt: string
  /** Keyed by sorted IATA pair, e.g. `DDD-MLE`. Fares are treated as symmetric. */
  airRoutes: Record<string, AirRouteFare>
  airModel?: FareModel
  /** RTL / public ferry: priced by straight-line distance between the stops × `seaDetour`. */
  ferry?: FareModel
  /** Flat fares for specific services, keyed by service id (e.g. the Malé–Vilimalé ferry). */
  serviceFares?: Record<string, FareModel>
  /** Scheduled speedboat (airport transfers). */
  speedboat?: FareModel
  /** Road links (taxi / ride-hailing). */
  road?: FareModel
  seaDetour: number
  notes: string[]
}

export interface LegCost {
  leg: JourneyLeg
  mvr: number | null
  basis: string
  confidence: FareConfidence | 'free' | 'unknown'
}

export interface JourneyCost {
  /** Sum of the priced legs, MVR. */
  knownMvr: number
  /** Legs that need a fare but have no data. */
  unknownLegs: number
  /** True when every leg is priced (free legs count as priced). */
  complete: boolean
  /** Weakest confidence among priced, non-free legs. */
  confidence: FareConfidence | 'free'
  legs: LegCost[]
}

const CONFIDENCE_RANK: Record<FareConfidence, number> = { sourced: 0, estimated: 1, assumption: 2 }

function haversineKm(aLat: number, aLon: number, bLat: number, bLon: number): number {
  const rad = Math.PI / 180
  const dLat = (bLat - aLat) * rad
  const dLon = (bLon - aLon) * rad
  const h = Math.sin(dLat / 2) ** 2 + Math.cos(aLat * rad) * Math.cos(bLat * rad) * Math.sin(dLon / 2) ** 2
  return 2 * 6371 * Math.asin(Math.sqrt(h))
}

function nodeCoordinates(network: MultimodalNetwork, node: string): [number, number] | null {
  const [prefix, id] = [node.slice(0, node.indexOf(':')), node.slice(node.indexOf(':') + 1)]
  if (prefix === 'stop') {
    const stop = network.stops.find((s) => s.id === id)
    return stop ? [stop.lat, stop.lon] : null
  }
  if (prefix === 'airport') {
    const airport = network.airports.find((a) => a.iata === id || a.id === id)
    return airport ? [airport.lat, airport.lon] : null
  }
  if (prefix === 'island') {
    const island = network.islands.find((i) => i.id === id)
    return island ? [island.lat, island.lon] : null
  }
  return null
}

function legKm(network: MultimodalNetwork, leg: JourneyLeg, detour: number): number | null {
  if (leg.distanceKm !== undefined && leg.distanceKm > 0) return leg.distanceKm
  const from = nodeCoordinates(network, leg.fromNode)
  const to = nodeCoordinates(network, leg.toNode)
  if (!from || !to) return null
  return haversineKm(from[0], from[1], to[0], to[1]) * detour
}

function priceByModel(model: FareModel | undefined, km: number | null, label: string): Omit<LegCost, 'leg'> {
  if (!model) return { mvr: null, basis: `No ${label} fare data`, confidence: 'unknown' }
  if (model.bMvrPerKm !== 0 && km === null) {
    return { mvr: null, basis: `${label} distance unknown`, confidence: 'unknown' }
  }
  const mvr = Math.round(model.aMvr + model.bMvrPerKm * (km ?? 0))
  const distance = model.bMvrPerKm !== 0 && km !== null ? ` (${km.toFixed(0)} km)` : ''
  return { mvr, basis: `${model.basis}${distance}`, confidence: model.confidence }
}

function airportCode(node: string): string | null {
  return node.startsWith('airport:') ? node.slice('airport:'.length) : null
}

function priceLeg(network: MultimodalNetwork, fares: FareTable, leg: JourneyLeg): Omit<LegCost, 'leg'> {
  if (leg.mode === 'walk' || leg.mode === 'ferry_transfer') {
    return { mvr: 0, basis: 'Walking', confidence: 'free' }
  }
  const fixed = leg.serviceId ? fares.serviceFares?.[leg.serviceId] : undefined
  if (fixed) return priceByModel(fixed, null, 'service')
  if (leg.kind === 'air' || leg.mode === 'air') {
    const from = airportCode(leg.fromNode)
    const to = airportCode(leg.toNode)
    if (from && to) {
      const route = fares.airRoutes[[from, to].sort().join('-')]
      if (route) {
        const range = route.lowestMvr !== undefined ? `; promo from MVR ${route.lowestMvr.toLocaleString('en-US')}` : ''
        return { mvr: route.mvr, basis: `${route.basis}${range}`, confidence: route.confidence }
      }
    }
    return priceByModel(fares.airModel, legKm(network, leg, 1), 'domestic air')
  }
  // The ferry tariff is set by great-circle distance between stops, so no detour factor.
  if (leg.kind === 'ferry') return priceByModel(fares.ferry, legKm(network, leg, 1), 'ferry')
  if (leg.kind === 'sea' || leg.mode === 'sea') {
    // Observed boat links have no tariff; price them like a public ferry of the same distance.
    const priced = priceByModel(fares.ferry, legKm(network, leg, 1), 'boat')
    if (priced.mvr === null) return priced
    return { ...priced, basis: `Boat (observed traffic), priced at the RTL tariff${priced.basis.match(/ \(\d+ km\)$/)?.[0] ?? ''}`, confidence: 'estimated' }
  }
  if (leg.mode === 'speedboat') return priceByModel(fares.speedboat, legKm(network, leg, fares.seaDetour), 'speedboat')
  if (leg.kind === 'road' || leg.mode === 'road') return priceByModel(fares.road, legKm(network, leg, 1), 'road')
  return { mvr: null, basis: `No fare rule for ${leg.mode}`, confidence: 'unknown' }
}

/** Price every leg of `journey`. A 0-minute (same island) journey costs nothing. */
export function estimateJourneyCost(network: MultimodalNetwork, fares: FareTable, journey: Journey): JourneyCost {
  const legs: LegCost[] = journey.legs.map((leg) => ({ leg, ...priceLeg(network, fares, leg) }))
  let knownMvr = 0
  let unknownLegs = 0
  let worst: FareConfidence | 'free' = 'free'
  for (const cost of legs) {
    if (cost.mvr === null) {
      unknownLegs += 1
      continue
    }
    knownMvr += cost.mvr
    if (cost.confidence === 'free' || cost.confidence === 'unknown') continue
    if (worst === 'free' || CONFIDENCE_RANK[cost.confidence] > CONFIDENCE_RANK[worst]) worst = cost.confidence
  }
  return { knownMvr, unknownLegs, complete: unknownLegs === 0, confidence: worst, legs }
}
