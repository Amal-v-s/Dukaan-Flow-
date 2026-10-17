import React, { useEffect, useMemo, useState } from 'react'
import type { FormEvent } from 'react'
import { ArrowRight, LoaderCircle, RotateCcw, SlidersHorizontal } from 'lucide-react'
import { formatPaiseToINR, formatDate, parseINRToPaise } from '../../lib/formatters'
import { StatusPill } from '../../components/ui/StatusPill'

interface ScenarioOption {
  source_id: string
  event_type: 'customer_collection' | 'supplier_bill'
  title: string
  amount_paise: number
  scheduled_date: string
}

interface ScenarioOptionsResponse {
  today: string
  horizon_days: number
  items: ScenarioOption[]
}

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

const inputClass = 'w-full rounded-lg border border-[#E8EAED] bg-white px-3 py-2.5 text-sm text-[#17191C] focus:border-[#16A36A] focus:outline-none focus:ring-2 focus:ring-[#16A36A]/10 disabled:bg-[#F7F8FA]'
const cardClass = 'rounded-xl border border-[#E8EAED] bg-white p-5 shadow-[0_1px_3px_rgba(0,0,0,0.04)]'

function moneyInput(paise: number): string {
  const rupees = Math.floor(paise / 100)
  const remainder = paise % 100
  return remainder ? `${rupees}.${String(remainder).padStart(2, '0')}` : String(rupees)
}

function offsetDate(isoDate: string, days: number): string {
  const date = new Date(`${isoDate}T00:00:00Z`)
  date.setUTCDate(date.getUTCDate() + days)
  return date.toISOString().slice(0, 10)
}

export const SimulatorPage: React.FC = () => {
  const [options, setOptions] = useState<ScenarioOptionsResponse | null>(null)
  const [selectedEvent, setSelectedEvent] = useState('')
  const [amountInr, setAmountInr] = useState('')
  const [scenarioDate, setScenarioDate] = useState('')
  const [forecast, setForecast] = useState<ScenarioForecastResponse | null>(null)
  const [loadingOptions, setLoadingOptions] = useState(true)
  const [running, setRunning] = useState(false)
  const [error, setError] = useState('')

  const selectedOption = options?.items.find((item) => item.source_id === selectedEvent)
  const isExpense = selectedEvent === 'unexpected-expense'
  const minimumDate = options?.today || ''
  const maximumDate = useMemo(
    () => options ? offsetDate(options.today, options.horizon_days - 1) : '',
    [options],
  )

  useEffect(() => {
    let active = true
    fetch('/api/v1/scenarios/options')
      .then(async (response) => {
        const data = await response.json()
        if (!response.ok) throw new Error(data?.error?.message || 'Could not load upcoming events')
        if (!active) return
        setOptions(data)
        if (data.items.length) {
          setSelectedEvent(data.items[0].source_id)
          setAmountInr(moneyInput(data.items[0].amount_paise))
          setScenarioDate(data.items[0].scheduled_date)
        } else {
          setScenarioDate(data.today)
        }
      })
      .catch((err) => { if (active) setError(err.message || 'Could not load upcoming events') })
      .finally(() => { if (active) setLoadingOptions(false) })
    return () => { active = false }
  }, [])

  const handleEventChange = (value: string) => {
    setSelectedEvent(value)
    setForecast(null)
    setError('')
    if (value === 'unexpected-expense') {
      setAmountInr('')
      setScenarioDate(options?.today || '')
      return
    }
    const event = options?.items.find((item) => item.source_id === value)
    if (event) {
      setAmountInr(moneyInput(event.amount_paise))
      setScenarioDate(event.scheduled_date)
    }
  }

  const resetInputs = () => {
    setForecast(null)
    setError('')
    if (options?.items.length) {
      setSelectedEvent(options.items[0].source_id)
      setAmountInr(moneyInput(options.items[0].amount_paise))
      setScenarioDate(options.items[0].scheduled_date)
    } else {
      setSelectedEvent('unexpected-expense')
      setAmountInr('')
      setScenarioDate(options?.today || '')
    }
  }

  const runSimulation = async (event: FormEvent) => {
    event.preventDefault()
    setError('')
    setForecast(null)
    if (!selectedEvent) {
      setError('Choose a collection, supplier bill, or unexpected expense.')
      return
    }
    if (!scenarioDate || scenarioDate < minimumDate || scenarioDate > maximumDate) {
      setError(`Choose a date between ${formatDate(minimumDate)} and ${formatDate(maximumDate)}.`)
      return
    }
    if (!/^\d+(\.\d{1,2})?$/.test(amountInr) || parseINRToPaise(amountInr) <= 0) {
      setError('Enter an amount greater than ₹0, with up to two decimal places.')
      return
    }

    const body = {
      event_type: isExpense ? 'extra_expense' : selectedOption?.event_type,
      source_id: isExpense ? null : selectedOption?.source_id,
      amount_paise: parseINRToPaise(amountInr),
      original_date: isExpense ? null : selectedOption?.scheduled_date,
      scenario_date: scenarioDate,
      description: isExpense ? 'Unexpected shop expense' : selectedOption?.title,
    }
    setRunning(true)
    try {
      const response = await fetch('/api/v1/scenarios/preview', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })
      const data = await response.json()
      if (!response.ok) throw new Error(data?.error?.message || 'Could not run this simulation')
      setForecast(data)
    } catch (err: any) {
      setError(err.message || 'Could not run this simulation')
    } finally {
      setRunning(false)
    }
  }

  const impactLabel = forecast?.shortage_resolved
    ? 'Shortage avoided'
    : forecast?.scenario_has_shortage
      ? 'Cash may fall below zero'
      : forecast && forecast.scenario_lowest_dip_paise < forecast.safety_buffer_paise
        ? 'Below your safety buffer'
        : 'Above your safety buffer'
  const impactVariant = forecast?.shortage_resolved
    ? 'safe'
    : forecast?.scenario_has_shortage
      ? 'alert'
      : forecast && forecast.scenario_lowest_dip_paise < forecast.safety_buffer_paise
        ? 'warning'
        : 'safe'

  return (
    <div className="mx-auto max-w-4xl space-y-5">
      <section className="flex items-start gap-3 rounded-xl border border-[#BFDBFE] bg-[#EDF2FD] p-4">
        <SlidersHorizontal className="mt-0.5 h-5 w-5 shrink-0 text-[#6D8FE8]" />
        <div>
          <h2 className="text-sm font-bold text-[#17191C]">Try one change to your cash forecast</h2>
          <p className="mt-1 text-xs leading-5 text-[#737780]">This is only a preview. Your customer balances, bills, and cash records won’t change.</p>
        </div>
      </section>

      <form onSubmit={runSimulation} className={`${cardClass} space-y-4`}>
        <div>
          <h3 className="text-base font-bold text-[#17191C]">What would you like to change?</h3>
          <p className="mt-1 text-xs text-[#737780]">Choose an upcoming item or add an unexpected expense.</p>
        </div>

        <label className="block space-y-1.5 text-xs font-semibold text-[#17191C]" htmlFor="simulator-event">
          Item
          <select id="simulator-event" className={inputClass} value={selectedEvent} onChange={(event) => handleEventChange(event.target.value)} disabled={loadingOptions || running}>
            <option value="">Choose an item</option>
            {(options?.items || []).map((item) => (
              <option key={item.source_id} value={item.source_id}>
                {item.event_type === 'customer_collection' ? 'Collect from' : 'Pay'} {item.title.replace(/ collection$| bill$/, '')} · {formatPaiseToINR(item.amount_paise)} · {formatDate(item.scheduled_date)}
              </option>
            ))}
            <option value="unexpected-expense">Add an unexpected expense</option>
          </select>
        </label>

        {!loadingOptions && !options?.items.length && (
          <p className="rounded-lg bg-[#F7F8FA] p-3 text-xs text-[#737780]">No collections or bills are due in the next 14 days. You can still try an unexpected expense.</p>
        )}

        <div className="grid gap-4 sm:grid-cols-2">
          <label className="block space-y-1.5 text-xs font-semibold text-[#17191C]" htmlFor="simulator-amount">
            {isExpense ? 'Expense amount' : selectedOption?.event_type === 'supplier_bill' ? 'Payment amount' : 'Collection amount'}
            <div className="relative">
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-sm text-[#737780]">₹</span>
              <input id="simulator-amount" className={`${inputClass} pl-8`} type="number" min="0.01" step="0.01" inputMode="decimal" placeholder="e.g. 5,000" value={amountInr} onChange={(event) => setAmountInr(event.target.value)} disabled={loadingOptions || running || !selectedEvent} />
            </div>
            {!isExpense && selectedOption && <span className="block font-normal text-[#737780]">Current amount: {formatPaiseToINR(selectedOption.amount_paise)}</span>}
          </label>

          <label className="block space-y-1.5 text-xs font-semibold text-[#17191C]" htmlFor="simulator-date">
            {isExpense ? 'When would it happen?' : selectedOption?.event_type === 'supplier_bill' ? 'New payment date' : 'New collection date'}
            <input id="simulator-date" className={inputClass} type="date" min={minimumDate} max={maximumDate} value={scenarioDate} onChange={(event) => setScenarioDate(event.target.value)} disabled={loadingOptions || running || !selectedEvent} />
            <span className="block font-normal text-[#737780]">Choose a day in the next {options?.horizon_days || 14} days.</span>
          </label>
        </div>

        {error && <p role="alert" className="rounded-lg bg-[#FDF0F0] px-3 py-2 text-xs font-medium text-[#DC5555]">{error}</p>}

        <div className="flex flex-wrap items-center gap-3 border-t border-[#F0F2F5] pt-4">
          <button type="submit" disabled={loadingOptions || running || !selectedEvent} className="inline-flex items-center justify-center gap-2 rounded-lg bg-[#16A36A] px-4 py-2.5 text-sm font-bold text-white transition-colors hover:bg-[#0D6843] disabled:cursor-not-allowed disabled:opacity-50">
            {running ? <LoaderCircle className="h-4 w-4 animate-spin" /> : <ArrowRight className="h-4 w-4" />}
            {running ? 'Calculating…' : 'Run simulation'}
          </button>
          <button type="button" onClick={resetInputs} disabled={running || loadingOptions} className="inline-flex items-center gap-1.5 rounded-lg px-3 py-2.5 text-xs font-semibold text-[#737780] hover:bg-[#F7F8FA] disabled:opacity-50">
            <RotateCcw className="h-3.5 w-3.5" /> Reset
          </button>
          {loadingOptions && <span role="status" className="text-xs text-[#737780]">Loading upcoming items…</span>}
        </div>
      </form>

      {forecast && (
        <section aria-live="polite" className={`${cardClass} space-y-4`}>
          <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#F0F2F5] pb-3">
            <div>
              <h3 className="text-base font-bold text-[#17191C]">Your forecast result</h3>
              <p className="mt-1 text-xs text-[#737780]">Lowest projected cash over the next {forecast.horizon_days} days</p>
            </div>
            <StatusPill label={impactLabel || 'Forecast'} variant={impactVariant as 'safe' | 'warning' | 'alert'} />
          </div>

          <div className="grid gap-3 sm:grid-cols-3">
            <div className="rounded-lg bg-[#F7F8FA] p-3">
              <p className="text-[11px] font-semibold uppercase tracking-wide text-[#737780]">Before</p>
              <p className="mt-1 text-lg font-bold tabular-nums text-[#17191C]">{formatPaiseToINR(forecast.baseline_lowest_dip_paise)}</p>
              <p className="mt-0.5 text-[11px] text-[#737780]">{formatDate(forecast.baseline_lowest_dip_date)}</p>
            </div>
            <div className="rounded-lg bg-[#F7F8FA] p-3">
              <p className="text-[11px] font-semibold uppercase tracking-wide text-[#737780]">After your change</p>
              <p className={`mt-1 text-lg font-bold tabular-nums ${forecast.scenario_lowest_dip_paise < 0 ? 'text-[#DC5555]' : forecast.scenario_lowest_dip_paise < forecast.safety_buffer_paise ? 'text-[#E9A23B]' : 'text-[#16A36A]'}`}>{formatPaiseToINR(forecast.scenario_lowest_dip_paise)}</p>
              <p className="mt-0.5 text-[11px] text-[#737780]">{formatDate(forecast.scenario_lowest_dip_date)}</p>
            </div>
            <div className="rounded-lg bg-[#F7F8FA] p-3">
              <p className="text-[11px] font-semibold uppercase tracking-wide text-[#737780]">Difference</p>
              <p className={`mt-1 text-lg font-bold tabular-nums ${forecast.net_improvement_paise > 0 ? 'text-[#16A36A]' : forecast.net_improvement_paise < 0 ? 'text-[#DC5555]' : 'text-[#17191C]'}`}>
                {forecast.net_improvement_paise > 0 ? '+' : ''}{formatPaiseToINR(forecast.net_improvement_paise)}
              </p>
              <p className="mt-0.5 text-[11px] text-[#737780]">change in lowest balance</p>
            </div>
          </div>

          <p className="text-xs leading-5 text-[#737780]">
            {forecast.shortage_resolved
              ? 'This change avoids the projected cash shortage.'
              : forecast.scenario_has_shortage
                ? 'A projected cash shortage remains after this change.'
                : forecast.scenario_lowest_dip_paise < forecast.safety_buffer_paise
                  ? `Cash stays above zero but falls below your ${formatPaiseToINR(forecast.safety_buffer_paise)} safety buffer.`
                  : 'Your projected cash stays above the safety buffer.'}
          </p>

          <details className="border-t border-[#F0F2F5] pt-3">
            <summary className="cursor-pointer text-xs font-bold text-[#496BC3] hover:underline">View 14-day forecast details</summary>
            <div className="mt-4 space-y-4">
              <div className="flex flex-wrap gap-x-4 gap-y-2 text-[11px] text-[#737780]">
                <span><span className="mr-1 inline-block h-2.5 w-2.5 rounded-sm bg-[#737780]/40" />Before</span>
                <span><span className="mr-1 inline-block h-2.5 w-2.5 rounded-sm bg-[#16A36A]" />After</span>
                <span><span className="mr-1 inline-block h-0.5 w-3 bg-[#DC5555] align-middle" />Zero balance</span>
              </div>
              <div className="grid grid-cols-7 items-end gap-2 border-b border-[#E8EAED] pb-2 sm:grid-cols-14">
                {forecast.days.map((day) => {
                  const maxBalance = Math.max(...forecast.days.map((item) => Math.max(item.baseline_closing_paise, item.scenario_closing_paise, 1)))
                  const height = (value: number) => `${Math.max(4, Math.min(100, Math.round((Math.max(0, value) / maxBalance) * 100)))}%`
                  return (
                    <div key={day.date} className="flex h-28 flex-col items-center justify-end gap-1" title={`${formatDate(day.date)} · Before ${formatPaiseToINR(day.baseline_closing_paise)} · After ${formatPaiseToINR(day.scenario_closing_paise)}`}>
                      <div className="flex h-20 w-full items-end justify-center gap-0.5">
                        <span style={{ height: height(day.baseline_closing_paise) }} className={`w-2 rounded-t ${day.baseline_closing_paise < 0 ? 'bg-[#DC5555]/60' : 'bg-[#737780]/40'}`} />
                        <span style={{ height: height(day.scenario_closing_paise) }} className={`w-2 rounded-t ${day.scenario_closing_paise < 0 ? 'bg-[#DC5555]' : day.scenario_below_buffer ? 'bg-[#E9A23B]' : 'bg-[#16A36A]'}`} />
                      </div>
                      <span className="text-[10px] text-[#737780]">{day.date.slice(8, 10)}</span>
                    </div>
                  )
                })}
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="border-b border-[#E8EAED] text-[10px] uppercase tracking-wide text-[#737780]">
                    <tr><th className="py-2 pr-3">Date</th><th className="px-3 py-2 text-right">Before</th><th className="px-3 py-2 text-right">After</th><th className="px-3 py-2 text-right">Change</th><th className="py-2 pl-3 text-right">Status</th></tr>
                  </thead>
                  <tbody className="divide-y divide-[#F0F2F5]">
                    {forecast.days.map((day) => (
                      <tr key={day.date}>
                        <td className="py-2 pr-3 font-medium">{formatDate(day.date)}</td>
                        <td className="px-3 py-2 text-right tabular-nums">{formatPaiseToINR(day.baseline_closing_paise)}</td>
                        <td className={`px-3 py-2 text-right font-semibold tabular-nums ${day.scenario_below_zero ? 'text-[#DC5555]' : day.scenario_below_buffer ? 'text-[#E9A23B]' : 'text-[#16A36A]'}`}>{formatPaiseToINR(day.scenario_closing_paise)}</td>
                        <td className={`px-3 py-2 text-right tabular-nums ${day.delta_paise > 0 ? 'text-[#16A36A]' : day.delta_paise < 0 ? 'text-[#DC5555]' : 'text-[#737780]'}`}>{day.delta_paise > 0 ? '+' : ''}{formatPaiseToINR(day.delta_paise)}</td>
                        <td className="py-2 pl-3 text-right text-[10px] text-[#737780]">{day.scenario_below_zero ? 'Below zero' : day.scenario_below_buffer ? 'Below buffer' : 'Healthy'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </details>
        </section>
      )}
    </div>
  )
}
