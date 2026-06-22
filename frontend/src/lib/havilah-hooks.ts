"use client"

/**
 * Havilah OS — React hooks for the dashboard
 * ----------------------------------------------------------------------------
 * Wraps the havilahApi client with React Query.
 * Falls back to mock data when the API is not configured (preview environments).
 */

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { havilahApi, isApiConfigured } from "./havilah-api"
import {
  agents as mockAgents,
  approvalItems as mockApprovals,
  memoryItems as mockMemory,
  activityEvents as mockActivity,
} from "@/components/havilah/mock-data"

// ─── Agents ────────────────────────────────────────────────────────────────

export function useAgents() {
  return useQuery({
    queryKey: ["agents"],
    queryFn: async () => {
      if (!isApiConfigured) return mockAgents
      const remote = await havilahApi.listAgents()
      // Map remote → shape used by mock-data.ts (icon is set client-side)
      return remote.map((a, i) => ({
        id: a.name,
        name: a.display_name,
        // Preserve icons from mock list to keep the visual identity
        icon: mockAgents[i]?.icon ?? mockAgents[0].icon,
        status: a.is_active ? "active" : "idle",
        capabilities: a.capabilities,
        color: mockAgents[i]?.color ?? "#d4a853",
        description: a.description,
      }))
    },
    staleTime: 30_000,
  })
}

// ─── Approvals ─────────────────────────────────────────────────────────────

export function useApprovals() {
  return useQuery({
    queryKey: ["approvals"],
    queryFn: async () => {
      if (!isApiConfigured) return mockApprovals
      const remote = await havilahApi.listApprovals({ status: "pending" })
      return remote.map((a) => ({
        id: a.id,
        actionType: a.action_type as never,
        riskLevel: a.risk_level as never,
        summary: a.summary,
        requestedBy: a.requested_by,
        timestamp: a.created_at,
        details: "",
      }))
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
      if (!isApiConfigured) return mockMemory
      const remote = await havilahApi.searchMemory("", limit)
      return remote.map((m) => ({
        id: m.id,
        type: m.type as never,
        importance: m.importance as never,
        title: m.title,
        content: m.content,
        timestamp: m.created_at,
        tags: m.tags ?? [],
      }))
    },
    staleTime: 30_000,
  })
}

// ─── Activity ──────────────────────────────────────────────────────────────

export function useActivity(limit = 20) {
  return useQuery({
    queryKey: ["activity", limit],
    queryFn: async () => {
      if (!isApiConfigured) return mockActivity
      const remote = await havilahApi.listActivity(limit)
      return remote.map((e, i) => ({
        id: e.aggregate_id,
        category: (e.aggregate_type as never) ?? "system",
        title: e.event_type.replace(/_/g, " "),
        description: JSON.stringify(e.payload).slice(0, 120),
        timestamp: e.created_at,
        color: mockActivity[i % mockActivity.length].color,
      }))
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
      return havilahApi.listRuns()
    },
    staleTime: 5_000,
    refetchInterval: 5_000, // Poll for live updates
  })
}

export function useHermesHealth() {
  return useQuery({
    queryKey: ["hermes-health"],
    queryFn: async () => {
      if (!isApiConfigured) {
        return {
          status: "mock",
          llm: { configured: false, model: "—", connected: false },
          hermes_enabled: false,
          agents_registered: 10,
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
