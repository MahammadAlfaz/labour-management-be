import { useState } from 'react'
import Avatar from '../../components/Avatar'
import BottomSheet from '../../components/BottomSheet'
import { PrimaryButton } from '../../components/form'
import { CheckCircleIcon, SearchIcon } from '../../components/icons'
import { useAssignLabourers, useAvailableLabourers } from './useBoard'

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
  const [selectedIds, setSelectedIds] = useState<string[]>([])
  const [error, setError] = useState<string | null>(null)
  const { data: labourers, isLoading } = useAvailableLabourers(workDate, search, true)
  const assignMutation = useAssignLabourers(siteId, workDate)

  function toggle(labourerId: string) {
    setSelectedIds((prev) =>
      prev.includes(labourerId) ? prev.filter((id) => id !== labourerId) : [...prev, labourerId]
    )
  }

  async function handleAssignSelected() {
    if (selectedIds.length === 0) return
    setError(null)
    const idsToAssign = [...selectedIds]
    const { failed } = await assignMutation.mutateAsync(idsToAssign)

    if (failed.length === 0) {
      onClose()
      return
    }

    const failedIds = new Set(failed.map((f) => f.labourerId))
    setSelectedIds(idsToAssign.filter((id) => failedIds.has(id)))
    const names = failed
      .map((f) => labourers?.find((l) => l.labourer_id === f.labourerId)?.labourer_name ?? 'someone')
      .join(', ')
    setError(
      failed.length === idsToAssign.length
        ? `Could not add ${names}.`
        : `Added the rest, but couldn't add ${names}.`
    )
  }

  return (
    <BottomSheet title="Add labourers to today's crew" onClose={onClose}>
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
            const selected = selectedIds.includes(labourer.labourer_id)
            return (
              <li key={labourer.labourer_id}>
                <button
                  type="button"
                  disabled={unavailable || assignMutation.isPending}
                  onClick={() => toggle(labourer.labourer_id)}
                  className={`flex w-full cursor-pointer items-center justify-between gap-3 rounded-xl border p-3 text-left transition-colors disabled:cursor-not-allowed disabled:opacity-50 ${
                    selected
                      ? 'border-brand-500 bg-brand-50'
                      : 'border-slate-200 bg-white active:bg-slate-50'
                  }`}
                >
                  <span className="flex min-w-0 items-center gap-3">
                    <Avatar photoUrl={labourer.labourer_photo_url} name={labourer.labourer_name} size="sm" />
                    <span className="truncate font-medium text-slate-900">{labourer.labourer_name}</span>
                  </span>
                  {unavailable ? (
                    <span className="shrink-0 text-xs text-amber-700">{labourer.unavailable_reason}</span>
                  ) : (
                    <CheckCircleIcon
                      className={`h-6 w-6 shrink-0 ${selected ? 'text-brand-500' : 'text-slate-300'}`}
                    />
                  )}
                </button>
              </li>
            )
          })}
        </ul>

        <PrimaryButton
          onClick={handleAssignSelected}
          disabled={selectedIds.length === 0 || assignMutation.isPending}
          className="w-full"
        >
          {assignMutation.isPending
            ? 'Adding…'
            : selectedIds.length === 0
              ? 'Select labourers to add'
              : `Add ${selectedIds.length} labourer${selectedIds.length === 1 ? '' : 's'}`}
        </PrimaryButton>
      </div>
    </BottomSheet>
  )
}
