/**
 * Sentry server-side configuration (Node runtime).
 * Captures unhandled rejections / exceptions in API routes & server components.
 */
import * as Sentry from "@sentry/nextjs"

const SENTRY_DSN = process.env.SENTRY_DSN

if (SENTRY_DSN) {
  Sentry.init({
    dsn: SENTRY_DSN,
    tracesSampleRate: Number(process.env.SENTRY_TRACES_SAMPLE_RATE ?? 0.1),
    profilesSampleRate: 0,
    environment: process.env.NODE_ENV,
    sendDefaultPii: false,
  })
}
