"use client"

import { useEffect, useState, useCallback } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Skeleton } from "@/components/ui/skeleton"
import { Button } from "@/components/ui/button"
import { havilahApi, ActivityEvent, isApiConfigured, ApiError } from "@/lib/havilah-api"
import {
  Bot,
  ShieldCheck,
  Brain,
  Settings,
  Mail,
  FolderKanban,
  AlertCircle,
  RefreshCw,
  Bell,
  CheckCircle2,
  XCircle,
  Play,
  FileText,
  type LucideIcon,
} from "lucide-react"
import { motion } from "framer-motion"

// Map event_type → { icon, color, label }
const EVENT_TYPE_META: Record<string, { icon: LucideIcon; color: string; label: string }> = {
  // Approval events
  ApprovalRequested:   { icon: ShieldCheck, color: "#f59e0b", label: "Approval Requested" },
  ApprovalApproved:    { icon: CheckCircle2, color: "#10b981", label: "Approved" },
  ApprovalRejected:    { icon: XCircle, color: "#ef4444", label: "Rejected" },
  ApprovalExecuted:    { icon: Play, color: "#8b5cf6", label: "Executed" },
  ApprovalEscalated:   { icon: AlertCircle, color: "#f97316", label: "Escalated" },
  // Memory events
  MemoryCaptured:      { icon: Brain, color: "#06b6d4", label: "Memory Captured" },
  MemoryReinforced:    { icon: Brain, color: "#0891b2", label: "Memory Reinforced" },
  // Hermes events
  HermesRunStarted:    { icon: Bot, color: "#3b82f6", label: "Hermes Run Started" },
  HermesRunCompleted:  { icon: CheckCircle2, color: "#10b981", label: "Hermes Run Completed" },
  HermesRunFailed:     { icon: XCircle, color: "#ef4444", label: "Hermes Run Failed" },
  HermesStepDispatched:{ icon: Play, color: "#6366f1", label: "Step Dispatched" },
  HermesStepCompleted: { icon: CheckCircle2, color: "#22c55e", label: "Step Completed" },
  // Notifications
  NotificationCreated: { icon: Bell, color: "#a78bfa", label: "Notification" },
  // Project / Task
  ProjectCreated:      { icon: FolderKanban, color: "#ec4899", label: "Project Created" },
  TaskCreated:         { icon: FolderKanban, color: "#f43f5e", label: "Task Created" },
  TaskCompleted:       { icon: CheckCircle2, color: "#10b981", label: "Task Completed" },
  // Communication
  MessageSent:         { icon: Mail, color: "#0ea5e9", label: "Message Sent" },
  // Content / Writing
  ContentDrafted:      { icon: FileText, color: "#84cc16", label: "Content Drafted" },
  // Fallback
  _default:            { icon: Settings, color: "#64748b", label: "System Event" },
}

function getEventMeta(eventType: string) {
  return EVENT_TYPE_META[eventType] ?? EVENT_TYPE_META._default
}

// Format ISO date → "2m ago" / "1h ago" / "3d ago"
function timeAgo(iso: string): string {
  const d = new Date(iso)
  const now = Date.now()
  const diff = Math.max(0, now - d.getTime())
  const seconds = Math.floor(diff / 1000)
  if (seconds < 60) return `${seconds}s ago`
  const minutes = Math.floor(seconds / 60)
  if (minutes < 60) return `${minutes}m ago`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}h ago`
  const days = Math.floor(hours / 24)
  if (days < 7) return `${days}d ago`
  return d.toLocaleDateString()
}

const container = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: { staggerChildren: 0.06 },
  },
}

const itemAnim = {
  hidden: { opacity: 0, x: -10 },
  show: { opacity: 1, x: 0 },
}

type LoadState = "loading" | "live" | "error" | "empty"

export function ActivityTimeline() {
  const [events, setEvents] = useState<ActivityEvent[]>([])
  const [state, setState] = useState<LoadState>(isApiConfigured ? "loading" : "empty")
  const [errorMsg, setErrorMsg] = useState("")

  const load = useCallback(async () => {
    if (!isApiConfigured) {
      setState("empty")
      return
    }
    setState("loading")
    setErrorMsg("")
    try {
      const data = await havilahApi.listActivity(30)
      if (Array.isArray(data) && data.length > 0) {
        setEvents(data)
        setState("live")
      } else {
        setEvents([])
        setState("empty")
      }
    } catch (e: any) {
      setErrorMsg(e instanceof ApiError ? e.message : String(e))
      setState("error")
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])

  return (
    <Card className="border-border bg-card">
      <CardHeader>
        <CardTitle className="flex items-center justify-between text-foreground">
          <span className="flex items-center gap-2">
            <Settings className="h-5 w-5 text-havilah-gold" />
            Recent Activity
            {state === "live" && (
              <Badge variant="outline" className="border-emerald-500/30 text-emerald-500 text-[10px]">
                LIVE
              </Badge>
            )}
          </span>
          {state === "live" && (
            <Badge variant="outline" className="border-havilah-gold/30 text-havilah-gold text-xs">
              {events.length} events
            </Badge>
          )}
        </CardTitle>
      </CardHeader>
      <CardContent>
        {state === "loading" && (
          <div className="space-y-2">
            {Array.from({ length: 6 }).map((_, i) => (
              <Skeleton key={i} className="h-14 rounded-lg" />
            ))}
          </div>
        )}

        {state === "error" && (
          <div className="flex flex-col items-center justify-center py-8 gap-3 text-center">
            <AlertCircle className="h-8 w-8 text-red-500" />
            <p className="text-sm text-muted-foreground">Failed to load activity feed.</p>
            <p className="text-xs text-muted-foreground/70 max-w-md">{errorMsg}</p>
            <Button variant="outline" size="sm" onClick={load} className="mt-2">
              <RefreshCw className="h-3 w-3 mr-2" />
              Retry
            </Button>
          </div>
        )}

        {state === "empty" && (
          <div className="flex flex-col items-center justify-center py-8 gap-2 text-center">
            <Settings className="h-8 w-8 text-muted-foreground/40" />
            <p className="text-sm text-muted-foreground">No recent activity yet.</p>
            <p className="text-xs text-muted-foreground/70 max-w-sm">
              Activity will appear here as you submit Hermes instructions, capture memories,
              and approve actions.
            </p>
          </div>
        )}

        {state === "live" && (
          <ScrollArea className="max-h-96">
            <motion.div
              variants={container}
              initial="hidden"
              animate="show"
              className="relative"
            >
              {/* Timeline line */}
              <div className="absolute left-[15px] top-2 bottom-2 w-px bg-border" />

              <div className="space-y-1">
                {events.map((event, idx) => {
                  const meta = getEventMeta(event.event_type)
                  const Icon = meta.icon
                  const summary =
                    event.payload?.summary ??
                    event.payload?.title ??
                    event.payload?.message ??
                    event.event_type
                  const description =
                    event.payload?.description ??
                    event.payload?.detail ??
                    (event.payload?.action_type
                      ? `Action: ${event.payload.action_type}`
                      : `Actor: ${event.actor_type}`)

                  return (
                    <motion.div
                      key={`${event.aggregate_id}-${idx}`}
                      variants={itemAnim}
                      className="relative flex gap-3 px-1 py-2"
                    >
                      {/* Timeline dot */}
                      <div
                        className="relative z-10 flex h-[30px] w-[30px] shrink-0 items-center justify-center rounded-full border bg-card"
                        style={{ borderColor: `${meta.color}30` }}
                      >
                        <div
                          className="flex h-5 w-5 items-center justify-center rounded-full"
                          style={{ backgroundColor: `${meta.color}20`, color: meta.color }}
                        >
                          <Icon className="h-3.5 w-3.5" />
                        </div>
                      </div>

                      {/* Content */}
                      <div className="flex-1 space-y-0.5 pb-2">
                        <div className="flex items-start justify-between gap-2">
                          <p className="text-sm font-medium text-foreground">
                            {meta.label}
                          </p>
                          <span
                            className="shrink-0 text-[10px] text-muted-foreground whitespace-nowrap"
                            title={new Date(event.created_at).toLocaleString()}
                          >
                            {timeAgo(event.created_at)}
                          </span>
                        </div>
                        <p className="text-xs leading-relaxed text-muted-foreground">
                          <span className="text-foreground/80">{String(summary)}</span>
                          {description && description !== summary && (
                            <> — {String(description)}</>
                          )}
                        </p>
                      </div>
                    </motion.div>
                  )
                })}
              </div>
            </motion.div>
          </ScrollArea>
        )}
      </CardContent>
    </Card>
  )
}
