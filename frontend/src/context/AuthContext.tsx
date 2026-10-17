import React, { createContext, useContext, useState, useEffect } from 'react'
import { getAuthToken, setAuthToken, getStoredUser, setStoredUser, apiFetch } from '../lib/api'

export interface AuthUser {
  id: string
  email: string
  full_name: string
  business_id: string
  business_name: string
  role: string
}

interface AuthContextType {
  user: AuthUser | null
  token: string | null
  isAuthenticated: boolean
  isLoading: boolean
  login: (email: string, password: string) => Promise<void>
  register: (email: string, password: string, fullName: string, businessName: string) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [token, setTokenState] = useState<string | null>(() => getAuthToken())
  const [user, setUserState] = useState<AuthUser | null>(() => getStoredUser())
  const [isLoading, setIsLoading] = useState<boolean>(true)

  useEffect(() => {
    async function verifySession() {
      const currentToken = getAuthToken()
      if (!currentToken) {
        setIsLoading(false)
        return
      }

      try {
        const res = await apiFetch('/api/v1/auth/me')
        if (res.ok) {
          const userData = await res.json()
          setUserState(userData)
          setStoredUser(userData)
        } else {
          // Token expired or invalid
          setAuthToken(null)
          setTokenState(null)
          setUserState(null)
        }
      } catch (err) {
        console.error('Session verification failed', err)
      } finally {
        setIsLoading(false)
      }
    }

    verifySession()
  }, [])

  const login = async (email: string, password: string) => {
    const res = await fetch('/api/v1/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    })

    if (!res.ok) {
      const errorData = await res.json().catch(() => ({}))
      const msg = errorData.detail || errorData.error?.message || 'Login failed. Please check your credentials.'
      throw new Error(msg)
    }

    const data = await res.json()
    setAuthToken(data.access_token)
    setStoredUser(data.user)
    setTokenState(data.access_token)
    setUserState(data.user)
  }

  const register = async (email: string, password: string, fullName: string, businessName: string) => {
    const res = await fetch('/api/v1/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email,
        password,
        full_name: fullName,
        business_name: businessName,
      }),
    })

    if (!res.ok) {
      const errorData = await res.json().catch(() => ({}))
      const msg = errorData.detail || errorData.error?.message || 'Registration failed. Please check your inputs.'
      throw new Error(msg)
    }

    const data = await res.json()
    setAuthToken(data.access_token)
    setStoredUser(data.user)
    setTokenState(data.access_token)
    setUserState(data.user)
  }

  const logout = () => {
    setAuthToken(null)
    setTokenState(null)
    setUserState(null)
    window.location.href = '/login'
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isAuthenticated: !!token && !!user,
        isLoading,
        login,
        register,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
