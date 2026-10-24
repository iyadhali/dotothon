import { createError } from 'h3'
import { createHash } from 'node:crypto'
import { existsSync, mkdirSync, renameSync, writeFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { DatabaseSync } from 'node:sqlite'
import type { FeatureCollection } from 'geojson'
import type { MultimodalNetwork } from '../../shared/routing/types'

const SCHEMA_VERSION = 1
const ASSET_KEY = 'maldives.sqlite'
const CACHE_DIRECTORY = 'island-access-atlas'

export class DatabaseUnavailableError extends Error {
  readonly code = 'database_unavailable'

  constructor(message: string, options?: { cause?: unknown }) {
    super(message, options)
    this.name = 'DatabaseUnavailableError'
  }
}

let databasePromise: Promise<DatabaseSync> | null = null

function toBytes(value: unknown): Uint8Array {
  if (value instanceof Uint8Array) return value
  if (value instanceof ArrayBuffer) return new Uint8Array(value)
  if (typeof value === 'string') return new TextEncoder().encode(value)
  throw new Error(`unexpected server asset payload type: ${typeof value}`)
}

async function resolveDatabasePath(): Promise<string> {
  const override = process.env.MULTIMODAL_DB_PATH
  if (override) {
    if (!existsSync(override)) {
      throw new DatabaseUnavailableError(
        'MULTIMODAL_DB_PATH is set but the database file does not exist.',
      )
    }
    return override
  }

  const storage = useStorage('assets:server')
  const raw = await storage.getItemRaw(ASSET_KEY)
  if (!raw) {
    throw new DatabaseUnavailableError(
      'The prepared SQLite database is not bundled. Run `npm run db:build` before starting the server.',
    )
  }

  const bytes = toBytes(raw)
  const digest = createHash('sha256').update(bytes).digest('hex').slice(0, 16)
  const directory = join(tmpdir(), CACHE_DIRECTORY)
  const path = join(directory, `maldives-${digest}.sqlite`)
  if (!existsSync(path)) {
    mkdirSync(directory, { recursive: true })
    const temporaryPath = `${path}.tmp-${process.pid}`
    writeFileSync(temporaryPath, bytes)
    try {
      renameSync(temporaryPath, path)
    } catch (error) {
      if (!existsSync(path)) throw error
    }
  }
  return path
}

async function openDatabase(): Promise<DatabaseSync> {
  const path = await resolveDatabasePath()
  let db: DatabaseSync
  try {
    db = new DatabaseSync(path, { readOnly: true })
    db.exec('PRAGMA query_only = ON')
    const version = db.prepare('PRAGMA user_version').get() as { user_version?: number } | undefined
    if (Number(version?.user_version ?? 0) !== SCHEMA_VERSION) {
      db.close()
      throw new DatabaseUnavailableError(
        `The prepared SQLite database has schema version ${version?.user_version ?? 0}; expected ${SCHEMA_VERSION}. Rebuild it with \`npm run db:build\`.`,
      )
    }
    const integrity = db.prepare('PRAGMA quick_check').get() as
      | { quick_check?: string }
      | undefined
    if (String(integrity?.quick_check ?? '').toLowerCase() !== 'ok') {
      db.close()
      throw new DatabaseUnavailableError('The prepared SQLite database is corrupt. Rebuild it with `npm run db:build`.')
    }
    const names = new Set(
      (db.prepare("SELECT name FROM sqlite_master WHERE type = 'table'").all() as Array<{
        name: string
      }>).map((row) => row.name),
    )
    for (const table of [
      'meta',
      'islands',
      'stops',
      'airports',
      'access_edges',
      'services',
      'service_stops',
      'facilities',
      'categories',
      'facility_categories',
      'hdx_meta',
      'hdx_national',
      'hdx_units',
    ]) {
      if (!names.has(table)) {
        db.close()
        throw new DatabaseUnavailableError(
          `The prepared SQLite database is missing table "${table}". Rebuild it with \`npm run db:build\`.`,
        )
      }
    }
  } catch (error) {
    if (error instanceof DatabaseUnavailableError) throw error
    throw new DatabaseUnavailableError('The prepared SQLite database could not be opened.', {
      cause: error,
    })
  }
  return db
}

/** Cached read-only database handle. Rejects if the asset is missing or invalid. */
export function getDatabase(): Promise<DatabaseSync> {
  if (!databasePromise) {
    databasePromise = openDatabase().catch((error: unknown) => {
      databasePromise = null
      throw error
    })
  }
  return databasePromise
}

function parseJson<T>(value: string | null | undefined): T {
  if (!value) throw new DatabaseUnavailableError('The prepared SQLite database contains an empty payload.')
  return JSON.parse(value) as T
}

function rows<T>(db: DatabaseSync, table: string, orderBy = 'ordinal'): T[] {
  return (db.prepare(`SELECT payload_json FROM ${table} ORDER BY ${orderBy}`).all() as Array<{
    payload_json: string
  }>).map((row) => parseJson<T>(row.payload_json))
}

export interface DatabaseStats {
  schemaVersion: number
  islands: number
  facilities: number
  services: number
  categories: number
}

export async function getNetwork(): Promise<MultimodalNetwork> {
  const db = await getDatabase()
  const metaRow = db.prepare('SELECT payload_json FROM meta WHERE id = 1').get() as
    | { payload_json: string }
    | undefined
  return {
    meta: parseJson(metaRow?.payload_json),
    islands: rows(db, 'islands'),
    stops: rows(db, 'stops'),
    airports: rows(db, 'airports'),
    accessEdges: rows(db, 'access_edges'),
    services: rows(db, 'services'),
    facilities: rows(db, 'facilities'),
    categories: rows(db, 'categories'),
  } as MultimodalNetwork
}

export async function getIslands(): Promise<FeatureCollection> {
  const db = await getDatabase()
  const features = (db
    .prepare('SELECT feature_json FROM islands ORDER BY ordinal')
    .all() as Array<{ feature_json: string }>).map((row) => parseJson<FeatureCollection['features'][number]>(row.feature_json))
  return { type: 'FeatureCollection', features }
}

export async function getHdx(): Promise<{
  source: string
  method: string
  warning: string
  national: unknown[]
  units: unknown[]
}> {
  const db = await getDatabase()
  const metaRow = db.prepare('SELECT payload_json FROM hdx_meta WHERE id = 1').get() as
    | { payload_json: string }
    | undefined
  return {
    ...parseJson<{ source: string; method: string; warning: string }>(metaRow?.payload_json),
    national: rows(db, 'hdx_national'),
    units: rows(db, 'hdx_units'),
  }
}

export async function getDatabaseStats(): Promise<DatabaseStats> {
  const db = await getDatabase()
  const count = (table: string): number => {
    const row = db.prepare(`SELECT count(*) AS count FROM ${table}`).get() as { count: number }
    return Number(row.count)
  }
  return {
    schemaVersion: SCHEMA_VERSION,
    islands: count('islands'),
    facilities: count('facilities'),
    services: count('services'),
    categories: count('categories'),
  }
}

export function asDatabaseError(error: unknown): Error {
  if (error instanceof DatabaseUnavailableError) {
    return createError({
      statusCode: 503,
      statusMessage: 'Prepared network database unavailable',
      data: { code: error.code },
      cause: error,
    })
  }
  return error instanceof Error ? error : new Error(String(error))
}
