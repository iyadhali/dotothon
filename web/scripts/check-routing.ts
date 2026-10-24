/// <reference types="node" />
/**
 * Routing smoke check.
 *
 *   node --experimental-strip-types web/scripts/check-routing.ts
 *   node --experimental-strip-types web/scripts/check-routing.ts --fixture
 *   node --experimental-strip-types web/scripts/check-routing.ts path/to/multimodal.json
 *
 * Loads `web/public/data/multimodal.json` (the data-pipeline output), prints national
 * accessibility for health_hospital at 08:00 with and without the estimated air layer,
 * and exercises the RTL route Z2R18 pilot: baseline journey from Dharavandhoo, add a
 * shifted trip, cancel a service, delay a service. Exits non-zero when a check fails.
 *
 * When the network file is missing the script prints a clear SKIP and exits 0, so it can
 * run in CI before the data pipeline has produced output.
 */

import { existsSync, readFileSync } from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

import type { Facility, Journey, MultimodalNetwork, TimetabledService, TravelMode } from '../shared/routing/types'
import {
  applyScenario,
  computeAccessibility,
  createServiceFromPattern,
  getRoutingDefaults,
  planJourneyWithStatus,
} from '../shared/routing/router.ts'

const WEB_ROOT = fileURLToPath(new URL('..', import.meta.url))
const DEFAULT_NETWORK_PATH = path.join(WEB_ROOT, 'public', 'data', 'multimodal.json')
const FIXTURE_NETWORK_PATH = path.join(WEB_ROOT, 'shared', 'routing', 'fixtures', 'sample-network.json')

let failures = 0

function check(label: string, condition: boolean, detail?: string): void {
  if (condition) {
    console.log(`  PASS  ${label}`)
  } else {
    failures += 1
    console.error(`  FAIL  ${label}${detail ? ` — ${detail}` : ''}`)
  }
}

function close(actual: number, expected: number, tolerance = 1e-6): boolean {
  return Math.abs(actual - expected) <= tolerance
}

function number(value: number): string {
  return value.toLocaleString('en-US')
}

function percent(value: number): string {
  return `${(value * 100).toFixed(3)}%`
}

function clock(minutes: number): string {
  if (!Number.isFinite(minutes)) return '—'
  const day = Math.floor(minutes / 1440)
  const minuteOfDay = ((minutes % 1440) + 1440) % 1440
  const hours = Math.floor(minuteOfDay / 60)
  const mins = minuteOfDay % 60
  const suffix = day > 0 ? ` (+${day}d)` : ''
  return `${String(hours).padStart(2, '0')}:${String(mins).padStart(2, '0')}${suffix}`
}

/** Re-derive every ledger invariant from the legs; a router bug must fail the CLI. */
function validateJourney(label: string, journey: Journey): void {
  const totals = journey.waitMinutes + journey.rideMinutes + journey.accessMinutes + journey.transferMinutes
  check(`${label}: totals sum to elapsed`, close(totals, journey.elapsedMinutes), `totals=${totals} elapsed=${journey.elapsedMinutes}`)
  check(
    `${label}: arrival = departure + elapsed`,
    close(journey.departureMinute + journey.elapsedMinutes, journey.arrivalMinute),
    `departure=${journey.departureMinute} elapsed=${journey.elapsedMinutes} arrival=${journey.arrivalMinute}`,
  )
  check(`${label}: elapsed is not negative`, journey.elapsedMinutes >= 0)
  check(`${label}: every minute is finite`, Number.isFinite(journey.elapsedMinutes) && Number.isFinite(journey.arrivalMinute))

  const transitLegs = journey.legs.filter((leg) => leg.kind === 'ferry' || leg.kind === 'air' || leg.kind === 'sea')
  check(`${label}: transfers = transit legs - 1`, journey.transfers === Math.max(0, transitLegs.length - 1), `transfers=${journey.transfers} transitLegs=${transitLegs.length}`)
  const expectedConfidence = transitLegs.length === 0 || transitLegs.every((leg) => leg.serviceConfidence === 'verified') ? 'verified' : 'estimated'
  check(`${label}: serviceConfidence follows legs`, journey.serviceConfidence === expectedConfidence, `actual=${journey.serviceConfidence} expected=${expectedConfidence}`)
  check(`${label}: usesEstimatedAir follows legs`, journey.usesEstimatedAir === transitLegs.some((leg) => leg.kind === 'air'))

  if (journey.legs.length === 0) {
    check(`${label}: zero-leg journey has zero elapsed`, journey.elapsedMinutes === 0)
    return
  }
  const first = journey.legs[0]!
  const last = journey.legs[journey.legs.length - 1]!
  // A journey may board a service straight from the origin island (e.g. an island-to-island boat),
  // so the first leg can start after the departure time; that initial wait counts as a gap below.
  const boardsAtOrigin = first.kind !== 'access' && first.kind !== 'road'
  check(
    `${label}: first leg starts at departure`,
    boardsAtOrigin ? first.departureMinute >= journey.departureMinute - 1e-6 : close(first.departureMinute, journey.departureMinute),
    `leg=${first.departureMinute} journey=${journey.departureMinute}`,
  )
  // Alighting is reported on the journey total, so a final transit leg ends before the journey.
  const finalAlight = last.kind === 'ferry' || last.kind === 'sea' ? 2 : last.kind === 'air' ? 15 : 0
  check(
    `${label}: last leg plus final alighting ends at arrival`,
    close(last.arrivalMinute + finalAlight, journey.arrivalMinute),
    `leg=${last.arrivalMinute}+alight${finalAlight} journey=${journey.arrivalMinute}`,
  )
  let gapSum = boardsAtOrigin ? first.departureMinute - journey.departureMinute : 0
  for (let index = 0; index < journey.legs.length; index += 1) {
    const leg = journey.legs[index]!
    check(`${label}: leg ${index} ride spans departure→arrival`, close(leg.departureMinute + leg.rideMinutes, leg.arrivalMinute), `${leg.departureMinute}+${leg.rideMinutes}!=${leg.arrivalMinute}`)
    check(`${label}: leg ${index} wait is not negative`, leg.waitMinutes >= -1e-6, `wait=${leg.waitMinutes}`)
    if (index > 0) {
      const previous = journey.legs[index - 1]!
      const gap = leg.departureMinute - previous.arrivalMinute
      check(`${label}: leg ${index} does not depart before the previous arrival`, gap >= -1e-6, `gap=${gap}`)
      gapSum += gap
    }
  }
  check(
    `${label}: leg gaps sum to wait + transfer`,
    // The final alighting buffer is part of transferMinutes but lies after the last leg, not
    // between legs; it only appears when the journey ends on a transit leg at the island.
    close(gapSum, journey.waitMinutes + journey.transferMinutes - (last.toNode.startsWith('island:') ? finalAlight : 0)),
    `gaps=${gapSum} wait+transfer=${journey.waitMinutes + journey.transferMinutes}`,
  )
}

function describeJourney(journey: Journey | null): string {
  if (!journey) return 'no journey'
  return `${journey.originIslandName} ${clock(journey.departureMinute)} → ${journey.destinationIslandName} ${clock(journey.arrivalMinute)} (${journey.elapsedMinutes} min, ${journey.legs.length} legs, ${journey.serviceConfidence})`
}

function isTimetabled(service: { kind: string }): service is TimetabledService {
  return service.kind === 'timetabled'
}

function normaliseRouteCode(value: string): string {
  return value.toUpperCase().replace(/[^A-Z0-9]/g, '')
}

function stopIslandMap(network: MultimodalNetwork): Map<string, string> {
  return new Map(network.stops.map((stop) => [stop.id, stop.islandId]))
}

function categoriesOnIsland(facilities: Facility[], islandId: string): string[] {
  const categories = new Set<string>()
  for (const facility of facilities) {
    if (facility.islandId !== islandId) continue
    for (const category of facility.categories) categories.add(category)
  }
  return [...categories]
}

interface RoutePatternChoice {
  service: TimetabledService
  stops: TimetabledService['stops']
  originIslandId: string
  downstreamIslandIds: string[]
  categoryId: string
}

function choosePilotPattern(network: MultimodalNetwork): RoutePatternChoice | null {
  const timetabled = network.services.filter(isTimetabled)
  const routeMatches = timetabled.filter((service) => normaliseRouteCode(service.routeCode) === 'Z2R18' || normaliseRouteCode(service.routeId) === 'Z2R18')
  if (routeMatches.length === 0) return null

  const islandById = new Map(network.islands.map((island) => [island.id, island]))
  const stopIsland = stopIslandMap(network)
  const patterns = routeMatches
    .map((service) => {
      const stops = service.stops.slice().sort((a, b) => a.sequence - b.sequence)
      return { service, stops }
    })
    .filter((pattern) => pattern.stops.length > 0)
  if (patterns.length === 0) return null

  const islandForStop = (stopId: string): string | null => stopIsland.get(stopId) ?? null
  const isDharavandhoo = (pattern: { stops: TimetabledService['stops'] }): boolean => {
    const islandId = islandForStop(pattern.stops[0]!.stopId)
    if (!islandId) return false
    const island = islandById.get(islandId)
    return island?.airportIata === 'DRV' || /dharavandhoo/i.test(island?.name ?? '')
  }
  const chosen = patterns.find(isDharavandhoo) ?? patterns[0]!
  const originIslandId = islandForStop(chosen.stops[0]!.stopId)
  if (!originIslandId) return null
  const downstreamIslandIds = [...new Set(chosen.stops.slice(1).map((stop) => islandForStop(stop.stopId)).filter((value): value is string => value !== null))]

  // Prefer the most common category that is served downstream but not already on the origin,
  // so the pilot exercises a real trip instead of the same-island shortcut.
  const originCategories = new Set(categoriesOnIsland(network.facilities, originIslandId))
  const downstreamCategories = new Set<string>()
  for (const islandId of downstreamIslandIds) {
    for (const category of categoriesOnIsland(network.facilities, islandId)) downstreamCategories.add(category)
  }
  const ordered = network.categories.slice().sort((a, b) => b.facilityCount - a.facilityCount || a.id.localeCompare(b.id))
  const category =
    ordered.find((definition) => downstreamCategories.has(definition.id) && !originCategories.has(definition.id)) ??
    ordered.find((definition) => downstreamCategories.has(definition.id)) ??
    ordered[0]
  if (!category) return null

  return { service: chosen.service, stops: chosen.stops, originIslandId, downstreamIslandIds, categoryId: category.id }
}

async function main(): Promise<void> {
  const args = process.argv.slice(2)
  const fixtureMode = args.includes('--fixture')
  const explicitPath = args.find((argument) => !argument.startsWith('--'))
  const networkPath = explicitPath ? path.resolve(process.cwd(), explicitPath) : fixtureMode ? FIXTURE_NETWORK_PATH : DEFAULT_NETWORK_PATH
  const displayPath = path.relative(WEB_ROOT, networkPath) || networkPath

  console.log('Multimodal routing check')
  console.log(`  network: ${displayPath}`)
  console.log('')

  if (!existsSync(networkPath)) {
    console.log(`SKIP: network file not found: ${displayPath}`)
    console.log('      Run the multimodal data pipeline first (MULTIMODAL_IMPLEMENTATION.md §3),')
    console.log('      pass an explicit path, or run with --fixture for the bundled sample network.')
    return
  }

  let network: MultimodalNetwork
  try {
    network = JSON.parse(readFileSync(networkPath, 'utf8')) as MultimodalNetwork
  } catch (error) {
    failures += 1
    console.error(`  FAIL  could not read/parse network JSON: ${error instanceof Error ? error.message : String(error)}`)
    return
  }

  const defaults = getRoutingDefaults(network)
  const timetabledCount = network.services.filter(isTimetabled).length
  console.log('Network')
  console.log(`  islands ${number(network.islands.length)} · origins ${number(network.islands.filter((island) => island.isOrigin).length)} · stops ${number(network.stops.length)} · airports ${number(network.airports.length)}`)
  console.log(`  services: ${number(timetabledCount)} timetabled · ${number(network.services.length - timetabledCount)} frequency · facilities ${number(network.facilities.length)} · categories ${number(network.categories.length)}`)
  const interventionCategories = network.categories.filter((definition) => definition.kind === 'intervention')
  console.log(
    `  intervention categories: ${number(interventionCategories.length)}${interventionCategories.length > 0 ? ` · ${interventionCategories.slice(0, 8).map((definition) => definition.id).join(', ')}${interventionCategories.length > 8 ? ', …' : ''}` : ''}`,
  )
  check(
    'intervention categories use service: ids',
    interventionCategories.every((definition) => definition.id.startsWith('service:')),
    interventionCategories.map((definition) => definition.id).join(', '),
  )
  const computedOriginsPopulation = network.islands.filter((island) => island.isOrigin).reduce((sum, island) => sum + island.population, 0)
  console.log(`  population: origins ${number(computedOriginsPopulation)} (computed from islands[].population) · meta ${number(network.meta.population.origins)} · originCount ${number(network.meta.population.originCount)}`)
  console.log(`  buffers: ferry board ${defaults.ferryBoardMinutes} / alight ${defaults.ferryAlightMinutes} · air board ${defaults.airBoardMinutes} (MLE ${defaults.airBoardMinutesMle}) / alight ${defaults.airAlightMinutes} · transfer ${defaults.transferPenaltyMinutes} · extra board ${defaults.additionalBoardPenaltyMinutes}`)
  console.log('')

  check('meta originCount matches islands with isOrigin', network.meta.population.originCount === network.islands.filter((island) => island.isOrigin).length, `${network.meta.population.originCount}`)
  if (network.meta.population.origins !== computedOriginsPopulation) {
    console.log(`  NOTE  meta.population.origins (${number(network.meta.population.origins)}) differs from the computed island sum (${number(computedOriginsPopulation)}); the router uses the computed sum.`)
  }

  // ---------------------------------------------------------------------------------------------
  // National accessibility, 08:00, health_hospital, air off then on
  // ---------------------------------------------------------------------------------------------
  const departureMinute = 8 * 60
  const category = 'health_hospital'
  console.log('')
  console.log(`National accessibility — ${category} @ ${clock(departureMinute)}`)

  const results = new Map<boolean, ReturnType<typeof computeAccessibility>>()
  for (const includeEstimatedAir of [false, true]) {
    const result = computeAccessibility(network, { departureMinute, category, includeEstimatedAir })
    results.set(includeEstimatedAir, result)
    const summary = result.summary
    console.log(`  includeEstimatedAir=${includeEstimatedAir ? 'ON' : 'OFF'}`)
    console.log(`    origins: ${number(summary.originsReachable)} reachable · ${number(summary.originsUnreachable)} unreachable · ${number(summary.originsNoAccess)} no origin access`)
    console.log(`    population: ${number(summary.populationReachable)} / ${number(summary.populationTotal)} reachable · coverage ${percent(summary.coverage)}`)
    console.log(`    within 60/120/240 min: ${number(summary.within60)} / ${number(summary.within120)} / ${number(summary.within240)}`)
    console.log(`    unreachable ${number(summary.unreachablePopulation)} · no origin access ${number(summary.noOriginAccessPopulation)} · no destination ${number(summary.noDestinationPopulation)}`)
    console.log(`    verified ${number(summary.reachableVerifiedPopulation)} · estimated ${number(summary.reachableEstimatedPopulation)}`)

    check(`[air=${includeEstimatedAir ? 'on' : 'off'}] reachable ≤ total population`, summary.populationReachable <= summary.populationTotal)
    check(`[air=${includeEstimatedAir ? 'on' : 'off'}] within60 ≤ within120`, summary.within60 <= summary.within120)
    check(`[air=${includeEstimatedAir ? 'on' : 'off'}] within120 ≤ within240`, summary.within120 <= summary.within240)
    check(`[air=${includeEstimatedAir ? 'on' : 'off'}] within240 ≤ reachable population`, summary.within240 <= summary.populationReachable)
    check(`[air=${includeEstimatedAir ? 'on' : 'off'}] verified + estimated = reachable population`, summary.reachableVerifiedPopulation + summary.reachableEstimatedPopulation === summary.populationReachable)
    check(`[air=${includeEstimatedAir ? 'on' : 'off'}] population partitions`, summary.populationReachable + summary.unreachablePopulation + summary.noOriginAccessPopulation + summary.noDestinationPopulation <= summary.populationTotal)
    check(
      `[air=${includeEstimatedAir ? 'on' : 'off'}] noDestination counters agree`,
      Object.values(result.perOrigin).filter((origin) => origin.status === 'no_destination').length === summary.originsNoDestination,
    )
    const noAccessOrigins = Object.values(result.perOrigin).filter((origin) => origin.status === 'no_origin_access')
    if (noAccessOrigins.length > 0) {
      const names = noAccessOrigins.slice(0, 12).map((origin) => network.islands.find((island) => island.id === origin.originIslandId)?.name ?? origin.originIslandId)
      console.log(`    no-origin-access (${noAccessOrigins.length}): ${names.join(', ')}${noAccessOrigins.length > 12 ? ', …' : ''}`)
    }
    const unreachableOrigins = Object.values(result.perOrigin).filter((origin) => origin.status === 'not_reachable')
    if (unreachableOrigins.length > 0) {
      const names = unreachableOrigins.slice(0, 12).map((origin) => network.islands.find((island) => island.id === origin.originIslandId)?.name ?? origin.originIslandId)
      console.log(`    unreachable (${unreachableOrigins.length}): ${names.join(', ')}${unreachableOrigins.length > 12 ? ', …' : ''}`)
    }
    check(
      `[air=${includeEstimatedAir ? 'on' : 'off'}] coverage = reachable / total`,
      summary.populationTotal === 0 ? summary.coverage === 0 : close(summary.coverage, summary.populationReachable / summary.populationTotal, 1e-12),
    )
    check(
      `[air=${includeEstimatedAir ? 'on' : 'off'}] per-origin count matches summary`,
      Object.values(result.perOrigin).filter((origin) => origin.status === 'reachable').length === summary.originsReachable &&
        Object.values(result.perOrigin).filter((origin) => origin.status === 'not_reachable').length === summary.originsUnreachable &&
        Object.values(result.perOrigin).filter((origin) => origin.status === 'no_origin_access').length === summary.originsNoAccess &&
        Object.values(result.perOrigin).filter((origin) => origin.status === 'no_destination').length === summary.originsNoDestination,
    )

    let originFailures = 0
    for (const origin of Object.values(result.perOrigin)) {
      if (!origin.journey) continue
      const totals = origin.journey.waitMinutes + origin.journey.rideMinutes + origin.journey.accessMinutes + origin.journey.transferMinutes
      const consistent =
        close(totals, origin.journey.elapsedMinutes) &&
        close(origin.journey.departureMinute + origin.journey.elapsedMinutes, origin.journey.arrivalMinute) &&
        origin.journey.originIslandId === origin.originIslandId &&
        origin.journey.category === category
      if (!consistent) {
        originFailures += 1
        if (originFailures <= 3) console.error(`    leg ledger mismatch for ${origin.originIslandId}: ${describeJourney(origin.journey)} totals=${totals}`)
      }
    }
    check(`[air=${includeEstimatedAir ? 'on' : 'off'}] all ${Object.keys(result.perOrigin).length} origin journeys have consistent ledgers`, originFailures === 0, `${originFailures} mismatches`)
  }

  const airOff = results.get(false)!
  const airOn = results.get(true)!
  check('estimated air layer cannot reduce reachable population', airOn.summary.populationReachable >= airOff.summary.populationReachable)
  check('estimated air layer cannot reduce within60 population', airOn.summary.within60 >= airOff.summary.within60)
  check('estimated air layer cannot reduce within120 population', airOn.summary.within120 >= airOff.summary.within120)
  check('estimated air layer cannot reduce within240 population', airOn.summary.within240 >= airOff.summary.within240)

  // Travel-mode presets (§10.1): the UI lets a user pick land / sea / air combinations.
  console.log('')
  console.log(`Mode presets — ${category} @ ${clock(departureMinute)}`)
  const modePresets: Array<{ label: string; allowedModes: TravelMode[] }> = [
    { label: 'land-only', allowedModes: ['land'] },
    { label: 'sea', allowedModes: ['sea'] },
    { label: 'air', allowedModes: ['air'] },
    { label: 'land+sea', allowedModes: ['land', 'sea'] },
    { label: 'multimodal', allowedModes: ['land', 'sea', 'air'] },
  ]
  const presetSummaries = new Map<string, ReturnType<typeof computeAccessibility>['summary']>()
  for (const preset of modePresets) {
    const summary = computeAccessibility(network, { departureMinute, category, allowedModes: preset.allowedModes }).summary
    presetSummaries.set(preset.label, summary)
    console.log(
      `  ${preset.label.padEnd(9)} origins ${number(summary.originsReachable)} reachable · ${number(summary.originsUnreachable)} unreachable · ${number(summary.originsNoAccess)} no access · population ${number(summary.populationReachable)} (${percent(summary.coverage)}) · within 60/120/240 ${number(summary.within60)} / ${number(summary.within120)} / ${number(summary.within240)} · verified ${number(summary.reachableVerifiedPopulation)} · estimated ${number(summary.reachableEstimatedPopulation)}`,
    )
    check(
      `[modes=${preset.label}] population partitions`,
      summary.populationReachable + summary.unreachablePopulation + summary.noOriginAccessPopulation + summary.noDestinationPopulation === summary.populationTotal,
    )
    check(
      `[modes=${preset.label}] verified + estimated = reachable population`,
      summary.reachableVerifiedPopulation + summary.reachableEstimatedPopulation === summary.populationReachable,
    )
  }
  check('mode preset "multimodal" matches the air-inclusive baseline', JSON.stringify(presetSummaries.get('multimodal')) === JSON.stringify(airOn.summary))
  check('mode preset "land+sea" matches the air-excluded baseline', JSON.stringify(presetSummaries.get('land+sea')) === JSON.stringify(airOff.summary))

  // The real file happens to list air services before ferry services. Nothing in the router may
  // depend on that: reversing the service array is a cheap order-independence probe.
  const reorderedNetwork: MultimodalNetwork = { ...network, services: [...network.services].reverse() }
  for (const includeEstimatedAir of [false, true]) {
    const reordered = computeAccessibility(reorderedNetwork, { departureMinute, category, includeEstimatedAir }).summary
    const original = results.get(includeEstimatedAir)!.summary
    check(
      `[air=${includeEstimatedAir ? 'on' : 'off'}] service ordering does not change the accessibility summary`,
      JSON.stringify(reordered) === JSON.stringify(original),
    )
  }

  // ---------------------------------------------------------------------------------------------
  // Route Z2R18 pilot (Dharavandhoo origin)
  // ---------------------------------------------------------------------------------------------
  console.log('')
  console.log('Pilot — route Z2R18')
  const pilot = choosePilotPattern(network)
  if (!pilot) {
    console.log('  SKIP  no timetabled service with routeCode/routeId Z2R18 in this network.')
  } else {
    const selectedPattern = pilot
    const firstStop = selectedPattern.stops[0]!
    const firstDeparture = firstStop.departure
    const originIsland = network.islands.find((island) => island.id === selectedPattern.originIslandId)
    console.log(`  pattern ${selectedPattern.service.id} (${selectedPattern.service.routeCode}) · ${selectedPattern.stops.length} stops · first departure ${clock(firstDeparture)}`)
    console.log(`  origin ${originIsland?.name ?? selectedPattern.originIslandId} · category ${selectedPattern.categoryId}`)

    // Leave enough room for access + boarding buffer to reach the first departure.
    const baselineDeparture = Math.max(0, firstDeparture - 60)
    const request = {
      originIslandId: selectedPattern.originIslandId,
      departureMinute: baselineDeparture,
      category: selectedPattern.categoryId,
      includeEstimatedAir: false,
    }

    const baseline = planJourneyWithStatus(network, request)
    console.log(`  baseline (${clock(baselineDeparture)}): ${describeJourney(baseline.journey)} [${baseline.status}]`)
    check('pilot baseline is reachable', baseline.status === 'reachable' && baseline.journey !== null, baseline.status)
    if (baseline.journey) {
      validateJourney('pilot baseline', baseline.journey)
      check('pilot baseline catches the chosen route', baseline.journey.legs.some((leg) => leg.serviceId === selectedPattern.service.id), `legs=${baseline.journey.legs.map((leg) => leg.serviceId ?? leg.kind).join(',')}`)
      const baselineArrival = baseline.journey.arrivalMinute

      // Route filters (§10.1): removing the pilot route must never produce an earlier arrival.
      const routeDisabled = planJourneyWithStatus(network, { ...request, disabledRouteIds: [selectedPattern.service.routeId] })
      console.log(`  route ${selectedPattern.service.routeId} disabled: ${describeJourney(routeDisabled.journey)} [${routeDisabled.status}]`)
      check(
        'disabling the pilot route cannot improve the arrival',
        routeDisabled.journey === null || routeDisabled.journey.arrivalMinute >= baselineArrival,
        routeDisabled.journey ? `arrival=${routeDisabled.journey.arrivalMinute} baseline=${baselineArrival}` : 'no journey',
      )

      // Add: shift the same pattern earlier and confirm it is taken without worsening arrival.
      const addedFirstDeparture = Math.max(0, firstDeparture - 45)
      const added = createServiceFromPattern(network, selectedPattern.service.id, addedFirstDeparture)
      check('createServiceFromPattern shifts the first departure', added.stops[0]?.departure === addedFirstDeparture, `${added.stops[0]?.departure}`)
      check('createServiceFromPattern keeps the stop count', added.stops.length === selectedPattern.stops.length)
      let durationsPreserved = true
      for (let index = 1; index < added.stops.length; index += 1) {
        const original = selectedPattern.stops[index]!
        const shifted = added.stops[index]!
        const originalGap = original.departure - selectedPattern.stops[index - 1]!.departure
        const shiftedGap = shifted.departure - added.stops[index - 1]!.departure
        if (!close(shiftedGap, originalGap)) durationsPreserved = false
      }
      check('createServiceFromPattern keeps leg durations', durationsPreserved)
      check('createServiceFromPattern does not mutate the network', network.services.some((service) => service.id === selectedPattern.service.id && service.kind === 'timetabled' && service.stops[0]?.departure === firstStop.departure))

      const addRequest = { ...request, departureMinute: Math.max(0, addedFirstDeparture - 60) }
      const withAdded = planJourneyWithStatus(applyScenario(network, { addedTrips: [added] }), addRequest)
      console.log(`  add trip (${clock(addedFirstDeparture)}): ${describeJourney(withAdded.journey)} [${withAdded.status}]`)
      check('pilot add-trip journey is reachable', withAdded.status === 'reachable' && withAdded.journey !== null, withAdded.status)
      check(
        'pilot add trip does not worsen arrival',
        withAdded.journey !== null && withAdded.journey.arrivalMinute <= baselineArrival,
        withAdded.journey ? `arrival=${withAdded.journey.arrivalMinute} baseline=${baselineArrival}` : 'null',
      )
      if (withAdded.journey) {
        validateJourney('pilot add trip', withAdded.journey)
        check('pilot add trip uses the added service', withAdded.journey.legs.some((leg) => leg.serviceId === added.id))
      }

      // Cancel: the cancelled service must never produce an earlier arrival.
      const cancelled = planJourneyWithStatus(applyScenario(network, { cancelledServiceIds: [selectedPattern.service.id] }), request)
      console.log(`  cancel ${selectedPattern.service.id}: ${describeJourney(cancelled.journey)} [${cancelled.status}]`)
      check(
        'pilot cancel cannot improve arrival',
        cancelled.journey === null || cancelled.journey.arrivalMinute >= baselineArrival,
        cancelled.journey ? `arrival=${cancelled.journey.arrivalMinute} baseline=${baselineArrival}` : 'null',
      )
      if (cancelled.journey) validateJourney('pilot cancel', cancelled.journey)

      // Delay: +30 minutes on the chosen service must never produce an earlier arrival.
      const delayed = planJourneyWithStatus(applyScenario(network, { delayMinutesByServiceId: { [selectedPattern.service.id]: 30 } }), request)
      console.log(`  delay ${selectedPattern.service.id} +30: ${describeJourney(delayed.journey)} [${delayed.status}]`)
      check(
        'pilot delay cannot improve arrival',
        delayed.journey === null || delayed.journey.arrivalMinute >= baselineArrival,
        delayed.journey ? `arrival=${delayed.journey.arrivalMinute} baseline=${baselineArrival}` : 'null',
      )
      if (delayed.journey) validateJourney('pilot delay', delayed.journey)
    }
  }

  console.log('')
  if (failures > 0) {
    console.error(`FAILED: ${failures} check(s) failed.`)
    process.exitCode = 1
  } else {
    console.log('OK: all routing checks passed.')
  }
}

await main()
