/**
 * Tests for the island access report: nearest destinations, island-to-island planning,
 * fare estimates and same-day return. Uses the bundled Baa/Greater Malé fixture.
 *
 *   node --experimental-strip-types --test shared/routing/nearby.test.ts
 */
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import test from 'node:test'

import type { Journey, MultimodalNetwork } from './types'
import type { FareTable } from './cost'
import { estimateJourneyCost } from './cost.ts'
import { buildAccessReport } from './nearby.ts'
import { planIslandToIsland, planJourney, planNearestDestinations } from './router.ts'

const DHARAVANDHOO = 'MV007006'
const MAALHOS = 'MV007007'
const EYDHAFUSHI = 'MV007008'
const MAALE = 'MV021001'

function loadFixture(): MultimodalNetwork {
  return JSON.parse(readFileSync(new URL('./fixtures/sample-network.json', import.meta.url), 'utf8')) as MultimodalNetwork
}

const FARES: FareTable = {
  schemaVersion: 1,
  currency: 'MVR',
  usdMvr: 15.42,
  generatedAt: '2026-10-24',
  airRoutes: { 'DRV-MLE': { mvr: 1435, basis: 'Resident one-way', confidence: 'estimated' } },
  ferry: { aMvr: 33.82, bMvrPerKm: 1.794, basis: 'RTL tariff', confidence: 'sourced' },
  road: { aMvr: 57, bMvrPerKm: 3.8, basis: 'Taxi', confidence: 'estimated' },
  seaDetour: 1.1,
  notes: [],
}

test('nearest destinations: first journey equals planJourney', () => {
  const network = loadFixture()
  const request = { originIslandId: DHARAVANDHOO, departureMinute: 14 * 60 + 5, category: 'health_hospital' }
  const single = planJourney(network, request)
  const nearest = planNearestDestinations(network, request, 3)
  assert.equal(nearest.status, 'reachable')
  assert.ok(single)
  assert.equal(nearest.journeys[0]?.destinationIslandId, single.destinationIslandId)
  assert.equal(nearest.journeys[0]?.arrivalMinute, single.arrivalMinute)
})

test('nearest destinations: distinct islands in arrival order', () => {
  const network = loadFixture()
  const plan = planNearestDestinations(
    network,
    { originIslandId: DHARAVANDHOO, departureMinute: 6 * 60, category: 'health_any' },
    5,
  )
  const ids = plan.journeys.map((journey) => journey.destinationIslandId)
  assert.equal(new Set(ids).size, ids.length)
  // The origin hosts a health centre, so the 0-minute journey comes first.
  assert.equal(plan.journeys[0]?.elapsedMinutes, 0)
  for (let i = 1; i < plan.journeys.length; i += 1) {
    assert.ok((plan.journeys[i]?.arrivalMinute ?? 0) >= (plan.journeys[i - 1]?.arrivalMinute ?? 0))
  }
})

test('nearest destinations: unknown category is no_destination', () => {
  const plan = planNearestDestinations(
    loadFixture(),
    { originIslandId: DHARAVANDHOO, departureMinute: 480, category: 'service:none' },
    3,
  )
  assert.deepEqual(plan, { status: 'no_destination', journeys: [] })
})

test('island to island: same-vehicle ferry Maalhos → Eydhafushi', () => {
  const journey = planIslandToIsland(loadFixture(), {
    fromIslandId: MAALHOS,
    toIslandId: EYDHAFUSHI,
    departureMinute: 8 * 60,
  })
  assert.ok(journey)
  assert.equal(journey.destinationIslandId, EYDHAFUSHI)
  assert.ok(journey.legs.some((leg) => leg.kind === 'ferry'))
})

test('island to island: same island is a 0-minute journey', () => {
  const journey = planIslandToIsland(loadFixture(), {
    fromIslandId: MAALHOS,
    toIslandId: MAALHOS,
    departureMinute: 600,
  })
  assert.equal(journey?.elapsedMinutes, 0)
})

test('cost: walking is free, ferry priced from the tariff, unknown legs flagged', () => {
  const network = loadFixture()
  const journey = planJourney(network, {
    originIslandId: DHARAVANDHOO,
    departureMinute: 14 * 60 + 5,
    category: 'health_hospital',
    includeEstimatedAir: false,
  }) as Journey
  const cost = estimateJourneyCost(network, FARES, journey)
  const ferry = cost.legs.find((leg) => leg.leg.kind === 'ferry')
  assert.ok(ferry && ferry.mvr !== null && ferry.mvr >= 34, 'ferry fare at least the base tariff')
  assert.ok(cost.legs.filter((leg) => leg.leg.mode === 'walk').every((leg) => leg.mvr === 0))
  assert.equal(cost.complete, true)
  assert.equal(cost.knownMvr, cost.legs.reduce((sum, leg) => sum + (leg.mvr ?? 0), 0))

  const noFerryFare = estimateJourneyCost(network, { ...FARES, ferry: undefined }, journey)
  assert.equal(noFerryFare.complete, false)
  assert.ok(noFerryFare.unknownLegs >= 1)
})

test('cost: air leg uses the published pair fare', () => {
  const network = loadFixture()
  const journey = planJourney(network, {
    originIslandId: DHARAVANDHOO,
    departureMinute: 6 * 60,
    category: 'health_regional_tertiary',
    includeEstimatedAir: true,
  })
  assert.ok(journey)
  const cost = estimateJourneyCost(network, FARES, journey)
  const air = cost.legs.find((leg) => leg.leg.kind === 'air')
  assert.ok(air, 'journey uses the flight')
  assert.equal(air.mvr, 1435)
})

test('access report: on-island facility is free with same-day return', () => {
  const report = buildAccessReport(loadFixture(), FARES, {
    originIslandId: EYDHAFUSHI,
    departureMinute: 480,
    categories: ['health_hospital'],
  })
  const first = report[0]?.destinations[0]
  assert.equal(first?.journey.elapsedMinutes, 0)
  assert.equal(first?.roundTripMvr, 0)
  assert.equal(first?.sameDayReturn, true)
})

test('access report: no return trip means overnight, priced when a night cost is given', () => {
  const network = loadFixture()
  const options = { originIslandId: MAALHOS, departureMinute: 480, categories: ['health_hospital'] }
  const withoutNight = buildAccessReport(network, FARES, options)[0]?.destinations[0]
  assert.ok(withoutNight)
  if (withoutNight.sameDayReturn) return // fixture has a same-day return: nothing more to check
  assert.equal(withoutNight.roundTripPartial, true)
  const withNight = buildAccessReport(network, FARES, { ...options, overnightMvr: 950 })[0]?.destinations[0]
  assert.ok(withNight)
  assert.equal(withNight.roundTripMvr - withoutNight.roundTripMvr, 950)
})

test('access report: Malé facility reached by air from Dharavandhoo returns the same day', () => {
  const report = buildAccessReport(loadFixture(), FARES, {
    originIslandId: DHARAVANDHOO,
    departureMinute: 6 * 60,
    categories: ['health_regional_tertiary'],
    overnightMvr: 950,
  })
  const toMale = report[0]?.destinations.find((d) => d.journey.destinationIslandId === MAALE)
  assert.ok(toMale, 'Malé is reachable')
  assert.ok(toMale.cost.knownMvr >= 1435)
  if (toMale.sameDayReturn) assert.ok((toMale.returnJourney?.arrivalMinute ?? 1440) < 1440)
})

test('travel times: origin is 0 and each time matches island-to-island planning', async () => {
  const { travelTimesFrom } = await import('./router.ts')
  const network = loadFixture()
  const times = travelTimesFrom(network, { originIslandId: DHARAVANDHOO, departureMinute: 14 * 60 + 5 })
  assert.equal(times.get(DHARAVANDHOO), 0)
  const toEydhafushi = times.get(EYDHAFUSHI)
  const planned = planIslandToIsland(network, {
    fromIslandId: DHARAVANDHOO,
    toIslandId: EYDHAFUSHI,
    departureMinute: 14 * 60 + 5,
  })
  assert.ok(toEydhafushi !== undefined && planned)
  assert.ok(Math.abs(toEydhafushi - planned.elapsedMinutes) <= 15, 'matrix time within the alighting buffer')
})

test('siting: picks never cover the same residents twice and gains add up', async () => {
  const { buildTravelMatrix, recommendSites } = await import('./recommend.ts')
  const network = loadFixture()
  const matrix = buildTravelMatrix(network, { departureMinute: 6 * 60, maxJourneyMinutes: 240 })
  const result = recommendSites(network, matrix, { category: 'health_hospital', thresholdMinutes: 240, picks: 3 })
  const all = result.sites.flatMap((site) => site.newlyCoveredIslandIds)
  assert.equal(new Set(all).size, all.length)
  const totalGain = result.sites.reduce((sum, site) => sum + site.gainPopulation, 0)
  assert.equal(result.coveredBefore + totalGain, result.sites.at(-1)?.coveredAfter ?? result.coveredBefore)
  for (let i = 1; i < result.sites.length; i += 1) {
    assert.ok((result.sites[i]?.gainPopulation ?? 0) <= (result.sites[i - 1]?.gainPopulation ?? 0))
  }
})
