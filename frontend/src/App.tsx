import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AppShell } from './components/layout/AppShell'
import { DashboardPage } from './features/dashboard/DashboardPage'
import { CustomersPage } from './features/customers/CustomersPage'
import { SuppliersPage } from './features/suppliers/SuppliersPage'
import { TransactionsPage } from './features/transactions/TransactionsPage'
import { CashFlowPage } from './features/cashflow/CashFlowPage'
import { SimulatorPage } from './features/simulator/SimulatorPage'
import { SettingsPage } from './features/settings/SettingsPage'

export function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AppShell />}>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/customers" element={<CustomersPage />} />
          <Route path="/suppliers" element={<SuppliersPage />} />
          <Route path="/transactions" element={<TransactionsPage />} />
          <Route path="/cash-flow" element={<CashFlowPage />} />
          <Route path="/simulator" element={<SimulatorPage />} />
          <Route path="/settings" element={<SettingsPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App
