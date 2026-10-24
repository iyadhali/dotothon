/**
 * Formatting helpers for the multimodal prototype.
 *
 * Times in the network are integer minutes after midnight in `Indian/Maldives`
 * (UTC+5). They are rendered as wall-clock strings and never reinterpreted in the
 * browser's local time zone.
 */

export const MINUTES_PER_DAY = 1440

const clockPattern = /^(\d{1,2}):(\d{2})$/

/** Parse a `HH:MM` input value into minutes after midnight (fallback when invalid). */
export function parseClock(value: string, fallback = 480): number {
  const match = clockPattern.exec(String(value ?? '').trim())
  if (!match) return fallback
  const hours = Number(match[1])
  const minutes = Number(match[2])
  if (!Number.isFinite(hours) || !Number.isFinite(minutes)) return fallback
  if (hours < 0 || hours > 23 || minutes < 0 || minutes > 59) return fallback
  return hours * 60 + minutes
}

/** Render minutes after midnight as `HH:MM` (wraps at 24h, use formatClockWithDay for journeys). */
export function formatClock(minute: number | null | undefined): string {
  if (minute == null || !Number.isFinite(minute)) return '—'
  const rounded = Math.round(minute)
  const normalised = ((rounded % MINUTES_PER_DAY) + MINUTES_PER_DAY) % MINUTES_PER_DAY
  const hours = Math.floor(normalised / 60)
  const minutes = normalised % 60
  return `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}`
}

/** Render a journey time with an explicit day offset when the journey crosses midnight. */
export function formatClockWithDay(minute: number | null | undefined): string {
  if (minute == null || !Number.isFinite(minute)) return '—'
  const rounded = Math.round(minute)
  const dayOffset = Math.floor(rounded / MINUTES_PER_DAY)
  if (dayOffset <= 0) return formatClock(rounded)
  return `${formatClock(rounded)} (+${dayOffset} day${dayOffset === 1 ? '' : 's'})`
}

/** Human duration such as `1 h 24 min`; minutes only below one hour. */
export function formatDuration(minutes: number | null | undefined): string {
  if (minutes == null || !Number.isFinite(minutes)) return '—'
  const total = Math.max(0, Math.round(minutes))
  const hours = Math.floor(total / 60)
  const mins = total % 60
  if (hours === 0) return `${mins} min`
  if (mins === 0) return `${hours} h`
  return `${hours} h ${mins} min`
}

/** Compact duration such as `1h 24m`. */
export function formatDurationCompact(minutes: number | null | undefined): string {
  if (minutes == null || !Number.isFinite(minutes)) return '—'
  const total = Math.max(0, Math.round(minutes))
  const hours = Math.floor(total / 60)
  const mins = total % 60
  if (hours === 0) return `${mins}m`
  if (mins === 0) return `${hours}h`
  return `${hours}h ${mins}m`
}

const populationFormatter = new Intl.NumberFormat('en-GB')

/** Group-separated population count. */
export function formatPopulation(value: number | null | undefined): string {
  if (value == null || !Number.isFinite(value)) return '—'
  return populationFormatter.format(Math.round(value))
}

/** Percentage from a 0..1 ratio. */
export function formatPercent(value: number | null | undefined, digits = 1): string {
  if (value == null || !Number.isFinite(value)) return '—'
  return `${(value * 100).toFixed(digits)}%`
}

/** Signed population/number delta with a leading `+`. */
export function formatSignedNumber(value: number | null | undefined): string {
  if (value == null || !Number.isFinite(value)) return '—'
  const rounded = Math.round(value)
  if (rounded === 0) return '0'
  return `${rounded > 0 ? '+' : '−'}${formatPopulation(Math.abs(rounded))}`
}

/** Safe date display for ISO timestamps and `YYYY-MM-DD` values. */
export function formatDate(value: string | null | undefined): string {
  if (!value) return '—'
  const raw = String(value).trim()
  const dateOnly = /^\d{4}-\d{2}-\d{2}$/.test(raw) ? new Date(`${raw}T00:00:00Z`) : new Date(raw)
  if (Number.isNaN(dateOnly.getTime())) return raw
  return new Intl.DateTimeFormat('en-GB', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
    timeZone: 'Indian/Maldives',
  }).format(dateOnly)
}

/** Pluralise a simple noun for counts. */
export function pluralise(count: number, singular: string, plural = `${singular}s`): string {
  return `${formatPopulation(count)} ${count === 1 ? singular : plural}`
}
