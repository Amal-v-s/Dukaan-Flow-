import React from 'react'
import { NavLink } from 'react-router-dom'
import { LayoutDashboard, Users, LineChart, SlidersHorizontal, MoreHorizontal } from 'lucide-react'

export const BottomNav: React.FC = () => {
  const items = [
    { name: 'Overview', to: '/', icon: LayoutDashboard },
    { name: 'Khata', to: '/customers', icon: Users },
    { name: 'Cash Flow', to: '/cash-flow', icon: LineChart },
    { name: 'Simulator', to: '/simulator', icon: SlidersHorizontal },
    { name: 'More', to: '/settings', icon: MoreHorizontal },
  ]

  return (
    <nav className="md:hidden fixed bottom-0 left-0 right-0 h-16 bg-white border-t border-[#E8EAED] flex items-center justify-around px-2 z-30">
      {items.map((item) => {
        const Icon = item.icon
        return (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === '/'}
            className={({ isActive }) =>
              `flex flex-col items-center justify-center py-1 px-2 text-[11px] font-medium transition-colors ${
                isActive ? 'text-[#16A36A] font-bold' : 'text-[#737780]'
              }`
            }
          >
            <Icon className="w-5 h-5 mb-0.5" />
            <span>{item.name}</span>
          </NavLink>
        )
      })}
    </nav>
  )
}
