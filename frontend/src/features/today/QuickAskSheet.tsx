import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import BottomSheet from '../../components/BottomSheet'
import { PrimaryButton, TextArea } from '../../components/form'

export default function QuickAskSheet({ onClose }: { onClose: () => void }) {
  const [draft, setDraft] = useState('')
  const navigate = useNavigate()

  function handleAsk() {
    const message = draft.trim()
    if (!message) return
    navigate('/assistant', { state: { initialMessage: message } })
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleAsk()
    }
  }

  return (
    <BottomSheet title="Ask the assistant" onClose={onClose}>
      <div className="flex flex-col gap-3">
        <p className="text-sm text-slate-600">
          Ask anything about labourers, sites, attendance, or payments.
        </p>
        <TextArea
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="e.g. How much do we owe Ramesh Kumar?"
          rows={2}
          className="resize-none"
          autoFocus
        />
        <PrimaryButton onClick={handleAsk} disabled={!draft.trim()} className="w-full">
          Ask
        </PrimaryButton>
      </div>
    </BottomSheet>
  )
}
