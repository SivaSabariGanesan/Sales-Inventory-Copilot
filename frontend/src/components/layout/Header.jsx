import React from 'react';
import { useLocation } from 'react-router-dom';
import { Menu, ChevronRight, Store, Activity } from 'lucide-react';
import { Button } from '@/components/ui/button';

const routeTitles = {
  '/': { title: 'Dashboard', section: 'Overview' },
  '/inventory': { title: 'Inventory Optimization', section: 'Operations' },
  '/sales': { title: 'Sales Analytics', section: 'Operations' },
  '/products': { title: 'Product Catalog', section: 'Catalog' },
  '/stores': { title: 'Store Network', section: 'Catalog' },
  '/copilot': { title: 'Retail Copilot Intelligence', section: 'Intelligence' },
  '/settings': { title: 'System Settings', section: 'Configuration' },
};

export function Header({ onMenuClick }) {
  const location = useLocation();
  const currentRoute = routeTitles[location.pathname] || {
    title: 'Workspace',
    section: 'Retail Copilot',
  };

  return (
    <header className="sticky top-0 z-30 flex h-16 w-full shrink-0 items-center justify-between border-b border-border bg-card/95 px-4 backdrop-blur-xs sm:px-6 lg:px-8">
      {/* Left: Mobile Menu Trigger & Responsive Breadcrumbs */}
      <div className="flex items-center gap-3 min-w-0">
        <Button
          variant="ghost"
          size="icon"
          className="h-9 w-9 md:hidden text-muted-foreground shrink-0"
          onClick={onMenuClick}
          aria-label="Open navigation menu"
        >
          <Menu className="h-5 w-5" />
        </Button>

        {/* Breadcrumb Navigation */}
        <nav aria-label="Breadcrumb" className="flex items-center gap-2 text-sm truncate">
          <span className="hidden sm:inline font-medium text-muted-foreground text-xs uppercase tracking-wider">
            {currentRoute.section}
          </span>
          <ChevronRight className="hidden sm:inline h-3.5 w-3.5 text-muted-foreground/60 shrink-0" aria-hidden="true" />
          <span className="font-bold text-foreground truncate text-sm sm:text-base">
            {currentRoute.title}
          </span>
        </nav>
      </div>

      {/* Right: Environment & System Status Area */}
      <div className="flex items-center gap-2 sm:gap-3 shrink-0">
        <div className="hidden sm:flex items-center gap-1.5 rounded-full border border-border bg-muted/40 px-2.5 py-1 text-xs text-muted-foreground">
          <span className="h-2 w-2 rounded-full bg-emerald-600 animate-pulse" aria-hidden="true"></span>
          <span>System Active</span>
        </div>

        <div className="flex items-center gap-1.5 sm:gap-2 rounded-md border border-border bg-background px-2.5 sm:px-3 py-1.5 text-xs text-muted-foreground">
          <Store className="h-3.5 w-3.5 text-primary shrink-0" aria-hidden="true" />
          <span className="font-semibold text-foreground hidden xs:inline">Main Store Network</span>
          <span className="font-semibold text-foreground xs:hidden">Network</span>
        </div>
      </div>
    </header>
  );
}

export default Header;
