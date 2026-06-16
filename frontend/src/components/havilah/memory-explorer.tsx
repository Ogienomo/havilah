"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { ScrollArea } from "@/components/ui/scroll-area"
import { memoryItems, type MemoryItem, type MemoryType, type Importance } from "./mock-data"
import { Search, Brain } from "lucide-react"

const typeColors: Record<MemoryType, string> = {
  profile: "bg-sky-500/10 text-sky-500 border-sky-500/20",
  client: "bg-havilah-gold/10 text-havilah-gold border-havilah-gold/20",
  project: "bg-violet-500/10 text-violet-500 border-violet-500/20",
  communication: "bg-pink-500/10 text-pink-500 border-pink-500/20",
  operational: "bg-teal-500/10 text-teal-500 border-teal-500/20",
  research: "bg-emerald-500/10 text-emerald-500 border-emerald-500/20",
  approval: "bg-amber-500/10 text-amber-500 border-amber-500/20",
  meeting: "bg-indigo-500/10 text-indigo-500 border-indigo-500/20",
}

const importanceColors: Record<Importance, string> = {
  low: "bg-slate-500/10 text-slate-400 border-slate-500/20",
  medium: "bg-sky-500/10 text-sky-500 border-sky-500/20",
  high: "bg-amber-500/10 text-amber-500 border-amber-500/20",
  critical: "bg-red-500/10 text-red-500 border-red-500/20",
}

export function MemoryExplorer() {
  const [search, setSearch] = useState("")

  const filtered = memoryItems.filter(
    (item) =>
      item.title.toLowerCase().includes(search.toLowerCase()) ||
      item.content.toLowerCase().includes(search.toLowerCase()) ||
      item.tags.some((tag) => tag.toLowerCase().includes(search.toLowerCase()))
  )

  return (
    <Card className="border-border bg-card">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-foreground">
          <Brain className="h-5 w-5 text-havilah-gold" />
          Memory Explorer
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Search */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search memories by title, content, or tags..."
            className="border-border bg-background pl-9 placeholder:text-muted-foreground focus-visible:border-havilah-gold focus-visible:ring-havilah-gold/30"
          />
        </div>

        {/* Memory list */}
        <ScrollArea className="max-h-96">
          <div className="space-y-2">
            {filtered.length === 0 ? (
              <div className="py-8 text-center">
                <p className="text-sm text-muted-foreground">No memories found.</p>
              </div>
            ) : (
              filtered.map((item) => (
                <div
                  key={item.id}
                  className="rounded-lg border border-border bg-background p-3 transition-colors hover:border-havilah-gold/20"
                >
                  <div className="flex flex-col gap-2">
                    {/* Badges row */}
                    <div className="flex flex-wrap items-center gap-1.5">
                      <Badge variant="outline" className={typeColors[item.type]}>
                        {item.type}
                      </Badge>
                      <Badge variant="outline" className={importanceColors[item.importance]}>
                        {item.importance}
                      </Badge>
                      <span className="ml-auto text-xs text-muted-foreground">
                        {item.timestamp}
                      </span>
                    </div>

                    {/* Title */}
                    <p className="text-sm font-medium text-foreground">{item.title}</p>

                    {/* Content */}
                    <p className="text-xs leading-relaxed text-muted-foreground line-clamp-2">
                      {item.content}
                    </p>

                    {/* Tags */}
                    <div className="flex flex-wrap gap-1">
                      {item.tags.map((tag) => (
                        <span
                          key={tag}
                          className="rounded-full bg-muted px-2 py-0.5 text-[10px] text-muted-foreground"
                        >
                          #{tag}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </ScrollArea>

        {/* Count */}
        <div className="flex items-center justify-between border-t border-border pt-3">
          <span className="text-xs text-muted-foreground">
            Showing {filtered.length} of {memoryItems.length} memories
          </span>
          <span className="text-xs text-muted-foreground">1,247 total entries</span>
        </div>
      </CardContent>
    </Card>
  )
}
