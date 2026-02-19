import { Globe } from "lucide-react"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { useLanguage } from "@/contexts/language-context"

export function LanguageToggle() {
  const { language, setLanguage } = useLanguage()

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button 
          variant="outline" 
          size="icon"
          className="relative w-10 h-10 rounded-full border-border bg-card hover:bg-accent hover:text-accent-foreground transition-all duration-300"
        >
          <Globe className="h-[1.2rem] w-[1.2rem]" />
          <span className="sr-only">Toggle language</span>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="bg-card border-border min-w-0">
        <DropdownMenuItem 
          onClick={() => setLanguage("es")}
          className={`hover:bg-accent hover:text-accent-foreground cursor-pointer flex items-center gap-2 ${
            language === "es" ? "bg-accent text-accent-foreground" : ""
          }`}
        >
          <span>🇪🇸</span>
          <span>Español</span>
        </DropdownMenuItem>
        <DropdownMenuItem 
          onClick={() => setLanguage("en")}
          className={`hover:bg-accent hover:text-accent-foreground cursor-pointer flex items-center gap-2 ${
            language === "en" ? "bg-accent text-accent-foreground" : ""
          }`}
        >
          <span>🇺🇸</span>
          <span>English</span>
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}