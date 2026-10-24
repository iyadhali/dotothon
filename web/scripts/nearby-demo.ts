/// <reference types="node" />
/**
 * Print the island access report (nearest facilities, time, fare, same-day return) for
 * one origin island, using the prepared network and fare table.
 *
 *   node --experimental-strip-types web/scripts/nearby-demo.ts [islandName] [HH:MM]
 */
import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import path from 'node:path'

import type { MultimodalNetwork } from '../shared/routing/types'
import type { FareTable } from '../shared/routing/cost'
import { buildAccessReport } from '../shared/routing/nearby.ts'

const DATA = path.join(fileURLToPath(new URL('..', import.meta.url)), 'public', 'data')
const network = JSON.parse(readFileSync(path.join(DATA, 'multimodal.json'), 'utf8')) as MultimodalNetwork
const fares = JSON.parse(readFileSync(path.join(DATA, 'fares.json'), 'utf8')) as FareTable

const name = process.argv[2] ?? 'Maalhos'
const [hh, mm] = (process.argv[3] ?? '08:00').split(':').map(Number)
const origin = network.islands.find((island) => island.isOrigin && island.name.toLowerCase() === name.toLowerCase())
if (!origin) throw new Error(`No origin island named ${name}`)

const clock = (m: number) => `${String(Math.floor(m / 60) % 24).padStart(2, '0')}:${String(m % 60).padStart(2, '0')}${m >= 1440 ? ' (+1d)' : ''}`
const report = buildAccessReport(network, fares, {
  originIslandId: origin.id,
  departureMinute: hh * 60 + mm,
  categories: ['health_hospital', 'health_regional_tertiary', 'education_grade_11_12', 'service:dialysis'],
  overnightMvr: 950,
})
console.log(`${origin.name} (${origin.atollName}), depart ${clock(hh * 60 + mm)}`)
for (const row of report) {
  console.log(`\n${row.category}: ${row.status}`)
  for (const d of row.destinations) {
    const j = d.journey
    console.log(
      `  ${j.destinationIslandName.padEnd(16)} ${String(j.elapsedMinutes).padStart(4)} min  arrive ${clock(j.arrivalMinute)}  ` +
        `${j.modes.join('+') || 'on island'}  fare MVR ${d.cost.knownMvr}${d.cost.complete ? '' : '+?'} (${d.cost.confidence})  ` +
        `home ${d.returnJourney ? clock(d.returnJourney.arrivalMinute) : 'none'} ${d.sameDayReturn ? 'same day' : 'OVERNIGHT'}  ` +
        `round trip MVR ${d.roundTripMvr}${d.roundTripPartial ? '+' : ''}`,
    )
  }
}
