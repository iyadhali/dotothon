/// <reference types="node" />
/**
 * Export per-origin accessibility to CSV for downstream analysis.
 *
 *   node --experimental-strip-types web/scripts/export-accessibility.ts
 *   node --experimental-strip-types web/scripts/export-accessibility.ts --out /tmp/x.csv
 *
 * The router already computes `perOrigin` for every origin on each call. This script
 * sweeps a set of categories across the operating day (05:00-18:00, 60-minute steps)
 * and writes one row per (origin, category, departure). It also reports, per origin,
 * the best elapsed time observed anywhere in the day — a measure of *service quality*
 * rather than a single-snapshot artefact.
 *
 * Read-only with respect to the network; writes only the requested CSV.
 */

import { existsSync, readFileSync, writeFileSync } from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

import type { MultimodalNetwork } from '../shared/routing/types'
import { computeAccessibility } from '../shared/routing/router.ts'

const WEB_ROOT = fileURLToPath(new URL('..', import.meta.url))
const NETWORK_PATH = path.join(WEB_ROOT, 'public', 'data', 'multimodal.json')
const DEFAULT_OUT = path.join(WEB_ROOT, '..', 'data', 'processed', 'multimodal', 'island_access.csv')

const CATEGORIES = [
  'health_hospital',
  'health_regional_tertiary',
  'health_any',
  'education_grade_11_12',
  'education_higher_ed',
  'education_school',
  'service:emergency',
  'service:dialysis',
  'service:ct',
  'service:mri',
  'service:oncology',
  'service:telemedicine',
]

/** Departures 05:00 → 18:00 in 60-minute steps. */
const DEPARTURES = Array.from({ length: 14 }, (_, i) => (5 + i) * 60)

function csvCell(value: unknown): string {
  if (value === null || value === undefined) return ''
  const text = String(value)
  return /[",\n]/.test(text) ? `"${text.replaceAll('"', '""')}"` : text
}

function main(): void {
  const args = process.argv.slice(2)
  const outIndex = args.indexOf('--out')
  const outPath = outIndex >= 0 && args[outIndex + 1] ? args[outIndex + 1] : DEFAULT_OUT

  if (!existsSync(NETWORK_PATH)) {
    console.log(`SKIP  network not found at ${NETWORK_PATH}`)
    return
  }

  const network = JSON.parse(readFileSync(NETWORK_PATH, 'utf8')) as MultimodalNetwork
  const population = new Map(network.islands.map(island => [island.id, island.population]))
  const islandName = new Map(network.islands.map(island => [island.id, island.name]))
  const isOrigin = new Set(network.islands.filter(island => island.isOrigin).map(island => island.id))

  console.log(
    `network: ${network.islands.length} islands, ${isOrigin.size} origins, ` +
      `${network.facilities.length} facilities, reference day ${network.meta.referenceDay}`,
  )

  const header = [
    'origin_island_id',
    'origin_island_name',
    'population',
    'category',
    'departure_minute',
    'departure_clock',
    'estimated_air',
    'status',
    'elapsed_minutes',
    'wait_minutes',
    'ride_minutes',
    'access_minutes',
    'transfer_minutes',
    'transfers',
    'modes',
    'service_confidence',
    'uses_estimated_air',
    'day_offset',
    'destination_facility_count',
    'destination_island_id',
  ]
  const rows: string[] = [header.join(',')]
  const best = new Map<string, { minutes: number; departure: number }>()
  const started = Date.now()

  for (const estimatedAir of [false, true]) {
    for (const category of CATEGORIES) {
      for (const departureMinute of DEPARTURES) {
        const result = computeAccessibility(network, {
          category,
          departureMinute,
          includeEstimatedAir: estimatedAir,
        })
        if (!result || result.perOrigin === undefined) {
          console.log(`  (no summary for ${category} @ ${departureMinute})`)
          continue
        }
        const clock = `${String(Math.floor(departureMinute / 60)).padStart(2, '0')}:${String(departureMinute % 60).padStart(2, '0')}`
        for (const originId of isOrigin) {
          const access = result.perOrigin[originId]
          const journey = access?.journey ?? null
          const key = `${originId}|${category}|${estimatedAir ? 1 : 0}`
          const minutes = journey?.elapsedMinutes
          if (minutes !== undefined && Number.isFinite(minutes)) {
            const current = best.get(key)
            if (!current || minutes < current.minutes) best.set(key, { minutes, departure: departureMinute })
          }
          rows.push(
            [
              originId,
              islandName.get(originId) ?? '',
              population.get(originId) ?? 0,
              category,
              departureMinute,
              clock,
              estimatedAir ? 1 : 0,
              access?.status ?? 'missing',
              journey?.elapsedMinutes ?? '',
              journey?.waitMinutes ?? '',
              journey?.rideMinutes ?? '',
              journey?.accessMinutes ?? '',
              journey?.transferMinutes ?? '',
              journey?.transfers ?? '',
              journey?.modes?.join('+') ?? '',
              journey?.serviceConfidence ?? '',
              journey?.usesEstimatedAir ? 1 : 0,
              journey?.dayOffset ?? '',
              journey?.destinationFacilityIds?.length ?? '',
              journey?.destinationIslandId ?? '',
            ]
              .map(csvCell)
              .join(','),
          )
        }
      }
      console.log(`  ${category} × ${DEPARTURES.length} departures × 2 air settings — done`)
    }
  }

  writeFileSync(outPath, `${rows.join('\n')}\n`, 'utf8')
  console.log(`wrote ${rows.length - 1} rows to ${outPath} in ${((Date.now() - started) / 1000).toFixed(1)}s`)

  // Companion file: one row per (origin, category, air setting) with the best time found
  // anywhere in the operating day. This is the service-quality measure, not a snapshot.
  const bestPath = outPath.replace(/\.csv$/, '_best.csv')
  const bestRows: string[] = [
    ['origin_island_id', 'origin_island_name', 'population', 'category', 'estimated_air', 'best_elapsed_minutes', 'best_departure_minute'].join(','),
  ]
  for (const [key, value] of [...best.entries()].sort()) {
    const [originId, category, air] = key.split('|')
    bestRows.push(
      [originId, islandName.get(originId) ?? '', population.get(originId) ?? 0, category, air, value.minutes, value.departure]
        .map(csvCell)
        .join(','),
    )
  }
  writeFileSync(bestPath, `${bestRows.join('\n')}\n`, 'utf8')
  console.log(`wrote ${bestRows.length - 1} rows to ${bestPath}`)
}

main()
