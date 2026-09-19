import { useState } from 'react'
import BottomSheet from '../../components/BottomSheet'
import { Field, PrimaryButton, TextInput } from '../../components/form'
import { ApiError } from '../../lib/apiClient'
import { useCreateDeduction } from './usePayments'

export default function DeductionFormSheet({
  labourerId,
  onClose,
}: {
  labourerId: string
  onClose: () => void
}) {
  const [amount, setAmount] = useState('')
  const [reason, setReason] = useState('')
  const [error, setError] = useState<string | null>(null)
  const createDeduction = useCreateDeduction(labourerId)

  async function handleSave() {
    setError(null)
    const value = Number(amount)
    if (!amount || Number.isNaN(value) || value <= 0) {
      setError('Enter a valid amount')
      return
    }
    if (!reason.trim()) {
      setError('A reason is required for deductions')
      return
    }
    try {
      await createDeduction.mutateAsync({ amount, reason: reason.trim() })
      onClose()
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Could not record deduction')
    }
  }

  return (
    <BottomSheet title="Record deduction" onClose={onClose}>
      <div className="flex flex-col gap-4">
        <Field label="Amount (₹)" htmlFor="deduction-amount">
          <TextInput
            id="deduction-amount"
            type="number"
            inputMode="decimal"
            min="0"
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
            autoFocus
          />
        </Field>
        <Field label="Reason" htmlFor="deduction-reason">
          <TextInput
            id="deduction-reason"
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            placeholder="e.g. Tool damage"
          />
        </Field>
        {error && <p className="text-sm text-rose-600">{error}</p>}
        <PrimaryButton onClick={handleSave} disabled={createDeduction.isPending} className="w-full">
          {createDeduction.isPending ? 'Saving…' : 'Record deduction'}
        </PrimaryButton>
      </div>
    </BottomSheet>
  )
}
