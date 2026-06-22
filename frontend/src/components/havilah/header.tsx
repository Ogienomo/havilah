"use client"

import { Sun, Moon, Zap, Activity, LogOut } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { useTheme } from "next-themes"
import { useAuth } from "@/lib/auth-context"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"

export function Header() {
  const { theme, setTheme } = useTheme()
  const { user, logout } = useAuth()

  return (
    <header className="sticky top-0 z-50 border-b border-border/50 bg-background/90 backdrop-blur-xl">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="flex h-[60px] items-center justify-between">

          {/* Logo */}
          <div className="flex items-center gap-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-havilah-gold/15 ring-1 ring-havilah-gold/20">
              <Zap className="h-4 w-4 text-havilah-gold" />
            </div>
            <div>
              <h1 className="text-[15px] font-bold leading-none tracking-tight">
                <span className="gold-gradient-text">Havilah</span>{" "}
                <span className="text-foreground">OS</span>
              </h1>
              <p className="text-[10px] text-muted-foreground/60 mt-0.5 hidden sm:block tracking-wide">
                AI EXECUTIVE OPERATING SYSTEM
              </p>
            </div>
          </div>

          {/* Status + Controls */}
          <div className="flex items-center gap-2">

            {/* System Active */}
            <div className="hidden items-center gap-1.5 rounded-full border border-border/60 bg-card/60 px-3 py-1.5 sm:flex">
              <span className="relative flex h-1.5 w-1.5">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" />
                <span className="relative inline-flex h-1.5 w-1.5 rounded-full bg-emerald-500" />
              </span>
              <span className="text-[11px] font-medium text-foreground/80">System Active</span>
            </div>

            {/* Hermes Online */}
            <div className="hidden items-center gap-1.5 rounded-full border border-border/60 bg-card/60 px-3 py-1.5 md:flex">
              <Activity className="h-3 w-3 text-havilah-gold" />
              <span className="text-[11px] font-medium text-foreground/80">Hermes Online</span>
            </div>

            {/* Theme toggle */}
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
              className="h-8 w-8 rounded-lg text-muted-foreground hover:text-foreground hover:bg-accent/60"
            >
              <Sun className="h-4 w-4 rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
              <Moon className="absolute h-4 w-4 rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
              <span className="sr-only">Toggle theme</span>
            </Button>

            {/* User menu */}
            {user && (
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button
                    variant="ghost"
                    className="h-8 px-2 rounded-lg hover:bg-accent/60 gap-2"
                  >
                    <div className="flex h-6 w-6 items-center justify-center rounded-full bg-havilah-gold/20 text-havilah-gold text-[11px] font-bold ring-1 ring-havilah-gold/30">
                      {user.full_name?.charAt(0)?.toUpperCase() ?? "U"}
                    </div>
                    <span className="hidden sm:inline text-[13px] font-medium text-foreground/90 max-w-[110px] truncate">
                      {user.full_name}
                    </span>
                    {user.is_admin && (
                      <Badge variant="outline" className="hidden md:inline border-havilah-gold/30 text-havilah-gold text-[9px] px-1 py-0 leading-none">
                        ADMIN
                      </Badge>
                    )}
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="w-52 bg-card border-border/60">
                  <DropdownMenuLabel className="font-normal pb-2">
                    <p className="text-sm font-medium text-foreground">{user.full_name}</p>
                    <p className="text-xs text-muted-foreground/70 mt-0.5">{user.email}</p>
                    <p className="text-xs text-muted-foreground/50 mt-0.5 capitalize">
                      {user.role ?? (user.is_admin ? "admin" : "viewer")}
                    </p>
                  </DropdownMenuLabel>
                  <DropdownMenuSeparator className="bg-border/60" />
                  <DropdownMenuItem
                    onClick={() => logout()}
                    className="text-red-400 focus:text-red-300 focus:bg-red-500/10 cursor-pointer"
                  >
                    <LogOut className="h-3.5 w-3.5 mr-2" />
                    Sign out
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            )}
          </div>

        </div>
      </div>
    </header>
  )
}
