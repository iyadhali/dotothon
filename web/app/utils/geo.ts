/**
 * Mercator projection helpers for the token-free schematic map.
 *
 * The schematic is explicitly a diagram: island markers are projected centroids,
 * not physical island area or service catchments. Where simplified polygons from
 * `islands.geojson` are available they are drawn beneath the markers for context.
 */
import type { FeatureCollection, Geometry, Position } from 'geojson'

export type LonLat = [number, number]

export interface Projector {
  width: number
  height: number
  project: (lon: number, lat: number) => LonLat
}

const MAX_MERCATOR_LAT = 85.05112878
const FALLBACK_CORNERS: readonly LonLat[] = [
  [72.35, -0.9],
  [74.35, 7.45],
]

/** Normalised Web-Mercator coordinates in [0, 1] × [0, 1] (north at y = 0). */
export function mercatorPoint(lon: number, lat: number): LonLat {
  const clampedLat = Math.max(-MAX_MERCATOR_LAT, Math.min(MAX_MERCATOR_LAT, lat))
  const radians = (clampedLat * Math.PI) / 180
  const x = (lon + 180) / 360
  const y = (1 - Math.asinh(Math.tan(radians)) / Math.PI) / 2
  return [x, y]
}

/**
 * Build a uniform-scale projector that fits every supplied lon/lat point inside
 * the given logical canvas with padding. Aspect ratio is preserved so the diagram
 * is geographically shaped; unused space becomes ocean/letterboxing.
 */
export function createProjector(
  points: readonly LonLat[],
  width: number,
  height: number,
  padding = 56,
): Projector {
  const projected = points
    .map(([lon, lat]) => mercatorPoint(lon, lat))
    .filter(([x, y]) => Number.isFinite(x) && Number.isFinite(y))

  if (projected.length === 0) {
    for (const [lon, lat] of FALLBACK_CORNERS) projected.push(mercatorPoint(lon, lat))
  }

  let minX = Infinity
  let maxX = -Infinity
  let minY = Infinity
  let maxY = -Infinity
  for (const [x, y] of projected) {
    if (x < minX) minX = x
    if (x > maxX) maxX = x
    if (y < minY) minY = y
    if (y > maxY) maxY = y
  }

  const spanX = Math.max(maxX - minX, 1e-9)
  const spanY = Math.max(maxY - minY, 1e-9)
  const innerWidth = Math.max(width - padding * 2, 1)
  const innerHeight = Math.max(height - padding * 2, 1)
  const scale = Math.min(innerWidth / spanX, innerHeight / spanY)
  const offsetX = (width - spanX * scale) / 2
  const offsetY = (height - spanY * scale) / 2

  return {
    width,
    height,
    project(lon: number, lat: number): LonLat {
      const [x, y] = mercatorPoint(lon, lat)
      return [offsetX + (x - minX) * scale, offsetY + (y - minY) * scale]
    },
  }
}

function pushCoordinates(value: unknown, out: LonLat[]): void {
  if (!Array.isArray(value) || value.length === 0) return
  const first = value[0]
  const second = value[1]
  if (typeof first === 'number' && typeof second === 'number') {
    if (Number.isFinite(first) && Number.isFinite(second)) out.push([first, second])
    return
  }
  for (const child of value) pushCoordinates(child, out)
}

function pushGeometry(geometry: Geometry | null | undefined, out: LonLat[]): void {
  if (!geometry) return
  if (geometry.type === 'GeometryCollection') {
    for (const child of geometry.geometries) pushGeometry(child, out)
    return
  }
  pushCoordinates(geometry.coordinates, out)
}

/** Every lon/lat pair referenced by a FeatureCollection (used to fit the viewBox). */
export function collectGeoCoordinates(geo: FeatureCollection | null | undefined): LonLat[] {
  const out: LonLat[] = []
  if (!geo) return out
  for (const feature of geo.features) pushGeometry(feature.geometry, out)
  return out
}

function round(value: number): number {
  return Math.round(value * 100) / 100
}

function linePath(line: readonly Position[], project: Projector['project']): string {
  let path = ''
  let started = false
  for (const point of line) {
    const lon = point[0]
    const lat = point[1]
    if (typeof lon !== 'number' || typeof lat !== 'number') continue
    const [x, y] = project(lon, lat)
    path += `${started ? 'L' : 'M'}${round(x)},${round(y)} `
    started = true
  }
  return path.trim()
}

function polygonPath(polygon: readonly (readonly Position[])[], project: Projector['project']): string {
  const parts: string[] = []
  for (const ring of polygon) {
    const line = linePath(ring, project)
    if (line) parts.push(`${line} Z`)
  }
  return parts.join(' ')
}

/** SVG path data for polygon, line and multi-geometries. */
export function geometryToPath(
  geometry: Geometry | null | undefined,
  project: Projector['project'],
): string {
  if (!geometry) return ''
  switch (geometry.type) {
    case 'Polygon':
      return polygonPath(geometry.coordinates, project)
    case 'MultiPolygon':
      return geometry.coordinates.map((polygon) => polygonPath(polygon, project)).join(' ')
    case 'LineString':
      return linePath(geometry.coordinates, project)
    case 'MultiLineString':
      return geometry.coordinates.map((line) => linePath(line, project)).join(' ')
    default:
      return ''
  }
}

/** Island id from a GeoJSON feature's properties, tolerating `islandId`/`island_id`. */
export function featureIslandId(properties: unknown): string | null {
  if (!properties || typeof properties !== 'object') return null
  const record = properties as Record<string, unknown>
  const raw = record.islandId ?? record.island_id ?? record.adm2_pcode ?? record.id
  return typeof raw === 'string' && raw.length > 0 ? raw : null
}
