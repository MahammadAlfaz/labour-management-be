import { useState } from 'react'
import Avatar from '../../components/Avatar'
import BottomSheet from '../../components/BottomSheet'
import { SearchIcon } from '../../components/icons'
import { ApiError } from '../../lib/apiClient'
import { useAssignLabourer, useAvailableLabourers } from './useBoard'

export default function AssignLabourerSheet({
  siteId,
  workDate,
  onClose,
}: {
  siteId: string
  workDate: string
  onClose: () => void
}) {
  const [search, setSearch] = useState('')
  const [error, setError] = useState<string | null>(null)
  const { data: labourers, isLoading } = useAvailableLabourers(workDate, search, true)
  const assignMutation = useAssignLabourer(siteId, workDate)

  async function handleAssign(labourerId: string) {
    setError(null)
    try {
      await assignMutation.mutateAsync(labourerId)
      onClose()
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Could not assign labourer')
    }
  }

  return (
    <BottomSheet title="Add labourer to today's crew" onClose={onClose}>
      <div className="flex flex-col gap-3">
        <div className="relative">
          <SearchIcon className="pointer-events-none absolute top-1/2 left-3 h-5 w-5 -translate-y-1/2 text-slate-400" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search labourers…"
            autoFocus
            className="w-full rounded-xl border border-slate-300 bg-white py-2.5 pr-3 pl-10 text-base text-slate-900 placeholder:text-slate-400 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/30"
          />
        </div>

        {error && <p className="text-sm text-rose-600">{error}</p>}
        {isLoading && <p className="text-sm text-slate-500">Loading…</p>}
        {labourers && labourers.length === 0 && (
          <p className="text-sm text-slate-500">No active labourers match.</p>
        )}

        <ul className="flex max-h-[60vh] flex-col gap-2 overflow-y-auto">
          {labourers?.map((labourer) => {
            const unavailable = Boolean(labourer.unavailable_reason)
            return (
              <li key={labourer.labourer_id}>
                <button
                  type="button"
                  disabled={unavailable || assignMutation.isPending}
                  onClick={() => handleAssign(labourer.labourer_id)}
                  className="flex w-full cursor-pointer items-center justify-between gap-3 rounded-xl border border-slate-200 bg-white p-3 text-left transition-colors active:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  <span className="flex min-w-0 items-center gap-3">
                    <Avatar photoUrl={labourer.labourer_photo_url} name={labourer.labourer_name} size="sm" />
                    <span className="truncate font-medium text-slate-900">{labourer.labourer_name}</span>
                  </span>
                  {unavailable && (
                    <span className="shrink-0 text-xs text-amber-700">{labourer.unavailable_reason}</span>
                  )}
                </button>
              </li>
            )
          })}
        </ul>
      </div>
    </BottomSheet>
  )
}
