"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { agents } from "./mock-data"
import { motion } from "framer-motion"

const container = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: { staggerChildren: 0.05 },
  },
}

const item = {
  hidden: { opacity: 0, scale: 0.95 },
  show: { opacity: 1, scale: 1 },
}

export function AgentGrid() {
  return (
    <Card className="border-border bg-card">
      <CardHeader>
        <CardTitle className="flex items-center justify-between text-foreground">
          <span>Agent Status Grid</span>
          <Badge variant="outline" className="border-havilah-gold/30 text-havilah-gold">
            10 Agents
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <motion.div
          variants={container}
          initial="hidden"
          animate="show"
          className="grid grid-cols-2 gap-3 sm:gap-4 md:grid-cols-3 lg:grid-cols-5"
        >
          {agents.map((agent) => {
            const Icon = agent.icon
            return (
              <motion.div
                key={agent.id}
                variants={item}
                className="group rounded-lg border border-border bg-card p-3 sm:p-4 transition-all duration-300 hover:border-havilah-gold/30 hover:shadow-md hover:shadow-havilah-gold/5"
              >
                <div className="flex flex-col items-center text-center">
                  {/* Icon with status indicator */}
                  <div className="relative mb-3">
                    <div
                      className="flex h-12 w-12 items-center justify-center rounded-xl transition-transform duration-300 group-hover:scale-110"
                      style={{ backgroundColor: `${agent.color}15` }}
                    >
                      <Icon className="h-6 w-6" style={{ color: agent.color }} />
                    </div>
                    {/* Status dot */}
                    <span
                      className={`absolute -right-0.5 -top-0.5 flex h-3.5 w-3.5 items-center justify-center rounded-full border-2 border-card ${
                        agent.status === "active"
                          ? "bg-emerald-500"
                          : agent.status === "busy"
                          ? "bg-amber-500"
                          : "bg-slate-400 dark:bg-slate-500"
                      }`}
                    >
                      {agent.status === "active" && (
                        <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" />
                      )}
                      {agent.status === "busy" && (
                        <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-amber-400 opacity-75" />
                      )}
                    </span>
                  </div>

                  {/* Name */}
                  <h3 className="mb-1 text-sm font-semibold text-foreground">{agent.name}</h3>

                  {/* Status badge */}
                  <Badge
                    variant="outline"
                    className={`mb-2 text-[10px] ${
                      agent.status === "active"
                        ? "border-emerald-500/30 text-emerald-500"
                        : agent.status === "busy"
                        ? "border-amber-500/30 text-amber-500"
                        : "border-slate-400/30 text-slate-400 dark:text-slate-500"
                    }`}
                  >
                    {agent.status}
                  </Badge>

                  {/* Description */}
                  <p className="mb-2 text-[10px] leading-tight text-muted-foreground line-clamp-2">
                    {agent.description}
                  </p>

                  {/* Capabilities */}
                  <div className="flex flex-wrap justify-center gap-0.5">
                    {agent.capabilities.slice(0, 2).map((cap) => (
                      <span
                        key={cap}
                        className="rounded-full bg-muted px-1.5 py-0.5 text-[9px] text-muted-foreground"
                      >
                        {cap}
                      </span>
                    ))}
                    {agent.capabilities.length > 2 && (
                      <span className="rounded-full bg-muted px-1.5 py-0.5 text-[9px] text-muted-foreground">
                        +{agent.capabilities.length - 2}
                      </span>
                    )}
                  </div>
                </div>
              </motion.div>
            )
          })}
        </motion.div>
      </CardContent>
    </Card>
  )
}
