import { useQuery } from '@tanstack/react-query'
import { apiFetch } from '../../lib/apiClient'

interface HealthResponse {
  status: 'ok' | 'degraded'
  database: boolean
}

export default function TodayPage() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ['health'],
    queryFn: () => apiFetch<HealthResponse>('/health'),
  })

  return (
    <div className="p-4">
      <div className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
        <h2 className="text-base font-semibold text-gray-900">System status</h2>
        {isLoading && <p className="mt-1 text-sm text-gray-500">Checking backend…</p>}
        {isError && (
          <p className="mt-1 text-sm text-red-600">Could not reach the backend API.</p>
        )}
        {data && (
          <p className="mt-1 text-sm text-gray-600">
            API: <span className="font-medium">{data.status}</span> · Database:{' '}
            <span className="font-medium">{data.database ? 'connected' : 'unreachable'}</span>
          </p>
        )}
      </div>

      <div className="mt-4 rounded-xl border border-dashed border-gray-300 p-4 text-center text-sm text-gray-500">
        Site selection, date picker, and attendance marking will appear here (Phase 3).
      </div>
    </div>
  )
}
