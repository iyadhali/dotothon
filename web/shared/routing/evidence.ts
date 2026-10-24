/**
 * Evidence layers: where each service in the network comes from, so users can switch a
 * source off and every journey can say which evidence it relied on.
 *
 * Precedence is structural (scripts/multimodal/augment_network.py): MTCC 2023 trips are only
 * added in atolls with no RTL stop, and observed boat links only where no timetabled service
 * serves the island pair. So RTL > MTCC > observed boats, and estimated flights are separate.
 */
import type { Journey, MultimodalNetwork, Service } from './types'

export type EvidenceKey = 'rtl' | 'mtcc' | 'observed' | 'air' | 'male_ferry'

export interface EvidenceLayer {
  key: EvidenceKey
  label: string
  /** Short tag for a journey row. */
  tag: string
  /** Verified timetable vs estimate, for the confidence colour. */
  verified: boolean
}

export const EVIDENCE_LAYERS: EvidenceLayer[] = [
  { key: 'rtl', label: 'RTL ferries (2026 timetable)', tag: 'RTL timetable', verified: true },
  { key: 'mtcc', label: 'MTCC ferries (2023 timetable)', tag: 'MTCC 2023', verified: true },
  { key: 'observed', label: 'Observed boats (GPS, Aug 2025)', tag: 'Observed boats', verified: false },
  { key: 'air', label: 'Domestic flights (estimated)', tag: 'Estimated flight', verified: false },
  { key: 'male_ferry', label: 'Malé–Vilimalé ferry', tag: 'Malé ferry', verified: false },
]

export function serviceEvidence(service: Pick<Service, 'id' | 'kind' | 'mode'> & { operator?: string; routeId?: string }): EvidenceKey {
  if (service.mode === 'air') return 'air'
  if (service.id.startsWith('observed:') || service.routeId === 'observed-boats') return 'observed'
  if (service.kind === 'timetabled') return service.operator === 'MTCC' || service.id.startsWith('mtcc:') ? 'mtcc' : 'rtl'
  return 'male_ferry'
}

/** Service ids to disable so that only the enabled evidence layers remain. */
export function disabledByEvidence(network: MultimodalNetwork, enabled: ReadonlySet<EvidenceKey>): string[] {
  if (EVIDENCE_LAYERS.every((layer) => enabled.has(layer.key))) return []
  return network.services.filter((service) => !enabled.has(serviceEvidence(service))).map((service) => service.id)
}

/** Distinct evidence layers a journey used, in leg order. */
export function journeyEvidence(network: MultimodalNetwork, journey: Journey): EvidenceLayer[] {
  const services = new Map(network.services.map((service) => [service.id, service]))
  const keys: EvidenceKey[] = []
  for (const leg of journey.legs) {
    const service = leg.serviceId ? services.get(leg.serviceId) : undefined
    if (!service) continue
    const key = serviceEvidence(service)
    if (!keys.includes(key)) keys.push(key)
  }
  return keys.map((key) => EVIDENCE_LAYERS.find((layer) => layer.key === key)!)
}
