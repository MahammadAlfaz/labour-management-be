import type { Site } from '../sites/api'
import { useAllSitesExpenses } from '../sites/useSites'
import { useAllSitesBoards } from './useBoard'

function money(value: number) {
  return `₹${value.toLocaleString('en-IN', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`
}

export default function TodaySummary({ sites, workDate }: { sites: Site[]; workDate: string }) {
  const siteIds = sites.map((s) => s.id)
  const { boards, isLoading: boardsLoading } = useAllSitesBoards(siteIds, workDate)
  const { expensesBySite, isLoading: expensesLoading } = useAllSitesExpenses(siteIds)

  if (sites.length === 0) return null

  const totalLabourers = boards.reduce((sum, board) => sum + board.length, 0)
  const wages = boards.reduce(
    (sum, board) => sum + board.reduce((s, entry) => s + Number(entry.record.amount), 0),
    0
  )
  const travel = boards.reduce(
    (sum, board) => sum + board.reduce((s, entry) => s + Number(entry.travel_expenses_total), 0),
    0
  )
  const otherCosts = expensesBySite.reduce(
    (sum, expenses) =>
      sum +
      expenses
        .filter((e) => e.expense_date === workDate)
        .reduce((s, e) => s + Number(e.amount), 0),
    0
  )
  const totalExpenditure = wages + travel + otherCosts
  const isLoading = boardsLoading || expensesLoading

  return (
    <dl className="grid grid-cols-2 gap-2">
      <div className="rounded-xl border border-slate-200 bg-white p-3">
        <dt className="text-xs text-slate-500">Workers sent</dt>
        <dd className="mt-1 font-semibold text-slate-900">{isLoading ? '…' : totalLabourers}</dd>
      </div>
      <div className="rounded-xl border border-slate-200 bg-white p-3">
        <dt className="text-xs text-slate-500">Total expenditure</dt>
        <dd className="mt-1 font-semibold text-slate-900">{isLoading ? '…' : money(totalExpenditure)}</dd>
      </div>
    </dl>
  )
}
