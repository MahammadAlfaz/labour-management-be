import { useState } from 'react'
import BottomSheet from '../../components/BottomSheet'
import { Field, PrimaryButton, Select, TextInput } from '../../components/form'
import { ApiError } from '../../lib/apiClient'
import { useCreateSiteExpense } from '../sites/useSites'

export default function SiteExpenseSheet({ siteId, workDate, onClose }: { siteId: string; workDate: string; onClose: () => void }) {
  const [category, setCategory] = useState<'FOOD' | 'OTHER'>('FOOD')
  const [amount, setAmount] = useState('')
  const [note, setNote] = useState('')
  const [error, setError] = useState<string | null>(null)
  const createExpense = useCreateSiteExpense(siteId)

  async function save() {
    setError(null)
    if (!amount || Number(amount) <= 0) {
      setError('Enter a valid amount.')
      return
    }
    try {
      await createExpense.mutateAsync({ category, amount, expense_date: workDate, note: note.trim() || undefined })
      onClose()
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Could not record the site cost.')
    }
  }

  return <BottomSheet title="Record site cost" onClose={onClose}>
    <div className="flex flex-col gap-4">
      <p className="text-sm text-slate-600">This is recorded for {workDate} and included in the site’s costs and profit.</p>
      <Field label="Type" htmlFor="today-site-cost-type"><Select id="today-site-cost-type" value={category} onChange={(e) => setCategory(e.target.value as 'FOOD' | 'OTHER')}><option value="FOOD">Labour food</option><option value="OTHER">Other site cost</option></Select></Field>
      <Field label="Amount (₹)" htmlFor="today-site-cost-amount"><TextInput id="today-site-cost-amount" type="number" inputMode="decimal" min="0.01" step="0.01" value={amount} onChange={(e) => setAmount(e.target.value)} autoFocus /></Field>
      <Field label="Note (optional)" htmlFor="today-site-cost-note"><TextInput id="today-site-cost-note" value={note} onChange={(e) => setNote(e.target.value)} placeholder="e.g. Lunch for crew" /></Field>
      {error && <p className="text-sm text-rose-600">{error}</p>}
      <PrimaryButton onClick={save} disabled={createExpense.isPending} className="w-full">{createExpense.isPending ? 'Recording…' : 'Record site cost'}</PrimaryButton>
    </div>
  </BottomSheet>
}
