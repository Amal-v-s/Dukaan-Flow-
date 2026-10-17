import React, { useEffect, useState, useCallback } from 'react'
import { Plus, Search, X, CheckCircle2, AlertOctagon, Building2 } from 'lucide-react'
import { formatPaiseToINR, formatDate, parseINRToPaise } from '../../lib/formatters'
import { StatusPill } from '../../components/ui/StatusPill'

interface SupplierBill {
  id: string
  supplier_id: string
  supplier_name: string
  description: string
  bill_amount_paise: number
  paid_amount_paise: number
  remaining_amount_paise: number
  bill_date: string
  due_date: string
  status: 'unpaid' | 'partially_paid' | 'paid'
}

interface Supplier {
  id: string
  name: string
  phone?: string
}

export const SuppliersPage: React.FC = () => {
  const [bills, setBills] = useState<SupplierBill[]>([])
  const [suppliers, setSuppliers] = useState<Supplier[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('all')

  // Modals
  const [showAddBill, setShowAddBill] = useState(false)
  const [showPayBill, setShowPayBill] = useState(false)
  const [activeBill, setActiveBill] = useState<SupplierBill | null>(null)

  // Form states for New Bill
  const [selectedSupplierId, setSelectedSupplierId] = useState('')
  const [newSupplierName, setNewSupplierName] = useState('')
  const [billDesc, setBillDesc] = useState('')
  const [billAmountINR, setBillAmountINR] = useState('')
  const [billDate, setBillDate] = useState('2026-10-17')
  const [billDueDate, setBillDueDate] = useState('2026-10-25')

  // Form states for Pay Bill
  const [payAmountINR, setPayAmountINR] = useState('')
  const [payDate, setPayDate] = useState('2026-10-17')
  const [payMethod, setPayMethod] = useState('cash')
  const [payNotes, setPayNotes] = useState('')

  const [formError, setFormError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  const fetchData = useCallback(async () => {
    try {
      const [billsRes, supsRes] = await Promise.all([
        fetch('/api/v1/supplier-bills'),
        fetch('/api/v1/suppliers'),
      ])
      if (billsRes.ok) {
        const data = await billsRes.json()
        setBills(data.items || [])
      }
      if (supsRes.ok) {
        const data = await supsRes.json()
        setSuppliers(data.items || [])
        if (data.items?.length > 0 && !selectedSupplierId) {
          setSelectedSupplierId(data.items[0].id)
        }
      }
    } catch (err) {
      console.error('Error fetching suppliers data:', err)
    } finally {
      setLoading(false)
    }
  }, [selectedSupplierId])

  useEffect(() => {
    void fetchData()
  }, [fetchData])

  const handleOpenPay = (bill: SupplierBill) => {
    setActiveBill(bill)
    setPayAmountINR((bill.remaining_amount_paise / 100).toString())
    setPayDate('2026-10-17')
    setPayMethod('cash')
    setPayNotes('')
    setFormError(null)
    setShowPayBill(true)
  }

  const handleCreateBill = async (e: React.FormEvent) => {
    e.preventDefault()
    const amountPaise = parseINRToPaise(billAmountINR)
    if (amountPaise <= 0) {
      setFormError('Please enter a valid bill amount in rupees')
      return
    }

    if (!billDesc.trim()) {
      setFormError('Bill description is required')
      return
    }

    setSubmitting(true)
    setFormError(null)
    try {
      let targetSupplierId = selectedSupplierId
      // If user typed a new supplier name
      if (newSupplierName.trim()) {
        const supRes = await fetch('/api/v1/suppliers', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ name: newSupplierName.trim() }),
        })
        if (supRes.ok) {
          const newSup = await supRes.json()
          targetSupplierId = newSup.id
        }
      }

      const res = await fetch('/api/v1/supplier-bills', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          supplier_id: targetSupplierId,
          description: billDesc.trim(),
          bill_amount_paise: amountPaise,
          bill_date: billDate,
          due_date: billDueDate,
        }),
      })

      if (!res.ok) {
        const errData = await res.json()
        throw new Error(errData?.error?.message || 'Failed to record bill')
      }

      setShowAddBill(false)
      setBillDesc('')
      setBillAmountINR('')
      setNewSupplierName('')
      await fetchData()
    } catch (err: unknown) {
      if (err instanceof Error) {
        setFormError(err.message)
      } else {
        setFormError('Failed to record bill')
      }
    } finally {
      setSubmitting(false)
    }
  }

  const handleSubmitPayment = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!activeBill) return

    const amountPaise = parseINRToPaise(payAmountINR)
    if (amountPaise <= 0) {
      setFormError('Please enter a valid payment amount')
      return
    }

    if (amountPaise > activeBill.remaining_amount_paise) {
      setFormError(
        `Payment cannot exceed remaining due on this bill (${formatPaiseToINR(activeBill.remaining_amount_paise)})`
      )
      return
    }

    setSubmitting(true)
    setFormError(null)
    try {
      const res = await fetch(`/api/v1/supplier-bills/${activeBill.id}/payments`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          amount_paise: amountPaise,
          payment_date: payDate,
          payment_method: payMethod,
          notes: payNotes,
        }),
      })

      if (!res.ok) {
        const errData = await res.json()
        throw new Error(errData?.error?.message || 'Failed to record supplier payment')
      }

      setShowPayBill(false)
      await fetchData()
    } catch (err: unknown) {
      if (err instanceof Error) {
        setFormError(err.message)
      } else {
        setFormError('Failed to record supplier payment')
      }
    } finally {
      setSubmitting(false)
    }
  }

  const filtered = bills.filter((b) => {
    const matchesSearch =
      b.supplier_name.toLowerCase().includes(search.toLowerCase()) ||
      b.description.toLowerCase().includes(search.toLowerCase())
    if (!matchesSearch) return false
    if (statusFilter === 'all') return true
    return b.status === statusFilter
  })

  const totalPayable = bills.reduce((acc, b) => acc + b.remaining_amount_paise, 0)
  const totalBilled = bills.reduce((acc, b) => acc + b.bill_amount_paise, 0)
  const totalPaid = bills.reduce((acc, b) => acc + b.paid_amount_paise, 0)

  return (
    <div className="space-y-6">
      {/* Top summary KPIs */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-5">
        <div className="bg-white rounded-xl border border-[#E8EAED] p-5 shadow-[0_1px_3px_rgba(0,0,0,0.04)]">
          <span className="text-xs font-semibold text-[#737780] uppercase tracking-wider">Total Supplier Payables</span>
          <p className="text-2xl font-bold text-[#E9A23B] tabular-nums mt-0.5">
            {formatPaiseToINR(totalPayable)}
          </p>
          <p className="text-xs text-[#737780] mt-1">Pending payments to distributors</p>
        </div>

        <div className="bg-white rounded-xl border border-[#E8EAED] p-5 shadow-[0_1px_3px_rgba(0,0,0,0.04)]">
          <span className="text-xs font-semibold text-[#737780] uppercase tracking-wider">Total Purchases Billed</span>
          <p className="text-2xl font-bold text-[#17191C] tabular-nums mt-0.5">
            {formatPaiseToINR(totalBilled)}
          </p>
          <p className="text-xs text-[#737780] mt-1">Cumulative invoices received</p>
        </div>

        <div className="bg-white rounded-xl border border-[#E8EAED] p-5 shadow-[0_1px_3px_rgba(0,0,0,0.04)] flex flex-col justify-between">
          <div>
            <span className="text-xs font-semibold text-[#737780] uppercase tracking-wider">Total Invoices Settled</span>
            <p className="text-2xl font-bold text-[#16A36A] tabular-nums mt-0.5">
              {formatPaiseToINR(totalPaid)}
            </p>
          </div>
          <button
            onClick={() => {
              setFormError(null)
              setShowAddBill(true)
            }}
            className="mt-3 w-full py-2 bg-[#16A36A] hover:bg-[#0D6843] text-white text-xs font-bold rounded-lg transition-colors flex items-center justify-center gap-1.5 shadow-sm"
          >
            <Plus className="w-4 h-4" />
            <span>Add Supplier Bill</span>
          </button>
        </div>
      </div>

      {/* Bills Table Container */}
      <div className="bg-white rounded-xl border border-[#E8EAED] overflow-hidden shadow-[0_1px_3px_rgba(0,0,0,0.04)]">
        <div className="p-4 border-b border-[#E8EAED] flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-[#F7F8FA]">
          <div className="relative flex-1 max-w-sm">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-[#737780]" />
            <input
              type="text"
              placeholder="Search supplier or bill description..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-9 pr-3 py-1.5 bg-white border border-[#E8EAED] rounded-lg text-xs text-[#17191C] focus:outline-none focus:border-[#16A36A]"
            />
          </div>

          <div className="flex items-center gap-2">
            <span className="text-xs text-[#737780] font-semibold">Status:</span>
            <div className="inline-flex rounded-lg border border-[#E8EAED] p-0.5 bg-white text-xs">
              {['all', 'unpaid', 'partially_paid', 'paid'].map((st) => (
                <button
                  key={st}
                  onClick={() => setStatusFilter(st)}
                  className={`px-2.5 py-1 rounded-md font-medium capitalize transition-colors ${
                    statusFilter === st ? 'bg-[#16A36A] text-white font-bold' : 'text-[#737780] hover:text-[#17191C]'
                  }`}
                >
                  {st.replace('_', ' ')}
                </button>
              ))}
            </div>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-[#F0F2F5] text-[#737780] font-semibold uppercase tracking-wider border-b border-[#E8EAED]">
              <tr>
                <th className="py-3 px-4">Supplier</th>
                <th className="py-3 px-4">Invoice Description</th>
                <th className="py-3 px-4 text-right">Total Bill</th>
                <th className="py-3 px-4 text-right">Remaining Due</th>
                <th className="py-3 px-4">Due Date</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#E8EAED] text-[#17191C]">
              {loading ? (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-[#737780]">
                    Loading supplier bills...
                  </td>
                </tr>
              ) : filtered.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-[#737780]">
                    No supplier bills found matching criteria.
                  </td>
                </tr>
              ) : (
                filtered.map((b) => (
                  <tr key={b.id} className="hover:bg-[#F9FAFB] transition-colors">
                    <td className="py-3.5 px-4 font-semibold text-[#17191C]">
                      <div className="flex items-center gap-2">
                        <Building2 className="w-4 h-4 text-[#737780] shrink-0" />
                        <span>{b.supplier_name}</span>
                      </div>
                    </td>
                    <td className="py-3.5 px-4 text-[#737780]">{b.description}</td>
                    <td className="py-3.5 px-4 text-right tabular-nums text-[#737780]">
                      {formatPaiseToINR(b.bill_amount_paise)}
                    </td>
                    <td className="py-3.5 px-4 text-right font-bold tabular-nums text-[#17191C]">
                      {formatPaiseToINR(b.remaining_amount_paise)}
                    </td>
                    <td className="py-3.5 px-4 text-[#737780]">{formatDate(b.due_date)}</td>
                    <td className="py-3.5 px-4">
                      <StatusPill
                        label={b.status.replace('_', ' ')}
                        variant={b.status === 'paid' ? 'safe' : b.status === 'partially_paid' ? 'warning' : 'alert'}
                      />
                    </td>
                    <td className="py-3.5 px-4 text-right">
                      {b.status !== 'paid' ? (
                        <button
                          onClick={() => handleOpenPay(b)}
                          className="px-2.5 py-1 rounded bg-[#FEF6EB] text-[#E9A23B] font-bold hover:bg-[#FDE68A] transition-colors"
                        >
                          Pay Bill
                        </button>
                      ) : (
                        <span className="text-[11px] font-semibold text-[#16A36A]">Settled ✓</span>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Modal: Add Supplier Bill */}
      {showAddBill && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl border border-[#E8EAED] max-w-md w-full p-6 shadow-xl space-y-4">
            <div className="flex items-center justify-between border-b border-[#F0F2F5] pb-3">
              <h3 className="font-bold text-base text-[#17191C]">Record New Supplier Bill</h3>
              <button onClick={() => setShowAddBill(false)} className="text-[#737780] hover:text-[#17191C]">
                <X className="w-5 h-5" />
              </button>
            </div>

            {formError && (
              <div className="p-3 bg-[#FDF0F0] text-[#DC5555] rounded-lg text-xs font-semibold flex items-center gap-1.5">
                <AlertOctagon className="w-4 h-4 shrink-0" />
                <span>{formError}</span>
              </div>
            )}

            <form onSubmit={handleCreateBill} className="space-y-4 text-xs">
              <div>
                <label className="block font-semibold text-[#17191C] mb-1">Select Supplier</label>
                <select
                  value={selectedSupplierId}
                  onChange={(e) => setSelectedSupplierId(e.target.value)}
                  className="w-full px-3 py-2 border border-[#E8EAED] rounded-lg bg-white focus:outline-none focus:border-[#16A36A]"
                >
                  {suppliers.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.name}
                    </option>
                  ))}
                </select>
                <div className="mt-2">
                  <span className="text-[11px] text-[#737780]">Or enter new distributor name:</span>
                  <input
                    type="text"
                    placeholder="e.g. Balaji Agro Trading"
                    value={newSupplierName}
                    onChange={(e) => setNewSupplierName(e.target.value)}
                    className="w-full mt-1 px-3 py-1.5 border border-[#E8EAED] rounded-lg focus:outline-none focus:border-[#16A36A]"
                  />
                </div>
              </div>

              <div>
                <label className="block font-semibold text-[#17191C] mb-1">Invoice / Item Description *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Edible oil 15L tins restock"
                  value={billDesc}
                  onChange={(e) => setBillDesc(e.target.value)}
                  className="w-full px-3 py-2 border border-[#E8EAED] rounded-lg focus:outline-none focus:border-[#16A36A]"
                />
              </div>

              <div>
                <label className="block font-semibold text-[#17191C] mb-1">Total Bill Amount (₹ INR) *</label>
                <div className="relative">
                  <span className="absolute left-3 top-1/2 -translate-y-1/2 text-sm font-bold text-[#737780]">₹</span>
                  <input
                    type="number"
                    step="0.01"
                    required
                    placeholder="e.g. 15000"
                    value={billAmountINR}
                    onChange={(e) => setBillAmountINR(e.target.value)}
                    className="w-full pl-8 pr-3 py-2 border border-[#E8EAED] rounded-lg text-sm font-bold tabular-nums text-[#17191C] focus:outline-none focus:border-[#16A36A]"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-semibold text-[#17191C] mb-1">Invoice Date</label>
                  <input
                    type="date"
                    required
                    value={billDate}
                    onChange={(e) => setBillDate(e.target.value)}
                    className="w-full px-3 py-2 border border-[#E8EAED] rounded-lg focus:outline-none focus:border-[#16A36A]"
                  />
                </div>
                <div>
                  <label className="block font-semibold text-[#17191C] mb-1">Payment Due Date *</label>
                  <input
                    type="date"
                    required
                    value={billDueDate}
                    onChange={(e) => setBillDueDate(e.target.value)}
                    className="w-full px-3 py-2 border border-[#E8EAED] rounded-lg focus:outline-none focus:border-[#16A36A]"
                  />
                </div>
              </div>

              <div className="p-3 bg-[#FEF6EB] text-[#E9A23B] rounded-lg text-[11px] font-medium">
                Note: Creating a supplier bill increases your liabilities (payables) and feeds the 14-day cash forecast. Cash will only be deducted when a payment is made.
              </div>

              <div className="flex items-center justify-end gap-2 pt-2 border-t border-[#F0F2F5]">
                <button
                  type="button"
                  onClick={() => setShowAddBill(false)}
                  className="px-4 py-2 border border-[#E8EAED] rounded-lg text-xs font-semibold text-[#737780] hover:bg-[#F7F8FA]"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-4 py-2 bg-[#16A36A] hover:bg-[#0D6843] text-white rounded-lg text-xs font-bold transition-colors disabled:opacity-50"
                >
                  {submitting ? 'Recording...' : 'Record Bill'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal: Pay Supplier Bill */}
      {showPayBill && activeBill && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl border border-[#E8EAED] max-w-md w-full p-6 shadow-xl space-y-4">
            <div className="flex items-center justify-between border-b border-[#F0F2F5] pb-3">
              <div>
                <h3 className="font-bold text-base text-[#17191C]">Pay Supplier Bill</h3>
                <p className="text-xs text-[#737780]">{activeBill.supplier_name} - {activeBill.description}</p>
              </div>
              <button onClick={() => setShowPayBill(false)} className="text-[#737780] hover:text-[#17191C]">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="p-3 rounded-lg bg-[#F7F8FA] border border-[#E8EAED] flex items-center justify-between">
              <span className="text-xs text-[#737780]">Remaining Due on Invoice:</span>
              <span className="text-sm font-bold text-[#17191C] tabular-nums">
                {formatPaiseToINR(activeBill.remaining_amount_paise)}
              </span>
            </div>

            {formError && (
              <div className="p-3 bg-[#FDF0F0] text-[#DC5555] rounded-lg text-xs font-semibold flex items-center gap-1.5">
                <AlertOctagon className="w-4 h-4 shrink-0" />
                <span>{formError}</span>
              </div>
            )}

            <form onSubmit={handleSubmitPayment} className="space-y-4 text-xs">
              <div>
                <div className="flex items-center justify-between mb-1">
                  <label className="font-semibold text-[#17191C]">Payment Amount (₹ INR) *</label>
                  <button
                    type="button"
                    onClick={() => setPayAmountINR((activeBill.remaining_amount_paise / 100).toString())}
                    className="text-[11px] text-[#16A36A] font-bold hover:underline"
                  >
                    Pay Full Remaining
                  </button>
                </div>
                <div className="relative">
                  <span className="absolute left-3 top-1/2 -translate-y-1/2 text-sm font-bold text-[#737780]">₹</span>
                  <input
                    type="number"
                    step="0.01"
                    required
                    placeholder="e.g. 5000"
                    value={payAmountINR}
                    onChange={(e) => setPayAmountINR(e.target.value)}
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
                    value={payDate}
                    onChange={(e) => setPayDate(e.target.value)}
                    className="w-full px-3 py-2 border border-[#E8EAED] rounded-lg focus:outline-none focus:border-[#16A36A]"
                  />
                </div>
                <div>
                  <label className="block font-semibold text-[#17191C] mb-1">Payment Method</label>
                  <select
                    value={payMethod}
                    onChange={(e) => setPayMethod(e.target.value)}
                    className="w-full px-3 py-2 border border-[#E8EAED] rounded-lg focus:outline-none focus:border-[#16A36A] bg-white"
                  >
                    <option value="cash">Cash in Hand</option>
                    <option value="upi">UPI / Vendor QR</option>
                    <option value="bank_transfer">Bank Transfer / NEFT</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block font-semibold text-[#17191C] mb-1">Notes / Transaction Reference</label>
                <input
                  type="text"
                  placeholder="e.g. Paid via UPI ref #12345"
                  value={payNotes}
                  onChange={(e) => setPayNotes(e.target.value)}
                  className="w-full px-3 py-2 border border-[#E8EAED] rounded-lg focus:outline-none focus:border-[#16A36A]"
                />
              </div>

              <div className="p-3 bg-[#E8F7EF] text-[#16A36A] rounded-lg text-[11px] font-medium flex items-center gap-1.5">
                <CheckCircle2 className="w-4 h-4 shrink-0" />
                <span>Cash Synchronized: This payment will immediately deduct from your shop available cash.</span>
              </div>

              <div className="flex items-center justify-end gap-2 pt-2 border-t border-[#F0F2F5]">
                <button
                  type="button"
                  onClick={() => setShowPayBill(false)}
                  className="px-4 py-2 border border-[#E8EAED] rounded-lg text-xs font-semibold text-[#737780] hover:bg-[#F7F8FA]"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-4 py-2 bg-[#16A36A] hover:bg-[#0D6843] text-white rounded-lg text-xs font-bold transition-colors disabled:opacity-50"
                >
                  {submitting ? 'Recording...' : 'Record Payment'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
