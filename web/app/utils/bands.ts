/**
 * Travel-time bands and status colours shared by every map renderer and the legend.
 *
 * The bands are an explicit, documented simplification: 0–30, 30–60, 60–120,
 * 120–240 and 240+ minutes. `not_reachable`, `no_origin_access` and
 * `no_destination` are coverage states, never travel times, and must never be
 * conflated with a slow journey or with zero access.
 */
import type { AccessibilityResult, Island, OriginAccessStatus } from '../../shared/routing/types'

export type TravelBandKey =
  | 'b0_30'
  | 'b30_60'
  | 'b60_120'
  | 'b120_240'
  | 'b240_plus'
  | 'not_selected'
  | 'not_reachable'
  | 'no_origin_access'
  | 'no_destination'
  | 'non_origin'
  | 'not_computed'

export type BandPattern = 'none' | 'diagonal' | 'dots' | 'cross' | 'grid'

export interface BandStyle {
  key: TravelBandKey
  /** Legend label, e.g. `0–30 min`. */
  label: string
  /** Compact map/table label. */
  shortLabel: string
  color: string
  ink: string
  pattern: BandPattern
  /** Marker radius for point geometries (Mapbox px and schematic logical units differ). */
  radius: number
  description: string
}

export const BAND_STYLES: readonly BandStyle[] = [
  {
    key: 'b0_30',
    label: '0–30 min',
    shortLabel: '0–30',
    color: '#1c6b58',
    ink: '#ffffff',
    pattern: 'none',
    radius: 5.5,
    description: 'Reachable within 30 minutes of the requested departure.',
  },
  {
    key: 'b30_60',
    label: '30–60 min',
    shortLabel: '30–60',
    color: '#4d9a7d',
    ink: '#122c24',
    pattern: 'none',
    radius: 5,
    description: 'Reachable in 31–60 minutes.',
  },
  {
    key: 'b60_120',
    label: '60–120 min',
    shortLabel: '60–120',
    color: '#9dbf8f',
    ink: '#1b352b',
    pattern: 'none',
    radius: 4.5,
    description: 'Reachable in 61–120 minutes.',
  },
  {
    key: 'b120_240',
    label: '120–240 min',
    shortLabel: '120–240',
    color: '#e3c477',
    ink: '#3c2f12',
    pattern: 'none',
    radius: 4,
    description: 'Reachable in 121–240 minutes.',
  },
  {
    key: 'b240_plus',
    label: '240+ min',
    shortLabel: '240+',
    color: '#d78f60',
    ink: '#3a1c0c',
    pattern: 'none',
    radius: 3.8,
    description: 'Reachable but the best journey takes more than 240 minutes.',
  },
  {
    key: 'not_selected',
    label: 'Not selected by network filter',
    shortLabel: 'Not selected',
    color: '#dfe8ec',
    ink: '#2d3f47',
    pattern: 'grid',
    radius: 3.5,
    description:
      'This island has physical access in the prepared network, but the current Land/Sea/Air or route selection removes all of it. A user selection, not a coverage finding.',
  },
  {
    key: 'not_reachable',
    label: 'No same-day trip',
    shortLabel: 'No same-day trip',
    color: '#b9bcb4',
    ink: '#26332c',
    pattern: 'diagonal',
    radius: 3.5,
    description:
      'Transport exists in the network but no itinerary reaches an eligible facility within the journey horizon. This is not proof that no transport exists.',
  },
  {
    key: 'no_origin_access',
    label: 'No transport data',
    shortLabel: 'No data',
    color: '#efe9dd',
    ink: '#4a4f43',
    pattern: 'dots',
    radius: 3.5,
    description:
      'No ferry, flight or road link from this island in our data, so no journey can be modelled. A data coverage gap, not proof that no boat runs.',
  },
  {
    key: 'no_destination',
    label: 'No destination in category',
    shortLabel: 'No destination',
    color: '#e4deea',
    ink: '#3f354b',
    pattern: 'cross',
    radius: 3.3,
    description: 'No eligible facility in the selected category exists in the prepared data.',
  },
  {
    key: 'non_origin',
    label: 'Not an origin island',
    shortLabel: 'Not an origin',
    color: '#f4f6f5',
    ink: '#5c665c',
    pattern: 'none',
    radius: 2.8,
    description: 'Airport or islet included for context; not one of the 191 inhabited origin islands.',
  },
  {
    key: 'not_computed',
    label: 'Not computed yet',
    shortLabel: 'Pending',
    color: '#ffffff',
    ink: '#61746b',
    pattern: 'dots',
    radius: 3,
    description: 'The accessibility calculation has not produced a state for this island yet.',
  },
]

export const BAND_BY_KEY: Record<TravelBandKey, BandStyle> = Object.fromEntries(
  BAND_STYLES.map((band) => [band.key, band]),
) as Record<TravelBandKey, BandStyle>

export const BAND_ORDER: readonly TravelBandKey[] = BAND_STYLES.map((band) => band.key)

/** Bands shown in the map legend (everything except the transient "not computed" state). */
export const LEGEND_BANDS: readonly BandStyle[] = BAND_STYLES.filter(
  (band) => band.key !== 'not_computed',
)

export function bandForMinutes(minutes: number | null | undefined): TravelBandKey {
  if (minutes == null || !Number.isFinite(minutes)) return 'not_computed'
  if (minutes <= 30) return 'b0_30'
  if (minutes <= 60) return 'b30_60'
  if (minutes <= 120) return 'b60_120'
  if (minutes <= 240) return 'b120_240'
  return 'b240_plus'
}

export function bandForStatus(
  status: OriginAccessStatus | null | undefined,
  minutes?: number | null,
): TravelBandKey {
  switch (status) {
    case 'reachable':
      return minutes == null ? 'not_computed' : bandForMinutes(minutes)
    case 'not_reachable':
      return 'not_reachable'
    case 'no_origin_access':
      return 'no_origin_access'
    case 'no_destination':
      return 'no_destination'
    default:
      return 'not_computed'
  }
}

export interface IslandBandInfo {
  islandId: string
  band: TravelBandKey
  minutes: number | null
  status: OriginAccessStatus | null
  population: number
  /** True when the router's no-access state is caused by the user's filter. */
  filteredOut?: boolean
}

export interface IslandBandOptions {
  /** Any mode or route exclusion is active. */
  filterActive?: boolean
  /** Islands with at least one physical access edge in the prepared network. */
  hasInfrastructure?: ReadonlySet<string>
}

/** Join router accessibility output to island geometry/markers by island id. */
export function buildIslandBands(
  accessibility: AccessibilityResult | null,
  islands: readonly Island[],
  options: IslandBandOptions = {},
): Record<string, IslandBandInfo> {
  const bands: Record<string, IslandBandInfo> = {}
  for (const island of islands) {
    if (!island.isOrigin) {
      bands[island.id] = {
        islandId: island.id,
        band: 'non_origin',
        minutes: null,
        status: null,
        population: island.population,
      }
      continue
    }
    const access = accessibility?.perOrigin[island.id]
    if (!access) {
      bands[island.id] = {
        islandId: island.id,
        band: 'not_computed',
        minutes: null,
        status: null,
        population: island.population,
      }
      continue
    }
    const minutes = access.status === 'reachable' ? (access.journey?.elapsedMinutes ?? null) : null
    const filteredOut =
      Boolean(options.filterActive) &&
      access.status === 'no_origin_access' &&
      (options.hasInfrastructure?.has(island.id) ?? false)
    bands[island.id] = {
      islandId: island.id,
      band: filteredOut ? 'not_selected' : bandForStatus(access.status, minutes),
      minutes,
      status: access.status,
      population: island.population,
      filteredOut,
    }
  }
  return bands
}

/** CSS background overlay that mirrors the SVG patterns used by the schematic map. */
export function patternBackground(pattern: BandPattern): string {
  switch (pattern) {
    case 'diagonal':
      return 'repeating-linear-gradient(45deg, rgba(35, 61, 54, 0.28) 0 1px, transparent 1px 5px)'
    case 'dots':
      return 'radial-gradient(rgba(35, 61, 54, 0.35) 1px, transparent 1.1px) 0 0 / 6px 6px'
    case 'cross':
      return 'repeating-linear-gradient(45deg, rgba(35, 61, 54, 0.24) 0 1px, transparent 1px 6px), repeating-linear-gradient(-45deg, rgba(35, 61, 54, 0.24) 0 1px, transparent 1px 6px)'
    case 'grid':
      return 'repeating-linear-gradient(0deg, rgba(35, 61, 54, 0.2) 0 1px, transparent 1px 6px), repeating-linear-gradient(90deg, rgba(35, 61, 54, 0.2) 0 1px, transparent 1px 6px)'
    default:
      return 'none'
  }
}

export function bandOrderIndex(band: TravelBandKey): number {
  const index = BAND_ORDER.indexOf(band)
  return index === -1 ? BAND_ORDER.length : index
}
