"use client"

import { Card, CardContent } from "@/components/ui/card"
import { Users, ShieldCheck, Brain, CheckCircle2 } from "lucide-react"
import { motion } from "framer-motion"

interface StatItem {
  label: string
  value: string | number
  icon: React.ReactNode
  dotColor: string
  change: string
}

const stats: StatItem[] = [
  {
    label: "Active Agents",
    value: 10,
    icon: <Users className="h-5 w-5" />,
    dotColor: "bg-emerald-500",
    change: "All operational",
  },
  {
    label: "Pending Approvals",
    value: 3,
    icon: <ShieldCheck className="h-5 w-5" />,
    dotColor: "bg-amber-500",
    change: "Awaiting review",
  },
  {
    label: "Memory Items",
    value: "1,247",
    icon: <Brain className="h-5 w-5" />,
    dotColor: "bg-violet-500",
    change: "+23 today",
  },
  {
    label: "Tasks Completed",
    value: 89,
    icon: <CheckCircle2 className="h-5 w-5" />,
    dotColor: "bg-sky-500",
    change: "This week",
  },
]

const container = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: { staggerChildren: 0.1 },
  },
}

const item = {
  hidden: { opacity: 0, y: 20 },
  show: { opacity: 1, y: 0 },
}

export function HeroStats() {
  return (
    <motion.div
      variants={container}
      initial="hidden"
      animate="show"
      className="grid grid-cols-2 gap-3 sm:gap-4 lg:grid-cols-4"
    >
      {stats.map((stat) => (
        <motion.div key={stat.label} variants={item}>
          <Card className="group relative overflow-hidden border-border bg-card transition-all duration-300 hover:border-havilah-gold/30 hover:shadow-lg hover:shadow-havilah-gold/5">
            <CardContent className="p-4 sm:p-6">
              <div className="flex items-start justify-between">
                <div className="flex flex-col gap-1">
                  <p className="text-xs font-medium text-muted-foreground sm:text-sm">
                    {stat.label}
                  </p>
                  <p className="text-2xl font-bold tracking-tight text-foreground sm:text-3xl">
                    {stat.value}
                  </p>
                  <div className="flex items-center gap-1.5">
                    <span className={`h-1.5 w-1.5 rounded-full ${stat.dotColor}`} />
                    <span className="text-xs text-muted-foreground">{stat.change}</span>
                  </div>
                </div>
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-havilah-gold/10 text-havilah-gold transition-colors group-hover:bg-havilah-gold/20 sm:h-12 sm:w-12">
                  {stat.icon}
                </div>
              </div>
              {/* Subtle gold accent line at bottom */}
              <div className="absolute bottom-0 left-0 h-0.5 w-0 bg-gradient-to-r from-havilah-gold to-havilah-gold-light transition-all duration-500 group-hover:w-full" />
            </CardContent>
          </Card>
        </motion.div>
      ))}
    </motion.div>
  )
}
