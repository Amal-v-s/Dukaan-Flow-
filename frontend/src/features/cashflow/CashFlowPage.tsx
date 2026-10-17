import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { ShieldAlert, ChevronRight, SlidersHorizontal, Info } from 'lucide-react'
import { formatPaiseToINR, formatDate } from '../../lib/formatters'
import { StatusPill } from '../../components/ui/StatusPill'

interface ForecastDay {
  date: string
  opening_balance_paise: number
  inflows_paise: number
  outflows_paise: number
  closing_balance_paise: number
  below_zero: boolean
  below_safety_buffer: boolean
  contributors: Array<{
    source_type: string
    source_id: string
    description: string
    amount_paise: number
  }>
}

interface ForecastResponse {
  currency: string
  horizon_days: number
  cash_safety_buffer_paise: number
  lowest_dip_paise?: number
  lowest_dip_date?: string
  shortage_detected?: boolean
  buffer_breached?: boolean
  days: ForecastDay[]
  assumptions: string[]
}

interface CashAlert {
  id: string
  type: string
  severity: string
  title: string
  message: string
  breach_date: string
  projected_balance_paise: number
  deficit_paise: number
  acknowledged: boolean
  contributing_events: Array<{
    source_type: string
    source_id: string
    description: string
    amount_paise: number
    direction: string
  }>
  suggested_action: string
}

export const CashFlowPage: React.FC = () => {
  const [forecast, setForecast] = useState<ForecastResponse | null>(null)
  const [alerts, setAlerts] = useState<CashAlert[]>([])
  const [loading, setLoading] = useState(true)
  const [expandedDay, setExpandedDay] = useState<string | null>(null)

  useEffect(() => {
    const fetchForecastAndAlerts = async () => {
      try {
        const [fRes, aRes] = await Promise.all([
          fetch('/api/v1/cash-flow/forecast?horizon_days=14'),
          fetch('/api/v1/alerts'),
        ])
        if (fRes.ok) {
          const data = await fRes.json()
          setForecast(data)
        }
        if (aRes.ok) {
          const aData = await aRes.json()
          setAlerts(aData.alerts || [])
        }
      } catch (err) {
        console.error('Error fetching forecast:', err)
      } finally {
        setLoading(false)
      }
    }
    fetchForecastAndAlerts()
  }, [])

  if (loading || !forecast) {
    return (
      <div className="space-y-6 animate-pulse">
        <div className="h-48 bg-white rounded-xl border border-[#E8EAED]"></div>
        <div className="h-96 bg-white rounded-xl border border-[#E8EAED]"></div>
      </div>
    )
  }

  const minBalance = Math.min(...forecast.days.map((d) => d.closing_balance_paise))
  const maxBalance = Math.max(...forecast.days.map((d) => d.closing_balance_paise))

  return (
    <div className="space-y-6">
      {/* Active Shortage Alerts Panel */}
      {alerts.length > 0 && (
        <div className="space-y-3">
          {alerts.map((alert) => (
            <div
              key={alert.id}
              className={`rounded-xl p-4 sm:p-5 border-l-4 shadow-sm flex flex-col gap-3 ${
                alert.severity === 'critical'
                  ? 'bg-[#FDF0F0] border-[#DC5555]'
                  : 'bg-[#FEF6EB] border-[#E9A23B]'
              }`}
            >
              <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
                <div className="flex items-start gap-3">
                  <div
                    className={`w-9 h-9 rounded-lg flex items-center justify-center shrink-0 mt-0.5 ${
                      alert.severity === 'critical'
                        ? 'bg-[#FCE8E8] text-[#DC5555]'
                        : 'bg-[#FDF0D5] text-[#E9A23B]'
                    }`}
                  >
                    <ShieldAlert className="w-5 h-5" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="text-sm font-bold text-[#17191C]">{alert.title}</h3>
                      <StatusPill
                        label={alert.severity === 'critical' ? 'Deficit Warning' : 'Buffer Warning'}
                        variant={alert.severity === 'critical' ? 'alert' : 'warning'}
                      />
                    </div>
                    <p className="text-xs text-[#737780] mt-1">{alert.message}</p>
                  </div>
                </div>

                <Link
                  to="/simulator"
                  className={`px-3.5 py-2 rounded-lg text-white text-xs font-bold transition-colors flex items-center gap-1.5 shrink-0 self-end sm:self-auto ${
                    alert.severity === 'critical'
                      ? 'bg-[#DC5555] hover:bg-[#B91C1C]'
                      : 'bg-[#E9A23B] hover:bg-[#D97706]'
                  }`}
                >
                  <SlidersHorizontal className="w-3.5 h-3.5" />
                  <span>Test in What-If Simulator</span>
                  <ChevronRight className="w-3.5 h-3.5" />
                </Link>
              </div>

              {/* Attribution and Actionable Tips */}
              <div className="bg-white/90 rounded-lg p-3 text-xs border border-black/5 space-y-2">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="font-bold text-[#17191C]">Contributing Records:</span>
                  {alert.contributing_events.map((evt, idx) => (
                    <span
                      key={idx}
                      className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded bg-[#F7F8FA] border border-[#E8EAED] text-[11px]"
                    >
                      {evt.source_type === 'supplier_bill' ? (
                        <Link to="/suppliers" className="text-[#6D8FE8] hover:underline font-medium">
                          {evt.description}
                        </Link>
                      ) : (
                        <Link to="/khata" className="text-[#6D8FE8] hover:underline font-medium">
                          {evt.description}
                        </Link>
                      )}
                      <strong
                        className={`tabular-nums ${
                          evt.direction === 'outflow' ? 'text-[#DC5555]' : 'text-[#16A36A]'
                        }`}
                      >
                        {evt.direction === 'outflow' ? '-' : '+'}
                        {formatPaiseToINR(evt.amount_paise)}
                      </strong>
                    </span>
                  ))}
                </div>
                {alert.suggested_action && (
                  <p className="text-[11px] text-[#737780] font-medium flex items-center gap-1">
                    <Info className="w-3.5 h-3.5 text-[#6D8FE8] shrink-0" />
                    <span><strong className="text-[#17191C]">Merchant Plan:</strong> {alert.suggested_action}</span>
                  </p>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Forecast Header & Meta */}
      <div className="bg-white rounded-xl border border-[#E8EAED] p-5 shadow-[0_1px_3px_rgba(0,0,0,0.04)] flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="text-base font-bold text-[#17191C]">14-Day Deterministic Projection</h3>
            <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-[#EDF2FD] text-[#6D8FE8]">
              Projection Engine
            </span>
          </div>
          <p className="text-xs text-[#737780] mt-1">
            Calculated strictly from recorded credit sales due dates, scheduled supplier bills, and verified opening cash.
          </p>
        </div>

        <div className="flex items-center gap-4 text-xs">
          <div>
            <span className="text-[#737780] block text-[11px]">Safety Buffer Floor</span>
            <span className="font-bold text-[#E9A23B] tabular-nums">
              {formatPaiseToINR(forecast.cash_safety_buffer_paise)}
            </span>
          </div>
          <div className="h-8 w-px bg-[#E8EAED]"></div>
          <div>
            <span className="text-[#737780] block text-[11px]">Projected Lowest Dip</span>
            <span
              className={`font-bold tabular-nums ${
                minBalance < forecast.cash_safety_buffer_paise ? 'text-[#DC5555]' : 'text-[#16A36A]'
              }`}
            >
              {formatPaiseToINR(minBalance)}
            </span>
          </div>
        </div>
      </div>

      {/* Visual Chart Bars / Trajectory */}
      <div className="bg-white rounded-xl border border-[#E8EAED] p-5 shadow-[0_1px_3px_rgba(0,0,0,0.04)]">
        <div className="flex items-center justify-between mb-4">
          <span className="text-xs font-semibold text-[#737780] uppercase tracking-wider">
            Daily Projected Liquidity Trajectory
          </span>
          <div className="flex items-center gap-4 text-xs">
            <span className="flex items-center gap-1.5 text-[#6D8FE8]">
              <span className="w-2.5 h-2.5 rounded-sm bg-[#6D8FE8]"></span> Projected Closing
            </span>
            <span className="flex items-center gap-1.5 text-[#DC5555]">
              <span className="w-2.5 h-0.5 bg-[#DC5555]"></span> Safety Buffer (₹15,000)
            </span>
          </div>
        </div>

        {/* CSS based trajectory visualization */}
        <div className="grid grid-cols-7 sm:grid-cols-14 gap-2 pt-6 pb-2 items-end min-h-[160px] border-b border-[#E8EAED]">
          {forecast.days.map((day) => {
            const isAlert = day.below_safety_buffer || day.below_zero
            const heightPct = Math.max(
              15,
              Math.min(95, Math.round(((day.closing_balance_paise - Math.min(0, minBalance)) / (maxBalance - Math.min(0, minBalance) || 1)) * 100))
            )

            return (
              <div key={day.date} className="flex flex-col items-center gap-1 h-full justify-end group relative">
                {/* Tooltip on hover */}
                <div className="absolute -top-14 opacity-0 group-hover:opacity-100 transition-opacity bg-[#17191C] text-white text-[10px] p-2 rounded shadow-lg pointer-events-none z-20 whitespace-nowrap">
                  <p className="font-bold">{formatDate(day.date)}</p>
                  <p className="tabular-nums">Closing: {formatPaiseToINR(day.closing_balance_paise)}</p>
                  <p className="text-gray-300 tabular-nums">In: +{formatPaiseToINR(day.inflows_paise)} | Out: -{formatPaiseToINR(day.outflows_paise)}</p>
                </div>

                <span className="text-[10px] font-bold tabular-nums text-[#17191C]">
                  {formatPaiseToINR(day.closing_balance_paise, false)}
                </span>
                <div
                  style={{ height: `${heightPct}%` }}
                  className={`w-full max-w-[28px] rounded-t transition-all ${
                    isAlert ? 'bg-[#DC5555]' : 'bg-[#6D8FE8]'
                  } hover:brightness-110`}
                ></div>
                <span className="text-[10px] text-[#737780] font-medium mt-1">
                  {day.date.substring(8, 10)}
                </span>
              </div>
            )
          })}
        </div>
      </div>

      {/* 14-Day Table */}
      <div className="bg-white rounded-xl border border-[#E8EAED] overflow-hidden shadow-[0_1px_3px_rgba(0,0,0,0.04)]">
        <div className="p-4 bg-[#F7F8FA] border-b border-[#E8EAED] flex items-center justify-between">
          <h4 className="text-xs font-bold text-[#17191C] uppercase tracking-wider">Day-by-Day Forecast Breakdown</h4>
          <span className="text-xs text-[#737780]">Click any row with movements to see contributors</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-[#F0F2F5] text-[#737780] font-semibold uppercase tracking-wider border-b border-[#E8EAED]">
              <tr>
                <th className="py-3 px-4">Date</th>
                <th className="py-3 px-4 text-right">Opening Cash</th>
                <th className="py-3 px-4 text-right">Expected Inflows</th>
                <th className="py-3 px-4 text-right">Scheduled Outflows</th>
                <th className="py-3 px-4 text-right">Projected Closing</th>
                <th className="py-3 px-4">Liquidity Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#E8EAED] text-[#17191C]">
              {forecast.days.map((day) => {
                const hasContributors = day.contributors && day.contributors.length > 0
                const isExpanded = expandedDay === day.date

                return (
                  <React.Fragment key={day.date}>
                    <tr
                      onClick={() => hasContributors && setExpandedDay(isExpanded ? null : day.date)}
                      className={`transition-colors ${
                        hasContributors ? 'cursor-pointer hover:bg-[#F9FAFB]' : ''
                      } ${day.below_safety_buffer ? 'bg-[#FDF0F0]/30' : ''}`}
                    >
                      <td className="py-3 px-4 font-semibold text-[#17191C] flex items-center gap-1.5">
                        <span>{formatDate(day.date)}</span>
                        {hasContributors && (
                          <span className="text-[10px] px-1.5 py-0.2 rounded bg-[#EDF2FD] text-[#6D8FE8] font-bold">
                            {day.contributors.length} item{day.contributors.length > 1 ? 's' : ''}
                          </span>
                        )}
                      </td>
                      <td className="py-3 px-4 text-right tabular-nums text-[#737780]">
                        {formatPaiseToINR(day.opening_balance_paise)}
                      </td>
                      <td className="py-3 px-4 text-right tabular-nums font-medium text-[#16A36A]">
                        {day.inflows_paise > 0 ? `+${formatPaiseToINR(day.inflows_paise)}` : '₹0'}
                      </td>
                      <td className="py-3 px-4 text-right tabular-nums font-medium text-[#17191C]">
                        {day.outflows_paise > 0 ? `-${formatPaiseToINR(day.outflows_paise)}` : '₹0'}
                      </td>
                      <td
                        className={`py-3 px-4 text-right font-bold tabular-nums ${
                          day.below_safety_buffer ? 'text-[#DC5555]' : 'text-[#17191C]'
                        }`}
                      >
                        {formatPaiseToINR(day.closing_balance_paise)}
                      </td>
                      <td className="py-3 px-4">
                        {day.below_zero ? (
                          <StatusPill label="DEFICIT / CRITICAL" variant="alert" />
                        ) : day.below_safety_buffer ? (
                          <StatusPill label="BUFFER BREACH" variant="warning" />
                        ) : (
                          <StatusPill label="HEALTHY" variant="safe" />
                        )}
                      </td>
                    </tr>

                    {/* Expandable contributors sub-row */}
                    {isExpanded && hasContributors && (
                      <tr className="bg-[#F7F8FA]">
                        <td colSpan={6} className="px-6 py-2.5">
                          <div className="text-[11px] space-y-1">
                            <span className="font-bold text-[#737780] uppercase tracking-wider block">Contributing Events on {formatDate(day.date)}:</span>
                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                              {day.contributors.map((c, i) => (
                                <div key={i} className="flex items-center justify-between p-2 rounded bg-white border border-[#E8EAED]">
                                  <span className="font-medium text-[#17191C]">{c.description}</span>
                                  <span
                                    className={`font-bold tabular-nums ${
                                      c.source_type.includes('bill') || c.source_type.includes('expense')
                                        ? 'text-[#DC5555]'
                                        : 'text-[#16A36A]'
                                    }`}
                                  >
                                    {c.source_type.includes('bill') || c.source_type.includes('expense') ? '-' : '+'}
                                    {formatPaiseToINR(c.amount_paise)}
                                  </span>
                                </div>
                              ))}
                            </div>
                          </div>
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
                )
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
