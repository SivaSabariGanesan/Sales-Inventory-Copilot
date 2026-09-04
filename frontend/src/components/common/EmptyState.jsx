import React from 'react';
import { cn } from '@/lib/utils';
import { PackageOpen } from 'lucide-react';

export function EmptyState({
  icon: Icon = PackageOpen,
  title = 'No data available',
  description = 'Data will populate here once connected.',
  action,
  className,
}) {
  return (
    <div
      className={cn(
        'flex min-h-[200px] flex-col items-center justify-center rounded-lg border border-dashed border-border bg-card/40 p-6 sm:p-8 text-center transition-colors',
        className,
      )}
    >
      <div className="flex h-11 w-11 items-center justify-center rounded-full bg-muted text-muted-foreground ring-4 ring-muted/30 mb-3">
        <Icon className="h-5 w-5" aria-hidden="true" />
      </div>
      <h3 className="text-sm font-semibold text-foreground tracking-tight">{title}</h3>
      <p className="mt-1 max-w-sm text-xs text-muted-foreground leading-relaxed">
        {description}
      </p>
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}

export default EmptyState;
