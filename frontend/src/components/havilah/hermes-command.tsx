"use client"

import { useState, useCallback } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import {
  MessageSquare,
  LayoutGrid,
  Send,
  ShieldCheck,
  Play,
  Database,
  CheckCircle2,
  Circle,
  Loader2,
  Sparkles,
} from "lucide-react"
import { motion, AnimatePresence } from "framer-motion"
import { defaultPipelineStages, type PipelineStage } from "./mock-data"

const stageIcons = [MessageSquare, LayoutGrid, Send, ShieldCheck, Play, Database]

export function HermesCommand() {
  const [instruction, setInstruction] = useState("")
  const [isProcessing, setIsProcessing] = useState(false)
  const [stages, setStages] = useState<PipelineStage[]>(defaultPipelineStages)
  const [lastResult, setLastResult] = useState<string | null>(null)

  const runOrchestration = useCallback(async () => {
    if (!instruction.trim() || isProcessing) return

    setIsProcessing(true)
    setLastResult(null)
    setStages(defaultPipelineStages.map((s) => ({ ...s, status: "idle" as const })))

    // Animate through each stage
    for (let i = 0; i < defaultPipelineStages.length; i++) {
      // Set current stage to active
      setStages((prev) =>
        prev.map((s, idx) =>
          idx === i ? { ...s, status: "active" as const } : s
        )
      )

      // Wait for the "processing" time
      await new Promise((resolve) => setTimeout(resolve, 800 + Math.random() * 400))

      // Set current stage to complete
      setStages((prev) =>
        prev.map((s, idx) =>
          idx === i ? { ...s, status: "complete" as const } : s
        )
      )
    }

    setLastResult(
      `Orchestration complete. Instruction "${instruction.substring(0, 50)}${instruction.length > 50 ? "..." : ""}" processed through all 6 stages. Results recorded to memory.`
    )
    setIsProcessing(false)
  }, [instruction, isProcessing])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    runOrchestration()
  }

  return (
    <Card className="border-havilah-gold/20 bg-card gold-border-glow">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-foreground">
          <Sparkles className="h-5 w-5 text-havilah-gold" />
          Hermes Command Center
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Command Input */}
        <form onSubmit={handleSubmit} className="flex gap-2">
          <Input
            value={instruction}
            onChange={(e) => setInstruction(e.target.value)}
            placeholder="Enter natural language instruction... (e.g., 'Review Q1 performance and prepare executive summary')"
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
            <span className="hidden sm:inline">Submit to Hermes</span>
          </Button>
        </form>

        {/* Pipeline Visualization */}
        <div className="space-y-2">
          <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
            Orchestration Pipeline
          </p>
          <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
            {stages.map((stage, idx) => {
              const Icon = stageIcons[idx]
              return (
                <div key={stage.id} className="flex items-center gap-2 sm:flex-1">
                  <motion.div
                    className={`flex flex-col items-center gap-1.5 rounded-lg border p-3 sm:w-full ${
                      stage.status === "active"
                        ? "border-havilah-gold/50 bg-havilah-gold/10"
                        : stage.status === "complete"
                        ? "border-emerald-500/30 bg-emerald-500/5"
                        : "border-border bg-card"
                    }`}
                    animate={
                      stage.status === "active"
                        ? { scale: [1, 1.02, 1] }
                        : {}
                    }
                    transition={{ duration: 1, repeat: Infinity }}
                  >
                    <div
                      className={`flex h-8 w-8 items-center justify-center rounded-full ${
                        stage.status === "active"
                          ? "bg-havilah-gold/20 text-havilah-gold animate-pulse-gold"
                          : stage.status === "complete"
                          ? "bg-emerald-500/20 text-emerald-500"
                          : "bg-muted text-muted-foreground"
                      }`}
                    >
                      {stage.status === "complete" ? (
                        <CheckCircle2 className="h-4 w-4" />
                      ) : stage.status === "active" ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        <Icon className="h-4 w-4" />
                      )}
                    </div>
                    <span
                      className={`text-center text-xs font-medium ${
                        stage.status === "active"
                          ? "text-havilah-gold"
                          : stage.status === "complete"
                          ? "text-emerald-500"
                          : "text-muted-foreground"
                      }`}
                    >
                      {stage.label}
                    </span>
                  </motion.div>
                  {/* Connector Arrow */}
                  {idx < stages.length - 1 && (
                    <div className="hidden items-center sm:flex">
                      {stage.status === "complete" ? (
                        <div className="h-0.5 w-4 bg-emerald-500/50" />
                      ) : stage.status === "active" ? (
                        <div className="h-0.5 w-4 animate-flow-line" />
                      ) : (
                        <div className="h-0.5 w-4 bg-border" />
                      )}
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        </div>

        {/* Result */}
        <AnimatePresence>
          {lastResult && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              className="rounded-lg border border-emerald-500/20 bg-emerald-500/5 p-3"
            >
              <div className="flex items-start gap-2">
                <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-emerald-500" />
                <p className="text-sm text-foreground">{lastResult}</p>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Status indicators */}
        <div className="flex flex-wrap gap-3">
          <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
            <Circle className="h-2.5 w-2.5 fill-muted text-muted" />
            Idle
          </div>
          <div className="flex items-center gap-1.5 text-xs text-havilah-gold">
            <Circle className="h-2.5 w-2.5 fill-havilah-gold text-havilah-gold" />
            Active
          </div>
          <div className="flex items-center gap-1.5 text-xs text-emerald-500">
            <Circle className="h-2.5 w-2.5 fill-emerald-500 text-emerald-500" />
            Complete
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
