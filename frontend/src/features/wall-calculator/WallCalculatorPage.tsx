import { useState } from 'react'
import EmptyState from '../../components/EmptyState'
import { PlusIcon, RulerIcon } from '../../components/icons'
import { PrimaryButton } from '../../components/form'
import { useWallCalculations } from './useWallCalculations'
import WallCalculationFormSheet from './WallCalculationFormSheet'

export default function WallCalculatorPage() {
  const [creating, setCreating] = useState(false)
  const [editingId, setEditingId] = useState<string | null>(null)

  const { data: calculations, isLoading, isError } = useWallCalculations()
  const editing = calculations?.find((c) => c.id === editingId) ?? null

  return (
    <div className="flex flex-col gap-4 p-4">
      <div>
        <p className="text-sm font-medium text-brand-600">TOOLS</p>
        <h2 className="mt-1 text-2xl font-bold tracking-tight text-slate-900">Wall calculator</h2>
        <p className="mt-1 text-sm text-slate-600">
          Upload a measurement sheet, enter height/breadth per layer, and get the total area and cost.
        </p>
      </div>

      {isLoading && <p className="text-sm text-slate-500">Loading…</p>}
      {isError && <p className="text-sm text-rose-600">Could not load calculations.</p>}

      {calculations && calculations.length === 0 && (
        <EmptyState
          message="No calculations yet."
          action={<PrimaryButton onClick={() => setCreating(true)}>New calculation</PrimaryButton>}
        />
      )}

      <ul className="flex flex-col gap-2">
        {calculations?.map((calc) => (
          <li key={calc.id}>
            <button
              type="button"
              onClick={() => setEditingId(calc.id)}
              className="flex w-full cursor-pointer items-center gap-3 rounded-2xl border border-slate-200 bg-white p-3 text-left shadow-sm transition-colors active:bg-slate-50"
            >
              <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-slate-100 text-slate-600">
                <RulerIcon className="h-5 w-5" />
              </span>
              <span className="min-w-0 flex-1">
                <span className="block truncate font-semibold text-slate-900">
                  {calc.title || 'Untitled calculation'}
                </span>
                <span className="block text-sm text-slate-500">
                  {Number(calc.total_area).toFixed(2)} sq.ft · ₹{Number(calc.total_cost).toFixed(2)}
                </span>
              </span>
            </button>
          </li>
        ))}
      </ul>

      <button
        type="button"
        onClick={() => setCreating(true)}
        aria-label="New calculation"
        className="fixed right-4 bottom-24 flex h-14 w-14 cursor-pointer items-center justify-center rounded-full bg-brand-500 text-white shadow-lg transition-colors active:bg-brand-600"
      >
        <PlusIcon className="h-7 w-7" />
      </button>

      {creating && <WallCalculationFormSheet onClose={() => setCreating(false)} />}
      {editing && <WallCalculationFormSheet calculation={editing} onClose={() => setEditingId(null)} />}
    </div>
  )
}
