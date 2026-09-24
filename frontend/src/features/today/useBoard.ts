import { useQueries, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import type { AttendanceStatus, BoardEntry } from './api'
import {
  assignLabourer,
  clearAttendance,
  getBoard,
  searchAvailableLabourers,
  unassignLabourer,
  updateWorkRecord,
} from './api'

export function useBoard(siteId: string | null, workDate: string) {
  return useQuery({
    queryKey: ['board', siteId, workDate],
    queryFn: () => getBoard(siteId as string, workDate),
    enabled: siteId !== null,
  })
}

/**
 * Fetches every site's board for the same date in one go, sharing the same
 * query keys/cache as useBoard so this never duplicates a request already
 * made by a SiteGrid card.
 */
export function useAllSitesBoards(siteIds: string[], workDate: string) {
  const results = useQueries({
    queries: siteIds.map((siteId) => ({
      queryKey: ['board', siteId, workDate],
      queryFn: () => getBoard(siteId, workDate),
    })),
  })

  const isLoading = results.some((r) => r.isLoading)
  const boards: BoardEntry[][] = results.map((r) => r.data ?? [])
  return { boards, isLoading }
}

export function useAvailableLabourers(workDate: string, search: string, enabled: boolean) {
  return useQuery({
    queryKey: ['available-labourers', workDate, search],
    queryFn: () => searchAvailableLabourers(workDate, search || undefined),
    enabled,
  })
}

export function useAssignLabourer(siteId: string, workDate: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (labourerId: string) =>
      assignLabourer({ labourer_id: labourerId, site_id: siteId, work_date: workDate }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['board', siteId, workDate] })
      queryClient.invalidateQueries({ queryKey: ['available-labourers', workDate] })
    },
  })
}

export function useUnassignLabourer(siteId: string, workDate: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (recordId: string) => unassignLabourer(recordId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['board', siteId, workDate] })
      queryClient.invalidateQueries({ queryKey: ['available-labourers', workDate] })
    },
  })
}

export function useClearAttendance(siteId: string, workDate: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (recordId: string) => clearAttendance(recordId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['board', siteId, workDate] }),
  })
}

export function useMarkAttendance(siteId: string, workDate: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (input: { recordId: string; status: AttendanceStatus; amount?: string }) =>
      updateWorkRecord(input.recordId, { status: input.status, amount: input.amount }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['board', siteId, workDate] })
    },
  })
}
