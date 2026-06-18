"use client"

import { useState, useCallback, useEffect, useRef } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import {
  MessageSquare,
  LayoutGrid,
  Send,
  ShieldCheck,
  ShieldAlert,
  Database,
  CheckCircle2,
  Loader2,
  Sparkles,
  XCircle,
  AlertCircle,
  RefreshCw,
  Zap,
  ChevronDown,
  ChevronRight,
  Clock,
  Cpu,
  type LucideIcon,
} from "lucide-react"
import { motion, AnimatePresence } from "framer-motion"
import { toast } from "sonner"
import {
  havilahApi,
  HermesInstructionResponse,
  HermesResult,
  HermesStep,
  isApiConfigured,
  ApiError,
} from "@/lib/havilah-api"

// ─── Agent visual registry ────────────────────────────────────────
const AGENT_VISUALS: Record<string, { icon: LucideIcon; color: string }> = {
  planner:   { icon: LayoutGrid,    color: "#60a5fa" },
  executive: { icon: ShieldCheck,   color: "#d4a853" },
  research:  { icon: MessageSquare, color: "#34d399" },
  writing:   { icon: MessageSquare, color: "#f472b6" },
  meeting:   { icon: MessageSquare, color: "#a78bfa" },
  reviewer:  { icon: ShieldAlert,   color: "#fb7185" },
  critic:    { icon: AlertCircle,   color: "#fb923c" },
  memory:    { icon: Database,      color: "#22d3ee" },
  learning:  { icon: Sparkles,      color: "#4ade80" },
  approval:  { icon: ShieldCheck,   color: "#facc15" },
}

function getAgentVisual(name?: string) {
  if (!name) return { icon: MessageSquare, color: "#64748b" }
  return AGENT_VISUALS[name.toLowerCase()] ?? { icon: MessageSquare, color: "#64748b" }
}

const RISK_COLORS: Record<string, string> = {
  low:      "border-emerald-500/30 text-emerald-500 bg-emerald-500/5",
  medium:   "border-amber-500/30   text-amber-500   bg-amber-500/5",
  high:     "border-red-500/30     text-red-500     bg-red-500/5",
  critical: "border-purple-500/30  text-purple-500  bg-purple-500/5",
}

type RunState = "idle" | "submitting" | "completed" | "awaiting_approval" | "failed" | "auto_approving"

const AUTO_APPROVE_KEY = "havilah_auto_approve"

// ─── Helper: detect if a response needs human approval ─────────────
function needsApproval(resp: HermesInstructionResponse): boolean {
  return (
    resp.status === "awaiting_approval" ||
    resp.approval_needed === true ||
    Boolean(resp.approval_id)
  )
}

// ─── Helper: extract a clean string from a result object ──────────
function getResultText(r: HermesResult): string {
  if (typeof r === "string") return r
  return r.output ?? r.error ?? r.action ?? JSON.stringify(r, null, 2)
}

// ─── Component ────────────────────────────────────────────────────
export function HermesCommand() {
  const [instruction, setInstruction] = useState("")
  const [runState, setRunState] = useState<RunState>("idle")
  const [result, setResult] = useState<HermesInstructionResponse | null>(null)
  const [errorMsg, setErrorMsg] = useState<string>("")
  const [actingOnApproval, setActingOn] = useState<"approve" | "reject" | null>(null)

  // Auto-approve toggle (persisted to localStorage)
  const [autoApprove, setAutoApprove] = useState(false)
  const autoApproveRef = useRef(false)
  useEffect(() => {
    if (typeof window === "undefined") return
    const stored = localStorage.getItem(AUTO_APPROVE_KEY)
    const initial = stored === "true"
    setAutoApprove(initial)
    autoApproveRef.current = initial
  }, [])
  const toggleAutoApprove = useCallback(() => {
    const next = !autoApprove
    setAutoApprove(next)
    autoApproveRef.current = next
    try { localStorage.setItem(AUTO_APPROVE_KEY, String(next)) } catch {}
    if (next) {
      toast.success("Auto-Approve ON", {
        description: "Future runs will continue automatically when approval is needed.",
      })
    } else {
      toast.info("Auto-Approve OFF", {
        description: "Approval-required runs will pause for your review.",
      })
    }
  }, [autoApprove])

  // ─── Submit handler ───────────────────────────────────────────
  const handleSubmit = useCallback(async (e?: React.FormEvent) => {
    e?.preventDefault()
    if (!instruction.trim() || runState === "submitting") return

    if (!isApiConfigured) {
      toast.error("Backend not configured", {
        description: "Set NEXT_PUBLIC_HAVILAH_API_URL in Vercel env vars.",
      })
      return
    }

    setRunState("submitting")
    setErrorMsg("")
    setResult(null)

    try {
      const resp = await havilahApi.instruct(instruction.trim(), "dashboard")
      setResult(resp)
      applyRunState(resp)
    } catch (err: any) {
      const msg = err instanceof ApiError ? err.message : String(err)
      setErrorMsg(msg)
      setRunState("failed")
      toast.error("Hermes call failed", { description: msg })
    }
  }, [instruction, runState])

  // Apply the right run state from a response
  function applyRunState(resp: HermesInstructionResponse) {
    if (needsApproval(resp)) {
      setRunState("awaiting_approval")
      // If auto-approve is ON, immediately continue
      if (autoApproveRef.current) {
        toast.info("Auto-approving…", {
          description: "Auto-Approve is ON — continuing the run automatically.",
        })
        // Fire-and-forget approve
        setTimeout(() => doApprove(resp.run_id, true), 200)
      } else {
        toast.info("Approval needed", {
          description: `Step paused. Review and approve to continue.`,
        })
      }
    } else if (resp.status === "completed") {
      setRunState("completed")
      toast.success("Hermes run completed", {
        description: resp.summary ?? "See results below.",
      })
    } else if (resp.status === "failed") {
      setRunState("failed")
      setErrorMsg(resp.error || resp.message || "Hermes run failed.")
      toast.error("Hermes run failed")
    } else {
      // planning, executing, cancelled, etc. — treat as completed for display
      setRunState("completed")
    }
  }

  // ─── Approve / Reject ────────────────────────────────────────
  const doApprove = useCallback(async (runId: string, isAuto = false) => {
    setActingOn("approve")
    if (!isAuto) setRunState("auto_approving")
    try {
      const resp = await havilahApi.approve(runId, isAuto ? "Auto-approved via dashboard" : "Approved via dashboard")
      // The approve endpoint returns a new HermesInstructionResponse — update state
      if (resp && typeof resp === "object" && "run_id" in resp) {
        setResult(resp as HermesInstructionResponse)
        applyRunState(resp as HermesInstructionResponse)
      } else {
        // Just flip local state if response shape is unexpected
        setRunState("completed")
      }
      if (isAuto) {
        toast.success("Auto-approved & continued", {
          description: "Hermes has resumed the run automatically.",
        })
      } else {
        toast.success("Approved", { description: "Hermes is continuing the run." })
      }
    } catch (e: any) {
      const msg = e instanceof ApiError ? e.message : String(e)
      toast.error("Approve failed", { description: msg })
      // Restore awaiting state so user can retry
      setRunState("awaiting_approval")
    } finally {
      setActingOn(null)
    }
  }, [])

  const handleApprove = () => {
    if (!result?.run_id) return
    doApprove(result.run_id, false)
  }

  const handleReject = async () => {
    if (!result?.run_id) return
    setActingOn("reject")
    try {
      const resp = await havilahApi.reject(result.run_id, "Rejected via dashboard")
      toast.error("Rejected", { description: "Hermes run has been cancelled." })
      if (resp && typeof resp === "object" && "run_id" in resp) {
        setResult(resp as HermesInstructionResponse)
        setRunState("failed")
        setErrorMsg("Run rejected by user.")
      } else {
        setRunState("failed")
        setErrorMsg("Run rejected by user.")
      }
    } catch (e: any) {
      const msg = e instanceof ApiError ? e.message : String(e)
      toast.error("Reject failed", { description: msg })
    } finally {
      setActingOn(null)
    }
  }

  const handleReset = () => {
    setInstruction("")
    setResult(null)
    setRunState("idle")
    setErrorMsg("")
  }

  // ─── Derived state ───────────────────────────────────────────
  const isProcessing = runState === "submitting" || runState === "auto_approving"
  const steps = result?.plan?.steps ?? []
  const results = result?.results ?? []

  // ─── Status badge for header ────────────────────────────────
  const statusBadge = (() => {
    if (runState === "idle") return null
    const config: Record<string, { label: string; cls: string }> = {
      submitting:         { label: "RUNNING",       cls: "border-havilah-gold/30 text-havilah-gold" },
      auto_approving:     { label: "AUTO-APPROVING", cls: "border-purple-500/30 text-purple-500" },
      completed:          { label: "COMPLETED",     cls: "border-emerald-500/30 text-emerald-500" },
      awaiting_approval:  { label: "AWAITING APPROVAL", cls: "border-amber-500/30 text-amber-500" },
      failed:             { label: "FAILED",        cls: "border-red-500/30 text-red-500" },
    }
    const c = config[runState]
    if (!c) return null
    return (
      <Badge variant="outline" className={`text-[10px] font-mono tracking-wider ${c.cls}`}>
        {c.label}
      </Badge>
    )
  })()

  return (
    <Card className="border-havilah-gold/20 bg-card gold-border-glow">
      <CardHeader className="pb-4">
        <CardTitle className="flex items-center justify-between gap-3 text-foreground">
          <span className="flex items-center gap-2.5">
            <Sparkles className="h-5 w-5 text-havilah-gold" />
            <span className="text-base sm:text-lg">Hermes Command Center</span>
            {statusBadge}
          </span>
          <div className="flex items-center gap-2">
            {result?.run_id && (
              <Badge variant="outline" className="font-mono text-[10px] text-muted-foreground hidden sm:inline-flex">
                <Clock className="h-3 w-3 mr-1" />
                {result.run_id.slice(0, 8)}…
              </Badge>
            )}
            {result?.elapsed_seconds != null && (
              <Badge variant="outline" className="font-mono text-[10px] text-muted-foreground hidden md:inline-flex">
                {result.elapsed_seconds.toFixed(1)}s
              </Badge>
            )}
          </div>
        </CardTitle>
      </CardHeader>

      <CardContent className="space-y-5">
        {/* ─── Command Input + Auto-Approve Toggle ─────────────────── */}
        <div className="space-y-3">
          <form onSubmit={handleSubmit} className="flex flex-col sm:flex-row gap-2.5">
            <Input
              value={instruction}
              onChange={(e) => setInstruction(e.target.value)}
              placeholder="Enter a natural language instruction…  (e.g. “Research the top 5 AI coding tools in 2026”)"
              disabled={isProcessing}
              className="flex-1 h-11 border-border bg-background text-sm placeholder:text-muted-foreground focus-visible:border-havilah-gold focus-visible:ring-havilah-gold/30"
            />
            <Button
              type="submit"
              disabled={isProcessing || !instruction.trim()}
              className="h-11 px-5 bg-gradient-to-r from-havilah-gold to-havilah-gold-dark text-white shadow-lg shadow-havilah-gold/25 hover:shadow-havilah-gold/40 hover:brightness-110 disabled:opacity-50"
            >
              {isProcessing ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Send className="h-4 w-4" />
              )}
              <span className="ml-2 text-sm font-medium">
                {isProcessing ? "Working…" : "Submit"}
              </span>
            </Button>
          </form>

          {/* Auto-Approve Toggle */}
          <div className="flex items-center justify-between gap-3 rounded-lg border border-border bg-background/50 px-3.5 py-2.5">
            <div className="flex items-start gap-2.5 min-w-0">
              <div className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-md ${autoApprove ? "bg-purple-500/15 text-purple-500" : "bg-muted text-muted-foreground"}`}>
                {autoApprove ? <Zap className="h-4 w-4" /> : <ShieldCheck className="h-4 w-4" />}
              </div>
              <div className="min-w-0">
                <p className="text-sm font-medium text-foreground leading-tight">
                  Auto-Approve {autoApprove ? "ON" : "OFF"}
                </p>
                <p className="text-xs text-muted-foreground leading-snug mt-0.5">
                  {autoApprove
                    ? "Runs will continue automatically when approval is needed — no manual review."
                    : "Approval-required runs will pause and wait for your manual sign-off."}
                </p>
              </div>
            </div>
            <button
              type="button"
              role="switch"
              aria-checked={autoApprove}
              onClick={toggleAutoApprove}
              disabled={isProcessing}
              className={`relative shrink-0 h-6 w-11 rounded-full transition-colors disabled:opacity-50 ${
                autoApprove ? "bg-purple-500" : "bg-muted-foreground/30"
              }`}
            >
              <span
                className={`absolute top-0.5 left-0.5 h-5 w-5 rounded-full bg-white shadow-sm transition-transform ${
                  autoApprove ? "translate-x-5" : "translate-x-0"
                }`}
              />
            </button>
          </div>
        </div>

        {/* ─── Loading state during submission ─────────────────────── */}
        {isProcessing && (
          <div className="flex flex-col items-center justify-center py-10 gap-3">
            <div className="relative">
              <div className="absolute inset-0 animate-ping rounded-full bg-havilah-gold/30" />
              <div className="relative flex h-14 w-14 items-center justify-center rounded-full bg-havilah-gold/15">
                {runState === "auto_approving" ? (
                  <Zap className="h-7 w-7 text-purple-500 animate-pulse" />
                ) : (
                  <Sparkles className="h-7 w-7 text-havilah-gold animate-pulse" />
                )}
              </div>
            </div>
            <p className="text-sm font-medium text-foreground">
              {runState === "auto_approving"
                ? "Auto-approving and continuing the run…"
                : "Hermes is planning your instruction through 10 agents…"}
            </p>
            <p className="text-xs text-muted-foreground/60">
              This calls GPT-4o and may take 10–30 seconds per step.
            </p>
          </div>
        )}

        {/* ─── Plan visualization ─────────────────────────────────── */}
        {!isProcessing && steps.length > 0 && (
          <div className="space-y-3">
            <div className="flex items-center justify-between gap-3">
              <p className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
                Orchestration Plan
              </p>
              <span className="text-xs text-muted-foreground">
                {steps.length} step{steps.length !== 1 ? "s" : ""} •{" "}
                {result?.plan?.requires_any_approval ? (
                  <span className="text-amber-500">Approval required</span>
                ) : (
                  <span className="text-emerald-500">No approval needed</span>
                )}
              </span>
            </div>

            {/* Plan summary */}
            {result?.plan?.summary && (
              <div className="rounded-lg border border-havilah-gold/20 bg-havilah-gold/5 px-4 py-3">
                <p className="text-sm text-foreground/90 italic leading-relaxed">
                  &ldquo;{result.plan.summary}&rdquo;
                </p>
              </div>
            )}

            {/* Steps */}
            <div className="space-y-2">
              {steps.map((step, idx) => {
                // Try to find a matching result for this step
                const matchingResult = results.find((r) => r.step_number === step.step_number)
                return (
                  <StepCard
                    key={idx}
                    step={step}
                    result={matchingResult}
                    isAwaiting={
                      runState === "awaiting_approval" &&
                      step.approval_required &&
                      matchingResult != null
                    }
                  />
                )
              })}
            </div>
          </div>
        )}

        {/* ─── Approval actions ───────────────────────────────────── */}
        {runState === "awaiting_approval" && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="rounded-xl border border-amber-500/30 bg-amber-500/5 p-4 sm:p-5 space-y-4"
          >
            <div className="flex items-start gap-3">
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-amber-500/15">
                <ShieldCheck className="h-5 w-5 text-amber-500" />
              </div>
              <div className="flex-1 min-w-0 space-y-1">
                <p className="text-sm font-semibold text-foreground">
                  Human approval required to continue
                </p>
                <p className="text-xs text-muted-foreground leading-relaxed">
                  Hermes has paused the run. Review the pending step above, then choose to continue or cancel.
                </p>
                {result?.approval_id && (
                  <p className="text-[11px] text-muted-foreground/70 font-mono pt-1">
                    Approval ID: {result.approval_id.slice(0, 8)}…
                  </p>
                )}
              </div>
            </div>
            <div className="flex flex-col-reverse sm:flex-row gap-2 sm:justify-end">
              <Button
                onClick={handleReject}
                disabled={actingOnApproval !== null}
                variant="outline"
                className="h-10 border-red-500/30 text-red-500 hover:bg-red-500/10"
              >
                {actingOnApproval === "reject" ? (
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                ) : (
                  <XCircle className="h-4 w-4 mr-2" />
                )}
                Reject
              </Button>
              <Button
                onClick={handleApprove}
                disabled={actingOnApproval !== null}
                className="h-10 bg-emerald-600 text-white hover:bg-emerald-700 shadow-md shadow-emerald-600/20"
              >
                {actingOnApproval === "approve" ? (
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                ) : (
                  <CheckCircle2 className="h-4 w-4 mr-2" />
                )}
                Approve &amp; Continue
              </Button>
            </div>
          </motion.div>
        )}

        {/* ─── Run summary (completed) ────────────────────────────── */}
        <AnimatePresence>
          {runState === "completed" && result?.summary && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              className="rounded-xl border border-emerald-500/20 bg-emerald-500/5 p-4 sm:p-5"
            >
              <div className="flex items-start gap-3">
                <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-emerald-500/15">
                  <CheckCircle2 className="h-5 w-5 text-emerald-500" />
                </div>
                <div className="flex-1 min-w-0 space-y-2">
                  <p className="text-sm font-semibold text-foreground">Run completed</p>
                  <p className="text-sm text-foreground/85 whitespace-pre-wrap leading-relaxed">
                    {result.summary}
                  </p>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* ─── Error state ────────────────────────────────────────── */}
        <AnimatePresence>
          {runState === "failed" && errorMsg && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              className="rounded-xl border border-red-500/20 bg-red-500/5 p-4 sm:p-5"
            >
              <div className="flex items-start gap-3">
                <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-red-500/15">
                  <AlertCircle className="h-5 w-5 text-red-500" />
                </div>
                <div className="flex-1 min-w-0 space-y-1">
                  <p className="text-sm font-semibold text-foreground">Run failed</p>
                  <p className="text-sm text-foreground/80 leading-relaxed">{errorMsg}</p>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* ─── Footer actions ─────────────────────────────────────── */}
        {runState !== "idle" && runState !== "submitting" && (
          <div className="flex justify-center pt-1">
            <Button variant="ghost" size="sm" onClick={handleReset} className="h-8 text-xs">
              <RefreshCw className="h-3 w-3 mr-2" />
              New instruction
            </Button>
          </div>
        )}

        {/* ─── Idle hint ──────────────────────────────────────────── */}
        {runState === "idle" && (
          <div className="rounded-xl border border-dashed border-border bg-background/40 p-5 space-y-2">
            <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              Try one of these
            </p>
            <div className="flex flex-wrap gap-2">
              {[
                "Research the top 5 AI coding tools in 2026",
                "Draft a project brief for a Q3 competitive audit",
                "Summarize the latest AI agent research papers",
              ].map((ex) => (
                <button
                  key={ex}
                  type="button"
                  onClick={() => setInstruction(ex)}
                  className="rounded-full border border-border bg-card px-3 py-1.5 text-xs text-foreground/80 hover:border-havilah-gold/40 hover:bg-havilah-gold/5 hover:text-foreground transition-colors"
                >
                  {ex}
                </button>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

// ─── Step Card subcomponent ────────────────────────────────────────
function StepCard({
  step,
  result,
  isAwaiting,
}: {
  step: HermesStep
  result?: HermesResult
  isAwaiting?: boolean
}) {
  const visual = getAgentVisual(step.agent)
  const Icon = visual.icon
  const riskColor = RISK_COLORS[step.risk_level] ?? RISK_COLORS.low
  const [expanded, setExpanded] = useState(false)
  const hasResult = result && result.output
  const isFailed = result?.status === "failed"

  return (
    <motion.div
      initial={{ opacity: 0, x: -10 }}
      animate={{ opacity: 1, x: 0 }}
      className={`rounded-lg border bg-background transition-colors ${
        isAwaiting
          ? "border-amber-500/40 bg-amber-500/5"
          : isFailed
          ? "border-red-500/30"
          : "border-border hover:border-havilah-gold/20"
      }`}
    >
      <div className="p-3.5 sm:p-4">
        <div className="flex items-start gap-3">
          {/* Agent icon */}
          <div
            className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg"
            style={{ backgroundColor: `${visual.color}15`, color: visual.color }}
          >
            <Icon className="h-4 w-4" />
          </div>

          {/* Content */}
          <div className="flex-1 space-y-2 min-w-0">
            {/* Action line + badges */}
            <div className="space-y-1.5">
              <p className="text-sm font-medium text-foreground leading-snug">
                <span className="text-muted-foreground/60 text-xs mr-1.5 font-mono">
                  #{step.step_number}
                </span>
                {step.action}
              </p>
              <div className="flex flex-wrap items-center gap-1.5">
                <Badge variant="outline" className="text-[10px] capitalize">
                  {step.agent}
                </Badge>
                <Badge variant="outline" className={`text-[10px] capitalize ${riskColor}`}>
                  {step.risk_level}
                </Badge>
                {step.approval_required && (
                  <Badge variant="outline" className="text-[10px] border-amber-500/30 text-amber-500 bg-amber-500/5">
                    <ShieldCheck className="h-3 w-3 mr-1" />
                    Approval
                  </Badge>
                )}
                {result?.status === "success" && (
                  <Badge variant="outline" className="text-[10px] border-emerald-500/30 text-emerald-500 bg-emerald-500/5">
                    <CheckCircle2 className="h-3 w-3 mr-1" />
                    Done
                  </Badge>
                )}
                {isAwaiting && (
                  <Badge variant="outline" className="text-[10px] border-amber-500/40 text-amber-500 bg-amber-500/10 animate-pulse">
                    <Clock className="h-3 w-3 mr-1" />
                    Paused
                  </Badge>
                )}
                {result?.status === "failed" && (
                  <Badge variant="outline" className="text-[10px] border-red-500/30 text-red-500 bg-red-500/5">
                    <XCircle className="h-3 w-3 mr-1" />
                    Failed
                  </Badge>
                )}
              </div>
            </div>

            {/* Expected output */}
            {step.expected_output && !hasResult && (
              <p className="text-xs text-muted-foreground/80 leading-relaxed pl-1">
                <span className="text-muted-foreground/60">Expected:</span>{" "}
                {step.expected_output}
              </p>
            )}

            {/* Result output (collapsible if long) */}
            {hasResult && (
              <ResultOutput
                text={getResultText(result!)}
                tokens={result!.tokens}
                expanded={expanded}
                onToggle={() => setExpanded((v) => !v)}
              />
            )}
          </div>
        </div>
      </div>
    </motion.div>
  )
}

// ─── Result output (collapsible long text) ─────────────────────────
function ResultOutput({
  text,
  tokens,
  expanded,
  onToggle,
}: {
  text: string
  tokens?: number
  expanded: boolean
  onToggle: () => void
}) {
  const isLong = text.length > 240
  const preview = isLong && !expanded ? text.slice(0, 240) + "…" : text

  return (
    <div className="rounded-md bg-muted/30 border border-border/60 overflow-hidden">
      <div className="px-3 py-2.5">
        <div className="flex items-center justify-between gap-2 mb-1.5">
          <div className="flex items-center gap-1.5 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground/70">
            <Cpu className="h-3 w-3" />
            Output
          </div>
          {tokens != null && (
            <span className="text-[10px] text-muted-foreground/60 font-mono">
              {tokens} tok
            </span>
          )}
        </div>
        <p className="text-xs leading-relaxed text-foreground/85 whitespace-pre-wrap font-mono">
          {preview}
        </p>
      </div>
      {isLong && (
        <button
          type="button"
          onClick={onToggle}
          className="w-full flex items-center justify-center gap-1.5 py-1.5 text-[11px] text-muted-foreground hover:text-foreground hover:bg-muted/50 transition-colors border-t border-border/60"
        >
          {expanded ? (
            <>
              <ChevronDown className="h-3 w-3" />
              Show less
            </>
          ) : (
            <>
              <ChevronRight className="h-3 w-3" />
              Show full output ({text.length} chars)
            </>
          )}
        </button>
      )}
    </div>
  )
}
