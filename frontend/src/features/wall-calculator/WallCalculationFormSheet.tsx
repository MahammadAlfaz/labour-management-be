import { type ChangeEvent, useRef, useState } from 'react'
import BottomSheet from '../../components/BottomSheet'
import { DangerButton, Field, PrimaryButton, Select, SecondaryButton, TextInput } from '../../components/form'
import { ApiError } from '../../lib/apiClient'
import { useSites } from '../sites/useSites'
import type { LayerInput, MeasurementLine, WallCalculation } from './api'
import LayerEditor from './LayerEditor'
import MeasurementTable from './MeasurementTable'
import {
  useCreateWallCalculation,
  useDeleteWallCalculation,
  useExtractMeasurements,
  useUpdateWallCalculation,
} from './useWallCalculations'

function sumIncluded(measurements: MeasurementLine[]): number {
  return measurements.reduce((total, row) => {
    if (!row.included) return total
    const length = Number(row.length)
    const quantity = Number(row.quantity)
    if (!length || !quantity) return total
    return total + length * quantity
  }, 0)
}

function formatDecimal(value: number): string {
  return String(Math.round(value * 10000) / 10000)
}

export default function WallCalculationFormSheet({
  calculation,
  initialSiteId,
  onClose,
}: {
  calculation?: WallCalculation | null
  initialSiteId?: string
  onClose: () => void
}) {
  const isEdit = Boolean(calculation)
  const cameraInputRef = useRef<HTMLInputElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const { data: sites } = useSites({})
  const [siteId, setSiteId] = useState(calculation?.site_id ?? initialSiteId ?? '')
  const [title, setTitle] = useState(calculation?.title ?? '')
  const [sourceImagePath, setSourceImagePath] = useState(calculation?.source_image_path ?? null)
  const [measurements, setMeasurements] = useState<MeasurementLine[]>(calculation?.measurements ?? [])
  const [totalMeasurement, setTotalMeasurement] = useState(calculation?.total_measurement ?? '')
  const [layers, setLayers] = useState<LayerInput[]>(
    calculation?.layers.map((l) => ({ label: l.label, height: l.height, breadth: l.breadth })) ?? [
      { label: '', height: '', breadth: '' },
    ]
  )
  const [rate, setRate] = useState(calculation?.rate_per_sqft ?? '')
  const [warnings, setWarnings] = useState<string[]>([])
  const [error, setError] = useState<string | null>(null)

  const extractMutation = useExtractMeasurements()
  const createMutation = useCreateWallCalculation()
  const updateMutation = useUpdateWallCalculation()
  const deleteMutation = useDeleteWallCalculation()
  const isSaving = createMutation.isPending || updateMutation.isPending

  async function handleFileChange(e: ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    e.target.value = ''
    if (!file) return

    setError(null)
    setWarnings([])
    try {
      const result = await extractMutation.mutateAsync(file)
      setSourceImagePath(result.source_image_path)
      const rows: MeasurementLine[] = result.measurements.map((m) => ({
        raw_text: m.raw_text,
        length: m.length,
        quantity: m.quantity,
        confidence: m.confidence,
        included: true,
      }))
      setMeasurements(rows)
      setTotalMeasurement(formatDecimal(sumIncluded(rows)))
      setWarnings(result.warnings)
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : 'Could not read the image. You can still enter measurements manually.'
      )
    }
  }

  function handleMeasurementsChange(next: MeasurementLine[]) {
    setMeasurements(next)
  }

  function recalculateTotal() {
    setTotalMeasurement(formatDecimal(sumIncluded(measurements)))
  }

  const totalMeasurementNumber = Number(totalMeasurement) || 0
  const totalAreaPreview = layers.reduce((total, layer) => {
    const height = Number(layer.height)
    const breadth = Number(layer.breadth)
    if (!totalMeasurementNumber || !height || !breadth) return total
    return total + totalMeasurementNumber * height * breadth
  }, 0)
  const totalCostPreview = totalAreaPreview * (Number(rate) || 0)

  async function handleSave() {
    setError(null)

    if (!totalMeasurement || Number(totalMeasurement) <= 0) {
      setError('Enter a total measurement greater than zero')
      return
    }
    if (!rate || Number(rate) <= 0) {
      setError('Enter a rate per sq.ft greater than zero')
      return
    }
    if (layers.length === 0) {
      setError('Add at least one layer')
      return
    }
    for (const layer of layers) {
      if (!layer.height || Number(layer.height) <= 0 || !layer.breadth || Number(layer.breadth) <= 0) {
        setError('Each layer needs a height and breadth greater than zero')
        return
      }
    }

    const payload = {
      site_id: siteId || null,
      title: title.trim() || null,
      source_image_path: sourceImagePath,
      measurements,
      total_measurement: totalMeasurement,
      layers,
      rate_per_sqft: rate,
    }

    try {
      if (isEdit && calculation) {
        await updateMutation.mutateAsync({ id: calculation.id, input: payload })
      } else {
        await createMutation.mutateAsync(payload)
      }
      onClose()
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Could not save the calculation')
    }
  }

  async function handleDelete() {
    if (!calculation) return
    await deleteMutation.mutateAsync(calculation.id)
    onClose()
  }

  return (
    <BottomSheet title={isEdit ? 'Edit calculation' : 'New wall calculation'} onClose={onClose}>
      <div className="flex flex-col gap-4">
        <Field label="Title (optional)" htmlFor="wc-title">
          <TextInput
            id="wc-title"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="e.g. North boundary wall"
            autoFocus
          />
        </Field>

        <Field label="Site (optional)" htmlFor="wc-site">
          <Select id="wc-site" value={siteId} onChange={(e) => setSiteId(e.target.value)}>
            <option value="">No site</option>
            {sites?.map((site) => (
              <option key={site.id} value={site.id}>
                {site.name}
                {site.status === 'closed' ? ' (closed)' : ''}
              </option>
            ))}
          </Select>
        </Field>

        <div className="flex flex-col gap-2">
          <p className="text-sm font-medium text-slate-700">Measurement sheet</p>
          <div className="flex gap-2">
            <SecondaryButton
              onClick={() => cameraInputRef.current?.click()}
              disabled={extractMutation.isPending}
              className="flex-1"
            >
              {extractMutation.isPending ? 'Reading…' : 'Take photo'}
            </SecondaryButton>
            <SecondaryButton
              onClick={() => fileInputRef.current?.click()}
              disabled={extractMutation.isPending}
              className="flex-1"
            >
              {extractMutation.isPending ? 'Reading…' : 'Choose file'}
            </SecondaryButton>
          </div>
          {/* capture forces the camera directly on mobile; the plain input
              opens the file browser / photo library on both mobile and desktop. */}
          <input
            ref={cameraInputRef}
            type="file"
            accept="image/*"
            capture="environment"
            className="hidden"
            onChange={handleFileChange}
          />
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            className="hidden"
            onChange={handleFileChange}
          />
          {warnings.length > 0 && (
            <ul className="rounded-xl bg-amber-50 p-2.5 text-xs text-amber-800">
              {warnings.map((w, i) => (
                <li key={i}>{w}</li>
              ))}
            </ul>
          )}
        </div>

        <MeasurementTable measurements={measurements} onChange={handleMeasurementsChange} />

        <Field label="Total measurement" htmlFor="wc-total-measurement">
          <div className="flex gap-2">
            <TextInput
              id="wc-total-measurement"
              type="number"
              inputMode="decimal"
              step="0.001"
              min="0"
              value={totalMeasurement}
              onChange={(e) => setTotalMeasurement(e.target.value)}
            />
            <SecondaryButton onClick={recalculateTotal} className="shrink-0 px-3">
              Recalculate
            </SecondaryButton>
          </div>
        </Field>

        <div className="flex flex-col gap-2">
          <p className="text-sm font-medium text-slate-700">Layers</p>
          <LayerEditor layers={layers} totalMeasurement={totalMeasurementNumber} onChange={setLayers} />
        </div>

        <Field label="Rate per sq.ft (₹)" htmlFor="wc-rate">
          <TextInput
            id="wc-rate"
            type="number"
            inputMode="decimal"
            step="0.01"
            min="0"
            value={rate}
            onChange={(e) => setRate(e.target.value)}
          />
        </Field>

        <div className="rounded-xl bg-slate-50 p-3">
          <div className="flex justify-between text-sm text-slate-600">
            <span>Total area</span>
            <span className="font-medium text-slate-900">{totalAreaPreview.toFixed(2)} sq.ft</span>
          </div>
          <div className="mt-1 flex justify-between text-sm text-slate-600">
            <span>Total cost</span>
            <span className="font-semibold text-slate-900">₹{totalCostPreview.toFixed(2)}</span>
          </div>
        </div>

        {error && <p className="text-sm text-rose-600">{error}</p>}

        <PrimaryButton onClick={handleSave} disabled={isSaving} className="w-full">
          {isSaving ? 'Saving…' : isEdit ? 'Save changes' : 'Save calculation'}
        </PrimaryButton>

        {isEdit && (
          <DangerButton onClick={handleDelete} disabled={deleteMutation.isPending} className="w-full">
            {deleteMutation.isPending ? 'Deleting…' : 'Delete calculation'}
          </DangerButton>
        )}
      </div>
    </BottomSheet>
  )
}
