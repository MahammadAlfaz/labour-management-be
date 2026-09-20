import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  type WallCalculationInput,
  createWallCalculation,
  deleteWallCalculation,
  extractMeasurements,
  listWallCalculations,
  updateWallCalculation,
} from './api'

export function useWallCalculations(params: { site_id?: string } = {}) {
  return useQuery({
    queryKey: ['wall-calculations', params],
    queryFn: () => listWallCalculations(params),
  })
}

function useInvalidateWallCalculations() {
  const queryClient = useQueryClient()
  return () => queryClient.invalidateQueries({ queryKey: ['wall-calculations'] })
}

export function useExtractMeasurements() {
  return useMutation({ mutationFn: (file: File) => extractMeasurements(file) })
}

export function useCreateWallCalculation() {
  const invalidate = useInvalidateWallCalculations()
  return useMutation({
    mutationFn: (input: WallCalculationInput) => createWallCalculation(input),
    onSuccess: invalidate,
  })
}

export function useUpdateWallCalculation() {
  const invalidate = useInvalidateWallCalculations()
  return useMutation({
    mutationFn: ({ id, input }: { id: string; input: Partial<WallCalculationInput> }) =>
      updateWallCalculation(id, input),
    onSuccess: invalidate,
  })
}

export function useDeleteWallCalculation() {
  const invalidate = useInvalidateWallCalculations()
  return useMutation({
    mutationFn: (id: string) => deleteWallCalculation(id),
    onSuccess: invalidate,
  })
}
