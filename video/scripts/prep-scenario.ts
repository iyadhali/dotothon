/// <reference types="node" />
/**
 * Scenario data for clip 5, from the project's own siting engine (web/shared/routing/recommend.ts).
 *
 *   node --experimental-strip-types video/scripts/prep-scenario.ts [category] [thresholdMin] [HH:MM] [picks] [--exclude=Name,...] [--order=south-north]
 *
 * Writes video/src/data/scenario.json: which islands are within the threshold of an existing facility,
 * and, for each recommended site, which islands newly come within it.
 */
import {readFileSync, writeFileSync} from 'node:fs'
import {fileURLToPath} from 'node:url'
import path from 'node:path'

import type {MultimodalNetwork} from '../../web/shared/routing/types'
import {buildTravelMatrix, recommendSites} from '../../web/shared/routing/recommend.ts'

const ROOT = fileURLToPath(new URL('../..', import.meta.url))
const network = JSON.parse(
  readFileSync(path.join(ROOT, 'web', 'public', 'data', 'multimodal.json'), 'utf8'),
) as MultimodalNetwork

const positional = process.argv.slice(2).filter((arg) => !arg.startsWith('--'))
const category = positional[0] ?? 'education_grade_11_12'
const threshold = Number(positional[1] ?? 120)
const [hh, mm] = (positional[2] ?? '08:00').split(':').map(Number)
const picks = Number(positional[3] ?? 3)
// --exclude=Maafushi,Other : islands (by name) the siting engine may not pick.
const excludeNames = (process.argv.find((arg) => arg.startsWith('--exclude='))?.slice('--exclude='.length) ?? '')
  .split(',')
  .map((name) => name.trim().toLowerCase())
  .filter(Boolean)
const excludeIslandIds = network.islands.filter((i) => excludeNames.includes(i.name.toLowerCase())).map((i) => i.id)

const matrix = buildTravelMatrix(network, {departureMinute: hh * 60 + mm, maxJourneyMinutes: threshold})
const result = recommendSites(network, matrix, {category, thresholdMinutes: threshold, picks, excludeIslandIds})

const islandById = new Map(network.islands.map((i) => [i.id, i]))
const origins = network.islands.filter((i) => i.isOrigin && i.status === 'inhabited')
const facilityIslands = new Set(
  network.facilities.filter((f) => f.categories.includes(category)).map((f) => f.islandId),
)
const within = (o: string, s: string) => (matrix.get(o)?.get(s) ?? Infinity) <= threshold

const coveredBefore = origins.filter((o) => [...facilityIslands].some((s) => within(o.id, s))).map((o) => o.id)

// --order=south-north : show the chosen sites south -> north (smoother camera) and re-derive each
// site's marginal gain in that order. The union of covered islands, and the final total, are unchanged.
const populationOf = new Map(origins.map((o) => [o.id, o.population]))
const sumPopulation = (ids: string[]) => ids.reduce((sum, id) => sum + (populationOf.get(id) ?? 0), 0)
let orderedSites = result.sites
if (process.argv.includes('--order=south-north')) {
  const covered = new Set(coveredBefore)
  orderedSites = [...result.sites]
    .sort((a, b) => islandById.get(a.islandId)!.lat - islandById.get(b.islandId)!.lat)
    .map((site, i) => {
      const ids = origins.filter((o) => !covered.has(o.id) && within(o.id, site.islandId)).map((o) => o.id)
      ids.forEach((id) => covered.add(id))
      return {
        ...site,
        rank: i + 1,
        gainPopulation: sumPopulation(ids),
        newlyCoveredIslandIds: ids,
        coveredAfter: sumPopulation([...covered]),
      }
    })
}

const scenario = {
  category,
  thresholdMinutes: threshold,
  departure: `${String(hh).padStart(2, '0')}:${String(mm).padStart(2, '0')}`,
  populationTotal: result.populationTotal,
  coveredBeforePopulation: result.coveredBefore,
  coveredBefore,
  facilityIslands: [...facilityIslands]
    .filter((id) => islandById.has(id))
    .map((id) => ({id, lon: islandById.get(id)!.lon, lat: islandById.get(id)!.lat})),
  origins: origins.map((o) => ({id: o.id, name: o.name, lon: o.lon, lat: o.lat, pop: o.population})),
  sites: orderedSites.map((s) => ({
    rank: s.rank,
    id: s.islandId,
    name: s.name,
    atoll: s.atollName,
    lon: islandById.get(s.islandId)!.lon,
    lat: islandById.get(s.islandId)!.lat,
    gainPopulation: s.gainPopulation,
    newlyCovered: s.newlyCoveredIslandIds,
    coveredAfterPopulation: s.coveredAfter,
  })),
}

writeFileSync(
  path.join(ROOT, 'video', 'src', 'data', 'scenario.json'),
  JSON.stringify(scenario),
)
console.log({
  excluded: excludeIslandIds,
  category,
  threshold,
  total: scenario.populationTotal,
  before: scenario.coveredBeforePopulation,
  coveredIslandsBefore: coveredBefore.length,
  sites: scenario.sites.map((s) => `${s.rank} ${s.name} (${s.atoll}) +${s.gainPopulation} / ${s.newlyCovered.length} islands -> ${s.coveredAfterPopulation}`),
})
