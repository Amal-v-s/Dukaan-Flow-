import React, { useEffect, useState } from 'react'
import {
  Wallet,
  ArrowDownLeft,
  ArrowUpRight,
  AlertOctagon,
  Calendar,
  CheckCircle2,
  TrendingDown,
  TrendingUp,
  Clock,
  ChevronRight,
  ShieldAlert
} from 'lucide-react'
import { MetricCard } from '../../components/ui/MetricCard'
import { StatusPill } from '../../components/ui/StatusPill'
import { formatPaiseToINR, formatDate } from '../../lib/formatters'
import { Link } from 'react-router-dom'

interface DashboardData {
  currency: string
  available_cash_paise: number
  receivables_paise: number
  payables_paise: number
  today_income_paise: number
  today_expenses_paise: number
  forecast: {
    horizon_days: number
    lowest_balance_paise: number
    lowest_balance_date: string
    has_shortage: boolean
    safety_buffer_breach: boolean
  }
  recent_transactions: Array<{
    id: string
    type: string
    description: string
    amount_paise: number
    date: string
    direction: 'inflow' | 'outflow'
  }>
  upcoming_items: Array<{
    id: string
    title: string
    entity_type: 'customer_due' | 'supplier_bill' | 'expense'
    amount_paise: number
    due_date: string
    status: string
  }>
  next_installments_due: Array<{ plan_id: string; installment_id: string; customer_name: string; due_date: string; amount_paise: number }>
  overdue_plan_count: number
  budget_alert_count: number
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

export const DashboardPage: React.FC = () => {
  const [data, setData] = useState<DashboardData | null>(null)
  const [alerts, setAlerts] = useState<CashAlert[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchDashboard = async () => {
    setLoading(true)
    setError(null)
    try {
      const [dashRes, alertRes] = await Promise.all([
        fetch('/api/v1/dashboard'),
        fetch('/api/v1/alerts'),
      ])
      if (!dashRes.ok) {
        throw new Error(`Failed to load dashboard: ${dashRes.statusText}`)
      }
      const json = await dashRes.json()
      setData(json)

      if (alertRes.ok) {
        const alertJson = await alertRes.json()
        setAlerts(alertJson.alerts || [])
      }
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message)
      } else {
        setError('An unexpected error occurred')
      }
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchDashboard()
  }, [])

  if (loading) {
    return (
      <div className="space-y-6 animate-pulse">
        <div className="h-28 bg-white rounded-xl border border-[#E8EAED]"></div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-32 bg-white rounded-xl border border-[#E8EAED]"></div>
          ))}
        </div>
      </div>
    )
  }

  if (error || !data) {
    return (
      <div className="bg-[#FDF0F0] border border-[#FECACA] rounded-xl p-6 text-center text-[#DC5555]">
        <AlertOctagon className="w-8 h-8 mx-auto mb-2 text-[#DC5555]" />
        <h3 className="font-bold text-base">Unable to load dashboard data</h3>
        <p className="text-xs mt-1 text-[#737780]">{error || 'Could not connect to API server'}</p>
        <button
          onClick={fetchDashboard}
          className="mt-4 px-4 py-2 bg-[#DC5555] text-white text-xs font-semibold rounded-lg hover:bg-[#B91C1C] transition-colors"
        >
          Retry
        </button>
      </div>
    )
  }

  const handleAcknowledgeAlert = async (alertId: string) => {
    try {
      await fetch(`/api/v1/alerts/${alertId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ acknowledged: true }),
      })
      setAlerts((prev) => prev.filter((a) => a.id !== alertId))
    } catch (err) {
      console.error('Failed to acknowledge alert:', err)
    }
  }

  return (
    <div className="space-y-6">
      {/* Shortage / Safety Alert Banners */}
      {alerts.map((alert) => (
        <div
          key={alert.id}
          className={`rounded-xl p-4 sm:p-5 flex flex-col gap-3 shadow-sm border-l-4 ${
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
                    label={alert.severity === 'critical' ? 'Critical Deficit' : 'Buffer Breach'}
                    variant={alert.severity === 'critical' ? 'alert' : 'warning'}
                  />
                </div>
                <p className="text-xs text-[#737780] mt-1">{alert.message}</p>
              </div>
            </div>

            <div className="flex items-center gap-2 shrink-0 self-end sm:self-auto">
              <button
                onClick={() => handleAcknowledgeAlert(alert.id)}
                className="px-3 py-1.5 text-xs font-semibold text-[#737780] hover:text-[#17191C] bg-white border border-[#E8EAED] rounded-lg transition-colors"
              >
                Dismiss
              </button>
              <Link
                to="/simulator"
                className={`px-3.5 py-1.5 rounded-lg text-white text-xs font-bold transition-colors flex items-center gap-1.5 ${
                  alert.severity === 'critical'
                    ? 'bg-[#DC5555] hover:bg-[#B91C1C]'
                    : 'bg-[#E9A23B] hover:bg-[#D97706]'
                }`}
              >
                <span>Run What-If Simulation</span>
                <ChevronRight className="w-3.5 h-3.5" />
              </Link>
            </div>
          </div>

          {/* Contributing Events Breakdown */}
          {alert.contributing_events.length > 0 && (
            <div className="bg-white/80 rounded-lg p-3 text-xs border border-black/5 mt-1">
              <span className="font-bold text-[#17191C] block mb-1">Key Contributing Commitments:</span>
              <div className="flex flex-wrap gap-2">
                {alert.contributing_events.map((evt, idx) => (
                  <span
                    key={idx}
                    className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-[#F7F8FA] border border-[#E8EAED] text-[11px]"
                  >
                    <span className="font-medium text-[#17191C]">{evt.description}:</span>
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
                <p className="text-[11px] text-[#737780] mt-2 font-medium">
                  💡 <strong className="text-[#17191C]">Suggested Action:</strong> {alert.suggested_action}
                </p>
              )}
            </div>
          )}
        </div>
      ))}


      {/* Primary KPI Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        <MetricCard
          label="AVAILABLE CASH"
          amountPaise={data.available_cash_paise}
          icon={Wallet}
          accent="emerald"
          statusText="Actual In Hand"
          subtext="Excludes dues"
        />
        <MetricCard
          label="RECEIVABLES (UDHAAR)"
          amountPaise={data.receivables_paise}
          icon={ArrowDownLeft}
          accent="blue"
          statusText="Customers Owe You"
          subtext="Estimated inflow"
        />
        <MetricCard
          label="PAYABLES (DUE BILLS)"
          amountPaise={data.payables_paise}
          icon={ArrowUpRight}
          accent="amber"
          statusText="You Owe Suppliers"
          subtext="Mandatory outflow"
        />
        <MetricCard
          label="14-DAY FORECAST LOW"
          amountPaise={data.forecast.lowest_balance_paise}
          icon={Calendar}
          accent={data.forecast.has_shortage ? 'red' : 'emerald'}
          statusText={data.forecast.has_shortage ? 'Shortage Detected' : 'Liquidity Safe'}
          subtext={`Lowest on ${formatDate(data.forecast.lowest_balance_date)}`}
        />
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        <Link to="/management" className="rounded-xl border border-[#E8EAED] bg-white p-4 hover:border-[#16A36A]">
          <p className="text-xs text-[#737780]">Next repayment instalments</p>
          <strong className="text-lg">{data.next_installments_due.length}</strong>
          <p className="mt-1 text-xs text-[#737780]">{data.next_installments_due[0] ? `${data.next_installments_due[0].customer_name} · ${formatPaiseToINR(data.next_installments_due[0].amount_paise)} due ${formatDate(data.next_installments_due[0].due_date)}` : 'No scheduled instalments'}</p>
        </Link>
        <Link to="/management" className="rounded-xl border border-[#E8EAED] bg-white p-4 hover:border-[#E9A23B]">
          <p className="text-xs text-[#737780]">Overdue repayment plans</p><strong className="text-lg">{data.overdue_plan_count}</strong><p className="mt-1 text-xs text-[#737780]">Calculated from due dates and unpaid amounts</p>
        </Link>
        <Link to="/management" className="rounded-xl border border-[#E8EAED] bg-white p-4 hover:border-[#DC5555]">
          <p className="text-xs text-[#737780]">Budget threshold alerts</p><strong className="text-lg">{data.budget_alert_count}</strong><p className="mt-1 text-xs text-[#737780]">Based on recorded expenses</p>
        </Link>
      </div>

      {/* Lower Split: Upcoming Obligations vs Recent Transactions */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Upcoming Obligations */}
        <div className="bg-white rounded-xl border border-[#E8EAED] p-5 shadow-[0_1px_3px_rgba(0,0,0,0.04)]">
          <div className="flex items-center justify-between pb-3 mb-3 border-b border-[#F0F2F5]">
            <div className="flex items-center gap-2">
              <Clock className="w-4 h-4 text-[#737780]" />
              <h3 className="text-sm font-bold text-[#17191C]">Upcoming Dues & Collections</h3>
            </div>
            <Link to="/cash-flow" className="text-xs font-semibold text-[#16A36A] hover:underline flex items-center gap-1">
              <span>View 14-day flow</span>
              <ChevronRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          <div className="divide-y divide-[#F0F2F5]">
            {data.upcoming_items.length === 0 ? (
              <p className="text-xs text-[#737780] py-6 text-center">No upcoming bills or expected collections.</p>
            ) : (
              data.upcoming_items.map((item) => (
                <div key={item.id} className="py-3 flex items-center justify-between">
                  <div className="min-w-0 pr-3">
                    <p className="text-xs font-semibold text-[#17191C] truncate">{item.title}</p>
                    <p className="text-[11px] text-[#737780] mt-0.5">Due: {formatDate(item.due_date)}</p>
                  </div>
                  <div className="text-right shrink-0">
                    <p
                      className={`text-xs font-bold tabular-nums ${
                        item.entity_type === 'customer_due' ? 'text-[#16A36A]' : 'text-[#17191C]'
                      }`}
                    >
                      {item.entity_type === 'customer_due' ? '+' : '-'}
                      {formatPaiseToINR(item.amount_paise)}
                    </p>
                    <div className="mt-1">
                      <StatusPill
                        label={item.status}
                        variant={item.status === 'OVERDUE' ? 'alert' : item.status === 'DUE SOON' ? 'warning' : 'neutral'}
                      />
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Recent Transactions */}
        <div className="bg-white rounded-xl border border-[#E8EAED] p-5 shadow-[0_1px_3px_rgba(0,0,0,0.04)]">
          <div className="flex items-center justify-between pb-3 mb-3 border-b border-[#F0F2F5]">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-[#737780]" />
              <h3 className="text-sm font-bold text-[#17191C]">Recent Cash Activity</h3>
            </div>
            <Link to="/transactions" className="text-xs font-semibold text-[#16A36A] hover:underline flex items-center gap-1">
              <span>All records</span>
              <ChevronRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          <div className="divide-y divide-[#F0F2F5]">
            {data.recent_transactions.length === 0 ? (
              <p className="text-xs text-[#737780] py-6 text-center">No recent transactions recorded.</p>
            ) : (
              data.recent_transactions.map((tx) => (
                <div key={tx.id} className="py-3 flex items-center justify-between">
                  <div className="flex items-center gap-2.5 min-w-0 pr-3">
                    <div
                      className={`w-7 h-7 rounded-full flex items-center justify-center shrink-0 ${
                        tx.direction === 'inflow' ? 'bg-[#E8F7EF] text-[#16A36A]' : 'bg-[#FEF6EB] text-[#E9A23B]'
                      }`}
                    >
                      {tx.direction === 'inflow' ? <TrendingUp className="w-3.5 h-3.5" /> : <TrendingDown className="w-3.5 h-3.5" />}
                    </div>
                    <div className="min-w-0">
                      <p className="text-xs font-semibold text-[#17191C] truncate">{tx.description}</p>
                      <p className="text-[11px] text-[#737780]">{formatDate(tx.date)}</p>
                    </div>
                  </div>
                  <div className="text-right shrink-0">
                    <p
                      className={`text-xs font-bold tabular-nums ${
                        tx.direction === 'inflow' ? 'text-[#16A36A]' : 'text-[#17191C]'
                      }`}
                    >
                      {tx.direction === 'inflow' ? '+' : '-'}
                      {formatPaiseToINR(tx.amount_paise)}
                    </p>
                    <span className="text-[10px] text-[#737780] capitalize">{tx.type}</span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
