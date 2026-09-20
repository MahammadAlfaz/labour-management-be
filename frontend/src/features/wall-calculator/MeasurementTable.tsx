import { PlusIcon, CloseIcon } from '../../components/icons'
import type { MeasurementLine } from './api'

function blankRow(): MeasurementLine {
  return { raw_text: '', length: '', quantity: 1, confidence: 'high', included: true }
}

export default function MeasurementTable({
  measurements,
  onChange,
}: {
  measurements: MeasurementLine[]
  onChange: (next: MeasurementLine[]) => void
}) {
  function updateRow(index: number, patch: Partial<MeasurementLine>) {
    onChange(measurements.map((row, i) => (i === index ? { ...row, ...patch } : row)))
  }

  function removeRow(index: number) {
    onChange(measurements.filter((_, i) => i !== index))
  }

  return (
    <div className="flex flex-col gap-2">
      {measurements.length === 0 && (
        <p className="rounded-xl border border-dashed border-slate-300 p-3 text-center text-sm text-slate-500">
          No measurements yet. Upload an image or add a row manually.
        </p>
      )}

      {measurements.map((row, index) => (
        <div
          key={index}
          className={`rounded-xl border p-2.5 ${
            row.confidence === 'low' ? 'border-amber-300 bg-amber-50' : 'border-slate-200 bg-white'
          }`}
        >
          <div className="flex items-start gap-2">
            <input
              type="checkbox"
              checked={row.included}
              onChange={(e) => updateRow(index, { included: e.target.checked })}
              aria-label="Include this row"
              className="mt-3 h-4 w-4 shrink-0 cursor-pointer accent-brand-500"
            />

            <div className="flex min-w-0 flex-1 flex-col gap-1.5">
              {row.raw_text && (
                <p className="truncate text-xs text-slate-500">
                  {row.raw_text}
                  {row.confidence === 'low' && (
                    <span className="ml-1.5 rounded-full bg-amber-200 px-1.5 py-0.5 text-[10px] font-semibold text-amber-800">
                      Verify
                    </span>
                  )}
                </p>
              )}
              <div className="flex gap-2">
                <input
                  type="number"
                  inputMode="decimal"
                  step="0.001"
                  min="0"
                  value={row.length}
                  onChange={(e) => updateRow(index, { length: e.target.value })}
                  placeholder="Length"
                  aria-label="Length"
                  className="min-h-10 w-full min-w-0 rounded-lg border border-slate-300 px-2.5 py-1.5 text-base focus:border-brand-500 focus:outline-none"
                />
                <span className="flex items-center text-slate-400">×</span>
                <input
                  type="number"
                  inputMode="numeric"
                  min="1"
                  step="1"
                  value={row.quantity}
                  onChange={(e) => updateRow(index, { quantity: Number(e.target.value) })}
                  placeholder="Qty"
                  aria-label="Quantity"
                  className="min-h-10 w-20 shrink-0 rounded-lg border border-slate-300 px-2.5 py-1.5 text-base focus:border-brand-500 focus:outline-none"
                />
              </div>
            </div>

            <button
              type="button"
              onClick={() => removeRow(index)}
              aria-label="Remove row"
              className="mt-1 flex h-8 w-8 shrink-0 cursor-pointer items-center justify-center rounded-full text-slate-400 transition-colors active:bg-slate-100"
            >
              <CloseIcon className="h-4 w-4" />
            </button>
          </div>
        </div>
      ))}

      <button
        type="button"
        onClick={() => onChange([...measurements, blankRow()])}
        className="flex min-h-10 cursor-pointer items-center justify-center gap-1.5 rounded-xl border border-dashed border-slate-300 py-2 text-sm font-medium text-slate-600 transition-colors active:bg-slate-50"
      >
        <PlusIcon className="h-4 w-4" /> Add row
      </button>
    </div>
  )
}
