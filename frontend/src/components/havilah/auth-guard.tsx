"use client"

import { useEffect, ReactNode } from "react"
import { useRouter } from "next/navigation"
import { useAuth } from "@/lib/auth-context"
import { Loader2, Crown } from "lucide-react"

/**
 * Wraps any page that requires authentication.
 * - Shows a full-screen loader while we restore the session
 * - Redirects to /login if not authenticated
 * - Renders children once we have a confirmed user
 */
export function AuthGuard({ children }: { children: ReactNode }) {
  const router = useRouter()
  const { user, loading } = useAuth()

  useEffect(() => {
    if (!loading && !user) {
      router.replace("/login")
    }
  }, [loading, user, router])

  if (loading) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center gap-4 bg-background">
        <div className="inline-flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-amber-400 to-amber-600 shadow-lg shadow-amber-500/20">
          <Crown className="h-6 w-6 text-white" />
        </div>
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <Loader2 className="h-4 w-4 animate-spin" />
          Loading your workspace...
        </div>
      </div>
    )
  }

  if (!user) {
    // Redirect is in flight — render nothing to avoid flashing the dashboard
    return null
  }

  return <>{children}</>
}
