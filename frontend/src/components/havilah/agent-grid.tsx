"use client"

import { useEffect, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { agents as mockAgents } from "./mock-data"
import { motion } from "framer-motion"
import { havilahApi, HermesAgent, isApiConfigured, ApiError } from "@/lib/havilah-api"
import { Skeleton } from "@/components/ui/skeleton"
import { AlertCircle, RefreshCw } from "lucide-react"
import { Button } from "@/components/ui/button"

const container = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: { staggerChildren: 0.05 },
  },
}

const item = {
  hidden: { opacity: 0, scale: 0.95 },
  show: { opacity: 1, scale: 1 },
}

// Map backend agent_type → color + icon (mirrors mock-data.ts)
const AGENT_VISUALS: Record<string, { color: string; icon: typeof mockAgents[0]["icon"] }> = {
  planner:   { color: "#60a5fa", icon: mockAgents.find(a => a.id === "planner")!.icon },
  executive: { color: "#d4a853", icon: mockAgents.find(a => a.id === "executive")!.icon },
  research:  { color: "#34d399", icon: mockAgents.find(a => a.id === "research")!.icon },
  writing:   { color: "#f472b6", icon: mockAgents.find(a => a.id === "writing")!.icon },
  meeting:   { color: "#a78bfa", icon: mockAgents.find(a => a.id === "meeting")!.icon },
  reviewer:  { color: "#fb7185", icon: mockAgents.find(a => a.id === "reviewer")!.icon },
  critic:    { color: "#fb923c", icon: mockAgents.find(a => a.id === "critic")!.icon },
  memory:    { color: "#22d3ee", icon: mockAgents.find(a => a.id === "memory")!.icon },
  learning:  { color: "#4ade80", icon: mockAgents.find(a => a.id === "learning")!.icon },
  approval:  { color: "#facc15", icon: mockAgents.find(a => a.id === "approval")!.icon },
}

type LoadState = "loading" | "live" | "error" | "mock"

export function AgentGrid() {
  const [liveAgents, setLiveAgents] = useState<HermesAgent[]>([])
  const [state, setState] = useState<LoadState>(isApiConfigured ? "loading" : "mock")
  const [errorMsg, setErrorMsg] = useState<string>("")

  const loadAgents = async () => {
    if (!isApiConfigured) {
      setState("mock")
      return
    }
    setState("loading")
    setErrorMsg("")
    try {
      const data = await havilahApi.listAgents()
      if (Array.isArray(data) && data.length > 0) {
        setLiveAgents(data)
        setState("live")
      } else {
        // Empty array — fall back to mock
        setState("mock")
      }
    } catch (e: any) {
      setErrorMsg(e instanceof ApiError ? e.message : String(e))
      setState("error")
    }
  }

  useEffect(() => {
    loadAgents()
  }, [])

  const displayAgents =
    state === "live"
      ? liveAgents.map(a => {
          const visual = AGENT_VISUALS[a.agent_type] ?? AGENT_VISUALS.planner
          return {
            id: a.name,
            name: a.display_name?.replace(" Agent", "") || a.name,
            icon: visual.icon,
            color: visual.color,
            status: a.is_active ? "active" : "idle",
            description: a.description,
            capabilities: a.capabilities ?? [],
          }
        })
      : mockAgents

  return (
    <Card className="border-border bg-card">
      <CardHeader>
        <CardTitle className="flex items-center justify-between text-foreground">
          <span className="flex items-center gap-2">
            Agent Status Grid
            {state === "live" && (
              <Badge variant="outline" className="border-emerald-500/30 text-emerald-500 text-[10px]">
                LIVE
              </Badge>
            )}
            {state === "mock" && (
              <Badge variant="outline" className="border-amber-500/30 text-amber-500 text-[10px]">
                DEMO DATA
              </Badge>
            )}
          </span>
          <Badge variant="outline" className="border-havilah-gold/30 text-havilah-gold">
            {displayAgents.length} Agents
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent>
        {state === "loading" && (
          <div className="grid grid-cols-2 gap-3 sm:gap-4 md:grid-cols-3 lg:grid-cols-5">
            {Array.from({ length: 10 }).map((_, i) => (
              <Skeleton key={i} className="h-32 rounded-lg" />
            ))}
          </div>
        )}

        {state === "error" && (
          <div className="flex flex-col items-center justify-center py-8 gap-3 text-center">
            <AlertCircle className="h-8 w-8 text-red-500" />
            <p className="text-sm text-muted-foreground">
              Failed to load agents from backend.
            </p>
            <p className="text-xs text-muted-foreground/70 max-w-md">{errorMsg}</p>
            <Button
              variant="outline"
              size="sm"
              onClick={loadAgents}
              className="mt-2"
            >
              <RefreshCw className="h-3 w-3 mr-2" />
              Retry
            </Button>
          </div>
        )}

        {(state === "live" || state === "mock") && (
          <motion.div
            variants={container}
            initial="hidden"
            animate="show"
            className="grid grid-cols-2 gap-3 sm:gap-4 md:grid-cols-3 lg:grid-cols-5"
          >
            {displayAgents.map((agent) => {
              const Icon = agent.icon
              return (
                <motion.div
                  key={agent.id}
                  variants={item}
                  className="group rounded-lg border border-border bg-card p-3 sm:p-4 transition-all duration-300 hover:border-havilah-gold/30 hover:shadow-md hover:shadow-havilah-gold/5"
                >
                  <div className="flex flex-col items-center text-center">
                    {/* Icon with status indicator */}
                    <div className="relative mb-3">
                      <div
                        className="flex h-12 w-12 items-center justify-center rounded-xl transition-transform duration-300 group-hover:scale-110"
                        style={{ backgroundColor: `${agent.color}15` }}
                      >
                        <Icon className="h-6 w-6" style={{ color: agent.color }} />
                      </div>
                      <span
                        className={`absolute -right-0.5 -top-0.5 flex h-3.5 w-3.5 items-center justify-center rounded-full border-2 border-card ${
                          agent.status === "active"
                            ? "bg-emerald-500"
                            : agent.status === "busy"
                            ? "bg-amber-500"
                            : "bg-slate-400 dark:bg-slate-500"
                        }`}
                      >
                        {agent.status === "active" && (
                          <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" />
                        )}
                        {agent.status === "busy" && (
                          <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-amber-400 opacity-75" />
                        )}
                      </span>
                    </div>

                    <h3 className="mb-1 text-sm font-semibold text-foreground">{agent.name}</h3>

                    <Badge
                      variant="outline"
                      className={`mb-2 text-[10px] ${
                        agent.status === "active"
                          ? "border-emerald-500/30 text-emerald-500"
                          : agent.status === "busy"
                          ? "border-amber-500/30 text-amber-500"
                          : "border-slate-400/30 text-slate-400 dark:text-slate-500"
                      }`}
                    >
                      {agent.status}
                    </Badge>

                    <p className="mb-2 text-[10px] leading-tight text-muted-foreground line-clamp-2">
                      {agent.description}
                    </p>

                    <div className="flex flex-wrap justify-center gap-0.5">
                      {agent.capabilities.slice(0, 2).map((cap) => (
                        <span
                          key={cap}
                          className="rounded-full bg-muted px-1.5 py-0.5 text-[9px] text-muted-foreground"
                        >
                          {cap}
                        </span>
                      ))}
                      {agent.capabilities.length > 2 && (
                        <span className="rounded-full bg-muted px-1.5 py-0.5 text-[9px] text-muted-foreground">
                          +{agent.capabilities.length - 2}
                        </span>
                      )}
                    </div>
                  </div>
                </motion.div>
              )
            })}
          </motion.div>
        )}
      </CardContent>
    </Card>
  )
}
