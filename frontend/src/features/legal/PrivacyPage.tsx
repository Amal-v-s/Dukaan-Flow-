import React from 'react'
import { Link } from 'react-router-dom'
import { ArrowLeft, Shield, Lock, Database, FileText } from 'lucide-react'

export const PrivacyPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-[#F7F8FA] py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-3xl mx-auto bg-white border border-[#E8EAED] rounded-2xl p-8 sm:p-12 shadow-sm">
        <Link
          to="/"
          className="inline-flex items-center gap-2 text-xs font-semibold text-[#16A36A] hover:underline mb-6"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to DukaanFlow</span>
        </Link>

        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 rounded-xl bg-[#E8F7EF] text-[#16A36A] flex items-center justify-center">
            <Shield className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-[#17191C]">Merchant Privacy Policy</h1>
            <p className="text-xs text-[#737780] mt-0.5">Last updated: October 2026</p>
          </div>
        </div>

        <div className="space-y-6 text-sm text-[#4A4D53] leading-relaxed">
          <section>
            <h2 className="text-base font-bold text-[#17191C] flex items-center gap-2 mb-2">
              <Database className="w-4 h-4 text-[#16A36A]" />
              1. What Information We Store
            </h2>
            <p>
              DukaanFlow stores the operational data necessary to compute your store's cash book, khata balances, and cash-flow projections:
            </p>
            <ul className="list-disc pl-5 mt-2 space-y-1 text-xs">
              <li><strong>Merchant Profile:</strong> Store name, email address, and authenticated user IDs.</li>
              <li><strong>Customer Khata:</strong> Customer names, optional phone numbers, and chronological ledger entries (credit sales and repayments).</li>
              <li><strong>Supplier Accounts:</strong> Supplier names, invoices/bills, and payment records.</li>
              <li><strong>Cash Register Events:</strong> Daily opening cash balances, recorded expenses, and categorized cash movements.</li>
            </ul>
          </section>

          <section>
            <h2 className="text-base font-bold text-[#17191C] flex items-center gap-2 mb-2">
              <Lock className="w-4 h-4 text-[#16A36A]" />
              2. Data Storage & Multi-Tenant Isolation
            </h2>
            <p>
              Your store's financial data is strictly tenant-isolated. No merchant can access another merchant's records. All production databases are hosted securely on Google Cloud Platform in the India region (Mumbai, <code>asia-south1</code>), adhering to Indian data residency standards.
            </p>
          </section>

          <section>
            <h2 className="text-base font-bold text-[#17191C] flex items-center gap-2 mb-2">
              <FileText className="w-4 h-4 text-[#16A36A]" />
              3. Artificial Intelligence & Privacy Disclosures
            </h2>
            <p>
              When optional AI explanations or business summaries are requested:
            </p>
            <ul className="list-disc pl-5 mt-2 space-y-1 text-xs">
              <li>Only mathematical summaries and high-level totals are submitted to language models.</li>
              <li>Raw customer phone numbers, internal merchant notes, and unredacted names are never sent to external AI providers.</li>
              <li>Your store data is never used to train public language models.</li>
            </ul>
          </section>

          <section>
            <h2 className="text-base font-bold text-[#17191C] mb-2">4. Data Export & Deletion</h2>
            <p>
              You own your data completely. At any time, you can export your entire khata, supplier bills, and expenses via the built-in CSV export tools. Upon account closure, all associated records will be permanently purged in accordance with our data retention schedule.
            </p>
          </section>
        </div>
      </div>
    </div>
  )
}
