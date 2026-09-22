import { useEffect, useRef, useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { PrimaryButton, TextArea } from '../../components/form'
import { ApiError } from '../../lib/apiClient'
import type { ChatMessage } from './api'
import { useSendChatMessage } from './useChat'

const EXAMPLE_QUESTIONS = [
  'How much do we owe Ramesh Kumar right now?',
  "Who's working at Whitefield Site today?",
  "What's the profit on Site X so far?",
  'Who still has unpaid earnings this week?',
]

export default function ChatPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [draft, setDraft] = useState('')
  const [error, setError] = useState<string | null>(null)
  const sendMutation = useSendChatMessage()
  const listRef = useRef<HTMLDivElement>(null)
  const location = useLocation()
  const navigate = useNavigate()
  const autoSentRef = useRef(false)

  useEffect(() => {
    listRef.current?.scrollTo({ top: listRef.current.scrollHeight, behavior: 'smooth' })
  }, [messages, sendMutation.isPending])

  // Runs once on mount only -- intentionally ignores changes to location/navigate/messages,
  // since this is purely about consuming a one-time message passed in from QuickAskSheet.
  useEffect(() => {
    const initialMessage = (location.state as { initialMessage?: string } | null)?.initialMessage
    if (!initialMessage || autoSentRef.current) return
    autoSentRef.current = true
    // Clear the navigation state so a refresh or back-navigation doesn't resend it.
    navigate(location.pathname, { replace: true, state: null })
    sendMessage(initialMessage)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  async function sendMessage(text: string) {
    const message = text.trim()
    if (!message || sendMutation.isPending) return

    setError(null)
    const history = messages
    setMessages((prev) => [...prev, { role: 'user', content: message }])
    setDraft('')

    try {
      const result = await sendMutation.mutateAsync({ message, history })
      setMessages((prev) => [...prev, { role: 'model', content: result.reply }])
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Could not reach the assistant')
    }
  }

  async function handleSend() {
    await sendMessage(draft)
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="flex h-full flex-col gap-4 p-4">
      <div>
        <p className="text-sm font-medium text-brand-600">TOOLS</p>
        <h2 className="mt-1 text-2xl font-bold tracking-tight text-slate-900">Assistant</h2>
        <p className="mt-1 text-sm text-slate-600">
          Ask about labourers, sites, attendance, or payments. Read-only -- it can look things up
          but never changes anything.
        </p>
      </div>

      <div ref={listRef} className="flex flex-1 flex-col gap-3 overflow-y-auto">
        {messages.length === 0 && (
          <div className="flex flex-col gap-2 rounded-2xl border border-dashed border-slate-300 p-4">
            <p className="text-sm text-slate-500">Try asking things like:</p>
            <ul className="flex flex-col gap-1.5">
              {EXAMPLE_QUESTIONS.map((q) => (
                <li key={q}>
                  <button
                    type="button"
                    onClick={() => setDraft(q)}
                    className="cursor-pointer text-left text-sm text-brand-600 underline decoration-dotted active:text-brand-700"
                  >
                    {q}
                  </button>
                </li>
              ))}
            </ul>
          </div>
        )}

        {messages.map((m, i) => (
          <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div
              className={`max-w-[85%] rounded-2xl px-3.5 py-2.5 text-sm whitespace-pre-wrap ${
                m.role === 'user'
                  ? 'bg-brand-500 text-white'
                  : 'border border-slate-200 bg-white text-slate-900'
              }`}
            >
              {m.content}
            </div>
          </div>
        ))}

        {sendMutation.isPending && (
          <div className="flex justify-start">
            <div className="max-w-[85%] rounded-2xl border border-slate-200 bg-white px-3.5 py-2.5 text-sm text-slate-400">
              Thinking…
            </div>
          </div>
        )}
      </div>

      {error && <p className="text-sm text-rose-600">{error}</p>}

      <div className="flex items-end gap-2">
        <TextArea
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask a question…"
          rows={1}
          className="max-h-32 min-h-11 flex-1 resize-none"
        />
        <PrimaryButton onClick={handleSend} disabled={sendMutation.isPending || !draft.trim()}>
          Send
        </PrimaryButton>
      </div>
    </div>
  )
}
