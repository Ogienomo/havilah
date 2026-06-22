"use client"

import { useEffect, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { motion } from "framer-motion"
import { havilahApi, HermesAgent, isApiConfigured, ApiError } from "@/lib/havilah-api"
import { Skeleton } from "@/components/ui/skeleton"
import {
  AlertCircle,
  RefreshCw,
  LayoutList,
  Crown,
  Search,
  PenTool,
  Users,
  Eye,
  ShieldAlert,
  Brain,
  GraduationCap,
  ShieldCheck,
  type LucideIcon,
} from "lucide-react"
import { Button } from "@/components/ui/button"

// Inline agent visual registry — no mock-data dependency
const AGENT_VISUALS: Record<string, { color: string; icon: LucideIcon }> = {
  planner:   { color: "#2563eb", icon: LayoutList },
  executive: { color: "#b8821e", icon: Crown },
  research:  { color: "#059669", icon: Search },
  writing:   { color: "#db2777", icon: PenTool },
  meeting:   { color: "#7c3aed", icon: Users },
  reviewer:  { color: "#0d9488", icon: Eye },
  critic:    { color: "#ea580c", icon: ShieldAlert },
  memory:    { color: "#4f46e5", icon: Brain },
  learning:  { color: "#16a34a", icon: GraduationCap },
  approval:  { color: "#ca8a04", icon: ShieldCheck },
}

function getAgentVisual(agentType: string): { color: string; icon: LucideIcon } {
  return AGENT_VISUALS[agentType] ?? { color: "#64748b", icon: LayoutList }
}

const container = {
  hidden: { opacity: 0 },
  show: { opacity: 1, transition: { staggerChildren: 0.04 } },
}
const item = { hidden: { opacity: 0, scale: 0.96 }, show: { opacity: 1, scale: 1 } }

type LoadState = "loading" | "live" | "error" | "empty"

export function AgentGrid() {
  const [liveAgents, setLiveAgents] = useState<HermesAgent[]>([])
  const [state, setState] = useState<LoadState>(isApiConfigured ? "loading" : "empty")
  const [errorMsg, setErrorMsg] = useState<string>("")

  const loadAgents = async () => {
    if (!isApiConfigured) { setState("empty"); return }
    setState("loading")
    setErrorMsg("")
    try {
      const data = await havilahApi.listAgents()
      if (Array.isArray(data) && data.length > 0) {
        setLiveAgents(data)
        setState("live")
      } else {
        setState("empty")
      }
    } catch (e: any) {
      setErrorMsg(e instanceof ApiError ? e.message : String(e))
      setState("error")
    }
  }

  useEffect(() => { loadAgents() }, [])

  const displayAgents = liveAgents.map(a => {
    const visual = getAgentVisual(a.agent_type)
    return {
      id: a.name,
      name: a.display_name?.replace(" Agent", "") || a.name,
      icon: visual.icon,
      color: visual.color,
      isActive: a.is_active,
      description: a.description,
      capabilities: a.capabilities ?? [],
    }
  })

  return (
    <Card className="border-border bg-card shadow-sm">
      <CardHeader className="pb-4">
        <CardTitle className="flex items-center justify-between text-foreground">
          <span className="flex items-center gap-2 text-base font-semibold">
            Agent Roster
            {state === "live" && (
              <Badge variant="outline" className="border-emerald-500/30 text-emerald-600 text-[10px] font-medium">
                LIVE
              </Badge>
            )}
          </span>
          <Badge variant="outline" className="border-border text-muted-foreground text-xs font-medium">
            {displayAgents.length} Agents
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent>
        {state === "loading" && (
          <div className="grid grid-cols-2 gap-3 sm:gap-4 md:grid-cols-3 lg:grid-cols-5">
            {Array.from({ length: 10 }).map((_, i) => (
              <Skeleton key={i} className="h-36 rounded-lg" />
            ))}
          </div>
        )}

        {state === "error" && (
          <div className="flex flex-col items-center justify-center py-10 gap-3 text-center">
            <AlertCircle className="h-8 w-8 text-red-500" />
            <p className="text-sm font-medium text-foreground">Failed to load agents</p>
            <p className="text-xs text-muted-foreground max-w-md">{errorMsg}</p>
            <Button variant="outline" size="sm" onClick={loadAgents} className="mt-1 h-8">
              <RefreshCw className="h-3 w-3 mr-1.5" />
              Retry
            </Button>
          </div>
        )}

        {state === "empty" && (
          <div className="flex flex-col items-center justify-center py-10 gap-2 text-center">
            <LayoutList className="h-8 w-8 text-muted-foreground/40" />
            <p className="text-sm font-medium text-foreground">No agents registered</p>
            <p className="text-xs text-muted-foreground max-w-sm">
              The backend reported 0 agents. Check that the Hermes agent registry is initialized.
            </p>
          </div>
        )}

        {state === "live" && (
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
                  className="group rounded-lg border border-border bg-card p-4 transition-all duration-200 hover:border-havilah-gold/30 hover:shadow-md hover:shadow-havilah-gold/5"
                >
                  <div className="flex flex-col items-center text-center">
                    {/* Icon with status indicator */}
                    <div className="relative mb-3">
                      <div
                        className="flex h-12 w-12 items-center justify-center rounded-xl transition-transform duration-200 group-hover:scale-105"
                        style={{ backgroundColor: `${agent.color}12` }}
                      >
                        <Icon className="h-5 w-5" style={{ color: agent.color }} />
                      </div>
                      {agent.isActive && (
                        <span
                          className="absolute -right-0.5 -top-0.5 flex h-3 w-3 items-center justify-center rounded-full border-2 border-card bg-emerald-500"
                          title="Active"
                        >
                          <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-60" />
                        </span>
                      )}
                    </div>

                    <h3 className="mb-1 text-sm font-semibold text-foreground leading-tight">
                      {agent.name}
                    </h3>

                    <p className="text-[11px] leading-snug text-muted-foreground line-clamp-2">
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
