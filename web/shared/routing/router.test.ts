/// <reference types="node" />
/**
 * Contract tests for the multimodal router.
 *
 * Run with: node --experimental-strip-types --test web/shared/routing/router.test.ts
 *
 * Every expected number here is hand-derived from the fixture timetable and the buffer rules in
 * `MULTIMODAL_IMPLEMENTATION.md` §4. The fixture is small enough to verify by hand: Dharavandhoo
 * (MV007006) sits two walk-minutes from stop:RTL:207, the Z2R18 ferry leaves it at 905, stops at
 * Maalhos (208) at 915 and reaches Eydhafushi (209) at 930; the return trip departs 209 at 960.
 * Dharavandhoo is also five walk-minutes from airport:DRV, with flights DRV→MLE at 510 and 750
 * (40 minutes) and DRV↔MLE ferries connecting Hulhule to Maale by road.
 */
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import test from 'node:test'

import type {
  AccessibilityResult,
  CategoryDefinition,
  Facility,
  FrequencyService,
  Journey,
  JourneyLeg,
  JourneyRequest,
  MultimodalNetwork,
  Scenario,
  TimetabledService,
  TravelMode,
} from './types'
import {
  applyScenario,
  computeAccessibility,
  createServiceFromPattern,
  listRoutePatterns,
  planJourney,
  planJourneyWithStatus,
} from './router.ts'

const FIXTURE_URL = new URL('./fixtures/sample-network.json', import.meta.url)

const DHARAVANDHOO = 'MV007006'
const MAALHOS = 'MV007007'
const EYDHAFUSHI = 'MV007008'
const MAALE = 'MV021001'
const VILINGILI = 'MV021002'
const HULHUMALE = 'MV021003'
const HULHULE = 'MV009052'
const TEST_ISLET = 'MV007999'

const FERRY_259 = 'ferry:259:1'
const REVERSE_FERRY = 'fixture:ferry:reverse'

function loadFixture(): MultimodalNetwork {
  return JSON.parse(readFileSync(FIXTURE_URL, 'utf8')) as MultimodalNetwork
}

interface RequestOptions {
  includeEstimatedAir?: boolean
  allowNextDay?: boolean
  scenario?: Scenario
  maxJourneyMinutes?: number
  allowedModes?: TravelMode[]
  disabledRouteIds?: string[]
  disabledServiceIds?: string[]
}

function journeyRequest(originIslandId: string, departureMinute: number, category = 'health_hospital', options: RequestOptions = {}): JourneyRequest {
  return {
    originIslandId,
    departureMinute,
    category,
    includeEstimatedAir: options.includeEstimatedAir ?? false,
    ...options,
  }
}

function accessibilityRequest(departureMinute: number, options: RequestOptions = {}) {
  return {
    departureMinute,
    category: 'health_hospital',
    includeEstimatedAir: options.includeEstimatedAir ?? false,
    ...options,
  }
}

function sum(values: number[]): number {
  return values.reduce((total, value) => total + value, 0)
}

function transitLegs(journey: Journey): JourneyLeg[] {
  return journey.legs.filter((leg) => leg.kind === 'ferry' || leg.kind === 'air' || leg.kind === 'sea')
}

/** Every reported total must be explained by the legs, and the leg chain must be time-consistent. */
function assertLedger(journey: Journey): void {
  assert.equal(journey.arrivalMinute, journey.departureMinute + journey.elapsedMinutes, 'arrival must equal departure + elapsed')
  assert.equal(
    journey.elapsedMinutes,
    journey.waitMinutes + journey.rideMinutes + journey.accessMinutes + journey.transferMinutes,
    'elapsed must equal the four reported totals',
  )
  assert.equal(journey.waitMinutes, sum(journey.legs.map((leg) => leg.waitMinutes)), 'waitMinutes must equal the sum of leg waits')
  assert.equal(journey.rideMinutes, sum(transitLegs(journey).map((leg) => leg.rideMinutes)), 'rideMinutes must equal the sum of transit leg rides')
  assert.equal(
    journey.accessMinutes,
    sum(journey.legs.filter((leg) => leg.kind === 'access' || leg.kind === 'road').map((leg) => leg.rideMinutes)),
    'accessMinutes must equal the sum of access/road leg minutes',
  )
  assert.equal(journey.transfers, Math.max(0, transitLegs(journey).length - 1), 'transfers is boardings minus one')
  for (let index = 1; index < journey.legs.length; index += 1) {
    const previous = journey.legs[index - 1]
    const leg = journey.legs[index]
    assert.ok(previous !== undefined && leg !== undefined)
    assert.ok(leg.departureMinute >= previous.arrivalMinute, `leg ${index} departs before leg ${index - 1} arrives`)
  }
  if (journey.legs.length > 0) {
    const first = journey.legs[0]
    assert.ok(first !== undefined)
    // A journey can start with a frequency service departing an island node; the boarding buffer
    // is then reported as the first leg's wait, so departure − wait is the request minute.
    assert.equal(first.departureMinute - first.waitMinutes, journey.departureMinute, 'first leg departs after its boarding wait')
    const last = journey.legs[journey.legs.length - 1]
    assert.ok(last !== undefined)
    // Alighting is reported on the journey total, not on the leg: a frequency leg that ends the
    // journey still needs its ferry/air alight minutes before the destination island is reached.
    const finalAlight = last.kind === 'ferry' || last.kind === 'sea' ? 2 : last.kind === 'air' ? 15 : 0
    assert.equal(last.arrivalMinute + finalAlight, journey.arrivalMinute, 'last leg arrival plus alighting is the journey arrival')
  }
  for (const leg of journey.legs) {
    assert.ok(leg.waitMinutes >= 0, 'leg waits must not be negative')
    assert.equal(leg.rideMinutes, leg.arrivalMinute - leg.departureMinute, 'leg ride is its duration')
  }
  const transit = transitLegs(journey)
  const allTimetabled = transit.every((leg) => leg.serviceConfidence === 'verified')
  assert.equal(journey.serviceConfidence, allTimetabled ? 'verified' : 'estimated', 'confidence follows the transit legs')
  assert.equal(journey.usesEstimatedAir, journey.legs.some((leg) => leg.kind === 'air'), 'usesEstimatedAir follows air legs')
}

function getJourney(network: MultimodalNetwork, request: JourneyRequest): Journey {
  const journey = planJourney(network, request)
  assert.ok(journey, `expected a journey for ${request.originIslandId} at ${request.departureMinute}`)
  return journey
}

/* -------------------------------------------------------------------------------------------------
 * Baseline: the 09:00 Dharavandhoo → Baa Atoll Hospital journey
 * ---------------------------------------------------------------------------------------------- */

test('Dharavandhoo 09:00 → health_hospital with air excluded arrives 934 at Baa Atoll Hospital', () => {
  const network = loadFixture()
  const journey = getJourney(network, journeyRequest(DHARAVANDHOO, 540, 'health_hospital', { includeEstimatedAir: false }))

  assert.equal(journey.originIslandName, 'Dharavandhoo')
  assert.equal(journey.destinationIslandId, EYDHAFUSHI)
  assert.equal(journey.destinationIslandName, 'Eydhafushi')
  assert.deepEqual(journey.destinationFacilityIds, ['health:fixture:baa-atoll-hospital'])
  assert.deepEqual(journey.destinationFacilityNames, ['Baa Atoll Hospital (fixture)'])
  assert.equal(journey.category, 'health_hospital')
  assert.equal(journey.arrivalMinute, 934)
  assert.equal(journey.elapsedMinutes, 394)
  assert.equal(journey.waitMinutes, 363)
  assert.equal(journey.rideMinutes, 25)
  assert.equal(journey.accessMinutes, 4)
  assert.equal(journey.transferMinutes, 2)
  assert.equal(journey.transfers, 0)
  assert.equal(journey.dayOffset, 0)
  assert.equal(journey.serviceConfidence, 'verified')
  assert.equal(journey.usesEstimatedAir, false)
  assert.deepEqual(journey.modes, ['walk', 'ferry'])

  assert.equal(journey.legs.length, 3)
  const [accessOut, ferry, accessIn] = journey.legs
  assert.ok(accessOut !== undefined && ferry !== undefined && accessIn !== undefined)
  assert.equal(accessOut.kind, 'access')
  assert.equal(accessOut.fromNode, `island:${DHARAVANDHOO}`)
  assert.equal(accessOut.toNode, 'stop:207')
  assert.equal(accessOut.departureMinute, 540)
  assert.equal(accessOut.arrivalMinute, 542)
  assert.equal(accessOut.waitMinutes, 0)

  assert.equal(ferry.kind, 'ferry')
  assert.equal(ferry.mode, 'ferry')
  assert.equal(ferry.serviceId, FERRY_259)
  assert.equal(ferry.routeCode, 'Z2R18')
  assert.equal(ferry.serviceConfidence, 'verified')
  assert.equal(ferry.fromNode, 'stop:207')
  assert.equal(ferry.toNode, 'stop:209')
  assert.equal(ferry.departureMinute, 905)
  assert.equal(ferry.arrivalMinute, 930)
  assert.equal(ferry.waitMinutes, 363)
  assert.equal(ferry.rideMinutes, 25)

  assert.equal(accessIn.kind, 'access')
  assert.equal(accessIn.fromNode, 'stop:209')
  assert.equal(accessIn.toNode, `island:${EYDHAFUSHI}`)
  assert.equal(accessIn.departureMinute, 932)
  assert.equal(accessIn.arrivalMinute, 934)

  assertLedger(journey)
})

test('air ON beats the ferry at 09:00: Maale/IGMH at 822, estimated, four legs', () => {
  const network = loadFixture()
  const journey = getJourney(network, journeyRequest(DHARAVANDHOO, 540, 'health_hospital', { includeEstimatedAir: true }))

  assert.equal(journey.destinationIslandId, MAALE)
  assert.equal(journey.destinationIslandName, 'Maale')
  assert.deepEqual(journey.destinationFacilityIds, ['health:fixture:igmh'])
  assert.equal(journey.arrivalMinute, 822)
  assert.equal(journey.elapsedMinutes, 282)
  assert.equal(journey.waitMinutes, 205)
  assert.equal(journey.rideMinutes, 40)
  assert.equal(journey.accessMinutes, 22)
  assert.equal(journey.transferMinutes, 15)
  assert.equal(journey.dayOffset, 0)
  assert.equal(journey.serviceConfidence, 'estimated')
  assert.equal(journey.usesEstimatedAir, true)
  assert.deepEqual(journey.modes, ['walk', 'air', 'road'])
  assert.ok(journey.legs.length >= 3)
  assert.equal(journey.legs.length, 4)

  const [walkToAirport, air, walkToHulhule, roadToMaale] = journey.legs
  assert.ok(walkToAirport !== undefined && air !== undefined && walkToHulhule !== undefined && roadToMaale !== undefined)
  assert.equal(walkToAirport.toNode, 'airport:DRV')
  assert.equal(air.kind, 'air')
  assert.equal(air.serviceId, 'air:DRV-MLE')
  assert.equal(air.departureMinute, 750)
  assert.equal(air.arrivalMinute, 790)
  assert.equal(air.waitMinutes, 205)
  assert.equal(walkToHulhule.kind, 'access')
  assert.equal(walkToHulhule.fromNode, 'airport:MLE')
  assert.equal(walkToHulhule.toNode, `island:${HULHULE}`)
  assert.equal(roadToMaale.kind, 'road')
  assert.equal(roadToMaale.toNode, `island:${MAALE}`)

  assertLedger(journey)
})

/* -------------------------------------------------------------------------------------------------
 * Scenarios: added trip, cancellation, delay
 * ---------------------------------------------------------------------------------------------- */

test('createServiceFromPattern shifts Z2R18 to 570 and the added trip arrives 599', () => {
  const network = loadFixture()
  const baseline = getJourney(network, journeyRequest(DHARAVANDHOO, 540, 'health_hospital', { includeEstimatedAir: false }))
  assert.equal(baseline.arrivalMinute, 934)

  const added = createServiceFromPattern(network, '259', 570)
  assert.equal(added.id, `${FERRY_259}:added:570`)
  assert.equal(added.routeCode, 'Z2R18')
  assert.deepEqual(added.stops.map((stop) => stop.departure), [570, 580, 595])
  assert.deepEqual(added.stops.map((stop) => stop.arrival), [570, 580, 595])
  assert.deepEqual(added.stops.map((stop) => stop.stopId), ['207', '208', '209'])
  // Same leg durations as the source pattern: 10 minutes to Maalhos, 15 to Eydhafushi.
  assert.equal(added.stops[1]!.departure - added.stops[0]!.departure, 10)
  assert.equal(added.stops[2]!.departure - added.stops[1]!.departure, 15)

  const journey = getJourney(network, journeyRequest(DHARAVANDHOO, 540, 'health_hospital', { includeEstimatedAir: false, scenario: { addedTrips: [added] } }))
  assert.equal(journey.arrivalMinute, 599)
  assert.equal(journey.elapsedMinutes, 59)
  assert.equal(journey.waitMinutes, 28)
  assert.equal(journey.rideMinutes, 25)
  assert.equal(journey.accessMinutes, 4)
  assert.equal(journey.transferMinutes, 2)
  assert.equal(journey.legs.length, 3)
  const ferry = journey.legs[1]
  assert.ok(ferry !== undefined)
  assert.equal(ferry.serviceId, added.id)
  assert.equal(ferry.departureMinute, 570)
  assert.equal(ferry.arrivalMinute, 595)
  assert.equal(ferry.routeCode, 'Z2R18')
  assertLedger(journey)

  // The scenario is applied to a clone, never to the caller's network.
  assert.equal(planJourney(network, journeyRequest(DHARAVANDHOO, 540, 'health_hospital', { includeEstimatedAir: false }))?.arrivalMinute, 934)
  assert.equal(network.services.filter((service) => service.kind === 'timetabled').length, 2)
})

test('cancelling ferry:259:1 makes Dharavandhoo unreachable without leaking into the network', () => {
  const network = loadFixture()
  const scenario: Scenario = { cancelledServiceIds: [FERRY_259] }
  const plan = planJourneyWithStatus(network, journeyRequest(DHARAVANDHOO, 540, 'health_hospital', { includeEstimatedAir: false, scenario }))
  assert.equal(plan.status, 'not_reachable')
  assert.equal(plan.journey, null)

  assert.equal(planJourneyWithStatus(network, journeyRequest(DHARAVANDHOO, 540, 'health_hospital', { includeEstimatedAir: false })).status, 'reachable')
  assert.equal(planJourney(network, journeyRequest(DHARAVANDHOO, 540, 'health_hospital', { includeEstimatedAir: false }))?.arrivalMinute, 934)
})

test('delaying ferry:259:1 by 30 minutes shifts the arrival to 964', () => {
  const network = loadFixture()
  const scenario: Scenario = { delayMinutesByServiceId: { [FERRY_259]: 30 } }
  const journey = getJourney(network, journeyRequest(DHARAVANDHOO, 540, 'health_hospital', { includeEstimatedAir: false, scenario }))

  assert.equal(journey.arrivalMinute, 964)
  assert.equal(journey.elapsedMinutes, 424)
  assert.equal(journey.waitMinutes, 393)
  assert.equal(journey.rideMinutes, 25)
  assert.equal(journey.accessMinutes, 4)
  assert.equal(journey.transferMinutes, 2)
  const ferry = journey.legs[1]
  assert.ok(ferry !== undefined)
  assert.equal(ferry.departureMinute, 935)
  assert.equal(ferry.arrivalMinute, 960)
  assert.equal(ferry.serviceId, FERRY_259)
  assertLedger(journey)
})

/* -------------------------------------------------------------------------------------------------
 * Reverse direction, same-vehicle, and the departure-time boundary
 * ---------------------------------------------------------------------------------------------- */

test('reverse run: Maalhos 940 and 958 both arrive 994; the last boarding minute is 958', () => {
  const network = loadFixture()

  for (const departureMinute of [940, 958]) {
    const journey = getJourney(network, journeyRequest(MAALHOS, departureMinute, 'health_any', { includeEstimatedAir: false }))
    assert.equal(journey.destinationIslandId, DHARAVANDHOO)
    assert.equal(journey.arrivalMinute, 994)
    assert.equal(journey.serviceConfidence, 'verified')
    const ferry = journey.legs[1]
    assert.ok(ferry !== undefined)
    assert.equal(ferry.serviceId, REVERSE_FERRY)
    assert.equal(ferry.departureMinute, 975)
    assert.equal(ferry.arrivalMinute, 990)
    assert.equal(ferry.waitMinutes, 975 - (departureMinute + 2))
    assert.equal(journey.legs.filter((leg) => leg.kind === 'ferry').length, 1)
    assertLedger(journey)
  }

  const at958 = getJourney(network, journeyRequest(MAALHOS, 958, 'health_any', { includeEstimatedAir: false }))
  assert.equal(at958.waitMinutes, 15)

  const missed = planJourneyWithStatus(network, journeyRequest(MAALHOS, 959, 'health_any', { includeEstimatedAir: false }))
  assert.equal(missed.status, 'not_reachable')
  assert.equal(missed.journey, null)
})

test('origin that already hosts the category gets a zero-minute verified journey', () => {
  const network = loadFixture()
  const journey = getJourney(network, journeyRequest(DHARAVANDHOO, 540, 'health_any', { includeEstimatedAir: true }))
  assert.equal(journey.destinationIslandId, DHARAVANDHOO)
  assert.equal(journey.arrivalMinute, 540)
  assert.equal(journey.elapsedMinutes, 0)
  assert.deepEqual(journey.legs, [])
  assert.equal(journey.waitMinutes, 0)
  assert.equal(journey.rideMinutes, 0)
  assert.equal(journey.accessMinutes, 0)
  assert.equal(journey.transferMinutes, 0)
  assert.equal(journey.transfers, 0)
  assert.equal(journey.serviceConfidence, 'verified')
  assert.equal(journey.usesEstimatedAir, false)
  assert.deepEqual(journey.destinationFacilityIds, ['health:fixture:drv-health-centre'])
  assert.deepEqual(journey.destinationFacilityNames, ['Dharavandhoo Health Centre (fixture)'])
})

test('same-vehicle: Dharavandhoo and Maalhos reach Eydhafushi with exactly one ferry leg', () => {
  const network = loadFixture()

  const fromDharavandhoo = getJourney(network, journeyRequest(DHARAVANDHOO, 540, 'health_hospital', { includeEstimatedAir: false }))
  assert.equal(fromDharavandhoo.legs.filter((leg) => leg.kind === 'ferry').length, 1)
  assert.equal(fromDharavandhoo.transfers, 0)

  const fromMaalhos = getJourney(network, journeyRequest(MAALHOS, 540, 'health_hospital', { includeEstimatedAir: false }))
  assert.equal(fromMaalhos.legs.filter((leg) => leg.kind === 'ferry').length, 1)
  assert.equal(fromMaalhos.arrivalMinute, 934)
  assert.equal(fromMaalhos.elapsedMinutes, 394)
  assert.equal(fromMaalhos.waitMinutes, 373)
  assert.equal(fromMaalhos.rideMinutes, 15)
  const ferry = fromMaalhos.legs[1]
  assert.ok(ferry !== undefined)
  assert.equal(ferry.serviceId, FERRY_259)
  assert.equal(ferry.departureMinute, 915)
  assert.equal(ferry.arrivalMinute, 930)
  assertLedger(fromMaalhos)
})

test('departure boundary: 888 catches the 905 ferry, 889 has already missed it', () => {
  const network = loadFixture()

  const caught = getJourney(network, journeyRequest(DHARAVANDHOO, 888, 'health_hospital', { includeEstimatedAir: false }))
  assert.equal(caught.arrivalMinute, 934)
  assert.equal(caught.waitMinutes, 15)

  const missed = planJourneyWithStatus(network, journeyRequest(DHARAVANDHOO, 889, 'health_hospital', { includeEstimatedAir: false }))
  assert.equal(missed.status, 'not_reachable')
  assert.equal(missed.journey, null)
})

/* -------------------------------------------------------------------------------------------------
 * Accessibility semantics: air, frequency ferries, no-destination, no-origin-access
 * ---------------------------------------------------------------------------------------------- */

test('07:00 tertiary care needs estimated air: 582 with air ON, unreachable with air OFF', () => {
  const network = loadFixture()

  const airON = getJourney(network, journeyRequest(DHARAVANDHOO, 420, 'health_regional_tertiary', { includeEstimatedAir: true }))
  assert.equal(airON.destinationIslandId, MAALE)
  assert.equal(airON.destinationFacilityIds[0], 'health:fixture:igmh')
  assert.equal(airON.arrivalMinute, 582)
  assert.equal(airON.elapsedMinutes, 162)
  assert.equal(airON.waitMinutes, 85)
  assert.equal(airON.rideMinutes, 40)
  assert.equal(airON.accessMinutes, 22)
  assert.equal(airON.transferMinutes, 15)
  assert.equal(airON.serviceConfidence, 'estimated')
  assert.equal(airON.usesEstimatedAir, true)
  assert.ok(airON.legs.length >= 3)
  const air = airON.legs.find((leg) => leg.kind === 'air')
  assert.ok(air !== undefined)
  assert.equal(air.departureMinute, 510)
  assert.equal(air.arrivalMinute, 550)
  assertLedger(airON)

  const airOFF = planJourneyWithStatus(network, journeyRequest(DHARAVANDHOO, 420, 'health_regional_tertiary', { includeEstimatedAir: false }))
  assert.equal(airOFF.status, 'not_reachable')
  assert.equal(airOFF.journey, null)
})

test('frequency ferry: Vilin\'gili 08:00 arrives 504 for 24 minutes; last departure 615 boards at 600', () => {
  const network = loadFixture()

  const journey = getJourney(network, journeyRequest(VILINGILI, 480, 'health_hospital', { includeEstimatedAir: false }))
  assert.equal(journey.destinationIslandId, MAALE)
  assert.equal(journey.arrivalMinute, 504)
  assert.equal(journey.elapsedMinutes, 24)
  assert.equal(journey.waitMinutes, 15)
  assert.equal(journey.rideMinutes, 7)
  assert.equal(journey.accessMinutes, 0)
  assert.equal(journey.transferMinutes, 2)
  assert.equal(journey.serviceConfidence, 'estimated')
  assert.equal(journey.usesEstimatedAir, false)
  assert.deepEqual(journey.modes, ['ferry'])
  assert.equal(journey.legs.length, 1)
  const ferry = journey.legs[0]
  assert.ok(ferry !== undefined)
  assert.equal(ferry.serviceId, 'frequency:ferry:villimale-male')
  assert.equal(ferry.serviceConfidence, 'estimated')
  assert.equal(ferry.departureMinute, 495)
  assert.equal(ferry.arrivalMinute, 502)
  assertLedger(journey)

  const last = getJourney(network, journeyRequest(VILINGILI, 600, 'health_hospital', { includeEstimatedAir: false }))
  assert.equal(last.arrivalMinute, 624)
  assert.equal(last.legs[0]?.departureMinute, 615)

  const missed = planJourneyWithStatus(network, journeyRequest(VILINGILI, 601, 'health_hospital', { includeEstimatedAir: false }))
  assert.equal(missed.status, 'not_reachable')
})

test('no_origin_access is a coverage state: MV007999 has no way out, MV021002 has a frequency ferry', () => {
  const network = loadFixture()

  const plan = planJourneyWithStatus(network, journeyRequest(TEST_ISLET, 540, 'health_hospital', { includeEstimatedAir: true }))
  assert.equal(plan.status, 'no_origin_access')
  assert.equal(plan.journey, null)

  const result = computeAccessibility(network, accessibilityRequest(480, { includeEstimatedAir: true }))
  assert.equal(result.perOrigin[TEST_ISLET]?.status, 'no_origin_access')
  assert.equal(result.summary.noOriginAccessPopulation, 10)
  assert.equal(result.summary.originsNoAccess, 1)

  // MV021002 has no fixed edge but a frequency ferry leaving its island node, so it is routable.
  assert.notEqual(result.perOrigin[VILINGILI]?.status, 'no_origin_access')
  assert.equal(result.perOrigin[VILINGILI]?.journey?.arrivalMinute, 504)
  assert.equal(result.perOrigin[VILINGILI]?.journey?.serviceConfidence, 'estimated')
})

test('no_destination wins for a category the country does not serve, and is counted in the summary', () => {
  const network = loadFixture()
  const result = computeAccessibility(network, { departureMinute: 480, category: 'not_a_real_category', includeEstimatedAir: true })

  assert.equal(result.summary.category, 'not_a_real_category')
  assert.equal(result.summary.populationTotal, 214669)
  assert.equal(result.summary.populationReachable, 0)
  assert.equal(result.summary.originsReachable, 0)
  assert.equal(result.summary.originsNoDestination, 8)
  assert.equal(result.summary.originsUnreachable, 0)
  assert.equal(result.summary.originsNoAccess, 0)
  assert.equal(result.summary.noDestinationPopulation, 214669)
  assert.equal(result.summary.unreachablePopulation, 0)
  assert.equal(result.summary.noOriginAccessPopulation, 0)
  assert.equal(result.summary.coverage, 0)
  for (const status of Object.values(result.perOrigin)) {
    assert.equal(status.status, 'no_destination')
    assert.equal(status.journey, null)
  }

  // no_destination takes precedence over the origin's lack of access.
  assert.equal(planJourneyWithStatus(network, journeyRequest(TEST_ISLET, 540, 'not_a_real_category')).status, 'no_destination')
})

/* -------------------------------------------------------------------------------------------------
 * Next day, monotonicity, maximum journey time, purity, ordering
 * ---------------------------------------------------------------------------------------------- */

test('allowNextDay repeats the 905 ferry at +1440: 16:40 arrives 2374 on day 1', () => {
  const network = loadFixture()
  const journey = getJourney(network, journeyRequest(DHARAVANDHOO, 1000, 'health_hospital', { includeEstimatedAir: false, allowNextDay: true }))

  assert.equal(journey.arrivalMinute, 2374)
  assert.equal(journey.elapsedMinutes, 1374)
  assert.equal(journey.dayOffset, 1)
  assert.equal(journey.waitMinutes, 1343)
  assert.equal(journey.rideMinutes, 25)
  assert.equal(journey.accessMinutes, 4)
  assert.equal(journey.transferMinutes, 2)
  assert.equal(journey.serviceConfidence, 'verified')
  const ferry = journey.legs[1]
  assert.ok(ferry !== undefined)
  assert.equal(ferry.departureMinute, 2345)
  assert.equal(ferry.arrivalMinute, 2370)
  assert.equal(ferry.serviceId, FERRY_259)
  assert.ok(journey.legs.every((leg) => leg.departureMinute >= 0))
  assertLedger(journey)

  const sameDayOnly = planJourneyWithStatus(network, journeyRequest(DHARAVANDHOO, 1000, 'health_hospital', { includeEstimatedAir: false }))
  assert.equal(sameDayOnly.status, 'not_reachable')
  assert.equal(sameDayOnly.journey, null)
})

test('arrival time is monotone non-decreasing in departure time and never recovers after a miss', () => {
  const network = loadFixture()

  for (const includeEstimatedAir of [false, true]) {
    let previousArrival: number | null = null
    let sawUnreachable = false
    for (let departureMinute = 0; departureMinute < 1440; departureMinute += 1) {
      const journey = planJourney(network, journeyRequest(DHARAVANDHOO, departureMinute, 'health_hospital', { includeEstimatedAir }))
      if (!journey) {
        sawUnreachable = true
        continue
      }
      assert.equal(sawUnreachable, false, `air=${includeEstimatedAir}: departure ${departureMinute} recovered after a miss`)
      if (previousArrival !== null) {
        assert.ok(journey.arrivalMinute >= previousArrival, `air=${includeEstimatedAir}: arrival fell at departure ${departureMinute}`)
      }
      previousArrival = journey.arrivalMinute
    }
  }
})

test('maxJourneyMinutes is inclusive and never returns a slower journey than allowed', () => {
  const network = loadFixture()

  assert.equal(planJourney(network, journeyRequest(DHARAVANDHOO, 540, 'health_hospital', { includeEstimatedAir: false, maxJourneyMinutes: 394 }))?.arrivalMinute, 934)
  const tooShort = planJourneyWithStatus(network, journeyRequest(DHARAVANDHOO, 540, 'health_hospital', { includeEstimatedAir: false, maxJourneyMinutes: 393 }))
  assert.equal(tooShort.status, 'not_reachable')
  assert.equal(tooShort.journey, null)
})

test('invalid departure minutes are rejected instead of silently planning', () => {
  const network = loadFixture()
  assert.throws(() => planJourney(network, journeyRequest(DHARAVANDHOO, Number.NaN)), TypeError)
  assert.throws(() => computeAccessibility(network, accessibilityRequest(Number.POSITIVE_INFINITY)), TypeError)
})

test('planning, scenarios and pattern creation never mutate the input network', () => {
  const network = loadFixture()
  const before = JSON.stringify(network)

  planJourney(network, journeyRequest(DHARAVANDHOO, 540, 'health_hospital', { includeEstimatedAir: true }))
  computeAccessibility(network, accessibilityRequest(480, { includeEstimatedAir: true }))
  applyScenario(network, {
    cancelledServiceIds: [FERRY_259],
    delayMinutesByServiceId: { [REVERSE_FERRY]: 30 },
    addedTrips: [createServiceFromPattern(network, '259', 570)],
  })
  createServiceFromPattern(network, '259', 570)

  assert.equal(JSON.stringify(network), before)
})

test('applyScenario clones containers and applies cancel, delay and add exactly once', () => {
  const network = loadFixture()
  const added = createServiceFromPattern(network, '259', 570, 'trip:added')
  const applied = applyScenario(network, {
    cancelledServiceIds: [FERRY_259],
    delayMinutesByServiceId: { [REVERSE_FERRY]: 5 },
    addedTrips: [added],
  })

  assert.notEqual(applied, network)
  assert.notEqual(applied.islands, network.islands)
  assert.notEqual(applied.services, network.services)
  assert.equal(applied.services.filter((service) => service.kind === 'timetabled').length, 2)
  assert.equal(applied.services.some((service) => service.id === FERRY_259), false)

  const delayed = applied.services.find((service) => service.id === REVERSE_FERRY) as TimetabledService
  assert.deepEqual(delayed.stops.map((stop) => stop.departure), [965, 980, 995])
  const addedInClone = applied.services.find((service) => service.id === 'trip:added') as TimetabledService | undefined
  assert.ok(addedInClone !== undefined)
  assert.deepEqual(addedInClone.stops.map((stop) => stop.departure), [570, 580, 595])

  // The source network and the source service objects are untouched.
  assert.equal(network.services.length, 6)
  const originalFerry = network.services.find((service) => service.id === FERRY_259) as TimetabledService
  const originalReverse = network.services.find((service) => service.id === REVERSE_FERRY) as TimetabledService
  assert.deepEqual(originalFerry.stops.map((stop) => stop.departure), [905, 915, 930])
  assert.deepEqual(originalReverse.stops.map((stop) => stop.departure), [960, 975, 990])
})

/* -------------------------------------------------------------------------------------------------
 * National accessibility summary (fixture, 08:00)
 * ---------------------------------------------------------------------------------------------- */

test('08:00 accessibility with air excluded: 214669 total, 214659 reachable, one no-access origin', () => {
  const network = loadFixture()
  const result = computeAccessibility(network, accessibilityRequest(480, { includeEstimatedAir: false }))
  const summary = result.summary

  assert.deepEqual(Object.keys(result.perOrigin).sort(), [HULHULE, HULHUMALE, MAALE, MAALHOS, DHARAVANDHOO, EYDHAFUSHI, TEST_ISLET, VILINGILI].sort())
  assert.equal(summary.category, 'health_hospital')
  assert.equal(summary.populationTotal, 214669)
  assert.equal(summary.populationReachable, 214659)
  assert.equal(summary.within60, 213090)
  assert.equal(summary.within120, 213090)
  assert.equal(summary.within240, 213090)
  assert.equal(summary.unreachablePopulation, 0)
  assert.equal(summary.noOriginAccessPopulation, 10)
  assert.equal(summary.noDestinationPopulation, 0)
  assert.equal(summary.coverage, 214659 / 214669)
  assert.equal(summary.reachableVerifiedPopulation, 207904)
  assert.equal(summary.reachableEstimatedPopulation, 6755)
  assert.equal(summary.originsReachable, 7)
  assert.equal(summary.originsUnreachable, 0)
  assert.equal(summary.originsNoAccess, 1)
  assert.equal(summary.originsNoDestination, 0)
  assert.equal(
    summary.populationReachable + summary.unreachablePopulation + summary.noOriginAccessPopulation + summary.noDestinationPopulation,
    summary.populationTotal,
    'population partitions must add up to the total',
  )

  const expectedByOrigin: Record<string, [number, number, string]> = {
    [DHARAVANDHOO]: [934, 454, 'verified'],
    [MAALHOS]: [934, 454, 'verified'],
    [EYDHAFUSHI]: [480, 0, 'verified'],
    [MAALE]: [480, 0, 'verified'],
    [VILINGILI]: [504, 24, 'estimated'],
    [HULHUMALE]: [505, 25, 'verified'],
    [HULHULE]: [495, 15, 'verified'],
  }
  for (const [originIslandId, [arrivalMinute, elapsedMinutes, confidence]] of Object.entries(expectedByOrigin)) {
    const origin = result.perOrigin[originIslandId]
    assert.ok(origin !== undefined)
    assert.equal(origin.status, 'reachable', originIslandId)
    assert.ok(origin.journey !== null)
    assert.equal(origin.journey.arrivalMinute, arrivalMinute, originIslandId)
    assert.equal(origin.journey.elapsedMinutes, elapsedMinutes, originIslandId)
    assert.equal(origin.journey.serviceConfidence, confidence, originIslandId)
    assertLedger(origin.journey)
  }
})

test('08:00 accessibility with air included keeps the population but flips Dharavandhoo to estimated', () => {
  const network = loadFixture()
  const airOFF = computeAccessibility(network, accessibilityRequest(480, { includeEstimatedAir: false })).summary
  const airON = computeAccessibility(network, accessibilityRequest(480, { includeEstimatedAir: true })).summary

  assert.equal(airON.populationTotal, airOFF.populationTotal)
  assert.equal(airON.populationReachable, airOFF.populationReachable)
  assert.equal(airON.within60, airOFF.within60)
  assert.equal(airON.within120, airOFF.within120)
  assert.equal(airON.within240, airOFF.within240)
  assert.equal(airON.noOriginAccessPopulation, airOFF.noOriginAccessPopulation)
  assert.equal(airON.reachableVerifiedPopulation, 206907)
  assert.equal(airON.reachableEstimatedPopulation, 7752)
  assert.equal(airON.originsReachable, 7)
  assert.equal(airON.originsNoAccess, 1)

  const dharavandhoo = computeAccessibility(network, accessibilityRequest(480, { includeEstimatedAir: true })).perOrigin[DHARAVANDHOO]
  assert.ok(dharavandhoo?.journey !== null && dharavandhoo !== undefined)
  assert.equal(dharavandhoo.journey.arrivalMinute, 822)
  assert.equal(dharavandhoo.journey.elapsedMinutes, 342)
  assert.equal(dharavandhoo.journey.serviceConfidence, 'estimated')
  assert.equal(dharavandhoo.journey.usesEstimatedAir, true)
})

test('accessibility population comes from islands, not from meta.population', () => {
  const network = loadFixture()
  network.meta.population.origins = 1
  const summary = computeAccessibility(network, accessibilityRequest(480, { includeEstimatedAir: false })).summary
  assert.equal(summary.populationTotal, 214669)
  assert.equal(summary.populationReachable, 214659)
})

test('a cancelled service inside a scenario changes accessibility on a clone only', () => {
  const network = loadFixture()
  const scenario: Scenario = { cancelledServiceIds: [FERRY_259] }
  const cancelled = computeAccessibility(network, accessibilityRequest(480, { includeEstimatedAir: false, scenario }))
  assert.equal(cancelled.summary.populationReachable, 213090)
  assert.equal(cancelled.summary.originsUnreachable, 2)
  assert.equal(cancelled.perOrigin[DHARAVANDHOO]?.status, 'not_reachable')
  assert.equal(cancelled.perOrigin[MAALHOS]?.status, 'not_reachable')

  const untouched = computeAccessibility(network, accessibilityRequest(480, { includeEstimatedAir: false }))
  assert.equal(untouched.summary.populationReachable, 214659)
})

/* -------------------------------------------------------------------------------------------------
 * Helpers and determinism
 * ---------------------------------------------------------------------------------------------- */

test('listRoutePatterns exposes both fixture patterns for the add-trip UI', () => {
  const network = loadFixture()
  const patterns = listRoutePatterns(network)
  assert.equal(patterns.length, 2)
  assert.deepEqual(patterns.map((pattern) => pattern.routeCode), ['Z2R18', 'Z2R18R'])
  const dharavandhooPattern = patterns.find((pattern) => pattern.serviceId === FERRY_259)
  assert.ok(dharavandhooPattern !== undefined)
  assert.equal(dharavandhooPattern.firstDeparture, 905)
  assert.equal(dharavandhooPattern.stopCount, 3)
  assert.equal(dharavandhooPattern.firstStopIslandId, DHARAVANDHOO)
  assert.equal(dharavandhooPattern.lastStopIslandId, EYDHAFUSHI)
})

test('createServiceFromPattern accepts a route id or an exact service id and preserves dwell', () => {
  const network = loadFixture()

  const byRouteId = createServiceFromPattern(network, '259', 570)
  assert.equal(byRouteId.id, `${FERRY_259}:added:570`)

  const byServiceId = createServiceFromPattern(network, REVERSE_FERRY, 950, 'trip:reverse-shift')
  assert.equal(byServiceId.id, 'trip:reverse-shift')
  assert.deepEqual(byServiceId.stops.map((stop) => stop.departure), [950, 965, 980])
  assert.deepEqual(byServiceId.stops.map((stop) => stop.arrival), [950, 965, 980])

  assert.throws(() => createServiceFromPattern(network, 'route-does-not-exist', 570), /no timetabled service/)
  assert.throws(() => createServiceFromPattern(network, '259', Number.NaN), TypeError)
})

test('service ordering does not change the base journey or the accessibility summary', () => {
  const network = loadFixture()
  const reversed: MultimodalNetwork = { ...network, services: [...network.services].reverse() }

  const original = getJourney(network, journeyRequest(DHARAVANDHOO, 540, 'health_hospital', { includeEstimatedAir: false }))
  const shuffled = getJourney(reversed, journeyRequest(DHARAVANDHOO, 540, 'health_hospital', { includeEstimatedAir: false }))
  assert.deepEqual(
    { arrival: shuffled.arrivalMinute, elapsed: shuffled.elapsedMinutes, serviceId: shuffled.legs[1]?.serviceId, confidence: shuffled.serviceConfidence },
    { arrival: original.arrivalMinute, elapsed: original.elapsedMinutes, serviceId: original.legs[1]?.serviceId, confidence: original.serviceConfidence },
  )

  const originalSummary = computeAccessibility(network, accessibilityRequest(480, { includeEstimatedAir: true })).summary
  const shuffledSummary = computeAccessibility(reversed, accessibilityRequest(480, { includeEstimatedAir: true })).summary
  assert.deepEqual(shuffledSummary, originalSummary)
})

/* -------------------------------------------------------------------------------------------------
 * v2: transport scope, route selection and scenario additions (§10)
 * ---------------------------------------------------------------------------------------------- */

const ADDED_SEA_ROUTE_ID = 'scenario:sea:baa'
const ADDED_SEA_SERVICE_ID = 'scenario:sea:dharavandhoo-eydhafushi'

function scenarioSeaLink(overrides: Partial<FrequencyService> = {}): FrequencyService {
  return {
    id: ADDED_SEA_SERVICE_ID,
    kind: 'frequency',
    mode: 'sea',
    routeId: ADDED_SEA_ROUTE_ID,
    label: 'Scenario sea link',
    fromNode: `island:${DHARAVANDHOO}`,
    toNode: `island:${EYDHAFUSHI}`,
    weeklyFrequency: 7,
    departuresPerDay: 1,
    operatingWindow: { start: 540, end: 600 },
    blockMinutes: 60,
    departures: [555],
    confidence: 'estimated_frequency',
    status: 'assumed',
    source: 'scenario',
    ...overrides,
  }
}

function scenarioFacility(overrides: Partial<Facility> = {}): Facility {
  return {
    id: 'scenario:facility:maalhos-hospital',
    name: 'Maalhos User Hospital',
    islandId: MAALHOS,
    kind: 'health',
    categories: ['health_any', 'health_hospital'],
    precision: 'island',
    source: 'scenario',
    reviewed: true,
    userAdded: true,
    serviceCategories: ['health_hospital'],
    ...overrides,
  }
}

test('land-only preset excludes ferries and air: four origins reachable, offshore islands have no way out', () => {
  const network = loadFixture()
  const result = computeAccessibility(network, accessibilityRequest(480, { allowedModes: ['land'] }))
  const summary = result.summary

  assert.equal(summary.populationReachable, 206335)
  assert.equal(summary.originsReachable, 4)
  assert.equal(summary.within60, 206335)
  assert.equal(summary.within120, 206335)
  assert.equal(summary.within240, 206335)
  assert.equal(summary.unreachablePopulation, 1569)
  assert.equal(summary.originsUnreachable, 2)
  assert.equal(summary.noOriginAccessPopulation, 6765)
  assert.equal(summary.originsNoAccess, 2)
  assert.equal(summary.reachableVerifiedPopulation, 206335)
  assert.equal(summary.reachableEstimatedPopulation, 0)
  assert.equal(
    summary.populationReachable + summary.unreachablePopulation + summary.noOriginAccessPopulation + summary.noDestinationPopulation,
    summary.populationTotal,
  )

  for (const originId of [DHARAVANDHOO, MAALHOS]) assert.equal(result.perOrigin[originId]?.status, 'not_reachable', originId)
  for (const originId of [VILINGILI, TEST_ISLET]) assert.equal(result.perOrigin[originId]?.status, 'no_origin_access', originId)
  for (const originId of [MAALE, HULHULE, HULHUMALE, EYDHAFUSHI]) {
    const origin = result.perOrigin[originId]
    assert.equal(origin?.status, 'reachable', originId)
    assert.ok(origin?.journey !== null && origin !== undefined)
    assert.ok(
      origin.journey.legs.every((leg) => leg.kind === 'road' || leg.kind === 'access'),
      'a land-only journey may only use land legs',
    )
    assertLedger(origin.journey)
  }

  // Hulhumaale -> Hulhule (10) -> Maale (15) is the only long land chain in the fixture.
  const hulhumale = result.perOrigin[HULHUMALE]
  assert.ok(hulhumale?.journey !== null && hulhumale !== undefined)
  assert.equal(hulhumale.journey.destinationIslandId, MAALE)
  assert.equal(hulhumale.journey.arrivalMinute, 505)
  assert.equal(hulhumale.journey.elapsedMinutes, 25)
})

test('sea-only preset keeps the published ferry network and applies ferry boarding buffers', () => {
  const network = loadFixture()
  const result = computeAccessibility(network, accessibilityRequest(480, { allowedModes: ['sea'] }))
  const summary = result.summary

  assert.equal(summary.populationReachable, 146574)
  assert.equal(summary.originsReachable, 3)
  assert.equal(summary.within60, 146574)
  assert.equal(summary.within120, 146574)
  assert.equal(summary.within240, 146574)
  assert.equal(summary.noOriginAccessPopulation, 68095)
  assert.equal(summary.originsNoAccess, 5)
  assert.equal(summary.reachableVerifiedPopulation, 139819)
  assert.equal(summary.reachableEstimatedPopulation, 6755)
  assert.equal(result.perOrigin[DHARAVANDHOO]?.status, 'no_origin_access')
  assert.equal(result.perOrigin[MAALHOS]?.status, 'no_origin_access')
  assert.equal(result.perOrigin[MAALE]?.journey?.elapsedMinutes, 0, 'an origin hosting the facility needs no travel')

  const vilingili = result.perOrigin[VILINGILI]
  assert.ok(vilingili?.journey !== null && vilingili !== undefined)
  assert.equal(vilingili.journey.arrivalMinute, 504)
  assert.equal(vilingili.journey.elapsedMinutes, 24)
  assert.equal(vilingili.journey.waitMinutes, 15)
  assert.equal(vilingili.journey.rideMinutes, 7)
  assert.equal(vilingili.journey.transferMinutes, 2)
  assert.equal(vilingili.journey.legs.length, 1)
  assert.equal(vilingili.journey.legs[0]?.kind, 'ferry')
  assertLedger(vilingili.journey)
})

test('air-only preset cannot leave an island without land access; land+air flies to Maale', () => {
  const network = loadFixture()
  const airOnly = computeAccessibility(network, accessibilityRequest(480, { allowedModes: ['air'] }))
  assert.equal(airOnly.summary.populationReachable, 139819)
  assert.equal(airOnly.summary.originsReachable, 2)
  assert.equal(airOnly.summary.noOriginAccessPopulation, 74850)
  assert.equal(airOnly.summary.originsNoAccess, 6)
  assert.equal(airOnly.perOrigin[DHARAVANDHOO]?.status, 'no_origin_access')

  const journey = getJourney(network, journeyRequest(DHARAVANDHOO, 540, 'health_hospital', { allowedModes: ['land', 'air'] }))
  assert.equal(journey.destinationIslandId, MAALE)
  assert.equal(journey.arrivalMinute, 822)
  assert.equal(journey.elapsedMinutes, 282)
  assert.equal(journey.serviceConfidence, 'estimated')
  assert.equal(journey.usesEstimatedAir, true)
  assert.equal(journey.legs.filter((leg) => leg.kind === 'air').length, 1)
  assertLedger(journey)

  const landAir = computeAccessibility(network, accessibilityRequest(480, { allowedModes: ['land', 'air'] })).summary
  assert.equal(landAir.populationReachable, 207332)
  assert.equal(landAir.originsReachable, 5)
  assert.equal(landAir.within60, 206335)
  assert.equal(landAir.within240, 206335)
  assert.equal(landAir.unreachablePopulation, 572)
  assert.equal(landAir.noOriginAccessPopulation, 6765)
  assert.equal(landAir.reachableVerifiedPopulation, 206335)
  assert.equal(landAir.reachableEstimatedPopulation, 997)
})

test('allowedModes takes precedence over the legacy includeEstimatedAir switch', () => {
  const network = loadFixture()

  const explicitLand = computeAccessibility(network, accessibilityRequest(480, { allowedModes: ['land'], includeEstimatedAir: true })).summary
  assert.equal(explicitLand.populationReachable, 206335)
  assert.equal(explicitLand.reachableEstimatedPopulation, 0)

  const explicitAir = computeAccessibility(network, accessibilityRequest(480, { allowedModes: ['air'], includeEstimatedAir: false })).summary
  assert.equal(explicitAir.populationReachable, 139819)

  const legacyOff = computeAccessibility(network, accessibilityRequest(480, { includeEstimatedAir: false })).summary
  const landSea = computeAccessibility(network, accessibilityRequest(480, { allowedModes: ['land', 'sea'] })).summary
  assert.deepEqual(landSea, legacyOff)
})

test('enabling every mode reproduces the v1 air-inclusive baseline and leaves the v1 air-excluded result untouched', () => {
  const network = loadFixture()

  const airInclusive = computeAccessibility(network, accessibilityRequest(480, { includeEstimatedAir: true })).summary
  const explicitAll = computeAccessibility(
    network,
    accessibilityRequest(480, { allowedModes: ['land', 'sea', 'air'], disabledRouteIds: [], disabledServiceIds: [] }),
  ).summary
  assert.deepEqual(explicitAll, airInclusive)
  assert.equal(explicitAll.populationReachable, 214659)
  assert.equal(explicitAll.reachableVerifiedPopulation, 206907)
  assert.equal(explicitAll.reachableEstimatedPopulation, 7752)

  const baseJourney = getJourney(network, journeyRequest(DHARAVANDHOO, 540, 'health_hospital', { includeEstimatedAir: false }))
  assert.equal(baseJourney.arrivalMinute, 934)
  const allModesJourney = getJourney(network, journeyRequest(DHARAVANDHOO, 540, 'health_hospital', { allowedModes: ['land', 'sea', 'air'] }))
  assert.equal(allModesJourney.arrivalMinute, 822)
  assert.equal(allModesJourney.usesEstimatedAir, true)
})

test('disabledRouteIds removes only that route and can never improve an earliest arrival', () => {
  const network = loadFixture()

  const reverseDisabled = getJourney(network, journeyRequest(DHARAVANDHOO, 540, 'health_hospital', { disabledRouteIds: [REVERSE_FERRY] }))
  assert.equal(reverseDisabled.arrivalMinute, 934)
  assert.equal(reverseDisabled.legs[1]?.serviceId, FERRY_259)

  const routeDisabled = planJourneyWithStatus(network, journeyRequest(DHARAVANDHOO, 540, 'health_hospital', { disabledRouteIds: ['259'] }))
  assert.equal(routeDisabled.status, 'not_reachable')
  assert.equal(routeDisabled.journey, null)

  const exactDisabled = planJourneyWithStatus(network, journeyRequest(DHARAVANDHOO, 540, 'health_hospital', { disabledServiceIds: [FERRY_259] }))
  assert.equal(exactDisabled.status, 'not_reachable')

  const baseline = getJourney(network, journeyRequest(DHARAVANDHOO, 540, 'health_hospital'))
  for (const request of [
    journeyRequest(DHARAVANDHOO, 540, 'health_hospital', { disabledRouteIds: ['259'] }),
    journeyRequest(DHARAVANDHOO, 540, 'health_hospital', { disabledServiceIds: [FERRY_259] }),
  ]) {
    const plan = planJourneyWithStatus(network, request)
    assert.ok(plan.journey === null || plan.journey.arrivalMinute >= baseline.arrivalMinute, 'removing a route cannot improve the arrival')
  }

  const airBaseline = getJourney(network, journeyRequest(DHARAVANDHOO, 540, 'health_hospital', { includeEstimatedAir: true }))
  const airWithRouteDisabled = getJourney(
    network,
    journeyRequest(DHARAVANDHOO, 540, 'health_hospital', { includeEstimatedAir: true, disabledRouteIds: ['259'] }),
  )
  assert.ok(airWithRouteDisabled.arrivalMinute >= airBaseline.arrivalMinute, 'with air enabled, removing the ferry must not improve the arrival')
})

test('an added sea link is routed with ferry buffers and reported as a sea leg', () => {
  const network = loadFixture()
  const withSea = applyScenario(network, { addedServices: [scenarioSeaLink()] })
  assert.equal(network.services.length, 6, 'the base network must not be mutated')
  assert.equal(withSea.services.length, 7)

  const journey = getJourney(withSea, journeyRequest(DHARAVANDHOO, 540, 'health_hospital', { allowedModes: ['sea'] }))
  assert.equal(journey.arrivalMinute, 617)
  assert.equal(journey.elapsedMinutes, 77)
  assert.equal(journey.waitMinutes, 15)
  assert.equal(journey.rideMinutes, 60)
  assert.equal(journey.transferMinutes, 2)
  assert.equal(journey.transfers, 0)
  assert.equal(journey.serviceConfidence, 'estimated')
  assert.equal(journey.usesEstimatedAir, false)
  assert.deepEqual(journey.modes, ['sea'])
  assert.equal(journey.legs.length, 1)
  const leg = journey.legs[0]
  assert.ok(leg !== undefined)
  assert.equal(leg.kind, 'sea')
  assert.equal(leg.mode, 'sea')
  assert.equal(leg.serviceId, ADDED_SEA_SERVICE_ID)
  assert.equal(leg.waitMinutes, 15)
  assert.equal(leg.rideMinutes, 60)
  assertLedger(journey)

  // A 15-minute ferry boarding buffer: 541 + 15 = 556 is after the only departure at 555.
  assert.equal(planJourney(withSea, journeyRequest(DHARAVANDHOO, 541, 'health_hospital', { allowedModes: ['sea'] })), null)

  const disabled = planJourneyWithStatus(
    withSea,
    journeyRequest(DHARAVANDHOO, 540, 'health_hospital', { allowedModes: ['sea'], disabledRouteIds: [ADDED_SEA_ROUTE_ID] }),
  )
  assert.equal(disabled.status, 'no_origin_access')
})

test('ferry then sea shares one coarse ride mode: no mode-change penalty, one transfer', () => {
  const network = loadFixture()
  const seaToMaale = scenarioSeaLink({
    id: 'scenario:sea:eydhafushi-maale',
    routeId: 'scenario:sea:test',
    fromNode: `island:${EYDHAFUSHI}`,
    toNode: `island:${MAALE}`,
    departures: [960],
    blockMinutes: 120,
    operatingWindow: { start: 900, end: 1000 },
  })
  const withSea = applyScenario(network, { addedServices: [seaToMaale] })
  const journey = getJourney(withSea, journeyRequest(DHARAVANDHOO, 540, 'health_regional_tertiary'))

  assert.equal(journey.destinationIslandId, MAALE)
  assert.equal(journey.arrivalMinute, 1082)
  assert.equal(journey.elapsedMinutes, 542)
  assert.equal(journey.waitMinutes, 384)
  assert.equal(journey.rideMinutes, 145)
  assert.equal(journey.accessMinutes, 4)
  assert.equal(journey.transferMinutes, 9, 'ferry alight 2 + extra boarding 5 + final sea alight 2')
  assert.equal(journey.transfers, 1)
  assert.deepEqual(journey.modes, ['walk', 'ferry', 'sea'])
  assert.equal(journey.serviceConfidence, 'estimated')
  assert.equal(journey.usesEstimatedAir, false)
  assert.equal(journey.legs.length, 4)
  assert.equal(journey.legs[3]?.kind, 'sea')
  assertLedger(journey)
})

test('an added island-to-island road link is usable only when land is enabled', () => {
  const network = loadFixture()
  const roadLink = {
    from: `island:${DHARAVANDHOO}`,
    to: `island:${EYDHAFUSHI}`,
    mode: 'road' as const,
    minutes: 40,
    confidence: 'assumption' as const,
    basis: 'user road link',
    assumed: true,
  }
  const withRoad = applyScenario(network, { addedAccessEdges: [roadLink] })
  assert.equal(network.accessEdges.length, 7)
  assert.equal(withRoad.accessEdges.length, 8)

  const journey = getJourney(withRoad, journeyRequest(DHARAVANDHOO, 540, 'health_hospital', { allowedModes: ['land'] }))
  assert.equal(journey.arrivalMinute, 580)
  assert.equal(journey.elapsedMinutes, 40)
  assert.equal(journey.accessMinutes, 40)
  assert.equal(journey.legs.length, 1)
  const leg = journey.legs[0]
  assert.ok(leg !== undefined)
  assert.equal(leg.kind, 'road')
  assert.equal(leg.fromNode, `island:${DHARAVANDHOO}`)
  assert.equal(leg.toNode, `island:${EYDHAFUSHI}`)
  assert.equal(leg.basis, 'user road link')
  assertLedger(journey)

  const seaOnly = planJourneyWithStatus(withRoad, journeyRequest(DHARAVANDHOO, 540, 'health_hospital', { allowedModes: ['sea'] }))
  assert.equal(seaOnly.status, 'no_origin_access')
})

test('an added facility changes which island is the destination', () => {
  const network = loadFixture()
  const facility = scenarioFacility()
  const withFacility = applyScenario(network, { addedFacilities: [facility] })
  assert.equal(network.facilities.length, 5, 'the base network must not be mutated')
  assert.equal(withFacility.facilities.length, 6)

  const journey = getJourney(withFacility, journeyRequest(DHARAVANDHOO, 540, 'health_hospital'))
  assert.equal(journey.destinationIslandId, MAALHOS)
  assert.equal(journey.destinationIslandName, 'Maalhos')
  assert.deepEqual(journey.destinationFacilityIds, [facility.id])
  assert.equal(journey.arrivalMinute, 919)
  assert.equal(journey.elapsedMinutes, 379)
  assert.equal(journey.rideMinutes, 10)
  assert.equal(journey.legs.filter((leg) => leg.kind === 'ferry').length, 1)
  assertLedger(journey)

  const plan = computeAccessibility(withFacility, accessibilityRequest(480, { includeEstimatedAir: false })).perOrigin[DHARAVANDHOO]
  assert.ok(plan?.journey !== null && plan !== undefined)
  assert.equal(plan.journey.destinationIslandId, MAALHOS)
  assert.equal(plan.journey.arrivalMinute, 919)
})

test('intervention categories route like any other destination category', () => {
  const network = loadFixture()
  const category: CategoryDefinition = {
    id: 'service:lab_basic',
    label: 'Basic laboratory',
    definition: 'Fixture intervention probe',
    facilityCount: 1,
    islandCount: 1,
    confidenceNote: 'fixture',
    kind: 'intervention',
    group: 'Diagnostics',
    source: 'fixture',
  }
  const lab: Facility = scenarioFacility({
    id: 'scenario:facility:hulhumale-lab',
    name: 'Hulhumaale Laboratory',
    islandId: HULHUMALE,
    categories: ['service:lab_basic'],
    serviceCategories: ['service:lab_basic'],
    serviceEvidence: [{ category: 'service:lab_basic', confidence: 'medium', source: 'fixture' }],
  })
  network.categories.push(category)
  network.facilities.push(lab)

  const result = computeAccessibility(network, { departureMinute: 480, category: 'service:lab_basic', includeEstimatedAir: false })
  assert.equal(result.summary.populationReachable, 210509)
  assert.equal(result.summary.originsReachable, 4)
  assert.equal(result.summary.within60, 210509)
  assert.equal(result.summary.within240, 210509)
  assert.equal(result.summary.noOriginAccessPopulation, 10)

  const maale = result.perOrigin[MAALE]
  assert.ok(maale?.journey !== null && maale !== undefined)
  assert.equal(maale.journey.destinationIslandId, HULHUMALE)
  assert.equal(maale.journey.arrivalMinute, 505)
  assert.equal(maale.journey.legs.filter((leg) => leg.kind === 'road').length, 2)
  assertLedger(maale.journey)
})

test('the selection is part of the graph cache key: results do not depend on call order', () => {
  const network = loadFixture()

  const airFirst = computeAccessibility(network, accessibilityRequest(480, { allowedModes: ['air'] })).summary
  const land = computeAccessibility(network, accessibilityRequest(480, { allowedModes: ['land'] })).summary
  const airAgain = computeAccessibility(network, accessibilityRequest(480, { allowedModes: ['air'] })).summary
  assert.deepEqual(airAgain, airFirst)
  assert.equal(land.populationReachable, 206335)
  assert.equal(airFirst.populationReachable, 139819)

  const ferryOff = getJourney(network, journeyRequest(DHARAVANDHOO, 540, 'health_hospital', { includeEstimatedAir: false }))
  const air = getJourney(network, journeyRequest(DHARAVANDHOO, 540, 'health_hospital', { includeEstimatedAir: true }))
  const ferryOffAgain = getJourney(network, journeyRequest(DHARAVANDHOO, 540, 'health_hospital', { includeEstimatedAir: false }))
  assert.equal(air.arrivalMinute, 822)
  assert.equal(ferryOffAgain.arrivalMinute, ferryOff.arrivalMinute)
  assert.equal(ferryOffAgain.legs[1]?.serviceId, FERRY_259)
})
