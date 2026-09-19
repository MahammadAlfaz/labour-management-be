import { apiFetch } from '../../lib/apiClient'
import type { AttendanceStatus } from '../today/api'
import type { Payment } from '../payments/api'

const API_BASE_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

export interface LabourerHistoryWorkRecord {
  id: string
  work_date: string
  site_id: string
  site_name: string
  status: AttendanceStatus | null
  amount: string
  expenses_total: string
  paid: boolean
}

export interface LabourerHistoryReport {
  labourer_id: string
  labourer_name: string
  period_start: string
  period_end: string
  work_records: LabourerHistoryWorkRecord[]
  payments: Payment[]
  total_earnings: string
  outstanding_balance: string
}

export interface SiteAttendanceEntry {
  work_date: string
  labourer_id: string
  labourer_name: string
  status: AttendanceStatus | null
  amount: string
}

export interface SiteAttendanceReport {
  site_id: string
  site_name: string
  period_start: string
  period_end: string
  entries: SiteAttendanceEntry[]
  total_amount: string
}

export interface WeeklySettlementEntry {
  labourer_id: string
  labourer_name: string
  suggested_amount: string
  has_unpaid_earnings: boolean
}

export interface WeeklySettlementReport {
  period_start: string
  period_end: string
  entries: WeeklySettlementEntry[]
}

export function getLabourerHistory(labourerId: string, from: string, to: string) {
  const query = new URLSearchParams({ from, to })
  return apiFetch<LabourerHistoryReport>(`/reports/labourer/${labourerId}/history?${query.toString()}`)
}

export function getSiteAttendance(siteId: string, from: string, to: string) {
  const query = new URLSearchParams({ from, to })
  return apiFetch<SiteAttendanceReport>(`/reports/site/${siteId}/attendance?${query.toString()}`)
}

export function getWeeklySettlement(from: string, to: string) {
  const query = new URLSearchParams({ from, to })
  return apiFetch<WeeklySettlementReport>(`/reports/weekly-settlement?${query.toString()}`)
}

export function labourerHistoryExportUrl(labourerId: string, from: string, to: string) {
  const query = new URLSearchParams({ from, to })
  return `${API_BASE_URL}/reports/labourer/${labourerId}/history/export?${query.toString()}`
}

export function siteAttendanceExportUrl(siteId: string, from: string, to: string) {
  const query = new URLSearchParams({ from, to })
  return `${API_BASE_URL}/reports/site/${siteId}/attendance/export?${query.toString()}`
}

export function weeklySettlementExportUrl(from: string, to: string) {
  const query = new URLSearchParams({ from, to })
  return `${API_BASE_URL}/reports/weekly-settlement/export?${query.toString()}`
}
