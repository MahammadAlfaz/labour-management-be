import { BuildingIcon } from '../../components/icons'
import type { Site } from '../sites/api'
import { useSiteExpenses } from '../sites/useSites'
import { useBoard } from './useBoard'

function money(value: number) {
  return `₹${value.toLocaleString('en-IN', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`
}

export default function SiteGrid({
  sites,
  workDate,
  onSelect,
}: {
  sites: Site[]
  workDate: string
  onSelect: (siteId: string) => void
}) {
  return (
    <div className="grid grid-cols-2 gap-3">
      {sites.map((site) => (
        <SiteGridCard key={site.id} site={site} workDate={workDate} onSelect={onSelect} />
      ))}
    </div>
  )
}

function SiteGridCard({
  site,
  workDate,
  onSelect,
}: {
  site: Site
  workDate: string
  onSelect: (siteId: string) => void
}) {
  const { data: board } = useBoard(site.id, workDate)
  const { data: siteExpenses } = useSiteExpenses(site.id)

  const totalLabourers = board?.length ?? 0
  const wages = board?.reduce((sum, entry) => sum + Number(entry.record.amount), 0) ?? 0
  const travel = board?.reduce((sum, entry) => sum + Number(entry.travel_expenses_total), 0) ?? 0
  const otherCosts =
    siteExpenses
      ?.filter((expense) => expense.expense_date === workDate)
      .reduce((sum, expense) => sum + Number(expense.amount), 0) ?? 0
  const totalCost = wages + travel + otherCosts

  return (
    <button
      type="button"
      onClick={() => onSelect(site.id)}
      className="cursor-pointer overflow-hidden rounded-2xl border border-slate-200 bg-white text-left shadow-sm transition-colors active:bg-slate-50"
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
        {board && (
          <div className="mt-1.5 flex items-center justify-between gap-1 border-t border-slate-100 pt-1.5">
            <span className="text-xs text-slate-600">
              {totalLabourers} labour{totalLabourers === 1 ? '' : 'ers'}
            </span>
            <span className="text-xs font-semibold text-slate-900">{money(totalCost)}</span>
          </div>
        )}
        {otherCosts > 0 && (
          <p className="mt-0.5 text-xs text-slate-500">+{money(otherCosts)} other</p>
        )}
      </div>
    </button>
  )
}
