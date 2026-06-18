"use client"

import { useEffect, useState, useCallback } from "react"
import { Card, CardContent } from "@/components/ui/card"
import { Users, ShieldCheck, Brain, CheckCircle2, Activity, Zap } from "lucide-react"
import { motion } from "framer-motion"
import { havilahApi, isApiConfigured, ApiError } from "@/lib/havilah-api"
import { Skeleton } from "@/components/ui/skeleton"
import { AlertCircle, RefreshCw } from "lucide-react"
import { Button } from "@/components/ui/button"

interface StatItem {
  label: string
  value: string | number
  icon: React.ReactNode
  dotColor: string
  change: string
}

const container = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: { staggerChildren: 0.1 },
  },
}

const item = {
  hidden: { opacity: 0, y: 20 },
  show: { opacity: 1, y: 0 },
}

type LoadState = "loading" | "live" | "error" | "demo"

export function HeroStats() {
  const [stats, setStats] = useState<StatItem[]>([])
  const [state, setState] = useState<LoadState>(isApiConfigured ? "loading" : "demo")
  const [errorMsg, setErrorMsg] = useState("")

  const load = useCallback(async () => {
    if (!isApiConfigured) {
      setStats(getDemoStats())
      setState("demo")
      return
    }
    setState("loading")
    setErrorMsg("")
    try {
      // Fire all 3 requests in parallel for speed
      const [healthResp, runsResp, eventsResp] = await Promise.allSettled([
        havilahApi.health(),
        havilahApi.listRuns(),
        havilahApi.listActivity(50),
      ])

      // Health is critical — if it fails, show error
      if (healthResp.status !== "fulfilled") {
        const err = healthResp.reason
        setErrorMsg(err instanceof ApiError ? err.message : String(err))
        setState("error")
        return
      }

      const health = healthResp.value
      const agentsRegistered = health.checks?.agents_registered ?? 10
      const llmConnected = health.checks?.llm_connected ?? false
      const model = health.checks?.model ?? "gpt-4o"

      // Active runs (currently always 0 because Hermes completes synchronously)
      const activeRuns = runsResp.status === "fulfilled" ? runsResp.value.length : 0

      // Pending approvals = events of type ApprovalRequested
      let pendingApprovals = 0
      let recentEventsCount = 0
      if (eventsResp.status === "fulfilled") {
        const events = eventsResp.value
        recentEventsCount = events.length
        pendingApprovals = events.filter(
          (e) => e.event_type === "ApprovalRequested"
        ).length
      }

      setStats([
        {
          label: "Active Agents",
          value: agentsRegistered,
          icon: <Users className="h-5 w-5" />,
          dotColor: "bg-emerald-500",
          change: llmConnected ? `${model} online` : "LLM offline",
        },
        {
          label: "Pending Approvals",
          value: pendingApprovals,
          icon: <ShieldCheck className="h-5 w-5" />,
          dotColor: pendingApprovals > 0 ? "bg-amber-500" : "bg-emerald-500",
          change: pendingApprovals > 0 ? "Awaiting review" : "All clear",
        },
        {
          label: "Active Hermes Runs",
          value: activeRuns,
          icon: <Activity className="h-5 w-5" />,
          dotColor: activeRuns > 0 ? "bg-sky-500" : "bg-slate-400",
          change: activeRuns > 0 ? "In progress" : "Idle",
        },
        {
          label: "Recent Events",
          value: recentEventsCount,
          icon: <Zap className="h-5 w-5" />,
          dotColor: "bg-violet-500",
          change: "Last 50 events",
        },
      ])
      setState("live")
    } catch (e: any) {
      setErrorMsg(e instanceof ApiError ? e.message : String(e))
      setState("error")
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])

  // Show skeleton during loading
  if (state === "loading") {
    return (
      <div className="grid grid-cols-2 gap-3 sm:gap-4 lg:grid-cols-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <Skeleton key={i} className="h-28 rounded-xl" />
        ))}
      </div>
    )
  }

  // Show error state
  if (state === "error") {
    return (
      <Card className="border-red-500/30 bg-card">
        <CardContent className="p-6 flex flex-col items-center gap-3 text-center">
          <AlertCircle className="h-8 w-8 text-red-500" />
          <p className="text-sm text-muted-foreground">Failed to load dashboard stats.</p>
          <p className="text-xs text-muted-foreground/70 max-w-md">{errorMsg}</p>
          <Button variant="outline" size="sm" onClick={load} className="mt-2">
            <RefreshCw className="h-3 w-3 mr-2" />
            Retry
          </Button>
        </CardContent>
      </Card>
    )
  }

  return (
    <motion.div
      variants={container}
      initial="hidden"
      animate="show"
      className="grid grid-cols-2 gap-4 sm:gap-5 lg:grid-cols-4"
    >
      {stats.map((stat) => (
        <motion.div key={stat.label} variants={item}>
          <Card className="group relative overflow-hidden border-border bg-card transition-all duration-300 hover:border-havilah-gold/30 hover:shadow-lg hover:shadow-havilah-gold/5">
            <CardContent className="p-5 sm:p-6">
              <div className="flex items-start justify-between gap-3">
                <div className="flex flex-col gap-2 min-w-0">
                  <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
                    {stat.label}
                  </p>
                  <p className="text-3xl font-bold tracking-tight text-foreground sm:text-4xl">
                    {stat.value}
                  </p>
                  <div className="flex items-center gap-1.5">
                    <span className={`h-1.5 w-1.5 rounded-full ${stat.dotColor}`} />
                    <span className="text-xs text-muted-foreground truncate">{stat.change}</span>
                  </div>
                </div>
                <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-lg bg-havilah-gold/10 text-havilah-gold transition-colors group-hover:bg-havilah-gold/20 sm:h-12 sm:w-12">
                  {stat.icon}
                </div>
              </div>
              {/* Subtle gold accent line at bottom */}
              <div className="absolute bottom-0 left-0 h-0.5 w-0 bg-gradient-to-r from-havilah-gold to-havilah-gold-light transition-all duration-500 group-hover:w-full" />
            </CardContent>
          </Card>
        </motion.div>
      ))}
    </motion.div>
  )
}

function getDemoStats(): StatItem[] {
  return [
    {
      label: "Active Agents",
      value: "—",
      icon: <Users className="h-5 w-5" />,
      dotColor: "bg-slate-400",
      change: "Demo mode",
    },
    {
      label: "Pending Approvals",
      value: "—",
      icon: <ShieldCheck className="h-5 w-5" />,
      dotColor: "bg-slate-400",
      change: "Demo mode",
    },
    {
      label: "Active Hermes Runs",
      value: "—",
      icon: <Activity className="h-5 w-5" />,
      dotColor: "bg-slate-400",
      change: "Demo mode",
    },
    {
      label: "Recent Events",
      value: "—",
      icon: <Zap className="h-5 w-5" />,
      dotColor: "bg-slate-400",
      change: "Demo mode",
    },
  ]
}
