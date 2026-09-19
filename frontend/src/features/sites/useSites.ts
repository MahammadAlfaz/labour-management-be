import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  type SiteInput,
  createClientReceipt,
  createSiteExpense,
  createSite,
  getSiteFinancialSummary,
  listClientReceipts,
  listSiteExpenses,
  listSites,
  removeSitePhoto,
  setSiteActive,
  updateSite,
  uploadSitePhoto,
} from './api'

export function useSites(params: { status?: string }) {
  return useQuery({
    queryKey: ['sites', params],
    queryFn: () => listSites(params),
  })
}

export function useSiteFinancialSummary(siteId: string | null) {
  return useQuery({
    queryKey: ['site-financial-summary', siteId],
    queryFn: () => getSiteFinancialSummary(siteId as string),
    enabled: siteId !== null,
  })
}

export function useClientReceipts(siteId: string | null) {
  return useQuery({
    queryKey: ['site-client-receipts', siteId],
    queryFn: () => listClientReceipts(siteId as string),
    enabled: siteId !== null,
  })
}

export function useCreateClientReceipt(siteId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (input: { amount: string; received_on: string; note?: string }) =>
      createClientReceipt(siteId, input),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['site-financial-summary', siteId] })
      queryClient.invalidateQueries({ queryKey: ['site-client-receipts', siteId] })
    },
  })
}

export function useSiteExpenses(siteId: string | null) {
  return useQuery({ queryKey: ['site-expenses', siteId], queryFn: () => listSiteExpenses(siteId as string), enabled: siteId !== null })
}

export function useCreateSiteExpense(siteId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (input: { category: 'FOOD' | 'OTHER'; amount: string; expense_date: string; note?: string }) => createSiteExpense(siteId, input),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['site-financial-summary', siteId] })
      queryClient.invalidateQueries({ queryKey: ['site-expenses', siteId] })
    },
  })
}

function useInvalidateSites() {
  const queryClient = useQueryClient()
  return () => queryClient.invalidateQueries({ queryKey: ['sites'] })
}

export function useCreateSite() {
  const invalidate = useInvalidateSites()
  return useMutation({
    mutationFn: (input: SiteInput) => createSite(input),
    onSuccess: invalidate,
  })
}

export function useUpdateSite() {
  const invalidate = useInvalidateSites()
  return useMutation({
    mutationFn: ({ id, input }: { id: string; input: Partial<SiteInput> }) =>
      updateSite(id, input),
    onSuccess: invalidate,
  })
}

export function useSetSiteActive() {
  const invalidate = useInvalidateSites()
  return useMutation({
    mutationFn: ({ id, isActive }: { id: string; isActive: boolean }) =>
      setSiteActive(id, isActive),
    onSuccess: invalidate,
  })
}

export function useUploadSitePhoto() {
  const invalidate = useInvalidateSites()
  return useMutation({
    mutationFn: ({ id, file }: { id: string; file: File }) => uploadSitePhoto(id, file),
    onSuccess: invalidate,
  })
}

export function useRemoveSitePhoto() {
  const invalidate = useInvalidateSites()
  return useMutation({
    mutationFn: (id: string) => removeSitePhoto(id),
    onSuccess: invalidate,
  })
}
