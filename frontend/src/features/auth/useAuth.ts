import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { type Admin, fetchMe, loginWithGoogle, logout as apiLogout } from './api'
import { ApiError } from '../../lib/apiClient'

export const ME_QUERY_KEY = ['auth', 'me'] as const

export function useCurrentAdmin() {
  return useQuery<Admin, ApiError>({
    queryKey: ME_QUERY_KEY,
    queryFn: fetchMe,
    retry: false,
  })
}

export function useLogin() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: loginWithGoogle,
    onSuccess: (data) => {
      queryClient.setQueryData(ME_QUERY_KEY, data.admin)
    },
  })
}

export function useLogout() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: apiLogout,
    onSuccess: () => {
      queryClient.removeQueries({ queryKey: ME_QUERY_KEY })
    },
  })
}
