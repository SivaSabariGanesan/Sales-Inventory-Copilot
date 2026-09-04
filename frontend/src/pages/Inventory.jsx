import React, { useState, useEffect, useMemo } from 'react';
import PageHeader from '@/components/common/PageHeader';
import SectionHeader from '@/components/common/SectionHeader';
import EmptyState from '@/components/common/EmptyState';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { fetchStockoutRisks, fetchInventoryMetadata } from '@/services/inventory';
import {
  AlertTriangle,
  AlertCircle,
  Clock,
  Flame,
  ChevronDown,
  ChevronUp,
  Search,
  Filter,
  RefreshCw,
  Store,
  Tag,
  Info,
  Package,
} from 'lucide-react';

export function Inventory() {
  const [data, setData] = useState(null);
  const [metadata, setMetadata] = useState({ stores: [], categories: [] });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Filters
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedStore, setSelectedStore] = useState('ALL');
  const [selectedCategory, setSelectedCategory] = useState('ALL');
  const [selectedRiskLevel, setSelectedRiskLevel] = useState('ALL');

  // Expanded row IDs for explainability
  const [expandedRows, setExpandedRows] = useState(new Set());

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [riskRes, metaRes] = await Promise.all([
        fetchStockoutRisks({
          storeId: selectedStore !== 'ALL' ? Number(selectedStore) : null,
          category: selectedCategory !== 'ALL' ? selectedCategory : null,
          riskLevel: selectedRiskLevel !== 'ALL' ? selectedRiskLevel : null,
        }),
        fetchInventoryMetadata(),
      ]);
      setData(riskRes);
      setMetadata(metaRes);
    } catch (err) {
      setError(err.message || 'Unable to load stock-out risk data. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [selectedStore, selectedCategory, selectedRiskLevel]);

  // Client-side search filtering by product name or SKU
  const filteredResults = useMemo(() => {
    if (!data || !data.results) return [];
    if (!searchQuery.trim()) return data.results;
    const query = searchQuery.toLowerCase();
    return data.results.filter(
      (item) =>
        item.product_name.toLowerCase().includes(query) ||
        item.sku.toLowerCase().includes(query) ||
        item.store_name.toLowerCase().includes(query),
    );
  }, [data, searchQuery]);

  const toggleRowExpand = (key) => {
    setExpandedRows((prev) => {
      const next = new Set(prev);
      if (next.has(key)) {
        next.delete(key);
      } else {
        next.add(key);
      }
      return next;
    });
  };

  const summary = data?.summary || {
    high_risk_count: 0,
    medium_risk_count: 0,
    total_at_risk: 0,
    most_urgent_product: null,
    most_urgent_store: null,
    min_days_remaining: null,
  };

  return (
    <div className="mx-auto w-full max-w-7xl px-4 py-6 sm:px-6 lg:px-8 space-y-6 sm:space-y-8">
      {/* Page Header */}
      <PageHeader
        title="Inventory Optimization & Stock-Out Risks"
        description="Deterministic stock depletion forecast based on 14-day sales velocity across store nodes."
        badge={
          <Badge variant="outline" className="gap-1 font-semibold">
            <Clock className="h-3 w-3 text-muted-foreground" />
            14-Day Demand Model
          </Badge>
        }
        action={
          <Button
            variant="outline"
            size="sm"
            onClick={loadData}
            disabled={loading}
            className="gap-1.5 text-xs"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${loading ? 'animate-spin' : ''}`} />
            Refresh Analysis
          </Button>
        }
      />

      {/* Summary KPI Cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {/* High Risk Card */}
        <Card className="border-border bg-card">
          <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
            <CardTitle className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
              High Risk (≤ 3 Days)
            </CardTitle>
            <AlertTriangle className="h-4 w-4 text-red-600" aria-hidden="true" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold tracking-tight text-red-600">
              {loading ? '—' : summary.high_risk_count}
            </div>
            <p className="mt-1 text-xs text-muted-foreground">
              Critical stockout risk within 72 hours
            </p>
          </CardContent>
        </Card>

        {/* Medium Risk Card */}
        <Card className="border-border bg-card">
          <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
            <CardTitle className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
              Medium Risk (4–7 Days)
            </CardTitle>
            <AlertCircle className="h-4 w-4 text-amber-600" aria-hidden="true" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold tracking-tight text-amber-600">
              {loading ? '—' : summary.medium_risk_count}
            </div>
            <p className="mt-1 text-xs text-muted-foreground">
              Reorder attention required within 1 week
            </p>
          </CardContent>
        </Card>

        {/* Total At-Risk Card */}
        <Card className="border-border bg-card">
          <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
            <CardTitle className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
              Total At-Risk SKUs
            </CardTitle>
            <Package className="h-4 w-4 text-primary" aria-hidden="true" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold tracking-tight text-foreground">
              {loading ? '—' : summary.total_at_risk}
            </div>
            <p className="mt-1 text-xs text-muted-foreground">
              Across {metadata.stores.length || 4} store locations
            </p>
          </CardContent>
        </Card>

        {/* Most Urgent Product Card */}
        <Card className="border-border bg-card">
          <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
            <CardTitle className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
              Most Urgent SKU
            </CardTitle>
            <Flame className="h-4 w-4 text-red-500" aria-hidden="true" />
          </CardHeader>
          <CardContent>
            <div className="text-sm font-bold tracking-tight text-foreground truncate" title={summary.most_urgent_product || 'None'}>
              {loading ? '—' : summary.most_urgent_product || 'None'}
            </div>
            <p className="mt-1 text-xs text-muted-foreground truncate">
              {summary.min_days_remaining !== null && summary.min_days_remaining !== undefined
                ? `${summary.min_days_remaining.toFixed(2)} days left • ${summary.most_urgent_store}`
                : 'No immediate urgency'}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Stock-Out Risk Section & Interactive Table */}
      <div className="space-y-4">
        <SectionHeader
          title="Stock-Out Risk Analysis"
          description="Detailed inventory depletion rates sorted by urgency (highest risk first)."
        />

        {/* Filter Toolbar */}
        <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
          {/* Search Box */}
          <div className="relative w-full md:max-w-xs">
            <label htmlFor="risk-search" className="sr-only">Search</label>
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" aria-hidden="true" />
            <Input
              id="risk-search"
              type="search"
              placeholder="Search product, SKU, or store..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-9 h-9 text-sm"
            />
          </div>

          {/* Filter Dropdowns */}
          <div className="flex flex-wrap items-center gap-2">
            {/* Store Filter */}
            <div className="flex items-center gap-1">
              <Store className="h-3.5 w-3.5 text-muted-foreground hidden sm:inline" />
              <select
                aria-label="Filter by store"
                value={selectedStore}
                onChange={(e) => setSelectedStore(e.target.value)}
                className="h-9 rounded-md border border-input bg-card px-2.5 py-1 text-xs font-medium text-foreground shadow-xs focus:outline-none focus:ring-1 focus:ring-ring"
              >
                <option value="ALL">All Stores</option>
                {metadata.stores.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.store_name}
                  </option>
                ))}
              </select>
            </div>

            {/* Category Filter */}
            <div className="flex items-center gap-1">
              <Tag className="h-3.5 w-3.5 text-muted-foreground hidden sm:inline" />
              <select
                aria-label="Filter by category"
                value={selectedCategory}
                onChange={(e) => setSelectedCategory(e.target.value)}
                className="h-9 rounded-md border border-input bg-card px-2.5 py-1 text-xs font-medium text-foreground shadow-xs focus:outline-none focus:ring-1 focus:ring-ring"
              >
                <option value="ALL">All Categories</option>
                {metadata.categories.map((cat) => (
                  <option key={cat} value={cat}>
                    {cat}
                  </option>
                ))}
              </select>
            </div>

            {/* Risk Level Filter */}
            <select
              aria-label="Filter by risk severity"
              value={selectedRiskLevel}
              onChange={(e) => setSelectedRiskLevel(e.target.value)}
              className="h-9 rounded-md border border-input bg-card px-2.5 py-1 text-xs font-medium text-foreground shadow-xs focus:outline-none focus:ring-1 focus:ring-ring"
            >
              <option value="ALL">All Risks (High & Med)</option>
              <option value="HIGH">High Risk Only</option>
              <option value="MEDIUM">Medium Risk Only</option>
            </select>
          </div>
        </div>

        {/* Error State */}
        {error && (
          <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-center dark:border-red-900/50 dark:bg-red-950/20">
            <p className="text-sm font-medium text-red-800 dark:text-red-300">
              {error}
            </p>
            <Button
              variant="outline"
              size="sm"
              onClick={loadData}
              className="mt-3 text-xs"
            >
              Retry
            </Button>
          </div>
        )}

        {/* Loading State */}
        {loading && !error && (
          <div className="flex min-h-[260px] items-center justify-center rounded-lg border border-border bg-card p-8 text-center">
            <div className="flex flex-col items-center gap-3">
              <RefreshCw className="h-6 w-6 animate-spin text-primary" />
              <p className="text-xs text-muted-foreground">
                Analyzing inventory levels against 14-day sales velocity...
              </p>
            </div>
          </div>
        )}

        {/* Table Content */}
        {!loading && !error && (
          <div className="overflow-hidden rounded-lg border border-border bg-card shadow-xs">
            <div className="overflow-x-auto">
              <table className="w-full min-w-[720px] text-left text-sm" role="table">
                <thead className="border-b border-border bg-muted/40 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  <tr>
                    <th scope="col" className="px-4 py-3">Product</th>
                    <th scope="col" className="px-4 py-3">Store</th>
                    <th scope="col" className="px-4 py-3 text-right">Current Stock</th>
                    <th scope="col" className="px-4 py-3 text-right">Avg Daily Sales</th>
                    <th scope="col" className="px-4 py-3 text-right">Days Left</th>
                    <th scope="col" className="px-4 py-3 text-center">Risk Level</th>
                    <th scope="col" className="px-4 py-3 text-center">Explainability</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border/60">
                  {filteredResults.length === 0 ? (
                    <tr>
                      <td colSpan={7} className="p-0">
                        <EmptyState
                          icon={AlertCircle}
                          title="No immediate stock-out risks detected"
                          description="All products in the selected store/category have sufficient inventory relative to recent sales demand."
                          className="border-0 rounded-none bg-transparent py-14"
                        />
                      </td>
                    </tr>
                  ) : (
                    filteredResults.map((item) => {
                      const rowKey = `${item.store_id}-${item.product_id}`;
                      const isExpanded = expandedRows.has(rowKey);
                      const isHighRisk = item.risk_level === 'HIGH';

                      return (
                        <React.Fragment key={rowKey}>
                          <tr className={`transition-colors hover:bg-muted/30 ${isHighRisk ? 'bg-red-500/5' : ''}`}>
                            {/* Product Info */}
                            <td className="px-4 py-3">
                              <div className="font-medium text-foreground">
                                {item.product_name}
                              </div>
                              <div className="text-xs text-muted-foreground flex items-center gap-1.5 mt-0.5">
                                <span className="font-mono">{item.sku}</span>
                                <span>•</span>
                                <span>{item.category}</span>
                              </div>
                            </td>

                            {/* Store Info */}
                            <td className="px-4 py-3 text-xs font-medium text-foreground">
                              {item.store_name}
                            </td>

                            {/* Current Stock */}
                            <td className="px-4 py-3 text-right font-mono font-semibold text-foreground">
                              {item.current_stock}
                            </td>

                            {/* Avg Daily Sales (14d) */}
                            <td className="px-4 py-3 text-right font-mono text-muted-foreground">
                              {item.average_daily_sales.toFixed(2)} /day
                            </td>

                            {/* Days Remaining */}
                            <td className="px-4 py-3 text-right font-mono font-bold">
                              <span className={isHighRisk ? 'text-red-600' : 'text-amber-600'}>
                                {item.estimated_days_remaining !== null
                                  ? `${item.estimated_days_remaining.toFixed(2)}d`
                                  : 'N/A'}
                              </span>
                            </td>

                            {/* Risk Badge */}
                            <td className="px-4 py-3 text-center">
                              {isHighRisk ? (
                                <span className="inline-flex items-center rounded-md bg-red-100 px-2 py-0.5 text-xs font-bold text-red-700 dark:bg-red-950/60 dark:text-red-400">
                                  HIGH
                                </span>
                              ) : (
                                <span className="inline-flex items-center rounded-md bg-amber-100 px-2 py-0.5 text-xs font-bold text-amber-700 dark:bg-amber-950/60 dark:text-amber-400">
                                  MEDIUM
                                </span>
                              )}
                            </td>

                            {/* Expandable Details Button */}
                            <td className="px-4 py-3 text-center">
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => toggleRowExpand(rowKey)}
                                className="h-7 px-2 text-xs gap-1 text-muted-foreground hover:text-foreground"
                                aria-label="Toggle risk explanation"
                              >
                                <span>{isExpanded ? 'Hide' : 'Details'}</span>
                                {isExpanded ? (
                                  <ChevronUp className="h-3 w-3" />
                                ) : (
                                  <ChevronDown className="h-3 w-3" />
                                )}
                              </Button>
                            </td>
                          </tr>

                          {/* Expanded Explainability Row */}
                          {isExpanded && (
                            <tr className="bg-muted/40">
                              <td colSpan={7} className="px-6 py-4">
                                <div className="rounded-md border border-border bg-card p-4 text-xs space-y-2">
                                  <div className="flex items-center gap-2 font-semibold text-foreground">
                                    <Info className="h-4 w-4 text-primary" />
                                    <span>Stock-Out Evidence & Diagnostics</span>
                                  </div>
                                  <p className="text-muted-foreground leading-relaxed">
                                    {item.explanation}
                                  </p>
                                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-2 text-[11px] border-t border-border mt-2">
                                    <div>
                                      <span className="text-muted-foreground">Lookback Period:</span>
                                      <span className="font-semibold text-foreground ml-1">14 Calendar Days</span>
                                    </div>
                                    <div>
                                      <span className="text-muted-foreground">14-Day Sales Volume:</span>
                                      <span className="font-semibold text-foreground ml-1">{item.recent_quantity_sold} units</span>
                                    </div>
                                    <div>
                                      <span className="text-muted-foreground">Reorder Threshold:</span>
                                      <span className="font-semibold text-foreground ml-1">{item.reorder_level || '—'} units</span>
                                    </div>
                                    <div>
                                      <span className="text-muted-foreground">Depletion Velocity:</span>
                                      <span className="font-semibold text-foreground ml-1">{item.average_daily_sales.toFixed(2)} units/day</span>
                                    </div>
                                  </div>
                                </div>
                              </td>
                            </tr>
                          )}
                        </React.Fragment>
                      );
                    })
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default Inventory;
