import React from 'react';
import { cn } from '@/lib/utils';
import EmptyState from './EmptyState';
import { Database } from 'lucide-react';

export function DataTableShell({
  columns = [],
  emptyTitle = 'No records found',
  emptyDescription = 'Records will appear here once data is connected.',
  icon = Database,
  className,
}) {
  return (
    <div className={cn('overflow-hidden rounded-lg border border-border bg-card shadow-xs', className)}>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[540px] text-left text-sm" role="table">
          <thead className="border-b border-border bg-muted/40 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            <tr>
              {columns.map((col, idx) => (
                <th
                  key={idx}
                  scope="col"
                  className={cn(
                    'px-4 py-3 font-semibold text-muted-foreground',
                    col.align === 'right' ? 'text-right' : 'text-left',
                    col.className,
                  )}
                >
                  {col.header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-border/60">
            <tr>
              <td colSpan={columns.length || 1} className="p-0">
                <EmptyState
                  icon={icon}
                  title={emptyTitle}
                  description={emptyDescription}
                  className="border-0 rounded-none bg-transparent py-14"
                />
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default DataTableShell;
