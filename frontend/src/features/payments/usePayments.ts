import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import type { PeriodType } from './api'
import {
  createAdvance,
  createDeduction,
  createPayment,
  getPaymentPreview,
  listAdvances,
  listDeductions,
  listPayments,
} from './api'

export function usePaymentPreview(params: {
  labourerId: string | null
  periodType: PeriodType
  periodStart: string
  periodEnd: string
}) {
  return useQuery({
    queryKey: ['payment-preview', params],
    queryFn: () =>
      getPaymentPreview({
        labourerId: params.labourerId as string,
        periodType: params.periodType,
        periodStart: params.periodStart,
        periodEnd: params.periodEnd,
      }),
    enabled: params.labourerId !== null,
  })
}

export function usePaymentHistory(labourerId: string | null) {
  return useQuery({
    queryKey: ['payments', labourerId],
    queryFn: () => listPayments(labourerId as string),
    enabled: labourerId !== null,
  })
}

export function useAdvances(labourerId: string | null) {
  return useQuery({
    queryKey: ['advances', labourerId],
    queryFn: () => listAdvances(labourerId as string),
    enabled: labourerId !== null,
  })
}

export function useDeductions(labourerId: string | null) {
  return useQuery({
    queryKey: ['deductions', labourerId],
    queryFn: () => listDeductions(labourerId as string),
    enabled: labourerId !== null,
  })
}

function useInvalidateLabourerFinancials(labourerId: string) {
  const queryClient = useQueryClient()
  return () => {
    queryClient.invalidateQueries({ queryKey: ['payment-preview'] })
    queryClient.invalidateQueries({ queryKey: ['payments', labourerId] })
    queryClient.invalidateQueries({ queryKey: ['advances', labourerId] })
    queryClient.invalidateQueries({ queryKey: ['deductions', labourerId] })
  }
}

export function useCreatePayment(labourerId: string) {
  const invalidate = useInvalidateLabourerFinancials(labourerId)
  return useMutation({
    mutationFn: ({
      input,
      idempotencyKey,
    }: {
      input: {
        labourer_id: string
        period_type: PeriodType
        period_start: string
        period_end: string
        paid_amount: string
        adjustment_reason?: string
      }
      idempotencyKey: string
    }) => createPayment(input, idempotencyKey),
    onSuccess: invalidate,
  })
}

export function useCreateAdvance(labourerId: string) {
  const invalidate = useInvalidateLabourerFinancials(labourerId)
  return useMutation({
    mutationFn: (input: { amount: string; note?: string; given_at: string }) =>
      createAdvance({ labourer_id: labourerId, ...input }),
    onSuccess: invalidate,
  })
}

export function useCreateDeduction(labourerId: string) {
  const invalidate = useInvalidateLabourerFinancials(labourerId)
  return useMutation({
    mutationFn: (input: { amount: string; reason: string }) =>
      createDeduction({ labourer_id: labourerId, ...input }),
    onSuccess: invalidate,
  })
}
