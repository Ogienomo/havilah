"use client"

/**
 * Havilah OS — React hooks for the dashboard
 * ----------------------------------------------------------------------------
 * Wraps the havilahApi client with React Query.
 * Returns empty arrays when the API is not configured (no more mock data).
 */

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { havilahApi, isApiConfigured } from "./havilah-api"

// ─── Agents ────────────────────────────────────────────────────────────────

export function useAgents() {
  return useQuery({
    queryKey: ["agents"],
    queryFn: async () => {
      if (!isApiConfigured) return []
      return havilahApi.listAgents()
    },
    staleTime: 30_000,
  })
}

// ─── Approvals ─────────────────────────────────────────────────────────────

export function useApprovals() {
  return useQuery({
    queryKey: ["approvals"],
    queryFn: async () => {
      if (!isApiConfigured) return []
      try {
        return await havilahApi.listApprovals({ status: "pending" })
      } catch {
        return []
      }
    },
    staleTime: 10_000,
  })
}

export function useApproveAction() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ runId, reason }: { runId: string; reason?: string }) =>
      havilahApi.approve(runId, reason),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["approvals"] })
      qc.invalidateQueries({ queryKey: ["runs"] })
    },
  })
}

export function useRejectAction() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ runId, reason }: { runId: string; reason?: string }) =>
      havilahApi.reject(runId, reason),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["approvals"] })
      qc.invalidateQueries({ queryKey: ["runs"] })
    },
  })
}

// ─── Memory ────────────────────────────────────────────────────────────────

export function useMemory(limit = 20) {
  return useQuery({
    queryKey: ["memory", limit],
    queryFn: async () => {
      if (!isApiConfigured) return []
      try {
        return await havilahApi.searchMemory("", limit)
      } catch {
        return []
      }
    },
    staleTime: 30_000,
  })
}

// ─── Activity ──────────────────────────────────────────────────────────────

export function useActivity(limit = 20) {
  return useQuery({
    queryKey: ["activity", limit],
    queryFn: async () => {
      if (!isApiConfigured) return []
      try {
        return await havilahApi.listActivity(limit)
      } catch {
        return []
      }
    },
    staleTime: 10_000,
  })
}

// ─── Hermes runs ───────────────────────────────────────────────────────────

export function useHermesRuns() {
  return useQuery({
    queryKey: ["runs"],
    queryFn: async () => {
      if (!isApiConfigured) return []
      try {
        return await havilahApi.listRuns()
      } catch {
        return []
      }
    },
    staleTime: 5_000,
    refetchInterval: 10_000,
  })
}

export function useHermesHealth() {
  return useQuery({
    queryKey: ["hermes-health"],
    queryFn: async () => {
      if (!isApiConfigured) {
        return {
          status: "unconfigured",
          checks: {
            hermes_enabled: false,
            openai_configured: false,
            model: "—",
            llm_connected: false,
            agents_registered: 0,
          },
        } as const
      }
      return havilahApi.health()
    },
    staleTime: 30_000,
    refetchInterval: 30_000,
  })
}

export function useInstruct() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (instruction: string) =>
      havilahApi.instruct(instruction, "dashboard"),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["runs"] })
      qc.invalidateQueries({ queryKey: ["approvals"] })
      qc.invalidateQueries({ queryKey: ["activity"] })
      qc.invalidateQueries({ queryKey: ["memory"] })
    },
  })
}
