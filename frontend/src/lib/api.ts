/**
 * DukaanFlow Central API Client.
 *
 * Features:
 * - Automatic Authorization Bearer token injection for all /api/v1/ requests.
 * - Central token storage in localStorage ('dukaanflow_token').
 * - 401 Unauthorized handling with automatic session eviction and redirect to /login.
 * - Helper utilities (api.get, api.post, etc.) and global fetch interception.
 */

const TOKEN_KEY = 'dukaanflow_token'
const USER_KEY = 'dukaanflow_user'

export function getAuthToken(): string | null {
  try {
    return localStorage.getItem(TOKEN_KEY)
  } catch {
    return null
  }
}

export function setAuthToken(token: string | null): void {
  try {
    if (token) {
      localStorage.setItem(TOKEN_KEY, token)
    } else {
      localStorage.removeItem(TOKEN_KEY)
      localStorage.removeItem(USER_KEY)
    }
  } catch (err) {
    console.error('Failed to update auth token in storage', err)
  }
}

export function getStoredUser(): any | null {
  try {
    const raw = localStorage.getItem(USER_KEY)
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}

export function setStoredUser(user: any | null): void {
  try {
    if (user) {
      localStorage.setItem(USER_KEY, JSON.stringify(user))
    } else {
      localStorage.removeItem(USER_KEY)
    }
  } catch (err) {
    console.error('Failed to update stored user in storage', err)
  }
}

export async function apiFetch(input: RequestInfo | URL, init?: RequestInit): Promise<Response> {
  const token = getAuthToken()
  const headers = new Headers(init?.headers || {})

  if (token && !headers.has('Authorization')) {
    headers.set('Authorization', `Bearer ${token}`)
  }

  if (!headers.has('Content-Type') && !(init?.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json')
  }

  const response = await originalFetch(input, {
    ...init,
    headers,
  })

  // Evict credentials on 401 and redirect to login if not already on login page
  if (response.status === 401) {
    const urlStr = typeof input === 'string' ? input : input instanceof URL ? input.toString() : input.url
    const isAuthEndpoint = urlStr.includes('/auth/login') || urlStr.includes('/auth/register')
    if (!isAuthEndpoint) {
      setAuthToken(null)
      if (window.location.pathname !== '/login') {
        window.location.href = '/login'
      }
    }
  }

  return response
}

// Global fetch wrapper to ensure ALL existing feature components seamlessly send Bearer tokens and handle 401
const originalFetch = window.fetch
window.fetch = async function (input: RequestInfo | URL, init?: RequestInit): Promise<Response> {
  const urlStr = typeof input === 'string' ? input : input instanceof URL ? input.toString() : input.url
  const isAuthEndpoint = urlStr.includes('/api/v1/auth/login') || urlStr.includes('/api/v1/auth/register')
  let response: Response

  if (urlStr.includes('/api/v1/') && !isAuthEndpoint) {
    const token = getAuthToken()
    const headers = new Headers(init?.headers || {})
    if (token && !headers.has('Authorization')) {
      headers.set('Authorization', `Bearer ${token}`)
    }
    response = await originalFetch(input, { ...init, headers })
  } else {
    response = await originalFetch(input, init)
  }

  if (response.status === 401 && !isAuthEndpoint) {
    setAuthToken(null)
    if (window.location.pathname !== '/login') {
      window.location.href = '/login'
    }
  }

  return response
}

/**
 * Downloads a file from an authenticated endpoint by fetching the blob with Bearer token
 * and triggering a browser download anchor.
 */
export async function downloadFile(url: string, defaultFilename: string): Promise<void> {
  const response = await fetch(url)
  if (!response.ok) {
    const err = await response.json().catch(() => ({}))
    throw new Error(err?.detail || err?.error?.message || 'Download failed')
  }

  const blob = await response.blob()
  const contentDisposition = response.headers.get('Content-Disposition')
  let filename = defaultFilename
  if (contentDisposition) {
    const match = contentDisposition.match(/filename="?([^";]+)"?/)
    if (match && match[1]) {
      filename = match[1]
    }
  }

  const blobUrl = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = blobUrl
  a.download = filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(blobUrl)
}

export const api = {
  get: (url: string, init?: RequestInit) => apiFetch(url, { ...init, method: 'GET' }),
  post: (url: string, body?: any, init?: RequestInit) =>
    apiFetch(url, {
      ...init,
      method: 'POST',
      body: body ? JSON.stringify(body) : undefined,
    }),
  patch: (url: string, body?: any, init?: RequestInit) =>
    apiFetch(url, {
      ...init,
      method: 'PATCH',
      body: body ? JSON.stringify(body) : undefined,
    }),
  delete: (url: string, init?: RequestInit) => apiFetch(url, { ...init, method: 'DELETE' }),
}
