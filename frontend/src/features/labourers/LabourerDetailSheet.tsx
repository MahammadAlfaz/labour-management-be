import { useState } from 'react'
import BottomSheet from '../../components/BottomSheet'
import { DangerButton, Field, PrimaryButton, SecondaryButton, TextInput } from '../../components/form'
import PhotoUploader from '../../components/PhotoUploader'
import { ApiError } from '../../lib/apiClient'
import { todayIso } from '../../lib/date'
import type { Labourer } from './api'
import {
  useAddWage,
  useRemoveLabourerPhoto,
  useSetLabourerActive,
  useUploadLabourerPhoto,
  useWageHistory,
} from './useLabourers'

export default function LabourerDetailSheet({
  labourer,
  onClose,
  onEdit,
}: {
  labourer: Labourer
  onClose: () => void
  onEdit: () => void
}) {
  const { data: wages, isLoading } = useWageHistory(labourer.id)
  const addWageMutation = useAddWage(labourer.id)
  const setActiveMutation = useSetLabourerActive()
  const uploadPhotoMutation = useUploadLabourerPhoto()
  const removePhotoMutation = useRemoveLabourerPhoto()

  const [showWageForm, setShowWageForm] = useState(false)
  const [dailyWage, setDailyWage] = useState('')
  const [effectiveFrom, setEffectiveFrom] = useState(todayIso())
  const [wageError, setWageError] = useState<string | null>(null)

  const currentWage = wages?.[0]

  async function handleAddWage() {
    setWageError(null)
    const amount = Number(dailyWage)
    if (!dailyWage || Number.isNaN(amount) || amount <= 0) {
      setWageError('Enter a valid wage amount')
      return
    }
    try {
      await addWageMutation.mutateAsync({ daily_wage: dailyWage, effective_from: effectiveFrom })
      setShowWageForm(false)
      setDailyWage('')
    } catch (err) {
      setWageError(err instanceof ApiError ? err.message : 'Could not add wage')
    }
  }

  return (
    <BottomSheet title={labourer.name} onClose={onClose}>
      <div className="flex flex-col gap-4">
        <PhotoUploader
          photoUrl={labourer.photo_url}
          onUpload={(file) => uploadPhotoMutation.mutateAsync({ id: labourer.id, file })}
          onRemove={() => removePhotoMutation.mutateAsync(labourer.id)}
          isUploading={uploadPhotoMutation.isPending}
          isRemoving={removePhotoMutation.isPending}
          label="photo"
        />

        <div className="flex flex-wrap items-center gap-2 text-sm text-slate-600">
          <span
            className={`rounded-full px-2.5 py-1 font-medium ${
              labourer.status === 'active'
                ? 'bg-emerald-100 text-emerald-700'
                : 'bg-slate-200 text-slate-600'
            }`}
          >
            {labourer.status === 'active' ? 'Active' : 'Inactive'}
          </span>
          {labourer.work_category && <span>{labourer.work_category}</span>}
          {labourer.phone && <span>· {labourer.phone}</span>}
          <span className="capitalize">· {labourer.payment_frequency} pay</span>
        </div>

        <div className="rounded-xl bg-slate-50 p-3">
          <p className="text-xs font-medium tracking-wide text-slate-500 uppercase">Current wage</p>
          <p className="mt-0.5 text-xl font-semibold tabular-nums text-slate-900">
            {currentWage ? `₹${currentWage.daily_wage}` : 'Not set'}
          </p>
          {currentWage && (
            <p className="text-xs text-slate-500">since {currentWage.effective_from}</p>
          )}
        </div>

        <div>
          <div className="mb-2 flex items-center justify-between">
            <h3 className="text-sm font-semibold text-slate-900">Wage history</h3>
            {!showWageForm && (
              <button
                type="button"
                onClick={() => setShowWageForm(true)}
                className="cursor-pointer text-sm font-medium text-brand-600 active:text-brand-700"
              >
                + Add wage
              </button>
            )}
          </div>

          {showWageForm && (
            <div className="mb-3 flex flex-col gap-3 rounded-xl border border-slate-200 p-3">
              <Field label="Daily wage (₹)" htmlFor="wage-amount">
                <TextInput
                  id="wage-amount"
                  type="number"
                  inputMode="decimal"
                  min="0"
                  value={dailyWage}
                  onChange={(e) => setDailyWage(e.target.value)}
                  placeholder="e.g. 800"
                  autoFocus
                />
              </Field>
              <Field label="Effective from" htmlFor="wage-date">
                <TextInput
                  id="wage-date"
                  type="date"
                  value={effectiveFrom}
                  onChange={(e) => setEffectiveFrom(e.target.value)}
                />
              </Field>
              {wageError && <p className="text-sm text-rose-600">{wageError}</p>}
              <div className="flex gap-2">
                <PrimaryButton
                  onClick={handleAddWage}
                  disabled={addWageMutation.isPending}
                  className="flex-1"
                >
                  {addWageMutation.isPending ? 'Saving…' : 'Save wage'}
                </PrimaryButton>
                <SecondaryButton onClick={() => setShowWageForm(false)} className="flex-1">
                  Cancel
                </SecondaryButton>
              </div>
            </div>
          )}

          {isLoading && <p className="text-sm text-slate-500">Loading…</p>}
          {wages && wages.length === 0 && !showWageForm && (
            <p className="text-sm text-slate-500">No wage set yet.</p>
          )}
          {wages && wages.length > 0 && (
            <ul className="flex flex-col gap-2">
              {wages.map((wage) => (
                <li
                  key={wage.id}
                  className="flex items-center justify-between rounded-xl border border-slate-200 px-3 py-2 text-sm"
                >
                  <span className="text-slate-600">since {wage.effective_from}</span>
                  <span className="font-semibold tabular-nums text-slate-900">
                    ₹{wage.daily_wage}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className="flex flex-col gap-2 border-t border-slate-200 pt-4">
          <div className="flex gap-2">
            <SecondaryButton onClick={onEdit} className="flex-1">
              Edit details
            </SecondaryButton>
            {labourer.status === 'active' ? (
              <DangerButton
                onClick={() => {
                  if (
                    window.confirm(
                      `Remove ${labourer.name} from the active labour list? Their history is kept, and you can bring them back anytime from the Inactive filter.`
                    )
                  ) {
                    setActiveMutation.mutate({ id: labourer.id, isActive: false })
                  }
                }}
                disabled={setActiveMutation.isPending}
                className="flex-1"
              >
                Remove labourer
              </DangerButton>
            ) : (
              <PrimaryButton
                onClick={() => setActiveMutation.mutate({ id: labourer.id, isActive: true })}
                disabled={setActiveMutation.isPending}
                className="flex-1"
              >
                Add back as active
              </PrimaryButton>
            )}
          </div>
          {labourer.status === 'active' ? (
            <p className="text-xs text-slate-500">
              Removing hides them from site assignment and new attendance, without deleting past
              records.
            </p>
          ) : (
            <p className="text-xs text-slate-500">
              This labourer is inactive and won't appear when assigning to a site.
            </p>
          )}
        </div>
      </div>
    </BottomSheet>
  )
}
