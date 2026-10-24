import assert from 'node:assert/strict'
import { mkdtempSync, readFileSync, rmSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { fileURLToPath } from 'node:url'
import { DatabaseSync } from 'node:sqlite'
import test from 'node:test'
import { buildDatabase, checkDatabase, EXPECTED } from './build-db.ts'

const SOURCE_DIR = fileURLToPath(new URL('../public/data/', import.meta.url))

function temporaryDatabase(): { directory: string; outputPath: string } {
  const directory = mkdtempSync(join(tmpdir(), 'island-access-db-'))
  return { directory, outputPath: join(directory, 'maldives.sqlite') }
}

test('builds every source entity into the serving database', () => {
  const { directory, outputPath } = temporaryDatabase()
  try {
    const summary = buildDatabase({ sourceDir: SOURCE_DIR, outputPath })
    assert.equal(summary.schemaVersion, 1)
    assert.deepEqual(summary.counts, {
      islands: EXPECTED.islands,
      stops: EXPECTED.stops,
      airports: EXPECTED.airports,
      accessEdges: EXPECTED.accessEdges,
      services: EXPECTED.services,
      facilities: EXPECTED.facilities,
      categories: EXPECTED.categories,
      facilityCategories: 1858,
      serviceStops: 498, // 390 RTL + 108 MTCC 2023 stop-times (augment_network.py)
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
        123, // 102 RTL + 21 MTCC 2023 trips
      )
      assert.equal(
        (db.prepare('SELECT count(*) AS count FROM services WHERE kind = ?').get('frequency') as {
          count: number
        }).count,
        226, // 64 air/ferry frequency services + 162 observed boat links
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
