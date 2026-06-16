"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { ScrollArea } from "@/components/ui/scroll-area"
import { activityEvents } from "./mock-data"
import {
  Bot,
  ShieldCheck,
  Brain,
  Settings,
  Mail,
  FolderKanban,
} from "lucide-react"
import { motion } from "framer-motion"

const categoryIcons: Record<string, React.ReactNode> = {
  agent: <Bot className="h-3.5 w-3.5" />,
  approval: <ShieldCheck className="h-3.5 w-3.5" />,
  memory: <Brain className="h-3.5 w-3.5" />,
  system: <Settings className="h-3.5 w-3.5" />,
  communication: <Mail className="h-3.5 w-3.5" />,
  project: <FolderKanban className="h-3.5 w-3.5" />,
}

const container = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: { staggerChildren: 0.06 },
  },
}

const item = {
  hidden: { opacity: 0, x: -10 },
  show: { opacity: 1, x: 0 },
}

export function ActivityTimeline() {
  return (
    <Card className="border-border bg-card">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-foreground">
          <Settings className="h-5 w-5 text-havilah-gold" />
          Recent Activity
        </CardTitle>
      </CardHeader>
      <CardContent>
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
              {activityEvents.map((event) => (
                <motion.div
                  key={event.id}
                  variants={item}
                  className="relative flex gap-3 px-1 py-2"
                >
                  {/* Timeline dot */}
                  <div
                    className="relative z-10 flex h-[30px] w-[30px] shrink-0 items-center justify-center rounded-full border border-border bg-card"
                    style={{ borderColor: `${event.color}30` }}
                  >
                    <div
                      className="flex h-5 w-5 items-center justify-center rounded-full"
                      style={{ backgroundColor: `${event.color}20`, color: event.color }}
                    >
                      {categoryIcons[event.category]}
                    </div>
                  </div>

                  {/* Content */}
                  <div className="flex-1 space-y-0.5 pb-2">
                    <div className="flex items-start justify-between gap-2">
                      <p className="text-sm font-medium text-foreground">
                        {event.title}
                      </p>
                      <span className="shrink-0 text-[10px] text-muted-foreground whitespace-nowrap">
                        {event.timestamp}
                      </span>
                    </div>
                    <p className="text-xs leading-relaxed text-muted-foreground">
                      {event.description}
                    </p>
                  </div>
                </motion.div>
              ))}
            </div>
          </motion.div>
        </ScrollArea>
      </CardContent>
    </Card>
  )
}
