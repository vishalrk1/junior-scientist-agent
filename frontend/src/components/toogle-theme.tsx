import { Moon, Sun } from "lucide-react"

import { Button } from "@/components/ui/button"
import { useTheme } from "@/contexts/theme-provider"

export function ModeToggle() {
  const { setTheme, theme } = useTheme()

  return (
    <Button
      variant="ghost"
      size="icon"
      onClick={() => setTheme(theme === "light" ? "dark" : "light")}
      aria-label={`Switch to ${theme === "light" ? "dark" : "light"} mode`}
      className="bg-primary/10"
    >
      {theme === "light" ? <Moon className="h-16 w-16" /> : <Sun className="h-16 w-16" />}
    </Button>
  )
}
