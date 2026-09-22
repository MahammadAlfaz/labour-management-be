import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { SparkleIcon } from '../../components/icons'

export default function QuickAskSheet({ onClose }: { onClose: () => void }) {
  const [draft, setDraft] = useState('')
  const navigate = useNavigate()

  function handleAsk() {
    const message = draft.trim()
    if (!message) return
    navigate('/assistant', { state: { initialMessage: message } })
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === 'Enter') {
      e.preventDefault()
      handleAsk()
    } else if (e.key === 'Escape') {
      onClose()
    }
  }

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label="Ask the assistant"
      onClick={onClose}
      className="fixed inset-0 z-50 flex items-start justify-center bg-slate-900/40 px-4 pt-24"
    >
      <div
        onClick={(e) => e.stopPropagation()}
        className="flex w-full max-w-md items-center gap-3 rounded-full bg-slate-900 px-4 py-3.5 shadow-2xl"
      >
        <SparkleIcon className="h-5 w-5 shrink-0 text-brand-500" />
        <input
          autoFocus
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="What can I help you with today?"
          className="w-full min-w-0 bg-transparent text-base text-white placeholder:text-slate-400 focus:outline-none"
        />
      </div>
    </div>
  )
}
