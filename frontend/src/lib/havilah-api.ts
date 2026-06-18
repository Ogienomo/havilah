/**
 * Havilah OS — Frontend API Client
 * ----------------------------------------------------------------------------
 * Talks to the Havilah backend (deployed on Railway) via REST.
 * Uses the JWT stored by <AuthProvider> for all authenticated calls.
 *
 * Env vars:
 *   NEXT_PUBLIC_HAVILAH_API_URL — backend URL, e.g. https://havilah-production.up.railway.app
 */

const API_URL = process.env.NEXT_PUBLIC_HAVILAH_API_URL ?? ""
const TOKEN_KEY = "havilah_jwt"

export const isApiConfigured = Boolean(API_URL)

// ── Token management ─────────────────────────────────────────
function getToken(): string | null {
  if (typeof window === "undefined") return null
  return localStorage.getItem(TOKEN_KEY)
}

export function setApiToken(token: string | null) {
  if (typeof window === "undefined") return
  if (token) localStorage.setItem(TOKEN_KEY, token)
  else localStorage.removeItem(TOKEN_KEY)
}

// ── Fetch wrapper ────────────────────────────────────────────
export class ApiError extends Error {
  status: number
  detail: any
  constructor(status: number, detail: any, message?: string) {
    super(message ?? `Havilah API ${status}`)
    this.status = status
    this.detail = detail
  }
}

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  if (!API_URL) {
    throw new Error(
      "NEXT_PUBLIC_HAVILAH_API_URL is not set. Configure it in Vercel env vars."
    )
  }
  const url = `${API_URL.replace(/\/$/, "")}${path}`
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(init?.headers as Record<string, string>),
  }
  const token = getToken()
  if (token) headers.Authorization = `Bearer ${token}`

  const res = await fetch(url, {
    ...init,
    headers,
    // Disable Next.js fetch caching for authenticated requests — we want
    // fresh data every time the user clicks something.
    cache: "no-store",
  })

  if (!res.ok) {
    let detail: any = null
    let message = `Havilah API ${res.status}`
    try {
      detail = await res.json()
      if (detail?.detail) message = detail.detail
    } catch {
      try { detail = await res.text() } catch {}
    }
    // Auto-logout on 401 — token expired or revoked
    if (res.status === 401 && typeof window !== "undefined") {
      localStorage.removeItem(TOKEN_KEY)
      localStorage.removeItem("havilah_user")
      // Redirect to /login if we're not already there
      if (window.location.pathname !== "/login") {
        window.location.href = "/login"
      }
    }
    throw new ApiError(res.status, detail, message)
  }
  // Some endpoints return empty body on success
  const text = await res.text()
  if (!text) return {} as T
  try {
    return JSON.parse(text) as T
  } catch {
    return text as unknown as T
  }
}

// ─── Types ────────────────────────────────────────────────────────────────

export interface HermesAgent {
  name: string
  display_name: string
  agent_type: string
  description: string
  capabilities: string[]
  tool_access: string[]
  approval_scope?: string | null
  is_active: boolean
}

export interface HermesRun {
  run_id: string
  status:
    | "pending"
    | "planning"
    | "executing"
    | "awaiting_approval"
    | "completed"
    | "failed"
    | "cancelled"
  source: string
  instruction: string
  started_at: string
  completed_at?: string
  steps?: HermesStep[]
  summary?: string
}

export interface HermesStep {
  step_number: number
  agent: string
  action: string
  approval_required: boolean
  approval_category?: string
  expected_output: string
  depends_on: number[]
  risk_level: "low" | "medium" | "high" | "critical"
  status?: "pending" | "dispatched" | "completed" | "failed"
  result?: string
}

export interface HermesInstructionResponse {
  run_id: string
  status: string
  plan: {
    plan_id: string
    summary: string
    requires_any_approval: boolean
    steps: HermesStep[]
  }
  results?: string[]
  memory_captured?: boolean
  awaiting_approval?: {
    approval_id: string
    step: HermesStep
  }
  message: string
}

export interface Approval {
  id: string
  current_state: string
  action_type: string
  risk_level: string
  summary: string
  requested_by: string
  created_at: string
}

export interface MemoryItem {
  id: string
  type: string
  importance: string
  title: string
  content: string
  created_at: string
  tags?: string[]
}

export interface ActivityEvent {
  id: string
  event_type: string
  entity_type: string
  entity_id: string
  payload: Record<string, unknown>
  created_at: string
}

export interface HermesHealth {
  status: string
  llm: {
    configured: boolean
    model: string
    connected: boolean
  }
  hermes_enabled: boolean
  agents_registered: number
}

// ─── Endpoints ────────────────────────────────────────────────────────────

export const havilahApi = {
  /** Health + LLM connectivity check (public) */
  health: () => apiFetch<HermesHealth>("/api/hermes/health"),

  /** List all 10 specialized agents (requires auth) */
  listAgents: async (): Promise<HermesAgent[]> => {
    const resp = await apiFetch<{ agents: HermesAgent[]; total: number }>("/api/hermes/agents")
    return resp.agents ?? []
  },

  /** Submit a natural-language instruction to Hermes */
  instruct: (instruction: string, source = "dashboard") =>
    apiFetch<HermesInstructionResponse>("/api/hermes/instruct", {
      method: "POST",
      body: JSON.stringify({ instruction, source, context: {} }),
    }),

  /** Approve a pending step */
  approve: (runId: string, reason = "Approved via dashboard") =>
    apiFetch<{ run_id: string; status: string; message: string }>(
      "/api/hermes/approve",
      {
        method: "POST",
        body: JSON.stringify({ run_id: runId, reason }),
      }
    ),

  /** Reject a pending step */
  reject: (runId: string, reason = "Rejected via dashboard") =>
    apiFetch<{ run_id: string; status: string; message: string }>(
      "/api/hermes/reject",
      {
        method: "POST",
        body: JSON.stringify({ run_id: runId, reason }),
      }
    ),

  /** List active runs */
  listRuns: () => apiFetch<HermesRun[]>("/api/hermes/runs"),

  /** Get a specific run's status */
  getRun: (runId: string) =>
    apiFetch<HermesRun>(`/api/hermes/runs/${runId}`),

  /** Pending approvals */
  listApprovals: (params: { status?: string } = {}) => {
    const q = new URLSearchParams(params).toString()
    return apiFetch<Approval[]>(`/api/approvals${q ? `?${q}` : ""}`)
  },

  /** Recent memory items */
  listMemory: (limit = 20) =>
    apiFetch<MemoryItem[]>(`/api/memory?limit=${limit}`),

  /** Activity timeline */
  listActivity: (limit = 20) =>
    apiFetch<ActivityEvent[]>(`/api/events?limit=${limit}`),

  /** Direct chat (no planning pipeline) */
  chat: (message: string, agentType = "default") =>
    apiFetch<{ response: string; tokens_used: number }>(
      "/api/hermes/chat",
      {
        method: "POST",
        body: JSON.stringify({ message, agent_type: agentType }),
      }
    ),
}
