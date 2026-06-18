"use client"

import { ThemeProvider as NextThemesProvider } from "next-themes"
import { AuthProvider } from "@/lib/auth-context"

export function ThemeProvider({
  children,
  ...props
}: React.ComponentProps<typeof NextThemesProvider>) {
  return (
    <NextThemesProvider {...props}>
      <AuthProvider>{children}</AuthProvider>
    </NextThemesProvider>
  )
}
