import { apiFetch } from '../../lib/apiClient'

export type PeriodType = 'daily' | 'weekly'
export type PaymentStatus = 'paid' | 'partial' | 'overpaid'

export interface PaymentSnapshot {
  wages: string
  travel_expenses: string
  earnings: string
  unsettled_advances: string
  unsettled_deductions: string
  unsettled_adjustments: string
  prior_balance: string
  suggested_amount: string
}

export interface PaymentPreview extends PaymentSnapshot {
  labourer_id: string
  period_type: PeriodType
  period_start: string
  period_end: string
  unpaid_work_record_ids: string[]
  adjustments: Adjustment[]
}

export interface Adjustment {
  id: string
  amount: string
  reason: string
  created_at: string
}

export interface Payment {
  id: string
  labourer_id: string
  period_type: PeriodType
  period_start: string
  period_end: string
  calculation_snapshot: PaymentSnapshot
  paid_amount: string
  adjustment_reason: string | null
  status: PaymentStatus
  created_by: string
  created_at: string
}

export interface Advance {
  id: string
  labourer_id: string
  amount: string
  note: string | null
  given_at: string
  settled: boolean
  settled_in_payment_id: string | null
  created_by: string
  created_at: string
}

export interface Deduction {
  id: string
  labourer_id: string
  amount: string
  reason: string
  settled: boolean
  settled_in_payment_id: string | null
  created_by: string
  created_at: string
}

export function getPaymentPreview(params: {
  labourerId: string
  periodType: PeriodType
  periodStart: string
  periodEnd: string
}) {
  const query = new URLSearchParams({
    labourer_id: params.labourerId,
    period_type: params.periodType,
    period_start: params.periodStart,
    period_end: params.periodEnd,
  })
  return apiFetch<PaymentPreview>(`/payments/preview?${query.toString()}`)
}

export function createPayment(
  input: {
    labourer_id: string
    period_type: PeriodType
    period_start: string
    period_end: string
    paid_amount: string
    adjustment_reason?: string
  },
  idempotencyKey: string
) {
  return apiFetch<Payment>('/payments', {
    method: 'POST',
    body: JSON.stringify(input),
    headers: { 'Idempotency-Key': idempotencyKey },
  })
}

export function listPayments(labourerId: string) {
  return apiFetch<Payment[]>(`/payments/labourer/${labourerId}`)
}

export function createAdvance(input: { labourer_id: string; amount: string; note?: string; given_at: string }) {
  return apiFetch<Advance>('/advances', { method: 'POST', body: JSON.stringify(input) })
}

export function listAdvances(labourerId: string) {
  return apiFetch<Advance[]>(`/advances/labourer/${labourerId}`)
}

export function createDeduction(input: { labourer_id: string; amount: string; reason: string }) {
  return apiFetch<Deduction>('/deductions', { method: 'POST', body: JSON.stringify(input) })
}

export function listDeductions(labourerId: string) {
  return apiFetch<Deduction[]>(`/deductions/labourer/${labourerId}`)
}
