import React, { useState } from 'react'
import { Shield, Store, CheckCircle2 } from 'lucide-react'
import { formatPaiseToINR } from '../../lib/formatters'

export const SettingsPage: React.FC = () => {
  const [bufferInr, setBufferInr] = useState('15000')
  const [saved, setSaved] = useState(false)

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault()
    setSaved(true)
    setTimeout(() => setSaved(false), 2500)
  }

  return (
    <div className="space-y-6 max-w-3xl">
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
              Current buffer: <strong className="tabular-nums">{formatPaiseToINR(parseInt(bufferInr || '0', 10) * 100)}</strong>
            </p>
          </div>

          <div className="flex items-center gap-3 pt-2">
            <button
              type="submit"
              className="px-4 py-2 bg-[#16A36A] hover:bg-[#0D6843] text-white text-xs font-bold rounded-lg transition-colors shadow-sm"
            >
              Update Buffer
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
            <span className="font-semibold text-[#17191C]">Demo Kirana Store</span>
          </div>
          <div className="flex justify-between py-1 border-b border-[#F0F2F5]">
            <span className="text-[#737780]">Currency:</span>
            <span className="font-semibold text-[#17191C]">INR (₹)</span>
          </div>
          <div className="flex justify-between py-1 border-b border-[#F0F2F5]">
            <span className="text-[#737780]">Timezone:</span>
            <span className="font-semibold text-[#17191C]">Asia/Kolkata</span>
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
