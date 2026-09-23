/**
 * Date.toISOString() always converts to UTC, which silently shifts the
 * calendar date back by one day for a locally-constructed Date in any
 * timezone ahead of UTC (e.g. IST, UTC+5:30) -- worst case, a full day off
 * for a midnight-anchored date, or just the midnight-to-offset window for
 * "now". Format from the local year/month/day fields instead so "today"
 * and date-range boundaries stay correct everywhere in the app.
 */
export function toLocalIsoDate(d: Date): string {
  const year = d.getFullYear()
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

export function todayIso(): string {
  return toLocalIsoDate(new Date())
}
