import React, { useState, useEffect, useMemo } from 'react';
import PageHeader from '@/components/common/PageHeader';
import SectionHeader from '@/components/common/SectionHeader';
import EmptyState from '@/components/common/EmptyState';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { fetchSalesAnomalies } from '@/services/sales';
import { fetchInventoryMetadata } from '@/services/inventory';
import {
  TrendingUp,
  TrendingDown,
  Activity,
  Zap,
  Search,
  RefreshCw,
  Store,
  Tag,
  Info,
  ChevronDown,
  ChevronUp,
  AlertCircle,
  HelpCircle,
  Calendar,
} from 'lucide-react';

export function Sales() {
  const [salesData, setSalesData] = useState(null);
  const [metadata, setMetadata] = useState({ stores: [], categories: [] });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Filters
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedStore, setSelectedStore] = useState('ALL');
  const [selectedCategory, setSelectedCategory] = useState('ALL');
  const [statusFilter, setStatusFilter] = useState('ALL');

  // Expanded rows for explainability
  const [expandedRows, setExpandedRows] = useState(new Set());

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [anomalyRes, metaRes] = await Promise.all([
        fetchSalesAnomalies({
          storeId: selectedStore !== 'ALL' ? Number(selectedStore) : null,
          category: selectedCategory !== 'ALL' ? selectedCategory : null,
          status: statusFilter !== 'ALL' ? statusFilter : null,
        }),
        fetchInventoryMetadata(),
      ]);
      setSalesData(anomalyRes);
      setMetadata(metaRes);
    } catch (err) {
      setError(err.message || 'Unable to load sales anomaly intelligence data.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [selectedStore, selectedCategory, statusFilter]);

  const toggleRow = (id) => {
    setExpandedRows((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  // Filtered Results via client search
  const filteredResults = useMemo(() => {
    if (!salesData?.results) return [];
    if (!searchQuery.trim()) return salesData.results;
    const query = searchQuery.toLowerCase();
    return salesData.results.filter(
      (item) =>
        item.product_name.toLowerCase().includes(query) ||
        item.sku.toLowerCase().includes(query) ||
        item.store_name.toLowerCase().includes(query) ||
        item.category.toLowerCase().includes(query),
    );
  }, [salesData, searchQuery]);

  const summary = salesData?.summary || {
    spike_count: 0,
    drop_count: 0,
    total_signals: 0,
    largest_change_pct: null,
    insufficient_baseline_count: 0,
  };

  const getSignalBadge = (status, pctChange) => {
    switch (status) {
      case 'SPIKE':
        return (
          <Badge className="bg-emerald-600 hover:bg-emerald-700 text-white font-medium flex items-center gap-1">
            <TrendingUp className="h-3 w-3" />
            SPIKE {pctChange !== null && pctChange !== undefined ? `(+${pctChange.toFixed(1)}%)` : ''}
          </Badge>
        );
      case 'DROP':
        return (
          <Badge variant="destructive" className="font-medium flex items-center gap-1">
            <TrendingDown className="h-3 w-3" />
            DROP {pctChange !== null && pctChange !== undefined ? `(${pctChange.toFixed(1)}%)` : ''}
          </Badge>
        );
      case 'INSUFFICIENT_BASELINE':
        return (
          <Badge variant="outline" className="text-muted-foreground border-dashed font-medium flex items-center gap-1">
            <HelpCircle className="h-3 w-3 text-muted-foreground" />
            INSUFFICIENT BASELINE
          </Badge>
        );
      case 'NORMAL':
        return (
          <Badge variant="secondary" className="font-medium">
            NORMAL
          </Badge>
        );
      default:
        return (
          <Badge variant="outline">
            {status}
          </Badge>
        );
    }
  };

  return (
    <div className="mx-auto w-full max-w-7xl px-4 py-6 sm:px-6 lg:px-8 space-y-6 sm:space-y-8">
      {/* Page Header */}
      <PageHeader
        title="Sales Analytics & Signals"
        description="Deterministic detection of recent velocity shifts (7-day demand vs 30-day historical baseline)."
        badge={<Badge variant="default" className="bg-primary/90">Live SQLite Analytics</Badge>}
      />

      {/* Sales KPI Summary Cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {/* Sales Spikes */}
        <Card className="bg-card shadow-sm border-l-4 border-l-emerald-500">
          <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
            <CardTitle className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
              Sales Spikes (≥ +50%)
            </CardTitle>
            <TrendingUp className="h-4 w-4 text-emerald-600" aria-hidden="true" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold tracking-tight text-emerald-600">
              {loading ? '...' : summary.spike_count}
            </div>
            <p className="mt-1 text-xs text-muted-foreground">
              Products exceeding recent velocity threshold
            </p>
          </CardContent>
        </Card>

        {/* Sales Drops */}
        <Card className="bg-card shadow-sm border-l-4 border-l-destructive">
          <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
            <CardTitle className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
              Sales Drops (≤ -40%)
            </CardTitle>
            <TrendingDown className="h-4 w-4 text-destructive" aria-hidden="true" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold tracking-tight text-destructive">
              {loading ? '...' : summary.drop_count}
            </div>
            <p className="mt-1 text-xs text-muted-foreground">
              Significant velocity contractions requiring review
            </p>
          </CardContent>
        </Card>

        {/* Total Active Signals */}
        <Card className="bg-card shadow-sm border-l-4 border-l-blue-500">
          <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
            <CardTitle className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
              Total Signals
            </CardTitle>
            <Zap className="h-4 w-4 text-blue-500" aria-hidden="true" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold tracking-tight">
              {loading ? '...' : summary.total_signals}
            </div>
            <p className="mt-1 text-xs text-muted-foreground">
              Combined spike and drop alerts
            </p>
          </CardContent>
        </Card>

        {/* Largest Change */}
        <Card className="bg-card shadow-sm border-l-4 border-l-amber-500">
          <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
            <CardTitle className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
              Largest Change
            </CardTitle>
            <Activity className="h-4 w-4 text-amber-500" aria-hidden="true" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold tracking-tight text-amber-600">
              {loading ? (
                '...'
              ) : summary.largest_change_pct !== null && summary.largest_change_pct !== undefined ? (
                `${summary.largest_change_pct.toFixed(1)}%`
              ) : (
                '—'
              )}
            </div>
            <p className="mt-1 text-xs text-muted-foreground">
              Peak velocity change magnitude
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Main Signals Section */}
      <div className="space-y-4">
        <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <SectionHeader
            title="Sales Signals & Anomaly Detection"
            description={
              salesData?.recent_start_date && salesData?.baseline_start_date
                ? `Comparing Recent 7d (${salesData.recent_start_date} to ${salesData.recent_end_date}) vs Baseline 30d (${salesData.baseline_start_date} to ${salesData.baseline_end_date})`
                : 'Deterministic comparison between recent 7-day velocity and 30-day baseline.'
            }
          />
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={loadData}
              disabled={loading}
              className="gap-1.5"
            >
              <RefreshCw className={`h-3.5 w-3.5 ${loading ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
          </div>
        </div>

        {/* Filters Bar */}
        <Card className="bg-card/50">
          <CardContent className="p-4">
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 md:grid-cols-4">
              {/* Search Bar */}
              <div className="relative">
                <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search product, SKU, store..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-8 text-sm"
                />
              </div>

              {/* Store Filter */}
              <div className="flex items-center space-x-2">
                <Store className="h-4 w-4 text-muted-foreground shrink-0" />
                <select
                  aria-label="Filter by Store"
                  value={selectedStore}
                  onChange={(e) => setSelectedStore(e.target.value)}
                  className="w-full rounded-md border border-input bg-background px-3 py-1.5 text-sm ring-offset-background focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
                >
                  <option value="ALL">All Stores</option>
                  {metadata.stores.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.store_name} ({s.store_code})
                    </option>
                  ))}
                </select>
              </div>

              {/* Category Filter */}
              <div className="flex items-center space-x-2">
                <Tag className="h-4 w-4 text-muted-foreground shrink-0" />
                <select
                  aria-label="Filter by Category"
                  value={selectedCategory}
                  onChange={(e) => setSelectedCategory(e.target.value)}
                  className="w-full rounded-md border border-input bg-background px-3 py-1.5 text-sm ring-offset-background focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
                >
                  <option value="ALL">All Categories</option>
                  {metadata.categories.map((c) => (
                    <option key={c} value={c}>
                      {c}
                    </option>
                  ))}
                </select>
              </div>

              {/* Status Filter */}
              <div className="flex items-center space-x-2">
                <Activity className="h-4 w-4 text-muted-foreground shrink-0" />
                <select
                  aria-label="Filter by Signal Status"
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                  className="w-full rounded-md border border-input bg-background px-3 py-1.5 text-sm ring-offset-background focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
                >
                  <option value="ALL">All Statuses</option>
                  <option value="SPIKE">Sales Spikes</option>
                  <option value="DROP">Sales Drops</option>
                  <option value="INSUFFICIENT_BASELINE">Insufficient Baseline</option>
                  <option value="NORMAL">Normal</option>
                </select>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Error State */}
        {error && (
          <Card className="border-destructive/50 bg-destructive/5">
            <CardContent className="p-4 flex items-center justify-between text-destructive">
              <div className="flex items-center gap-2">
                <AlertCircle className="h-5 w-5" />
                <span className="text-sm font-medium">{error}</span>
              </div>
              <Button variant="outline" size="sm" onClick={loadData}>
                Retry
              </Button>
            </CardContent>
          </Card>
        )}

        {/* Signals Table */}
        <Card>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="border-b bg-muted/40 text-xs uppercase text-muted-foreground font-semibold">
                <tr>
                  <th scope="col" className="px-4 py-3">Product</th>
                  <th scope="col" className="px-4 py-3">Store</th>
                  <th scope="col" className="px-4 py-3 text-right">Recent Sales (7d)</th>
                  <th scope="col" className="px-4 py-3 text-right">Baseline Avg/Day (30d)</th>
                  <th scope="col" className="px-4 py-3 text-right">Recent Avg/Day (7d)</th>
                  <th scope="col" className="px-4 py-3 text-right">Change</th>
                  <th scope="col" className="px-4 py-3 text-center">Signal</th>
                  <th scope="col" className="px-4 py-3 text-center">Details</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {loading ? (
                  <tr>
                    <td colSpan={8} className="px-4 py-12 text-center text-muted-foreground">
                      <div className="flex flex-col items-center justify-center gap-2">
                        <RefreshCw className="h-6 w-6 animate-spin text-primary" />
                        <p>Computing deterministic sales anomaly signals...</p>
                      </div>
                    </td>
                  </tr>
                ) : filteredResults.length === 0 ? (
                  <tr>
                    <td colSpan={8} className="p-8">
                      <EmptyState
                        icon={Activity}
                        title="No sales anomaly signals found"
                        description="No product-store combinations matched the selected filters or crossed anomaly thresholds."
                      />
                    </td>
                  </tr>
                ) : (
                  filteredResults.map((item) => {
                    const rowKey = `${item.store_id}-${item.product_id}`;
                    const isExpanded = expandedRows.has(rowKey);

                    return (
                      <React.Fragment key={rowKey}>
                        <tr
                          className={`transition-colors hover:bg-muted/30 cursor-pointer ${
                            item.status === 'SPIKE'
                              ? 'bg-emerald-500/5'
                              : item.status === 'DROP'
                              ? 'bg-destructive/5'
                              : ''
                          }`}
                          onClick={() => toggleRow(rowKey)}
                        >
                          {/* Product */}
                          <td className="px-4 py-3 font-medium">
                            <div className="flex flex-col">
                              <span className="text-foreground">{item.product_name}</span>
                              <span className="text-xs text-muted-foreground font-mono">
                                {item.sku} · {item.category}
                              </span>
                            </div>
                          </td>

                          {/* Store */}
                          <td className="px-4 py-3 text-muted-foreground whitespace-nowrap">
                            {item.store_name}
                          </td>

                          {/* Recent Sales (7d) */}
                          <td className="px-4 py-3 text-right font-medium">
                            {item.recent_quantity_sold} units
                          </td>

                          {/* Baseline Avg/Day (30d) */}
                          <td className="px-4 py-3 text-right text-muted-foreground">
                            {item.baseline_average_daily_sales.toFixed(2)}/day
                            <span className="block text-[11px] text-muted-foreground/75">
                              ({item.baseline_quantity_sold} in 30d)
                            </span>
                          </td>

                          {/* Recent Avg/Day (7d) */}
                          <td className="px-4 py-3 text-right font-semibold">
                            {item.recent_average_daily_sales.toFixed(2)}/day
                          </td>

                          {/* Change */}
                          <td className="px-4 py-3 text-right font-semibold whitespace-nowrap">
                            {item.percentage_change !== null && item.percentage_change !== undefined ? (
                              <span
                                className={
                                  item.percentage_change > 0
                                    ? 'text-emerald-600'
                                    : item.percentage_change < 0
                                    ? 'text-destructive'
                                    : 'text-muted-foreground'
                                }
                              >
                                {item.percentage_change > 0 ? '+' : ''}
                                {item.percentage_change.toFixed(1)}%
                              </span>
                            ) : (
                              <span className="text-muted-foreground text-xs italic">
                                Insufficient Baseline
                              </span>
                            )}
                            <span className="block text-[11px] text-muted-foreground font-normal">
                              ({item.absolute_change > 0 ? '+' : ''}
                              {item.absolute_change.toFixed(2)}/day)
                            </span>
                          </td>

                          {/* Signal */}
                          <td className="px-4 py-3 text-center whitespace-nowrap">
                            {getSignalBadge(item.status, item.percentage_change)}
                          </td>

                          {/* Expand Button */}
                          <td className="px-4 py-3 text-center">
                            <Button
                              variant="ghost"
                              size="sm"
                              className="h-7 w-7 p-0"
                              onClick={(e) => {
                                e.stopPropagation();
                                toggleRow(rowKey);
                              }}
                              aria-label="Toggle Details"
                            >
                              {isExpanded ? (
                                <ChevronUp className="h-4 w-4 text-muted-foreground" />
                              ) : (
                                <ChevronDown className="h-4 w-4 text-muted-foreground" />
                              )}
                            </Button>
                          </td>
                        </tr>

                        {/* Explainability Accordion Detail */}
                        {isExpanded && (
                          <tr className="bg-muted/20">
                            <td colSpan={8} className="px-6 py-4">
                              <div className="rounded-md border bg-card p-4 space-y-2">
                                <div className="flex items-center gap-2 text-xs font-semibold uppercase text-muted-foreground tracking-wider">
                                  <Info className="h-4 w-4 text-primary shrink-0" />
                                  Numerical Breakdown & Explanation
                                </div>
                                <p className="text-sm text-foreground leading-relaxed">
                                  {item.explanation}
                                </p>
                                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-2 text-xs border-t mt-3">
                                  <div>
                                    <span className="text-muted-foreground block">Recent Window:</span>
                                    <span className="font-medium font-mono">
                                      {item.recent_days} Days ({item.recent_quantity_sold} total units)
                                    </span>
                                  </div>
                                  <div>
                                    <span className="text-muted-foreground block">Historical Baseline:</span>
                                    <span className="font-medium font-mono">
                                      {item.baseline_days} Days ({item.baseline_quantity_sold} total units)
                                    </span>
                                  </div>
                                  <div>
                                    <span className="text-muted-foreground block">Velocity Delta:</span>
                                    <span className="font-medium font-mono">
                                      {item.absolute_change > 0 ? '+' : ''}
                                      {item.absolute_change.toFixed(2)} units/day
                                    </span>
                                  </div>
                                  <div>
                                    <span className="text-muted-foreground block">Classification:</span>
                                    <span className="font-medium font-mono">
                                      {item.status}
                                    </span>
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
        </Card>
      </div>
    </div>
  );
}

export default Sales;
