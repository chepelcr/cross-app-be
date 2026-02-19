import { Switch, Route, useLocation } from "wouter";
import { queryClient } from "./lib/queryClient";
import { QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import { ThemeProvider } from "@/components/theme-provider";
import { LanguageProvider } from "@/contexts/language-context";
import { useEffect } from "react";
import Home from "@/pages/home";
import ProjectsPage from "@/pages/projects";
import NotFound from "@/pages/not-found";

function Router() {
  const [location, navigate] = useLocation();

  // Handle root redirect to default language
  useEffect(() => {
    if (location === "/") {
      const savedLanguage = localStorage.getItem("portfolio-language") || "es";
      navigate(`/${savedLanguage}`);
    }
  }, [location, navigate]);

  return (
    <Switch>
      {/* Language-prefixed routes */}
      <Route path="/es" component={Home} />
      <Route path="/es/:section" component={Home} />
      <Route path="/en" component={Home} />
      <Route path="/en/:section" component={Home} />
      
      {/* Projects page routes */}
      <Route path="/es/projects" component={ProjectsPage} />
      <Route path="/en/projects" component={ProjectsPage} />
      
      {/* Fallback for old URLs without language prefix */}
      <Route path="/" component={() => null} />
      <Route component={NotFound} />
    </Switch>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider defaultTheme="dark" storageKey="portfolio-theme">
        <LanguageProvider>
          <TooltipProvider>
            <div className="scroll-smooth">
              <Toaster />
              <Router />
            </div>
          </TooltipProvider>
        </LanguageProvider>
      </ThemeProvider>
    </QueryClientProvider>
  );
}

export default App;
