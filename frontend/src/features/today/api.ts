import { apiFetch } from '../../lib/apiClient'

export type AttendanceStatus = 'FULL_DAY' | 'HALF_DAY' | 'ABSENT'
export type ExpenseCategory = 'PETROL' | 'BUS' | 'AUTO' | 'OTHER'

export interface WorkRecord {
  id: string
  labourer_id: string
  site_id: string
  work_date: string
  status: AttendanceStatus | null
  wage_snapshot: string | null
  original_amount: string
  amount: string
  adjustment_reason: string | null
  adjusted_by: string | null
  adjusted_at: string | null
  payment_id: string | null
  created_by: string
  updated_by: string
  created_at: string
  updated_at: string
}

export interface Expense {
  id: string
  daily_work_record_id: string
  category: ExpenseCategory
  amount: string
  note: string | null
  created_by: string
  updated_by: string
  created_at: string
  updated_at: string
}

export interface WorkRecordDetail extends WorkRecord {
  expenses: Expense[]
  total_earnings: string
}

export interface BoardEntry {
  labourer_id: string
  labourer_name: string
  labourer_photo_url: string | null
  record: WorkRecord
}

export interface AvailableLabourer {
  labourer_id: string
  labourer_name: string
  labourer_photo_url: string | null
  unavailable_reason: string | null
}

export function getBoard(siteId: string, workDate: string) {
  const query = new URLSearchParams({ site_id: siteId, work_date: workDate })
  return apiFetch<BoardEntry[]>(`/work-records/board?${query.toString()}`)
}

export function searchAvailableLabourers(workDate: string, search?: string) {
  const query = new URLSearchParams({ work_date: workDate })
  if (search) query.set('search', search)
  return apiFetch<AvailableLabourer[]>(`/work-records/available-labourers?${query.toString()}`)
}

export function getWorkRecordDetail(id: string) {
  return apiFetch<WorkRecordDetail>(`/work-records/${id}`)
}

export function assignLabourer(input: { labourer_id: string; site_id: string; work_date: string }) {
  return apiFetch<WorkRecord>('/work-records', { method: 'POST', body: JSON.stringify(input) })
}

export function unassignLabourer(recordId: string) {
  return apiFetch<void>(`/work-records/${recordId}`, { method: 'DELETE' })
}

export function clearAttendance(recordId: string) {
  return apiFetch<WorkRecord>(`/work-records/${recordId}/clear-attendance`, { method: 'PATCH' })
}

export function updateWorkRecord(
  id: string,
  input: { status: AttendanceStatus; amount?: string }
) {
  return apiFetch<WorkRecord>(`/work-records/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(input),
  })
}

export function adjustWorkRecordAmount(id: string, input: { amount: string; reason?: string }) {
  return apiFetch<WorkRecord>(`/work-records/${id}/adjust-amount`, {
    method: 'PATCH',
    body: JSON.stringify(input),
  })
}

export function addExpense(
  recordId: string,
  input: { category: ExpenseCategory; amount: string; note?: string }
) {
  return apiFetch<Expense>(`/work-records/${recordId}/expenses`, {
    method: 'POST',
    body: JSON.stringify(input),
  })
}

export function updateExpense(
  recordId: string,
  expenseId: string,
  input: Partial<{ category: ExpenseCategory; amount: string; note: string | null }>
) {
  return apiFetch<Expense>(`/work-records/${recordId}/expenses/${expenseId}`, {
    method: 'PATCH',
    body: JSON.stringify(input),
  })
}

export function deleteExpense(recordId: string, expenseId: string) {
  return apiFetch<void>(`/work-records/${recordId}/expenses/${expenseId}`, { method: 'DELETE' })
}
