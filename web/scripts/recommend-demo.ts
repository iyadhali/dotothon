/// <reference types="node" />
/**
 * Print greedy facility-siting recommendations for a category on the prepared network.
 *
 *   node --experimental-strip-types web/scripts/recommend-demo.ts [category] [thresholdMin] [HH:MM]
 */
import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import path from 'node:path'

import type { MultimodalNetwork } from '../shared/routing/types'
import { buildTravelMatrix, recommendSites } from '../shared/routing/recommend.ts'

const DATA = path.join(fileURLToPath(new URL('..', import.meta.url)), 'public', 'data')
const network = JSON.parse(readFileSync(path.join(DATA, 'multimodal.json'), 'utf8')) as MultimodalNetwork
const category = process.argv[2] ?? 'health_hospital'
const threshold = Number(process.argv[3] ?? 120)
const [hh, mm] = (process.argv[4] ?? '08:00').split(':').map(Number)

const started = performance.now()
const matrix = buildTravelMatrix(network, { departureMinute: hh * 60 + mm, maxJourneyMinutes: threshold })
const built = performance.now()
const result = recommendSites(network, matrix, { category, thresholdMinutes: threshold, picks: 5 })
console.log(`matrix ${Math.round(built - started)} ms, ranking ${Math.round(performance.now() - built)} ms`)
console.log(
  `${category} within ${threshold} min: ${result.coveredBefore.toLocaleString()} of ${result.populationTotal.toLocaleString()} now`,
)
for (const site of result.sites) {
  console.log(
    `  #${site.rank} ${site.name} (${site.atollName}): +${site.gainPopulation.toLocaleString()} residents, ` +
      `${site.newlyCoveredIslandIds.length} islands → ${site.coveredAfter.toLocaleString()}`,
  )
}
