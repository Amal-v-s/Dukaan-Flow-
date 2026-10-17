import React from 'react'
import { Link } from 'react-router-dom'
import { ArrowLeft, BookOpen, AlertCircle } from 'lucide-react'

export const TermsPage: React.FC = () => {
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
            <BookOpen className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-[#17191C]">Terms of Service</h1>
            <p className="text-xs text-[#737780] mt-0.5">Pilot Terms & Conditions — October 2026</p>
          </div>
        </div>

        <div className="space-y-6 text-sm text-[#4A4D53] leading-relaxed">
          <section className="p-4 bg-amber-50 border border-amber-200 rounded-xl flex items-start gap-3 text-xs text-amber-900">
            <AlertCircle className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
            <div>
              <strong className="font-semibold block mb-1">Financial & Legal Disclaimer:</strong>
              DukaanFlow provides cash-flow estimation, khata calculations, and working capital visibility tools. DukaanFlow does not provide formal chartered accountancy, legal, tax filing, or lending advice. All final business decisions remain solely the responsibility of the merchant.
            </div>
          </section>

          <section>
            <h2 className="text-base font-bold text-[#17191C] mb-2">1. Nature of Cash Flow Projections</h2>
            <p>
              The 14-day cash-flow forecast and "What-If" simulator are deterministic mathematical models derived from the customer collection due dates, supplier bill due dates, and expense history entered by the merchant. Projections reflect projected timing, not guaranteed bank deposits.
            </p>
          </section>

          <section>
            <h2 className="text-base font-bold text-[#17191C] mb-2">2. Acceptable Use</h2>
            <p>
              Merchants agree to use DukaanFlow exclusively for legitimate business recordkeeping. Any attempt to probe other tenants, reverse engineer proprietary forecasting engines, or submit malicious payloads will result in immediate suspension.
            </p>
          </section>

          <section>
            <h2 className="text-base font-bold text-[#17191C] mb-2">3. Controlled Pilot Limitations</h2>
            <p>
              During this controlled pilot phase, services are provided with active monitoring and continuous refinement. Features marked with "Experimental" or "AI" are supplementary and require merchant review before execution.
            </p>
          </section>
        </div>
      </div>
    </div>
  )
}
