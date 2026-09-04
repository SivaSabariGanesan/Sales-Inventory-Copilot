import React from 'react';
import { useLocation } from 'react-router-dom';
import { Menu, ChevronRight, Store, ShieldCheck } from 'lucide-react';
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
    <header className="sticky top-0 z-30 flex h-16 w-full items-center justify-between border-b border-border bg-card px-4 sm:px-6 lg:px-8">
      {/* Left: Mobile Menu Trigger & Breadcrumb */}
      <div className="flex items-center gap-3">
        <Button
          variant="ghost"
          size="icon"
          className="h-9 w-9 md:hidden text-muted-foreground"
          onClick={onMenuClick}
          aria-label="Open navigation menu"
        >
          <Menu className="h-5 w-5" />
        </Button>

        {/* Breadcrumbs & Page Title */}
        <div className="flex items-center gap-2 text-sm">
          <span className="hidden sm:inline font-medium text-muted-foreground">
            {currentRoute.section}
          </span>
          <ChevronRight className="hidden sm:inline h-3.5 w-3.5 text-muted-foreground/60" />
          <span className="font-semibold text-foreground">
            {currentRoute.title}
          </span>
        </div>
      </div>

      {/* Right: Environment & System Status */}
      <div className="flex items-center gap-3">
        <div className="hidden sm:flex items-center gap-1.5 rounded-full border border-border bg-muted/50 px-2.5 py-1 text-xs text-muted-foreground">
          <span className="h-2 w-2 rounded-full bg-emerald-600"></span>
          <span>System Active</span>
        </div>

        <div className="flex items-center gap-2 rounded-md border border-border bg-background px-3 py-1.5 text-xs text-muted-foreground">
          <Store className="h-3.5 w-3.5 text-primary" />
          <span className="font-medium text-foreground">Main Store Network</span>
        </div>
      </div>
    </header>
  );
}

export default Header;
