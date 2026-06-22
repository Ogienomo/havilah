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

async function apiFetch<T>(path: string, init?: RequestInit & { timeoutMs?: number }): Promise<T> {
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

  // Timeout support via AbortController — default 30s, override per-call
  const timeoutMs = (init as any)?.timeoutMs ?? 30_000
  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs)

  let res: Response
  try {
    res = await fetch(url, {
      ...init,
      headers,
      cache: "no-store",
      signal: controller.signal,
    })
  } catch (fetchErr: any) {
    clearTimeout(timeoutId)
    if (fetchErr?.name === "AbortError") {
      throw new ApiError(0, null, `Request timed out after ${timeoutMs / 1000}s`)
    }
    throw fetchErr
  }
  clearTimeout(timeoutId)

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

/** A single step's execution result returned in HermesInstructionResponse.results */
export interface HermesResult {
  step_number: number
  agent: string
  action: string
  status: "success" | "failed" | string
  output: string
  tokens?: number
  requires_approval?: boolean
  approval?: {
    approval_id: string
    current_state?: string
    [key: string]: any
  }
  error?: string
}

export interface HermesInstructionResponse {
  run_id: string
  status:
    | "pending"
    | "planning"
    | "executing"
    | "awaiting_approval"
    | "completed"
    | "failed"
    | "cancelled"
    | string
  plan: {
    plan_id?: string
    summary: string
    requires_any_approval: boolean
    steps: HermesStep[]
  }
  /** Array of step result objects (NOT strings — each has .output, .agent, .status) */
  results?: HermesResult[]
  summary?: string
  approval_needed?: boolean
  approval_id?: string | null
  /** NOTE: Backend returns this as `null` even when approval is needed — use `approval_needed` instead */
  awaiting_approval?: {
    approval_id: string
    step: HermesStep
  } | null
  memory_recorded?: any
  memory_captured?: boolean
  elapsed_seconds?: number
  message?: string
  error?: string
  reason?: string
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

/** Shape returned by GET /api/events/recent */
export interface ActivityEvent {
  aggregate_type: string
  aggregate_id: string
  event_type: string
  actor_type: string
  payload: Record<string, any>
  created_at: string
}

/** Shape returned by GET /api/hermes/runs */
export interface ActiveRunsResponse {
  active_runs: HermesRun[]
}

/** Shape returned by GET /api/hermes/health */
export interface HermesHealthDetailed {
  status: string
  checks?: {
    hermes_enabled: boolean
    openai_configured: boolean
    model: string
    llm_connected: boolean
    llm_test_tokens: number
    agents_registered: number
  }
}

/** Shape returned by POST /api/memory/search */
export interface MemorySearchResponse {
  results?: MemoryItem[]
  memories?: MemoryItem[]
  total?: number
  [key: string]: any
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
  health: () => apiFetch<HermesHealthDetailed>("/api/hermes/health"),

  /** List all 10 specialized agents (requires auth) */
  listAgents: async (): Promise<HermesAgent[]> => {
    const resp = await apiFetch<{ agents: HermesAgent[]; total: number }>("/api/hermes/agents")
    return resp.agents ?? []
  },

  /** Submit a natural-language instruction to Hermes (90s timeout — LLM calls are slow) */
  instruct: (instruction: string, source = "dashboard") =>
    apiFetch<HermesInstructionResponse>("/api/hermes/instruct", {
      method: "POST",
      body: JSON.stringify({ instruction, source, context: {} }),
      timeoutMs: 90_000,
    } as RequestInit & { timeoutMs: number }),

  /** Approve a pending step (90s timeout — continues the run, which calls LLM) */
  approve: (runId: string, reason = "Approved via dashboard") =>
    apiFetch<{ run_id: string; status: string; message: string } & Partial<HermesInstructionResponse>>(
      "/api/hermes/approve",
      {
        method: "POST",
        body: JSON.stringify({ run_id: runId, reason }),
        timeoutMs: 90_000,
      } as RequestInit & { timeoutMs: number }
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
  listRuns: async (): Promise<HermesRun[]> => {
    const resp = await apiFetch<ActiveRunsResponse>("/api/hermes/runs")
    return resp.active_runs ?? []
  },

  /** Get a specific run's status */
  getRun: (runId: string) =>
    apiFetch<HermesRun>(`/api/hermes/runs/${runId}`),

  /** Pending approvals (note: backend route currently 500s — derive from events instead) */
  listApprovals: (params: { status?: string } = {}) => {
    const q = new URLSearchParams(params).toString()
    return apiFetch<Approval[]>(`/api/approvals/${q ? `?${q}` : ""}`)
  },

  /** Approve via the approvals API (admin only) */
  approveApproval: (approvalId: string, reason = "Approved via dashboard") =>
    apiFetch<{ status: string; message: string }>(
      `/api/approvals/${approvalId}/approve`,
      { method: "POST", body: JSON.stringify({ reason }) }
    ),

  /** Reject via the approvals API (admin only) */
  rejectApproval: (approvalId: string, reason = "Rejected via dashboard") =>
    apiFetch<{ status: string; message: string }>(
      `/api/approvals/${approvalId}/reject`,
      { method: "POST", body: JSON.stringify({ reason }) }
    ),

  /** Search memory items by text */
  searchMemory: async (searchText: string, limit = 20): Promise<MemoryItem[]> => {
    const resp = await apiFetch<MemorySearchResponse>("/api/memory/search", {
      method: "POST",
      body: JSON.stringify({ search_text: searchText, limit }),
    })
    return resp.results ?? resp.memories ?? []
  },

  /** List memories by type */
  listMemoryByType: (memoryType: string) =>
    apiFetch<MemoryItem[]>(`/api/memory/type/${encodeURIComponent(memoryType)}`),

  /** Recent activity events */
  listActivity: (limit = 20) =>
    apiFetch<ActivityEvent[]>(`/api/events/recent?limit=${limit}`),

  /** Direct chat (no planning pipeline) */
  chat: (message: string, agentType = "default") =>
    apiFetch<{ response: string; tokens_used: number }>(
      "/api/hermes/chat",
      {
        method: "POST",
        body: JSON.stringify({ message, agent_type: agentType }),
      }
    ),

  /** Get user preferences from backend (auto_approve, etc.) */
  getPreferences: (userId: string) =>
    apiFetch<{ user_id: string; auto_approve: boolean; preferences: Record<string, unknown> }>(
      `/api/user/preferences?user_id=${encodeURIComponent(userId)}`
    ),

  /** Update user preferences in backend */
  updatePreferences: (userId: string, update: { auto_approve?: boolean; preferences?: Record<string, unknown> }) =>
    apiFetch<{ user_id: string; auto_approve: boolean; preferences: Record<string, unknown> }>(
      `/api/user/preferences?user_id=${encodeURIComponent(userId)}`,
      {
        method: "PUT",
        body: JSON.stringify(update),
      }
    ),
}
