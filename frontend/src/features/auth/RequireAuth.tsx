import { useEffect, type ReactNode } from 'react'
import { useCurrentAdmin } from './useAuth'
import LoginPage from './LoginPage'

export default function RequireAuth({ children }: { children: ReactNode }) {
  const { data: admin, isLoading, isError, refetch } = useCurrentAdmin()

  useEffect(() => {
    const handleExpired = () => { void refetch() }
    window.addEventListener('auth:expired', handleExpired)
    return () => window.removeEventListener('auth:expired', handleExpired)
  }, [refetch])

  if (isLoading) {
    return (
      <div className="flex h-full items-center justify-center text-sm text-gray-500">
        Loading…
      </div>
    )
  }

  if (isError || !admin) {
    return <LoginPage />
  }

  return <>{children}</>
}
