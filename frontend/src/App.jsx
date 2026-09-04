import React from 'react';
import {
  Layers,
  LayoutDashboard,
  TrendingUp,
  Package,
  Bot,
  Settings,
  ShieldCheck,
  Building2,
} from 'lucide-react';
import { Button } from '@/components/ui/button';

function App() {
  return (
    <div className="min-h-screen bg-background flex flex-col">
      {/* Enterprise Top Navigation Bar */}
      <header className="sticky top-0 z-50 w-full border-b border-border bg-card/95 backdrop-blur-sm">
        <div className="mx-auto flex h-14 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
          {/* Brand Identity */}
          <div className="flex items-center gap-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-md bg-primary text-primary-foreground">
              <Layers className="h-4 w-4" />
            </div>
            <div className="flex flex-col">
              <span className="text-sm font-semibold tracking-tight text-foreground">
                Retail Sales & Inventory Copilot
              </span>
              <span className="text-[11px] text-muted-foreground font-medium">
                Enterprise Decision Support System
              </span>
            </div>
          </div>

          {/* Navigation Placeholders */}
          <nav className="hidden md:flex items-center gap-1 text-sm font-medium">
            <span className="flex items-center gap-2 rounded-md bg-muted px-3 py-1.5 text-foreground">
              <LayoutDashboard className="h-4 w-4 text-primary" />
              Overview
            </span>
            <span className="flex items-center gap-2 rounded-md px-3 py-1.5 text-muted-foreground hover:text-foreground cursor-pointer transition-colors">
              <TrendingUp className="h-4 w-4" />
              Sales Analytics
            </span>
            <span className="flex items-center gap-2 rounded-md px-3 py-1.5 text-muted-foreground hover:text-foreground cursor-pointer transition-colors">
              <Package className="h-4 w-4" />
              Inventory Optimization
            </span>
            <span className="flex items-center gap-2 rounded-md px-3 py-1.5 text-muted-foreground hover:text-foreground cursor-pointer transition-colors">
              <Bot className="h-4 w-4 text-secondary" />
              Copilot Assistant
            </span>
          </nav>

          {/* System Status & Actions */}
          <div className="flex items-center gap-3">
            <div className="hidden sm:flex items-center gap-1.5 rounded-full border border-border bg-muted/50 px-2.5 py-1 text-xs text-muted-foreground">
              <span className="h-2 w-2 rounded-full bg-emerald-600"></span>
              <span>System Online</span>
            </div>
            <Button variant="outline" size="sm" className="gap-1.5 text-xs">
              <Building2 className="h-3.5 w-3.5 text-muted-foreground" />
              Store: #0412
            </Button>
            <Button variant="ghost" size="icon" className="h-8 w-8 text-muted-foreground">
              <Settings className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </header>

      {/* Main Content Area Placeholder */}
      <main className="flex-1 mx-auto w-full max-w-7xl p-4 sm:p-6 lg:p-8">
        <div className="rounded-lg border border-border bg-card p-8 shadow-sm">
          <div className="max-w-xl">
            <div className="inline-flex items-center gap-2 rounded-md bg-primary/10 px-2.5 py-1 text-xs font-semibold text-primary mb-4">
              <ShieldCheck className="h-3.5 w-3.5" />
              Design System Foundation Ready
            </div>
            <h1 className="text-2xl font-bold tracking-tight text-foreground">
              Enterprise Retail Workspace
            </h1>
            <p className="mt-2 text-sm text-muted-foreground leading-relaxed">
              The shadcn/ui foundation, Tailwind CSS token hierarchy, and enterprise color palette
              have been established. Ready for business modules and decision-support features in subsequent phases.
            </p>

            <div className="mt-6 flex flex-wrap items-center gap-3">
              <Button size="sm">Primary Action</Button>
              <Button variant="secondary" size="sm">Secondary Action</Button>
              <Button variant="outline" size="sm">System Settings</Button>
            </div>
          </div>
        </div>
      </main>

      {/* Minimal Footer */}
      <footer className="border-t border-border bg-card py-3">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8 text-xs text-muted-foreground">
          <span>Retail Sales & Inventory Copilot • Platform Shell</span>
          <span>Theme: Enterprise Slate & Navy</span>
        </div>
      </footer>
    </div>
  );
}

export default App;
