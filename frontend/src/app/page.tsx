"use client"

import { Header } from "@/components/havilah/header"
import { HeroStats } from "@/components/havilah/hero-stats"
import { HermesCommand } from "@/components/havilah/hermes-command"
import { AgentGrid } from "@/components/havilah/agent-grid"
import { ApprovalQueue } from "@/components/havilah/approval-queue"
import { MemoryExplorer } from "@/components/havilah/memory-explorer"
import { ActivityTimeline } from "@/components/havilah/activity-timeline"
import { SystemArchitecture } from "@/components/havilah/system-architecture"
import { AuthGuard } from "@/components/havilah/auth-guard"

export default function Home() {
  return (
    <AuthGuard>
      <div className="min-h-screen flex flex-col bg-background">
        <Header />

        <main className="flex-1 mx-auto w-full max-w-7xl px-4 sm:px-6 lg:px-8 py-8 space-y-10">

          {/* ── Stats row ──────────────────────────────────────────── */}
          <section aria-label="Key metrics">
            <HeroStats />
          </section>

          {/* ── Hermes — the star of the show ──────────────────────── */}
          <section aria-label="Hermes Command Center">
            <HermesCommand />
          </section>

          {/* ── Approval Queue + Memory side by side ───────────────── */}
          <section aria-label="Approvals and Memory">
            <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
              <ApprovalQueue />
              <MemoryExplorer />
            </div>
          </section>

          {/* ── Agents ─────────────────────────────────────────────── */}
          <section aria-label="Agent Status">
            <AgentGrid />
          </section>

          {/* ── Activity + Architecture ─────────────────────────────── */}
          <section aria-label="Activity and Architecture">
            <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
              <ActivityTimeline />
              <SystemArchitecture />
            </div>
          </section>

        </main>

        <footer className="border-t border-border/60 bg-card/30">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-4">
            <div className="flex flex-col items-center justify-between gap-2 sm:flex-row">
              <div className="flex items-center gap-2.5">
                <span className="gold-gradient-text text-sm font-bold tracking-tight">Havilah OS</span>
                <span className="text-border">·</span>
                <span className="text-xs text-muted-foreground/60">AI Executive Operating System</span>
              </div>
              <div className="flex items-center gap-4 text-xs text-muted-foreground/50">
                <span>10 Agents</span>
                <span>155 Endpoints</span>
                <span>v2.1.0</span>
              </div>
            </div>
          </div>
        </footer>
      </div>
    </AuthGuard>
  )
}
