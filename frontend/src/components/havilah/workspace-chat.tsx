"use client"

import { useState, useCallback, useEffect, useRef } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import {
  Sparkles,
  Send,
  Loader2,
  CheckCircle2,
  XCircle,
  AlertCircle,
  RefreshCw,
  Zap,
  ShieldCheck,
  Clock,
  Copy,
  Save,
  ChevronRight,
  MessageSquare,
  Crown,
  type LucideIcon,
} from "lucide-react"
import Markdown from "react-markdown"
import { motion, AnimatePresence } from "framer-motion"
import { toast } from "sonner"
import {
  havilahApi,
  HermesInstructionResponse,
  HermesResult,
  isApiConfigured,
  ApiError,
} from "@/lib/havilah-api"

// ─── Types ────────────────────────────────────────────────────────────
interface Message {
  id: string
  role: "user" | "assistant"
  content: string
  timestamp: number
  runId?: string
  mode?: "direct" | "orchestrated"
  status?: "completed" | "awaiting_approval" | "failed"
  results?: HermesResult[]
  approvalId?: string
  elapsedSeconds?: number
}

// ─── Agent visual registry ────────────────────────────────────────────
const AGENT_VISUALS: Record<string, { icon: LucideIcon; color: string; label: string }> = {
  planner:   { icon: MessageSquare, color: "#2563eb", label: "Planner" },
  executive: { icon: Crown,         color: "#b8821e", label: "Executive" },
  research:  { icon: Sparkles,      color: "#059669", label: "Research" },
  writing:   { icon: MessageSquare, color: "#db2777", label: "Writing" },
  meeting:   { icon: MessageSquare, color: "#7c3aed", label: "Meeting" },
  reviewer:  { icon: ShieldCheck,   color: "#0d9488", label: "Reviewer" },
  critic:    { icon: AlertCircle,   color: "#ea580c", label: "Critic" },
  memory:    { icon: Save,          color: "#4f46e5", label: "Memory" },
  learning:  { icon: Sparkles,      color: "#16a34a", label: "Learning" },
  approval:  { icon: ShieldCheck,   color: "#ca8a04", label: "Approval" },
}

function getAgentVisual(name?: string) {
  if (!name) return { icon: Sparkles, color: "#64748b", label: "Agent" }
  return AGENT_VISUALS[name.toLowerCase()] ?? { icon: Sparkles, color: "#64748b", label: name }
}

function formatTokens(tokens?: HermesResult["tokens"]): string | null {
  if (tokens == null) return null
  if (typeof tokens === "number") return `${tokens} tok`
  if (typeof tokens === "object") {
    const t = tokens.total ?? ((tokens.prompt ?? 0) + (tokens.completion ?? 0))
    return `${t} tok`
  }
  return null
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
  return r.output ?? r.error ?? r.action ?? ""
}

const SUGGESTIONS = [
  "What's the difference between OKR and KPI?",
  "Draft a Q3 priorities memo for my leadership team",
  "Summarize the key risks of launching without beta testing",
  "Compare Slack vs Microsoft Teams for a 50-person remote team",
]

// ─── Main component ──────────────────────────────────────────────────
export function WorkspaceChat() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState("")
  const [isProcessing, setIsProcessing] = useState(false)
  const [autoApprove, setAutoApprove] = useState(false)
  const autoApproveRef = useRef(false)
  const scrollRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  // Restore auto-approve preference
  useEffect(() => {
    if (typeof window === "undefined") return
    const cached = localStorage.getItem("havilah_auto_approve") === "true"
    setAutoApprove(cached)
    autoApproveRef.current = cached
  }, [])

  // Auto-scroll to bottom on new message
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [messages, isProcessing])

  // ── Submit ─────────────────────────────────────────────────────
  const handleSubmit = useCallback(async (e?: React.FormEvent) => {
    e?.preventDefault()
    const trimmed = input.trim()
    if (!trimmed || isProcessing) return

    if (!isApiConfigured) {
      toast.error("Backend not configured", {
        description: "Set NEXT_PUBLIC_HAVILAH_API_URL in Vercel env vars.",
      })
      return
    }

    const userMsg: Message = {
      id: `u-${Date.now()}`,
      role: "user",
      content: trimmed,
      timestamp: Date.now(),
    }
    setMessages((prev) => [...prev, userMsg])
    setInput("")
    setIsProcessing(true)

    try {
      const resp = await havilahApi.instruct(trimmed, "dashboard")
      const assistantMsg: Message = {
        id: `a-${Date.now()}`,
        role: "assistant",
        content: resp.summary || getResultText(resp.results?.[0]) || "(no output)",
        timestamp: Date.now(),
        runId: resp.run_id,
        mode: (resp as any).mode === "direct" ? "direct" : "orchestrated",
        status: needsApproval(resp) ? "awaiting_approval" : resp.status === "failed" ? "failed" : "completed",
        results: resp.results ?? [],
        approvalId: resp.approval_id,
        elapsedSeconds: resp.elapsed_seconds,
      }
      setMessages((prev) => [...prev, assistantMsg])

      // Auto-approve if enabled and approval needed
      if (needsApproval(resp) && autoApproveRef.current && resp.run_id) {
        setTimeout(() => doApprove(resp.run_id, assistantMsg.id), 300)
      }
    } catch (err: any) {
      const msg = err instanceof ApiError ? err.message : String(err)
      setMessages((prev) => [...prev, {
        id: `a-${Date.now()}`,
        role: "assistant",
        content: `**Error:** ${msg}`,
        timestamp: Date.now(),
        status: "failed",
      }])
      toast.error("Request failed", { description: msg })
    } finally {
      setIsProcessing(false)
    }
  }, [input, isProcessing])

  // ── Approve ────────────────────────────────────────────────────
  const doApprove = useCallback(async (runId: string, msgId: string, isAuto = false) => {
    try {
      const resp = await havilahApi.approve(runId, isAuto ? "Auto-approved" : "Approved via dashboard")
      if (resp && typeof resp === "object" && "run_id" in resp) {
        const updated: Partial<Message> = {
          content: resp.summary || getResultText(resp.results?.[0]) || "(no output)",
          status: needsApproval(resp as HermesInstructionResponse) ? "awaiting_approval" : "completed",
          results: (resp as HermesInstructionResponse).results ?? [],
          mode: (resp as any).mode === "direct" ? "direct" : "orchestrated",
          elapsedSeconds: (resp as HermesInstructionResponse).elapsed_seconds,
        }
        setMessages((prev) => prev.map((m) => m.id === msgId ? { ...m, ...updated } : m))

        // If still needs approval and auto-approve is on, continue
        if (needsApproval(resp as HermesInstructionResponse) && autoApproveRef.current) {
          setTimeout(() => doApprove(runId, msgId, true), 300)
        }
      }
    } catch (err: any) {
      toast.error("Approve failed", { description: err instanceof ApiError ? err.message : String(err) })
    }
  }, [])

  const toggleAutoApprove = useCallback(() => {
    const next = !autoApprove
    setAutoApprove(next)
    autoApproveRef.current = next
    try { localStorage.setItem("havilah_auto_approve", String(next)) } catch {}
    toast[next ? "success" : "info"](
      next ? "Auto-Approve enabled" : "Auto-Approve disabled",
      { description: next ? "Runs continue automatically." : "Approval-required runs pause." }
    )
  }, [autoApprove])

  // ── Copy to clipboard ──────────────────────────────────────────
  const handleCopy = useCallback((text: string) => {
    navigator.clipboard.writeText(text).then(() => {
      toast.success("Copied to clipboard")
    }).catch(() => {
      toast.error("Copy failed")
    })
  }, [])

  // ── Save as memory ─────────────────────────────────────────────
  const handleSaveMemory = useCallback(async (text: string) => {
    try {
      await havilahApi.createMemory({
        title: `Saved from conversation (${new Date().toLocaleString()})`,
        content: text,
        type: "operational",
        importance: "medium",
      })
      toast.success("Saved to memory", { description: "You can find it in Memory Explorer." })
    } catch (e: any) {
      toast.error("Save failed", { description: e instanceof ApiError ? e.message : String(e) })
    }
  }, [])

  return (
    <Card className="border-border bg-card shadow-sm flex flex-col h-[calc(100vh-12rem)] min-h-[600px]">
      {/* ── Header ─────────────────────────────────────────────── */}
      <CardHeader className="pb-3 border-b border-border/60 shrink-0">
        <CardTitle className="flex items-center justify-between gap-3">
          <span className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-havilah-gold/15">
              <Sparkles className="h-4 w-4 text-havilah-gold" />
            </div>
            <span className="text-base font-semibold text-foreground">Hermes</span>
            <Badge variant="outline" className="text-[10px] border-emerald-500/30 text-emerald-600">
              GPT-4o
            </Badge>
          </span>
          <button
            type="button"
            role="switch"
            aria-checked={autoApprove}
            onClick={toggleAutoApprove}
            disabled={isProcessing}
            className={`flex items-center gap-2 rounded-lg border px-3 py-1.5 text-xs font-medium transition-colors disabled:opacity-50 ${
              autoApprove
                ? "border-violet-500/40 bg-violet-500/10 text-violet-600"
                : "border-border bg-background text-muted-foreground"
            }`}
          >
            <Zap className={`h-3 w-3 ${autoApprove ? "fill-violet-500" : ""}`} />
            Auto-Approve {autoApprove ? "ON" : "OFF"}
          </button>
        </CardTitle>
      </CardHeader>

      {/* ── Conversation thread ────────────────────────────────── */}
      <CardContent className="flex-1 overflow-hidden p-0">
        <div ref={scrollRef} className="h-full overflow-y-auto px-4 sm:px-6 py-4">
          {messages.length === 0 ? (
            <EmptyState onPick={(s) => setInput(s)} />
          ) : (
            <div className="space-y-6 max-w-3xl mx-auto">
              <AnimatePresence mode="popLayout">
                {messages.map((msg) => (
                  <motion.div
                    key={msg.id}
                    layout
                    initial={{ opacity: 0, y: 8 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0 }}
                    className={msg.role === "user" ? "flex justify-end" : ""}
                  >
                    {msg.role === "user" ? (
                      <UserBubble content={msg.content} timestamp={msg.timestamp} />
                    ) : (
                      <AssistantMessage
                        msg={msg}
                        onCopy={handleCopy}
                        onSaveMemory={handleSaveMemory}
                        onApprove={(runId) => doApprove(runId, msg.id)}
                        isProcessing={isProcessing}
                      />
                    )}
                  </motion.div>
                ))}
              </AnimatePresence>
              {isProcessing && (
                <motion.div
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="flex gap-3 max-w-3xl mx-auto"
                >
                  <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-havilah-gold/15">
                    <Loader2 className="h-4 w-4 text-havilah-gold animate-spin" />
                  </div>
                  <div className="flex items-center gap-2 pt-2">
                    <span className="text-sm text-muted-foreground">Working on it…</span>
                    <span className="flex gap-1">
                      <span className="h-1.5 w-1.5 rounded-full bg-havilah-gold/40 animate-pulse" style={{ animationDelay: "0ms" }} />
                      <span className="h-1.5 w-1.5 rounded-full bg-havilah-gold/40 animate-pulse" style={{ animationDelay: "150ms" }} />
                      <span className="h-1.5 w-1.5 rounded-full bg-havilah-gold/40 animate-pulse" style={{ animationDelay: "300ms" }} />
                    </span>
                  </div>
                </motion.div>
              )}
            </div>
          )}
        </div>
      </CardContent>

      {/* ── Input bar ──────────────────────────────────────────── */}
      <div className="border-t border-border/60 p-3 sm:p-4 shrink-0 bg-card/50">
        <form onSubmit={handleSubmit} className="max-w-3xl mx-auto flex gap-2">
          <Input
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask Hermes anything, or describe what you need done…"
            disabled={isProcessing}
            className="flex-1 h-11 bg-background border-border text-sm placeholder:text-muted-foreground/50 focus-visible:border-havilah-gold focus-visible:ring-havilah-gold/20"
          />
          <Button
            type="submit"
            disabled={isProcessing || !input.trim()}
            className="h-11 px-5 bg-havilah-gold text-white font-semibold hover:bg-havilah-gold-light disabled:opacity-40 shadow-md shadow-havilah-gold/20"
          >
            {isProcessing ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
            <span className="ml-2 hidden sm:inline">{isProcessing ? "Working…" : "Send"}</span>
          </Button>
        </form>
      </div>
    </Card>
  )
}

// ─── Empty state ──────────────────────────────────────────────────────
function EmptyState({ onPick }: { onPick: (s: string) => void }) {
  return (
    <div className="flex flex-col items-center justify-center h-full gap-6 text-center py-12">
      <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-havilah-gold/10">
        <Sparkles className="h-8 w-8 text-havilah-gold" />
      </div>
      <div className="space-y-2 max-w-md">
        <h2 className="text-xl font-semibold text-foreground">What can I do for you?</h2>
        <p className="text-sm text-muted-foreground">
          Ask a question, request a draft, or describe a task. Simple requests get instant answers;
          complex ones go through the full agent orchestration.
        </p>
      </div>
      <div className="flex flex-wrap gap-2 justify-center max-w-2xl">
        {SUGGESTIONS.map((s) => (
          <button
            key={s}
            type="button"
            onClick={() => onPick(s)}
            className="rounded-full border border-border/70 bg-background px-3.5 py-2 text-xs text-muted-foreground hover:border-havilah-gold/40 hover:bg-havilah-gold/5 hover:text-foreground transition-all duration-200"
          >
            {s}
          </button>
        ))}
      </div>
    </div>
  )
}

// ─── User message bubble ──────────────────────────────────────────────
function UserBubble({ content, timestamp }: { content: string; timestamp: number }) {
  return (
    <div className="max-w-[80%] rounded-2xl rounded-tr-sm bg-havilah-gold/15 border border-havilah-gold/20 px-4 py-2.5">
      <p className="text-sm text-foreground leading-relaxed whitespace-pre-wrap">{content}</p>
      <p className="text-[10px] text-muted-foreground/60 mt-1 text-right">
        {new Date(timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
      </p>
    </div>
  )
}

// ─── Assistant message ────────────────────────────────────────────────
function AssistantMessage({
  msg,
  onCopy,
  onSaveMemory,
  onApprove,
  isProcessing,
}: {
  msg: Message
  onCopy: (text: string) => void
  onSaveMemory: (text: string) => void
  onApprove: (runId: string) => void
  isProcessing: boolean
}) {
  const [showSteps, setShowSteps] = useState(false)
  const hasResults = msg.results && msg.results.length > 0
  const fullText = msg.results && msg.results.length > 0
    ? msg.results.map((r) => getResultText(r)).join("\n\n---\n\n")
    : msg.content

  return (
    <div className="max-w-[92%] sm:max-w-[85%]">
      <div className="flex gap-3">
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-card border border-border/60">
          {msg.mode === "direct" ? (
            <Zap className="h-4 w-4 text-havilah-gold" />
          ) : (
            <Sparkles className="h-4 w-4 text-havilah-gold" />
          )}
        </div>
        <div className="flex-1 min-w-0 space-y-2">
          {/* Header line */}
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-xs font-semibold text-foreground">
              {msg.mode === "direct" ? "Direct answer" : "Hermes"}
            </span>
            {msg.status === "completed" && (
              <Badge variant="outline" className="text-[9px] border-emerald-500/30 text-emerald-600 h-4 px-1.5">
                <CheckCircle2 className="h-2.5 w-2.5 mr-0.5" />Done
              </Badge>
            )}
            {msg.status === "awaiting_approval" && (
              <Badge variant="outline" className="text-[9px] border-amber-500/40 text-amber-600 h-4 px-1.5 animate-pulse">
                <Clock className="h-2.5 w-2.5 mr-0.5" />Needs approval
              </Badge>
            )}
            {msg.status === "failed" && (
              <Badge variant="outline" className="text-[9px] border-red-500/30 text-red-600 h-4 px-1.5">
                <XCircle className="h-2.5 w-2.5 mr-0.5" />Failed
              </Badge>
            )}
            {msg.elapsedSeconds != null && (
              <span className="text-[10px] text-muted-foreground/50 font-mono">
                {msg.elapsedSeconds.toFixed(1)}s
              </span>
            )}
          </div>

          {/* Main content — rendered markdown */}
          <div className="rounded-2xl rounded-tl-sm border border-border/60 bg-background px-4 py-3">
            <div className="prose-answer max-w-none text-foreground/90 text-sm [&_h1]:text-base [&_h1]:font-semibold [&_h1]:mt-3 [&_h1]:mb-1.5 [&_h2]:text-sm [&_h2]:font-semibold [&_h2]:mt-2.5 [&_h2]:mb-1 [&_h3]:text-[13px] [&_h3]:font-semibold [&_h3]:mt-2 [&_h3]:mb-1 [&_p]:mb-2 [&_p]:leading-relaxed [&_ul]:my-1.5 [&_ul]:pl-5 [&_ol]:my-1.5 [&_ol]:pl-5 [&_li]:mb-1 [&_li]:leading-relaxed [&_code]:text-[11px] [&_code]:bg-muted [&_code]:px-1 [&_code]:py-0.5 [&_code]:rounded [&_pre]:bg-muted [&_pre]:p-3 [&_pre]:rounded-md [&_pre]:overflow-x-auto [&_pre_code]:bg-transparent [&_pre_code]:p-0 [&_blockquote]:border-l-2 [&_blockquote]:border-havilah-gold/40 [&_blockquote]:pl-3 [&_blockquote]:text-muted-foreground [&_hr]:my-3 [&_hr]:border-border [&_a]:text-havilah-gold [&_a]:underline [&_strong]:font-semibold [&_table]:w-full [&_th]:border [&_th]:border-border [&_th]:px-2 [&_th]:py-1 [&_th]:bg-muted [&_td]:border [&_td]:border-border [&_td]:px-2 [&_td]:py-1">
              <Markdown>{msg.content}</Markdown>
            </div>

            {/* Action bar */}
            <div className="flex items-center gap-1 mt-2 pt-2 border-t border-border/40">
              <ActionButton
                onClick={() => onCopy(fullText)}
                icon={Copy}
                label="Copy"
              />
              <ActionButton
                onClick={() => onSaveMemory(fullText)}
                icon={Save}
                label="Save"
              />
              {hasResults && msg.results!.length > 1 && (
                <ActionButton
                  onClick={() => setShowSteps((v) => !v)}
                  icon={ChevronRight}
                  label={`${msg.results!.length} steps`}
                  active={showSteps}
                />
              )}
            </div>
          </div>

          {/* Approval gate */}
          {msg.status === "awaiting_approval" && msg.runId && (
            <div className="rounded-xl border border-amber-500/30 bg-amber-500/5 p-3 flex items-center justify-between gap-3">
              <div className="flex items-center gap-2 min-w-0">
                <ShieldCheck className="h-4 w-4 text-amber-600 shrink-0" />
                <span className="text-xs text-foreground/80">Approval required to continue</span>
              </div>
              <Button
                size="sm"
                onClick={() => onApprove(msg.runId!)}
                disabled={isProcessing}
                className="h-7 px-3 bg-emerald-600 text-white hover:bg-emerald-700 text-xs"
              >
                {isProcessing ? <Loader2 className="h-3 w-3 mr-1 animate-spin" /> : <CheckCircle2 className="h-3 w-3 mr-1" />}
                Approve
              </Button>
            </div>
          )}

          {/* Collapsible step trace for orchestrated runs */}
          {showSteps && hasResults && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              className="space-y-2 pt-1"
            >
              {msg.results!.map((r, idx) => (
                <StepResult key={idx} result={r} />
              ))}
            </motion.div>
          )}
        </div>
      </div>
    </div>
  )
}

// ─── Action button ────────────────────────────────────────────────────
function ActionButton({
  onClick,
  icon: Icon,
  label,
  active,
}: {
  onClick: () => void
  icon: LucideIcon
  label: string
  active?: boolean
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`flex items-center gap-1.5 px-2 py-1 rounded text-[11px] font-medium transition-colors ${
        active
          ? "bg-havilah-gold/10 text-havilah-gold"
          : "text-muted-foreground/60 hover:text-foreground hover:bg-muted/50"
      }`}
    >
      <Icon className={`h-3 w-3 ${active ? "rotate-90" : ""}`} />
      {label}
    </button>
  )
}

// ─── Step result (in expanded trace) ──────────────────────────────────
function StepResult({ result }: { result: HermesResult }) {
  const visual = getAgentVisual(result.agent)
  const Icon = visual.icon
  const text = getResultText(result)
  const isFailed = result.status === "failed"
  const tokenStr = formatTokens(result.tokens)

  return (
    <div
      className={`rounded-lg border bg-card overflow-hidden ${
        isFailed ? "border-red-500/30" : "border-border/60"
      }`}
    >
      <div className="px-3 py-2 flex items-center gap-2 border-b border-border/40 bg-muted/20">
        <div
          className="flex h-6 w-6 shrink-0 items-center justify-center rounded"
          style={{ backgroundColor: `${visual.color}15`, color: visual.color }}
        >
          <Icon className="h-3 w-3" />
        </div>
        <span className="text-xs font-medium text-foreground truncate">{visual.label}</span>
        {result.status === "success" && (
          <CheckCircle2 className="h-3 w-3 text-emerald-500 ml-auto shrink-0" />
        )}
        {isFailed && <XCircle className="h-3 w-3 text-red-500 ml-auto shrink-0" />}
        {tokenStr && <span className="text-[10px] text-muted-foreground/50 font-mono shrink-0">{tokenStr}</span>}
      </div>
      <div className="px-3 py-2.5 prose-answer max-w-none text-foreground/80 text-xs [&_p]:mb-1.5 [&_ul]:pl-4 [&_li]:mb-0.5">
        <Markdown>{text}</Markdown>
      </div>
    </div>
  )
}
