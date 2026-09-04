import React from 'react';
import PageHeader from '@/components/common/PageHeader';
import SectionHeader from '@/components/common/SectionHeader';
import FilterBar from '@/components/common/FilterBar';
import DataTableShell from '@/components/common/DataTableShell';
import { Badge } from '@/components/ui/badge';
import { Tag } from 'lucide-react';

const productColumns = [
  { header: 'Product Name / SKU' },
  { header: 'Category' },
  { header: 'Unit Cost', align: 'right' },
  { header: 'Retail Price', align: 'right' },
  { header: 'Margin %', align: 'right' },
  { header: 'Supplier' },
  { header: 'Status' },
];

export function Products() {
  return (
    <div className="mx-auto w-full max-w-7xl px-4 py-6 sm:px-6 lg:px-8 space-y-6 sm:space-y-8">
      {/* Page Header */}
      <PageHeader
        title="Product Catalog"
        description="Manage master product catalog, classifications, unit costs, and pricing margins."
        badge={<Badge variant="outline">0 Products</Badge>}
      />

      <div className="space-y-4">
        <SectionHeader
          title="Master Catalog"
          description="Complete listing of items across all retail departments."
        />

        {/* Search & Filter Toolbar */}
        <FilterBar searchPlaceholder="Search products by title, SKU, or brand..." />

        {/* Product Table Shell */}
        <DataTableShell
          columns={productColumns}
          icon={Tag}
          emptyTitle="No products in catalog"
          emptyDescription="Import your product catalog or connect your ERP to populate merchandise records."
        />
      </div>
    </div>
  );
}

export default Products;
