import React, { useState, useEffect, useMemo } from 'react';
import PageHeader from '@/components/common/PageHeader';
import SectionHeader from '@/components/common/SectionHeader';
import EmptyState from '@/components/common/EmptyState';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  fetchStockoutRisks,
  fetchOverstockInventory,
  fetchInventoryMetadata,
} from '@/services/inventory';
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
  Layers,
  Archive,
  Hourglass,
  HelpCircle,
  TrendingDown,
} from 'lucide-react';

export function Inventory() {
  const [activeTab, setActiveTab] = useState('stockout'); // 'stockout' | 'overstock'

  // Data states
  const [stockoutData, setStockoutData] = useState(null);
  const [overstockData, setOverstockData] = useState(null);
  const [metadata, setMetadata] = useState({ stores: [], categories: [] });

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Common Filters
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedStore, setSelectedStore] = useState('ALL');
  const [selectedCategory, setSelectedCategory] = useState('ALL');

  // Sub-filters
  const [stockoutRiskFilter, setStockoutRiskFilter] = useState('ALL');
  const [overstockStatusFilter, setOverstockStatusFilter] = useState('ALL');

  // Expanded rows for explainability
  const [expandedStockoutRows, setExpandedStockoutRows] = useState(new Set());
  const [expandedOverstockRows, setExpandedOverstockRows] = useState(new Set());

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [stockoutRes, overstockRes, metaRes] = await Promise.all([
        fetchStockoutRisks({
          storeId: selectedStore !== 'ALL' ? Number(selectedStore) : null,
          category: selectedCategory !== 'ALL' ? selectedCategory : null,
          riskLevel: stockoutRiskFilter !== 'ALL' ? stockoutRiskFilter : null,
        }),
        fetchOverstockInventory({
          storeId: selectedStore !== 'ALL' ? Number(selectedStore) : null,
          category: selectedCategory !== 'ALL' ? selectedCategory : null,
          status: overstockStatusFilter !== 'ALL' ? overstockStatusFilter : null,
        }),
        fetchInventoryMetadata(),
      ]);
      setStockoutData(stockoutRes);
      setOverstockData(overstockRes);
      setMetadata(metaRes);
    } catch (err) {
      setError(err.message || 'Unable to load inventory intelligence data. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [selectedStore, selectedCategory, stockoutRiskFilter, overstockStatusFilter]);

  // Filtered Stockout Results (search by product name, SKU, or store)
  const filteredStockoutResults = useMemo(() => {
    if (!stockoutData?.results) return [];
    if (!searchQuery.trim()) return stockoutData.results;
    const query = searchQuery.toLowerCase();
    return stockoutData.results.filter(
      (item) =>
        item.product_name.toLowerCase().includes(query) ||
        item.sku.toLowerCase().includes(query) ||
        item.store_name.toLowerCase().includes(query),
    );
  }, [stockoutData, searchQuery]);

  // Filtered Overstock Results
  const filteredOverstockResults = useMemo(() => {
    if (!overstockData?.results) return [];
    if (!searchQuery.trim()) return overstockData.results;
    const query = searchQuery.toLowerCase();
    return overstockData.results.filter(
      (item) =>
        item.product_name.toLowerCase().includes(query) ||
        item.sku.toLowerCase().includes(query) ||
        item.store_name.toLowerCase().includes(query),
    );
  }, [overstockData, searchQuery]);

  const toggleStockoutRow = (key) => {
    setExpandedStockoutRows((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  };

  const toggleOverstockRow = (key) => {
    setExpandedOverstockRows((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  };

  const stockoutSummary = stockoutData?.summary || {
    high_risk_count: 0,
    medium_risk_count: 0,
    total_at_risk: 0,
    most_urgent_product: null,
    most_urgent_store: null,
    min_days_remaining: null,
  };

  const overstockSummary = overstockData?.summary || {
    overstock_count: 0,
    severe_overstock_count: 0,
    no_recent_demand_count: 0,
    slow_moving_count: 0,
    total_attention_items: 0,
  };

  return (
    <div className="mx-auto w-full max-w-7xl px-4 py-6 sm:px-6 lg:px-8 space-y-6 sm:space-y-8">
      {/* Page Header */}
      <PageHeader
        title="Inventory Optimization & Analytics"
        description="Deterministic stock diagnostics combining 14-day stock-out risk forecasting with 30-day overstock and slow-moving detection."
        badge={
          <Badge variant="outline" className="gap-1 font-semibold">
            <Clock className="h-3 w-3 text-muted-foreground" />
            Deterministic Engine Active
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
            Refresh Intelligence
          </Button>
        }
      />

      {/* Primary Section Navigation Tabs */}
      <div className="flex flex-wrap items-center gap-2 border-b border-border pb-3">
        <Button
          variant={activeTab === 'stockout' ? 'default' : 'outline'}
          size="sm"
          onClick={() => setActiveTab('stockout')}
          className="gap-2 text-xs font-semibold"
        >
          <AlertTriangle className="h-3.5 w-3.5" />
          <span>Stock-Out Risks</span>
          <span className="ml-1 rounded-full bg-primary-foreground/20 px-1.5 py-0.2 text-[10px]">
            {loading ? '…' : stockoutSummary.total_at_risk}
          </span>
        </Button>

        <Button
          variant={activeTab === 'overstock' ? 'default' : 'outline'}
          size="sm"
          onClick={() => setActiveTab('overstock')}
          className="gap-2 text-xs font-semibold"
        >
          <Archive className="h-3.5 w-3.5" />
          <span>Overstock & Slow-Moving</span>
          <span className="ml-1 rounded-full bg-primary-foreground/20 px-1.5 py-0.2 text-[10px]">
            {loading ? '…' : overstockSummary.total_attention_items}
          </span>
        </Button>
      </div>

      {/* Global Filter Toolbar */}
      <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between bg-card p-3 rounded-lg border border-border shadow-xs">
        {/* Search Box */}
        <div className="relative w-full md:max-w-xs">
          <label htmlFor="inv-search" className="sr-only">Search</label>
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" aria-hidden="true" />
          <Input
            id="inv-search"
            type="search"
            placeholder="Search SKU, product, or store..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9 h-9 text-xs"
          />
        </div>

        {/* Dropdown Filters */}
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

          {/* Tab-Specific Status Filter */}
          {activeTab === 'stockout' ? (
            <select
              aria-label="Filter by stockout risk severity"
              value={stockoutRiskFilter}
              onChange={(e) => setStockoutRiskFilter(e.target.value)}
              className="h-9 rounded-md border border-input bg-card px-2.5 py-1 text-xs font-medium text-foreground shadow-xs focus:outline-none focus:ring-1 focus:ring-ring"
            >
              <option value="ALL">All Risks (High & Med)</option>
              <option value="HIGH">High Risk Only</option>
              <option value="MEDIUM">Medium Risk Only</option>
            </select>
          ) : (
            <select
              aria-label="Filter by overstock status"
              value={overstockStatusFilter}
              onChange={(e) => setOverstockStatusFilter(e.target.value)}
              className="h-9 rounded-md border border-input bg-card px-2.5 py-1 text-xs font-medium text-foreground shadow-xs focus:outline-none focus:ring-1 focus:ring-ring"
            >
              <option value="ALL">All Overstock Categories</option>
              <option value="SEVERE_OVERSTOCK">Severe Overstock (&gt;60d)</option>
              <option value="OVERSTOCK">Overstock (30–60d)</option>
              <option value="NO_RECENT_DEMAND">No Recent Demand (0 sales)</option>
              <option value="SLOW_MOVING">Slow-Moving (≤1/day)</option>
            </select>
          )}
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
              Executing deterministic inventory calculations from SQLite telemetry...
            </p>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* TAB 1: STOCK-OUT RISKS (Feature 1) */}
      {/* ========================================================================= */}
      {!loading && !error && activeTab === 'stockout' && (
        <div className="space-y-6">
          {/* Summary KPI Cards */}
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <Card className="border-border bg-card">
              <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
                <CardTitle className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                  High Risk (≤ 3 Days)
                </CardTitle>
                <AlertTriangle className="h-4 w-4 text-red-600" aria-hidden="true" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold tracking-tight text-red-600">
                  {stockoutSummary.high_risk_count}
                </div>
                <p className="mt-1 text-xs text-muted-foreground">
                  Critical stockout risk within 72 hours
                </p>
              </CardContent>
            </Card>

            <Card className="border-border bg-card">
              <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
                <CardTitle className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                  Medium Risk (4–7 Days)
                </CardTitle>
                <AlertCircle className="h-4 w-4 text-amber-600" aria-hidden="true" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold tracking-tight text-amber-600">
                  {stockoutSummary.medium_risk_count}
                </div>
                <p className="mt-1 text-xs text-muted-foreground">
                  Reorder attention required within 1 week
                </p>
              </CardContent>
            </Card>

            <Card className="border-border bg-card">
              <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
                <CardTitle className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                  Total At-Risk SKUs
                </CardTitle>
                <Package className="h-4 w-4 text-primary" aria-hidden="true" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold tracking-tight text-foreground">
                  {stockoutSummary.total_at_risk}
                </div>
                <p className="mt-1 text-xs text-muted-foreground">
                  Across {metadata.stores.length || 4} store locations
                </p>
              </CardContent>
            </Card>

            <Card className="border-border bg-card">
              <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
                <CardTitle className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                  Most Urgent SKU
                </CardTitle>
                <Flame className="h-4 w-4 text-red-500" aria-hidden="true" />
              </CardHeader>
              <CardContent>
                <div className="text-sm font-bold tracking-tight text-foreground truncate" title={stockoutSummary.most_urgent_product || 'None'}>
                  {stockoutSummary.most_urgent_product || 'None'}
                </div>
                <p className="mt-1 text-xs text-muted-foreground truncate">
                  {stockoutSummary.min_days_remaining !== null && stockoutSummary.min_days_remaining !== undefined
                    ? `${stockoutSummary.min_days_remaining.toFixed(2)} days left • ${stockoutSummary.most_urgent_store}`
                    : 'No immediate urgency'}
                </p>
              </CardContent>
            </Card>
          </div>

          {/* Stockout Risk Table */}
          <div className="space-y-3">
            <SectionHeader
              title="Stock-Out Risk Analysis"
              description="Inventory depletion rates sorted by urgency (highest risk first, based on 14-day sales velocity)."
            />

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
                    {filteredStockoutResults.length === 0 ? (
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
                      filteredStockoutResults.map((item) => {
                        const rowKey = `stockout-${item.store_id}-${item.product_id}`;
                        const isExpanded = expandedStockoutRows.has(rowKey);
                        const isHighRisk = item.risk_level === 'HIGH';

                        return (
                          <React.Fragment key={rowKey}>
                            <tr className={`transition-colors hover:bg-muted/30 ${isHighRisk ? 'bg-red-500/5' : ''}`}>
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

                              <td className="px-4 py-3 text-xs font-medium text-foreground">
                                {item.store_name}
                              </td>

                              <td className="px-4 py-3 text-right font-mono font-semibold text-foreground">
                                {item.current_stock}
                              </td>

                              <td className="px-4 py-3 text-right font-mono text-muted-foreground">
                                {item.average_daily_sales.toFixed(2)} /day
                              </td>

                              <td className="px-4 py-3 text-right font-mono font-bold">
                                <span className={isHighRisk ? 'text-red-600' : 'text-amber-600'}>
                                  {item.estimated_days_remaining !== null
                                    ? `${item.estimated_days_remaining.toFixed(2)}d`
                                    : 'N/A'}
                                </span>
                              </td>

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

                              <td className="px-4 py-3 text-center">
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => toggleStockoutRow(rowKey)}
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
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* TAB 2: OVERSTOCK & SLOW-MOVING INVENTORY (Feature 2) */}
      {/* ========================================================================= */}
      {!loading && !error && activeTab === 'overstock' && (
        <div className="space-y-6">
          {/* Summary KPI Cards */}
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <Card className="border-border bg-card">
              <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
                <CardTitle className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                  Overstocked Items
                </CardTitle>
                <Archive className="h-4 w-4 text-amber-600" aria-hidden="true" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold tracking-tight text-amber-600">
                  {overstockSummary.overstock_count}
                </div>
                <p className="mt-1 text-xs text-muted-foreground">
                  Stock holding exceeds 30 days of demand
                </p>
              </CardContent>
            </Card>

            <Card className="border-border bg-card">
              <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
                <CardTitle className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                  Severe Overstock (&gt;60d)
                </CardTitle>
                <AlertTriangle className="h-4 w-4 text-red-600" aria-hidden="true" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold tracking-tight text-red-600">
                  {overstockSummary.severe_overstock_count}
                </div>
                <p className="mt-1 text-xs text-muted-foreground">
                  Excess capital locked (&gt;60 days of stock)
                </p>
              </CardContent>
            </Card>

            <Card className="border-border bg-card">
              <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
                <CardTitle className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                  No Recent Demand
                </CardTitle>
                <HelpCircle className="h-4 w-4 text-purple-600" aria-hidden="true" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold tracking-tight text-purple-600">
                  {overstockSummary.no_recent_demand_count}
                </div>
                <p className="mt-1 text-xs text-muted-foreground">
                  Holding positive stock with 0 sales in 30 days
                </p>
              </CardContent>
            </Card>

            <Card className="border-border bg-card">
              <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
                <CardTitle className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                  Slow-Moving (≤1/day)
                </CardTitle>
                <TrendingDown className="h-4 w-4 text-muted-foreground" aria-hidden="true" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold tracking-tight text-foreground">
                  {overstockSummary.slow_moving_count}
                </div>
                <p className="mt-1 text-xs text-muted-foreground">
                  Low velocity sales &le; 1 unit/day
                </p>
              </CardContent>
            </Card>
          </div>

          {/* Overstock Table */}
          <div className="space-y-3">
            <SectionHeader
              title="Overstock & Slow-Moving Inventory"
              description="Products sorted by business urgency (Severe Overstock > No Demand > Overstock > Slow-Moving, highest days of stock first)."
            />

            <div className="overflow-hidden rounded-lg border border-border bg-card shadow-xs">
              <div className="overflow-x-auto">
                <table className="w-full min-w-[740px] text-left text-sm" role="table">
                  <thead className="border-b border-border bg-muted/40 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                    <tr>
                      <th scope="col" className="px-4 py-3">Product</th>
                      <th scope="col" className="px-4 py-3">Store</th>
                      <th scope="col" className="px-4 py-3 text-right">Current Stock</th>
                      <th scope="col" className="px-4 py-3 text-right">30-Day Sales</th>
                      <th scope="col" className="px-4 py-3 text-right">Avg Daily Sales</th>
                      <th scope="col" className="px-4 py-3 text-right">Days of Stock</th>
                      <th scope="col" className="px-4 py-3 text-center">Status</th>
                      <th scope="col" className="px-4 py-3 text-center">Explainability</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border/60">
                    {filteredOverstockResults.length === 0 ? (
                      <tr>
                        <td colSpan={8} className="p-0">
                          <EmptyState
                            icon={Package}
                            title="No overstock or slow-moving items detected"
                            description="All products in the selected store/category have healthy inventory turnover."
                            className="border-0 rounded-none bg-transparent py-14"
                          />
                        </td>
                      </tr>
                    ) : (
                      filteredOverstockResults.map((item) => {
                        const rowKey = `overstock-${item.store_id}-${item.product_id}`;
                        const isExpanded = expandedOverstockRows.has(rowKey);

                        return (
                          <React.Fragment key={rowKey}>
                            <tr className="transition-colors hover:bg-muted/30">
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

                              {/* 30-Day Sales Volume */}
                              <td className="px-4 py-3 text-right font-mono text-muted-foreground">
                                {item.recent_quantity_sold}
                              </td>

                              {/* Avg Daily Sales (30d) */}
                              <td className="px-4 py-3 text-right font-mono text-muted-foreground">
                                {item.average_daily_sales.toFixed(2)} /day
                              </td>

                              {/* Days of Stock */}
                              <td className="px-4 py-3 text-right font-mono font-bold">
                                {item.days_of_stock !== null && item.days_of_stock !== undefined ? (
                                  <span className={item.days_of_stock > 60 ? 'text-red-600' : 'text-amber-600'}>
                                    {item.days_of_stock.toFixed(1)}d
                                  </span>
                                ) : (
                                  <span className="text-purple-600 text-xs font-semibold">
                                    No demand
                                  </span>
                                )}
                              </td>

                              {/* Status Badge */}
                              <td className="px-4 py-3 text-center">
                                {item.status === 'SEVERE_OVERSTOCK' && (
                                  <span className="inline-flex items-center rounded-md bg-red-100 px-2 py-0.5 text-xs font-bold text-red-700 dark:bg-red-950/60 dark:text-red-400">
                                    SEVERE OVERSTOCK
                                  </span>
                                )}
                                {item.status === 'OVERSTOCK' && (
                                  <span className="inline-flex items-center rounded-md bg-amber-100 px-2 py-0.5 text-xs font-bold text-amber-700 dark:bg-amber-950/60 dark:text-amber-400">
                                    OVERSTOCK
                                  </span>
                                )}
                                {item.status === 'NO_RECENT_DEMAND' && (
                                  <span className="inline-flex items-center rounded-md bg-purple-100 px-2 py-0.5 text-xs font-bold text-purple-700 dark:bg-purple-950/60 dark:text-purple-400">
                                    NO DEMAND
                                  </span>
                                )}
                                {item.status === 'SLOW_MOVING' && (
                                  <span className="inline-flex items-center rounded-md bg-slate-100 px-2 py-0.5 text-xs font-bold text-slate-700 dark:bg-slate-800 dark:text-slate-300">
                                    SLOW MOVING
                                  </span>
                                )}
                              </td>

                              {/* Details Button */}
                              <td className="px-4 py-3 text-center">
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => toggleOverstockRow(rowKey)}
                                  className="h-7 px-2 text-xs gap-1 text-muted-foreground hover:text-foreground"
                                  aria-label="Toggle overstock explanation"
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
                                <td colSpan={8} className="px-6 py-4">
                                  <div className="rounded-md border border-border bg-card p-4 text-xs space-y-2">
                                    <div className="flex items-center gap-2 font-semibold text-foreground">
                                      <Info className="h-4 w-4 text-primary" />
                                      <span>Overstock Evidence & Diagnostics</span>
                                    </div>
                                    <p className="text-muted-foreground leading-relaxed">
                                      {item.explanation}
                                    </p>
                                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-2 text-[11px] border-t border-border mt-2">
                                      <div>
                                        <span className="text-muted-foreground">Lookback Period:</span>
                                        <span className="font-semibold text-foreground ml-1">30 Calendar Days</span>
                                      </div>
                                      <div>
                                        <span className="text-muted-foreground">30-Day Sales Volume:</span>
                                        <span className="font-semibold text-foreground ml-1">{item.recent_quantity_sold} units</span>
                                      </div>
                                      <div>
                                        <span className="text-muted-foreground">Sales Velocity:</span>
                                        <span className="font-semibold text-foreground ml-1">{item.average_daily_sales.toFixed(2)} units/day</span>
                                      </div>
                                      <div>
                                        <span className="text-muted-foreground">Holding Status:</span>
                                        <span className="font-semibold text-foreground ml-1">{item.status.replace(/_/g, ' ')}</span>
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
          </div>
        </div>
      )}
    </div>
  );
}

export default Inventory;
