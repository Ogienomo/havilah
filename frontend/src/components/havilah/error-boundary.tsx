"use client"

import { Component, ReactNode } from "react"
import { AlertCircle, RefreshCw } from "lucide-react"
import { Button } from "@/components/ui/button"

interface Props {
  children: ReactNode
  fallback?: ReactNode
}

interface State {
  hasError: boolean
  error: Error | null
}

/**
 * Error Boundary — catches unhandled render errors in the subtree
 * and shows a clean fallback instead of a frozen white screen.
 *
 * Also logs to console.error so Sentry (or similar) can pick it up
 * if/when it's wired in.
 */
export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    // Structured console log — Sentry can capture this automatically
    console.error("[Havilah ErrorBoundary]", {
      error: error.message,
      stack: error.stack,
      componentStack: errorInfo.componentStack,
      timestamp: new Date().toISOString(),
      url: typeof window !== "undefined" ? window.location.href : "SSR",
    })
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null })
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) return this.props.fallback
      return (
        <div className="flex min-h-[400px] flex-col items-center justify-center gap-4 p-8 text-center">
          <div className="flex h-14 w-14 items-center justify-center rounded-full bg-red-500/10">
            <AlertCircle className="h-7 w-7 text-red-500" />
          </div>
          <div className="space-y-1">
            <p className="text-base font-semibold text-foreground">Something went wrong</p>
            <p className="text-sm text-muted-foreground max-w-md">
              The dashboard hit an unexpected error. Try reloading — your session is preserved.
            </p>
          </div>
          {this.state.error && (
            <details className="max-w-lg w-full">
              <summary className="text-xs text-muted-foreground cursor-pointer hover:text-foreground">
                Show error details
              </summary>
              <pre className="mt-2 text-[11px] text-left bg-muted/50 rounded-lg p-3 overflow-auto max-h-48 font-mono text-muted-foreground">
                {this.state.error.message}
                {this.state.error.stack && `\n\n${this.state.error.stack}`}
              </pre>
            </details>
          )}
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={this.handleReset} className="h-9">
              <RefreshCw className="h-3.5 w-3.5 mr-1.5" />
              Try again
            </Button>
            <Button
              size="sm"
              onClick={() => window.location.reload()}
              className="h-9 bg-havilah-gold text-white hover:bg-havilah-gold-light"
            >
              Reload page
            </Button>
          </div>
        </div>
      )
    }
    return this.props.children
  }
}
