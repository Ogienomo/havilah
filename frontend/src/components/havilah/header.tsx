"use client"

import { useTheme } from "next-themes"
import { Sun, Moon, Zap, Activity, LogOut, User } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
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
    <header className="sticky top-0 z-50 border-b border-border bg-background/80 backdrop-blur-xl">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="flex h-16 items-center justify-between">
          {/* Logo & Title */}
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-gradient-to-br from-havilah-gold to-havilah-gold-dark shadow-lg shadow-havilah-gold/20">
              <Zap className="h-5 w-5 text-white" />
            </div>
            <div className="flex flex-col">
              <h1 className="text-lg font-bold tracking-tight">
                <span className="gold-gradient-text">Havilah</span>{" "}
                <span className="text-foreground">OS</span>
              </h1>
              <p className="hidden text-xs text-muted-foreground sm:block">
                AI Executive Operating System
              </p>
            </div>
          </div>

          {/* Status & Controls */}
          <div className="flex items-center gap-3">
            {/* System Status */}
            <div className="hidden items-center gap-2 rounded-full border border-border bg-card px-3 py-1.5 sm:flex">
              <span className="relative flex h-2 w-2">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" />
                <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-500" />
              </span>
              <span className="text-xs font-medium text-foreground">System Active</span>
            </div>

            {/* Hermes Status */}
            <div className="hidden items-center gap-2 rounded-full border border-border bg-card px-3 py-1.5 md:flex">
              <Activity className="h-3.5 w-3.5 text-havilah-gold" />
              <span className="text-xs font-medium text-foreground">Hermes Online</span>
            </div>

            {/* API Endpoints Badge */}
            <Badge
              variant="outline"
              className="hidden border-havilah-gold/30 text-havilah-gold lg:flex"
            >
              155 Endpoints
            </Badge>

            {/* Theme Toggle */}
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
              className="h-9 w-9 rounded-lg hover:bg-havilah-gold/10"
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
                    className="h-9 px-2 sm:px-3 rounded-lg hover:bg-havilah-gold/10 gap-2"
                  >
                    <div className="flex h-7 w-7 items-center justify-center rounded-full bg-gradient-to-br from-havilah-gold to-havilah-gold-dark text-white text-xs font-bold">
                      {user.full_name?.charAt(0)?.toUpperCase() ?? "U"}
                    </div>
                    <span className="hidden sm:inline text-sm font-medium text-foreground max-w-[120px] truncate">
                      {user.full_name}
                    </span>
                    {user.is_admin && (
                      <Badge
                        variant="outline"
                        className="hidden md:inline border-havilah-gold/40 text-havilah-gold text-[10px] px-1 py-0"
                      >
                        ADMIN
                      </Badge>
                    )}
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="w-56">
                  <DropdownMenuLabel className="font-normal">
                    <div className="flex flex-col space-y-1">
                      <p className="text-sm font-medium leading-none">{user.full_name}</p>
                      <p className="text-xs leading-none text-muted-foreground">{user.email}</p>
                      <p className="text-xs leading-none text-muted-foreground mt-1">
                        Role: {user.role ?? (user.is_admin ? "admin" : "viewer")}
                      </p>
                    </div>
                  </DropdownMenuLabel>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem
                    onClick={() => logout()}
                    className="text-red-600 dark:text-red-400 focus:text-red-700 dark:focus:text-red-300 cursor-pointer"
                  >
                    <LogOut className="h-4 w-4 mr-2" />
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
