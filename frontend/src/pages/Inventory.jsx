import React from 'react';
import PageHeader from '@/components/common/PageHeader';
import SectionHeader from '@/components/common/SectionHeader';
import FilterBar from '@/components/common/FilterBar';
import DataTableShell from '@/components/common/DataTableShell';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Package, AlertCircle, RefreshCw, Layers } from 'lucide-react';

const inventoryColumns = [
  { header: 'SKU / Item Name' },
  { header: 'Category' },
  { header: 'Store / Location' },
  { header: 'Stock on Hand', align: 'right' },
  { header: 'Reorder Point', align: 'right' },
  { header: 'Status' },
];

export function Inventory() {
  return (
    <div className="mx-auto w-full max-w-7xl px-4 py-6 sm:px-6 lg:px-8 space-y-6">
      {/* Page Header */}
      <PageHeader
        title="Inventory Optimization"
        description="Monitor multi-location inventory levels, safety stocks, and replenishment triggers."
        badge={<Badge variant="outline">0 SKUs Tracked</Badge>}
      />

      {/* Inventory Overview Metric Shells */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {[
          { title: 'Total SKUs Tracked', icon: Package },
          { title: 'Low Stock Alerts', icon: AlertCircle },
          { title: 'Out of Stock Items', icon: AlertCircle },
          { title: 'Pending Reorders', icon: RefreshCw },
        ].map((stat, idx) => (
          <Card key={idx}>
            <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
              <CardTitle className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                {stat.title}
              </CardTitle>
              <stat.icon className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold tracking-tight text-muted-foreground/50">—</div>
              <p className="mt-1 text-xs text-muted-foreground">
                No inventory source connected
              </p>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Inventory Table Section */}
      <div className="space-y-4">
        <SectionHeader
          title="Stock Registry"
          description="Detailed inventory breakdown by store and SKU."
        />

        {/* Search & Filter Toolbar */}
        <FilterBar searchPlaceholder="Search by SKU, product name, or category..." />

        {/* Data Table Shell with Empty State */}
        <DataTableShell
          columns={inventoryColumns}
          icon={Package}
          emptyTitle="No inventory records found"
          emptyDescription="Connect your inventory data to start tracking stock levels and reorder parameters."
        />
      </div>
    </div>
  );
}

export default Inventory;
