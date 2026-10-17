import React, { useEffect, useState } from 'react'
import { Plus, Filter, X, CheckCircle2, AlertOctagon, TrendingDown, TrendingUp, Tag } from 'lucide-react'
import { formatPaiseToINR, formatDate, parseINRToPaise } from '../../lib/formatters'

interface TransactionItem {
  id: string
  type: string
  description: string
  category?: string
  amount_paise: number
  date: string
  direction: 'inflow' | 'outflow'
  payment_method: string
}

export const TransactionsPage: React.FC = () => {
  const [transactions, setTransactions] = useState<TransactionItem[]>([])
  const [loading, setLoading] = useState(true)
  const [directionFilter, setDirectionFilter] = useState<'all' | 'inflow' | 'outflow'>('all')
  const [categoryFilter, setCategoryFilter] = useState<string>('all')

  // Expense Modal
  const [showAddExpense, setShowAddExpense] = useState(false)
  const [expTitle, setExpTitle] = useState('')
  const [expCategory, setExpCategory] = useState('utilities')
  const [expAmountINR, setExpAmountINR] = useState('')
  const [expDate, setExpDate] = useState('2026-10-17')
  const [expMethod, setExpMethod] = useState('cash')
  const [expNotes, setExpNotes] = useState('')

  const [formError, setFormError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  const fetchTransactions = async () => {
    try {
      const res = await fetch('/api/v1/transactions')
      if (res.ok) {
        const data = await res.json()
        setTransactions(data.items || [])
      }
    } catch (err) {
      console.error('Error fetching transactions:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchTransactions()
  }, [])

  const handleCreateExpense = async (e: React.FormEvent) => {
    e.preventDefault()
    const amountPaise = parseINRToPaise(expAmountINR)
    if (amountPaise <= 0) {
      setFormError('Please enter a valid expense amount in rupees')
      return
    }

    if (!expTitle.trim()) {
      setFormError('Expense title is required')
      return
    }

    setSubmitting(true)
    setFormError(null)
    try {
      const res = await fetch('/api/v1/expenses', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: expTitle.trim(),
          category: expCategory,
          amount_paise: amountPaise,
          expense_date: expDate,
          payment_method: expMethod,
          notes: expNotes,
        }),
      })

      if (!res.ok) {
        const errData = await res.json()
        throw new Error(errData?.error?.message || 'Failed to record expense')
      }

      setShowAddExpense(false)
      setExpTitle('')
      setExpAmountINR('')
      setExpNotes('')
      await fetchTransactions()
    } catch (err: unknown) {
      if (err instanceof Error) {
        setFormError(err.message)
      } else {
        setFormError('Failed to record expense')
      }
    } finally {
      setSubmitting(false)
    }
  }

  const categories = Array.from(new Set(transactions.map((t) => t.category || t.type).filter(Boolean)))

  const filtered = transactions.filter((t) => {
    if (directionFilter !== 'all' && t.direction !== directionFilter) return false
    if (categoryFilter !== 'all' && (t.category || t.type) !== categoryFilter) return false
    return true
  })

  const totalInflows = transactions.filter((t) => t.direction === 'inflow').reduce((acc, t) => acc + t.amount_paise, 0)
  const totalOutflows = transactions.filter((t) => t.direction === 'outflow').reduce((acc, t) => acc + t.amount_paise, 0)

  return (
    <div className="space-y-6">
      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-5">
        <div className="bg-white rounded-xl border border-[#E8EAED] p-5 shadow-[0_1px_3px_rgba(0,0,0,0.04)]">
          <span className="text-xs font-semibold text-[#737780] uppercase tracking-wider">Total Recorded Inflows</span>
          <p className="text-2xl font-bold text-[#16A36A] tabular-nums mt-0.5">
            +{formatPaiseToINR(totalInflows)}
          </p>
          <p className="text-xs text-[#737780] mt-1">Opening register and customer repayments</p>
        </div>

        <div className="bg-white rounded-xl border border-[#E8EAED] p-5 shadow-[0_1px_3px_rgba(0,0,0,0.04)]">
          <span className="text-xs font-semibold text-[#737780] uppercase tracking-wider">Total Recorded Outflows</span>
          <p className="text-2xl font-bold text-[#DC5555] tabular-nums mt-0.5">
            -{formatPaiseToINR(totalOutflows)}
          </p>
          <p className="text-xs text-[#737780] mt-1">Paid expenses and settled supplier bills</p>
        </div>

        <div className="bg-white rounded-xl border border-[#E8EAED] p-5 shadow-[0_1px_3px_rgba(0,0,0,0.04)] flex flex-col justify-between">
          <div>
            <span className="text-xs font-semibold text-[#737780] uppercase tracking-wider">Net Cash Movement</span>
            <p className="text-2xl font-bold text-[#17191C] tabular-nums mt-0.5">
              {formatPaiseToINR(totalInflows - totalOutflows)}
            </p>
          </div>
          <button
            onClick={() => {
              setFormError(null)
              setShowAddExpense(true)
            }}
            className="mt-3 w-full py-2 bg-[#16A36A] hover:bg-[#0D6843] text-white text-xs font-bold rounded-lg transition-colors flex items-center justify-center gap-1.5 shadow-sm"
          >
            <Plus className="w-4 h-4" />
            <span>Record Shop Expense</span>
          </button>
        </div>
      </div>

      {/* Transactions Table Container */}
      <div className="bg-white rounded-xl border border-[#E8EAED] overflow-hidden shadow-[0_1px_3px_rgba(0,0,0,0.04)]">
        {/* Filters Bar */}
        <div className="p-4 border-b border-[#E8EAED] flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-[#F7F8FA]">
          <div className="flex flex-wrap items-center gap-3">
            <div className="flex items-center gap-2">
              <Filter className="w-3.5 h-3.5 text-[#737780]" />
              <span className="text-xs font-semibold text-[#737780]">Type:</span>
              <div className="inline-flex rounded-lg border border-[#E8EAED] p-0.5 bg-white text-xs">
                <button
                  onClick={() => setDirectionFilter('all')}
                  className={`px-3 py-1 rounded-md font-medium transition-colors ${
                    directionFilter === 'all' ? 'bg-[#16A36A] text-white font-bold' : 'text-[#737780] hover:text-[#17191C]'
                  }`}
                >
                  All
                </button>
                <button
                  onClick={() => setDirectionFilter('inflow')}
                  className={`px-3 py-1 rounded-md font-medium transition-colors ${
                    directionFilter === 'inflow' ? 'bg-[#16A36A] text-white font-bold' : 'text-[#737780] hover:text-[#17191C]'
                  }`}
                >
                  Inflows (+)
                </button>
                <button
                  onClick={() => setDirectionFilter('outflow')}
                  className={`px-3 py-1 rounded-md font-medium transition-colors ${
                    directionFilter === 'outflow' ? 'bg-[#16A36A] text-white font-bold' : 'text-[#737780] hover:text-[#17191C]'
                  }`}
                >
                  Outflows (-)
                </button>
              </div>
            </div>

            {/* Category Dropdown */}
            {categories.length > 0 && (
              <div className="flex items-center gap-1.5 text-xs">
                <Tag className="w-3.5 h-3.5 text-[#737780]" />
                <select
                  value={categoryFilter}
                  onChange={(e) => setCategoryFilter(e.target.value)}
                  className="px-2.5 py-1 bg-white border border-[#E8EAED] rounded-lg text-xs text-[#17191C] focus:outline-none focus:border-[#16A36A]"
                >
                  <option value="all">All Categories</option>
                  {categories.map((cat) => (
                    <option key={cat} value={cat}>
                      {cat.charAt(0).toUpperCase() + cat.slice(1)}
                    </option>
                  ))}
                </select>
              </div>
            )}
          </div>

          <span className="text-xs text-[#737780] font-medium">{filtered.length} cash entries</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-[#F0F2F5] text-[#737780] font-semibold uppercase tracking-wider border-b border-[#E8EAED]">
              <tr>
                <th className="py-3 px-4">Date</th>
                <th className="py-3 px-4">Description</th>
                <th className="py-3 px-4">Category / Origin</th>
                <th className="py-3 px-4">Payment Method</th>
                <th className="py-3 px-4 text-right">Amount</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#E8EAED] text-[#17191C]">
              {loading ? (
                <tr>
                  <td colSpan={5} className="py-8 text-center text-[#737780]">
                    Loading transactions...
                  </td>
                </tr>
              ) : filtered.length === 0 ? (
                <tr>
                  <td colSpan={5} className="py-8 text-center text-[#737780]">
                    No transactions match current filters.
                  </td>
                </tr>
              ) : (
                filtered.map((t) => (
                  <tr key={t.id} className="hover:bg-[#F9FAFB] transition-colors">
                    <td className="py-3.5 px-4 text-[#737780]">{formatDate(t.date)}</td>
                    <td className="py-3.5 px-4 font-semibold text-[#17191C]">
                      <div className="flex items-center gap-2">
                        <div
                          className={`w-6 h-6 rounded-full flex items-center justify-center shrink-0 ${
                            t.direction === 'inflow' ? 'bg-[#E8F7EF] text-[#16A36A]' : 'bg-[#FEF6EB] text-[#E9A23B]'
                          }`}
                        >
                          {t.direction === 'inflow' ? <TrendingUp className="w-3.5 h-3.5" /> : <TrendingDown className="w-3.5 h-3.5" />}
                        </div>
                        <span>{t.description}</span>
                      </div>
                    </td>
                    <td className="py-3.5 px-4">
                      <span className="px-2 py-0.5 rounded bg-[#F0F2F5] text-[#737780] font-medium text-[11px] capitalize">
                        {t.category || t.type.replace('_', ' ')}
                      </span>
                    </td>
                    <td className="py-3.5 px-4 text-[#737780] capitalize">{t.payment_method}</td>
                    <td
                      className={`py-3.5 px-4 text-right font-bold tabular-nums ${
                        t.direction === 'inflow' ? 'text-[#16A36A]' : 'text-[#DC5555]'
                      }`}
                    >
                      {t.direction === 'inflow' ? '+' : '-'}
                      {formatPaiseToINR(t.amount_paise)}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Modal: Record Shop Expense */}
      {showAddExpense && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl border border-[#E8EAED] max-w-md w-full p-6 shadow-xl space-y-4">
            <div className="flex items-center justify-between border-b border-[#F0F2F5] pb-3">
              <h3 className="font-bold text-base text-[#17191C]">Record Shop Expense</h3>
              <button onClick={() => setShowAddExpense(false)} className="text-[#737780] hover:text-[#17191C]">
                <X className="w-5 h-5" />
              </button>
            </div>

            {formError && (
              <div className="p-3 bg-[#FDF0F0] text-[#DC5555] rounded-lg text-xs font-semibold flex items-center gap-1.5">
                <AlertOctagon className="w-4 h-4 shrink-0" />
                <span>{formError}</span>
              </div>
            )}

            <form onSubmit={handleCreateExpense} className="space-y-4 text-xs">
              <div>
                <label className="block font-semibold text-[#17191C] mb-1">Expense Title / Item *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Electric bill, packing tape, shop rent"
                  value={expTitle}
                  onChange={(e) => setExpTitle(e.target.value)}
                  className="w-full px-3 py-2 border border-[#E8EAED] rounded-lg focus:outline-none focus:border-[#16A36A]"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-semibold text-[#17191C] mb-1">Expense Category</label>
                  <select
                    value={expCategory}
                    onChange={(e) => setExpCategory(e.target.value)}
                    className="w-full px-3 py-2 border border-[#E8EAED] rounded-lg bg-white focus:outline-none focus:border-[#16A36A]"
                  >
                    <option value="utilities">Utilities & Power</option>
                    <option value="rent">Shop Rent</option>
                    <option value="packaging">Packaging & Bags</option>
                    <option value="repairs">Repairs & Maintenance</option>
                    <option value="transport">Freight & Transport</option>
                    <option value="misc">Miscellaneous</option>
                  </select>
                </div>

                <div>
                  <label className="block font-semibold text-[#17191C] mb-1">Amount (₹ INR) *</label>
                  <div className="relative">
                    <span className="absolute left-3 top-1/2 -translate-y-1/2 text-sm font-bold text-[#737780]">₹</span>
                    <input
                      type="number"
                      step="0.01"
                      required
                      placeholder="e.g. 1500"
                      value={expAmountINR}
                      onChange={(e) => setExpAmountINR(e.target.value)}
                      className="w-full pl-8 pr-3 py-2 border border-[#E8EAED] rounded-lg text-sm font-bold tabular-nums text-[#17191C] focus:outline-none focus:border-[#16A36A]"
                    />
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-semibold text-[#17191C] mb-1">Payment Date</label>
                  <input
                    type="date"
                    required
                    value={expDate}
                    onChange={(e) => setExpDate(e.target.value)}
                    className="w-full px-3 py-2 border border-[#E8EAED] rounded-lg focus:outline-none focus:border-[#16A36A]"
                  />
                </div>
                <div>
                  <label className="block font-semibold text-[#17191C] mb-1">Payment Source</label>
                  <select
                    value={expMethod}
                    onChange={(e) => setExpMethod(e.target.value)}
                    className="w-full px-3 py-2 border border-[#E8EAED] rounded-lg bg-white focus:outline-none focus:border-[#16A36A]"
                  >
                    <option value="cash">Cash in Hand</option>
                    <option value="upi">UPI / QR</option>
                    <option value="bank_transfer">Bank Transfer</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block font-semibold text-[#17191C] mb-1">Notes / Receipt Ref</label>
                <input
                  type="text"
                  placeholder="e.g. Paid cash to meter reader"
                  value={expNotes}
                  onChange={(e) => setExpNotes(e.target.value)}
                  className="w-full px-3 py-2 border border-[#E8EAED] rounded-lg focus:outline-none focus:border-[#16A36A]"
                />
              </div>

              <div className="p-3 bg-[#E8F7EF] text-[#16A36A] rounded-lg text-[11px] font-medium flex items-center gap-1.5">
                <CheckCircle2 className="w-4 h-4 shrink-0" />
                <span>Cash Synchronized: This expense will be immediately deducted from your register cash.</span>
              </div>

              <div className="flex items-center justify-end gap-2 pt-2 border-t border-[#F0F2F5]">
                <button
                  type="button"
                  onClick={() => setShowAddExpense(false)}
                  className="px-4 py-2 border border-[#E8EAED] rounded-lg text-xs font-semibold text-[#737780] hover:bg-[#F7F8FA]"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-4 py-2 bg-[#16A36A] hover:bg-[#0D6843] text-white rounded-lg text-xs font-bold transition-colors disabled:opacity-50"
                >
                  {submitting ? 'Recording...' : 'Record Expense'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
