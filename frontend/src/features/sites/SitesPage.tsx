import { useState } from 'react'
import EmptyState from '../../components/EmptyState'
import { BuildingIcon, PlusIcon } from '../../components/icons'
import { PrimaryButton } from '../../components/form'
import type { SiteStatus } from './api'
import SiteFormSheet from './SiteFormSheet'
import { useSites } from './useSites'

const FILTERS: { label: string; value: SiteStatus | 'all' }[] = [
  { label: 'Active', value: 'active' },
  { label: 'Closed', value: 'closed' },
  { label: 'All', value: 'all' },
]

export default function SitesPage() {
  const [status, setStatus] = useState<SiteStatus | 'all'>('active')
  const [creating, setCreating] = useState(false)
  const [editingId, setEditingId] = useState<string | null>(null)

  const { data: sites, isLoading, isError } = useSites({
    status: status === 'all' ? undefined : status,
  })

  // Derived from the live query cache so an open sheet reflects updates
  // like a freshly uploaded photo immediately.
  const editing = sites?.find((s) => s.id === editingId) ?? null

  return (
    <div className="flex flex-col gap-4 p-4">
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
      {isError && <p className="text-sm text-rose-600">Could not load sites.</p>}

      {sites && sites.length === 0 && (
        <EmptyState
          message="No sites yet."
          action={<PrimaryButton onClick={() => setCreating(true)}>Add your first site</PrimaryButton>}
        />
      )}

      <ul className="grid grid-cols-2 gap-3">
        {sites?.map((site) => (
          <li key={site.id}>
            <button
              type="button"
              onClick={() => setEditingId(site.id)}
              className="relative w-full cursor-pointer overflow-hidden rounded-2xl border border-slate-200 bg-white text-left shadow-sm transition-colors active:bg-slate-50"
            >
              <div className="flex aspect-square items-center justify-center bg-slate-100">
                {site.photo_url ? (
                  <img src={site.photo_url} alt="" className="h-full w-full object-cover" />
                ) : (
                  <BuildingIcon className="h-10 w-10 text-slate-300" />
                )}
              </div>
              <div className="p-2.5">
                <p className="truncate font-semibold text-slate-900">{site.name}</p>
                <p className="truncate text-xs text-slate-500">{site.location}</p>
              </div>
              {site.status === 'closed' && (
                <span className="absolute top-2 right-2 rounded-full bg-slate-800 px-2 py-0.5 text-xs font-medium text-white">
                  Closed
                </span>
              )}
            </button>
          </li>
        ))}
      </ul>

      <button
        type="button"
        onClick={() => setCreating(true)}
        aria-label="Add site"
        className="fixed right-4 bottom-24 flex h-14 w-14 cursor-pointer items-center justify-center rounded-full bg-brand-500 text-white shadow-lg transition-colors active:bg-brand-600"
      >
        <PlusIcon className="h-7 w-7" />
      </button>

      {creating && <SiteFormSheet onClose={() => setCreating(false)} />}
      {editing && <SiteFormSheet site={editing} onClose={() => setEditingId(null)} />}
    </div>
  )
}
