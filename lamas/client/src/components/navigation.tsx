import { useState, useEffect, useRef } from "react";
import { Menu, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";
import { ThemeToggle } from "@/components/theme-toggle";
import { LanguageToggle } from "@/components/language-toggle";
import { useLanguage, type Section } from "@/contexts/language-context";
import { useLocation } from "wouter";

export default function Navigation() {
  const [isScrolled, setIsScrolled] = useState(false);
  const [isOpen, setIsOpen] = useState(false);
  const { t, language } = useLanguage();
  const [location] = useLocation();
  
  // Get current section from URL
  const getCurrentSection = (): Section => {
    const pathParts = location.split('/').filter(Boolean);
    return (pathParts[1] as Section) || "home";
  };
  
  const currentSection = getCurrentSection();

  const navigationItems = [
    { section: "home" as Section, label: t("nav.home") },
    { section: "about" as Section, label: t("nav.about") },
    { section: "education" as Section, label: t("nav.education") },
    { section: "experience" as Section, label: t("nav.experience") },
    { section: "skills" as Section, label: t("nav.skills") },
    { section: "projects" as Section, label: t("nav.projects") },
    { section: "contact" as Section, label: t("nav.contact") },
  ];

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 10);
    };

    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  const handleClick = (section: Section) => {
    setIsOpen(false);
    
    // Update URL first
    const newPath = section === "home" ? `/${language}` : `/${language}/${section}`;
    window.history.pushState({}, '', newPath);
    
    // Find and scroll to element
    setTimeout(() => {
      const element = document.getElementById(section);
      if (element) {
        element.scrollIntoView({ behavior: "smooth", block: "start" });
      }
    }, 100);
  };

  return (
    <nav
      className={`fixed top-0 w-full z-50 transition-all duration-300 ${
        isScrolled ? "bg-navy/95 backdrop-blur-sm border-b border-border" : ""
      }`}
    >
      <div className="container-spacing">
        <div className="flex justify-between items-center py-4">
          <button
            onClick={() => handleClick("home")}
            className="text-xl font-bold text-accent hover:text-accent/80 transition-colors"
          >
            Keylor Lamas
          </button>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center space-x-8">
            {navigationItems.map((item) => (
              <button
                key={item.section}
                onClick={() => handleClick(item.section)}
                className={`hover:text-accent transition-colors cursor-pointer ${
                  currentSection === item.section ? "text-accent" : ""
                }`}
              >
                {item.label}
              </button>
            ))}
            <div className="flex items-center space-x-2">
              <LanguageToggle />
              <ThemeToggle />
            </div>
          </div>

          {/* Mobile Navigation */}
          <div className="md:hidden flex items-center space-x-2">
            <LanguageToggle />
            <ThemeToggle />
            <Sheet open={isOpen} onOpenChange={setIsOpen}>
              <SheetTrigger asChild>
                <Button variant="ghost" size="icon">
                  <Menu className="h-6 w-6" />
                </Button>
              </SheetTrigger>
            <SheetContent side="right" className="bg-card border-border">
              <div className="flex flex-col space-y-4 mt-8">
                {navigationItems.map((item) => (
                  <button
                    key={item.section}
                    onClick={() => handleClick(item.section)}
                    className={`text-left py-2 hover:text-accent transition-colors text-lg ${
                      currentSection === item.section ? "text-accent" : ""
                    }`}
                  >
                    {item.label}
                  </button>
                ))}
              </div>
            </SheetContent>
            </Sheet>
          </div>
        </div>
      </div>
    </nav>
  );
}