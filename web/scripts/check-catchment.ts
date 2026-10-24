/// <reference types="node" />
/** Service area of each recommended site, best over several departure times. */
import { readFileSync } from 'node:fs'
import type { MultimodalNetwork } from '../shared/routing/types'
import { buildTravelMatrix, recommendSites } from '../shared/routing/recommend.ts'

const network = JSON.parse(readFileSync('public/data/multimodal.json', 'utf8')) as MultimodalNetwork
const category = process.argv[2] ?? 'health_hospital'
const horizon = Number(process.argv[3] ?? 180)
const deps = [360, 480, 600, 840]
const t0 = performance.now()
const sites = recommendSites(network, buildTravelMatrix(network, { departureMinute: 480, maxJourneyMinutes: 60 }), { category, thresholdMinutes: 60, picks: 5 }).sites
const best = new Map<string, Map<string, number>>()
for (const d of deps) {
  for (const [o, row] of buildTravelMatrix(network, { departureMinute: d, maxJourneyMinutes: horizon })) {
    const acc = best.get(o) ?? new Map()
    for (const [i, t] of row) acc.set(i, Math.min(acc.get(i) ?? Infinity, t))
    best.set(o, acc)
  }
}
const existing = [...new Set(network.facilities.filter((f) => f.categories.includes(category)).map((f) => f.islandId))]
const before = new Map([...best].map(([o, row]) => [o, Math.min(...existing.map((id) => row.get(id) ?? Infinity))]))
for (const site of sites) {
  const reach = [...best].filter(([o, row]) => o !== site.islandId && row.has(site.islandId))
  const better = reach.filter(([o, row]) => row.get(site.islandId)! < before.get(o)!)
  console.log(`#${site.rank} ${site.name}: ${reach.length} within ${horizon} min (best departure), ${better.length} faster than today`)
}
console.log(`${Math.round(performance.now() - t0)} ms`)
