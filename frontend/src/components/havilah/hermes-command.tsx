"use client"

import { useState, useCallback, useEffect, useRef } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import {
  LayoutList,
  Crown,
  Search,
  PenTool,
  Users,
  Eye,
  ShieldAlert,
  Brain,
  GraduationCap,
  MessageSquare,
  Send,
  ShieldCheck,
  CheckCircle2,
  Loader2,
  Sparkles,
  XCircle,
  AlertCircle,
  RefreshCw,
  Zap,
  ChevronRight,
  Clock,
  Cpu,
  type LucideIcon,
} from "lucide-react"
import Markdown from "react-markdown"
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
const AGENT_VISUALS: Record<string, { icon: LucideIcon; color: string; label: string }> = {
  planner:   { icon: LayoutList,    color: "#60a5fa", label: "Planner"   },
  executive: { icon: Crown,         color: "#b8821e", label: "Executive" },
  research:  { icon: Search,        color: "#34d399", label: "Research"  },
  writing:   { icon: PenTool,       color: "#f472b6", label: "Writing"   },
  meeting:   { icon: Users,         color: "#a78bfa", label: "Meeting"   },
  reviewer:  { icon: Eye,           color: "#2dd4bf", label: "Reviewer"  },
  critic:    { icon: ShieldAlert,   color: "#fb923c", label: "Critic"    },
  memory:    { icon: Brain,         color: "#818cf8", label: "Memory"    },
  learning:  { icon: GraduationCap, color: "#4ade80", label: "Learning"  },
  approval:  { icon: ShieldCheck,   color: "#facc15", label: "Approval"  },
}

function getAgentVisual(name?: string) {
  if (!name) return { icon: MessageSquare, color: "#64748b", label: "Agent" }
  return AGENT_VISUALS[name.toLowerCase()] ?? { icon: MessageSquare, color: "#64748b", label: name }
}

const RISK_COLORS: Record<string, string> = {
  low:      "border-emerald-500/30 text-emerald-400 bg-emerald-500/5",
  medium:   "border-amber-500/30   text-amber-400   bg-amber-500/5",
  high:     "border-red-500/30     text-red-400     bg-red-500/5",
  critical: "border-purple-500/30  text-purple-400  bg-purple-500/5",
}

type RunState = "idle" | "submitting" | "completed" | "awaiting_approval" | "failed" | "auto_approving"

const AUTO_APPROVE_KEY = "havilah_auto_approve"
const USER_KEY = "havilah_user"

function getCurrentUserId(): string | null {
  if (typeof window === "undefined") return null
  try {
    const raw = localStorage.getItem(USER_KEY)
    if (!raw) return null
    const parsed = JSON.parse(raw)
    return parsed?.id ?? parsed?.user_id ?? null
  } catch { return null }
}

function needsApproval(resp: HermesInstructionResponse): boolean {
  return (
    resp.status === "awaiting_approval" ||
    resp.approval_needed === true ||
    Boolean(resp.approval_id)
  )
}

function getResultText(r: HermesResult): string {
  if (typeof r === "string") return r
  return r.output ?? r.error ?? r.action ?? JSON.stringify(r, null, 2)
}

// ─── Main component ────────────────────────────────────────────────
export function HermesCommand() {
  const [instruction, setInstruction] = useState("")
  const [runState, setRunState] = useState<RunState>("idle")
  const [result, setResult] = useState<HermesInstructionResponse | null>(null)
  const [errorMsg, setErrorMsg] = useState<string>("")
  const [actingOnApproval, setActingOn] = useState<"approve" | "reject" | null>(null)
  const [traceOpen, setTraceOpen] = useState(false)

  const [autoApprove, setAutoApprove] = useState(false)
  const autoApproveRef = useRef(false)

  useEffect(() => {
    if (typeof window === "undefined") return
    const cached = localStorage.getItem(AUTO_APPROVE_KEY) === "true"
    setAutoApprove(cached)
    autoApproveRef.current = cached

    if (!isApiConfigured) return
    const userId = getCurrentUserId()
    if (!userId) return
    havilahApi.getPreferences(userId)
      .then((prefs) => {
        setAutoApprove(prefs.auto_approve)
        autoApproveRef.current = prefs.auto_approve
        try { localStorage.setItem(AUTO_APPROVE_KEY, String(prefs.auto_approve)) } catch {}
      })
      .catch(() => {})
  }, [])

  const toggleAutoApprove = useCallback(() => {
    const next = !autoApprove
    setAutoApprove(next)
    autoApproveRef.current = next
    try { localStorage.setItem(AUTO_APPROVE_KEY, String(next)) } catch {}

    const userId = getCurrentUserId()
    if (userId && isApiConfigured) {
      havilahApi.updatePreferences(userId, { auto_approve: next }).catch(() => {})
    }

    toast[next ? "success" : "info"](
      next ? "Auto-Approve enabled" : "Auto-Approve disabled",
      { description: next
          ? "Runs will continue automatically when approval is needed."
          : "Approval-required runs will pause for your sign-off." }
    )
  }, [autoApprove])

  // ─── Submit ───────────────────────────────────────────────────
  const handleSubmit = useCallback(async (e?: React.FormEvent) => {
    e?.preventDefault()
    if (!instruction.trim() || runState === "submitting") return

    if (!isApiConfigured) {
      toast.error("Backend not configured", {
        description: "Set NEXT_PUBLIC_HAVILAH_API_URL in your Vercel environment variables.",
      })
      return
    }

    setRunState("submitting")
    setErrorMsg("")
    setResult(null)
    setTraceOpen(false)

    try {
      const resp = await havilahApi.instruct(instruction.trim(), "dashboard")
      setResult(resp)
      applyRunState(resp)
    } catch (err: any) {
      const msg = err instanceof ApiError ? err.message : String(err)
      setErrorMsg(msg)
      setRunState("failed")
      toast.error("Hermes failed", { description: msg })
    }
  }, [instruction, runState])

  function applyRunState(resp: HermesInstructionResponse) {
    if (needsApproval(resp)) {
      setRunState("awaiting_approval")
      setTraceOpen(true) // show steps when approval needed
      if (autoApproveRef.current) {
        toast.info("Auto-approving…")
        setTimeout(() => doApprove(resp.run_id, true), 200)
      } else {
        toast.info("Approval required", { description: "Review the pending step and approve to continue." })
      }
    } else if (resp.status === "completed") {
      setRunState("completed")
      toast.success("Completed", { description: "Hermes has finished your request." })
    } else if (resp.status === "failed") {
      setRunState("failed")
      setErrorMsg(resp.error || resp.message || "Hermes run failed.")
      toast.error("Run failed")
    } else {
      setRunState("completed")
    }
  }

  // ─── Approve / Reject ────────────────────────────────────────
  const doApprove = useCallback(async (runId: string, isAuto = false) => {
    setActingOn("approve")
    if (!isAuto) setRunState("auto_approving")
    try {
      const resp = await havilahApi.approve(runId, isAuto ? "Auto-approved" : "Approved via dashboard")
      if (resp && typeof resp === "object" && "run_id" in resp) {
        setResult(resp as HermesInstructionResponse)
        applyRunState(resp as HermesInstructionResponse)
      } else {
        setRunState("completed")
      }
      toast.success(isAuto ? "Auto-approved & continued" : "Approved", {
        description: "Hermes is continuing the run.",
      })
    } catch (e: any) {
      toast.error("Approve failed", { description: e instanceof ApiError ? e.message : String(e) })
      setRunState("awaiting_approval")
    } finally {
      setActingOn(null)
    }
  }, [])

  const handleApprove = () => { if (result?.run_id) doApprove(result.run_id, false) }

  const handleReject = async () => {
    if (!result?.run_id) return
    setActingOn("reject")
    try {
      const resp = await havilahApi.reject(result.run_id, "Rejected via dashboard")
      toast.error("Rejected", { description: "Run has been cancelled." })
      if (resp && typeof resp === "object" && "run_id" in resp) {
        setResult(resp as HermesInstructionResponse)
      }
      setRunState("failed")
      setErrorMsg("Run rejected.")
    } catch (e: any) {
      toast.error("Reject failed", { description: e instanceof ApiError ? e.message : String(e) })
    } finally {
      setActingOn(null)
    }
  }

  const handleReset = () => {
    setInstruction("")
    setResult(null)
    setRunState("idle")
    setErrorMsg("")
    setTraceOpen(false)
  }

  // ─── Derived ────────────────────────────────────────────────
  const isProcessing = runState === "submitting" || runState === "auto_approving"
  const steps = result?.plan?.steps ?? []
  const results = result?.results ?? []

  return (
    <Card className="border-havilah-gold/20 bg-card shadow-xl shadow-black/20">
      {/* ── Header ─────────────────────────────────────────────── */}
      <CardHeader className="pb-4 border-b border-border/60">
        <CardTitle className="flex items-center justify-between gap-3">
          <span className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-havilah-gold/15">
              <Sparkles className="h-4 w-4 text-havilah-gold" />
            </div>
            <span className="text-base font-semibold text-foreground">Hermes Command</span>
            {runState !== "idle" && (
              <RunBadge state={runState} />
            )}
          </span>
          {result?.run_id && (
            <span className="font-mono text-[10px] text-muted-foreground/50 hidden sm:block">
              {result.run_id.slice(0, 8)}
              {result.elapsed_seconds != null && ` · ${result.elapsed_seconds.toFixed(1)}s`}
            </span>
          )}
        </CardTitle>
      </CardHeader>

      <CardContent className="space-y-5 pt-5">
        {/* ── Input ──────────────────────────────────────────────── */}
        <div className="space-y-3">
          <form onSubmit={handleSubmit} className="flex flex-col sm:flex-row gap-2.5">
            <Input
              value={instruction}
              onChange={(e) => setInstruction(e.target.value)}
              placeholder='What would you like Hermes to do? (e.g. "Research the top 5 AI tools for 2026")'
              disabled={isProcessing}
              className="flex-1 h-11 bg-background/60 border-border text-sm placeholder:text-muted-foreground/50 focus-visible:border-havilah-gold focus-visible:ring-havilah-gold/20"
            />
            <Button
              type="submit"
              disabled={isProcessing || !instruction.trim()}
              className="h-11 px-5 bg-havilah-gold text-[#0f1117] font-semibold hover:bg-havilah-gold-light disabled:opacity-40 shadow-lg shadow-havilah-gold/20"
            >
              {isProcessing ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
              <span className="ml-2">{isProcessing ? "Working…" : "Send"}</span>
            </Button>
          </form>

          {/* Auto-approve toggle */}
          <div className="flex items-center gap-3 rounded-lg border border-border/60 bg-card/80 px-3.5 py-2.5">
            <div className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-md ${autoApprove ? "bg-violet-500/15 text-violet-400" : "bg-muted/60 text-muted-foreground"}`}>
              {autoApprove ? <Zap className="h-3.5 w-3.5" /> : <ShieldCheck className="h-3.5 w-3.5" />}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-xs font-medium text-foreground">Auto-Approve {autoApprove ? "ON" : "OFF"}</p>
              <p className="text-[11px] text-muted-foreground/70 leading-snug">
                {autoApprove ? "Runs continue automatically without manual sign-off." : "Runs pause when Hermes needs your approval."}
              </p>
            </div>
            <button
              type="button"
              role="switch"
              aria-checked={autoApprove}
              onClick={toggleAutoApprove}
              disabled={isProcessing}
              className={`relative shrink-0 h-5 w-9 rounded-full transition-colors disabled:opacity-40 ${autoApprove ? "bg-violet-500" : "bg-muted-foreground/25"}`}
            >
              <span className={`absolute top-0.5 left-0.5 h-4 w-4 rounded-full bg-white shadow-sm transition-transform ${autoApprove ? "translate-x-4" : "translate-x-0"}`} />
            </button>
          </div>
        </div>

        {/* ── Loading ─────────────────────────────────────────────── */}
        {isProcessing && (
          <div className="flex flex-col items-center justify-center py-12 gap-4">
            <div className="relative">
              <div className="absolute inset-0 animate-ping rounded-full bg-havilah-gold/20" />
              <div className="relative flex h-16 w-16 items-center justify-center rounded-full border border-havilah-gold/30 bg-havilah-gold/10">
                {runState === "auto_approving"
                  ? <Zap className="h-7 w-7 text-violet-400 animate-pulse" />
                  : <Sparkles className="h-7 w-7 text-havilah-gold animate-pulse" />}
              </div>
            </div>
            <div className="text-center space-y-1">
              <p className="text-sm font-medium text-foreground">
                {runState === "auto_approving" ? "Auto-approving and continuing…" : "Hermes is working on your request…"}
              </p>
              <p className="text-xs text-muted-foreground/50">This may take 10–30 seconds per step</p>
            </div>
          </div>
        )}

        {/* ── Approval gate ────────────────────────────────────────── */}
        <AnimatePresence>
          {runState === "awaiting_approval" && (
            <motion.div
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              className="rounded-xl border border-amber-500/30 bg-amber-500/5 p-4 sm:p-5 space-y-4"
            >
              <div className="flex items-start gap-3">
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-amber-500/15">
                  <ShieldCheck className="h-5 w-5 text-amber-400" />
                </div>
                <div className="flex-1 space-y-1">
                  <p className="text-sm font-semibold text-foreground">Approval required to continue</p>
                  <p className="text-xs text-muted-foreground/80 leading-relaxed">
                    Hermes has paused. Review the pending step in the execution trace below, then choose to continue or cancel.
                  </p>
                  {result?.approval_id && (
                    <p className="text-[10px] text-muted-foreground/50 font-mono pt-1">ID: {result.approval_id.slice(0, 12)}…</p>
                  )}
                </div>
              </div>
              <div className="flex gap-2 justify-end">
                <Button
                  onClick={handleReject}
                  disabled={actingOnApproval !== null}
                  variant="outline"
                  size="sm"
                  className="border-red-500/30 text-red-400 hover:bg-red-500/10"
                >
                  {actingOnApproval === "reject" ? <Loader2 className="h-3.5 w-3.5 mr-1.5 animate-spin" /> : <XCircle className="h-3.5 w-3.5 mr-1.5" />}
                  Reject
                </Button>
                <Button
                  onClick={handleApprove}
                  disabled={actingOnApproval !== null}
                  size="sm"
                  className="bg-emerald-600 text-white hover:bg-emerald-500 shadow-md shadow-emerald-600/20"
                >
                  {actingOnApproval === "approve" ? <Loader2 className="h-3.5 w-3.5 mr-1.5 animate-spin" /> : <CheckCircle2 className="h-3.5 w-3.5 mr-1.5" />}
                  Approve & Continue
                </Button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* ── Answer panel ─────────────────────────────────────────── */}
        <AnimatePresence>
          {!isProcessing && runState === "completed" && result?.summary && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              className="rounded-xl border border-havilah-gold/25 bg-havilah-gold/5 p-5 sm:p-6 space-y-3"
            >
              <div className="flex items-center gap-2.5 pb-2 border-b border-havilah-gold/15">
                <div className="flex h-6 w-6 items-center justify-center rounded bg-havilah-gold/20">
                  <CheckCircle2 className="h-3.5 w-3.5 text-havilah-gold" />
                </div>
                <span className="text-xs font-semibold uppercase tracking-widest text-havilah-gold">Result</span>
              </div>
              <div className="prose-answer">
                <Markdown>{result.summary}</Markdown>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* ── Error state ──────────────────────────────────────────── */}
        <AnimatePresence>
          {runState === "failed" && errorMsg && (
            <motion.div
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              className="rounded-xl border border-red-500/20 bg-red-500/5 p-4"
            >
              <div className="flex items-start gap-3">
                <AlertCircle className="h-5 w-5 text-red-400 shrink-0 mt-0.5" />
                <div>
                  <p className="text-sm font-medium text-foreground">Run failed</p>
                  <p className="text-xs text-muted-foreground/80 mt-0.5 leading-relaxed">{errorMsg}</p>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* ── Execution trace (collapsible) ────────────────────────── */}
        {!isProcessing && steps.length > 0 && (
          <div className="space-y-2">
            <button
              type="button"
              onClick={() => setTraceOpen((v) => !v)}
              className="flex w-full items-center gap-2 text-xs font-medium text-muted-foreground/70 hover:text-muted-foreground transition-colors py-1"
            >
              <ChevronRight className={`h-3.5 w-3.5 transition-transform ${traceOpen ? "rotate-90" : ""}`} />
              <span>{steps.length}-step execution trace</span>
              {result?.plan?.requires_any_approval ? (
                <Badge variant="outline" className="ml-auto text-[10px] border-amber-500/30 text-amber-400">Approval required</Badge>
              ) : (
                <Badge variant="outline" className="ml-auto text-[10px] border-emerald-500/30 text-emerald-500">Auto-executed</Badge>
              )}
            </button>

            <AnimatePresence>
              {traceOpen && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: "auto" }}
                  exit={{ opacity: 0, height: 0 }}
                  className="overflow-hidden"
                >
                  <div className="space-y-2 pt-1">
                    {result?.plan?.summary && (
                      <div className="rounded-lg border border-border/60 bg-muted/30 px-3.5 py-2.5">
                        <p className="text-xs text-muted-foreground/80 italic">{result.plan.summary}</p>
                      </div>
                    )}
                    {steps.map((step, idx) => {
                      const matchingResult = results.find((r) => r.step_number === step.step_number)
                      return (
                        <StepCard
                          key={idx}
                          step={step}
                          result={matchingResult}
                          isAwaiting={runState === "awaiting_approval" && step.approval_required && matchingResult != null}
                        />
                      )
                    })}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        )}

        {/* ── Footer: new instruction / idle hints ─────────────────── */}
        {runState !== "idle" && !isProcessing && (
          <div className="flex justify-center pt-1">
            <Button variant="ghost" size="sm" onClick={handleReset} className="h-8 text-xs text-muted-foreground hover:text-foreground">
              <RefreshCw className="h-3 w-3 mr-1.5" />
              New instruction
            </Button>
          </div>
        )}

        {runState === "idle" && (
          <div className="rounded-xl border border-dashed border-border/60 bg-background/30 p-4 space-y-2.5">
            <p className="text-[11px] font-semibold uppercase tracking-widest text-muted-foreground/60">
              Try asking Hermes
            </p>
            <div className="flex flex-wrap gap-2">
              {[
                "Research the top 5 AI coding tools in 2026",
                "Draft a project brief for a Q3 competitive audit",
                "Summarise the latest trends in EdTech for Havilah",
              ].map((ex) => (
                <button
                  key={ex}
                  type="button"
                  onClick={() => setInstruction(ex)}
                  className="rounded-full border border-border/60 bg-card px-3 py-1.5 text-xs text-muted-foreground hover:border-havilah-gold/40 hover:bg-havilah-gold/5 hover:text-foreground transition-all duration-200"
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

// ─── Run state badge ──────────────────────────────────────────────
function RunBadge({ state }: { state: RunState }) {
  const config: Record<string, { label: string; cls: string }> = {
    submitting:        { label: "Running",         cls: "border-havilah-gold/40 text-havilah-gold" },
    auto_approving:    { label: "Auto-approving",  cls: "border-violet-500/40 text-violet-400" },
    completed:         { label: "Completed",       cls: "border-emerald-500/30 text-emerald-400" },
    awaiting_approval: { label: "Needs approval",  cls: "border-amber-500/30 text-amber-400" },
    failed:            { label: "Failed",          cls: "border-red-500/30 text-red-400" },
  }
  const c = config[state]
  if (!c) return null
  return (
    <Badge variant="outline" className={`text-[10px] font-mono tracking-wide ${c.cls}`}>
      {c.label}
    </Badge>
  )
}

// ─── Step card ────────────────────────────────────────────────────
function StepCard({ step, result, isAwaiting }: { step: HermesStep; result?: HermesResult; isAwaiting?: boolean }) {
  const visual = getAgentVisual(step.agent)
  const Icon = visual.icon
  const riskColor = RISK_COLORS[step.risk_level] ?? RISK_COLORS.low
  const [expanded, setExpanded] = useState(false)
  const hasResult = Boolean(result?.output)
  const isFailed = result?.status === "failed"

  return (
    <motion.div
      initial={{ opacity: 0, x: -8 }}
      animate={{ opacity: 1, x: 0 }}
      className={`rounded-lg border bg-background/60 transition-colors ${
        isAwaiting ? "border-amber-500/40 bg-amber-500/5"
        : isFailed  ? "border-red-500/25"
        : "border-border/60 hover:border-havilah-gold/20"
      }`}
    >
      <div className="p-3 sm:p-3.5">
        <div className="flex items-start gap-3">
          <div
            className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg"
            style={{ backgroundColor: `${visual.color}15`, color: visual.color }}
          >
            <Icon className="h-3.5 w-3.5" />
          </div>

          <div className="flex-1 space-y-1.5 min-w-0">
            <p className="text-xs font-medium text-foreground/90 leading-snug">
              <span className="text-muted-foreground/40 font-mono mr-1.5">#{step.step_number}</span>
              {step.action}
            </p>
            <div className="flex flex-wrap items-center gap-1">
              <Badge variant="outline" className="text-[10px] capitalize border-border/60 text-muted-foreground/80">
                {visual.label}
              </Badge>
              <Badge variant="outline" className={`text-[10px] capitalize ${riskColor}`}>
                {step.risk_level}
              </Badge>
              {step.approval_required && (
                <Badge variant="outline" className="text-[10px] border-amber-500/30 text-amber-400 bg-amber-500/5">
                  <ShieldCheck className="h-2.5 w-2.5 mr-1" />Approval
                </Badge>
              )}
              {result?.status === "success" && (
                <Badge variant="outline" className="text-[10px] border-emerald-500/30 text-emerald-400 bg-emerald-500/5">
                  <CheckCircle2 className="h-2.5 w-2.5 mr-1" />Done
                </Badge>
              )}
              {isAwaiting && (
                <Badge variant="outline" className="text-[10px] border-amber-500/40 text-amber-400 bg-amber-500/8 animate-pulse">
                  <Clock className="h-2.5 w-2.5 mr-1" />Paused
                </Badge>
              )}
              {isFailed && (
                <Badge variant="outline" className="text-[10px] border-red-500/30 text-red-400 bg-red-500/5">
                  <XCircle className="h-2.5 w-2.5 mr-1" />Failed
                </Badge>
              )}
            </div>

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

// ─── Result output (collapsible) ──────────────────────────────────
function ResultOutput({ text, tokens, expanded, onToggle }: { text: string; tokens?: number; expanded: boolean; onToggle: () => void }) {
  const isLong = text.length > 400
  const preview = isLong && !expanded ? text.slice(0, 400) + "…" : text

  return (
    <div className="rounded-md bg-muted/30 border border-border/50 overflow-hidden mt-2">
      <div className="px-3 py-2.5">
        <div className="flex items-center gap-1.5 mb-2">
          <Cpu className="h-2.5 w-2.5 text-muted-foreground/40" />
          <span className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground/40">Output</span>
          {tokens != null && (
            <span className="ml-auto text-[10px] text-muted-foreground/35 font-mono">{tokens} tok</span>
          )}
        </div>
        <div className="text-xs leading-relaxed text-foreground/75 prose-answer [&_h2]:text-xs [&_h3]:text-xs [&_p]:mb-1.5 [&_ul]:pl-3 [&_li]:mb-0.5">
          <Markdown>{preview}</Markdown>
        </div>
      </div>
      {isLong && (
        <button
          type="button"
          onClick={onToggle}
          className="w-full flex items-center justify-center gap-1.5 py-1.5 text-[10px] text-muted-foreground/50 hover:text-muted-foreground hover:bg-muted/40 transition-colors border-t border-border/40"
        >
          <ChevronRight className={`h-3 w-3 transition-transform ${expanded ? "rotate-90" : ""}`} />
          {expanded ? "Show less" : `Show full output (${text.length} chars)`}
        </button>
      )}
    </div>
  )
}
