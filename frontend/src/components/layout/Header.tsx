import React, { useEffect, useState } from 'react'
import { Shield } from 'lucide-react'
import { Link } from 'react-router-dom'
import { apiFetch } from '../../lib/api'
import { formatPaiseToINR } from '../../lib/formatters'

interface HeaderProps {
  title: string
  subtitle?: string
}

export const Header: React.FC<HeaderProps> = ({ title, subtitle }) => {
  const [bufferPaise, setBufferPaise] = useState<number | null>(null)

  useEffect(() => {
    let active = true
    const handleBufferUpdate = (event: Event) => {
      const value = (event as CustomEvent<number>).detail
      if (Number.isInteger(value)) setBufferPaise(value)
    }
    window.addEventListener('dukaanflow:safety-buffer-updated', handleBufferUpdate)
    apiFetch('/api/v1/settings')
      .then(async (response) => {
        if (!response.ok) return
        const data = await response.json()
        if (active && Number.isInteger(data.cash_safety_buffer_paise)) {
          setBufferPaise(data.cash_safety_buffer_paise)
        }
      })
      .catch((error) => console.error('Could not load safety buffer:', error))
    return () => {
      active = false
      window.removeEventListener('dukaanflow:safety-buffer-updated', handleBufferUpdate)
    }
  }, [])

  return (
    <header className="h-[72px] bg-white border-b border-[#E8EAED] px-6 lg:px-8 flex items-center justify-between sticky top-0 z-10">
      <div>
        <h2 className="text-xl font-bold text-[#17191C] tracking-tight">{title}</h2>
        {subtitle && <p className="text-xs text-[#737780] font-normal">{subtitle}</p>}
      </div>

      <div className="flex items-center gap-3">
        {/* Safety buffer pill */}
        <Link to="/settings" title="Configure cash safety buffer" className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-[#FEF6EB] text-[#E9A23B] border border-[#FCD34D] text-xs font-semibold hover:bg-[#FFF0D6] transition-colors">
          <Shield className="w-3.5 h-3.5" />
          <span>Buffer: {bufferPaise === null ? '…' : formatPaiseToINR(bufferPaise)}</span>
        </Link>

        {/* Demo data badge */}
        <div className="hidden sm:inline-flex items-center gap-1 px-2.5 py-1 rounded-md bg-[#F0F2F5] text-[#737780] text-xs font-medium">
          <span className="w-1.5 h-1.5 rounded-full bg-[#16A36A]"></span>
          Sample Data
        </div>

      </div>
    </header>
  )
}
