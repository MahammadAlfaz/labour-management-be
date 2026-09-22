import { apiFetch } from '../../lib/apiClient'

export interface ChatMessage {
  role: 'user' | 'model'
  content: string
}

export function sendChatMessage(payload: { message: string; history: ChatMessage[] }) {
  return apiFetch<{ reply: string }>('/chat/message', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}
