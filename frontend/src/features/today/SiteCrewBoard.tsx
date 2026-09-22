import { useState } from 'react'
import EmptyState from '../../components/EmptyState'
import { PrimaryButton, SecondaryButton } from '../../components/form'
import { BuildingIcon, ChevronRightIcon, PlusIcon } from '../../components/icons'
import type { Site } from '../sites/api'
import { useSiteExpenses } from '../sites/useSites'
import AssignLabourerSheet from './AssignLabourerSheet'
import LabourerBoardCard from './LabourerBoardCard'
import { useBoard } from './useBoard'
import SiteExpenseSheet from './SiteExpenseSheet'

function money(value: number) {
  return `₹${value.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
}

export default function SiteCrewBoard({
  site,
  workDate,
  onBack,
}: {
  site: Site
  workDate: string
  onBack: () => void
}) {
  const [showAssignSheet, setShowAssignSheet] = useState(false)
  const [showExpenseSheet, setShowExpenseSheet] = useState(false)
  const { data: board, isLoading, isError } = useBoard(site.id, workDate)
  const { data: siteExpenses } = useSiteExpenses(site.id)

  const totalLabourers = board?.length ?? 0
  const totalAmount = board?.reduce((sum, entry) => sum + Number(entry.record.amount), 0) ?? 0
  const todaysExtraCost =
    siteExpenses
      ?.filter((expense) => expense.expense_date === workDate)
      .reduce((sum, expense) => sum + Number(expense.amount), 0) ?? 0

  return (
    <div className="flex flex-col gap-4">
      <button
        type="button"
        onClick={onBack}
        className="flex cursor-pointer items-center gap-3 rounded-2xl border border-slate-200 bg-white p-3 text-left shadow-sm active:bg-slate-50"
      >
        <ChevronRightIcon className="h-5 w-5 shrink-0 rotate-180 text-slate-400" />
        <div className="flex h-10 w-10 shrink-0 items-center justify-center overflow-hidden rounded-xl bg-slate-100">
          {site.photo_url ? (
            <img src={site.photo_url} alt="" className="h-full w-full object-cover" />
          ) : (
            <BuildingIcon className="h-5 w-5 text-slate-300" />
          )}
        </div>
        <div className="min-w-0">
          <p className="truncate font-semibold text-slate-900">{site.name}</p>
          <p className="truncate text-xs text-slate-500">Change site</p>
        </div>
      </button>

      {board && (
        <dl className="grid grid-cols-3 gap-2">
          <DailyStat label="Labourers" value={String(totalLabourers)} />
          <DailyStat label="Wages today" value={money(totalAmount)} />
          <DailyStat label="Other costs" value={money(todaysExtraCost)} />
        </dl>
      )}

      <PrimaryButton onClick={() => setShowAssignSheet(true)} className="flex w-full items-center justify-center gap-1.5">
        <PlusIcon className="h-5 w-5" />
        Add labourer
      </PrimaryButton>
      <SecondaryButton onClick={() => setShowExpenseSheet(true)} className="w-full">
        Add site cost
      </SecondaryButton>

      {isLoading && <p className="text-sm text-slate-500">Loading today's crew…</p>}
      {isError && <p className="text-sm text-rose-600">Could not load the attendance board.</p>}

      {board && board.length === 0 && (
        <EmptyState message="No one's been added to this site today yet. Tap 'Add labourer' above to get started." />
      )}

      {board && board.length > 0 && (
        <ul className="flex flex-col gap-3">
          {board.map((entry) => (
            <li key={entry.labourer_id}>
              <LabourerBoardCard entry={entry} siteId={site.id} workDate={workDate} />
            </li>
          ))}
        </ul>
      )}

      {showAssignSheet && (
        <AssignLabourerSheet
          siteId={site.id}
          workDate={workDate}
          onClose={() => setShowAssignSheet(false)}
        />
      )}
      {showExpenseSheet && <SiteExpenseSheet siteId={site.id} workDate={workDate} onClose={() => setShowExpenseSheet(false)} />}
    </div>
  )
}

function DailyStat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-3">
      <dt className="truncate text-xs text-slate-500">{label}</dt>
      <dd className="mt-1 truncate font-semibold text-slate-900">{value}</dd>
    </div>
  )
}
