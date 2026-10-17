import React, { useEffect, useState } from 'react'
import { Plus, Search, Phone, X, History, CheckCircle2, AlertOctagon } from 'lucide-react'
import { formatPaiseToINR, formatDate, parseINRToPaise } from '../../lib/formatters'

interface Customer {
  id: string
  name: string
  phone: string | null
  notes?: string
  outstanding_balance_paise: number
  total_credit_paise: number
  total_repaid_paise: number
  last_activity_date: string
  is_active: boolean
}

interface LedgerEntry {
  id: string
  customer_id: string
  entry_type: string
  amount_paise: number
  effective_date: string
  due_date?: string
  status: string
  payment_method?: string
  notes?: string
  created_at: string
}

export const CustomersPage: React.FC = () => {
  const [customers, setCustomers] = useState<Customer[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')

  // Modals & Panels
  const [selectedCustomerId, setSelectedCustomerId] = useState<string | null>(null)
  const [customerLedger, setCustomerLedger] = useState<LedgerEntry[]>([])
  const [loadingLedger, setLoadingLedger] = useState(false)

  const [showAddCustomer, setShowAddCustomer] = useState(false)
  const [showAddCredit, setShowAddCredit] = useState(false)
  const [showRepay, setShowRepay] = useState(false)
  const [activeCustomer, setActiveCustomer] = useState<Customer | null>(null)

  // Form states
  const [custName, setCustName] = useState('')
  const [custPhone, setCustPhone] = useState('')
  const [custNotes, setCustNotes] = useState('')

  const [entryAmountINR, setEntryAmountINR] = useState('')
  const [entryDate, setEntryDate] = useState('2026-10-17')
  const [entryDueDate, setEntryDueDate] = useState('2026-10-24')
  const [entryMethod, setEntryMethod] = useState('cash')
  const [entryNotes, setEntryNotes] = useState('')
  const [formError, setFormError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  const fetchCustomers = async () => {
    try {
      const res = await fetch('/api/v1/customers')
      if (res.ok) {
        const data = await res.json()
        setCustomers(data.items || [])
      }
    } catch (err) {
      console.error('Error fetching customers:', err)
    } finally {
      setLoading(false)
    }
  }

  const fetchCustomerLedger = async (customerId: string) => {
    setLoadingLedger(true)
    try {
      const res = await fetch(`/api/v1/customers/${customerId}/ledger`)
      if (res.ok) {
        const data = await res.json()
        setCustomerLedger(data.entries || [])
      }
    } catch (err) {
      console.error('Error loading ledger:', err)
    } finally {
      setLoadingLedger(false)
    }
  }

  useEffect(() => {
    fetchCustomers()
  }, [])

  const handleOpenLedger = (c: Customer) => {
    setActiveCustomer(c)
    setSelectedCustomerId(c.id)
    fetchCustomerLedger(c.id)
  }

  const handleOpenCredit = (c: Customer, e?: React.MouseEvent) => {
    if (e) e.stopPropagation()
    setActiveCustomer(c)
    setEntryAmountINR('')
    setEntryDate('2026-10-17')
    setEntryDueDate('2026-10-24')
    setEntryNotes('')
    setFormError(null)
    setShowAddCredit(true)
  }

  const handleOpenRepay = (c: Customer, e?: React.MouseEvent) => {
    if (e) e.stopPropagation()
    setActiveCustomer(c)
    setEntryAmountINR('')
    setEntryDate('2026-10-17')
    setEntryMethod('cash')
    setEntryNotes('')
    setFormError(null)
    setShowRepay(true)
  }

  const handleCreateCustomer = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!custName.trim()) {
      setFormError('Customer name is required')
      return
    }

    setSubmitting(true)
    setFormError(null)
    try {
      const res = await fetch('/api/v1/customers', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: custName.trim(),
          phone: custPhone.trim() || null,
          notes: custNotes.trim() || '',
        }),
      })

      if (!res.ok) {
        const errData = await res.json()
        throw new Error(errData?.error?.message || 'Failed to create customer')
      }

      setCustName('')
      setCustPhone('')
      setCustNotes('')
      setShowAddCustomer(false)
      await fetchCustomers()
    } catch (err: unknown) {
      if (err instanceof Error) {
        setFormError(err.message)
      } else {
        setFormError('Failed to create customer')
      }
    } finally {
      setSubmitting(false)
    }
  }

  const handleSubmitCreditSale = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!activeCustomer) return

    const amountPaise = parseINRToPaise(entryAmountINR)
    if (amountPaise <= 0) {
      setFormError('Please enter a valid credit amount in rupees')
      return
    }

    if (!entryDueDate) {
      setFormError('Due date is required for credit sales')
      return
    }

    setSubmitting(true)
    setFormError(null)
    try {
      const res = await fetch(`/api/v1/customers/${activeCustomer.id}/ledger-entries`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          entry_type: 'credit_sale',
          amount_paise: amountPaise,
          effective_date: entryDate,
          due_date: entryDueDate,
          notes: entryNotes,
        }),
      })

      if (!res.ok) {
        const errData = await res.json()
        throw new Error(errData?.error?.message || 'Failed to record credit sale')
      }

      setShowAddCredit(false)
      await fetchCustomers()
      if (selectedCustomerId === activeCustomer.id) {
        await fetchCustomerLedger(activeCustomer.id)
      }
    } catch (err: unknown) {
      if (err instanceof Error) {
        setFormError(err.message)
      } else {
        setFormError('Failed to record credit sale')
      }
    } finally {
      setSubmitting(false)
    }
  }

  const handleSubmitRepayment = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!activeCustomer) return

    const amountPaise = parseINRToPaise(entryAmountINR)
    if (amountPaise <= 0) {
      setFormError('Please enter a valid repayment amount in rupees')
      return
    }

    if (amountPaise > activeCustomer.outstanding_balance_paise) {
      setFormError(
        `Repayment amount cannot exceed current outstanding balance (${formatPaiseToINR(
          activeCustomer.outstanding_balance_paise
        )})`
      )
      return
    }

    setSubmitting(true)
    setFormError(null)
    try {
      const res = await fetch(`/api/v1/customers/${activeCustomer.id}/ledger-entries`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          entry_type: 'repayment',
          amount_paise: amountPaise,
          effective_date: entryDate,
          payment_method: entryMethod,
          notes: entryNotes,
        }),
      })

      if (!res.ok) {
        const errData = await res.json()
        throw new Error(errData?.error?.message || 'Failed to record repayment')
      }

      setShowRepay(false)
      await fetchCustomers()
      if (selectedCustomerId === activeCustomer.id) {
        await fetchCustomerLedger(activeCustomer.id)
      }
    } catch (err: unknown) {
      if (err instanceof Error) {
        setFormError(err.message)
      } else {
        setFormError('Failed to record repayment')
      }
    } finally {
      setSubmitting(false)
    }
  }

  const filtered = customers.filter(
    (c) =>
      c.name.toLowerCase().includes(search.toLowerCase()) ||
      (c.phone && c.phone.includes(search))
  )

  const totalOutstanding = customers.reduce((acc, c) => acc + c.outstanding_balance_paise, 0)
  const totalCreditGiven = customers.reduce((acc, c) => acc + c.total_credit_paise, 0)
  const totalRepaidReceived = customers.reduce((acc, c) => acc + c.total_repaid_paise, 0)

  return (
    <div className="space-y-6">
      {/* Top summary cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-5">
        <div className="bg-white rounded-xl border border-[#E8EAED] p-5 shadow-[0_1px_3px_rgba(0,0,0,0.04)]">
          <span className="text-xs font-semibold text-[#737780] uppercase tracking-wider">Total Customer Udhaar</span>
          <p className="text-2xl font-bold text-[#DC5555] tabular-nums mt-0.5">
            {formatPaiseToINR(totalOutstanding)}
          </p>
          <p className="text-xs text-[#737780] mt-1">Pending collections across {customers.length} accounts</p>
        </div>

        <div className="bg-white rounded-xl border border-[#E8EAED] p-5 shadow-[0_1px_3px_rgba(0,0,0,0.04)]">
          <span className="text-xs font-semibold text-[#737780] uppercase tracking-wider">Total Credit Extended</span>
          <p className="text-2xl font-bold text-[#17191C] tabular-nums mt-0.5">
            {formatPaiseToINR(totalCreditGiven)}
          </p>
          <p className="text-xs text-[#737780] mt-1">Cumulative sales recorded on udhaar</p>
        </div>

        <div className="bg-white rounded-xl border border-[#E8EAED] p-5 shadow-[0_1px_3px_rgba(0,0,0,0.04)] flex flex-col justify-between">
          <div>
            <span className="text-xs font-semibold text-[#737780] uppercase tracking-wider">Total Repayments Collected</span>
            <p className="text-2xl font-bold text-[#16A36A] tabular-nums mt-0.5">
              {formatPaiseToINR(totalRepaidReceived)}
            </p>
          </div>
          <button
            onClick={() => setShowAddCustomer(true)}
            className="mt-3 w-full py-2 bg-[#16A36A] hover:bg-[#0D6843] text-white text-xs font-bold rounded-lg transition-colors flex items-center justify-center gap-1.5 shadow-sm"
          >
            <Plus className="w-4 h-4" />
            <span>Add New Customer</span>
          </button>
        </div>
      </div>

      {/* Main Customers List & Drawer Split */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">
        {/* Customer Table */}
        <div className={`${selectedCustomerId ? 'lg:col-span-2' : 'lg:col-span-3'} bg-white rounded-xl border border-[#E8EAED] overflow-hidden shadow-[0_1px_3px_rgba(0,0,0,0.04)]`}>
          <div className="p-4 border-b border-[#E8EAED] flex items-center justify-between gap-3 bg-[#F7F8FA]">
            <div className="relative flex-1 max-w-sm">
              <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-[#737780]" />
              <input
                type="text"
                placeholder="Search by customer name or phone..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full pl-9 pr-3 py-1.5 bg-white border border-[#E8EAED] rounded-lg text-xs text-[#17191C] focus:outline-none focus:border-[#16A36A]"
              />
            </div>
            <span className="text-xs text-[#737780] font-medium">{filtered.length} customers</span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-[#F0F2F5] text-[#737780] font-semibold uppercase tracking-wider border-b border-[#E8EAED]">
                <tr>
                  <th className="py-3 px-4">Customer Name</th>
                  <th className="py-3 px-4">Contact</th>
                  <th className="py-3 px-4 text-right">Outstanding Due</th>
                  <th className="py-3 px-4 text-right">Total Repaid</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#E8EAED] text-[#17191C]">
                {loading ? (
                  <tr>
                    <td colSpan={5} className="py-8 text-center text-[#737780]">
                      Loading customer accounts...
                    </td>
                  </tr>
                ) : filtered.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="py-8 text-center text-[#737780]">
                      No customers found. Click "Add New Customer" above to begin.
                    </td>
                  </tr>
                ) : (
                  filtered.map((c) => {
                    const isSelected = selectedCustomerId === c.id
                    return (
                      <tr
                        key={c.id}
                        onClick={() => handleOpenLedger(c)}
                        className={`cursor-pointer transition-colors ${
                          isSelected ? 'bg-[#E8F7EF]/50 border-l-4 border-[#16A36A]' : 'hover:bg-[#F9FAFB]'
                        }`}
                      >
                        <td className="py-3.5 px-4 font-semibold text-[#17191C]">
                          <div className="flex items-center gap-2.5">
                            <div className="w-7 h-7 rounded-full bg-[#E8F7EF] text-[#16A36A] font-bold flex items-center justify-center text-[11px] shrink-0">
                              {c.name.substring(0, 1)}
                            </div>
                            <div>
                              <p>{c.name}</p>
                              <p className="text-[10px] text-[#737780] font-normal">Last activity: {formatDate(c.last_activity_date)}</p>
                            </div>
                          </div>
                        </td>
                        <td className="py-3.5 px-4 text-[#737780]">
                          {c.phone ? (
                            <span className="flex items-center gap-1">
                              <Phone className="w-3 h-3" />
                              <span>{c.phone}</span>
                            </span>
                          ) : (
                            '-'
                          )}
                        </td>
                        <td className="py-3.5 px-4 text-right font-bold tabular-nums text-[#DC5555]">
                          {formatPaiseToINR(c.outstanding_balance_paise)}
                        </td>
                        <td className="py-3.5 px-4 text-right tabular-nums text-[#16A36A] font-medium">
                          {formatPaiseToINR(c.total_repaid_paise)}
                        </td>
                        <td className="py-3.5 px-4 text-right space-x-1.5" onClick={(e) => e.stopPropagation()}>
                          <button
                            onClick={(e) => handleOpenCredit(c, e)}
                            className="px-2.5 py-1 rounded bg-[#E8F7EF] text-[#16A36A] font-bold hover:bg-[#d1fae5] transition-colors"
                            title="Add Credit Sale"
                          >
                            + Credit
                          </button>
                          <button
                            onClick={(e) => handleOpenRepay(c, e)}
                            disabled={c.outstanding_balance_paise === 0}
                            className="px-2.5 py-1 rounded bg-[#F0F2F5] text-[#17191C] font-bold hover:bg-[#E5E7EB] transition-colors disabled:opacity-40"
                            title="Record Repayment"
                          >
                            Repay
                          </button>
                        </td>
                      </tr>
                    )
                  })
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Selected Customer Ledger History Drawer */}
        {selectedCustomerId && activeCustomer && (
          <div className="bg-white rounded-xl border border-[#E8EAED] p-5 shadow-[0_1px_3px_rgba(0,0,0,0.04)] sticky top-24 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-[#F0F2F5]">
              <div>
                <h3 className="font-bold text-sm text-[#17191C]">{activeCustomer.name}</h3>
                <p className="text-xs text-[#737780]">{activeCustomer.phone || 'No phone recorded'}</p>
              </div>
              <button
                onClick={() => setSelectedCustomerId(null)}
                className="p-1 rounded text-[#737780] hover:text-[#17191C] hover:bg-[#F0F2F5]"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Balances summary */}
            <div className="p-3 bg-[#F7F8FA] rounded-lg grid grid-cols-2 gap-2 text-xs">
              <div>
                <span className="text-[#737780] text-[10px] uppercase font-bold">Outstanding Due</span>
                <p className="text-base font-bold text-[#DC5555] tabular-nums">
                  {formatPaiseToINR(activeCustomer.outstanding_balance_paise)}
                </p>
              </div>
              <div>
                <span className="text-[#737780] text-[10px] uppercase font-bold">Total Repaid</span>
                <p className="text-base font-bold text-[#16A36A] tabular-nums">
                  {formatPaiseToINR(activeCustomer.total_repaid_paise)}
                </p>
              </div>
            </div>

            {/* Quick action buttons */}
            <div className="grid grid-cols-2 gap-2">
              <button
                onClick={() => handleOpenCredit(activeCustomer)}
                className="py-1.5 px-3 bg-[#16A36A] hover:bg-[#0D6843] text-white text-xs font-bold rounded-lg transition-colors flex items-center justify-center gap-1"
              >
                <Plus className="w-3.5 h-3.5" />
                <span>+ Credit</span>
              </button>
              <button
                onClick={() => handleOpenRepay(activeCustomer)}
                disabled={activeCustomer.outstanding_balance_paise === 0}
                className="py-1.5 px-3 bg-[#17191C] hover:bg-black text-white text-xs font-bold rounded-lg transition-colors flex items-center justify-center gap-1 disabled:opacity-40"
              >
                <span>Repay</span>
              </button>
            </div>

            {/* Chronological Ledger entries */}
            <div>
              <div className="flex items-center gap-1.5 text-xs font-bold text-[#737780] uppercase tracking-wider mb-2">
                <History className="w-3.5 h-3.5" />
                <span>Transaction History</span>
              </div>

              {loadingLedger ? (
                <p className="text-xs text-[#737780] py-4 text-center">Loading entries...</p>
              ) : customerLedger.length === 0 ? (
                <p className="text-xs text-[#737780] py-4 text-center">No transactions recorded yet.</p>
              ) : (
                <div className="divide-y divide-[#F0F2F5] max-h-80 overflow-y-auto">
                  {customerLedger.map((entry) => (
                    <div key={entry.id} className="py-2.5 flex items-center justify-between text-xs">
                      <div>
                        <div className="flex items-center gap-1.5">
                          <span
                            className={`w-2 h-2 rounded-full ${
                              entry.entry_type === 'credit_sale' ? 'bg-[#DC5555]' : 'bg-[#16A36A]'
                            }`}
                          ></span>
                          <span className="font-semibold text-[#17191C]">
                            {entry.entry_type === 'credit_sale' ? 'Credit Sale' : 'Repayment'}
                          </span>
                        </div>
                        <p className="text-[11px] text-[#737780] mt-0.5">
                          {formatDate(entry.effective_date)}
                          {entry.due_date ? ` · Due ${formatDate(entry.due_date)}` : ''}
                        </p>
                        {entry.notes && <p className="text-[10px] text-[#737780] italic mt-0.5">{entry.notes}</p>}
                      </div>
                      <div className="text-right">
                        <span
                          className={`font-bold tabular-nums ${
                            entry.entry_type === 'credit_sale' ? 'text-[#DC5555]' : 'text-[#16A36A]'
                          }`}
                        >
                          {entry.entry_type === 'credit_sale' ? '+' : '-'}
                          {formatPaiseToINR(entry.amount_paise)}
                        </span>
                        <p className="text-[10px] text-[#737780] capitalize">{entry.payment_method || 'credit'}</p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Modal: Add New Customer */}
      {showAddCustomer && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl border border-[#E8EAED] max-w-md w-full p-6 shadow-xl space-y-4">
            <div className="flex items-center justify-between border-b border-[#F0F2F5] pb-3">
              <h3 className="font-bold text-base text-[#17191C]">Add New Customer Account</h3>
              <button onClick={() => setShowAddCustomer(false)} className="text-[#737780] hover:text-[#17191C]">
                <X className="w-5 h-5" />
              </button>
            </div>

            {formError && (
              <div className="p-3 bg-[#FDF0F0] text-[#DC5555] rounded-lg text-xs font-semibold flex items-center gap-1.5">
                <AlertOctagon className="w-4 h-4 shrink-0" />
                <span>{formError}</span>
              </div>
            )}

            <form onSubmit={handleCreateCustomer} className="space-y-4 text-xs">
              <div>
                <label className="block font-semibold text-[#17191C] mb-1">Customer / Shop Name *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Ramesh Kirana"
                  value={custName}
                  onChange={(e) => setCustName(e.target.value)}
                  className="w-full px-3 py-2 border border-[#E8EAED] rounded-lg focus:outline-none focus:border-[#16A36A]"
                />
              </div>

              <div>
                <label className="block font-semibold text-[#17191C] mb-1">Phone Number (Optional)</label>
                <input
                  type="tel"
                  placeholder="+91 98765 00000"
                  value={custPhone}
                  onChange={(e) => setCustPhone(e.target.value)}
                  className="w-full px-3 py-2 border border-[#E8EAED] rounded-lg focus:outline-none focus:border-[#16A36A]"
                />
              </div>

              <div>
                <label className="block font-semibold text-[#17191C] mb-1">Notes / Address</label>
                <textarea
                  rows={2}
                  placeholder="e.g. Main bazaar corner shop"
                  value={custNotes}
                  onChange={(e) => setCustNotes(e.target.value)}
                  className="w-full px-3 py-2 border border-[#E8EAED] rounded-lg focus:outline-none focus:border-[#16A36A]"
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-2 border-t border-[#F0F2F5]">
                <button
                  type="button"
                  onClick={() => setShowAddCustomer(false)}
                  className="px-4 py-2 border border-[#E8EAED] rounded-lg text-xs font-semibold text-[#737780] hover:bg-[#F7F8FA]"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-4 py-2 bg-[#16A36A] hover:bg-[#0D6843] text-white rounded-lg text-xs font-bold transition-colors disabled:opacity-50"
                >
                  {submitting ? 'Creating...' : 'Create Account'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal: Give Credit Sale */}
      {showAddCredit && activeCustomer && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl border border-[#E8EAED] max-w-md w-full p-6 shadow-xl space-y-4">
            <div className="flex items-center justify-between border-b border-[#F0F2F5] pb-3">
              <div>
                <h3 className="font-bold text-base text-[#17191C]">Record Credit Sale (Udhaar)</h3>
                <p className="text-xs text-[#737780]">For {activeCustomer.name}</p>
              </div>
              <button onClick={() => setShowAddCredit(false)} className="text-[#737780] hover:text-[#17191C]">
                <X className="w-5 h-5" />
              </button>
            </div>

            {formError && (
              <div className="p-3 bg-[#FDF0F0] text-[#DC5555] rounded-lg text-xs font-semibold flex items-center gap-1.5">
                <AlertOctagon className="w-4 h-4 shrink-0" />
                <span>{formError}</span>
              </div>
            )}

            <form onSubmit={handleSubmitCreditSale} className="space-y-4 text-xs">
              <div>
                <label className="block font-semibold text-[#17191C] mb-1">Credit Amount (₹ INR) *</label>
                <div className="relative">
                  <span className="absolute left-3 top-1/2 -translate-y-1/2 text-sm font-bold text-[#737780]">₹</span>
                  <input
                    type="number"
                    step="0.01"
                    required
                    placeholder="e.g. 5000"
                    value={entryAmountINR}
                    onChange={(e) => setEntryAmountINR(e.target.value)}
                    className="w-full pl-8 pr-3 py-2 border border-[#E8EAED] rounded-lg text-sm font-bold tabular-nums text-[#17191C] focus:outline-none focus:border-[#16A36A]"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-semibold text-[#17191C] mb-1">Sale Date</label>
                  <input
                    type="date"
                    required
                    value={entryDate}
                    onChange={(e) => setEntryDate(e.target.value)}
                    className="w-full px-3 py-2 border border-[#E8EAED] rounded-lg focus:outline-none focus:border-[#16A36A]"
                  />
                </div>
                <div>
                  <label className="block font-semibold text-[#17191C] mb-1">Expected Repayment Due *</label>
                  <input
                    type="date"
                    required
                    value={entryDueDate}
                    onChange={(e) => setEntryDueDate(e.target.value)}
                    className="w-full px-3 py-2 border border-[#E8EAED] rounded-lg focus:outline-none focus:border-[#16A36A]"
                  />
                </div>
              </div>

              <div>
                <label className="block font-semibold text-[#17191C] mb-1">Items / Bill Notes</label>
                <input
                  type="text"
                  placeholder="e.g. 2 bags rice, 1 tin oil"
                  value={entryNotes}
                  onChange={(e) => setEntryNotes(e.target.value)}
                  className="w-full px-3 py-2 border border-[#E8EAED] rounded-lg focus:outline-none focus:border-[#16A36A]"
                />
              </div>

              <div className="p-3 bg-[#EDF2FD] text-[#6D8FE8] rounded-lg text-[11px] font-medium">
                Note: Credit sales increase customer receivables. Available cash is only updated when a repayment is recorded.
              </div>

              <div className="flex items-center justify-end gap-2 pt-2 border-t border-[#F0F2F5]">
                <button
                  type="button"
                  onClick={() => setShowAddCredit(false)}
                  className="px-4 py-2 border border-[#E8EAED] rounded-lg text-xs font-semibold text-[#737780] hover:bg-[#F7F8FA]"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-4 py-2 bg-[#16A36A] hover:bg-[#0D6843] text-white rounded-lg text-xs font-bold transition-colors disabled:opacity-50"
                >
                  {submitting ? 'Recording...' : 'Record Credit Sale'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal: Record Repayment */}
      {showRepay && activeCustomer && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl border border-[#E8EAED] max-w-md w-full p-6 shadow-xl space-y-4">
            <div className="flex items-center justify-between border-b border-[#F0F2F5] pb-3">
              <div>
                <h3 className="font-bold text-base text-[#17191C]">Record Customer Repayment</h3>
                <p className="text-xs text-[#737780]">For {activeCustomer.name}</p>
              </div>
              <button onClick={() => setShowRepay(false)} className="text-[#737780] hover:text-[#17191C]">
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Current outstanding banner */}
            <div className="p-3 rounded-lg bg-[#F7F8FA] border border-[#E8EAED] flex items-center justify-between">
              <span className="text-xs text-[#737780]">Current Outstanding:</span>
              <span className="text-sm font-bold text-[#DC5555] tabular-nums">
                {formatPaiseToINR(activeCustomer.outstanding_balance_paise)}
              </span>
            </div>

            {formError && (
              <div className="p-3 bg-[#FDF0F0] text-[#DC5555] rounded-lg text-xs font-semibold flex items-center gap-1.5">
                <AlertOctagon className="w-4 h-4 shrink-0" />
                <span>{formError}</span>
              </div>
            )}

            <form onSubmit={handleSubmitRepayment} className="space-y-4 text-xs">
              <div>
                <div className="flex items-center justify-between mb-1">
                  <label className="font-semibold text-[#17191C]">Repayment Amount (₹ INR) *</label>
                  <button
                    type="button"
                    onClick={() => setEntryAmountINR((activeCustomer.outstanding_balance_paise / 100).toString())}
                    className="text-[11px] text-[#16A36A] font-bold hover:underline"
                  >
                    Full Repayment
                  </button>
                </div>
                <div className="relative">
                  <span className="absolute left-3 top-1/2 -translate-y-1/2 text-sm font-bold text-[#737780]">₹</span>
                  <input
                    type="number"
                    step="0.01"
                    required
                    placeholder="e.g. 2000"
                    value={entryAmountINR}
                    onChange={(e) => setEntryAmountINR(e.target.value)}
                    className="w-full pl-8 pr-3 py-2 border border-[#E8EAED] rounded-lg text-sm font-bold tabular-nums text-[#17191C] focus:outline-none focus:border-[#16A36A]"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-semibold text-[#17191C] mb-1">Payment Date</label>
                  <input
                    type="date"
                    required
                    value={entryDate}
                    onChange={(e) => setEntryDate(e.target.value)}
                    className="w-full px-3 py-2 border border-[#E8EAED] rounded-lg focus:outline-none focus:border-[#16A36A]"
                  />
                </div>
                <div>
                  <label className="block font-semibold text-[#17191C] mb-1">Payment Method</label>
                  <select
                    value={entryMethod}
                    onChange={(e) => setEntryMethod(e.target.value)}
                    className="w-full px-3 py-2 border border-[#E8EAED] rounded-lg focus:outline-none focus:border-[#16A36A] bg-white"
                  >
                    <option value="cash">Cash in Hand</option>
                    <option value="upi">UPI / QR Code</option>
                    <option value="bank_transfer">Bank Transfer</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block font-semibold text-[#17191C] mb-1">Receipt / Payment Notes</label>
                <input
                  type="text"
                  placeholder="e.g. Received partial cash repayment"
                  value={entryNotes}
                  onChange={(e) => setEntryNotes(e.target.value)}
                  className="w-full px-3 py-2 border border-[#E8EAED] rounded-lg focus:outline-none focus:border-[#16A36A]"
                />
              </div>

              <div className="p-3 bg-[#E8F7EF] text-[#16A36A] rounded-lg text-[11px] font-medium flex items-center gap-1.5">
                <CheckCircle2 className="w-4 h-4 shrink-0" />
                <span>Synchronized: This repayment will instantly increase your shop available cash.</span>
              </div>

              <div className="flex items-center justify-end gap-2 pt-2 border-t border-[#F0F2F5]">
                <button
                  type="button"
                  onClick={() => setShowRepay(false)}
                  className="px-4 py-2 border border-[#E8EAED] rounded-lg text-xs font-semibold text-[#737780] hover:bg-[#F7F8FA]"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-4 py-2 bg-[#16A36A] hover:bg-[#0D6843] text-white rounded-lg text-xs font-bold transition-colors disabled:opacity-50"
                >
                  {submitting ? 'Recording...' : 'Accept Repayment'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
