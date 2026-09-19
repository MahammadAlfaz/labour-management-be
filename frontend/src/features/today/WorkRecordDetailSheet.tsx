import { useState } from 'react'
import BottomSheet from '../../components/BottomSheet'
import {
  DangerButton,
  Field,
  PrimaryButton,
  Select,
  SecondaryButton,
  TextInput,
} from '../../components/form'
import { ApiError } from '../../lib/apiClient'
import type { Expense, ExpenseCategory } from './api'
import {
  useAddExpense,
  useAdjustAmount,
  useDeleteExpense,
  useUpdateExpense,
  useWorkRecordDetail,
} from './useWorkRecordDetail'

const CATEGORIES: ExpenseCategory[] = ['PETROL', 'BUS', 'AUTO', 'OTHER']

export default function WorkRecordDetailSheet({
  recordId,
  labourerName,
  onClose,
}: {
  recordId: string
  labourerName: string
  onClose: () => void
}) {
  const { data: detail, isLoading } = useWorkRecordDetail(recordId)

  const [showAdjust, setShowAdjust] = useState(false)
  const [adjustAmount, setAdjustAmount] = useState('')
  const [adjustReason, setAdjustReason] = useState('')
  const [adjustError, setAdjustError] = useState<string | null>(null)
  const adjustMutation = useAdjustAmount(recordId)

  const [showExpenseForm, setShowExpenseForm] = useState(false)
  const [editingExpense, setEditingExpense] = useState<Expense | null>(null)
  const [category, setCategory] = useState<ExpenseCategory>('PETROL')
  const [expenseAmount, setExpenseAmount] = useState('')
  const [note, setNote] = useState('')
  const [expenseError, setExpenseError] = useState<string | null>(null)
  const addExpenseMutation = useAddExpense(recordId)
  const updateExpenseMutation = useUpdateExpense(recordId)
  const deleteExpenseMutation = useDeleteExpense(recordId)
  const isSavingExpense = addExpenseMutation.isPending || updateExpenseMutation.isPending

  function openAddExpenseForm() {
    setEditingExpense(null)
    setCategory('PETROL')
    setExpenseAmount('')
    setNote('')
    setShowExpenseForm(true)
  }

  function openEditExpenseForm(expense: Expense) {
    setEditingExpense(expense)
    setCategory(expense.category)
    setExpenseAmount(expense.amount)
    setNote(expense.note ?? '')
    setShowExpenseForm(true)
  }

  async function handleAdjust() {
    setAdjustError(null)
    const value = Number(adjustAmount)
    if (!adjustAmount || Number.isNaN(value) || value < 0) {
      setAdjustError('Enter a valid amount')
      return
    }
    try {
      await adjustMutation.mutateAsync({ amount: adjustAmount, reason: adjustReason || undefined })
      setShowAdjust(false)
      setAdjustAmount('')
      setAdjustReason('')
    } catch (err) {
      setAdjustError(err instanceof ApiError ? err.message : 'Could not adjust amount')
    }
  }

  async function handleSaveExpense() {
    setExpenseError(null)
    const value = Number(expenseAmount)
    if (!expenseAmount || Number.isNaN(value) || value <= 0) {
      setExpenseError('Enter a valid amount')
      return
    }
    try {
      if (editingExpense) {
        await updateExpenseMutation.mutateAsync({
          expenseId: editingExpense.id,
          input: { category, amount: expenseAmount, note: note || null },
        })
      } else {
        await addExpenseMutation.mutateAsync({ category, amount: expenseAmount, note: note || undefined })
      }
      setShowExpenseForm(false)
      setEditingExpense(null)
      setExpenseAmount('')
      setNote('')
    } catch (err) {
      setExpenseError(err instanceof ApiError ? err.message : 'Could not save expense')
    }
  }

  return (
    <BottomSheet title={labourerName} onClose={onClose}>
      {isLoading || !detail ? (
        <p className="text-sm text-slate-500">Loading…</p>
      ) : (
        <div className="flex flex-col gap-4">
          <div className="rounded-xl bg-slate-50 p-3">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs font-medium tracking-wide text-slate-500 uppercase">
                  {detail.status ? detail.status.replace('_', ' ') : 'Not yet marked'} wage
                </p>
                <p className="text-xl font-semibold tabular-nums text-slate-900">
                  ₹{detail.amount}
                  {detail.amount !== detail.original_amount && (
                    <span className="ml-2 text-sm font-normal text-slate-400 line-through">
                      ₹{detail.original_amount}
                    </span>
                  )}
                </p>
                {detail.adjustment_reason && (
                  <p className="text-xs text-slate-500">Adjusted: {detail.adjustment_reason}</p>
                )}
              </div>
              {!showAdjust && (
                <button
                  type="button"
                  onClick={() => {
                    setAdjustAmount(detail.amount)
                    setShowAdjust(true)
                  }}
                  className="cursor-pointer text-sm font-medium text-brand-600 active:text-brand-700"
                >
                  Adjust
                </button>
              )}
            </div>

            {showAdjust && (
              <div className="mt-3 flex flex-col gap-2 border-t border-slate-200 pt-3">
                <Field label="Adjusted amount (₹)" htmlFor="adjust-amount">
                  <TextInput
                    id="adjust-amount"
                    type="number"
                    inputMode="decimal"
                    min="0"
                    value={adjustAmount}
                    onChange={(e) => setAdjustAmount(e.target.value)}
                    autoFocus
                  />
                </Field>
                <Field label="Reason (optional)" htmlFor="adjust-reason">
                  <TextInput
                    id="adjust-reason"
                    value={adjustReason}
                    onChange={(e) => setAdjustReason(e.target.value)}
                    placeholder="e.g. Left 2 hours early"
                  />
                </Field>
                {adjustError && <p className="text-sm text-rose-600">{adjustError}</p>}
                <div className="flex gap-2">
                  <PrimaryButton onClick={handleAdjust} disabled={adjustMutation.isPending} className="flex-1">
                    Save
                  </PrimaryButton>
                  <SecondaryButton onClick={() => setShowAdjust(false)} className="flex-1">
                    Cancel
                  </SecondaryButton>
                </div>
              </div>
            )}
          </div>

          <div>
            <div className="mb-2 flex items-center justify-between">
              <h3 className="text-sm font-semibold text-slate-900">Travel expenses</h3>
              {!showExpenseForm && (
                <button
                  type="button"
                  onClick={openAddExpenseForm}
                  className="cursor-pointer text-sm font-medium text-brand-600 active:text-brand-700"
                >
                  + Add expense
                </button>
              )}
            </div>

            {showExpenseForm && (
              <div className="mb-3 flex flex-col gap-3 rounded-xl border border-slate-200 p-3">
                <p className="text-sm font-medium text-slate-700">
                  {editingExpense ? 'Edit expense' : 'New expense'}
                </p>
                <Field label="Category" htmlFor="expense-category">
                  <Select
                    id="expense-category"
                    value={category}
                    onChange={(e) => setCategory(e.target.value as ExpenseCategory)}
                  >
                    {CATEGORIES.map((c) => (
                      <option key={c} value={c}>
                        {c.charAt(0) + c.slice(1).toLowerCase()}
                      </option>
                    ))}
                  </Select>
                </Field>
                <Field label="Amount (₹)" htmlFor="expense-amount">
                  <TextInput
                    id="expense-amount"
                    type="number"
                    inputMode="decimal"
                    min="0"
                    value={expenseAmount}
                    onChange={(e) => setExpenseAmount(e.target.value)}
                    autoFocus
                  />
                </Field>
                <Field label="Note (optional)" htmlFor="expense-note">
                  <TextInput id="expense-note" value={note} onChange={(e) => setNote(e.target.value)} />
                </Field>
                {expenseError && <p className="text-sm text-rose-600">{expenseError}</p>}
                <div className="flex gap-2">
                  <PrimaryButton onClick={handleSaveExpense} disabled={isSavingExpense} className="flex-1">
                    Save
                  </PrimaryButton>
                  <SecondaryButton
                    onClick={() => {
                      setShowExpenseForm(false)
                      setEditingExpense(null)
                    }}
                    className="flex-1"
                  >
                    Cancel
                  </SecondaryButton>
                </div>
              </div>
            )}

            {detail.expenses.length === 0 && !showExpenseForm && (
              <p className="text-sm text-slate-500">No expenses recorded.</p>
            )}

            <ul className="flex flex-col gap-2">
              {detail.expenses.map((expense) => (
                <ExpenseRow
                  key={expense.id}
                  expense={expense}
                  onEdit={() => openEditExpenseForm(expense)}
                  onDelete={() => deleteExpenseMutation.mutate(expense.id)}
                  isDeleting={deleteExpenseMutation.isPending}
                />
              ))}
            </ul>
          </div>

          <div className="flex items-center justify-between border-t border-slate-200 pt-4">
            <span className="text-sm font-medium text-slate-600">Total for the day</span>
            <span className="text-lg font-semibold tabular-nums text-slate-900">
              ₹{detail.total_earnings}
            </span>
          </div>
        </div>
      )}
    </BottomSheet>
  )
}

function ExpenseRow({
  expense,
  onEdit,
  onDelete,
  isDeleting,
}: {
  expense: Expense
  onEdit: () => void
  onDelete: () => void
  isDeleting: boolean
}) {
  return (
    <li className="flex items-center justify-between rounded-xl border border-slate-200 px-3 py-2 text-sm">
      <button type="button" onClick={onEdit} className="min-w-0 flex-1 cursor-pointer text-left">
        <p className="font-medium text-slate-900">
          {expense.category.charAt(0) + expense.category.slice(1).toLowerCase()}
        </p>
        {expense.note && <p className="truncate text-xs text-slate-500">{expense.note}</p>}
      </button>
      <div className="flex items-center gap-3">
        <span className="font-semibold tabular-nums text-slate-900">₹{expense.amount}</span>
        <DangerButton
          onClick={onDelete}
          disabled={isDeleting}
          className="min-h-0 border-none px-2 py-1 text-xs"
        >
          Remove
        </DangerButton>
      </div>
    </li>
  )
}
