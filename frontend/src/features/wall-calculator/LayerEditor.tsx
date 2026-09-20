import { PlusIcon, CloseIcon } from '../../components/icons'
import type { LayerInput } from './api'

function blankLayer(): LayerInput {
  return { label: '', height: '', breadth: '' }
}

function layerArea(totalMeasurement: number, layer: LayerInput): number | null {
  const height = Number(layer.height)
  const breadth = Number(layer.breadth)
  if (!totalMeasurement || !height || !breadth) return null
  return totalMeasurement * height * breadth
}

export default function LayerEditor({
  layers,
  totalMeasurement,
  onChange,
}: {
  layers: LayerInput[]
  totalMeasurement: number
  onChange: (next: LayerInput[]) => void
}) {
  function updateLayer(index: number, patch: Partial<LayerInput>) {
    onChange(layers.map((layer, i) => (i === index ? { ...layer, ...patch } : layer)))
  }

  function removeLayer(index: number) {
    onChange(layers.filter((_, i) => i !== index))
  }

  return (
    <div className="flex flex-col gap-2">
      {layers.map((layer, index) => {
        const area = layerArea(totalMeasurement, layer)
        return (
          <div key={index} className="rounded-xl border border-slate-200 bg-white p-2.5">
            <div className="flex items-start gap-2">
              <div className="flex min-w-0 flex-1 flex-col gap-1.5">
                <input
                  type="text"
                  value={layer.label ?? ''}
                  onChange={(e) => updateLayer(index, { label: e.target.value })}
                  placeholder={`Layer ${index + 1} label (optional)`}
                  className="min-h-9 w-full rounded-lg border border-slate-200 px-2.5 py-1 text-sm text-slate-600 focus:border-brand-500 focus:outline-none"
                />
                <div className="flex items-center gap-2">
                  <input
                    type="number"
                    inputMode="decimal"
                    step="0.01"
                    min="0"
                    value={layer.height}
                    onChange={(e) => updateLayer(index, { height: e.target.value })}
                    placeholder="Height"
                    aria-label="Height"
                    className="min-h-10 w-full min-w-0 rounded-lg border border-slate-300 px-2.5 py-1.5 text-base focus:border-brand-500 focus:outline-none"
                  />
                  <span className="text-slate-400">×</span>
                  <input
                    type="number"
                    inputMode="decimal"
                    step="0.01"
                    min="0"
                    value={layer.breadth}
                    onChange={(e) => updateLayer(index, { breadth: e.target.value })}
                    placeholder="Breadth"
                    aria-label="Breadth"
                    className="min-h-10 w-full min-w-0 rounded-lg border border-slate-300 px-2.5 py-1.5 text-base focus:border-brand-500 focus:outline-none"
                  />
                </div>
                {area !== null && (
                  <p className="text-xs text-slate-500">
                    Area: <span className="font-medium text-slate-700">{area.toFixed(2)} sq.ft</span>
                  </p>
                )}
              </div>

              <button
                type="button"
                onClick={() => removeLayer(index)}
                disabled={layers.length <= 1}
                aria-label="Remove layer"
                className="mt-1 flex h-8 w-8 shrink-0 cursor-pointer items-center justify-center rounded-full text-slate-400 transition-colors active:bg-slate-100 disabled:cursor-not-allowed disabled:opacity-30"
              >
                <CloseIcon className="h-4 w-4" />
              </button>
            </div>
          </div>
        )
      })}

      <button
        type="button"
        onClick={() => onChange([...layers, blankLayer()])}
        className="flex min-h-10 cursor-pointer items-center justify-center gap-1.5 rounded-xl border border-dashed border-slate-300 py-2 text-sm font-medium text-slate-600 transition-colors active:bg-slate-50"
      >
        <PlusIcon className="h-4 w-4" /> Add layer
      </button>
    </div>
  )
}
