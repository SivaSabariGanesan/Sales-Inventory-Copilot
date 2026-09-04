import React from 'react';
import { cn } from '@/lib/utils';

export function SectionHeader({
  title,
  description,
  badge,
  action,
  className,
}) {
  return (
    <div className={cn('mb-3 flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between', className)}>
      <div>
        <div className="flex items-center gap-2">
          <h2 className="text-base font-semibold text-foreground">
            {title}
          </h2>
          {badge && <div>{badge}</div>}
        </div>
        {description && (
          <p className="text-xs text-muted-foreground">
            {description}
          </p>
        )}
      </div>
      {action && <div className="mt-1 sm:mt-0 flex items-center gap-2">{action}</div>}
    </div>
  );
}

export default SectionHeader;
