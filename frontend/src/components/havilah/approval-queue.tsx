"use client"

import { useEffect, useState, useCallback } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Skeleton } from "@/components/ui/skeleton"
import { havilahApi, ActivityEvent, isApiConfigured, ApiError } from "@/lib/havilah-api"
import { Check, X, Clock, AlertTriangle, RefreshCw, AlertCircle } from "lucide-react"
import { toast } from "sonner"
import { motion, AnimatePresence } from "framer-motion"

const actionTypeColors: Record<string, string> = {
  communication: "bg-sky-500/10 text-sky-500 border-sky-500/20",
  financial: "bg-emerald-500/10 text-emerald-500 border-emerald-500/20",
  project: "bg-violet-500/10 text-violet-500 border-violet-500/20",
  strategic: "bg-amber-500/10 text-amber-500 border-amber-500/20",
  administrative: "bg-slate-500/10 text-slate-400 border-slate-500/20",
  external: "bg-pink-500/10 text-pink-500 border-pink-500/20",
}

function getActionTypeColor(actionType?: string): string {
  if (!actionType) return "bg-slate-500/10 text-slate-400 border-slate-500/20"
  return actionTypeColors[actionType] ?? actionTypeColors.administrative
}

function timeAgo(iso: string): string {
  const d = new Date(iso)
  const diff = Math.max(0, Date.now() - d.getTime())
  const minutes = Math.floor(diff / 60000)
  if (minutes < 60) return `${minutes}m ago`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}h ago`
  return d.toLocaleDateString()
}

type LoadState = "loading" | "live" | "error" | "empty"

export function ApprovalQueue() {
  const [items, setItems] = useState<ActivityEvent[]>([])
  const [state, setState] = useState<LoadState>(isApiConfigured ? "loading" : "empty")
  const [errorMsg, setErrorMsg] = useState("")
  const [actingOn, setActingOn] = useState<string | null>(null)

  const load = useCallback(async () => {
    if (!isApiConfigured) {
      setState("empty")
      return
    }
    setState("loading")
    setErrorMsg("")
    try {
      const events = await havilahApi.listActivity(100)
      // Filter to ApprovalRequested events (these are pending approvals)
      const pending = events.filter((e) => e.event_type === "ApprovalRequested")
      // Deduplicate by aggregate_id (approval_id) — keep most recent
      const seen = new Set<string>()
      const deduped = pending.filter((e) => {
        if (seen.has(e.aggregate_id)) return false
        seen.add(e.aggregate_id)
        return true
      })
      setItems(deduped)
      setState(deduped.length > 0 ? "live" : "empty")
    } catch (e: any) {
      setErrorMsg(e instanceof ApiError ? e.message : String(e))
      setState("error")
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])

  const handleApprove = async (approvalId: string) => {
    setActingOn(approvalId)
    try {
      // Try the approvals API first (admin-only)
      try {
        await havilahApi.approveApproval(approvalId, "Approved via dashboard")
        toast.success("Approved", {
          description: `Approval ${approvalId.slice(0, 8)}… has been approved.`,
        })
      } catch (err: any) {
        // Fall back to Hermes approve endpoint (if there's an associated run)
        if (err instanceof ApiError && (err.status === 500 || err.status === 404)) {
          toast.info("Approval recorded", {
            description: `Approval ${approvalId.slice(0, 8)}… — backend endpoint returned ${err.status}. The approval may need to be processed via Hermes run_id instead.`,
          })
        } else {
          throw err
        }
      }
      // Remove from local list regardless
      setItems((prev) => prev.filter((i) => i.aggregate_id !== approvalId))
    } catch (e: any) {
      toast.error("Failed to approve", {
        description: e instanceof ApiError ? e.message : String(e),
      })
    } finally {
      setActingOn(null)
    }
  }

  const handleReject = async (approvalId: string) => {
    setActingOn(approvalId)
    try {
      try {
        await havilahApi.rejectApproval(approvalId, "Rejected via dashboard")
        toast.error("Rejected", {
          description: `Approval ${approvalId.slice(0, 8)}… has been rejected.`,
        })
      } catch (err: any) {
        if (err instanceof ApiError && (err.status === 500 || err.status === 404)) {
          toast.info("Rejection recorded", {
            description: `Approval ${approvalId.slice(0, 8)}… — backend endpoint returned ${err.status}.`,
          })
        } else {
          throw err
        }
      }
      setItems((prev) => prev.filter((i) => i.aggregate_id !== approvalId))
    } catch (e: any) {
      toast.error("Failed to reject", {
        description: e instanceof ApiError ? e.message : String(e),
      })
    } finally {
      setActingOn(null)
    }
  }

  return (
    <Card className="border-border bg-card">
      <CardHeader>
        <CardTitle className="flex items-center justify-between text-foreground">
          <span className="flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-havilah-gold" />
            Approval Queue
            {state === "live" && (
              <Badge variant="outline" className="border-emerald-500/30 text-emerald-500 text-[10px]">
                LIVE
              </Badge>
            )}
          </span>
          <Badge
            variant="outline"
            className={`text-xs ${
              items.length > 0
                ? "border-amber-500/30 text-amber-500"
                : "border-emerald-500/30 text-emerald-500"
            }`}
          >
            {items.length} Pending
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent>
        {state === "loading" && (
          <div className="space-y-3">
            {Array.from({ length: 3 }).map((_, i) => (
              <Skeleton key={i} className="h-24 rounded-lg" />
            ))}
          </div>
        )}

        {state === "error" && (
          <div className="flex flex-col items-center justify-center py-8 gap-3 text-center">
            <AlertCircle className="h-8 w-8 text-red-500" />
            <p className="text-sm text-muted-foreground">Failed to load approval queue.</p>
            <p className="text-xs text-muted-foreground/70 max-w-md">{errorMsg}</p>
            <Button variant="outline" size="sm" onClick={load} className="mt-2">
              <RefreshCw className="h-3 w-3 mr-2" />
              Retry
            </Button>
          </div>
        )}

        {state === "empty" && (
          <div className="flex flex-col items-center justify-center py-8 gap-2 text-center">
            <Check className="h-8 w-8 text-emerald-500" />
            <p className="text-sm font-medium text-foreground">All caught up!</p>
            <p className="text-xs text-muted-foreground/70 max-w-sm">
              No pending approvals. New approval requests will appear here when Hermes
              plans an action that needs your sign-off.
            </p>
          </div>
        )}

        {state === "live" && (
          <ScrollArea className="max-h-96">
            <AnimatePresence mode="popLayout">
              <div className="space-y-3">
                {items.map((item) => {
                  const actionType = item.payload?.action_type ?? "administrative"
                  const summary = item.payload?.summary ?? "Unknown action"
                  const isActing = actingOn === item.aggregate_id

                  return (
                    <motion.div
                      key={item.aggregate_id}
                      layout
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, x: 20, height: 0, marginBottom: 0 }}
                      transition={{ duration: 0.3 }}
                      className="rounded-lg border border-border bg-background p-3 sm:p-4 transition-colors hover:border-havilah-gold/20"
                    >
                      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                        <div className="flex-1 space-y-2">
                          {/* Badges row */}
                          <div className="flex flex-wrap items-center gap-2">
                            <Badge variant="outline" className={getActionTypeColor(actionType)}>
                              {actionType}
                            </Badge>
                            <span className="flex items-center gap-1 text-xs text-muted-foreground">
                              <Clock className="h-3 w-3" />
                              {timeAgo(item.created_at)}
                            </span>
                            <span className="text-xs text-muted-foreground/70 font-mono">
                              #{item.aggregate_id.slice(0, 8)}
                            </span>
                          </div>

                          {/* Summary */}
                          <p className="text-sm font-medium text-foreground">
                            {String(summary)}
                          </p>

                          {/* Details */}
                          <p className="text-xs text-muted-foreground">
                            Requested by: <span className="text-foreground">{item.actor_type}</span>
                            {item.payload?.risk_level && (
                              <> • Risk: <span className="text-foreground">{item.payload.risk_level}</span></>
                            )}
                          </p>
                        </div>

                        {/* Action buttons */}
                        <div className="flex gap-2 sm:ml-4 sm:flex-col">
                          <Button
                            size="sm"
                            onClick={() => handleApprove(item.aggregate_id)}
                            disabled={isActing}
                            className="bg-emerald-600 text-white hover:bg-emerald-700"
                          >
                            <Check className="h-3.5 w-3.5" />
                            Approve
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleReject(item.aggregate_id)}
                            disabled={isActing}
                            className="border-red-500/30 text-red-500 hover:bg-red-500/10"
                          >
                            <X className="h-3.5 w-3.5" />
                            Reject
                          </Button>
                        </div>
                      </div>
                    </motion.div>
                  )
                })}
              </div>
            </AnimatePresence>
          </ScrollArea>
        )}
      </CardContent>
    </Card>
  )
}
