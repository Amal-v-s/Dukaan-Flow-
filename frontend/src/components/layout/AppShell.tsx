import React from 'react'
import { Outlet, useLocation } from 'react-router-dom'
import { Sidebar } from './Sidebar'
import { Header } from './Header'
import { BottomNav } from './BottomNav'

const pageTitles: Record<string, { title: string; subtitle: string }> = {
  '/': { title: 'Dashboard Overview', subtitle: 'Live cash position, receivables, and payables summary' },
  '/customers': { title: 'Customers & Udhaar Khata', subtitle: 'Track customer credit sales, dues, and repayments' },
  '/suppliers': { title: 'Supplier Bills & Payables', subtitle: 'Manage distributor invoices, payment dates, and settlements' },
  '/transactions': { title: 'Transactions & Expenses', subtitle: 'Consolidated cash movements and categorized shop expenses' },
  '/cash-flow': { title: '14-Day Cash-Flow Forecast', subtitle: 'Deterministic projected liquidity and safety buffer alerts' },
  '/simulator': { title: 'What-If Cash Simulator', subtitle: 'Test hypothetical collections and bill shifts without altering actual records' },
  '/settings': { title: 'Store Settings', subtitle: 'Safety buffer configuration and business parameters' },
  '/management': { title: 'Business Management', subtitle: 'Repayment schedules, budgets, reports, and in-app reminders' },
  '/imports': { title: 'Import Expenses', subtitle: 'Validate a CSV preview and confirm before adding cashbook records' },
}

export const AppShell: React.FC = () => {
  const location = useLocation()
  const currentMeta = pageTitles[location.pathname] || { title: 'DukaanFlow', subtitle: 'Merchant Flow Precision' }

  return (
    <div className="min-h-screen flex bg-[#F7F8FA] text-[#17191C]">
      {/* Desktop Sidebar (240px) */}
      <Sidebar />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 pb-20 md:pb-8">
        <Header title={currentMeta.title} subtitle={currentMeta.subtitle} />

        <main className="flex-1 p-6 md:p-8 max-w-7xl w-full mx-auto">
          <Outlet />
        </main>
      </div>

      {/* Mobile Bottom Nav (64px) */}
      <BottomNav />
    </div>
  )
}
