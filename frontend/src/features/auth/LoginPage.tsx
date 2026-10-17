import React, { useState } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { Store, ShieldCheck, ArrowRight, Lock, Mail, User, Building, AlertCircle } from 'lucide-react'
import { useAuth } from '../../context/AuthContext'

export const LoginPage: React.FC = () => {
  const [isRegister, setIsRegister] = useState(false)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [fullName, setFullName] = useState('')
  const [businessName, setBusinessName] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  const { login, register } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const from = (location.state as any)?.from?.pathname || '/'

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setIsSubmitting(true)

    try {
      if (isRegister) {
        if (!fullName.trim() || !businessName.trim()) {
          throw new Error('Please provide both your name and business name.')
        }
        if (password.length < 8) {
          throw new Error('Password must be at least 8 characters long.')
        }
        await register(email, password, fullName, businessName)
      } else {
        await login(email, password)
      }
      navigate(from, { replace: true })
    } catch (err: any) {
      setError(err.message || 'Authentication failed. Please try again.')
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleDemoLogin = async () => {
    setError(null)
    setIsSubmitting(true)
    try {
      await login('demo@dukaanflow.in', 'password123')
      navigate(from, { replace: true })
    } catch {
      // If demo user wasn't registered yet, try registering demo user
      try {
        await register('demo@dukaanflow.in', 'password123', 'Ramesh Kumar (Demo)', 'Demo Kirana Store')
        navigate(from, { replace: true })
      } catch (regErr: any) {
        setError(regErr.message || 'Demo login failed.')
      }
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="min-h-screen bg-[#F7F8FA] flex flex-col justify-center items-center px-4 py-12 sm:px-6 lg:px-8">
      {/* Brand Header */}
      <div className="sm:mx-auto sm:w-full sm:max-w-md text-center mb-8">
        <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-[#E8F7EF] text-[#16A36A] mb-4 shadow-sm border border-[#C6ECD8]">
          <Store className="w-8 h-8" />
        </div>
        <h1 className="text-2xl font-bold tracking-tight text-[#17191C]">DukaanFlow</h1>
        <p className="mt-1 text-sm text-[#737780]">
          Merchant Precision Cash Book & Working Capital Management
        </p>
      </div>

      {/* Auth Card */}
      <div className="w-full max-w-md">
        <div className="bg-white py-8 px-6 shadow-sm border border-[#E8EAED] rounded-2xl sm:px-10">
          {/* Tab Selector */}
          <div className="flex border-b border-[#E8EAED] mb-6">
            <button
              type="button"
              onClick={() => {
                setIsRegister(false)
                setError(null)
              }}
              className={`flex-1 pb-3 text-sm font-semibold border-b-2 transition-colors ${
                !isRegister
                  ? 'border-[#16A36A] text-[#16A36A]'
                  : 'border-transparent text-[#737780] hover:text-[#17191C]'
              }`}
            >
              Sign In
            </button>
            <button
              type="button"
              onClick={() => {
                setIsRegister(true)
                setError(null)
              }}
              className={`flex-1 pb-3 text-sm font-semibold border-b-2 transition-colors ${
                isRegister
                  ? 'border-[#16A36A] text-[#16A36A]'
                  : 'border-transparent text-[#737780] hover:text-[#17191C]'
              }`}
            >
              Register Store
            </button>
          </div>

          {/* Error Banner */}
          {error && (
            <div className="mb-5 p-3.5 rounded-xl bg-red-50 border border-red-200 flex items-start gap-2.5 text-red-700 text-xs">
              <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
              <div className="font-medium leading-relaxed">{error}</div>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            {isRegister && (
              <>
                <div>
                  <label className="block text-xs font-semibold text-[#17191C] mb-1.5">
                    Your Full Name
                  </label>
                  <div className="relative">
                    <User className="w-4 h-4 text-[#A0A4A8] absolute left-3 top-3" />
                    <input
                      type="text"
                      required
                      value={fullName}
                      onChange={(e) => setFullName(e.target.value)}
                      placeholder="e.g. Ramesh Kumar"
                      className="w-full pl-9 pr-3 py-2 text-sm border border-[#D0D5DD] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#16A36A] focus:border-[#16A36A]"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-[#17191C] mb-1.5">
                    Dukaan / Business Name
                  </label>
                  <div className="relative">
                    <Building className="w-4 h-4 text-[#A0A4A8] absolute left-3 top-3" />
                    <input
                      type="text"
                      required
                      value={businessName}
                      onChange={(e) => setBusinessName(e.target.value)}
                      placeholder="e.g. Sharma Provision Store"
                      className="w-full pl-9 pr-3 py-2 text-sm border border-[#D0D5DD] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#16A36A] focus:border-[#16A36A]"
                    />
                  </div>
                </div>
              </>
            )}

            <div>
              <label className="block text-xs font-semibold text-[#17191C] mb-1.5">
                Email Address
              </label>
              <div className="relative">
                <Mail className="w-4 h-4 text-[#A0A4A8] absolute left-3 top-3" />
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="name@store.com"
                  className="w-full pl-9 pr-3 py-2 text-sm border border-[#D0D5DD] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#16A36A] focus:border-[#16A36A]"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-[#17191C] mb-1.5">
                Password {isRegister && <span className="font-normal text-[#737780]">(min. 8 characters)</span>}
              </label>
              <div className="relative">
                <Lock className="w-4 h-4 text-[#A0A4A8] absolute left-3 top-3" />
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full pl-9 pr-3 py-2 text-sm border border-[#D0D5DD] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#16A36A] focus:border-[#16A36A]"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full mt-2 flex items-center justify-center gap-2 py-2.5 px-4 border border-transparent rounded-lg shadow-sm text-sm font-semibold text-white bg-[#16A36A] hover:bg-[#138A5A] focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-[#16A36A] transition-colors disabled:opacity-50"
            >
              {isSubmitting ? (
                <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
              ) : (
                <>
                  <span>{isRegister ? 'Create Store Account' : 'Sign In to DukaanFlow'}</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </form>

          {/* Quick Demo Login Option */}
          <div className="mt-6 pt-6 border-t border-[#E8EAED]">
            <p className="text-center text-xs text-[#737780] mb-3">
              Want to explore with sample kirana data?
            </p>
            <button
              type="button"
              onClick={handleDemoLogin}
              disabled={isSubmitting}
              className="w-full py-2 px-3 text-xs font-semibold text-[#16A36A] bg-[#E8F7EF] hover:bg-[#D5F2E3] border border-[#C6ECD8] rounded-lg transition-colors flex items-center justify-center gap-2"
            >
              <ShieldCheck className="w-4 h-4" />
              <span>Use Instant Demo Store (1-Click)</span>
            </button>
          </div>
        </div>

        {/* Security badge footer */}
        <div className="mt-6 text-center text-xs text-[#737780] flex items-center justify-center gap-1.5">
          <ShieldCheck className="w-3.5 h-3.5 text-[#16A36A]" />
          <span>Tenant Isolated & Encrypted Sessions (JWT + Bcrypt)</span>
        </div>
      </div>
    </div>
  )
}
