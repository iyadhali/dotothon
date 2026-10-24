/**
 * Grouping and classification for destination categories.
 *
 * The data pipeline can publish `kind: 'intervention'` categories built from
 * facility service-evidence rows (laboratory, dialysis, dental, ...). Older or
 * fixture networks only have facility categories, so the fallback mapping keeps
 * the selector organised without inventing intervention categories.
 */
import type { CategoryDefinition } from '../../shared/routing/types'

export type CategoryGroupLabel =
  | 'Health facilities'
  | 'Education'
  | 'Diagnostics & procedures'
  | 'Specialist services'
  | 'Dental'
  | 'Other'

export interface CategoryGroup {
  label: CategoryGroupLabel
  categories: CategoryDefinition[]
}

const GROUP_ORDER: CategoryGroupLabel[] = [
  'Health facilities',
  'Education',
  'Diagnostics & procedures',
  'Specialist services',
  'Dental',
  'Other',
]

/** Explicit fallback for the intervention ids listed in the extension contract. */
const SERVICE_GROUP: ReadonlyArray<{ match: RegExp; group: CategoryGroupLabel }> = [
  { match: /dental|orthodont/i, group: 'Dental' },
  { match: /lab|blood|imaging|radiolog|diagnos|ecg|ultrasound/i, group: 'Diagnostics & procedures' },
  {
    match: /dialysis|oncology|cancer|cardio|maternity|surgery|specialist|rehab|physio|mental/i,
    group: 'Specialist services',
  },
]

export function isInterventionCategory(definition: CategoryDefinition): boolean {
  return definition.kind === 'intervention' || definition.id.startsWith('service:')
}

export function categoryGroupLabel(definition: CategoryDefinition): CategoryGroupLabel {
  if (definition.group) {
    const known = GROUP_ORDER.find((label) => label === definition.group)
    if (known) return known
  }
  if (definition.kind === 'intervention' || definition.id.startsWith('service:')) {
    const match = SERVICE_GROUP.find((entry) => entry.match.test(definition.id))
    return match?.group ?? 'Specialist services'
  }
  if (definition.id.startsWith('health')) return 'Health facilities'
  if (definition.id.startsWith('education')) return 'Education'
  return 'Other'
}

export function groupCategories(categories: readonly CategoryDefinition[]): CategoryGroup[] {
  const groups = new Map<CategoryGroupLabel, CategoryDefinition[]>()
  for (const definition of categories) {
    const label = categoryGroupLabel(definition)
    const existing = groups.get(label)
    if (existing) existing.push(definition)
    else groups.set(label, [definition])
  }
  return GROUP_ORDER.filter((label) => groups.has(label)).map((label) => ({
    label,
    categories: [...(groups.get(label) ?? [])].sort((a, b) => a.label.localeCompare(b.label)),
  }))
}

/** Facility categories that can receive a user-added facility in the simulator. */
export function facilityCategories(
  categories: readonly CategoryDefinition[],
): CategoryDefinition[] {
  return categories.filter((definition) => !isInterventionCategory(definition))
}
