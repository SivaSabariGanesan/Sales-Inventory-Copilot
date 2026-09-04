import React from 'react';
import PageContainer from '@/components/layout/PageContainer';
import { TrendingUp } from 'lucide-react';

export function SalesPage() {
  return (
    <PageContainer
      title="Sales Analytics"
      subtitle="Revenue trends, margin analysis, and category demand patterns."
    >
      <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
        <div className="flex items-center gap-3 text-muted-foreground">
          <TrendingUp className="h-5 w-5 text-primary" />
          <span className="text-sm font-medium">Sales analytics module placeholder</span>
        </div>
      </div>
    </PageContainer>
  );
}

export default SalesPage;
