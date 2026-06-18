"use client"

import { useState, useCallback } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import {
  MessageSquare,
  LayoutGrid,
  Send,
  ShieldCheck,
  Play,
  Database,
  CheckCircle2,
  Loader2,
  Sparkles,
  XCircle,
  AlertCircle,
  RefreshCw,
} from "lucide-react"
import { motion, AnimatePresence } from "framer-motion"
import { toast } from "sonner"
import {
  havilahApi,
  HermesInstructionResponse,
  HermesStep,
  isApiConfigured,
  ApiError,
} from "@/lib/havilah-api"

// Map agent name → icon + color
const AGENT_VISUALS: Record<string, { icon: typeof MessageSquare; color: string }> = {
  planner:   { icon: LayoutGrid,    color: "#60a5fa" },
  executive: { icon: ShieldCheck,   color: "#d4a853" },
  research:  { icon: MessageSquare, color: "#34d399" },
  writing:   { icon: MessageSquare, color: "#f472b6" },
  meeting:   { icon: MessageSquare, color: "#a78bfa" },
  reviewer:  { icon: ShieldCheck,   color: "#fb7185" },
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
  low: "border-emerald-500/30 text-emerald-500",
  medium: "border-amber-500/30 text-amber-500",
  high: "border-red-500/30 text-red-500",
  critical: "border-purple-500/30 text-purple-500",
}

type RunState = "idle" | "submitting" | "completed" | "awaiting_approval" | "failed"

export function HermesCommand() {
  const [instruction, setInstruction] = useState("")
  const [runState, setRunState] = useState<RunState>("idle")
  const [result, setResult] = useState<HermesInstructionResponse | null>(null)
  const [errorMsg, setErrorMsg] = useState<string>("")
  const [actingOnApproval, setActingOn] = useState<"approve" | "reject" | null>(null)

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

      if (resp.status === "awaiting_approval" && resp.awaiting_approval) {
        setRunState("awaiting_approval")
        toast.info("Approval needed", {
          description: `Step ${resp.awaiting_approval.step.step_number}: ${resp.awaiting_approval.step.action}`,
        })
      } else if (resp.status === "completed") {
        setRunState("completed")
        toast.success("Hermes run completed", {
          description: resp.summary ?? "See result below.",
        })
      } else if (resp.status === "failed") {
        setRunState("failed")
        setErrorMsg(resp.message || "Hermes run failed.")
        toast.error("Hermes run failed")
      } else {
        // planning, executing, etc. — treat as completed for display
        setRunState("completed")
      }
    } catch (err: any) {
      const msg = err instanceof ApiError ? err.message : String(err)
      setErrorMsg(msg)
      setRunState("failed")
      toast.error("Hermes call failed", { description: msg })
    }
  }, [instruction, runState])

  const handleApprove = async () => {
    if (!result?.run_id) return
    setActingOn("approve")
    try {
      await havilahApi.approve(result.run_id, "Approved via dashboard")
      toast.success("Approved", { description: "Hermes is continuing the run." })
      setRunState("completed")
      // Optionally re-fetch run state — for now just flip the local state
    } catch (e: any) {
      const msg = e instanceof ApiError ? e.message : String(e)
      toast.error("Approve failed", { description: msg })
    } finally {
      setActingOn(null)
    }
  }

  const handleReject = async () => {
    if (!result?.run_id) return
    setActingOn("reject")
    try {
      await havilahApi.reject(result.run_id, "Rejected via dashboard")
      toast.error("Rejected", { description: "Hermes run has been cancelled." })
      setRunState("failed")
      setErrorMsg("Run rejected by user.")
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

  const isProcessing = runState === "submitting"
  const steps = result?.plan?.steps ?? []

  return (
    <Card className="border-havilah-gold/20 bg-card gold-border-glow">
      <CardHeader>
        <CardTitle className="flex items-center justify-between text-foreground">
          <span className="flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-havilah-gold" />
            Hermes Command Center
            {result && (
              <Badge
                variant="outline"
                className={`text-[10px] ${
                  runState === "completed"
                    ? "border-emerald-500/30 text-emerald-500"
                    : runState === "awaiting_approval"
                    ? "border-amber-500/30 text-amber-500"
                    : runState === "failed"
                    ? "border-red-500/30 text-red-500"
                    : "border-havilah-gold/30 text-havilah-gold"
                }`}
              >
                {runState.toUpperCase().replace("_", " ")}
              </Badge>
            )}
          </span>
          {result?.run_id && (
            <Badge variant="outline" className="font-mono text-[10px] text-muted-foreground">
              {result.run_id.slice(0, 8)}…
            </Badge>
          )}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Command Input */}
        <form onSubmit={handleSubmit} className="flex gap-2">
          <Input
            value={instruction}
            onChange={(e) => setInstruction(e.target.value)}
            placeholder="Enter natural language instruction... (e.g., 'Research the top 5 AI coding tools in 2026')"
            disabled={isProcessing}
            className="flex-1 border-border bg-background placeholder:text-muted-foreground focus-visible:border-havilah-gold focus-visible:ring-havilah-gold/30"
          />
          <Button
            type="submit"
            disabled={isProcessing || !instruction.trim()}
            className="bg-gradient-to-r from-havilah-gold to-havilah-gold-dark text-white shadow-lg shadow-havilah-gold/25 hover:shadow-havilah-gold/40 hover:brightness-110 disabled:opacity-50"
          >
            {isProcessing ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Send className="h-4 w-4" />
            )}
            <span className="hidden sm:inline">
              {isProcessing ? "Submitting…" : "Submit to Hermes"}
            </span>
          </Button>
        </form>

        {/* Loading state during submission */}
        {isProcessing && (
          <div className="flex flex-col items-center justify-center py-8 gap-3">
            <div className="relative">
              <div className="absolute inset-0 animate-ping rounded-full bg-havilah-gold/30" />
              <div className="relative flex h-12 w-12 items-center justify-center rounded-full bg-havilah-gold/20">
                <Sparkles className="h-6 w-6 text-havilah-gold animate-pulse" />
              </div>
            </div>
            <p className="text-sm text-muted-foreground">
              Hermes is planning your instruction through 10 agents…
            </p>
            <p className="text-xs text-muted-foreground/60">
              This calls GPT-4o and may take 10–30 seconds.
            </p>
          </div>
        )}

        {/* Plan visualization */}
        {!isProcessing && steps.length > 0 && (
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
                Orchestration Plan
              </p>
              <span className="text-xs text-muted-foreground">
                {steps.length} step{steps.length !== 1 ? "s" : ""} •{" "}
                {result?.plan?.requires_any_approval ? "Approval required" : "No approval needed"}
              </span>
            </div>

            {/* Plan summary */}
            {result?.plan?.summary && (
              <div className="rounded-lg border border-havilah-gold/20 bg-havilah-gold/5 p-3">
                <p className="text-sm text-foreground/90 italic">
                  &ldquo;{result.plan.summary}&rdquo;
                </p>
              </div>
            )}

            {/* Steps */}
            <div className="space-y-2">
              {steps.map((step, idx) => (
                <StepCard key={idx} step={step} />
              ))}
            </div>
          </div>
        )}

        {/* Approval actions */}
        {runState === "awaiting_approval" && result?.awaiting_approval && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="rounded-lg border border-amber-500/30 bg-amber-500/5 p-4 space-y-3"
          >
            <div className="flex items-start gap-2">
              <ShieldCheck className="mt-0.5 h-5 w-5 shrink-0 text-amber-500" />
              <div className="flex-1">
                <p className="text-sm font-medium text-foreground">
                  Approval required for Step {result.awaiting_approval.step.step_number}
                </p>
                <p className="text-xs text-muted-foreground mt-1">
                  {result.awaiting_approval.step.action}
                </p>
                <p className="text-xs text-muted-foreground/70 mt-1 font-mono">
                  Approval ID: {result.awaiting_approval.approval_id.slice(0, 8)}…
                </p>
              </div>
            </div>
            <div className="flex gap-2">
              <Button
                onClick={handleApprove}
                disabled={actingOnApproval !== null}
                className="bg-emerald-600 text-white hover:bg-emerald-700"
              >
                {actingOnApproval === "approve" ? (
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                ) : (
                  <CheckCircle2 className="h-4 w-4 mr-2" />
                )}
                Approve & Continue
              </Button>
              <Button
                onClick={handleReject}
                disabled={actingOnApproval !== null}
                variant="outline"
                className="border-red-500/30 text-red-500 hover:bg-red-500/10"
              >
                {actingOnApproval === "reject" ? (
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                ) : (
                  <XCircle className="h-4 w-4 mr-2" />
                )}
                Reject
              </Button>
            </div>
          </motion.div>
        )}

        {/* Result summary */}
        <AnimatePresence>
          {runState === "completed" && result?.summary && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              className="rounded-lg border border-emerald-500/20 bg-emerald-500/5 p-3"
            >
              <div className="flex items-start gap-2">
                <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-emerald-500" />
                <div className="flex-1">
                  <p className="text-sm font-medium text-foreground mb-1">Run completed</p>
                  <p className="text-sm text-foreground/90 whitespace-pre-wrap">{result.summary}</p>
                  {result.results && result.results.length > 0 && (
                    <details className="mt-2">
                      <summary className="text-xs text-muted-foreground cursor-pointer hover:text-foreground">
                        View {result.results.length} raw result(s)
                      </summary>
                      <pre className="mt-2 text-xs bg-background/50 rounded p-2 overflow-auto max-h-48">
                        {result.results.map((r, i) => `[${i + 1}] ${r}`).join("\n\n")}
                      </pre>
                    </details>
                  )}
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Error state */}
        <AnimatePresence>
          {runState === "failed" && errorMsg && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              className="rounded-lg border border-red-500/20 bg-red-500/5 p-3"
            >
              <div className="flex items-start gap-2">
                <AlertCircle className="mt-0.5 h-4 w-4 shrink-0 text-red-500" />
                <div className="flex-1">
                  <p className="text-sm font-medium text-foreground mb-1">Run failed</p>
                  <p className="text-sm text-foreground/80">{errorMsg}</p>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Reset button after run */}
        {runState !== "idle" && runState !== "submitting" && (
          <div className="flex justify-center">
            <Button variant="ghost" size="sm" onClick={handleReset}>
              <RefreshCw className="h-3 w-3 mr-2" />
              New instruction
            </Button>
          </div>
        )}

        {/* Hint when idle */}
        {runState === "idle" && (
          <div className="rounded-lg border border-dashed border-border bg-background/50 p-4">
            <p className="text-xs text-muted-foreground text-center">
              Try:{" "}
              <span className="text-foreground/80">
                &ldquo;Research the top 5 AI coding tools in 2026&rdquo;
              </span>{" "}
              or{" "}
              <span className="text-foreground/80">
                &ldquo;Create a project for Q3 competitive audit&rdquo;
              </span>
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

// ─── Step Card subcomponent ────────────────────────────────────
function StepCard({ step }: { step: HermesStep }) {
  const visual = getAgentVisual(step.agent)
  const Icon = visual.icon
  const riskColor = RISK_COLORS[step.risk_level] ?? RISK_COLORS.low

  return (
    <motion.div
      initial={{ opacity: 0, x: -10 }}
      animate={{ opacity: 1, x: 0 }}
      className="rounded-lg border border-border bg-background p-3"
    >
      <div className="flex items-start gap-3">
        {/* Agent icon */}
        <div
          className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg"
          style={{ backgroundColor: `${visual.color}15`, color: visual.color }}
        >
          <Icon className="h-4 w-4" />
        </div>

        {/* Step content */}
        <div className="flex-1 space-y-1.5 min-w-0">
          <div className="flex items-start justify-between gap-2 flex-wrap">
            <p className="text-sm font-medium text-foreground">
              <span className="text-muted-foreground/70 text-xs mr-2">
                #{step.step_number}
              </span>
              {step.action}
            </p>
            <div className="flex items-center gap-1.5 shrink-0">
              <Badge variant="outline" className="text-[10px] capitalize">
                {step.agent}
              </Badge>
              <Badge variant="outline" className={`text-[10px] capitalize ${riskColor}`}>
                {step.risk_level}
              </Badge>
              {step.approval_required && (
                <Badge variant="outline" className="text-[10px] border-amber-500/30 text-amber-500">
                  <ShieldCheck className="h-3 w-3 mr-1" />
                  Approval
                </Badge>
              )}
            </div>
          </div>
          {step.expected_output && (
            <p className="text-xs text-muted-foreground">
              Expected: {step.expected_output}
            </p>
          )}
          {step.result && (
            <div className="mt-2 text-xs bg-muted/30 rounded p-2">
              <p className="text-foreground/80 whitespace-pre-wrap">{step.result}</p>
            </div>
          )}
        </div>
      </div>
    </motion.div>
  )
}
