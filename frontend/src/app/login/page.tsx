"use client"

import { useState, FormEvent, useEffect } from "react"
import { useRouter } from "next/navigation"
import { useAuth } from "@/lib/auth-context"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Loader2, Crown, LogIn, UserPlus, Eye, EyeOff } from "lucide-react"

export default function LoginPage() {
  const router = useRouter()
  const { login, register, user, loading, error, clearError } = useAuth()

  const [mode, setMode] = useState<"login" | "register">("login")
  const [email, setEmail] = useState("")
  const [fullName, setFullName] = useState("")
  const [password, setPassword] = useState("")
  const [showPassword, setShowPassword] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [localError, setLocalError] = useState<string | null>(null)

  // If already logged in, redirect to dashboard
  useEffect(() => {
    if (user && !loading) {
      router.replace("/")
    }
  }, [user, loading, router])

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setLocalError(null)
    clearError()
    setSubmitting(true)
    try {
      if (mode === "login") {
        await login(email, password)
      } else {
        if (password.length < 8) {
          setLocalError("Password must be at least 8 characters")
          setSubmitting(false)
          return
        }
        await register(email, fullName, password)
      }
      router.replace("/")
    } catch (err: any) {
      // Error is already set in context; just stop the spinner
    } finally {
      setSubmitting(false)
    }
  }

  const switchMode = () => {
    setMode(m => (m === "login" ? "register" : "login"))
    setLocalError(null)
    clearError()
  }

  const shownError = localError ?? error

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 via-amber-50/30 to-slate-100 p-4">
      {/* Decorative gradient */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 h-96 w-96 rounded-full bg-amber-200/20 blur-3xl" />
        <div className="absolute -bottom-40 -left-40 h-96 w-96 rounded-full bg-violet-200/20 blur-3xl" />
      </div>

      <div className="relative w-full max-w-md space-y-6">
        {/* Logo / Header */}
        <div className="text-center space-y-2">
          <div className="inline-flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-amber-400 to-amber-600 shadow-lg shadow-amber-500/20">
            <Crown className="h-7 w-7 text-white" />
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">Havilah OS</h1>
          <p className="text-sm text-slate-500">AI Executive Operating System</p>
        </div>

        <Card className="border-slate-200 shadow-xl shadow-slate-200/40">
          <CardHeader className="space-y-1">
            <CardTitle className="text-xl">
              {mode === "login" ? "Welcome back" : "Create your account"}
            </CardTitle>
            <CardDescription>
              {mode === "login"
                ? "Sign in to access your AI executive dashboard"
                : "Register to start orchestrating with Hermes"}
            </CardDescription>
          </CardHeader>

          <form onSubmit={handleSubmit}>
            <CardContent className="space-y-4">
              {shownError && (
                <Alert variant="destructive">
                  <AlertDescription>{shownError}</AlertDescription>
                </Alert>
              )}

              {mode === "register" && (
                <div className="space-y-2">
                  <Label htmlFor="fullName">Full name</Label>
                  <Input
                    id="fullName"
                    type="text"
                    placeholder="Jane Doe"
                    value={fullName}
                    onChange={e => setFullName(e.target.value)}
                    required
                    autoComplete="name"
                    disabled={submitting}
                  />
                </div>
              )}

              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <Input
                  id="email"
                  type="email"
                  placeholder="you@example.com"
                  value={email}
                  onChange={e => setEmail(e.target.value)}
                  required
                  autoComplete="email"
                  disabled={submitting}
                />
              </div>

              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label htmlFor="password">Password</Label>
                  {mode === "login" && (
                    <button
                      type="button"
                      className="text-xs text-slate-500 hover:text-slate-700 underline-offset-2 hover:underline"
                      onClick={() => setLocalError("Password reset is not yet implemented. Contact your administrator.")}
                    >
                      Forgot?
                    </button>
                  )}
                </div>
                <div className="relative">
                  <Input
                    id="password"
                    type={showPassword ? "text" : "password"}
                    placeholder={mode === "login" ? "••••••••" : "Min 8 characters"}
                    value={password}
                    onChange={e => setPassword(e.target.value)}
                    required
                    autoComplete={mode === "login" ? "current-password" : "new-password"}
                    disabled={submitting}
                    className="pr-10"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(s => !s)}
                    className="absolute right-2 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 p-1"
                    tabIndex={-1}
                  >
                    {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
              </div>
            </CardContent>

            <CardFooter className="flex flex-col gap-3">
              <Button
                type="submit"
                className="w-full bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-600 hover:to-amber-700 text-white shadow-md shadow-amber-500/20"
                disabled={submitting || loading}
              >
                {submitting ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    {mode === "login" ? "Signing in..." : "Creating account..."}
                  </>
                ) : mode === "login" ? (
                  <>
                    <LogIn className="h-4 w-4 mr-2" />
                    Sign in
                  </>
                ) : (
                  <>
                    <UserPlus className="h-4 w-4 mr-2" />
                    Create account
                  </>
                )}
              </Button>

              <button
                type="button"
                onClick={switchMode}
                className="text-sm text-slate-600 hover:text-slate-900 underline-offset-2 hover:underline"
                disabled={submitting}
              >
                {mode === "login"
                  ? "Don't have an account? Register"
                  : "Already have an account? Sign in"}
              </button>
            </CardFooter>
          </form>
        </Card>

        <p className="text-center text-xs text-slate-400">
          AI thinks, drafts, recommends, and prepares — but you decide.
        </p>
      </div>
    </div>
  )
}
