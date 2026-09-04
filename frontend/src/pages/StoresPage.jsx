import React from 'react';
import PageContainer from '@/components/layout/PageContainer';
import { Building2 } from 'lucide-react';

export function StoresPage() {
  return (
    <PageContainer
      title="Store Network"
      subtitle="Regional locations, fulfillment nodes, and physical store performance."
    >
      <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
        <div className="flex items-center gap-3 text-muted-foreground">
          <Building2 className="h-5 w-5 text-primary" />
          <span className="text-sm font-medium">Store network module placeholder</span>
        </div>
      </div>
    </PageContainer>
  );
}

export default StoresPage;
