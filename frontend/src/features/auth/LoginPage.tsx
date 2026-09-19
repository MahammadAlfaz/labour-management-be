import { useEffect, useRef } from 'react'
import { useLogin } from './useAuth'

const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID as string | undefined

export default function LoginPage() {
  const buttonRef = useRef<HTMLDivElement>(null)
  const login = useLogin()

  useEffect(() => {
    if (!GOOGLE_CLIENT_ID || !window.google || !buttonRef.current) return

    window.google.accounts.id.initialize({
      client_id: GOOGLE_CLIENT_ID,
      callback: (response) => login.mutate(response.credential),
    })
    window.google.accounts.id.renderButton(buttonRef.current, {
      theme: 'outline',
      size: 'large',
      width: 280,
    })
    // Google's script loads async; initialize/renderButton only needs to run once it's ready.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  return (
    <div className="flex h-full flex-col items-center justify-center gap-4 p-6 text-center">
      <h1 className="text-xl font-semibold text-gray-900">Labour Management</h1>
      <p className="max-w-xs text-sm text-gray-500">
        Sign in with an authorized admin Google account to continue.
      </p>

      {GOOGLE_CLIENT_ID ? (
        <div ref={buttonRef} />
      ) : (
        <p className="text-sm text-red-600">
          Google sign-in is not configured (missing VITE_GOOGLE_CLIENT_ID).
        </p>
      )}

      {login.isPending && <p className="text-sm text-gray-500">Signing in…</p>}
      {login.isError && (
        <p className="max-w-xs text-sm text-red-600">
          {login.error instanceof Error ? login.error.message : 'Sign-in failed. Please try again.'}
        </p>
      )}
    </div>
  )
}
