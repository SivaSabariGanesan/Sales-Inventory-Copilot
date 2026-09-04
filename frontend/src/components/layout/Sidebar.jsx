import React from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import {
  Layers,
  LayoutDashboard,
  Package,
  TrendingUp,
  Tag,
  Building2,
  Bot,
  Settings,
  X,
} from 'lucide-react';
import { cn } from '@/lib/utils';

const navigationGroups = [
  {
    group: 'OVERVIEW',
    items: [
      { name: 'Dashboard', path: '/', icon: LayoutDashboard },
    ],
  },
  {
    group: 'OPERATIONS',
    items: [
      { name: 'Inventory', path: '/inventory', icon: Package },
      { name: 'Sales', path: '/sales', icon: TrendingUp },
    ],
  },
  {
    group: 'CATALOG',
    items: [
      { name: 'Products', path: '/products', icon: Tag },
      { name: 'Stores', path: '/stores', icon: Building2 },
    ],
  },
  {
    group: 'INTELLIGENCE',
    items: [
      { name: 'Copilot', path: '/copilot', icon: Bot, highlight: true },
    ],
  },
];

export function Sidebar({ onClose, className }) {
  const location = useLocation();

  return (
    <aside
      className={cn(
        'flex h-full w-64 flex-col border-r border-border bg-card select-none',
        className,
      )}
    >
      {/* Brand Header */}
      <div className="flex h-16 items-center justify-between border-b border-border px-4">
        <NavLink to="/" className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-md bg-primary text-primary-foreground shadow-sm">
            <Layers className="h-5 w-5" />
          </div>
          <div className="flex flex-col">
            <span className="text-sm font-semibold tracking-tight text-foreground">
              Retail Copilot
            </span>
            <span className="text-[11px] font-medium text-muted-foreground">
              Operations & Insights
            </span>
          </div>
        </NavLink>

        {onClose && (
          <button
            type="button"
            onClick={onClose}
            className="flex h-8 w-8 items-center justify-center rounded-md text-muted-foreground hover:bg-muted hover:text-foreground md:hidden"
            aria-label="Close sidebar"
          >
            <X className="h-4 w-4" />
          </button>
        )}
      </div>

      {/* Navigation Links */}
      <div className="flex-1 overflow-y-auto px-3 py-4 space-y-6">
        {navigationGroups.map((navGroup) => (
          <div key={navGroup.group} className="space-y-1">
            <div className="px-3 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
              {navGroup.group}
            </div>
            <div className="mt-1 space-y-0.5">
              {navGroup.items.map((item) => {
                const Icon = item.icon;
                const isActive =
                  item.path === '/'
                    ? location.pathname === '/'
                    : location.pathname.startsWith(item.path);

                return (
                  <NavLink
                    key={item.path}
                    to={item.path}
                    onClick={onClose}
                    className={cn(
                      'group flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors',
                      isActive
                        ? 'bg-primary text-primary-foreground shadow-sm'
                        : 'text-muted-foreground hover:bg-muted hover:text-foreground',
                    )}
                  >
                    <Icon
                      className={cn(
                        'h-4 w-4 shrink-0 transition-colors',
                        isActive
                          ? 'text-primary-foreground'
                          : item.highlight
                          ? 'text-secondary group-hover:text-foreground'
                          : 'text-muted-foreground group-hover:text-foreground',
                      )}
                    />
                    <span className="truncate">{item.name}</span>
                  </NavLink>
                );
              })}
            </div>
          </div>
        ))}
      </div>

      {/* Bottom Area: Settings */}
      <div className="border-t border-border p-3">
        <NavLink
          to="/settings"
          onClick={onClose}
          className={cn(
            'flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors',
            location.pathname === '/settings'
              ? 'bg-primary text-primary-foreground shadow-sm'
              : 'text-muted-foreground hover:bg-muted hover:text-foreground',
          )}
        >
          <Settings className="h-4 w-4 shrink-0" />
          <span className="truncate">Settings</span>
        </NavLink>
      </div>
    </aside>
  );
}

export default Sidebar;
