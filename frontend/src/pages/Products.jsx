import React, { useState, useEffect } from 'react';
import PageHeader from '@/components/common/PageHeader';
import SectionHeader from '@/components/common/SectionHeader';
import EmptyState from '@/components/common/EmptyState';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { fetchProducts } from '@/services/products';
import {
  Tag,
  Search,
  Filter,
  RefreshCw,
  AlertCircle,
  Package,
  Layers,
  DollarSign,
  Boxes,
} from 'lucide-react';

export function Products() {
  const [productsData, setProductsData] = useState({
    total_count: 0,
    filtered_count: 0,
    categories: [],
    products: [],
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Filters
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('ALL');

  const loadProducts = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchProducts({
        search: searchTerm,
        category: selectedCategory,
      });
      setProductsData(data);
    } catch (err) {
      setError(err.message || 'Unable to load product catalog from database.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadProducts();
  }, [selectedCategory]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    loadProducts();
  };

  const handleSearchKeyDown = (e) => {
    if (e.key === 'Enter') {
      loadProducts();
    }
  };

  const { total_count, filtered_count, categories, products } = productsData;

  return (
    <div className="mx-auto w-full max-w-7xl px-4 py-6 sm:px-6 lg:px-8 space-y-6 sm:space-y-8">
      {/* Page Header */}
      <PageHeader
        title="Product Catalog"
        description="Master product catalogue, departmental classifications, unit pricing, and stock replenishment thresholds."
        badge={
          <Badge variant="outline" className="font-mono bg-primary/10 text-primary border-primary/20">
            {loading ? '...' : `${total_count} Products`}
          </Badge>
        }
        actions={
          <Button
            variant="outline"
            size="sm"
            onClick={loadProducts}
            disabled={loading}
            className="h-9 gap-1.5 text-xs font-medium"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        }
      />

      {/* Error Alert */}
      {error && (
        <div className="flex items-center justify-between rounded-lg border border-red-500/20 bg-red-500/10 p-4 text-sm text-red-700 dark:text-red-400">
          <div className="flex items-center gap-2">
            <AlertCircle className="h-5 w-5 flex-shrink-0" />
            <span>{error}</span>
          </div>
          <Button variant="outline" size="sm" onClick={loadProducts} className="text-xs">
            Try Again
          </Button>
        </div>
      )}

      {/* Catalog Overview Metrics */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <Card className="bg-card shadow-xs">
          <CardContent className="p-4 flex items-center gap-3">
            <div className="p-2.5 rounded-lg bg-blue-500/10 text-blue-600 dark:text-blue-400">
              <Package className="h-5 w-5" />
            </div>
            <div>
              <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Total Products</p>
              <h3 className="text-2xl font-bold tracking-tight text-foreground">{total_count}</h3>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-card shadow-xs">
          <CardContent className="p-4 flex items-center gap-3">
            <div className="p-2.5 rounded-lg bg-indigo-500/10 text-indigo-600 dark:text-indigo-400">
              <Layers className="h-5 w-5" />
            </div>
            <div>
              <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Active Categories</p>
              <h3 className="text-2xl font-bold tracking-tight text-foreground">{categories.length}</h3>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-card shadow-xs">
          <CardContent className="p-4 flex items-center gap-3">
            <div className="p-2.5 rounded-lg bg-emerald-500/10 text-emerald-600 dark:text-emerald-400">
              <Boxes className="h-5 w-5" />
            </div>
            <div>
              <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Matching In Scope</p>
              <h3 className="text-2xl font-bold tracking-tight text-foreground">{filtered_count}</h3>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Master Catalog Section */}
      <div className="space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <SectionHeader
            title="Master Catalog"
            description="Complete listing of items across all retail departments with live database pricing."
          />
        </div>

        {/* Search & Filter Toolbar */}
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 rounded-lg border border-border bg-card p-3 shadow-xs">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <input
              type="text"
              placeholder="Search products by title or SKU..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              onKeyDown={handleSearchKeyDown}
              className="w-full rounded-md border border-input bg-background pl-9 pr-4 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-primary"
            />
          </div>

          <div className="flex items-center gap-2">
            <div className="flex items-center gap-1.5 text-xs text-muted-foreground pl-1">
              <Filter className="h-3.5 w-3.5" />
              <span>Category:</span>
            </div>
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="rounded-md border border-input bg-background px-3 py-2 text-xs font-medium text-foreground focus:outline-none focus:ring-1 focus:ring-primary"
            >
              <option value="ALL">All Categories ({categories.length})</option>
              {categories.map((cat) => (
                <option key={cat} value={cat}>
                  {cat}
                </option>
              ))}
            </select>
            <Button size="sm" onClick={loadProducts} className="h-9 px-3 text-xs">
              Search
            </Button>
          </div>
        </div>

        {/* Data Table */}
        <div className="overflow-hidden rounded-lg border border-border bg-card shadow-xs">
          <div className="overflow-x-auto">
            <table className="w-full min-w-[640px] text-left text-sm" role="table">
              <thead className="border-b border-border bg-muted/40 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                <tr>
                  <th scope="col" className="px-4 py-3">Product Name</th>
                  <th scope="col" className="px-4 py-3">SKU</th>
                  <th scope="col" className="px-4 py-3">Category</th>
                  <th scope="col" className="px-4 py-3 text-right">Unit Price</th>
                  <th scope="col" className="px-4 py-3 text-right">Reorder Level</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border/60">
                {loading ? (
                  <tr>
                    <td colSpan={5} className="py-12 text-center text-muted-foreground">
                      <div className="flex flex-col items-center justify-center gap-2">
                        <RefreshCw className="h-6 w-6 animate-spin text-primary" />
                        <p className="text-xs">Loading master product catalog from database...</p>
                      </div>
                    </td>
                  </tr>
                ) : products.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="p-0">
                      <EmptyState
                        icon={Tag}
                        title="No products found"
                        description={
                          searchTerm || selectedCategory !== 'ALL'
                            ? 'No products matched your search or category filter. Try clearing filters.'
                            : 'No product records found in the database.'
                        }
                        className="border-0 rounded-none bg-transparent py-12"
                      />
                    </td>
                  </tr>
                ) : (
                  products.map((item) => (
                    <tr key={item.id} className="hover:bg-muted/30 transition-colors">
                      <td className="px-4 py-3.5">
                        <div className="font-semibold text-foreground">{item.product_name}</div>
                        <div className="text-[11px] text-muted-foreground">ID: #{item.id}</div>
                      </td>
                      <td className="px-4 py-3.5">
                        <code className="rounded bg-muted px-2 py-0.5 font-mono text-xs font-semibold text-foreground">
                          {item.sku}
                        </code>
                      </td>
                      <td className="px-4 py-3.5">
                        <Badge variant="secondary" className="text-xs font-normal">
                          {item.category}
                        </Badge>
                      </td>
                      <td className="px-4 py-3.5 text-right font-mono font-medium text-foreground">
                        ${item.unit_price.toFixed(2)}
                      </td>
                      <td className="px-4 py-3.5 text-right">
                        <span className="inline-flex items-center justify-center rounded-md bg-amber-500/10 px-2.5 py-1 text-xs font-mono font-semibold text-amber-600 dark:text-amber-400">
                          {Math.round(item.reorder_level)} units
                        </span>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
          {!loading && products.length > 0 && (
            <div className="border-t border-border bg-muted/20 px-4 py-2.5 text-xs text-muted-foreground flex items-center justify-between">
              <span>Showing {products.length} of {total_count} products</span>
              <span>Sorted by Category & Name</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default Products;
