"use client"

import { useState, useEffect } from "react"
import { ThemeProvider as NextThemesProvider } from "next-themes"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { AuthProvider } from "@/lib/auth-context"
import * as Sentry from "@sentry/nextjs"

export function ThemeProvider({
  children,
  ...props
}: React.ComponentProps<typeof NextThemesProvider>) {
  const [queryClient] = useState(() => new QueryClient())

  // Capture unhandled promise rejections and window errors — these slip past
  // React's ErrorBoundary (e.g. async fetch failures, setTimeout exceptions).
  useEffect(() => {
    const onUnhandledRejection = (ev: PromiseRejectionEvent) => {
      const reason = ev.reason
      const err = reason instanceof Error ? reason : new Error(String(reason))
      Sentry.captureException(err, {
        tags: { source: "unhandledrejection" },
        extra: { reason: String(reason) },
      })
    }
    const onError = (ev: ErrorEvent) => {
      Sentry.captureException(ev.error ?? new Error(ev.message), {
        tags: { source: "window.onerror" },
        extra: { filename: ev.filename, lineno: ev.lineno, colno: ev.colno },
      })
    }
    window.addEventListener("unhandledrejection", onUnhandledRejection)
    window.addEventListener("error", onError)
    return () => {
      window.removeEventListener("unhandledrejection", onUnhandledRejection)
      window.removeEventListener("error", onError)
    }
  }, [])

  return (
    <QueryClientProvider client={queryClient}>
      <NextThemesProvider {...props}>
        <AuthProvider>{children}</AuthProvider>
      </NextThemesProvider>
    </QueryClientProvider>
  )
}
