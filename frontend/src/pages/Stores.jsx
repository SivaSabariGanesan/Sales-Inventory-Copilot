import React from 'react';
import PageHeader from '@/components/common/PageHeader';
import SectionHeader from '@/components/common/SectionHeader';
import FilterBar from '@/components/common/FilterBar';
import DataTableShell from '@/components/common/DataTableShell';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Building2, MapPin, Truck, Store } from 'lucide-react';

const storeColumns = [
  { header: 'Store ID / Name' },
  { header: 'Region / City' },
  { header: 'Store Format' },
  { header: 'Square Footage', align: 'right' },
  { header: 'Fulfillment Hub' },
  { header: 'Operating Status' },
];

export function Stores() {
  return (
    <div className="mx-auto w-full max-w-7xl px-4 py-6 sm:px-6 lg:px-8 space-y-6 sm:space-y-8">
      {/* Page Header */}
      <PageHeader
        title="Store Network"
        description="Physical retail outlets, distribution centers, and regional fulfillment hubs."
        badge={<Badge variant="outline">0 Active Stores</Badge>}
      />

      {/* Store Overview Metric Shells */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {[
          { title: 'Total Locations', icon: Building2 },
          { title: 'Fulfillment Nodes', icon: Truck },
          { title: 'Regions Covered', icon: MapPin },
          { title: 'Flagship Outlets', icon: Store },
        ].map((item, idx) => (
          <Card key={idx} className="bg-card transition-shadow hover:shadow-sm">
            <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
              <CardTitle className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                {item.title}
              </CardTitle>
              <item.icon className="h-4 w-4 text-muted-foreground" aria-hidden="true" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold tracking-tight text-muted-foreground/40">—</div>
              <p className="mt-1 text-xs text-muted-foreground">
                No locations mapped
              </p>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Store Directory Table */}
      <div className="space-y-4">
        <SectionHeader
          title="Locations Directory"
          description="Detailed listing of store locations, types, and active fulfillment channels."
        />

        {/* Search & Filter Toolbar */}
        <FilterBar searchPlaceholder="Search stores by name, city, or code..." />

        {/* Store Table Shell */}
        <DataTableShell
          columns={storeColumns}
          icon={Building2}
          emptyTitle="No store locations configured"
          emptyDescription="Add retail store locations or warehouses to manage multi-store inventory distribution."
        />
      </div>
    </div>
  );
}

export default Stores;
