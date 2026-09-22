import { useMutation } from '@tanstack/react-query'
import { sendChatMessage, type ChatMessage } from './api'

export function useSendChatMessage() {
  return useMutation({
    mutationFn: (payload: { message: string; history: ChatMessage[] }) => sendChatMessage(payload),
  })
}
