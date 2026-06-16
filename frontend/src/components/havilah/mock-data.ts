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
  ShieldCheck,
  type LucideIcon,
} from "lucide-react"

export type AgentStatus = "active" | "idle" | "busy"

export interface Agent {
  id: string
  name: string
  icon: LucideIcon
  status: AgentStatus
  capabilities: string[]
  color: string
  description: string
}

export const agents: Agent[] = [
  {
    id: "planner",
    name: "Planner",
    icon: LayoutList,
    status: "active",
    capabilities: ["Task decomposition", "Timeline estimation", "Dependency mapping", "Resource allocation"],
    color: "#60a5fa",
    description: "Breaks down complex goals into actionable plans",
  },
  {
    id: "executive",
    name: "Executive",
    icon: Crown,
    status: "active",
    capabilities: ["Decision making", "Priority assessment", "Strategic alignment", "Risk evaluation"],
    color: "#d4a853",
    description: "Makes high-level decisions aligned with business strategy",
  },
  {
    id: "research",
    name: "Research",
    icon: Search,
    status: "busy",
    capabilities: ["Market analysis", "Competitive intelligence", "Data synthesis", "Trend identification"],
    color: "#4ade80",
    description: "Gathers and synthesizes information from multiple sources",
  },
  {
    id: "writing",
    name: "Writing",
    icon: PenTool,
    status: "idle",
    capabilities: ["Content drafting", "Email composition", "Report writing", "Document editing"],
    color: "#f472b6",
    description: "Creates polished written content and communications",
  },
  {
    id: "meeting",
    name: "Meeting",
    icon: Users,
    status: "active",
    capabilities: ["Schedule optimization", "Agenda creation", "Minutes capture", "Action tracking"],
    color: "#a78bfa",
    description: "Manages meeting logistics and follow-ups",
  },
  {
    id: "reviewer",
    name: "Reviewer",
    icon: Eye,
    status: "idle",
    capabilities: ["Quality assurance", "Compliance checking", "Consistency review", "Feedback generation"],
    color: "#2dd4bf",
    description: "Reviews outputs for quality and compliance standards",
  },
  {
    id: "critic",
    name: "Critic",
    icon: ShieldAlert,
    status: "active",
    capabilities: ["Risk assessment", "Blind spot detection", "Contrarian analysis", "Stress testing"],
    color: "#fb923c",
    description: "Identifies weaknesses and potential failure points",
  },
  {
    id: "memory",
    name: "Memory",
    icon: Brain,
    status: "active",
    capabilities: ["Knowledge storage", "Context retrieval", "Relationship mapping", "Pattern recognition"],
    color: "#818cf8",
    description: "Stores and retrieves organizational knowledge",
  },
  {
    id: "learning",
    name: "Learning",
    icon: GraduationCap,
    status: "idle",
    capabilities: ["Skill development", "Knowledge gaps", "Training recommendations", "Progress tracking"],
    color: "#34d399",
    description: "Identifies learning opportunities and tracks development",
  },
  {
    id: "approval",
    name: "Approval",
    icon: ShieldCheck,
    status: "active",
    capabilities: ["Request validation", "Risk scoring", "Policy compliance", "Audit logging"],
    color: "#fbbf24",
    description: "Manages approval workflows and compliance gates",
  },
]

export type ActionType = "communication" | "financial" | "project" | "strategic" | "administrative"
export type RiskLevel = "low" | "medium" | "high" | "critical"

export interface ApprovalItem {
  id: string
  actionType: ActionType
  riskLevel: RiskLevel
  summary: string
  requestedBy: string
  timestamp: string
  details: string
}

export const approvalItems: ApprovalItem[] = [
  {
    id: "apr-001",
    actionType: "communication",
    riskLevel: "medium",
    summary: "Send partnership proposal to Vertex Solutions CEO",
    requestedBy: "Writing Agent",
    timestamp: "2 min ago",
    details: "Draft email with partnership terms for Q2 collaboration. Includes NDA request and preliminary scope document.",
  },
  {
    id: "apr-002",
    actionType: "financial",
    riskLevel: "high",
    summary: "Approve $12,500 budget allocation for market research",
    requestedBy: "Executive Agent",
    timestamp: "15 min ago",
    details: "Allocate Q2 discretionary budget for competitive landscape analysis covering 5 key competitors in the APAC region.",
  },
  {
    id: "apr-003",
    actionType: "strategic",
    riskLevel: "critical",
    summary: "Initiate acquisition due diligence on DataFlow Inc.",
    requestedBy: "Research Agent",
    timestamp: "1 hr ago",
    details: "Begin preliminary due diligence process for potential acquisition target. Requires NDA execution and financial document request.",
  },
  {
    id: "apr-004",
    actionType: "project",
    riskLevel: "low",
    summary: "Create new project workspace for client onboarding",
    requestedBy: "Planner Agent",
    timestamp: "30 min ago",
    details: "Set up project infrastructure for new enterprise client onboarding including task boards, timelines, and resource allocation.",
  },
  {
    id: "apr-005",
    actionType: "administrative",
    riskLevel: "medium",
    summary: "Schedule quarterly board review meeting for March 15",
    requestedBy: "Meeting Agent",
    timestamp: "45 min ago",
    details: "Coordinate availability for 6 board members, prepare agenda covering Q1 performance, Q2 projections, and strategic initiatives.",
  },
]

export type MemoryType = "profile" | "client" | "project" | "communication" | "operational" | "research" | "approval" | "meeting"
export type Importance = "low" | "medium" | "high" | "critical"

export interface MemoryItem {
  id: string
  type: MemoryType
  importance: Importance
  title: string
  content: string
  timestamp: string
  tags: string[]
}

export const memoryItems: MemoryItem[] = [
  {
    id: "mem-001",
    type: "client",
    importance: "critical",
    title: "Vertex Solutions — Enterprise Partnership",
    content: "Key strategic partner for APAC expansion. CEO Sarah Chen, CTO Marcus Lee. Annual contract value $2.4M. Partnership renewed through 2027.",
    timestamp: "5 min ago",
    tags: ["partnership", "APAC", "enterprise"],
  },
  {
    id: "mem-002",
    type: "project",
    importance: "high",
    title: "Project Atlas — Platform Migration",
    content: "Migrating legacy systems to cloud-native architecture. Phase 2 complete, Phase 3 starts March 10. Budget: $340K remaining.",
    timestamp: "22 min ago",
    tags: ["migration", "cloud", "infrastructure"],
  },
  {
    id: "mem-003",
    type: "communication",
    importance: "medium",
    title: "Board Meeting Follow-up — Q1 Review",
    content: "Board approved 15% budget increase for AI initiatives. Key concern: talent retention. Action items assigned to HR and Operations.",
    timestamp: "1 hr ago",
    tags: ["board", "budget", "AI"],
  },
  {
    id: "mem-004",
    type: "research",
    importance: "high",
    title: "Competitive Analysis — Q1 2026",
    content: "Market share decreased 2% in enterprise segment. Key threat: TechNova's new AI suite. Recommendation: accelerate product roadmap.",
    timestamp: "2 hrs ago",
    tags: ["competition", "market", "AI"],
  },
  {
    id: "mem-005",
    type: "operational",
    importance: "low",
    title: "System Performance — Weekly Report",
    content: "API uptime 99.97%. Average response time 142ms. Memory database size: 1.2M entries. Agent utilization: 78% peak, 34% average.",
    timestamp: "3 hrs ago",
    tags: ["performance", "uptime", "metrics"],
  },
  {
    id: "mem-006",
    type: "profile",
    importance: "medium",
    title: "Dr. Elena Vasquez — Advisory Board",
    content: "AI ethics researcher, Stanford. Joined advisory board Jan 2026. Specializes in responsible AI deployment in financial services.",
    timestamp: "5 hrs ago",
    tags: ["advisory", "AI ethics", "Stanford"],
  },
  {
    id: "mem-007",
    type: "approval",
    importance: "high",
    title: "Approved: DataFlow Integration Contract",
    content: "Integration partnership approved. $180K annual value. 6-month pilot with option to extend. Legal review completed.",
    timestamp: "6 hrs ago",
    tags: ["contract", "integration", "legal"],
  },
  {
    id: "mem-008",
    type: "meeting",
    importance: "medium",
    title: "Product Strategy Sync — March 3",
    content: "Attendees: Product, Engineering, Design. Decided on Q2 feature priorities. Mobile experience overhaul greenlit. New analytics dashboard in scope.",
    timestamp: "8 hrs ago",
    tags: ["product", "strategy", "mobile"],
  },
  {
    id: "mem-009",
    type: "client",
    importance: "critical",
    title: "Meridian Corp — $4.2M Contract Renewal",
    content: "Largest client. Contract renewal due April 15. Satisfaction score 8.7/10. Key risk: new procurement head wants competitive bid.",
    timestamp: "1 day ago",
    tags: ["renewal", "enterprise", "risk"],
  },
  {
    id: "mem-010",
    type: "research",
    importance: "medium",
    title: "Industry Report — AI Agent Market 2026",
    content: "AI agent market projected to reach $47B by 2028. Key trend: multi-agent orchestration platforms. Havilah positioned in high-growth segment.",
    timestamp: "1 day ago",
    tags: ["market", "forecast", "agents"],
  },
]

export type ActivityCategory = "agent" | "approval" | "memory" | "system" | "communication" | "project"

export interface ActivityEvent {
  id: string
  category: ActivityCategory
  title: string
  description: string
  timestamp: string
  color: string
}

export const activityEvents: ActivityEvent[] = [
  {
    id: "act-001",
    category: "agent",
    title: "Research Agent completed market analysis",
    description: "Generated comprehensive competitive landscape report for APAC region covering 12 competitors",
    timestamp: "2 min ago",
    color: "#4ade80",
  },
  {
    id: "act-002",
    category: "approval",
    title: "Approval requested: Partnership proposal",
    description: "Writing Agent seeks approval to send partnership proposal to Vertex Solutions",
    timestamp: "5 min ago",
    color: "#fbbf24",
  },
  {
    id: "act-003",
    category: "memory",
    title: "Memory recorded: Board meeting outcomes",
    description: "Captured 4 key decisions and 6 action items from quarterly board review",
    timestamp: "12 min ago",
    color: "#818cf8",
  },
  {
    id: "act-004",
    category: "system",
    title: "Hermes orchestration completed",
    description: "Successfully processed instruction: 'Review Q1 performance and prepare executive summary'",
    timestamp: "18 min ago",
    color: "#d4a853",
  },
  {
    id: "act-005",
    category: "communication",
    title: "Email drafted to Meridian Corp",
    description: "Prepared contract renewal discussion email with key talking points and proposed terms",
    timestamp: "25 min ago",
    color: "#f472b6",
  },
  {
    id: "act-006",
    category: "project",
    title: "Project Atlas milestone reached",
    description: "Phase 2 migration completed 2 days ahead of schedule. All systems passing integration tests.",
    timestamp: "1 hr ago",
    color: "#60a5fa",
  },
  {
    id: "act-007",
    category: "approval",
    title: "Approved: Weekly team sync schedule",
    description: "Recurring meeting approved for cross-functional team alignment every Monday 9:00 AM",
    timestamp: "1.5 hrs ago",
    color: "#fbbf24",
  },
  {
    id: "act-008",
    category: "agent",
    title: "Critic Agent flagged potential risk",
    description: "Identified dependency risk in supply chain for Q2 product launch — single vendor for critical component",
    timestamp: "2 hrs ago",
    color: "#fb923c",
  },
  {
    id: "act-009",
    category: "system",
    title: "System backup completed",
    description: "Full memory database backup completed. 1.2M entries, 2.3GB total. Zero errors.",
    timestamp: "3 hrs ago",
    color: "#d4a853",
  },
  {
    id: "act-010",
    category: "memory",
    title: "Memory reinforced: Client preferences",
    description: "Updated communication preferences for 3 key clients based on recent interactions",
    timestamp: "4 hrs ago",
    color: "#818cf8",
  },
]

export interface PipelineStage {
  id: string
  label: string
  description: string
  status: "idle" | "active" | "complete"
}

export const defaultPipelineStages: PipelineStage[] = [
  { id: "instruction", label: "Instruction", description: "Receive natural language command", status: "idle" },
  { id: "planning", label: "Planning", description: "Decompose into agent tasks", status: "idle" },
  { id: "dispatch", label: "Agent Dispatch", description: "Assign tasks to specialized agents", status: "idle" },
  { id: "approval", label: "Approval Gate", description: "Human review for external actions", status: "idle" },
  { id: "execution", label: "Execution", description: "Agents execute approved tasks", status: "idle" },
  { id: "memory", label: "Memory Recording", description: "Store results in knowledge base", status: "idle" },
]
