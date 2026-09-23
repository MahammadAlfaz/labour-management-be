import { useState } from 'react'
import EmptyState from '../../components/EmptyState'
import { SearchIcon } from '../../components/icons'
import { toLocalIsoDate, todayIso } from '../../lib/date'
import { useLabourers } from '../labourers/useLabourers'
import DateRangeFields from './DateRangeFields'
import { labourerHistoryExportUrl } from './api'
import { useLabourerHistory } from './useReports'

function monthAgoIso() {
  const d = new Date()
  d.setDate(d.getDate() - 30)
  return toLocalIsoDate(d)
}

export default function LabourerHistoryView() {
  const [search, setSearch] = useState('')
  const [labourerId, setLabourerId] = useState<string | null>(null)
  const [from, setFrom] = useState(monthAgoIso())
  const [to, setTo] = useState(todayIso())

  const { data: labourers } = useLabourers({ search: search.trim() || undefined })
  const selectedLabourer = labourers?.find((l) => l.id === labourerId) ?? null
  const { data: report, isLoading } = useLabourerHistory(labourerId, from, to)

  if (!labourerId) {
    return (
      <div className="flex flex-col gap-3">
        <div className="relative">
          <SearchIcon className="pointer-events-none absolute top-1/2 left-3 h-5 w-5 -translate-y-1/2 text-slate-400" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search a labourer…"
            className="w-full rounded-xl border border-slate-300 bg-white py-2.5 pr-3 pl-10 text-base text-slate-900 placeholder:text-slate-400 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/30"
          />
        </div>
        <ul className="flex flex-col gap-2">
          {labourers?.map((labourer) => (
            <li key={labourer.id}>
              <button
                type="button"
                onClick={() => setLabourerId(labourer.id)}
                className="w-full cursor-pointer rounded-2xl border border-slate-200 bg-white p-4 text-left font-semibold text-slate-900 shadow-sm active:bg-slate-50"
              >
                {labourer.name}
              </button>
            </li>
          ))}
        </ul>
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <p className="text-lg font-semibold text-slate-900">{selectedLabourer?.name}</p>
        <button
          type="button"
          onClick={() => setLabourerId(null)}
          className="cursor-pointer text-sm font-medium text-brand-600 active:text-brand-700"
        >
          Change
        </button>
      </div>

      <DateRangeFields from={from} to={to} onFromChange={setFrom} onToChange={setTo} />

      {isLoading && <p className="text-sm text-slate-500">Loading…</p>}

      {report && (
        <>
          <div className="rounded-xl bg-slate-50 p-4">
            <div className="flex items-center justify-between text-sm">
              <span className="text-slate-600">Total earnings</span>
              <span className="font-semibold tabular-nums text-slate-900">₹{report.total_earnings}</span>
            </div>
            <div className="mt-1 flex items-center justify-between text-sm">
              <span className="text-slate-600">Outstanding balance</span>
              <span className="font-semibold tabular-nums text-slate-900">
                ₹{report.outstanding_balance}
              </span>
            </div>
          </div>

          {report.work_records.length === 0 ? (
            <EmptyState message="No attendance records in this period." />
          ) : (
            <ul className="flex flex-col gap-2">
              {report.work_records.map((r) => (
                <li
                  key={r.id}
                  className="flex items-center justify-between rounded-xl border border-slate-200 px-3 py-2 text-sm"
                >
                  <div>
                    <p className="text-slate-700">
                      {r.work_date} · {r.site_name}
                    </p>
                    <p className="text-xs text-slate-500">
                      {r.status ? r.status.replace('_', ' ') : 'Not yet marked'}
                      {!r.paid && ' · unpaid'}
                    </p>
                  </div>
                  <span className="font-semibold tabular-nums text-slate-900">
                    ₹{(Number(r.amount) + Number(r.expenses_total)).toFixed(2)}
                  </span>
                </li>
              ))}
            </ul>
          )}

          <a
            href={labourerHistoryExportUrl(labourerId, from, to)}
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
