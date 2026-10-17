import React, { useState, useEffect } from 'react'
import { RotateCcw, CheckCircle2, Shield } from 'lucide-react'
import { formatPaiseToINR } from '../../lib/formatters'

interface HeaderProps {
  title: string
  subtitle?: string
  onResetSeed?: () => Promise<void>
}

export const Header: React.FC<HeaderProps> = ({ title, subtitle, onResetSeed }) => {
  const [resetting, setResetting] = useState(false)
  const [resetSuccess, setResetSuccess] = useState(false)
  const [bufferPaise, setBufferPaise] = useState<number>(1500000)

  useEffect(() => {
    let mounted = true
    fetch('/api/v1/settings')
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        if (mounted && data?.cash_safety_buffer_paise != null) {
          setBufferPaise(data.cash_safety_buffer_paise)
        }
      })
      .catch(() => {})
    return () => {
      mounted = false
    }
  }, [])

  const handleReset = async () => {
    if (resetting) return
    setResetting(true)
    try {
      if (onResetSeed) {
        await onResetSeed()
      } else {
        const res = await fetch('/api/v1/seed/reset', { method: 'POST' })
        if (res.ok) {
          window.location.reload()
        }
      }
      setResetSuccess(true)
      setTimeout(() => setResetSuccess(false), 3000)
    } catch (err) {
      console.error('Reset failed:', err)
    } finally {
      setResetting(false)
    }
  }

  return (
    <header className="h-[72px] bg-white border-b border-[#E8EAED] px-6 lg:px-8 flex items-center justify-between sticky top-0 z-10">
      <div>
        <h2 className="text-xl font-bold text-[#17191C] tracking-tight">{title}</h2>
        {subtitle && <p className="text-xs text-[#737780] font-normal">{subtitle}</p>}
      </div>

      <div className="flex items-center gap-3">
        {/* Safety buffer pill */}
        <div className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-[#FEF6EB] text-[#E9A23B] border border-[#FCD34D] text-xs font-semibold">
          <Shield className="w-3.5 h-3.5" />
          <span>Buffer: {formatPaiseToINR(bufferPaise)}</span>
        </div>

        {/* Demo data badge */}
        <div className="hidden sm:inline-flex items-center gap-1 px-2.5 py-1 rounded-md bg-[#F0F2F5] text-[#737780] text-xs font-medium">
          <span className="w-1.5 h-1.5 rounded-full bg-[#16A36A]"></span>
          Sample Data
        </div>

        {/* Reset button */}
        <button
          onClick={handleReset}
          disabled={resetting}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-[#E8EAED] bg-white text-xs font-semibold text-[#17191C] hover:bg-[#F7F8FA] active:bg-[#F0F2F5] transition-colors disabled:opacity-50"
          title="Reset demo transactions and seed data"
        >
          <RotateCcw className={`w-3.5 h-3.5 text-[#737780] ${resetting ? 'animate-spin' : ''}`} />
          <span>{resetting ? 'Resetting...' : 'Reset Demo'}</span>
        </button>

        {resetSuccess && (
          <div className="flex items-center gap-1 text-xs text-[#16A36A] font-medium">
            <CheckCircle2 className="w-3.5 h-3.5" />
            <span>Reset!</span>
          </div>
        )}
      </div>
    </header>
  )
}
