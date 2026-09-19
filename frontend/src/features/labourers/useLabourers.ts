import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  type LabourerInput,
  addWage,
  createLabourer,
  listLabourers,
  listWages,
  removeLabourerPhoto,
  setLabourerActive,
  updateLabourer,
  uploadLabourerPhoto,
} from './api'

export function useLabourers(params: { status?: string; search?: string }) {
  return useQuery({
    queryKey: ['labourers', params],
    queryFn: () => listLabourers(params),
  })
}

export function useWageHistory(labourerId: string | null) {
  return useQuery({
    queryKey: ['labourers', labourerId, 'wages'],
    queryFn: () => listWages(labourerId as string),
    enabled: labourerId !== null,
  })
}

function useInvalidateLabourers() {
  const queryClient = useQueryClient()
  return () => queryClient.invalidateQueries({ queryKey: ['labourers'] })
}

export function useCreateLabourer() {
  const invalidate = useInvalidateLabourers()
  return useMutation({
    mutationFn: (input: LabourerInput) => createLabourer(input),
    onSuccess: invalidate,
  })
}

export function useUpdateLabourer() {
  const invalidate = useInvalidateLabourers()
  return useMutation({
    mutationFn: ({ id, input }: { id: string; input: Partial<LabourerInput> }) =>
      updateLabourer(id, input),
    onSuccess: invalidate,
  })
}

export function useSetLabourerActive() {
  const invalidate = useInvalidateLabourers()
  return useMutation({
    mutationFn: ({ id, isActive }: { id: string; isActive: boolean }) =>
      setLabourerActive(id, isActive),
    onSuccess: invalidate,
  })
}

export function useUploadLabourerPhoto() {
  const invalidate = useInvalidateLabourers()
  return useMutation({
    mutationFn: ({ id, file }: { id: string; file: File }) => uploadLabourerPhoto(id, file),
    onSuccess: invalidate,
  })
}

export function useRemoveLabourerPhoto() {
  const invalidate = useInvalidateLabourers()
  return useMutation({
    mutationFn: (id: string) => removeLabourerPhoto(id),
    onSuccess: invalidate,
  })
}

export function useAddWage(labourerId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (input: { daily_wage: string; effective_from: string }) =>
      addWage(labourerId, input),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['labourers', labourerId, 'wages'] })
    },
  })
}
