/**
 * One island classification for every map, legend and fallback, so the same island never
 * reads differently between views. Relative to the selected travel-time threshold.
 */
import type { OriginAccess } from '../../shared/routing/types'

export type AccessClass = 'served' | 'over_threshold' | 'no_trip' | 'no_data'

export const ACCESS_CLASSES: AccessClass[] = ['served', 'over_threshold', 'no_trip', 'no_data']

export function accessClassLabel(cls: AccessClass, thresholdMinutes: number): string {
  switch (cls) {
    case 'served':
      return `Within ${thresholdMinutes} min`
    case 'over_threshold':
      return 'Reachable, slower'
    case 'no_trip':
      return 'No same-day trip'
    case 'no_data':
      return 'No transport data'
  }
}

/** Fill colours shared by the Mapbox map, the fallback map and the legend dots. */
export const ACCESS_CLASS_COLORS: Record<AccessClass, string> = {
  served: '#cbd5e1',
  over_threshold: '#f59e0b',
  no_trip: '#dc2626',
  no_data: '#ffffff',
}

export function classifyAccess(access: OriginAccess | undefined, thresholdMinutes: number): AccessClass | null {
  if (!access) return null
  switch (access.status) {
    case 'reachable':
      return (access.journey?.elapsedMinutes ?? 0) <= thresholdMinutes ? 'served' : 'over_threshold'
    case 'no_origin_access':
      return 'no_data'
    case 'not_reachable':
      return 'no_trip'
    default:
      return null
  }
}
