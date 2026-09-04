import React from 'react';
import PageContainer from '@/components/layout/PageContainer';
import { LayoutDashboard } from 'lucide-react';

export function DashboardPage() {
  return (
    <PageContainer
      title="Executive Overview"
      subtitle="Comprehensive performance snapshot across sales channels and inventory hubs."
    >
      <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
        <div className="flex items-center gap-3 text-muted-foreground">
          <LayoutDashboard className="h-5 w-5 text-primary" />
          <span className="text-sm font-medium">Dashboard module container placeholder</span>
        </div>
      </div>
    </PageContainer>
  );
}

export default DashboardPage;
