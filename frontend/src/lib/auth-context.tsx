/**
 * Havilah OS — Auth Context
 * ----------------------------------------------------------------------------
 * Provides login / logout / register / current-user state to the whole app.
 * Persists the JWT in localStorage so refreshes keep you logged in.
 *
 * Usage:
 *   <AuthProvider>            // in layout.tsx
 *     <App />
 *   </AuthProvider>
 *
 *   const { user, login, logout, loading } = useAuth()
 */

"use client"

import { createContext, useContext, useEffect, useState, useCallback, ReactNode } from "react"

const API_URL = process.env.NEXT_PUBLIC_HAVILAH_API_URL ?? ""
const TOKEN_KEY = "havilah_jwt"
const USER_KEY = "havilah_user"

export interface HavilahUser {
  user_id?: string
  id?: string
  email: string
  full_name: string
  is_admin: boolean
  role?: string
}

interface AuthState {
  user: HavilahUser | null
  token: string | null
  loading: boolean          // true during initial token validation
  error: string | null
}

interface AuthContextValue extends AuthState {
  login: (email: string, password: string) => Promise<void>
  register: (email: string, fullName: string, password: string) => Promise<void>
  logout: () => void
  clearError: () => void
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AuthState>({
    user: null,
    token: null,
    loading: true,
    error: null,
  })

  // ── On mount: try to restore session from localStorage ───────
  useEffect(() => {
    const restore = async () => {
      // Read cached values OUTSIDE the try block so the catch handler can use them
      const token = typeof window !== "undefined" ? localStorage.getItem(TOKEN_KEY) : null
      const cachedUser = typeof window !== "undefined" ? localStorage.getItem(USER_KEY) : null
      try {
        if (!token) {
          setState({ user: null, token: null, loading: false, error: null })
          return
        }
        // Validate token by hitting /api/auth/me
        const resp = await fetch(`${API_URL}/api/auth/me`, {
          headers: { Authorization: `Bearer ${token}` },
        })
        if (resp.ok) {
          const me = await resp.json()
          const user: HavilahUser = {
            user_id: me.id,
            email: me.email,
            full_name: me.full_name,
            is_admin: me.is_admin,
            role: me.role,
          }
          localStorage.setItem(USER_KEY, JSON.stringify(user))
          setState({ user, token, loading: false, error: null })
        } else {
          // Token expired or invalid — clear it
          localStorage.removeItem(TOKEN_KEY)
          localStorage.removeItem(USER_KEY)
          setState({ user: null, token: null, loading: false, error: null })
        }
      } catch (e) {
        // Network error — fall back to cached user if present, else logout
        if (cachedUser) {
          try {
            const u = JSON.parse(cachedUser)
            setState({ user: u, token, loading: false, error: null })
            return
          } catch {}
        }
        localStorage.removeItem(TOKEN_KEY)
        localStorage.removeItem(USER_KEY)
        setState({ user: null, token: null, loading: false, error: null })
      }
    }
    restore()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const login = useCallback(async (email: string, password: string) => {
    setState(s => ({ ...s, loading: true, error: null }))
    try {
      const resp = await fetch(`${API_URL}/api/auth/token`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      })
      if (!resp.ok) {
        const data = await resp.json().catch(() => ({}))
        throw new Error(data.detail ?? `Login failed (HTTP ${resp.status})`)
      }
      const data = await resp.json()
      const user: HavilahUser = {
        user_id: data.user_id,
        email: data.email,
        full_name: data.full_name,
        is_admin: data.is_admin,
        role: data.role ?? (data.is_admin ? "admin" : "viewer"),
      }
      localStorage.setItem(TOKEN_KEY, data.access_token)
      localStorage.setItem(USER_KEY, JSON.stringify(user))
      setState({ user, token: data.access_token, loading: false, error: null })
    } catch (e: any) {
      setState(s => ({ ...s, loading: false, error: e.message ?? "Login failed" }))
      throw e
    }
  }, [])

  const register = useCallback(async (email: string, fullName: string, password: string) => {
    setState(s => ({ ...s, loading: true, error: null }))
    try {
      const resp = await fetch(`${API_URL}/api/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, full_name: fullName, password }),
      })
      if (!resp.ok) {
        const data = await resp.json().catch(() => ({}))
        throw new Error(data.detail ?? `Registration failed (HTTP ${resp.status})`)
      }
      // Auto-login after successful registration
      await login(email, password)
    } catch (e: any) {
      setState(s => ({ ...s, loading: false, error: e.message ?? "Registration failed" }))
      throw e
    }
  }, [login])

  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(USER_KEY)
    setState({ user: null, token: null, loading: false, error: null })
  }, [])

  const clearError = useCallback(() => {
    setState(s => ({ ...s, error: null }))
  }, [])

  return (
    <AuthContext.Provider
      value={{ ...state, login, register, logout, clearError }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext)
  if (!ctx) {
    throw new Error("useAuth must be used inside <AuthProvider>")
  }
  return ctx
}

// ── Helper for non-React code: get the raw token from storage ──
export function getStoredToken(): string | null {
  if (typeof window === "undefined") return null
  return localStorage.getItem(TOKEN_KEY)
}
