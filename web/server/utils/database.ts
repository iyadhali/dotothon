import { createError } from 'h3'
import { createHash } from 'node:crypto'
import { existsSync, mkdirSync, renameSync, writeFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { DatabaseSync } from 'node:sqlite'
import type { FeatureCollection } from 'geojson'
import type { MultimodalNetwork } from '../../shared/routing/types'

const SCHEMA_VERSION = 2
const ASSET_KEY = 'maldives.sqlite'
const CACHE_DIRECTORY = 'island-access-atlas'

export class DatabaseUnavailableError extends Error {
  readonly code = 'database_unavailable'

  constructor(message: string, options?: { cause?: unknown }) {
    super(message, options)
    this.name = 'DatabaseUnavailableError'
  }
}

export const EXTRA_TABLE_NAMES = [
  'fares_air',
  'fare_models',
  'island_profile',
  'health_facilities',
  'economics',
  'observed_sea_links',
  'validation_atoll',
  'island_access',
] as const

export const ACCESS_DEPARTURES = [360, 480, 840] as const

/** Raised for caller mistakes (bad query parameters); mapped to HTTP 400 by asDatabaseError. */
export class BadRequestError extends Error {
  readonly code = 'bad_request'

  constructor(message: string) {
    super(message)
    this.name = 'BadRequestError'
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
      'extras_meta',
      'fares_air',
      'fare_models',
      'island_profile',
      'health_facilities',
      'economics',
      'observed_sea_links',
      'validation_atoll',
      'island_access',
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
  /** Row counts of the analysis tables (0 = extras not built into this database). */
  extras: Record<string, number>
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
    extras: Object.fromEntries(EXTRA_TABLE_NAMES.map((table) => [table, count(table)])),
  }
}

type Row = Record<string, unknown>

function extrasMeta(db: DatabaseSync, names: string[]): Record<string, unknown> {
  const out: Record<string, unknown> = {}
  const statement = db.prepare('SELECT payload_json FROM extras_meta WHERE name = ?')
  for (const name of names) {
    const row = statement.get(name) as { payload_json: string } | undefined
    if (row) out[name] = JSON.parse(row.payload_json)
  }
  return out
}

export function queryFares(db: DatabaseSync) {
  return {
    airRoutes: db.prepare('SELECT * FROM fares_air ORDER BY pair').all() as Row[],
    models: db.prepare('SELECT * FROM fare_models ORDER BY mode').all() as Row[],
    meta: extrasMeta(db, ['fares_air', 'fare_models']),
  }
}

export function queryEconomics(db: DatabaseSync) {
  return {
    rows: db.prepare('SELECT * FROM economics ORDER BY id').all() as Row[],
    meta: extrasMeta(db, ['economics']),
  }
}

export function queryValidation(db: DatabaseSync) {
  return {
    atolls: db.prepare('SELECT * FROM validation_atoll ORDER BY estimated_air, atoll_code').all() as Row[],
    meta: extrasMeta(db, ['validation_atoll']),
  }
}

export function querySeaLinks(db: DatabaseSync, islandId?: string) {
  const rows = (islandId
    ? db
        .prepare(
          'SELECT * FROM observed_sea_links WHERE from_island_id = ?1 OR to_island_id = ?1 ORDER BY trips_per_day DESC, id',
        )
        .all(islandId)
    : db.prepare('SELECT * FROM observed_sea_links ORDER BY trips_per_day DESC, id').all()) as Row[]
  return { links: rows, meta: extrasMeta(db, ['observed_sea_links']) }
}

/** Best-of-day and fixed-departure accessibility for one category across all origins. */
export function queryAccess(db: DatabaseSync, category: string, departure: number, estimatedAir?: 0 | 1) {
  if (!category) throw new BadRequestError('Query parameter "category" is required.')
  if (!(ACCESS_DEPARTURES as readonly number[]).includes(departure)) {
    throw new BadRequestError(`Query parameter "departure" must be one of ${ACCESS_DEPARTURES.join(', ')}.`)
  }
  const known = db.prepare('SELECT 1 AS ok FROM island_access WHERE category = ? LIMIT 1').get(category)
  if (!known) throw new BadRequestError(`Unknown access category "${category}".`)
  const rows = db
    .prepare(
      `SELECT a.origin_island_id, i.name AS origin_name, i.population, a.estimated_air, a.status,
              a.elapsed_minutes, a.best_elapsed_minutes, a.modes, a.destination_island_id
         FROM island_access a JOIN islands i ON i.id = a.origin_island_id
        WHERE a.category = ?1 AND a.departure_minute = ?2 AND (?3 IS NULL OR a.estimated_air = ?3)
        ORDER BY a.estimated_air, a.origin_island_id`,
    )
    .all(category, departure, estimatedAir ?? null) as Row[]
  return { category, departure, rows, meta: extrasMeta(db, ['island_access']) }
}

/** Island profile (education/health context), access rows and the facilities at the destination islands. */
export function queryIslandProfile(db: DatabaseSync, islandId: string) {
  const profile = db.prepare('SELECT * FROM island_profile WHERE island_id = ?').get(islandId) as Row | undefined
  if (!profile) return null
  const access = db
    .prepare(
      `SELECT category, departure_minute, estimated_air, status, elapsed_minutes, best_elapsed_minutes,
              modes, destination_island_id
         FROM island_access WHERE origin_island_id = ?
        ORDER BY category, estimated_air, departure_minute`,
    )
    .all(islandId) as Row[]
  const facilityStatement = db.prepare(
    `SELECT f.id, f.name, f.kind, f.tier, f.type
       FROM facilities f JOIN facility_categories c ON c.facility_id = f.id
      WHERE f.island_id = ? AND c.category_id = ? ORDER BY f.name LIMIT 5`,
  )
  const destinationName = db.prepare('SELECT name FROM islands WHERE id = ?')
  // Nearest facilities: per category, the 08:00 journey over scheduled/observed services (estimated air excluded).
  const nearest: Row[] = []
  for (const row of access) {
    if (row.departure_minute !== 480 || row.estimated_air !== 0) continue
    if (row.status !== 'reachable' || !row.destination_island_id) continue
    const destination = String(row.destination_island_id)
    nearest.push({
      category: row.category,
      elapsed_minutes: row.elapsed_minutes,
      best_elapsed_minutes: row.best_elapsed_minutes,
      modes: row.modes,
      destination_island_id: destination,
      destination_name: (destinationName.get(destination) as { name: string } | undefined)?.name ?? null,
      facilities: facilityStatement.all(destination, String(row.category)),
    })
  }
  const healthFacilities = db
    .prepare(
      'SELECT facility_key, name, tier, grade, type, level_2026 FROM health_facilities WHERE island_id = ? ORDER BY facility_key',
    )
    .all(islandId) as Row[]
  return { profile, access, nearest, healthFacilities }
}

export function asDatabaseError(error: unknown): Error {
  if (error instanceof BadRequestError) {
    return createError({ statusCode: 400, statusMessage: error.message, data: { code: error.code }, cause: error })
  }
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
