import { TextInput } from '../../components/form'

export default function DateRangeFields({
  from,
  to,
  onFromChange,
  onToChange,
}: {
  from: string
  to: string
  onFromChange: (value: string) => void
  onToChange: (value: string) => void
}) {
  return (
    <div className="flex gap-3">
      <label className="flex-1 text-sm">
        <span className="mb-1 block font-medium text-slate-700">From</span>
        <TextInput type="date" value={from} onChange={(e) => onFromChange(e.target.value)} />
      </label>
      <label className="flex-1 text-sm">
        <span className="mb-1 block font-medium text-slate-700">To</span>
        <TextInput type="date" value={to} onChange={(e) => onToChange(e.target.value)} />
      </label>
    </div>
  )
}
