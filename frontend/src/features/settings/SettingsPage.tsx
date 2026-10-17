import React, { useState, useEffect, useCallback } from 'react'
import { Shield, Store, CheckCircle2, AlertCircle, Loader2 } from 'lucide-react'
import { formatPaiseToINR } from '../../lib/formatters'

interface SettingsData {
  store_name: string
  currency: string
  timezone: string
  opening_cash_paise: number
  cash_safety_buffer_paise: number
}

export const SettingsPage: React.FC = () => {
  const [storeName, setStoreName] = useState('Demo Kirana Store')
  const [bufferInr, setBufferInr] = useState('15000')
  const [currency, setCurrency] = useState('INR')
  const [timezone, setTimezone] = useState('Asia/Kolkata')
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchSettings = useCallback(async () => {
    try {
      const res = await fetch('/api/v1/settings')
      if (res.ok) {
        const data: SettingsData = await res.json()
        setStoreName(data.store_name)
        setBufferInr((data.cash_safety_buffer_paise / 100).toString())
        setCurrency(data.currency)
        setTimezone(data.timezone)
      }
    } catch (err) {
      console.error('Failed to load settings:', err)
      setError('Could not load current settings.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void fetchSettings()
  }, [fetchSettings])

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault()
    setSaving(true)
    setError(null)

    const bufferNum = parseInt(bufferInr || '0', 10)
    if (isNaN(bufferNum) || bufferNum < 0) {
      setError('Please provide a valid non-negative buffer amount.')
      setSaving(false)
      return
    }

    try {
      const res = await fetch('/api/v1/settings', {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          store_name: storeName.trim() || 'Demo Kirana Store',
          cash_safety_buffer_paise: bufferNum * 100,
        }),
      })

      if (!res.ok) {
        const data = await res.json().catch(() => null)
        throw new Error(data?.error?.message || data?.detail || 'Failed to update settings')
      }

      const updated: SettingsData = await res.json()
      setStoreName(updated.store_name)
      setBufferInr((updated.cash_safety_buffer_paise / 100).toString())
      setSaved(true)
      setTimeout(() => setSaved(false), 3000)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error saving settings.')
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20 text-[#737780]">
        <Loader2 className="w-6 h-6 animate-spin mr-2" />
        <span className="text-xs font-semibold">Loading settings…</span>
      </div>
    )
  }

  return (
    <div className="space-y-6 max-w-3xl">
      {error && (
        <div role="alert" className="flex items-center gap-2 rounded-lg border border-[#FECACA] bg-[#FDF0F0] p-3 text-xs text-[#B91C1C]">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      <div className="bg-white rounded-xl border border-[#E8EAED] p-6 shadow-[0_1px_3px_rgba(0,0,0,0.04)]">
        <div className="flex items-center gap-2 pb-4 mb-4 border-b border-[#F0F2F5]">
          <Shield className="w-5 h-5 text-[#E9A23B]" />
          <div>
            <h3 className="text-sm font-bold text-[#17191C]">Cash Liquidity Safety Buffer</h3>
            <p className="text-xs text-[#737780]">Minimum liquid reserve balance before shortage warnings trigger</p>
          </div>
        </div>

        <form onSubmit={handleSave} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-[#17191C] mb-1">
              Store / Business Name
            </label>
            <input
              type="text"
              value={storeName}
              onChange={(e) => setStoreName(e.target.value)}
              className="max-w-md w-full px-3 py-2 bg-white border border-[#E8EAED] rounded-lg text-xs font-bold text-[#17191C] focus:outline-none focus:border-[#16A36A]"
              placeholder="e.g. Sharma Kirana"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-[#17191C] mb-1">
              Safety Buffer Threshold (₹ INR)
            </label>
            <div className="relative max-w-xs">
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-xs font-bold text-[#737780]">₹</span>
              <input
                type="number"
                value={bufferInr}
                onChange={(e) => setBufferInr(e.target.value)}
                className="w-full pl-8 pr-3 py-2 bg-white border border-[#E8EAED] rounded-lg text-xs font-bold tabular-nums text-[#17191C] focus:outline-none focus:border-[#16A36A]"
              />
            </div>
            <p className="text-[11px] text-[#737780] mt-1.5">
              Active buffer: <strong className="tabular-nums">{formatPaiseToINR(parseInt(bufferInr || '0', 10) * 100)}</strong>
            </p>
          </div>

          <div className="flex items-center gap-3 pt-2">
            <button
              type="submit"
              disabled={saving}
              className="px-4 py-2 bg-[#16A36A] hover:bg-[#0D6843] text-white text-xs font-bold rounded-lg transition-colors shadow-sm disabled:opacity-50 flex items-center gap-1.5"
            >
              {saving && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
              Update Settings
            </button>
            {saved && (
              <span className="text-xs font-semibold text-[#16A36A] flex items-center gap-1">
                <CheckCircle2 className="w-3.5 h-3.5" />
                Settings saved!
              </span>
            )}
          </div>
        </form>
      </div>

      <div className="bg-white rounded-xl border border-[#E8EAED] p-6 shadow-[0_1px_3px_rgba(0,0,0,0.04)]">
        <div className="flex items-center gap-2 pb-4 mb-4 border-b border-[#F0F2F5]">
          <Store className="w-5 h-5 text-[#737780]" />
          <div>
            <h3 className="text-sm font-bold text-[#17191C]">Store Configuration</h3>
            <p className="text-xs text-[#737780]">Store parameters and localization</p>
          </div>
        </div>

        <div className="space-y-3 text-xs">
          <div className="flex justify-between py-1 border-b border-[#F0F2F5]">
            <span className="text-[#737780]">Store Name:</span>
            <span className="font-semibold text-[#17191C]">{storeName}</span>
          </div>
          <div className="flex justify-between py-1 border-b border-[#F0F2F5]">
            <span className="text-[#737780]">Currency:</span>
            <span className="font-semibold text-[#17191C]">{currency} (₹)</span>
          </div>
          <div className="flex justify-between py-1 border-b border-[#F0F2F5]">
            <span className="text-[#737780]">Timezone:</span>
            <span className="font-semibold text-[#17191C]">{timezone}</span>
          </div>
          <div className="flex justify-between py-1 border-b border-[#F0F2F5]">
            <span className="text-[#737780]">Storage Format:</span>
            <span className="font-semibold text-[#17191C]">Integer Paise (Zero Floating-Point)</span>
          </div>
        </div>
      </div>
    </div>
  )
}
