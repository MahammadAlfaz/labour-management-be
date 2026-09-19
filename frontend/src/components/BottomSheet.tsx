import type { ReactNode } from 'react'
import { CloseIcon } from './icons'

interface BottomSheetProps {
  title: string
  onClose: () => void
  children: ReactNode
}

export default function BottomSheet({ title, onClose, children }: BottomSheetProps) {
  return (
    <div className="fixed inset-0 z-50 flex flex-col justify-end">
      <button
        type="button"
        aria-label="Close"
        onClick={onClose}
        className="absolute inset-0 cursor-pointer bg-slate-900/40"
      />
      <div className="relative max-h-[90vh] overflow-y-auto rounded-t-2xl bg-white p-4 pb-[max(1rem,env(safe-area-inset-bottom))] shadow-lg">
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-base font-semibold text-slate-900">{title}</h2>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close"
            className="flex h-9 w-9 cursor-pointer items-center justify-center rounded-full text-slate-500 transition-colors active:bg-slate-100"
          >
            <CloseIcon className="h-5 w-5" />
          </button>
        </div>
        {children}
      </div>
    </div>
  )
}
