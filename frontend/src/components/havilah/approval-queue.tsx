"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { ScrollArea } from "@/components/ui/scroll-area"
import { approvalItems, type ApprovalItem } from "./mock-data"
import { Check, X, Clock, AlertTriangle } from "lucide-react"
import { toast } from "sonner"
import { motion, AnimatePresence } from "framer-motion"

const actionTypeColors: Record<string, string> = {
  communication: "bg-sky-500/10 text-sky-500 border-sky-500/20",
  financial: "bg-emerald-500/10 text-emerald-500 border-emerald-500/20",
  project: "bg-violet-500/10 text-violet-500 border-violet-500/20",
  strategic: "bg-amber-500/10 text-amber-500 border-amber-500/20",
  administrative: "bg-slate-500/10 text-slate-400 border-slate-500/20",
}

const riskColors: Record<string, string> = {
  low: "bg-emerald-500/10 text-emerald-500 border-emerald-500/20",
  medium: "bg-amber-500/10 text-amber-500 border-amber-500/20",
  high: "bg-red-500/10 text-red-500 border-red-500/20",
  critical: "bg-purple-500/10 text-purple-500 border-purple-500/20",
}

const riskIcons: Record<string, number> = {
  low: 1,
  medium: 2,
  high: 3,
  critical: 4,
}

export function ApprovalQueue() {
  const [items, setItems] = useState<ApprovalItem[]>(approvalItems)

  const handleApprove = (id: string) => {
    const item = items.find((i) => i.id === id)
    setItems((prev) => prev.filter((i) => i.id !== id))
    toast.success("Approved", {
      description: item?.summary ?? "Action approved and dispatched for execution.",
    })
  }

  const handleReject = (id: string) => {
    const item = items.find((i) => i.id === id)
    setItems((prev) => prev.filter((i) => i.id !== id))
    toast.error("Rejected", {
      description: item?.summary ?? "Action rejected and logged.",
    })
  }

  return (
    <Card className="border-border bg-card">
      <CardHeader>
        <CardTitle className="flex items-center justify-between text-foreground">
          <span className="flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-havilah-gold" />
            Approval Queue
          </span>
          <Badge
            variant="outline"
            className="border-amber-500/30 text-amber-500"
          >
            {items.length} Pending
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <ScrollArea className="max-h-96">
          <AnimatePresence mode="popLayout">
            {items.length === 0 ? (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="flex flex-col items-center justify-center py-8 text-center"
              >
                <Check className="mb-2 h-8 w-8 text-emerald-500" />
                <p className="text-sm font-medium text-foreground">All caught up!</p>
                <p className="text-xs text-muted-foreground">No pending approvals.</p>
              </motion.div>
            ) : (
              <div className="space-y-3">
                {items.map((item) => (
                  <motion.div
                    key={item.id}
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
                          <Badge
                            variant="outline"
                            className={actionTypeColors[item.actionType]}
                          >
                            {item.actionType}
                          </Badge>
                          <Badge
                            variant="outline"
                            className={riskColors[item.riskLevel]}
                          >
                            <AlertTriangle className="mr-1 h-3 w-3" />
                            {item.riskLevel}
                            {Array.from({ length: riskIcons[item.riskLevel] }).map((_, i) => (
                              <span key={i} className="ml-0.5 text-[8px]">
                                ■
                              </span>
                            ))}
                          </Badge>
                          <span className="flex items-center gap-1 text-xs text-muted-foreground">
                            <Clock className="h-3 w-3" />
                            {item.timestamp}
                          </span>
                        </div>

                        {/* Summary */}
                        <p className="text-sm font-medium text-foreground">
                          {item.summary}
                        </p>

                        {/* Details */}
                        <p className="text-xs text-muted-foreground">
                          {item.details}
                        </p>

                        {/* Requested by */}
                        <p className="text-xs text-muted-foreground">
                          Requested by: <span className="text-foreground">{item.requestedBy}</span>
                        </p>
                      </div>

                      {/* Action buttons */}
                      <div className="flex gap-2 sm:ml-4 sm:flex-col">
                        <Button
                          size="sm"
                          onClick={() => handleApprove(item.id)}
                          className="bg-emerald-600 text-white hover:bg-emerald-700"
                        >
                          <Check className="h-3.5 w-3.5" />
                          Approve
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleReject(item.id)}
                          className="border-red-500/30 text-red-500 hover:bg-red-500/10"
                        >
                          <X className="h-3.5 w-3.5" />
                          Reject
                        </Button>
                      </div>
                    </div>
                  </motion.div>
                ))}
              </div>
            )}
          </AnimatePresence>
        </ScrollArea>
      </CardContent>
    </Card>
  )
}
