import assert from 'node:assert/strict'
import { mkdtempSync, readFileSync, rmSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { fileURLToPath } from 'node:url'
import { DatabaseSync } from 'node:sqlite'
import test from 'node:test'
import { buildDatabase, checkDatabase, EXPECTED, EXTRA_TABLES } from './build-db.ts'
import {
  BadRequestError,
  queryAccess,
  queryEconomics,
  queryFares,
  queryIslandProfile,
  querySeaLinks,
  queryValidation,
} from '../server/utils/database.ts'

const SOURCE_DIR = fileURLToPath(new URL('../public/data/', import.meta.url))
/** The prepared network; its meta.counts is the manifest the database is checked against. */
const NETWORK = JSON.parse(readFileSync(join(SOURCE_DIR, 'multimodal.json'), 'utf8')) as {
  meta: { counts: { stops: number; accessEdges: number; services: number } }
  services: { kind: string; stops?: unknown[] }[]
}

function temporaryDatabase(): { directory: string; outputPath: string } {
  const directory = mkdtempSync(join(tmpdir(), 'island-access-db-'))
  return { directory, outputPath: join(directory, 'maldives.sqlite') }
}

test('builds every source entity into the serving database', () => {
  const { directory, outputPath } = temporaryDatabase()
  try {
    const summary = buildDatabase({ sourceDir: SOURCE_DIR, outputPath })
    assert.equal(summary.schemaVersion, 2)
    assert.deepEqual(summary.counts, {
      islands: EXPECTED.islands,
      stops: NETWORK.meta.counts.stops,
      airports: EXPECTED.airports,
      accessEdges: NETWORK.meta.counts.accessEdges,
      services: NETWORK.meta.counts.services,
      facilities: EXPECTED.facilities,
      categories: EXPECTED.categories,
      facilityCategories: 1858,
      serviceStops: NETWORK.services.reduce((sum, s) => sum + (s.stops?.length ?? 0), 0),
      hdxNational: EXPECTED.hdxNational,
      hdxUnits: EXPECTED.hdxUnits,
    })
    assert.ok(summary.bytes > 1_000_000, 'database should contain the served data')

    const db = new DatabaseSync(outputPath, { readOnly: true })
    try {
      const integrity = db.prepare('PRAGMA integrity_check').get() as { integrity_check: string }
      assert.equal(integrity.integrity_check, 'ok')
      assert.equal((db.prepare('PRAGMA foreign_key_check').all() as unknown[]).length, 0)
      assert.equal(
        (db.prepare('SELECT count(*) AS count FROM islands WHERE is_origin = 1').get() as { count: number })
          .count,
        EXPECTED.origins,
      )
      assert.equal(
        (db.prepare('SELECT count(*) AS count FROM services WHERE kind = ?').get('timetabled') as {
          count: number
        }).count,
        NETWORK.services.filter((s) => s.kind === 'timetabled').length,
      )
      assert.equal(
        (db.prepare('SELECT count(*) AS count FROM services WHERE kind = ?').get('frequency') as {
          count: number
        }).count,
        NETWORK.services.filter((s) => s.kind === 'frequency').length,
      )
    } finally {
      db.close()
    }
  } finally {
    rmSync(directory, { recursive: true, force: true })
  }
})

test('checkDatabase confirms payload parity with source JSON', () => {
  const { directory, outputPath } = temporaryDatabase()
  try {
    buildDatabase({ sourceDir: SOURCE_DIR, outputPath })
    const summary = checkDatabase({ sourceDir: SOURCE_DIR, outputPath })
    assert.equal(summary.counts.facilities, EXPECTED.facilities)
    assert.equal(summary.counts.categories, EXPECTED.categories)
  } finally {
    rmSync(directory, { recursive: true, force: true })
  }
})

test('checkDatabase rejects a tampered payload', () => {
  const { directory, outputPath } = temporaryDatabase()
  try {
    buildDatabase({ sourceDir: SOURCE_DIR, outputPath })
    const db = new DatabaseSync(outputPath)
    try {
      db.prepare('UPDATE meta SET payload_json = ? WHERE id = 1').run('{}')
    } finally {
      db.close()
    }
    assert.throws(
      () => checkDatabase({ sourceDir: SOURCE_DIR, outputPath }),
      /meta: database payload does not match source JSON/,
    )
  } finally {
    rmSync(directory, { recursive: true, force: true })
  }
})

test('missing source artifact fails with an actionable error', () => {
  const { directory, outputPath } = temporaryDatabase()
  try {
    assert.throws(
      () =>
        buildDatabase({
          sourceDir: join(directory, 'does-not-exist'),
          outputPath,
        }),
      /missing required file/,
    )
  } finally {
    rmSync(directory, { recursive: true, force: true })
  }
})

const EXTRAS_DIR = fileURLToPath(new URL('../public/data/extras/', import.meta.url))

function extraRowCount(name: string): number {
  const file = JSON.parse(readFileSync(join(EXTRAS_DIR, `${name}.json`), 'utf8')) as {
    meta: { rowCount: number }
    records: unknown[]
  }
  assert.equal(file.records.length, file.meta.rowCount, `${name}: meta.rowCount matches records`)
  return file.records.length
}

function withExtrasDatabase(run: (db: DatabaseSync) => void): void {
  const { directory, outputPath } = temporaryDatabase()
  try {
    buildDatabase({ sourceDir: SOURCE_DIR, outputPath })
    const db = new DatabaseSync(outputPath, { readOnly: true })
    try {
      run(db)
    } finally {
      db.close()
    }
  } finally {
    rmSync(directory, { recursive: true, force: true })
  }
}

test('analysis tables match their extras file row counts and foreign keys', () => {
  const { directory, outputPath } = temporaryDatabase()
  try {
    const summary = buildDatabase({ sourceDir: SOURCE_DIR, outputPath })
    for (const spec of EXTRA_TABLES) {
      assert.equal(summary.extras[spec.name], extraRowCount(spec.name), spec.name)
    }
    const checked = checkDatabase({ sourceDir: SOURCE_DIR, outputPath })
    assert.deepEqual(checked.extras, summary.extras)
    const db = new DatabaseSync(outputPath, { readOnly: true })
    try {
      assert.equal((db.prepare('PRAGMA foreign_key_check').all() as unknown[]).length, 0)
      assert.equal(
        (db.prepare('PRAGMA user_version').get() as { user_version: number }).user_version,
        2,
      )
      // every island has a profile row; access covers only the origins
      assert.equal(summary.extras.island_profile, EXPECTED.islands)
      assert.equal(
        (db.prepare('SELECT count(DISTINCT origin_island_id) AS n FROM island_access').get() as { n: number }).n,
        EXPECTED.origins,
      )
    } finally {
      db.close()
    }
  } finally {
    rmSync(directory, { recursive: true, force: true })
  }
})

test('builds without an extras directory and leaves the analysis tables empty', () => {
  const { directory, outputPath } = temporaryDatabase()
  try {
    const summary = buildDatabase({ sourceDir: SOURCE_DIR, outputPath, extrasDir: join(directory, 'no-extras') })
    assert.equal(summary.counts.islands, EXPECTED.islands)
    for (const spec of EXTRA_TABLES) assert.equal(summary.extras[spec.name], 0, spec.name)
  } finally {
    rmSync(directory, { recursive: true, force: true })
  }
})

test('fare, economics, validation and sea-link queries return populated rows', () => {
  withExtrasDatabase((db) => {
    const fares = queryFares(db)
    assert.equal(fares.airRoutes.length, extraRowCount('fares_air'))
    assert.ok(fares.airRoutes.every((row) => Number(row.resident_one_way_mvr) > 0))
    assert.ok(fares.models.some((row) => row.mode === 'fast_ferry_rtl'))
    assert.equal(queryEconomics(db).rows.length, extraRowCount('economics'))
    assert.equal(queryValidation(db).atolls.length, extraRowCount('validation_atoll'))
    const links = querySeaLinks(db)
    assert.equal(links.links.length, extraRowCount('observed_sea_links'))
    const first = links.links[0] as { from_island_id: string }
    const scoped = querySeaLinks(db, first.from_island_id).links as Array<{
      from_island_id: string
      to_island_id: string
    }>
    assert.ok(scoped.length > 0)
    assert.ok(scoped.every((row) => row.from_island_id === first.from_island_id || row.to_island_id === first.from_island_id))
  })
})

test('access query filters by category and departure and rejects bad input', () => {
  withExtrasDatabase((db) => {
    const result = queryAccess(db, 'health_hospital', 480, 0)
    assert.equal(result.rows.length, EXPECTED.origins)
    assert.ok(result.rows.every((row) => row.estimated_air === 0))
    assert.ok(result.rows.some((row) => row.status === 'reachable'))
    assert.equal(queryAccess(db, 'health_hospital', 360).rows.length, EXPECTED.origins * 2)
    assert.throws(() => queryAccess(db, 'health_hospital', 481), BadRequestError)
    assert.throws(() => queryAccess(db, 'no_such_category', 480), BadRequestError)
    assert.throws(() => queryAccess(db, '', 480), BadRequestError)
  })
})

test('island profile joins profile, access rows and nearest facilities', () => {
  withExtrasDatabase((db) => {
    const row = db
      .prepare(
        `SELECT origin_island_id AS id FROM island_access
          WHERE category = 'health_hospital' AND departure_minute = 480 AND estimated_air = 0 AND status = 'reachable'
          LIMIT 1`,
      )
      .get() as { id: string }
    const profile = queryIslandProfile(db, row.id)
    assert.ok(profile)
    assert.equal((profile.profile as { island_id: string }).island_id, row.id)
    assert.equal(profile.access.length, 12 * 3 * 2)
    assert.ok(profile.nearest.length > 0)
    assert.ok(profile.nearest.every((entry) => typeof entry.destination_island_id === 'string'))
    assert.equal(queryIslandProfile(db, 'MV-NOPE'), null)
  })
})
