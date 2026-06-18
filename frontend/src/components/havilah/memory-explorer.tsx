"use client"

import { useEffect, useState, useCallback, useRef } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Skeleton } from "@/components/ui/skeleton"
import { Button } from "@/components/ui/button"
import {
  havilahApi,
  MemoryItem,
  isApiConfigured,
  ApiError,
} from "@/lib/havilah-api"
import { Search, Brain, AlertCircle, RefreshCw, Sparkles } from "lucide-react"

// Memory types from the spec — colors mirror mock-data.ts
const typeColors: Record<string, string> = {
  profile: "bg-sky-500/10 text-sky-500 border-sky-500/20",
  client: "bg-havilah-gold/10 text-havilah-gold border-havilah-gold/20",
  project: "bg-violet-500/10 text-violet-500 border-violet-500/20",
  communication: "bg-pink-500/10 text-pink-500 border-pink-500/20",
  operational: "bg-teal-500/10 text-teal-500 border-teal-500/20",
  research: "bg-emerald-500/10 text-emerald-500 border-emerald-500/20",
  approval: "bg-amber-500/10 text-amber-500 border-amber-500/20",
  meeting: "bg-indigo-500/10 text-indigo-500 border-indigo-500/20",
  decision: "bg-rose-500/10 text-rose-500 border-rose-500/20",
}

const importanceColors: Record<string, string> = {
  low: "bg-slate-500/10 text-slate-400 border-slate-500/20",
  medium: "bg-sky-500/10 text-sky-500 border-sky-500/20",
  high: "bg-amber-500/10 text-amber-500 border-amber-500/20",
  critical: "bg-red-500/10 text-red-500 border-red-500/20",
}

function getTypeColor(type?: string): string {
  if (!type) return "bg-slate-500/10 text-slate-400 border-slate-500/20"
  return typeColors[type] ?? "bg-slate-500/10 text-slate-400 border-slate-500/20"
}

function getImportanceColor(importance?: string): string {
  if (!importance) return importanceColors.low
  return importanceColors[importance] ?? importanceColors.low
}

function timeAgo(iso?: string): string {
  if (!iso) return ""
  const d = new Date(iso)
  if (isNaN(d.getTime())) return ""
  const diff = Math.max(0, Date.now() - d.getTime())
  const minutes = Math.floor(diff / 60000)
  if (minutes < 60) return `${minutes}m ago`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}h ago`
  const days = Math.floor(hours / 24)
  if (days < 7) return `${days}d ago`
  return d.toLocaleDateString()
}

type LoadState = "idle" | "loading" | "live" | "error" | "empty"

export function MemoryExplorer() {
  const [search, setSearch] = useState("")
  const [results, setResults] = useState<MemoryItem[]>([])
  const [state, setState] = useState<LoadState>("idle")
  const [errorMsg, setErrorMsg] = useState("")
  const [hasSearched, setHasSearched] = useState(false)
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  const runSearch = useCallback(async (query: string) => {
    if (!isApiConfigured) {
      setState("empty")
      return
    }
    if (!query.trim()) {
      setState("idle")
      setResults([])
      setHasSearched(false)
      return
    }
    setState("loading")
    setErrorMsg("")
    setHasSearched(true)
    try {
      const data = await havilahApi.searchMemory(query.trim(), 20)
      if (Array.isArray(data) && data.length > 0) {
        setResults(data)
        setState("live")
      } else {
        setResults([])
        setState("empty")
      }
    } catch (e: any) {
      setErrorMsg(e instanceof ApiError ? e.message : String(e))
      setState("error")
    }
  }, [])

  // Debounced search on input change
  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current)
    debounceRef.current = setTimeout(() => {
      runSearch(search)
    }, 350)
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current)
    }
  }, [search, runSearch])

  const handleManualSearch = () => {
    if (debounceRef.current) clearTimeout(debounceRef.current)
    runSearch(search)
  }

  return (
    <Card className="border-border bg-card">
      <CardHeader>
        <CardTitle className="flex items-center justify-between text-foreground">
          <span className="flex items-center gap-2">
            <Brain className="h-5 w-5 text-havilah-gold" />
            Memory Explorer
            {state === "live" && (
              <Badge variant="outline" className="border-emerald-500/30 text-emerald-500 text-[10px]">
                LIVE
              </Badge>
            )}
          </span>
          {state === "live" && (
            <Badge variant="outline" className="border-havilah-gold/30 text-havilah-gold text-xs">
              {results.length} found
            </Badge>
          )}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Search */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            onKeyDown={(e) => { if (e.key === "Enter") handleManualSearch() }}
            placeholder="Search memories… (e.g. 'project atlas', 'client preferences')"
            className="border-border bg-background pl-9 placeholder:text-muted-foreground focus-visible:border-havilah-gold focus-visible:ring-havilah-gold/30"
            disabled={state === "loading"}
          />
        </div>

        {/* Memory list / states */}
        {state === "idle" && (
          <div className="flex flex-col items-center justify-center py-10 gap-3 text-center">
            <div className="flex h-12 w-12 items-center justify-center rounded-full bg-havilah-gold/10">
              <Sparkles className="h-6 w-6 text-havilah-gold" />
            </div>
            <div>
              <p className="text-sm font-medium text-foreground">Search your institutional memory</p>
              <p className="text-xs text-muted-foreground/70 max-w-sm mt-1">
                Memories are captured automatically as Hermes runs. Type a search query above
                to surface related decisions, profiles, projects, and communications.
              </p>
            </div>
          </div>
        )}

        {state === "loading" && (
          <div className="space-y-2">
            {Array.from({ length: 4 }).map((_, i) => (
              <Skeleton key={i} className="h-20 rounded-lg" />
            ))}
          </div>
        )}

        {state === "error" && (
          <div className="flex flex-col items-center justify-center py-8 gap-3 text-center">
            <AlertCircle className="h-8 w-8 text-red-500" />
            <p className="text-sm text-muted-foreground">Search failed.</p>
            <p className="text-xs text-muted-foreground/70 max-w-md">{errorMsg}</p>
            <Button variant="outline" size="sm" onClick={handleManualSearch} className="mt-2">
              <RefreshCw className="h-3 w-3 mr-2" />
              Retry
            </Button>
          </div>
        )}

        {state === "empty" && hasSearched && (
          <div className="flex flex-col items-center justify-center py-8 gap-2 text-center">
            <Brain className="h-8 w-8 text-muted-foreground/40" />
            <p className="text-sm text-muted-foreground">
              No memories matched &ldquo;{search}&rdquo;.
            </p>
            <p className="text-xs text-muted-foreground/70 max-w-sm">
              Try a different search term. New memories are captured each time Hermes
              completes an instruction.
            </p>
          </div>
        )}

        {state === "empty" && !hasSearched && isApiConfigured && (
          <div className="flex flex-col items-center justify-center py-8 gap-2 text-center">
            <Brain className="h-8 w-8 text-muted-foreground/40" />
            <p className="text-sm text-muted-foreground">No memories yet.</p>
            <p className="text-xs text-muted-foreground/70 max-w-sm">
              Run a Hermes instruction to start capturing institutional memory.
            </p>
          </div>
        )}

        {state === "live" && (
          <ScrollArea className="max-h-[28rem]">
            <div className="space-y-2.5 pr-1">
              {results.map((item, idx) => {
                const id = (item as any).id ?? (item as any).memory_id ?? `mem-${idx}`
                return (
                  <div
                    key={id}
                    className="rounded-lg border border-border bg-background p-3.5 transition-colors hover:border-havilah-gold/20"
                  >
                    <div className="flex flex-col gap-2">
                      <div className="flex flex-wrap items-center gap-1.5">
                        {item.type && (
                          <Badge variant="outline" className={getTypeColor(item.type)}>
                            {item.type}
                          </Badge>
                        )}
                        {item.importance && (
                          <Badge variant="outline" className={getImportanceColor(item.importance)}>
                            {item.importance}
                          </Badge>
                        )}
                        {item.created_at && (
                          <span className="ml-auto text-xs text-muted-foreground">
                            {timeAgo(item.created_at)}
                          </span>
                        )}
                      </div>

                      {item.title && (
                        <p className="text-sm font-medium text-foreground leading-snug">{item.title}</p>
                      )}

                      {item.content && (
                        <p className="text-xs leading-relaxed text-muted-foreground line-clamp-3">
                          {item.content}
                        </p>
                      )}

                      {item.tags && item.tags.length > 0 && (
                        <div className="flex flex-wrap gap-1 pt-1">
                          {item.tags.map((tag) => (
                            <span
                              key={tag}
                              className="rounded-full bg-muted px-2 py-0.5 text-[10px] text-muted-foreground"
                            >
                              #{tag}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                )
              })}
            </div>
          </ScrollArea>
        )}

        {/* Count footer */}
        <div className="flex items-center justify-between border-t border-border pt-3">
          <span className="text-xs text-muted-foreground">
            {state === "live"
              ? `Showing ${results.length} ${results.length === 1 ? "memory" : "memories"}`
              : "Ready to search"}
          </span>
          <span className="text-xs text-muted-foreground/60">
            POST /api/memory/search
          </span>
        </div>
      </CardContent>
    </Card>
  )
}
