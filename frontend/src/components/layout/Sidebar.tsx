import React from 'react'
import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard,
  Users,
  Building2,
  ArrowLeftRight,
  LineChart,
  SlidersHorizontal,
  Settings,
  Store,
  ShieldCheck
  , ClipboardList
} from 'lucide-react'

interface NavItem {
  name: string
  to: string
  icon: React.ElementType
}

const navItems: NavItem[] = [
  { name: 'Overview', to: '/', icon: LayoutDashboard },
  { name: 'Customers / Khata', to: '/customers', icon: Users },
  { name: 'Suppliers', to: '/suppliers', icon: Building2 },
  { name: 'Transactions', to: '/transactions', icon: ArrowLeftRight },
  { name: 'Cash Flow', to: '/cash-flow', icon: LineChart },
  { name: 'What-If Simulator', to: '/simulator', icon: SlidersHorizontal },
  { name: 'Business Management', to: '/management', icon: ClipboardList },
  { name: 'Import Expenses', to: '/imports', icon: ClipboardList },
  { name: 'Settings', to: '/settings', icon: Settings },
]

export const Sidebar: React.FC = () => {
  return (
    <aside className="hidden md:flex flex-col w-[240px] shrink-0 bg-white border-r border-[#E8EAED] min-h-screen z-20">
      {/* Brand Header */}
      <div className="h-[72px] px-6 flex items-center gap-3 border-b border-[#E8EAED]">
        <div className="w-9 h-9 rounded-lg bg-[#E8F7EF] flex items-center justify-center text-[#16A36A]">
          <Store className="w-5 h-5" />
        </div>
        <div>
          <h1 className="text-base font-bold text-[#17191C] leading-none tracking-tight">DukaanFlow</h1>
          <p className="text-[11px] text-[#737780] font-medium mt-1">Merchant Precision</p>
        </div>
      </div>

      {/* Navigation Links */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        {navItems.map((item) => {
          const Icon = item.icon
          return (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === '/'}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3.5 py-2.5 rounded-lg text-[13px] font-medium transition-colors ${
                  isActive
                    ? 'bg-[#E8F7EF] text-[#16A36A] font-semibold border-l-2 border-[#16A36A]'
                    : 'text-[#737780] hover:text-[#17191C] hover:bg-[#F0F2F5]'
                }`
              }
            >
              <Icon className="w-4 h-4 shrink-0" />
              <span>{item.name}</span>
            </NavLink>
          )
        })}
      </nav>

      {/* Merchant / Business Badge */}
      <div className="p-4 border-t border-[#E8EAED] bg-[#F7F8FA]">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-full bg-[#16A36A] text-white flex items-center justify-center text-xs font-bold shrink-0">
            DK
          </div>
          <div className="min-w-0 flex-1">
            <p className="text-xs font-semibold text-[#17191C] truncate">Demo Kirana Store</p>
            <div className="flex items-center gap-1 text-[10px] text-[#16A36A] font-medium mt-0.5">
              <ShieldCheck className="w-3 h-3" />
              <span>Verified Store (INR)</span>
            </div>
          </div>
        </div>
        <div className="mt-2 text-[10px] text-[#737780] flex items-center justify-between">
          <span>Mode: Demo Seed</span>
          <span className="bg-[#E8F7EF] text-[#16A36A] px-1.5 py-0.5 rounded font-semibold">Active</span>
        </div>
      </div>
    </aside>
  )
}
