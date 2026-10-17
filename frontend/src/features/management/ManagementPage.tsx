import React, { useEffect, useState } from 'react'
import { Bell, Wallet, ClipboardList, CalendarClock, Plus, Check } from 'lucide-react'
import { formatPaiseToINR, parseINRToPaise } from '../../lib/formatters'
import { Link } from 'react-router-dom'

type Tab = 'plans' | 'budgets' | 'reports' | 'reminders'
type AnyRow = Record<string, any>
const today = () => new Date().toISOString().slice(0, 10)

export const ManagementPage: React.FC = () => {
  const [tab, setTab] = useState<Tab>('plans')
  const [customers, setCustomers] = useState<AnyRow[]>([])
  const [plans, setPlans] = useState<AnyRow[]>([])
  const [budgets, setBudgets] = useState<AnyRow[]>([])
  const [reminders, setReminders] = useState<AnyRow[]>([])
  const [report, setReport] = useState<AnyRow | null>(null)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState(false)
  const [customerId, setCustomerId] = useState('')
  const [planAmount, setPlanAmount] = useState('')
  const [planDue, setPlanDue] = useState('')
  const [planType, setPlanType] = useState<'full_payment' | 'installments'>('full_payment')
  const [category, setCategory] = useState('utilities')
  const [budgetAmount, setBudgetAmount] = useState('')
  const [start, setStart] = useState(`${today().slice(0, 7)}-01`)
  const [end, setEnd] = useState(today())

  const load = async () => {
    setError('')
    setLoading(true)
    try {
      const [c, p, b, r] = await Promise.all(['/api/v1/customers', '/api/v1/repayment-plans', '/api/v1/budgets', '/api/v1/reminders'].map((url) => fetch(url)))
      if (![c, p, b, r].every((x) => x.ok)) throw new Error('Could not load management data. Check that the backend is running.')
      const [cj, pj, bj, rj] = await Promise.all([c.json(), p.json(), b.json(), r.json()])
      setCustomers(cj.items || []); setPlans(pj.items || []); setBudgets(bj.items || []); setReminders(rj.items || [])
      if (!customerId && cj.items?.length) setCustomerId(cj.items[0].id)
    } catch (e) { setError(e instanceof Error ? e.message : 'Unable to load data') }
    finally { setLoading(false) }
  }
  useEffect(() => { void load() }, [])

  const post = async (url: string, method: string, body: unknown) => {
    setBusy(true); setError('')
    try {
      const res = await fetch(url, { method, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) })
      const json = res.status === 204 ? null : await res.json()
      if (!res.ok) throw new Error(json?.error?.message || json?.detail || 'Request failed')
      await load(); setNotice('Changes saved.'); return json
    } catch (e) { setError(e instanceof Error ? e.message : 'Request failed'); return null }
    finally { setBusy(false) }
  }

  const createPlan = async (e: React.FormEvent) => {
    e.preventDefault(); const amount = parseINRToPaise(planAmount)
    if (!customerId || amount <= 0 || !planDue) { setError('Choose a customer, amount and due date.'); return }
    const secondDue = new Date(`${planDue}T12:00:00`); secondDue.setDate(secondDue.getDate() + 7)
    const installments = planType === 'full_payment' ? [{ due_date: planDue, amount_paise: amount }] : [{ due_date: planDue, amount_paise: Math.floor(amount / 2) }, { due_date: secondDue.toISOString().slice(0, 10), amount_paise: amount - Math.floor(amount / 2) }]
    await post('/api/v1/repayment-plans', 'POST', { customer_id: customerId, plan_type: planType, planned_amount_paise: amount, start_date: today(), notes: '', installments })
    setPlanAmount(''); setPlanDue('')
  }
  const createBudget = async (e: React.FormEvent) => {
    e.preventDefault(); const amount = parseINRToPaise(budgetAmount)
    if (amount <= 0) { setError('Enter a positive budget amount.'); return }
    const periodStart = `${today().slice(0, 7)}-01`; const periodEnd = new Date(Number(today().slice(0, 4)), Number(today().slice(5, 7)), 0).toISOString().slice(0, 10)
    const result = await post('/api/v1/budgets', 'POST', { category, period_start: periodStart, period_end: periodEnd, budget_amount_paise: amount, period_type: 'monthly', thresholds: [75, 90, 100] })
    if (result) setBudgetAmount('')
  }
  const loadReport = async () => {
    try { const res = await fetch(`/api/v1/reports/summary?start_date=${start}&end_date=${end}`); const j = await res.json(); if (!res.ok) throw new Error(j?.detail || 'Could not load report'); setReport(j); setError('') }
    catch (e) { setError(e instanceof Error ? e.message : 'Could not load report') }
  }
  const pay = async (p: AnyRow, i: AnyRow) => {
    const remain = i.amount_paise - i.paid_amount_paise
    const amount = window.prompt(`Record payment up to ${formatPaiseToINR(remain)} (enter rupees):`, String(Math.floor(remain / 100)))
    if (amount === null) return
    const paise = parseINRToPaise(amount)
    if (paise <= 0 || paise > remain) { setError('Payment must be positive and no greater than the instalment balance.'); return }
    await post(`/api/v1/repayment-plans/${p.id}/installments/${i.id}/payments`, 'POST', { payment_id: crypto.randomUUID(), amount_paise: paise, payment_date: today(), payment_method: 'cash' })
  }
  const acknowledge = async (r: AnyRow) => { await post(`/api/v1/reminders/${r.id}`, 'PATCH', { status: 'acknowledged' }) }

  const tabs: { id: Tab; label: string; icon: React.ElementType }[] = [
    { id: 'plans', label: 'Repayment plans', icon: CalendarClock }, { id: 'budgets', label: 'Budgets', icon: Wallet }, { id: 'reports', label: 'Reports', icon: ClipboardList }, { id: 'reminders', label: 'Reminders', icon: Bell },
  ]
  const card = 'bg-white rounded-xl border border-[#E8EAED] p-5 shadow-sm'
  const input = 'w-full rounded-lg border border-[#D8DCE2] px-3 py-2 text-sm focus:outline-none focus:border-[#16A36A]'

  return <div className="space-y-5">
    <div className="flex flex-wrap gap-2">{tabs.map(({ id, label, icon: Icon }) => <button key={id} onClick={() => setTab(id)} className={`inline-flex items-center gap-2 rounded-lg px-3.5 py-2 text-sm font-semibold ${tab === id ? 'bg-[#E8F7EF] text-[#16A36A]' : 'bg-white border border-[#E8EAED] text-[#737780]'}`}><Icon className="w-4 h-4" />{label}</button>)}</div>
    {error && <div role="alert" className="rounded-lg border border-[#FECACA] bg-[#FDF0F0] p-3 text-sm text-[#B91C1C]">{error}</div>}
    {notice && <div role="status" className="rounded-lg border border-[#B8E7CC] bg-[#E8F7EF] p-3 text-sm text-[#0D6843]">{notice}</div>}
    {loading ? <div role="status" className={card + ' text-sm text-[#737780]'}>Loading business management data…</div> : <>
    {tab === 'plans' && <div className="grid gap-5 lg:grid-cols-[320px_1fr]">
      <form onSubmit={createPlan} className={`${card} space-y-3 h-fit`}><h2 className="font-bold">Schedule customer repayment</h2><p className="text-xs text-[#737780]">A schedule tracks existing receivables. Payments are recorded as actual cash only when received.</p>
        <select className={input} value={customerId} onChange={(e) => setCustomerId(e.target.value)}>{customers.map((c) => <option key={c.id} value={c.id}>{c.name} · {formatPaiseToINR(c.outstanding_balance_paise)}</option>)}</select>
        <select className={input} value={planType} onChange={(e) => setPlanType(e.target.value as 'full_payment' | 'installments')}><option value="full_payment">Full payment</option><option value="installments">Two instalments, one week apart</option></select>
        <input className={input} placeholder="Planned amount (₹)" inputMode="decimal" value={planAmount} onChange={(e) => setPlanAmount(e.target.value)} />
        <label className="block text-xs text-[#737780]">Due date<input className={input} type="date" min={today()} value={planDue} onChange={(e) => setPlanDue(e.target.value)} /></label>
        <button disabled={busy || !customers.length} className="w-full rounded-lg bg-[#16A36A] px-3 py-2 text-sm font-bold text-white disabled:opacity-50"><Plus className="mr-1 inline h-4 w-4" />Create repayment schedule</button>
      </form>
      <div className="space-y-3">{plans.length ? plans.map((p) => <section className={card} key={p.id}><div className="flex justify-between gap-3"><div><h3 className="font-bold">{p.customer_name} <span className="ml-2 rounded bg-[#F0F2F5] px-2 py-1 text-xs font-medium">{p.status}</span></h3><p className="mt-1 text-xs text-[#737780]">{p.plan_type === 'full_payment' ? 'Full payment' : 'Instalments'} · {formatPaiseToINR(p.paid_amount_paise)} paid of {formatPaiseToINR(p.planned_amount_paise)} · due {p.final_due_date}</p></div></div>
        <div className="mt-4 divide-y divide-[#F0F2F5]">{p.installments.map((i: AnyRow) => <div key={i.id} className="flex flex-wrap items-center justify-between gap-2 py-2 text-sm"><span>Due {i.due_date} · {i.status}</span><span className="tabular-nums">{formatPaiseToINR(i.paid_amount_paise)} / {formatPaiseToINR(i.amount_paise)}</span>{i.status !== 'paid' && !['completed','cancelled'].includes(p.status) && <button disabled={busy} onClick={() => void pay(p, i)} className="rounded-md border px-2 py-1 text-xs font-semibold text-[#16A36A]">Record payment</button>}</div>)}</div></section>) : <div className={card}><p className="text-sm text-[#737780]">No repayment schedules yet. Create one from a customer’s existing outstanding balance.</p></div>}</div>
    </div>}
    {tab === 'budgets' && <div className="space-y-4"><form onSubmit={createBudget} className={`${card} flex flex-wrap items-end gap-3`}><label className="text-xs">Category<select className={`${input} mt-1`} value={category} onChange={(e) => setCategory(e.target.value)}>{['utilities','rent','transport','packaging','repairs','misc'].map((x) => <option key={x}>{x}</option>)}</select></label><label className="text-xs">Monthly limit (₹)<input className={`${input} mt-1`} inputMode="decimal" value={budgetAmount} onChange={(e) => setBudgetAmount(e.target.value)} /></label><button disabled={busy} className="rounded-lg bg-[#16A36A] px-4 py-2 text-sm font-bold text-white">Set budget</button></form>
      <p className="text-xs text-[#737780]">Utilization uses recorded paid expense transactions only; it may not include spending that has not been entered. Supplier bills are reported separately.</p>
      {budgets.map((b) => <div className={card} key={b.id}><div className="flex justify-between text-sm"><strong className="capitalize">{b.category}</strong><span>{formatPaiseToINR(b.spent_paise)} / {formatPaiseToINR(b.budget_amount_paise)}</span></div><div className="mt-3 h-2 rounded-full bg-[#F0F2F5]"><div className={`h-2 rounded-full ${b.exceeded ? 'bg-[#DC5555]' : b.triggered_thresholds.length ? 'bg-[#E9A23B]' : 'bg-[#16A36A]'}`} style={{ width: `${Math.min(100,b.utilization_percent)}%` }} /></div><p className="mt-2 text-xs text-[#737780]">{b.exceeded ? 'Over budget' : `${formatPaiseToINR(b.remaining_paise)} remaining`} · {b.utilization_percent}% utilized{b.triggered_thresholds.length ? ` · Alert threshold ${b.triggered_thresholds.at(-1)}%` : ''}</p></div>)}
    </div>}
    {tab === 'reports' && <div className="space-y-4"><div className={`${card} flex flex-wrap items-end gap-3`}><label className="text-xs">From<input className={`${input} mt-1`} type="date" value={start} onChange={(e) => setStart(e.target.value)} /></label><label className="text-xs">To<input className={`${input} mt-1`} type="date" value={end} onChange={(e) => setEnd(e.target.value)} /></label><button onClick={() => void loadReport()} className="rounded-lg bg-[#16A36A] px-4 py-2 text-sm font-bold text-white">Run report</button></div>
      {report && <><p className="text-xs text-[#737780]">Records from {report.start_date} to {report.end_date} · generated {new Date(report.generated_at).toLocaleString()}</p><div className="grid gap-3 sm:grid-cols-2"><div className={card}><p className="text-xs text-[#737780]">Recorded cash inflows</p><strong className="text-xl">{formatPaiseToINR(report.cash_inflows_paise)}</strong></div><div className={card}><p className="text-xs text-[#737780]">Recorded cash outflows</p><strong className="text-xl">{formatPaiseToINR(report.cash_outflows_paise)}</strong></div></div><section className={card}><h3 className="mb-3 font-bold">Expenses by category</h3>{report.expenses_by_category.length ? report.expenses_by_category.map((x: AnyRow) => <div className="flex justify-between border-b py-2 text-sm" key={x.category}><span className="capitalize">{x.category}</span><span>{formatPaiseToINR(x.amount_paise)}</span></div>) : <p className="text-sm text-[#737780]">No recorded expenses in this range.</p>}</section><section className={card}><h3 className="mb-3 font-bold">Receivables (current outstanding)</h3>{report.receivables.map((x: AnyRow) => <div className="flex justify-between border-b py-2 text-sm" key={x.customer_id}><span>{x.name}</span><span>{formatPaiseToINR(x.outstanding_paise)}</span></div>)}</section><section className={card}><h3 className="mb-2 font-bold">Definition</h3><p className="text-xs text-[#737780]">Cash totals include posted cashbook movements within the selected dates. Credit sales and receivables are reported separately and are not cash income. Payables are current unpaid supplier bills.</p></section></>}</div>}
    {tab === 'reminders' && <div className="space-y-3"><p className="text-xs text-[#737780]">In-app only. These reminders do not send WhatsApp or SMS messages.</p>{reminders.length ? reminders.map((r) => <div className={`${card} flex flex-wrap items-center justify-between gap-3`} key={r.id}><div><h3 className="font-bold">{r.title} · {r.type === 'supplier_bill' ? 'Supplier bill' : 'Customer instalment'}</h3><p className="text-xs text-[#737780]">{r.due_state === 'overdue' ? 'Overdue' : r.due_state === 'due_today' ? 'Due today' : 'Due'} {r.due_date} · {formatPaiseToINR(r.amount_paise)} · {r.status}</p><Link className="mt-1 inline-block text-xs font-semibold text-[#6D8FE8] hover:underline" to={r.type === 'supplier_bill' ? '/suppliers' : '/customers'}>Open {r.type === 'supplier_bill' ? 'supplier bills' : 'customer khata'}</Link></div>{r.status !== 'acknowledged' && <button disabled={busy} onClick={() => void acknowledge(r)} className="rounded-md border px-3 py-2 text-xs font-semibold"><Check className="mr-1 inline h-4 w-4" />Acknowledge</button>}</div>) : <div className={card}><p className="text-sm text-[#737780]">No due or overdue items in the current reminder window.</p></div>}</div>}
    </>}
  </div>
}
