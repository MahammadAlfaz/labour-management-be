import { useState } from 'react'
import EmptyState from '../../components/EmptyState'
import { useSites } from '../sites/useSites'
import DateRangeFields from './DateRangeFields'
import { siteAttendanceExportUrl } from './api'
import { useSiteAttendanceReport } from './useReports'

function monthAgoIso() {
  const d = new Date()
  d.setDate(d.getDate() - 30)
  return d.toISOString().slice(0, 10)
}

function todayIso() {
  return new Date().toISOString().slice(0, 10)
}

export default function SiteAttendanceView() {
  const [siteId, setSiteId] = useState<string | null>(null)
  const [from, setFrom] = useState(monthAgoIso())
  const [to, setTo] = useState(todayIso())

  const { data: sites } = useSites({})
  const { data: report, isLoading } = useSiteAttendanceReport(siteId, from, to)

  if (!siteId) {
    return (
      <ul className="flex flex-col gap-2">
        {sites?.map((site) => (
          <li key={site.id}>
            <button
              type="button"
              onClick={() => setSiteId(site.id)}
              className="w-full cursor-pointer rounded-2xl border border-slate-200 bg-white p-4 text-left font-semibold text-slate-900 shadow-sm active:bg-slate-50"
            >
              {site.name}
            </button>
          </li>
        ))}
      </ul>
    )
  }

  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <p className="text-lg font-semibold text-slate-900">{report?.site_name ?? '…'}</p>
        <button
          type="button"
          onClick={() => setSiteId(null)}
          className="cursor-pointer text-sm font-medium text-brand-600 active:text-brand-700"
        >
          Change
        </button>
      </div>

      <DateRangeFields from={from} to={to} onFromChange={setFrom} onToChange={setTo} />

      {isLoading && <p className="text-sm text-slate-500">Loading…</p>}

      {report && (
        <>
          <div className="flex items-center justify-between rounded-xl bg-slate-50 p-4 text-sm">
            <span className="text-slate-600">Total paid out</span>
            <span className="font-semibold tabular-nums text-slate-900">₹{report.total_amount}</span>
          </div>

          {report.entries.length === 0 ? (
            <EmptyState message="No attendance records in this period." />
          ) : (
            <ul className="flex flex-col gap-2">
              {report.entries.map((e) => (
                <li
                  key={`${e.labourer_id}-${e.work_date}`}
                  className="flex items-center justify-between rounded-xl border border-slate-200 px-3 py-2 text-sm"
                >
                  <div>
                    <p className="text-slate-700">{e.labourer_name}</p>
                    <p className="text-xs text-slate-500">
                      {e.work_date} · {e.status ? e.status.replace('_', ' ') : 'Not yet marked'}
                    </p>
                  </div>
                  <span className="font-semibold tabular-nums text-slate-900">₹{e.amount}</span>
                </li>
              ))}
            </ul>
          )}

          <a
            href={siteAttendanceExportUrl(siteId, from, to)}
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
