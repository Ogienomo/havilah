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
  executive: { color: "#b8821e", icon: mockAgents.find(a => a.id === "executive")!.icon },
  research:  { color: "#34d399", icon: mockAgents.find(a => a.id === "research")!.icon },
  writing:   { color: "#f472b6", icon: mockAgents.find(a => a.id === "writing")!.icon },
  meeting:   { color: "#a78bfa", icon: mockAgents.find(a => a.id === "meeting")!.icon },
  reviewer:  { color: "#2dd4bf", icon: mockAgents.find(a => a.id === "reviewer")!.icon },
  critic:    { color: "#fb923c", icon: mockAgents.find(a => a.id === "critic")!.icon },
  memory:    { color: "#818cf8", icon: mockAgents.find(a => a.id === "memory")!.icon },
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
            Agent Roster
          </span>
          <Badge variant="outline" className="border-havilah-gold/30 text-havilah-gold text-[10px]">
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
                    {/* Icon with status dot (only shown when active or busy) */}
                    <div className="relative mb-3">
                      <div
                        className="flex h-11 w-11 items-center justify-center rounded-xl transition-transform duration-300 group-hover:scale-105"
                        style={{ backgroundColor: `${agent.color}12` }}
                      >
                        <Icon className="h-5 w-5" style={{ color: agent.color }} />
                      </div>
                      {(agent.status === "active" || agent.status === "busy") && (
                        <span
                          className={`absolute -right-0.5 -top-0.5 flex h-3 w-3 items-center justify-center rounded-full border-2 border-card ${
                            agent.status === "active" ? "bg-emerald-500" : "bg-amber-500"
                          }`}
                        >
                          <span className={`absolute inline-flex h-full w-full animate-ping rounded-full opacity-60 ${
                            agent.status === "active" ? "bg-emerald-400" : "bg-amber-400"
                          }`} />
                        </span>
                      )}
                    </div>

                    <h3 className="mb-0.5 text-[13px] font-semibold text-foreground leading-tight">{agent.name}</h3>

                    {agent.status === "busy" && (
                      <Badge variant="outline" className="mb-1.5 text-[9px] border-amber-500/30 text-amber-600">
                        Working
                      </Badge>
                    )}

                    <p className="text-[10px] leading-tight text-muted-foreground line-clamp-2 mt-0.5">
                      {agent.description}
                    </p>
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
