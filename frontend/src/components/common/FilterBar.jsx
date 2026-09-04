import React from 'react';
import { Search, Filter } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

export function FilterBar({
  searchPlaceholder = 'Search records...',
  children,
  className,
}) {
  return (
    <div
      className={cn(
        'mb-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between',
        className,
      )}
    >
      <div className="relative w-full sm:max-w-xs md:max-w-sm">
        <label htmlFor="filterbar-search" className="sr-only">
          Search
        </label>
        <Search
          className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground pointer-events-none"
          aria-hidden="true"
        />
        <Input
          id="filterbar-search"
          type="search"
          placeholder={searchPlaceholder}
          className="pl-9 h-9 text-sm"
          disabled
          aria-disabled="true"
        />
      </div>

      <div className="flex flex-wrap items-center gap-2 shrink-0">
        {children || (
          <Button
            variant="outline"
            size="sm"
            className="h-9 gap-1.5 text-xs text-muted-foreground"
            disabled
            aria-disabled="true"
          >
            <Filter className="h-3.5 w-3.5" aria-hidden="true" />
            Filters
          </Button>
        )}
      </div>
    </div>
  );
}

export default FilterBar;
