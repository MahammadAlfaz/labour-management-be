import { apiFetch } from '../../lib/apiClient'

export interface Admin {
  id: string
  email: string
  name: string
  is_active: boolean
  created_at: string
}

interface AuthResponse {
  admin: Admin
}

export function fetchMe(): Promise<Admin> {
  return apiFetch<Admin>('/auth/me')
}

export function loginWithGoogle(idToken: string): Promise<AuthResponse> {
  return apiFetch<AuthResponse>('/auth/google', {
    method: 'POST',
    body: JSON.stringify({ id_token: idToken }),
  })
}

export function logout(): Promise<{ status: string }> {
  return apiFetch<{ status: string }>('/auth/logout', { method: 'POST' })
}
