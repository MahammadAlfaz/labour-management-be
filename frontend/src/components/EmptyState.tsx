import type { ReactNode } from 'react'
import { InboxIcon } from './icons'

export default function EmptyState({
  message,
  action,
}: {
  message: string
  action?: ReactNode
}) {
  return (
    <div className="flex flex-col items-center gap-3 rounded-2xl border border-dashed border-slate-300 p-8 text-center">
      <InboxIcon className="h-8 w-8 text-slate-400" />
      <p className="text-sm text-slate-500">{message}</p>
      {action}
    </div>
  )
}
