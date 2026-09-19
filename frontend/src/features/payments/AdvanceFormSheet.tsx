import { useState } from 'react'
import BottomSheet from '../../components/BottomSheet'
import { Field, PrimaryButton, TextInput } from '../../components/form'
import { ApiError } from '../../lib/apiClient'
import { useCreateAdvance } from './usePayments'

function todayIso() {
  return new Date().toISOString().slice(0, 10)
}

export default function AdvanceFormSheet({
  labourerId,
  onClose,
}: {
  labourerId: string
  onClose: () => void
}) {
  const [amount, setAmount] = useState('')
  const [givenAt, setGivenAt] = useState(todayIso())
  const [note, setNote] = useState('')
  const [error, setError] = useState<string | null>(null)
  const createAdvance = useCreateAdvance(labourerId)

  async function handleSave() {
    setError(null)
    const value = Number(amount)
    if (!amount || Number.isNaN(value) || value <= 0) {
      setError('Enter a valid amount')
      return
    }
    try {
      await createAdvance.mutateAsync({ amount, given_at: givenAt, note: note || undefined })
      onClose()
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Could not record advance')
    }
  }

  return (
    <BottomSheet title="Record advance" onClose={onClose}>
      <div className="flex flex-col gap-4">
        <Field label="Amount (₹)" htmlFor="advance-amount">
          <TextInput
            id="advance-amount"
            type="number"
            inputMode="decimal"
            min="0"
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
            autoFocus
          />
        </Field>
        <Field label="Given on" htmlFor="advance-date">
          <TextInput
            id="advance-date"
            type="date"
            value={givenAt}
            onChange={(e) => setGivenAt(e.target.value)}
          />
        </Field>
        <Field label="Note (optional)" htmlFor="advance-note">
          <TextInput id="advance-note" value={note} onChange={(e) => setNote(e.target.value)} />
        </Field>
        {error && <p className="text-sm text-rose-600">{error}</p>}
        <PrimaryButton onClick={handleSave} disabled={createAdvance.isPending} className="w-full">
          {createAdvance.isPending ? 'Saving…' : 'Record advance'}
        </PrimaryButton>
      </div>
    </BottomSheet>
  )
}
