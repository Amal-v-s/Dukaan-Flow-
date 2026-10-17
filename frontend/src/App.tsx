import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { ErrorBoundary } from './components/common/ErrorBoundary'
import { AuthProvider } from './context/AuthContext'
import { ProtectedRoute } from './components/auth/ProtectedRoute'
import { LoginPage } from './features/auth/LoginPage'
import { PrivacyPage } from './features/legal/PrivacyPage'
import { TermsPage } from './features/legal/TermsPage'
import { AppShell } from './components/layout/AppShell'
import { DashboardPage } from './features/dashboard/DashboardPage'
import { CustomersPage } from './features/customers/CustomersPage'
import { SuppliersPage } from './features/suppliers/SuppliersPage'
import { TransactionsPage } from './features/transactions/TransactionsPage'
import { CashFlowPage } from './features/cashflow/CashFlowPage'
import { SimulatorPage } from './features/simulator/SimulatorPage'
import { SettingsPage } from './features/settings/SettingsPage'
import { ManagementPage } from './features/management/ManagementPage'
import { ImportWizardPage } from './features/imports/ImportWizardPage'

export function App() {
  return (
    <ErrorBoundary>
      <BrowserRouter>
        <AuthProvider>
          <Routes>
            {/* Public Authentication & Legal Routes */}
            <Route path="/login" element={<LoginPage />} />
            <Route path="/privacy" element={<PrivacyPage />} />
            <Route path="/terms" element={<TermsPage />} />

            {/* Protected Merchant Routes */}
            <Route element={<ProtectedRoute />}>
              <Route element={<AppShell />}>
                <Route path="/" element={<DashboardPage />} />
                <Route path="/customers" element={<CustomersPage />} />
                <Route path="/suppliers" element={<SuppliersPage />} />
                <Route path="/transactions" element={<TransactionsPage />} />
                <Route path="/cash-flow" element={<CashFlowPage />} />
                <Route path="/simulator" element={<SimulatorPage />} />
                <Route path="/settings" element={<SettingsPage />} />
                <Route path="/management" element={<ManagementPage />} />
                <Route path="/imports" element={<ImportWizardPage />} />
                <Route path="*" element={<Navigate to="/" replace />} />
              </Route>
            </Route>
          </Routes>
        </AuthProvider>
      </BrowserRouter>
    </ErrorBoundary>
  )
}

export default App
