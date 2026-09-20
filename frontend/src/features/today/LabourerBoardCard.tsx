import { useState } from 'react'
import Avatar from '../../components/Avatar'
import { CloseIcon } from '../../components/icons'
import { PrimaryButton } from '../../components/form'
import { ApiError } from '../../lib/apiClient'
import type { AttendanceStatus, BoardEntry } from './api'
import { useMarkAttendance, useUnassignLabourer } from './useBoard'
import WorkRecordDetailSheet from './WorkRecordDetailSheet'

const STATUS_OPTIONS: { value: AttendanceStatus; label: string }[] = [
  { value: 'FULL_DAY', label: 'Full' },
  { value: 'HALF_DAY', label: 'Half' },
  { value: 'ABSENT', label: 'Absent' },
]

const STATUS_STYLES: Record<AttendanceStatus, string> = {
  FULL_DAY: 'bg-emerald-600 text-white border-emerald-600',
  HALF_DAY: 'bg-amber-500 text-white border-amber-500',
  ABSENT: 'bg-rose-600 text-white border-rose-600',
}

const INACTIVE_CHIP = 'bg-white text-slate-600 border-slate-300 active:bg-slate-50'

export default function LabourerBoardCard({
  entry,
  siteId,
  workDate,
}: {
  entry: BoardEntry
  siteId: string
  workDate: string
}) {
  const { record } = entry
  const isPending = record.status === null
  const [pendingHalfDay, setPendingHalfDay] = useState(false)
  const [amount, setAmount] = useState(record.status === 'HALF_DAY' ? record.amount : '')
  const [error, setError] = useState<string | null>(null)
  const [showDetail, setShowDetail] = useState(false)

  const markMutation = useMarkAttendance(siteId, workDate)
  const unassignMutation = useUnassignLabourer(siteId, workDate)

  async function handleSelect(status: AttendanceStatus) {
    setError(null)
    if (status === 'HALF_DAY') {
      setPendingHalfDay(true)
      return
    }
    try {
      await markMutation.mutateAsync({ recordId: record.id, status })
      setPendingHalfDay(false)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Could not save attendance')
    }
  }

  async function handleSaveHalfDay() {
    setError(null)
    const value = Number(amount)
    if (!amount || Number.isNaN(value) || value <= 0) {
      setError('Enter the half-day amount')
      return
    }
    try {
      await markMutation.mutateAsync({ recordId: record.id, status: 'HALF_DAY', amount })
      setPendingHalfDay(false)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Could not save attendance')
    }
  }

  async function handleUnassign() {
    setError(null)
    if (
      !isPending &&
      !window.confirm(`Remove ${entry.labourer_name}'s attendance for this date? This can't be undone.`)
    ) {
      return
    }
    try {
      await unassignMutation.mutateAsync(record.id)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Could not remove')
    }
  }

  const disabled = markMutation.isPending
  const showHalfDayInput = pendingHalfDay || record.status === 'HALF_DAY'
  const canRemove = record.payment_id === null

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
      <div className="flex items-center justify-between gap-2">
        <div className="flex min-w-0 items-center gap-2">
          <Avatar photoUrl={entry.labourer_photo_url} name={entry.labourer_name} size="sm" />
          <p className="truncate font-semibold text-slate-900">{entry.labourer_name}</p>
          {isPending && (
            <span className="shrink-0 rounded-full bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-500">
              Not yet marked
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          {!isPending && (
            <button
              type="button"
              onClick={() => setShowDetail(true)}
              className="cursor-pointer text-sm font-semibold tabular-nums text-slate-500 underline decoration-dotted active:text-slate-700"
            >
              ₹{record.amount}
            </button>
          )}
          {canRemove && (
            <button
              type="button"
              onClick={handleUnassign}
              disabled={unassignMutation.isPending}
              aria-label={isPending ? "Remove from today's crew" : 'Remove attendance record'}
              className="flex h-8 w-8 cursor-pointer items-center justify-center rounded-full text-slate-400 transition-colors active:bg-slate-100 disabled:opacity-50"
            >
              <CloseIcon className="h-4 w-4" />
            </button>
          )}
        </div>
      </div>

      <div className="mt-3 flex gap-2">
        {STATUS_OPTIONS.map((option) => {
          const isActive = record.status === option.value && !pendingHalfDay
          return (
            <button
              key={option.value}
              type="button"
              disabled={disabled}
              onClick={() => handleSelect(option.value)}
              className={`min-h-11 flex-1 cursor-pointer rounded-xl border text-sm font-semibold transition-colors disabled:cursor-not-allowed disabled:opacity-50 ${
                isActive ? STATUS_STYLES[option.value] : INACTIVE_CHIP
              }`}
            >
              {option.label}
            </button>
          )
        })}
      </div>

      {showHalfDayInput && !disabled && (
        <div className="mt-3 flex items-end gap-2">
          <label className="flex-1 text-sm">
            <span className="mb-1 block font-medium text-slate-700">Amount (₹)</span>
            <input
              type="number"
              inputMode="decimal"
              min="0"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              placeholder="e.g. 400"
              className="w-full rounded-xl border border-slate-300 px-3 py-2.5 text-base text-slate-900 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/30"
            />
          </label>
          <PrimaryButton onClick={handleSaveHalfDay} disabled={markMutation.isPending}>
            Save
          </PrimaryButton>
        </div>
      )}

      {error && <p className="mt-2 text-sm text-rose-600">{error}</p>}

      {showDetail && !isPending && (
        <WorkRecordDetailSheet
          recordId={record.id}
          labourerName={entry.labourer_name}
          onClose={() => setShowDetail(false)}
        />
      )}
    </div>
  )
}
