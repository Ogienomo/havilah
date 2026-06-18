"use client"

import { Header } from "@/components/havilah/header"
import { HeroStats } from "@/components/havilah/hero-stats"
import { HermesCommand } from "@/components/havilah/hermes-command"
import { AgentGrid } from "@/components/havilah/agent-grid"
import { ApprovalQueue } from "@/components/havilah/approval-queue"
import { MemoryExplorer } from "@/components/havilah/memory-explorer"
import { ActivityTimeline } from "@/components/havilah/activity-timeline"
import { SystemArchitecture } from "@/components/havilah/system-architecture"
import { Separator } from "@/components/ui/separator"
import { AuthGuard } from "@/components/havilah/auth-guard"

export default function Home() {
  return (
    <AuthGuard>
    <div className="min-h-screen flex flex-col bg-background">
      {/* Header */}
      <Header />

      {/* Main Content */}
      <main className="flex-1 mx-auto w-full max-w-7xl px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        {/* Hero Stats */}
        <section aria-label="Key metrics">
          <HeroStats />
        </section>

        {/* Hermes Command Center - Star Feature */}
        <section aria-label="Hermes Command Center">
          <HermesCommand />
        </section>

        {/* Agent Status Grid */}
        <section aria-label="Agent Status">
          <AgentGrid />
        </section>

        {/* Approval Queue + Memory Explorer side by side on larger screens */}
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <section aria-label="Approval Queue">
            <ApprovalQueue />
          </section>
          <section aria-label="Memory Explorer">
            <MemoryExplorer />
          </section>
        </div>

        {/* Activity Timeline + System Architecture side by side on larger screens */}
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <section aria-label="Recent Activity">
            <ActivityTimeline />
          </section>
          <section aria-label="System Architecture">
            <SystemArchitecture />
          </section>
        </div>
      </main>

      {/* Footer */}
      <footer className="mt-auto border-t border-border bg-card/50 backdrop-blur-sm">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex flex-col items-center justify-between gap-2 sm:flex-row">
            <div className="flex items-center gap-2">
              <span className="gold-gradient-text text-sm font-bold">Havilah OS</span>
              <Separator orientation="vertical" className="h-4" />
              <span className="text-xs text-muted-foreground">AI Executive Operating System</span>
            </div>
            <div className="flex items-center gap-4 text-xs text-muted-foreground">
              <span>10 Agents Active</span>
              <span>155 API Endpoints</span>
              <span>v2.1.0</span>
            </div>
          </div>
        </div>
      </footer>
    </div>
    </AuthGuard>
  )
}
