/**
 * Sentry client-side configuration.
 *
 * Auto-captures:
 *  - Unhandled promise rejections
 *  - Window.onerror events
 *  - React component errors (via ErrorBoundary → console.error forwarding)
 *
 * DSN is sourced from NEXT_PUBLIC_SENTRY_DSN. If absent, Sentry is a no-op
 * (safe for local dev / preview branches without secrets).
 */
import * as Sentry from "@sentry/nextjs"

const SENTRY_DSN = process.env.NEXT_PUBLIC_SENTRY_DSN

if (SENTRY_DSN) {
  Sentry.init({
    dsn: SENTRY_DSN,
    tracesSampleRate: Number(process.env.NEXT_PUBLIC_SENTRY_TRACES_SAMPLE_RATE ?? 0.1),
    profilesSampleRate: 0,
    environment: process.env.NODE_ENV,
    // Strip PII
    sendDefaultPii: false,
    // Replay disabled to keep bundle light & avoid capturing user input
    replaysSessionSampleRate: 0,
    replaysOnErrorSampleRate: 0.1,
    // Ignore noisy expected errors
    ignoreErrors: [
      "ResizeObserver loop limit exceeded",
      "Network request failed",
      "AbortError",
      // Browser extensions
      "top.GLOBALS",
      "canvas.contentDocument",
    ],
    denyUrls: [
      // Chrome / Firefox extensions
      /extensions\//i,
      /^chrome:\/\//i,
      /^moz-extension:\/\//i,
    ],
  })
}
