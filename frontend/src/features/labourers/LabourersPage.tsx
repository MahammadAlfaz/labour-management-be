import { useState } from 'react'
import EmptyState from '../../components/EmptyState'
import { PlusIcon, SearchIcon, UsersIcon } from '../../components/icons'
import { PrimaryButton } from '../../components/form'
import type { LabourerStatus } from './api'
import LabourerDetailSheet from './LabourerDetailSheet'
import LabourerFormSheet from './LabourerFormSheet'
import { useLabourers } from './useLabourers'

const FILTERS: { label: string; value: LabourerStatus | 'all' }[] = [
  { label: 'Active', value: 'active' },
  { label: 'Inactive', value: 'inactive' },
  { label: 'All', value: 'all' },
]

export default function LabourersPage() {
  const [status, setStatus] = useState<LabourerStatus | 'all'>('active')
  const [search, setSearch] = useState('')
  const [creating, setCreating] = useState(false)
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [editingId, setEditingId] = useState<string | null>(null)

  const { data: labourers, isLoading, isError } = useLabourers({
    status: status === 'all' ? undefined : status,
    search: search.trim() || undefined,
  })

  // Derived from the live query cache (not a stale snapshot) so an open
  // sheet reflects updates like a freshly uploaded photo immediately.
  const selected = labourers?.find((l) => l.id === selectedId) ?? null
  const editing = labourers?.find((l) => l.id === editingId) ?? null

  return (
    <div className="flex flex-col gap-4 p-4">
      <div className="relative">
        <SearchIcon className="pointer-events-none absolute top-1/2 left-3 h-5 w-5 -translate-y-1/2 text-slate-400" />
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search labourers…"
          className="w-full rounded-xl border border-slate-300 bg-white py-2.5 pr-3 pl-10 text-base text-slate-900 placeholder:text-slate-400 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/30"
        />
      </div>

      <div className="flex gap-2">
        {FILTERS.map((filter) => (
          <button
            key={filter.value}
            type="button"
            onClick={() => setStatus(filter.value)}
            className={`cursor-pointer rounded-full border px-3.5 py-1.5 text-sm font-medium transition-colors ${
              status === filter.value
                ? 'border-slate-800 bg-slate-800 text-white'
                : 'border-slate-300 bg-white text-slate-600 active:bg-slate-100'
            }`}
          >
            {filter.label}
          </button>
        ))}
      </div>

      {isLoading && <p className="text-sm text-slate-500">Loading…</p>}
      {isError && <p className="text-sm text-rose-600">Could not load labourers.</p>}

      {labourers && labourers.length === 0 && (
        <EmptyState
          message={search ? 'No labourers match your search.' : 'No labourers yet.'}
          action={
            !search && (
              <PrimaryButton onClick={() => setCreating(true)}>Add your first labourer</PrimaryButton>
            )
          }
        />
      )}

      <ul className="grid grid-cols-2 gap-3">
        {labourers?.map((labourer) => (
          <li key={labourer.id}>
            <button
              type="button"
              onClick={() => setSelectedId(labourer.id)}
              className="relative w-full cursor-pointer overflow-hidden rounded-2xl border border-slate-200 bg-white text-left shadow-sm transition-colors active:bg-slate-50"
            >
              <div className="flex aspect-square items-center justify-center bg-slate-100">
                {labourer.photo_url ? (
                  <img src={labourer.photo_url} alt="" className="h-full w-full object-cover" />
                ) : (
                  <UsersIcon className="h-10 w-10 text-slate-300" />
                )}
              </div>
              <div className="p-2.5">
                <p className="truncate font-semibold text-slate-900">{labourer.name}</p>
                <p className="truncate text-xs text-slate-500">
                  {labourer.work_category || 'General'}
                </p>
              </div>
              {labourer.status === 'inactive' && (
                <span className="absolute top-2 right-2 rounded-full bg-slate-800 px-2 py-0.5 text-xs font-medium text-white">
                  Inactive
                </span>
              )}
            </button>
          </li>
        ))}
      </ul>

      <button
        type="button"
        onClick={() => setCreating(true)}
        aria-label="Add labourer"
        className="fixed right-4 bottom-24 flex h-14 w-14 cursor-pointer items-center justify-center rounded-full bg-brand-500 text-white shadow-lg transition-colors active:bg-brand-600"
      >
        <PlusIcon className="h-7 w-7" />
      </button>

      {creating && <LabourerFormSheet onClose={() => setCreating(false)} />}
      {editing && (
        <LabourerFormSheet
          labourer={editing}
          onClose={() => {
            setEditingId(null)
            setSelectedId(null)
          }}
        />
      )}
      {selected && !editing && (
        <LabourerDetailSheet
          labourer={selected}
          onClose={() => setSelectedId(null)}
          onEdit={() => setEditingId(selected.id)}
        />
      )}
    </div>
  )
}
