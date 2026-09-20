// Strip a trailing slash so `${API_BASE_URL}${path}` never produces a
// double slash (e.g. VITE_API_URL="https://host.com/" + "/auth/me") --
// FastAPI treats "//auth/me" as a different, unmatched route and 404s.
const API_BASE_URL = (import.meta.env.VITE_API_URL ?? 'http://localhost:8000').replace(/\/+$/, '')

let refreshInFlight: Promise<boolean> | null = null

export class ApiError extends Error {
  status: number

  constructor(message: string, status: number) {
    super(message)
    this.status = status
  }
}

function responseErrorMessage(body: unknown, fallback: string): string {
  if (!body || typeof body !== 'object') return fallback
  const payload = body as { error?: { message?: string }; detail?: unknown }
  if (payload.error?.message) return payload.error.message
  if (typeof payload.detail === 'string') return payload.detail
  if (Array.isArray(payload.detail)) {
    const first = payload.detail[0] as { loc?: unknown[]; msg?: string } | undefined
    if (first?.msg) {
      const field = first.loc?.at(-1)
      return field ? `${String(field)}: ${first.msg}` : first.msg
    }
  }
  return fallback
}

async function refreshAccessToken(): Promise<boolean> {
  if (refreshInFlight) return refreshInFlight

  refreshInFlight = fetch(`${API_BASE_URL}/auth/refresh`, {
    method: 'POST',
    credentials: 'include',
  })
    .then((response) => response.ok)
    .catch(() => false)
    .finally(() => {
      refreshInFlight = null
    })
  return refreshInFlight
}

function makeRequest(path: string, init?: RequestInit) {
  return fetch(`${API_BASE_URL}${path}`, {
    credentials: 'include',
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...init?.headers,
    },
  })
}

export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  let response = await makeRequest(path, init)

  // The access token is deliberately short-lived. A refresh cookie is scoped
  // to /auth and is sent only to this endpoint; retrying once avoids repeated
  // 401s when several queries start at the same time after expiry.
  if (response.status === 401 && !path.startsWith('/auth/')) {
    const refreshed = await refreshAccessToken()
    if (refreshed) response = await makeRequest(path, init)
    else window.dispatchEvent(new Event('auth:expired'))
  }

  if (!response.ok) {
    const body = await response.json().catch(() => null)
    throw new ApiError(responseErrorMessage(body, response.statusText), response.status)
  }

  if (response.status === 204) {
    return undefined as T
  }

  return response.json() as Promise<T>
}

export async function apiUpload<T>(
  path: string,
  formData: FormData,
  init?: Omit<RequestInit, 'body' | 'method'>
): Promise<T> {
  // No Content-Type header here -- the browser sets the multipart boundary itself.
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: 'POST',
    credentials: 'include',
    body: formData,
    ...init,
  })

  if (!response.ok) {
    const body = await response.json().catch(() => null)
    throw new ApiError(responseErrorMessage(body, response.statusText), response.status)
  }

  return response.json() as Promise<T>
}
