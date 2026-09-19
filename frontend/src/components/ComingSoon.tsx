export default function ComingSoon({ title, phase }: { title: string; phase: string }) {
  return (
    <div className="p-4">
      <h2 className="text-base font-semibold text-gray-900">{title}</h2>
      <div className="mt-4 rounded-xl border border-dashed border-gray-300 p-6 text-center text-sm text-gray-500">
        {title} will be implemented in {phase}.
      </div>
    </div>
  )
}
