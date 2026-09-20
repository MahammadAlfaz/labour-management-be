import { useState } from 'react'
import EmptyState from '../../components/EmptyState'
import { PrimaryButton } from '../../components/form'
import { RulerIcon } from '../../components/icons'
import type { WallCalculation } from '../wall-calculator/api'
import WallCalculationFormSheet from '../wall-calculator/WallCalculationFormSheet'
import { useWallCalculations } from '../wall-calculator/useWallCalculations'

export default function SiteWallCalculationsPanel({ siteId }: { siteId: string }) {
  const [creating, setCreating] = useState(false)
  const [editing, setEditing] = useState<WallCalculation | null>(null)
  const { data: calculations, isLoading, isError } = useWallCalculations({ site_id: siteId })

  return (
    <section className="border-t border-slate-200 pt-4" aria-labelledby="site-wall-calculations-title">
      <h3 id="site-wall-calculations-title" className="text-base font-semibold text-slate-900">
        Wall calculations
      </h3>
      <p className="mt-1 text-sm text-slate-600">
        Compound wall measurements and costs recorded for this site.
      </p>

      {isLoading && <p className="mt-3 text-sm text-slate-500">Loading…</p>}
      {isError && <p className="mt-3 text-sm text-rose-600">Could not load calculations.</p>}

      {calculations && calculations.length === 0 && (
        <div className="mt-3">
          <EmptyState
            message="No wall calculations for this site yet."
            action={<PrimaryButton onClick={() => setCreating(true)}>New calculation</PrimaryButton>}
          />
        </div>
      )}

      {calculations && calculations.length > 0 && (
        <>
          <ul className="mt-3 flex flex-col gap-2">
            {calculations.map((calc) => (
              <li key={calc.id}>
                <button
                  type="button"
                  onClick={() => setEditing(calc)}
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
          <PrimaryButton onClick={() => setCreating(true)} className="mt-3 w-full">
            New calculation
          </PrimaryButton>
        </>
      )}

      {creating && <WallCalculationFormSheet initialSiteId={siteId} onClose={() => setCreating(false)} />}
      {editing && <WallCalculationFormSheet calculation={editing} onClose={() => setEditing(null)} />}
    </section>
  )
}
