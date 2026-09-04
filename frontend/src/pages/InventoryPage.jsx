import React from 'react';
import PageContainer from '@/components/layout/PageContainer';
import { Package } from 'lucide-react';

export function InventoryPage() {
  return (
    <PageContainer
      title="Inventory Optimization"
      subtitle="Stock health monitoring, reorder triggers, and multi-location inventory levels."
    >
      <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
        <div className="flex items-center gap-3 text-muted-foreground">
          <Package className="h-5 w-5 text-primary" />
          <span className="text-sm font-medium">Inventory management module placeholder</span>
        </div>
      </div>
    </PageContainer>
  );
}

export default InventoryPage;
