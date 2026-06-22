import { Header } from "@/components/havilah/header"
import { WorkspaceChat } from "@/components/havilah/workspace-chat"
import { TodayRail } from "@/components/havilah/today-rail"
import { AuthGuard } from "@/components/havilah/auth-guard"

export default function Home() {
  return (
    <AuthGuard>
      <div className="min-h-screen flex flex-col bg-background">
        <Header />

        <main className="flex-1 mx-auto w-full max-w-7xl px-4 sm:px-6 lg:px-8 py-6">
          {/* Two-column work surface: conversation (left) + today rail (right) */}
          <div className="grid grid-cols-1 lg:grid-cols-[1fr_360px] gap-4 lg:gap-6">
            <WorkspaceChat />
            <div className="lg:block">
              <TodayRail />
            </div>
          </div>
        </main>

        <footer className="border-t border-border/60 bg-card/30">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-3">
            <div className="flex flex-col items-center justify-between gap-1 sm:flex-row">
              <div className="flex items-center gap-2">
                <span className="gold-gradient-text text-xs font-bold tracking-tight">Havilah OS</span>
                <span className="text-border">·</span>
                <span className="text-[11px] text-muted-foreground/60">AI Executive Operating System</span>
              </div>
              <div className="flex items-center gap-3 text-[11px] text-muted-foreground/50">
                <span>GPT-4o</span>
                <span>10 Agents</span>
                <span>v3.0</span>
              </div>
            </div>
          </div>
        </footer>
      </div>
    </AuthGuard>
  )
}
