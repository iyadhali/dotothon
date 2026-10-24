/// <reference types="node" />
/** Sanity check for the minimal map: journeys and route geometry for one island. */
import { readFileSync } from 'node:fs'
import type { MultimodalNetwork } from '../shared/routing/types'
import type { FareTable } from '../shared/routing/cost'
import { buildAccessReport } from '../shared/routing/nearby.ts'
import { journeyPaths, buildRoutePaths } from '../app/utils/routes.ts'

const network = JSON.parse(readFileSync('public/data/multimodal.json', 'utf8')) as MultimodalNetwork
const fares = JSON.parse(readFileSync('public/data/fares.json', 'utf8')) as FareTable
const name = process.argv[2] ?? 'Thuraakunu'
const origin = network.islands.find((i) => i.name === name)!
console.log('all routes:', buildRoutePaths(network).length)
for (const type of [['health_any', 'health_hospital', 'health_regional_tertiary'], ['education_school', 'education_grade_11_12', 'education_higher_ed']]) {
  const report = buildAccessReport(network, fares, { originIslandId: origin.id, departureMinute: 480, categories: type, limit: 1 })
  for (const row of report) {
    const d = row.destinations[0]
    if (!d) { console.log(row.category, row.status); continue }
    const paths = journeyPaths(network, d.journey)
    console.log(row.category, '→', d.journey.destinationIslandName, d.journey.elapsedMinutes, 'min, MVR', d.cost.knownMvr,
      '| paths', paths.map((p) => `${p.mode}:${p.points.length}pt`).join(' '))
  }
}
