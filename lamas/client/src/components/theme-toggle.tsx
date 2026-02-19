import { Moon, Sun, Monitor } from "lucide-react"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { useTheme } from "@/components/theme-provider"

export function ThemeToggle() {
  const { setTheme, theme } = useTheme()

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button 
          variant="outline" 
          size="icon"
          className="relative w-10 h-10 rounded-full border-border bg-card hover:bg-accent hover:text-accent-foreground transition-all duration-300"
        >
          <Sun className="h-[1.2rem] w-[1.2rem] rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
          <Moon className="absolute h-[1.2rem] w-[1.2rem] rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
          <span className="sr-only">Toggle theme</span>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="bg-card border-border min-w-0">
        <DropdownMenuItem 
          onClick={() => theme !== "light" && setTheme("light")}
          className={`hover:bg-accent hover:text-accent-foreground cursor-pointer flex items-center gap-2 ${
            theme === "light" ? "bg-accent text-accent-foreground" : ""
          }`}
        >
          <Sun className="h-4 w-4" />
          <span>Light</span>
        </DropdownMenuItem>
        <DropdownMenuItem 
          onClick={() => theme !== "dark" && setTheme("dark")}
          className={`hover:bg-accent hover:text-accent-foreground cursor-pointer flex items-center gap-2 ${
            theme === "dark" ? "bg-accent text-accent-foreground" : ""
          }`}
        >
          <Moon className="h-4 w-4" />
          <span>Dark</span>
        </DropdownMenuItem>
        <DropdownMenuItem 
          onClick={() => theme !== "system" && setTheme("system")}
          className={`hover:bg-accent hover:text-accent-foreground cursor-pointer flex items-center gap-2 ${
            theme === "system" ? "bg-accent text-accent-foreground" : ""
          }`}
        >
          <Monitor className="h-4 w-4" />
          <span>System</span>
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}