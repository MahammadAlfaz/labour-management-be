const SIZE_CLASSES = {
  sm: 'h-9 w-9 text-xs',
  md: 'h-11 w-11 text-sm',
  lg: 'h-16 w-16 text-lg',
} as const

export default function Avatar({
  photoUrl,
  name,
  size = 'md',
  className = '',
}: {
  photoUrl?: string | null
  name: string
  size?: keyof typeof SIZE_CLASSES
  className?: string
}) {
  return (
    <div
      className={`flex shrink-0 items-center justify-center overflow-hidden rounded-full bg-slate-100 ${SIZE_CLASSES[size]} ${className}`}
    >
      {photoUrl ? (
        <img src={photoUrl} alt="" className="h-full w-full object-cover" />
      ) : (
        <span className="font-semibold text-slate-400">{name.charAt(0).toUpperCase()}</span>
      )}
    </div>
  )
}
