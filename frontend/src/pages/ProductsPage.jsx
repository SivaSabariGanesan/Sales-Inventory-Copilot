import React from 'react';
import PageContainer from '@/components/layout/PageContainer';
import { Tag } from 'lucide-react';

export function ProductsPage() {
  return (
    <PageContainer
      title="Product Catalog"
      subtitle="SKU hierarchy, pricing tiers, margins, and supplier classifications."
    >
      <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
        <div className="flex items-center gap-3 text-muted-foreground">
          <Tag className="h-5 w-5 text-primary" />
          <span className="text-sm font-medium">Product catalog module placeholder</span>
        </div>
      </div>
    </PageContainer>
  );
}

export default ProductsPage;
