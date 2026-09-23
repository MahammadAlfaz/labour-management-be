import { useState } from 'react'
import EmptyState from '../../components/EmptyState'
import { AlertIcon } from '../../components/icons'
import { toLocalIsoDate } from '../../lib/date'
import DateRangeFields from './DateRangeFields'
import { weeklySettlementExportUrl } from './api'
import { useWeeklySettlementReport } from './useReports'

/** Sunday-to-Saturday week containing today (see plan: Sat is payday). */
function currentWeekRange(): { start: string; end: string } {
  const d = new Date()
  const start = new Date(d)
  start.setDate(d.getDate() - d.getDay())
  const end = new Date(start)
  end.setDate(start.getDate() + 6)
  return { start: toLocalIsoDate(start), end: toLocalIsoDate(end) }
}

export default function WeeklySettlementView() {
  const initial = currentWeekRange()
  const [from, setFrom] = useState(initial.start)
  const [to, setTo] = useState(initial.end)

  const { data: report, isLoading } = useWeeklySettlementReport(from, to)

  return (
    <div className="flex flex-col gap-3">
      <DateRangeFields from={from} to={to} onFromChange={setFrom} onToChange={setTo} />

      {isLoading && <p className="text-sm text-slate-500">Loading…</p>}

      {report && (
        <>
          {report.entries.length === 0 ? (
            <EmptyState message="No active labourers." />
          ) : (
            <ul className="flex flex-col gap-2">
              {report.entries.map((entry) => (
                <li
                  key={entry.labourer_id}
                  className="flex items-center justify-between rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm shadow-sm"
                >
                  <div className="flex items-center gap-2">
                    <p className="font-medium text-slate-900">{entry.labourer_name}</p>
                    {entry.has_unpaid_earnings && (
                      <AlertIcon className="h-4 w-4 shrink-0 text-amber-600" />
                    )}
                  </div>
                  <span className="font-semibold tabular-nums text-slate-900">
                    ₹{entry.suggested_amount}
                  </span>
                </li>
              ))}
            </ul>
          )}

          <a
            href={weeklySettlementExportUrl(from, to)}
            target="_blank"
            rel="noopener noreferrer"
            className="text-center text-sm font-medium text-brand-600 active:text-brand-700"
          >
            Download CSV
          </a>
        </>
      )}
    </div>
  )
}
