import { apiFetch, apiUpload } from '../../lib/apiClient'

export type PaymentFrequency = 'daily' | 'weekly'
export type LabourerStatus = 'active' | 'inactive'

export interface Labourer {
  id: string
  name: string
  phone: string | null
  upi_id: string | null
  status: LabourerStatus
  work_category: string | null
  payment_frequency: PaymentFrequency
  photo_url: string | null
  created_by: string
  updated_by: string
  created_at: string
  updated_at: string
}

export interface LabourerInput {
  name: string
  phone?: string | null
  upi_id?: string | null
  work_category?: string | null
  payment_frequency?: PaymentFrequency
}

export interface WageEntry {
  id: string
  labourer_id: string
  daily_wage: string
  effective_from: string
  created_by: string
  created_at: string
}

export function listLabourers(params: { status?: string; search?: string } = {}) {
  const query = new URLSearchParams()
  if (params.status) query.set('status', params.status)
  if (params.search) query.set('search', params.search)
  const qs = query.toString()
  return apiFetch<Labourer[]>(`/labourers${qs ? `?${qs}` : ''}`)
}

export function createLabourer(input: LabourerInput) {
  return apiFetch<Labourer>('/labourers', { method: 'POST', body: JSON.stringify(input) })
}

export function updateLabourer(id: string, input: Partial<LabourerInput>) {
  return apiFetch<Labourer>(`/labourers/${id}`, { method: 'PATCH', body: JSON.stringify(input) })
}

export function setLabourerActive(id: string, isActive: boolean) {
  return apiFetch<Labourer>(`/labourers/${id}/${isActive ? 'activate' : 'deactivate'}`, {
    method: 'POST',
  })
}

export function listWages(labourerId: string) {
  return apiFetch<WageEntry[]>(`/labourers/${labourerId}/wages`)
}

export function addWage(labourerId: string, input: { daily_wage: string; effective_from: string }) {
  return apiFetch<WageEntry>(`/labourers/${labourerId}/wages`, {
    method: 'POST',
    body: JSON.stringify(input),
  })
}

export function uploadLabourerPhoto(id: string, file: File) {
  const formData = new FormData()
  formData.append('file', file)
  return apiUpload<Labourer>(`/labourers/${id}/photo`, formData)
}

export function removeLabourerPhoto(id: string) {
  return apiFetch<Labourer>(`/labourers/${id}/photo`, { method: 'DELETE' })
}
