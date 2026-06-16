"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import {
  MessageSquare,
  Zap,
  LayoutList,
  Crown,
  Search,
  PenTool,
  Users,
  Eye,
  ShieldAlert,
  Brain,
  GraduationCap,
  ShieldCheck,
  Database,
} from "lucide-react"

const agentIcons = [
  { icon: LayoutList, label: "Planner", color: "#60a5fa" },
  { icon: Crown, label: "Executive", color: "#d4a853" },
  { icon: Search, label: "Research", color: "#4ade80" },
  { icon: PenTool, label: "Writing", color: "#f472b6" },
  { icon: Users, label: "Meeting", color: "#a78bfa" },
  { icon: Eye, label: "Reviewer", color: "#2dd4bf" },
  { icon: ShieldAlert, label: "Critic", color: "#fb923c" },
  { icon: Brain, label: "Memory", color: "#818cf8" },
  { icon: GraduationCap, label: "Learning", color: "#34d399" },
  { icon: ShieldCheck, label: "Approval", color: "#fbbf24" },
]

function ArchNode({
  icon: Icon,
  label,
  color,
  size = "md",
  pulse = false,
}: {
  icon: React.ComponentType<{ className?: string }>
  label: string
  color: string
  size?: "sm" | "md" | "lg"
  pulse?: boolean
}) {
  const sizeClasses = {
    sm: "h-8 w-8",
    md: "h-10 w-10",
    lg: "h-12 w-12",
  }

  return (
    <div className="flex flex-col items-center gap-1.5">
      <div
        className={`flex ${sizeClasses[size]} items-center justify-center rounded-xl border transition-transform duration-300 hover:scale-110`}
        style={{
          backgroundColor: `${color}15`,
          borderColor: `${color}30`,
          boxShadow: pulse ? `0 0 20px ${color}20` : "none",
        }}
      >
        <Icon className="h-5 w-5" style={{ color }} />
      </div>
      <span className="text-[10px] font-medium text-muted-foreground">{label}</span>
    </div>
  )
}

function PulseLine({ color = "#d4a853" }: { color?: string }) {
  return (
    <div className="flex items-center">
      <div className="relative h-0.5 w-8 sm:w-12">
        <div className="absolute inset-0 bg-border" />
        <div
          className="animate-shimmer absolute inset-0"
          style={{
            background: `linear-gradient(90deg, transparent 0%, ${color}60 50%, transparent 100%)`,
            backgroundSize: "200% 100%",
          }}
        />
      </div>
      <svg className="h-3 w-3 -ml-1" viewBox="0 0 12 12" fill="none">
        <path d="M2 2L10 6L2 10Z" fill={color} opacity={0.6} />
      </svg>
    </div>
  )
}

export function SystemArchitecture() {
  return (
    <Card className="border-border bg-card">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-foreground">
          <Zap className="h-5 w-5 text-havilah-gold" />
          System Architecture
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex flex-col items-center gap-4 overflow-x-auto py-4">
          {/* Row 1: WhatsApp → Hermes */}
          <div className="flex items-center gap-2 sm:gap-4">
            <ArchNode icon={MessageSquare} label="WhatsApp" color="#25D366" size="lg" pulse />
            <PulseLine color="#25D366" />
            <ArchNode icon={Zap} label="Hermes" color="#d4a853" size="lg" pulse />
          </div>

          {/* Vertical connector */}
          <div className="relative h-6 w-0.5">
            <div className="absolute inset-0 bg-border" />
            <div
              className="animate-shimmer absolute inset-0"
              style={{
                background: `linear-gradient(180deg, transparent 0%, #d4a85360 50%, transparent 100%)`,
                backgroundSize: "100% 200%",
              }}
            />
          </div>

          {/* Row 2: 10 Agents */}
          <div className="flex flex-col items-center gap-2">
            <p className="text-xs font-medium text-muted-foreground">10 Specialized Agents</p>
            <div className="flex flex-wrap items-center justify-center gap-2 sm:gap-3">
              {agentIcons.map((agent) => (
                <ArchNode
                  key={agent.label}
                  icon={agent.icon}
                  label={agent.label}
                  color={agent.color}
                  size="sm"
                />
              ))}
            </div>
          </div>

          {/* Vertical connector */}
          <div className="relative h-6 w-0.5">
            <div className="absolute inset-0 bg-border" />
            <div
              className="animate-shimmer absolute inset-0"
              style={{
                background: `linear-gradient(180deg, transparent 0%, #fbbf2460 50%, transparent 100%)`,
                backgroundSize: "100% 200%",
              }}
            />
          </div>

          {/* Row 3: Approval Ledger → Memory → Database */}
          <div className="flex items-center gap-2 sm:gap-4">
            <ArchNode icon={ShieldCheck} label="Approval Ledger" color="#fbbf24" size="lg" pulse />
            <PulseLine color="#fbbf24" />
            <ArchNode icon={Brain} label="Memory" color="#818cf8" size="lg" pulse />
            <PulseLine color="#818cf8" />
            <ArchNode icon={Database} label="Database" color="#4ade80" size="lg" />
          </div>

          {/* Flow label */}
          <div className="mt-2 rounded-full border border-havilah-gold/20 bg-havilah-gold/5 px-4 py-1.5">
            <p className="text-[10px] font-medium text-havilah-gold">
              Instruction → Plan → Dispatch → Approve → Execute → Record
            </p>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
