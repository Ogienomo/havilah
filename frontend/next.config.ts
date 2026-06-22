import type { NextConfig } from "next";
import { withSentryConfig } from "@sentry/nextjs";

const nextConfig: NextConfig = {
  output: "standalone",
  typescript: {
    ignoreBuildErrors: true,
  },
  reactStrictMode: false,
};

// Sentry wrapper — no-op when SENTRY_DSN / NEXT_PUBLIC_SENTRY_DSN are unset
// (build still succeeds; telemetry simply isn't sent).
export default withSentryConfig(nextConfig, {
  // Only relevant if you have a Sentry auth token + org/project set.
  // For open-source builds without auth, this is safely skipped.
  silent: true,
  // Disable telemetry collection about the build itself
  disableClientWebpackPlugin: !process.env.NEXT_PUBLIC_SENTRY_DSN,
  disableServerWebpackPlugin: !process.env.SENTRY_DSN,
  org: process.env.SENTRY_ORG,
  project: process.env.SENTRY_PROJECT,
  // Tree-shake Sentry logger in production
  hideSourceMaps: true,
});
