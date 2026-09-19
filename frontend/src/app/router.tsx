import { createBrowserRouter } from 'react-router-dom'
import AppShell from './layout/AppShell'
import RequireAuth from '../features/auth/RequireAuth'
import TodayPage from '../features/today/TodayPage'
import LabourersPage from '../features/labourers/LabourersPage'
import SitesPage from '../features/sites/SitesPage'
import PaymentsPage from '../features/payments/PaymentsPage'
import MorePage from '../features/more/MorePage'

export const router = createBrowserRouter([
  {
    path: '/',
    element: (
      <RequireAuth>
        <AppShell />
      </RequireAuth>
    ),
    children: [
      { index: true, element: <TodayPage /> },
      { path: 'labourers', element: <LabourersPage /> },
      { path: 'sites', element: <SitesPage /> },
      { path: 'payments', element: <PaymentsPage /> },
      { path: 'more', element: <MorePage /> },
    ],
  },
])
