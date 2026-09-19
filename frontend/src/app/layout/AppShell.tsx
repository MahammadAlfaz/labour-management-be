import { NavLink, Outlet } from 'react-router-dom'
import { useCurrentAdmin, useLogout } from '../../features/auth/useAuth'

const NAV_ITEMS = [
  { to: '/', label: 'Today', icon: '📋', end: true },
  { to: '/labourers', label: 'Labourers', icon: '👷' },
  { to: '/sites', label: 'Sites', icon: '🏗️' },
  { to: '/payments', label: 'Payments', icon: '💵' },
  { to: '/more', label: 'More', icon: '⋯' },
] as const

export default function AppShell() {
  const { data: admin } = useCurrentAdmin()
  const logout = useLogout()

  return (
    <div className="flex h-full flex-col bg-gray-50">
      <header className="flex items-center justify-between border-b border-gray-200 bg-white px-4 py-3">
        <h1 className="text-lg font-semibold text-gray-900">Labour Management</h1>
        {admin && (
          <button
            type="button"
            onClick={() => logout.mutate()}
            className="text-sm text-gray-500 active:text-gray-700"
          >
            {admin.name.split(' ')[0]} · Logout
          </button>
        )}
      </header>

      <main className="flex-1 overflow-y-auto pb-20">
        <Outlet />
      </main>

      <nav className="fixed inset-x-0 bottom-0 border-t border-gray-200 bg-white">
        <ul className="grid grid-cols-5">
          {NAV_ITEMS.map((item) => (
            <li key={item.to}>
              <NavLink
                to={item.to}
                end={'end' in item ? item.end : false}
                className={({ isActive }) =>
                  `flex flex-col items-center gap-0.5 py-2 text-xs ${
                    isActive ? 'text-brand-600 font-medium' : 'text-gray-500'
                  }`
                }
              >
                <span className="text-lg leading-none">{item.icon}</span>
                {item.label}
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>
    </div>
  )
}
