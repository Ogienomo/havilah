"use client"

import { useState, useEffect, useCallback } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { ScrollArea } from "@/components/ui/scroll-area"
import {
  havilahApi,
  ActivityEvent,
  isApiConfigured,
  ApiError,
} from "@/lib/havilah-api"
import {
  CheckCircle2,
  XCircle,
  Clock,
  AlertCircle,
  RefreshCw,
  ChevronRight,
  Search,
  Zap,
  ShieldCheck,
  Brain,
  Bot,
  Bell,
  FolderKanban,
  Mail,
  FileText,
  Settings,
  Play,
  type LucideIcon,
} from "lucide-react"

const EVENT_META: Record<string, { icon: LucideIcon; color: string; label: string }> = {
  ApprovalRequested:   { icon: ShieldCheck,   color: "#f59e0b", label: "Approval needed" },
  ApprovalApproved:    { icon: CheckCircle2,  color: "#10b981", label: "Approved" },
  ApprovalRejected:    { icon: XCircle,       color: "#ef4444", label: "Rejected" },
  ApprovalExecuted:    { icon: Play,          color: "#8b5cf6", label: "Executed" },
  MemoryCaptured:      { icon: Brain,         color: "#06b6d4", label: "Memory saved" },
  HermesRunStarted:    { icon: Bot,           color: "#3b82f6", label: "Run started" },
  HermesRunCompleted:  { icon: CheckCircle2,  color: "#10b981", label: "Completed" },
  HermesRunFailed:     { icon: XCircle,       color: "#ef4444", label: "Failed" },
  NotificationCreated: { icon: Bell,          color: "#a78bfa", label: "Notification" },
  ProjectCreated:      { icon: FolderKanban,  color: "#ec4899", label: "Project" },
  TaskCreated:         { icon: FolderKanban,  color: "#f43f5e", label: "Task" },
  MessageSent:         { icon: Mail,          color: "#0ea5e9", label: "Message" },
  ContentDrafted:      { icon: FileText,      color: "#84cc16", label: "Drafted" },
  _default:            { icon: Settings,      color: "#64748b", label: "Event" },
}

function getMeta(t: string) { return EVENT_META[t] ?? EVENT_META._default }

function timeAgo(iso: string): string {
  const diff = Math.max(0, Date.now() - new Date(iso).getTime())
  const s = Math.floor(diff / 1000)
  if (s < 60) return `${s}s`
  const m = Math.floor(s / 60)
  if (m < 60) return `${m}m`
  const h = Math.floor(m / 60)
  if (h < 24) return `${h}h`
  return `${Math.floor(h / 24)}d`
}

type Tab = "today" | "approvals" | "memory"

export function TodayRail() {
  const [tab, setTab] = useState<Tab>("today")
  const [events, setEvents] = useState<ActivityEvent[]>([])
  const [pendingApprovals, setPendingApprovals] = useState<ActivityEvent[]>([])
  const [loading, setLoading] = useState(false)
  const [memoryQuery, setMemoryQuery] = useState("")
  const [memoryResults, setMemoryResults] = useState<any[]>([])
  const [searching, setSearching] = useState(false)

  const load = useCallback(async () => {
    if (!isApiConfigured) return
    setLoading(true)
    try {
      const acts = await havilahApi.listActivity(20)
      setEvents(acts)
      const pending = acts.filter((e) => e.event_type === "ApprovalRequested")
      // Dedupe by aggregate_id
      const seen = new Set<string>()
      const deduped = pending.filter((e) => {
        if (seen.has(e.aggregate_id)) return false
        seen.add(e.aggregate_id)
        return true
      })
      setPendingApprovals(deduped)
      // Auto-switch to approvals tab if there are pending ones and user hasn't searched
      if (deduped.length > 0 && tab === "today") {
        setTab("approvals")
      }
    } catch {
      // silent
    } finally {
      setLoading(false)
    }
  }, [tab])

  useEffect(() => { load() }, [load])

  // Debounced memory search
  useEffect(() => {
    if (!memoryQuery.trim()) {
      setMemoryResults([])
      return
    }
    setSearching(true)
    const t = setTimeout(async () => {
      try {
        const r = await havilahApi.searchMemory(memoryQuery.trim(), 10)
        setMemoryResults(r)
      } catch {
        setMemoryResults([])
      } finally {
        setSearching(false)
      }
    }, 350)
    return () => clearTimeout(t)
  }, [memoryQuery])

  return (
    <Card className="border-border bg-card shadow-sm h-[calc(100vh-12rem)] min-h-[600px] flex flex-col">
      <CardHeader className="pb-3 border-b border-border/60 shrink-0">
        <div className="flex items-center gap-1">
          <TabButton active={tab === "today"} onClick={() => setTab("today")} icon={Zap} label="Today" count={events.length} />
          <TabButton
            active={tab === "approvals"}
            onClick={() => setTab("approvals")}
            icon={ShieldCheck}
            label="Approvals"
            count={pendingApprovals.length}
            highlight={pendingApprovals.length > 0}
          />
          <TabButton active={tab === "memory"} onClick={() => setTab("memory")} icon={Brain} label="Memory" />
        </div>
      </CardHeader>

      <CardContent className="flex-1 overflow-hidden p-0">
        {tab === "today" && (
          <TodayFeed events={events} loading={loading} onRefresh={load} />
        )}
        {tab === "approvals" && (
          <ApprovalsList items={pendingApprovals} loading={loading} onRefresh={load} />
        )}
        {tab === "memory" && (
          <MemoryPanel
            query={memoryQuery}
            setQuery={setMemoryQuery}
            results={memoryResults}
            searching={searching}
          />
        )}
      </CardContent>
    </Card>
  )
}

function TabButton({
  active,
  onClick,
  icon: Icon,
  label,
  count,
  highlight,
}: {
  active: boolean
  onClick: () => void
  icon: LucideIcon
  label: string
  count?: number
  highlight?: boolean
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-colors flex-1 justify-center ${
        active
          ? "bg-havilah-gold/15 text-havilah-gold"
          : "text-muted-foreground hover:bg-muted/50 hover:text-foreground"
      }`}
    >
      <Icon className="h-3.5 w-3.5" />
      {label}
      {count != null && count > 0 && (
        <span className={`rounded-full px-1.5 py-0.5 text-[9px] font-mono ${
          highlight ? "bg-amber-500/20 text-amber-600" : "bg-muted text-muted-foreground"
        }`}>
          {count}
        </span>
      )}
    </button>
  )
}

// ─── Today feed ───────────────────────────────────────────────────────
function TodayFeed({ events, loading, onRefresh }: { events: ActivityEvent[]; loading: boolean; onRefresh: () => void }) {
  if (loading && events.length === 0) {
    return (
      <div className="p-4 space-y-2">
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="h-12 rounded-md bg-muted/30 animate-pulse" />
        ))}
      </div>
    )
  }

  if (events.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full gap-2 text-center p-6">
        <Zap className="h-8 w-8 text-muted-foreground/30" />
        <p className="text-sm text-muted-foreground">No activity yet today.</p>
        <p className="text-xs text-muted-foreground/70 max-w-xs">
          Submit a request to Hermes and your activity will appear here.
        </p>
      </div>
    )
  }

  return (
    <ScrollArea className="h-full">
      <div className="relative p-3 pr-2">
        <div className="absolute left-[18px] top-4 bottom-4 w-px bg-border/60" />
        <div className="space-y-1">
          {events.map((event, idx) => {
            const meta = getMeta(event.event_type)
            const Icon = meta.icon
            const summary =
              event.payload?.summary ??
              event.payload?.title ??
              event.payload?.message ??
              event.event_type
            return (
              <div
                key={`${event.aggregate_id}-${idx}`}
                className="relative flex gap-2.5 px-1 py-2 rounded-md hover:bg-muted/30 transition-colors"
              >
                <div
                  className="relative z-10 flex h-6 w-6 shrink-0 items-center justify-center rounded-full border bg-card"
                  style={{ borderColor: `${meta.color}40` }}
                >
                  <Icon className="h-3 w-3" style={{ color: meta.color }} />
                </div>
                <div className="flex-1 min-w-0 pt-0.5">
                  <div className="flex items-center gap-2">
                    <p className="text-xs font-medium text-foreground truncate">{meta.label}</p>
                    <span className="text-[10px] text-muted-foreground/60 ml-auto shrink-0" title={new Date(event.created_at).toLocaleString()}>
                      {timeAgo(event.created_at)}
                    </span>
                  </div>
                  <p className="text-xs text-muted-foreground/80 truncate mt-0.5">
                    {String(summary)}
                  </p>
                </div>
              </div>
            )
          })}
        </div>
        <div className="pt-2 px-1">
          <Button variant="ghost" size="sm" onClick={onRefresh} className="w-full h-7 text-xs text-muted-foreground">
            <RefreshCw className="h-3 w-3 mr-1.5" />
            Refresh
          </Button>
        </div>
      </div>
    </ScrollArea>
  )
}

// ─── Approvals list ───────────────────────────────────────────────────
function ApprovalsList({ items, loading, onRefresh }: { items: ActivityEvent[]; loading: boolean; onRefresh: () => void }) {
  const [acting, setActing] = useState<string | null>(null)

  const handleAct = async (id: string, approve: boolean) => {
    setActing(id)
    try {
      if (approve) {
        await havilahApi.approveApproval(id, "Approved via dashboard")
      } else {
        await havilahApi.rejectApproval(id, "Rejected via dashboard")
      }
      // Remove from list optimistically
      onRefresh()
    } catch (e: any) {
      // ignore — many of these are old/stale
      onRefresh()
    } finally {
      setActing(null)
    }
  }

  if (loading && items.length === 0) {
    return <div className="p-4 space-y-2">{Array.from({ length: 3 }).map((_, i) => <div key={i} className="h-20 rounded-md bg-muted/30 animate-pulse" />)}</div>
  }

  if (items.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full gap-2 text-center p-6">
        <CheckCircle2 className="h-8 w-8 text-emerald-500" />
        <p className="text-sm font-medium text-foreground">All caught up</p>
        <p className="text-xs text-muted-foreground/70 max-w-xs">
          No pending approvals. New requests appear here when Hermes needs your sign-off.
        </p>
      </div>
    )
  }

  return (
    <ScrollArea className="h-full">
      <div className="p-3 space-y-2">
        {items.map((item) => {
          const summary = item.payload?.summary ?? "Unknown action"
          const actionType = item.payload?.action_type ?? "administrative"
          const risk = item.payload?.risk_level
          return (
            <div
              key={item.aggregate_id}
              className="rounded-lg border border-border/70 bg-background p-3 space-y-2"
            >
              <div className="flex items-center gap-2">
                <Badge variant="outline" className="text-[9px] border-amber-500/30 text-amber-600 capitalize">
                  {actionType}
                </Badge>
                {risk && (
                  <Badge variant="outline" className={`text-[9px] capitalize ${
                    risk === "critical" ? "border-red-500/30 text-red-600"
                    : risk === "high" ? "border-orange-500/30 text-orange-600"
                    : "border-border text-muted-foreground"
                  }`}>
                    {risk}
                  </Badge>
                )}
                <span className="text-[10px] text-muted-foreground/60 ml-auto">
                  {timeAgo(item.created_at)}
                </span>
              </div>
              <p className="text-xs font-medium text-foreground leading-snug">{String(summary)}</p>
              <div className="flex gap-1.5 pt-1">
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => handleAct(item.aggregate_id, false)}
                  disabled={acting === item.aggregate_id}
                  className="h-7 px-2 text-[11px] border-red-500/30 text-red-600 hover:bg-red-500/10"
                >
                  <XCircle className="h-3 w-3 mr-1" />
                  Reject
                </Button>
                <Button
                  size="sm"
                  onClick={() => handleAct(item.aggregate_id, true)}
                  disabled={acting === item.aggregate_id}
                  className="h-7 px-2 text-[11px] bg-emerald-600 text-white hover:bg-emerald-700"
                >
                  <CheckCircle2 className="h-3 w-3 mr-1" />
                  Approve
                </Button>
              </div>
            </div>
          )
        })}
      </div>
    </ScrollArea>
  )
}

// ─── Memory panel ─────────────────────────────────────────────────────
function MemoryPanel({
  query,
  setQuery,
  results,
  searching,
}: {
  query: string
  setQuery: (s: string) => void
  results: any[]
  searching: boolean
}) {
  return (
    <div className="flex flex-col h-full">
      <div className="p-3 border-b border-border/60 shrink-0">
        <div className="relative">
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
          <Input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search memory…"
            className="h-8 pl-8 text-xs bg-background"
          />
        </div>
      </div>
      <ScrollArea className="flex-1">
        <div className="p-3 space-y-2">
          {!query && (
            <div className="flex flex-col items-center justify-center py-12 gap-2 text-center">
              <Brain className="h-8 w-8 text-muted-foreground/30" />
              <p className="text-xs text-muted-foreground">Search your institutional memory</p>
              <p className="text-[11px] text-muted-foreground/70 max-w-xs">
                Memories are captured automatically. Type a query above to find related decisions, projects, and notes.
              </p>
            </div>
          )}
          {searching && (
            <div className="space-y-2">
              {Array.from({ length: 3 }).map((_, i) => <div key={i} className="h-16 rounded-md bg-muted/30 animate-pulse" />)}
            </div>
          )}
          {!searching && query && results.length === 0 && (
            <div className="text-center py-8">
              <p className="text-xs text-muted-foreground">No memories matched &ldquo;{query}&rdquo;</p>
            </div>
          )}
          {results.map((m, idx) => (
            <div key={m.id ?? idx} className="rounded-md border border-border/70 bg-background p-2.5 space-y-1.5">
              <div className="flex items-center gap-1.5">
                {m.memory_type && (
                  <Badge variant="outline" className="text-[9px] border-havilah-gold/30 text-havilah-gold">
                    {m.memory_type}
                  </Badge>
                )}
                {m.created_at && (
                  <span className="text-[10px] text-muted-foreground/60 ml-auto">{timeAgo(m.created_at)}</span>
                )}
              </div>
              {m.title && <p className="text-xs font-medium text-foreground leading-snug">{m.title}</p>}
              {m.content && <p className="text-[11px] text-muted-foreground/80 line-clamp-3">{m.content}</p>}
            </div>
          ))}
        </div>
      </ScrollArea>
    </div>
  )
}
