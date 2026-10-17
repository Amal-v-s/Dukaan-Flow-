import React, { useEffect, useState } from 'react'
import {
  SlidersHorizontal,
  RotateCcw,
  CheckCircle2,
  TrendingUp,
} from 'lucide-react'
import { formatPaiseToINR, formatDate } from '../../lib/formatters'
import { StatusPill } from '../../components/ui/StatusPill'

interface ScenarioForecastDay {
  date: string
  baseline_closing_paise: number
  scenario_closing_paise: number
  delta_paise: number
  baseline_below_zero: boolean
  scenario_below_zero: boolean
  baseline_below_buffer: boolean
  scenario_below_buffer: boolean
}

interface ScenarioForecastResponse {
  scenario_id: string
  scenario_name: string
  currency: string
  horizon_days: number
  safety_buffer_paise: number
  baseline_lowest_dip_paise: number
  baseline_lowest_dip_date: string
  baseline_has_shortage: boolean
  scenario_lowest_dip_paise: number
  scenario_lowest_dip_date: string
  scenario_has_shortage: boolean
  net_improvement_paise: number
  shortage_resolved: boolean
  days: ScenarioForecastDay[]
}

export const SimulatorPage: React.FC = () => {
  // Hypothetical scenario levers
  const [advanceCollection, setAdvanceCollection] = useState(true)
  const [delaySupplierBill, setDelaySupplierBill] = useState(false)
  const [extraExpenseINR, setExtraExpenseINR] = useState(0)

  const [forecastComparison, setForecastComparison] = useState<ScenarioForecastResponse | null>(null)
  const [loading, setLoading] = useState(true)

  const runSimulation = async (
    adv: boolean,
    delay: boolean,
    exp: number
  ) => {
    setLoading(true)
    try {
      // Build hypothetical events based on selected levers
      const events = []
      if (adv) {
        events.push({
          event_type: 'customer_collection',
          source_id: 'entry_ravi_01',
          amount_paise: 5000000,
          original_date: '2026-10-22',
          scenario_date: '2026-10-19',
          description: 'Collect Ravi Stores 3 days earlier (19 Oct)',
        })
      }
      if (delay) {
        events.push({
          event_type: 'supplier_bill',
          source_id: 'bill_coastal_101',
          amount_paise: 2500000,
          original_date: '2026-10-20',
          scenario_date: '2026-10-25',
          description: 'Delay Coastal Wholesale bill to 25 Oct',
        })
      }
      if (exp > 0) {
        events.push({
          event_type: 'extra_expense',
          amount_paise: exp * 100,
          scenario_date: '2026-10-19',
          description: `Simulated Shop Repair / Expense (₹${exp})`,
        })
      }

      // Create transient scenario
      const scenRes = await fetch('/api/v1/scenarios', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: 'Interactive Merchant Scenario',
          description: 'Simulated from UI controls',
          events,
        }),
      })

      if (scenRes.ok) {
        const scenData = await scenRes.json()
        // Run forecast comparison
        const fRes = await fetch(`/api/v1/scenarios/${scenData.id}/forecast?horizon_days=14`, {
          method: 'POST',
        })
        if (fRes.ok) {
          const compData = await fRes.json()
          setForecastComparison(compData)
        }
      }
    } catch (err) {
      console.error('Simulation error:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    runSimulation(advanceCollection, delaySupplierBill, extraExpenseINR)
  }, [advanceCollection, delaySupplierBill, extraExpenseINR])

  const handleReset = () => {
    setAdvanceCollection(false)
    setDelaySupplierBill(false)
    setExtraExpenseINR(0)
  }

  return (
    <div className="space-y-6">
      {/* Simulation Banner & Sandbox Notice */}
      <div className="bg-[#EDF2FD] border border-[#BFDBFE] rounded-xl p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <SlidersHorizontal className="w-5 h-5 text-[#6D8FE8]" />
            <h3 className="text-base font-bold text-[#17191C]">Isolated Cash Flow Simulator</h3>
            <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-white text-[#6D8FE8] border border-[#BFDBFE]">
              Pure Sandbox Mode
            </span>
          </div>
          <p className="text-xs text-[#737780] mt-1">
            Test "What-If" payment rescheduling or sudden expenses in real time. Simulations compute in memory and{' '}
            <strong className="text-[#17191C]">never modify your live Khata, Bills, or Register</strong>.
          </p>
        </div>

        <button
          onClick={handleReset}
          className="px-3.5 py-1.5 rounded-lg border border-[#BFDBFE] bg-white text-xs font-semibold text-[#6D8FE8] hover:bg-[#EDF2FD] transition-colors flex items-center gap-1.5 shrink-0 self-start sm:self-auto"
        >
          <RotateCcw className="w-3.5 h-3.5" />
          <span>Reset to Baseline</span>
        </button>
      </div>

      {/* Baseline vs Scenario Comparison KPI Cards */}
      {forecastComparison && (
        <div className={`grid grid-cols-1 md:grid-cols-2 gap-6 ${loading ? 'opacity-70 transition-opacity' : ''}`}>
          {/* Baseline Card */}
          <div className="bg-white rounded-xl border border-[#E8EAED] p-5 shadow-[0_1px_3px_rgba(0,0,0,0.04)]">
            <div className="flex items-center justify-between pb-3 mb-3 border-b border-[#F0F2F5]">
              <span className="text-xs font-bold text-[#737780] uppercase tracking-wider">
                Baseline (Actual Recorded)
              </span>
              <StatusPill
                label={forecastComparison.baseline_has_shortage ? 'Deficit Risk' : 'Healthy'}
                variant={forecastComparison.baseline_has_shortage ? 'alert' : 'safe'}
              />
            </div>

            <div className="space-y-3">
              <div>
                <span className="text-xs text-[#737780]">Projected Lowest Dip</span>
                <p
                  className={`text-2xl font-bold tabular-nums ${
                    forecastComparison.baseline_lowest_dip_paise < 0 ? 'text-[#DC5555]' : 'text-[#17191C]'
                  }`}
                >
                  {formatPaiseToINR(forecastComparison.baseline_lowest_dip_paise)}
                </p>
                <p className="text-xs text-[#737780] mt-0.5">
                  Occurs on {formatDate(forecastComparison.baseline_lowest_dip_date)}
                </p>
              </div>
              <div className="p-3 rounded-lg bg-[#FDF0F0] text-xs text-[#DC5555] space-y-1">
                <p className="font-semibold">Root cause of deficit:</p>
                <p>• Supplier Coastal Wholesale bill ₹25,000 due 20 Oct</p>
                <p>• Ravi Stores ₹50,000 repayment scheduled only on 22 Oct</p>
              </div>
            </div>
          </div>

          {/* Scenario Result Card */}
          <div
            className={`bg-white rounded-xl border-2 p-5 shadow-[0_1px_3px_rgba(0,0,0,0.04)] relative ${
              forecastComparison.shortage_resolved
                ? 'border-[#16A36A]'
                : forecastComparison.scenario_has_shortage
                ? 'border-[#DC5555]'
                : 'border-[#E9A23B]'
            }`}
          >
            <div className="flex items-center justify-between pb-3 mb-3 border-b border-[#F0F2F5]">
              <span
                className={`text-xs font-bold uppercase tracking-wider ${
                  forecastComparison.shortage_resolved ? 'text-[#16A36A]' : 'text-[#17191C]'
                }`}
              >
                Simulated Scenario Outcome
              </span>
              <StatusPill
                label={
                  forecastComparison.shortage_resolved
                    ? 'Shortage Averted'
                    : forecastComparison.scenario_has_shortage
                    ? 'Deficit Persists'
                    : 'Buffer Warning'
                }
                variant={
                  forecastComparison.shortage_resolved
                    ? 'safe'
                    : forecastComparison.scenario_has_shortage
                    ? 'alert'
                    : 'warning'
                }
              />
            </div>

            <div className="space-y-3">
              <div>
                <span className="text-xs text-[#737780]">Simulated Lowest Dip</span>
                <p
                  className={`text-2xl font-bold tabular-nums ${
                    forecastComparison.scenario_lowest_dip_paise >= forecastComparison.safety_buffer_paise
                      ? 'text-[#16A36A]'
                      : forecastComparison.scenario_lowest_dip_paise >= 0
                      ? 'text-[#E9A23B]'
                      : 'text-[#DC5555]'
                  }`}
                >
                  {formatPaiseToINR(forecastComparison.scenario_lowest_dip_paise)}
                </p>
                <p className="text-xs text-[#16A36A] font-medium mt-0.5 flex items-center gap-1">
                  <TrendingUp className="w-3.5 h-3.5" />
                  <span>
                    Net Liquidity Shift: +{formatPaiseToINR(forecastComparison.net_improvement_paise)}
                  </span>
                </p>
              </div>

              <div
                className={`p-3 rounded-lg text-xs space-y-1 ${
                  forecastComparison.shortage_resolved
                    ? 'bg-[#E8F7EF] text-[#16A36A]'
                    : forecastComparison.scenario_has_shortage
                    ? 'bg-[#FDF0F0] text-[#DC5555]'
                    : 'bg-[#FEF6EB] text-[#E9A23B]'
                }`}
              >
                <p className="font-semibold">Simulated effect:</p>
                {advanceCollection && <p>✓ Ravi Stores repayment shifted to 19 Oct (+₹50,000 in hand)</p>}
                {delaySupplierBill && <p>✓ Coastal Wholesale bill deferred to 25 Oct (+₹25,000 liquidity)</p>}
                {extraExpenseINR > 0 && <p>• Unplanned expense of ₹{extraExpenseINR.toLocaleString('en-IN')} applied</p>}
                {!advanceCollection && !delaySupplierBill && extraExpenseINR === 0 && (
                  <p>Baseline configuration. Select levers below to simulate improvements.</p>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Interactive Levers Control Panel */}
      <div className="bg-white rounded-xl border border-[#E8EAED] p-5 shadow-[0_1px_3px_rgba(0,0,0,0.04)]">
        <h4 className="text-xs font-bold text-[#17191C] uppercase tracking-wider mb-4">
          Interactive Simulation Controls & Actionable Levers
        </h4>

        <div className="space-y-4">
          <label className="flex items-start gap-3 p-3.5 rounded-lg border border-[#E8EAED] hover:bg-[#F9FAFB] cursor-pointer transition-colors">
            <input
              type="checkbox"
              checked={advanceCollection}
              onChange={(e) => setAdvanceCollection(e.target.checked)}
              className="mt-1 h-4 w-4 rounded text-[#16A36A] focus:ring-[#16A36A]"
            />
            <div>
              <p className="text-xs font-bold text-[#17191C]">
                Collect from Ravi Stores 3 days earlier (19 Oct instead of 22 Oct)
              </p>
              <p className="text-[11px] text-[#737780] mt-0.5">
                Brings ₹50,000 credit repayment in hand before the Coastal Wholesale bill arrives.
              </p>
            </div>
          </label>

          <label className="flex items-start gap-3 p-3.5 rounded-lg border border-[#E8EAED] hover:bg-[#F9FAFB] cursor-pointer transition-colors">
            <input
              type="checkbox"
              checked={delaySupplierBill}
              onChange={(e) => setDelaySupplierBill(e.target.checked)}
              className="mt-1 h-4 w-4 rounded text-[#16A36A] focus:ring-[#16A36A]"
            />
            <div>
              <p className="text-xs font-bold text-[#17191C]">
                Negotiate supplier bill extension (pay Coastal Wholesale on 25 Oct)
              </p>
              <p className="text-[11px] text-[#737780] mt-0.5">
                Defers ₹25,000 outflow past the scheduled collection dates.
              </p>
            </div>
          </label>

          <div className="p-3.5 rounded-lg border border-[#E8EAED] bg-[#F7F8FA] flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div>
              <label className="block text-xs font-bold text-[#17191C]">
                Simulate Unplanned Shop Operating Expense (₹ INR)
              </label>
              <p className="text-[11px] text-[#737780] mt-0.5">
                Stress-test cash resilience if unexpected repairs, taxes, or stock purchases occur.
              </p>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-semibold text-[#737780]">₹</span>
              <input
                type="number"
                placeholder="e.g. 5000"
                value={extraExpenseINR || ''}
                onChange={(e) => setExtraExpenseINR(Math.max(0, parseInt(e.target.value || '0', 10)))}
                className="px-3 py-1.5 bg-white border border-[#E8EAED] rounded-lg text-xs font-bold tabular-nums text-[#17191C] w-36 focus:outline-none focus:border-[#16A36A]"
              />
            </div>
          </div>
        </div>
      </div>

      {/* Trajectory Comparison Chart */}
      {forecastComparison && (
        <div className="bg-white rounded-xl border border-[#E8EAED] p-5 shadow-[0_1px_3px_rgba(0,0,0,0.04)]">
          <div className="flex items-center justify-between mb-4">
            <span className="text-xs font-semibold text-[#737780] uppercase tracking-wider">
              14-Day Trajectory: Baseline vs Scenario
            </span>
            <div className="flex items-center gap-4 text-xs">
              <span className="flex items-center gap-1.5 text-[#737780]">
                <span className="w-2.5 h-2.5 rounded-sm bg-[#737780]/40"></span> Baseline Closing
              </span>
              <span className="flex items-center gap-1.5 text-[#16A36A]">
                <span className="w-2.5 h-2.5 rounded-sm bg-[#16A36A]"></span> Simulated Closing
              </span>
              <span className="flex items-center gap-1.5 text-[#DC5555]">
                <span className="w-2.5 h-0.5 bg-[#DC5555]"></span> Zero Line
              </span>
            </div>
          </div>

          <div className="grid grid-cols-7 sm:grid-cols-14 gap-2 pt-6 pb-2 items-end min-h-[160px] border-b border-[#E8EAED]">
            {forecastComparison.days.map((day) => {
              const bClosing = day.baseline_closing_paise
              const sClosing = day.scenario_closing_paise

              return (
                <div key={day.date} className="flex flex-col items-center gap-1 h-full justify-end group relative">
                  {/* Tooltip */}
                  <div className="absolute -top-16 opacity-0 group-hover:opacity-100 transition-opacity bg-[#17191C] text-white text-[10px] p-2 rounded shadow-lg pointer-events-none z-20 whitespace-nowrap">
                    <p className="font-bold">{formatDate(day.date)}</p>
                    <p className="text-gray-300 tabular-nums">Baseline: {formatPaiseToINR(bClosing)}</p>
                    <p className="text-[#16A36A] tabular-nums font-bold">Scenario: {formatPaiseToINR(sClosing)}</p>
                    <p className="text-blue-300 tabular-nums">Delta: {day.delta_paise >= 0 ? '+' : ''}{formatPaiseToINR(day.delta_paise)}</p>
                  </div>

                  <span className="text-[10px] font-bold tabular-nums text-[#17191C]">
                    {formatPaiseToINR(sClosing, false)}
                  </span>
                  <div className="w-full flex items-end justify-center gap-1 h-28">
                    {/* Baseline Bar */}
                    <div
                      style={{ height: `${Math.max(10, Math.min(100, Math.round(((bClosing + 2000000) / 10000000) * 100)))}%` }}
                      className={`w-2.5 rounded-t ${bClosing < 0 ? 'bg-[#DC5555]/60' : 'bg-[#737780]/30'}`}
                    ></div>
                    {/* Scenario Bar */}
                    <div
                      style={{ height: `${Math.max(10, Math.min(100, Math.round(((sClosing + 2000000) / 10000000) * 100)))}%` }}
                      className={`w-2.5 rounded-t ${
                        sClosing < 0
                          ? 'bg-[#DC5555]'
                          : sClosing < forecastComparison.safety_buffer_paise
                          ? 'bg-[#E9A23B]'
                          : 'bg-[#16A36A]'
                      }`}
                    ></div>
                  </div>
                  <span className="text-[10px] text-[#737780] font-medium mt-1">
                    {day.date.substring(8, 10)}
                  </span>
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* Comparative Day Breakdown Table */}
      {forecastComparison && (
        <div className="bg-white rounded-xl border border-[#E8EAED] overflow-hidden shadow-[0_1px_3px_rgba(0,0,0,0.04)]">
          <div className="p-4 bg-[#F7F8FA] border-b border-[#E8EAED] flex items-center justify-between">
            <h4 className="text-xs font-bold text-[#17191C] uppercase tracking-wider">
              Day-by-Day Impact Analysis
            </h4>
            <span className="text-xs text-[#737780]">Baseline vs Simulated Delta</span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-[#F0F2F5] text-[#737780] font-semibold uppercase tracking-wider border-b border-[#E8EAED]">
                <tr>
                  <th className="py-3 px-4">Date</th>
                  <th className="py-3 px-4 text-right">Baseline Closing</th>
                  <th className="py-3 px-4 text-right">Simulated Closing</th>
                  <th className="py-3 px-4 text-right">Net Delta</th>
                  <th className="py-3 px-4">Status Comparison</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#E8EAED] text-[#17191C]">
                {forecastComparison.days.map((day) => (
                  <tr key={day.date} className="hover:bg-[#F9FAFB] transition-colors">
                    <td className="py-3 px-4 font-semibold text-[#17191C]">{formatDate(day.date)}</td>
                    <td
                      className={`py-3 px-4 text-right tabular-nums ${
                        day.baseline_below_zero ? 'text-[#DC5555] font-bold' : 'text-[#737780]'
                      }`}
                    >
                      {formatPaiseToINR(day.baseline_closing_paise)}
                    </td>
                    <td
                      className={`py-3 px-4 text-right tabular-nums font-bold ${
                        day.scenario_below_zero
                          ? 'text-[#DC5555]'
                          : day.scenario_below_buffer
                          ? 'text-[#E9A23B]'
                          : 'text-[#16A36A]'
                      }`}
                    >
                      {formatPaiseToINR(day.scenario_closing_paise)}
                    </td>
                    <td
                      className={`py-3 px-4 text-right font-bold tabular-nums ${
                        day.delta_paise > 0
                          ? 'text-[#16A36A]'
                          : day.delta_paise < 0
                          ? 'text-[#DC5555]'
                          : 'text-[#737780]'
                      }`}
                    >
                      {day.delta_paise > 0 ? `+${formatPaiseToINR(day.delta_paise)}` : day.delta_paise < 0 ? formatPaiseToINR(day.delta_paise) : '—'}
                    </td>
                    <td className="py-3 px-4">
                      {day.baseline_below_zero && !day.scenario_below_zero ? (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-bold bg-[#E8F7EF] text-[#16A36A]">
                          <CheckCircle2 className="w-3 h-3" /> Deficit Resolved
                        </span>
                      ) : day.scenario_below_zero ? (
                        <StatusPill label="Critical Deficit" variant="alert" />
                      ) : day.scenario_below_buffer ? (
                        <StatusPill label="Buffer Breach" variant="warning" />
                      ) : (
                        <StatusPill label="Healthy" variant="safe" />
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
