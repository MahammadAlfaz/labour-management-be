import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import type { ExpenseCategory } from './api'
import {
  addExpense,
  adjustWorkRecordAmount,
  deleteExpense,
  getWorkRecordDetail,
  updateExpense,
} from './api'

export function useWorkRecordDetail(recordId: string | null) {
  return useQuery({
    queryKey: ['work-record-detail', recordId],
    queryFn: () => getWorkRecordDetail(recordId as string),
    enabled: recordId !== null,
  })
}

function useInvalidateDetail(recordId: string) {
  const queryClient = useQueryClient()
  return () => {
    queryClient.invalidateQueries({ queryKey: ['work-record-detail', recordId] })
    queryClient.invalidateQueries({ queryKey: ['board'] })
  }
}

export function useAdjustAmount(recordId: string) {
  const invalidate = useInvalidateDetail(recordId)
  return useMutation({
    mutationFn: (input: { amount: string; reason?: string }) =>
      adjustWorkRecordAmount(recordId, input),
    onSuccess: invalidate,
  })
}

export function useAddExpense(recordId: string) {
  const invalidate = useInvalidateDetail(recordId)
  return useMutation({
    mutationFn: (input: { category: ExpenseCategory; amount: string; note?: string }) =>
      addExpense(recordId, input),
    onSuccess: invalidate,
  })
}

export function useUpdateExpense(recordId: string) {
  const invalidate = useInvalidateDetail(recordId)
  return useMutation({
    mutationFn: ({
      expenseId,
      input,
    }: {
      expenseId: string
      input: Partial<{ category: ExpenseCategory; amount: string; note: string | null }>
    }) => updateExpense(recordId, expenseId, input),
    onSuccess: invalidate,
  })
}

export function useDeleteExpense(recordId: string) {
  const invalidate = useInvalidateDetail(recordId)
  return useMutation({
    mutationFn: (expenseId: string) => deleteExpense(recordId, expenseId),
    onSuccess: invalidate,
  })
}
