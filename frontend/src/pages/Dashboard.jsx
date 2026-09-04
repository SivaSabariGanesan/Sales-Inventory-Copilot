import React, { useState, useEffect } from 'react';
import PageHeader from '@/components/common/PageHeader';
import SectionHeader from '@/components/common/SectionHeader';
import EmptyState from '@/components/common/EmptyState';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { fetchDashboardSummary } from '@/services/dashboard';
import { fetchInventoryMetadata } from '@/services/inventory';
import { fetchValueAnalytics } from '@/services/analytics';
import {
  AlertTriangle,
  AlertCircle,
  TrendingUp,
  TrendingDown,
  Package,
  Activity,
  ArrowRight,
  RefreshCw,
  Clock,
  CheckCircle2,
  HelpCircle,
  Sparkles,
  ChevronDown,
  ChevronUp,
  Store,
  Tag,
  Flame,
  ShieldAlert,
  Building2,
  Boxes,
  Zap,
  Bot,
  Coins,
  DollarSign,
  Wallet,
} from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';

export function Dashboard() {
  const navigate = useNavigate();
  const [dashboardData, setDashboardData] = useState(null);
  const [valueData, setValueData] = useState(null);
  const [metadata, setMetadata] = useState({ stores: [], categories: [] });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Global Scope Filters
  const [selectedStore, setSelectedStore] = useState('ALL');
  const [selectedCategory, setSelectedCategory] = useState('ALL');

  // Expanded evidence state
  const [expandedCards, setExpandedCards] = useState(new Set());

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [summaryRes, metaRes, valRes] = await Promise.all([
        fetchDashboardSummary({
          storeId: selectedStore !== 'ALL' ? Number(selectedStore) : null,
          category: selectedCategory !== 'ALL' ? selectedCategory : null,
        }),
        fetchInventoryMetadata(),
        fetchValueAnalytics({
          storeId: selectedStore !== 'ALL' ? Number(selectedStore) : null,
          category: selectedCategory !== 'ALL' ? selectedCategory : null,
        }),
      ]);
      setDashboardData(summaryRes);
      setMetadata(metaRes);
      setValueData(valRes);
    } catch (err) {
      setError(err.message || 'Unable to load executive dashboard intelligence.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [selectedStore, selectedCategory]);

  const toggleCard = (id) => {
    setExpandedCards((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const kpis = dashboardData?.kpis || {
    total_products: 0,
    total_stores: 0,
    high_stockout_risks: 0,
    medium_stockout_risks: 0,
    overstocked_items: 0,
    severe_overstock_count: 0,
    no_recent_demand_count: 0,
    slow_moving_count: 0,
    sales_spikes: 0,
    sales_drops: 0,
    total_sales_signals: 0,
    urgent_action_items: 0,
  };

  const inventorySummary = dashboardData?.inventory_summary || {
    total_evaluated_skus: 0,
    healthy_count: 0,
    high_risk_count: 0,
    medium_risk_count: 0,
    overstock_count: 0,
    severe_overstock_count: 0,
    no_recent_demand_count: 0,
    slow_moving_count: 0,
  };

  const salesSummary = dashboardData?.sales_summary || {
    spike_count: 0,
    drop_count: 0,
    total_signals: 0,
    largest_spike: null,
    largest_drop: null,
  };

  const storeBreakdown = dashboardData?.store_breakdown || [];
  const attentionItems = dashboardData?.attention || [];

  const formattedTimestamp = dashboardData?.generated_at
    ? new Date(dashboardData.generated_at).toLocaleString([], {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      })
    : 'Updating...';

  const getPriorityBadge = (priority) => {
    switch (priority) {
      case 'HIGH':
        return (
          <Badge variant="destructive" className="font-semibold flex items-center gap-1">
            <Flame className="h-3 w-3" />
            HIGH PRIORITY
          </Badge>
        );
      case 'MEDIUM':
        return (
          <Badge className="bg-amber-600 hover:bg-amber-700 text-white font-semibold flex items-center gap-1">
            <AlertTriangle className="h-3 w-3" />
            MEDIUM PRIORITY
          </Badge>
        );
      case 'REVIEW':
        return (
          <Badge variant="outline" className="border-indigo-500 text-indigo-700 dark:text-indigo-400 font-semibold flex items-center gap-1">
            <HelpCircle className="h-3 w-3" />
            HUMAN REVIEW
          </Badge>
        );
      default:
        return (
          <Badge variant="secondary" className="font-semibold">
            {priority}
          </Badge>
        );
    }
  };

  return (
    <div className="mx-auto w-full max-w-7xl px-4 py-6 sm:px-6 lg:px-8 space-y-6 sm:space-y-8">
      {/* Header & Global Scope */}
      <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <PageHeader
          title="Executive Retail Dashboard"
          description="Consolidated operational intelligence, attention items, and health trajectory across the retail network."
          badge={<Badge variant="default" className="bg-primary/90">Deterministic SQLite Feed</Badge>}
        />
        <div className="flex flex-wrap items-center gap-2">
          <div className="text-xs text-muted-foreground flex items-center gap-1.5 font-mono">
            <Clock className="h-3.5 w-3.5 text-primary" />
            <span>Updated: {formattedTimestamp}</span>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={loadData}
            disabled={loading}
            className="gap-1.5 text-xs"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>
      </div>

      {/* Global Filter Bar */}
      <Card className="bg-card/60 shadow-xs border">
        <CardContent className="p-3.5 flex flex-wrap items-center justify-between gap-3">
          <div className="flex flex-wrap items-center gap-3">
            {/* Store Selector */}
            <div className="flex items-center space-x-2">
              <Store className="h-4 w-4 text-muted-foreground shrink-0" />
              <select
                aria-label="Filter Scope Store"
                value={selectedStore}
                onChange={(e) => setSelectedStore(e.target.value)}
                className="rounded-md border border-input bg-background px-3 py-1.5 text-xs sm:text-sm font-medium focus:outline-none focus:ring-2 focus:ring-ring"
              >
                <option value="ALL">All Stores (Network)</option>
                {metadata.stores.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.store_name} ({s.store_code})
                  </option>
                ))}
              </select>
            </div>

            {/* Category Selector */}
            <div className="flex items-center space-x-2">
              <Tag className="h-4 w-4 text-muted-foreground shrink-0" />
              <select
                aria-label="Filter Scope Category"
                value={selectedCategory}
                onChange={(e) => setSelectedCategory(e.target.value)}
                className="rounded-md border border-input bg-background px-3 py-1.5 text-xs sm:text-sm font-medium focus:outline-none focus:ring-2 focus:ring-ring"
              >
                <option value="ALL">All Categories</option>
                {metadata.categories.map((c) => (
                  <option key={c} value={c}>
                    {c}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Active Scope Tag */}
          <div className="text-xs text-muted-foreground font-mono bg-muted/40 px-2.5 py-1 rounded">
            Scope:{' '}
            <span className="font-semibold text-foreground">
              {dashboardData?.scope?.store_name || 'All Stores'} · {dashboardData?.scope?.category || 'All Categories'}
            </span>
          </div>
        </CardContent>
      </Card>

      {/* Error state */}
      {error && (
        <Card className="border-destructive/50 bg-destructive/5">
          <CardContent className="p-4 flex items-center justify-between text-destructive">
            <div className="flex items-center gap-2">
              <AlertCircle className="h-5 w-5" />
              <span className="text-sm font-medium">{error}</span>
            </div>
            <Button variant="outline" size="sm" onClick={loadData}>
              Try Again
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Top 5 KPI Cards */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
        {/* Products */}
        <Card className="bg-card shadow-xs transition-shadow hover:shadow-sm">
          <CardHeader className="flex flex-row items-center justify-between pb-1 space-y-0">
            <CardTitle className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
              Products
            </CardTitle>
            <Package className="h-4 w-4 text-muted-foreground" aria-hidden="true" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold tracking-tight">
              {loading ? '...' : kpis.total_products}
            </div>
            <p className="mt-0.5 text-[11px] text-muted-foreground">Catalog items in scope</p>
          </CardContent>
        </Card>

        {/* Active Stores */}
        <Card className="bg-card shadow-xs transition-shadow hover:shadow-sm">
          <CardHeader className="flex flex-row items-center justify-between pb-1 space-y-0">
            <CardTitle className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
              Stores
            </CardTitle>
            <Building2 className="h-4 w-4 text-muted-foreground" aria-hidden="true" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold tracking-tight">
              {loading ? '...' : kpis.total_stores}
            </div>
            <p className="mt-0.5 text-[11px] text-muted-foreground">Active locations</p>
          </CardContent>
        </Card>

        {/* Stock-Out Risks */}
        <Card className="bg-card shadow-xs border-l-4 border-l-destructive">
          <CardHeader className="flex flex-row items-center justify-between pb-1 space-y-0">
            <CardTitle className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
              Stock-Out Risks
            </CardTitle>
            <ShieldAlert className="h-4 w-4 text-destructive" aria-hidden="true" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold tracking-tight text-destructive">
              {loading ? '...' : kpis.high_stockout_risks}
            </div>
            <p className="mt-0.5 text-[11px] text-muted-foreground">
              {loading ? '' : `${kpis.medium_stockout_risks} medium risks pending`}
            </p>
          </CardContent>
        </Card>

        {/* Overstocked Items */}
        <Card className="bg-card shadow-xs border-l-4 border-l-amber-500">
          <CardHeader className="flex flex-row items-center justify-between pb-1 space-y-0">
            <CardTitle className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
              Overstocked
            </CardTitle>
            <Boxes className="h-4 w-4 text-amber-500" aria-hidden="true" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold tracking-tight text-amber-600">
              {loading ? '...' : kpis.overstocked_items}
            </div>
            <p className="mt-0.5 text-[11px] text-muted-foreground">
              {loading ? '' : `${kpis.severe_overstock_count} severe overstocked`}
            </p>
          </CardContent>
        </Card>

        {/* Sales Signals */}
        <Card className="bg-card shadow-xs border-l-4 border-l-blue-500">
          <CardHeader className="flex flex-row items-center justify-between pb-1 space-y-0">
            <CardTitle className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
              Sales Signals
            </CardTitle>
            <Zap className="h-4 w-4 text-blue-500" aria-hidden="true" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold tracking-tight text-blue-600">
              {loading ? '...' : kpis.total_sales_signals}
            </div>
            <p className="mt-0.5 text-[11px] text-muted-foreground">
              {loading ? '' : `${kpis.sales_spikes} spikes · ${kpis.sales_drops} drops`}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* SECTION: NEEDS ATTENTION TODAY */}
      <div className="space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
          <SectionHeader
            title="Needs Attention Today"
            description="Top actionable operational decisions prioritized by deterministic business urgency."
          />
          <Link to="/inventory">
            <Button variant="ghost" size="sm" className="gap-1 text-xs text-muted-foreground hover:text-foreground">
              View All Attention Items <ArrowRight className="h-3.5 w-3.5" />
            </Button>
          </Link>
        </div>

        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {[1, 2, 3].map((i) => (
              <Card key={i} className="animate-pulse bg-muted/30 h-48" />
            ))}
          </div>
        ) : attentionItems.length === 0 ? (
          <Card className="p-8">
            <EmptyState
              icon={CheckCircle2}
              title="You're all clear."
              description="No high-priority inventory deficits, overstocked items, or sales anomalies detected for the active scope."
            />
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {attentionItems.map((item) => {
              const isExpanded = expandedCards.has(item.id);

              return (
                <Card
                  key={item.id}
                  className={`flex flex-col justify-between transition-all hover:shadow-md border ${
                    item.priority === 'HIGH'
                      ? 'border-destructive/40 bg-destructive/5'
                      : item.priority === 'MEDIUM'
                      ? 'border-amber-500/40 bg-amber-500/5'
                      : 'border-border'
                  }`}
                >
                  <CardHeader className="pb-3 space-y-2">
                    <div className="flex items-start justify-between gap-2">
                      {getPriorityBadge(item.priority)}
                      <span className="text-[11px] font-mono text-muted-foreground uppercase">
                        {item.store_name}
                      </span>
                    </div>
                    <div>
                      <h4 className="text-sm font-bold text-foreground line-clamp-1">
                        {item.product_name}
                      </h4>
                      <p className="text-xs text-muted-foreground font-mono">
                        {item.sku} · {item.category}
                      </p>
                    </div>
                  </CardHeader>

                  <CardContent className="space-y-3 text-xs flex-1 flex flex-col justify-between">
                    <div className="space-y-2">
                      {/* Issue */}
                      <div className="rounded-md bg-background/80 p-2.5 border border-border/60 space-y-1">
                        <span className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground block">
                          Condition / Issue
                        </span>
                        <p className="text-xs font-medium text-foreground leading-snug">
                          {item.reason}
                        </p>
                      </div>

                      {/* Recommended Action */}
                      <div className="rounded-md bg-primary/5 p-2.5 border border-primary/20 space-y-1">
                        <span className="text-[10px] font-bold uppercase tracking-wider text-primary block flex items-center gap-1">
                          <Sparkles className="h-3 w-3" /> Recommended Action
                        </span>
                        <p className="text-xs font-semibold text-foreground leading-snug">
                          {item.recommendation}
                        </p>
                      </div>

                      {/* Human Review Banner */}
                      {item.needs_human_review && (
                        <div className="rounded bg-amber-500/10 p-2 text-[11px] text-amber-800 dark:text-amber-300 flex items-center gap-1.5">
                          <AlertTriangle className="h-3.5 w-3.5 shrink-0" />
                          <span>Manager validation recommended</span>
                        </div>
                      )}
                    </div>

                    {/* Expandable Evidence Accordion */}
                    <div className="pt-2 border-t mt-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => toggleCard(item.id)}
                        className="w-full justify-between h-7 px-1 text-[11px] text-muted-foreground hover:text-foreground"
                      >
                        <span>Evidence & Assumptions</span>
                        {isExpanded ? (
                          <ChevronUp className="h-3.5 w-3.5" />
                        ) : (
                          <ChevronDown className="h-3.5 w-3.5" />
                        )}
                      </Button>

                      {isExpanded && (
                        <div className="mt-2 pt-2 border-t space-y-2 bg-background/90 p-2.5 rounded border">
                          <div className="space-y-1">
                            <span className="text-[10px] font-bold text-muted-foreground uppercase">
                              Metrics Grounding:
                            </span>
                            <div className="grid grid-cols-2 gap-1 text-[11px] font-mono">
                              {Object.entries(item.evidence_metrics)
                                .filter(([k]) => k !== 'urgency_score')
                                .map(([key, val]) => (
                                  <div key={key}>
                                    <span className="text-muted-foreground">{key.replace(/_/g, ' ')}:</span>{' '}
                                    <span className="font-semibold text-foreground">
                                      {typeof val === 'number' ? (Number.isInteger(val) ? val : val.toFixed(2)) : String(val)}
                                    </span>
                                  </div>
                                ))}
                            </div>
                          </div>

                          {item.assumptions && item.assumptions.length > 0 && (
                            <div className="space-y-1 pt-1 border-t text-[10px] text-muted-foreground">
                              <span className="font-bold uppercase block">Assumptions:</span>
                              <ul className="list-disc pl-3.5 space-y-0.5">
                                {item.assumptions.map((asm, idx) => (
                                  <li key={idx}>{asm}</li>
                                ))}
                              </ul>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        )}
      </div>

      {/* HEALTH MATRIX: INVENTORY HEALTH & SALES HEALTH SPLIT */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* INVENTORY HEALTH OVERVIEW */}
        <div className="space-y-3">
          <SectionHeader
            title="Inventory Health Distribution"
            description="Real-time segmentation across evaluated store-product inventory units."
          />
          <Card className="bg-card shadow-xs">
            <CardContent className="p-4 space-y-4">
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 text-center">
                <div className="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/20">
                  <span className="text-xs text-emerald-700 dark:text-emerald-400 font-semibold uppercase block">
                    Healthy Stock
                  </span>
                  <span className="text-xl font-bold text-emerald-600">
                    {loading ? '...' : inventorySummary.healthy_count}
                  </span>
                </div>
                <div className="p-3 rounded-lg bg-destructive/10 border border-destructive/20">
                  <span className="text-xs text-destructive font-semibold uppercase block">
                    High Stockout
                  </span>
                  <span className="text-xl font-bold text-destructive">
                    {loading ? '...' : inventorySummary.high_risk_count}
                  </span>
                </div>
                <div className="p-3 rounded-lg bg-amber-500/10 border border-amber-500/20">
                  <span className="text-xs text-amber-700 dark:text-amber-400 font-semibold uppercase block">
                    Overstocked
                  </span>
                  <span className="text-xl font-bold text-amber-600">
                    {loading ? '...' : inventorySummary.overstock_count}
                  </span>
                </div>
                <div className="p-3 rounded-lg bg-indigo-500/10 border border-indigo-500/20">
                  <span className="text-xs text-indigo-700 dark:text-indigo-400 font-semibold uppercase block">
                    No Demand (30d)
                  </span>
                  <span className="text-xl font-bold text-indigo-600">
                    {loading ? '...' : inventorySummary.no_recent_demand_count}
                  </span>
                </div>
                <div className="p-3 rounded-lg bg-blue-500/10 border border-blue-500/20">
                  <span className="text-xs text-blue-700 dark:text-blue-400 font-semibold uppercase block">
                    Slow Moving
                  </span>
                  <span className="text-xl font-bold text-blue-600">
                    {loading ? '...' : inventorySummary.slow_moving_count}
                  </span>
                </div>
                <div className="p-3 rounded-lg bg-muted border">
                  <span className="text-xs text-muted-foreground font-semibold uppercase block">
                    Total Evaluated
                  </span>
                  <span className="text-xl font-bold text-foreground">
                    {loading ? '...' : inventorySummary.total_evaluated_skus}
                  </span>
                </div>
              </div>

              <div className="pt-2 flex justify-end">
                <Link to="/inventory">
                  <Button variant="outline" size="sm" className="text-xs gap-1">
                    Manage Inventory Intelligence <ArrowRight className="h-3 w-3" />
                  </Button>
                </Link>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* SALES HEALTH & ANOMALIES OVERVIEW */}
        <div className="space-y-3">
          <SectionHeader
            title="Sales Velocity Trajectory"
            description="7-day demand vs 30-day baseline extrema and anomaly distribution."
          />
          <Card className="bg-card shadow-xs">
            <CardContent className="p-4 space-y-4">
              <div className="grid grid-cols-2 gap-3 text-center">
                <div className="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/20">
                  <span className="text-xs text-emerald-700 dark:text-emerald-400 font-semibold uppercase block">
                    Demand Spikes (≥ +50%)
                  </span>
                  <span className="text-xl font-bold text-emerald-600">
                    {loading ? '...' : salesSummary.spike_count}
                  </span>
                </div>
                <div className="p-3 rounded-lg bg-destructive/10 border border-destructive/20">
                  <span className="text-xs text-destructive font-semibold uppercase block">
                    Sales Drops (≤ -40%)
                  </span>
                  <span className="text-xl font-bold text-destructive">
                    {loading ? '...' : salesSummary.drop_count}
                  </span>
                </div>
              </div>

              {/* Extrema Highlights */}
              <div className="space-y-2 pt-1">
                {salesSummary.largest_spike ? (
                  <div className="rounded-md border bg-muted/20 p-2.5 text-xs flex items-center justify-between">
                    <div className="space-y-0.5">
                      <span className="text-[10px] font-bold uppercase text-emerald-600 flex items-center gap-1">
                        <TrendingUp className="h-3 w-3" /> Peak Velocity Surge
                      </span>
                      <p className="font-semibold text-foreground">
                        {salesSummary.largest_spike.product}{' '}
                        <span className="text-muted-foreground font-normal">
                          ({salesSummary.largest_spike.store})
                        </span>
                      </p>
                    </div>
                    <Badge className="bg-emerald-600 text-white font-mono">
                      +{salesSummary.largest_spike.change_pct.toFixed(1)}%
                    </Badge>
                  </div>
                ) : null}

                {salesSummary.largest_drop ? (
                  <div className="rounded-md border bg-muted/20 p-2.5 text-xs flex items-center justify-between">
                    <div className="space-y-0.5">
                      <span className="text-[10px] font-bold uppercase text-destructive flex items-center gap-1">
                        <TrendingDown className="h-3 w-3" /> Peak Velocity Drop
                      </span>
                      <p className="font-semibold text-foreground">
                        {salesSummary.largest_drop.product}{' '}
                        <span className="text-muted-foreground font-normal">
                          ({salesSummary.largest_drop.store})
                        </span>
                      </p>
                    </div>
                    <Badge variant="destructive" className="font-mono">
                      {salesSummary.largest_drop.change_pct.toFixed(1)}%
                    </Badge>
                  </div>
                ) : null}
              </div>

              <div className="pt-2 flex justify-end">
                <Link to="/sales">
                  <Button variant="outline" size="sm" className="text-xs gap-1">
                    Explore Sales Signals <ArrowRight className="h-3 w-3" />
                  </Button>
                </Link>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* SECTION: BUSINESS VALUE & FINANCIAL ANALYTICS */}
      <div className="space-y-4">
        <SectionHeader
          title="Business Value & Financials"
          description="Authoritative inventory valuation, total sales revenue, and capital tied up in slow-moving stock."
        />

        {/* 3 Financial KPI Cards */}
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <Card className="border-border bg-card shadow-xs">
            <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
              <CardTitle className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                Total Inventory Value
              </CardTitle>
              <Wallet className="h-4 w-4 text-emerald-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold tracking-tight text-foreground">
                {loading ? '...' : (valueData ? valueData.total_inventory_value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : '0.00')}
              </div>
              <p className="mt-1 text-xs text-muted-foreground">
                {loading ? '' : `Across ${valueData?.total_stock_units?.toLocaleString() || 0} total stock units`}
              </p>
            </CardContent>
          </Card>

          <Card className="border-border bg-card shadow-xs">
            <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
              <CardTitle className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                Total Sales Revenue
              </CardTitle>
              <DollarSign className="h-4 w-4 text-blue-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold tracking-tight text-blue-600">
                {loading ? '...' : (valueData ? valueData.total_sales_revenue.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : '0.00')}
              </div>
              <p className="mt-1 text-xs text-muted-foreground">
                {loading ? '' : `From ${valueData?.total_sales_units?.toLocaleString() || 0} total units sold`}
              </p>
            </CardContent>
          </Card>

          <Card className="border-border bg-card shadow-xs border-l-4 border-l-amber-500">
            <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
              <CardTitle className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                Overstock Capital Tied Up
              </CardTitle>
              <Coins className="h-4 w-4 text-amber-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold tracking-tight text-amber-600">
                {loading ? '...' : (valueData ? valueData.overstock_inventory_value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : '0.00')}
              </div>
              <p className="mt-1 text-xs text-muted-foreground">
                {loading ? '' : `In ${valueData?.overstock_summary?.products_affected_count || 0} slow-moving / overstocked SKUs`}
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Top Products by Revenue & Top Stores by Revenue */}
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          {/* Top Revenue Products Card */}
          <Card className="bg-card shadow-xs">
            <CardHeader className="pb-3 border-b border-border/40">
              <CardTitle className="text-sm font-bold text-foreground flex items-center justify-between">
                <span>Top Products by Revenue</span>
                <Badge variant="outline" className="text-[10px]">Authoritative</Badge>
              </CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-muted/40 text-muted-foreground uppercase font-semibold">
                    <tr>
                      <th className="px-3 py-2">Product</th>
                      <th className="px-3 py-2 text-right">Units Sold</th>
                      <th className="px-3 py-2 text-right">Revenue</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border/40">
                    {loading ? (
                      <tr>
                        <td colSpan={3} className="py-6 text-center text-muted-foreground">Loading top products...</td>
                      </tr>
                    ) : (!valueData?.top_products_by_revenue || valueData.top_products_by_revenue.length === 0) ? (
                      <tr>
                        <td colSpan={3} className="py-6 text-center text-muted-foreground">No product sales in active scope.</td>
                      </tr>
                    ) : (
                      valueData.top_products_by_revenue.slice(0, 5).map((p) => (
                        <tr key={p.product_id} className="hover:bg-muted/20">
                          <td className="px-3 py-2 font-medium text-foreground">
                            <div className="truncate max-w-[200px]" title={p.product_name}>{p.product_name}</div>
                            <span className="text-[10px] text-muted-foreground font-mono">{p.sku} · {p.category}</span>
                          </td>
                          <td className="px-3 py-2 text-right text-muted-foreground">{p.total_sales_quantity}</td>
                          <td className="px-3 py-2 text-right font-semibold text-foreground">
                            {p.total_revenue.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>

          {/* Top Stores by Revenue Card */}
          <Card className="bg-card shadow-xs">
            <CardHeader className="pb-3 border-b border-border/40">
              <CardTitle className="text-sm font-bold text-foreground flex items-center justify-between">
                <span>Top Stores by Revenue</span>
                <Badge variant="outline" className="text-[10px]">Network</Badge>
              </CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-muted/40 text-muted-foreground uppercase font-semibold">
                    <tr>
                      <th className="px-3 py-2">Store</th>
                      <th className="px-3 py-2 text-right">Inventory Value</th>
                      <th className="px-3 py-2 text-right">Revenue</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border/40">
                    {loading ? (
                      <tr>
                        <td colSpan={3} className="py-6 text-center text-muted-foreground">Loading store performance...</td>
                      </tr>
                    ) : (!valueData?.top_stores_by_revenue || valueData.top_stores_by_revenue.length === 0) ? (
                      <tr>
                        <td colSpan={3} className="py-6 text-center text-muted-foreground">No store records found.</td>
                      </tr>
                    ) : (
                      valueData.top_stores_by_revenue.slice(0, 5).map((s) => (
                        <tr key={s.store_id} className="hover:bg-muted/20">
                          <td className="px-3 py-2 font-medium text-foreground">
                            <div>{s.store_name}</div>
                            <span className="text-[10px] text-muted-foreground font-mono">{s.store_code}</span>
                          </td>
                          <td className="px-3 py-2 text-right text-muted-foreground">
                            {s.total_inventory_value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                          </td>
                          <td className="px-3 py-2 text-right font-semibold text-foreground">
                            {s.total_revenue.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* STORE NETWORK PERFORMANCE BREAKDOWN TABLE */}
      <div className="space-y-3">
        <SectionHeader
          title="Store Network Breakdown"
          description="Operational risk and velocity signals compared across active store locations."
        />
        <Card>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="border-b bg-muted/40 text-xs uppercase text-muted-foreground font-semibold">
                <tr>
                  <th scope="col" className="px-4 py-3">Store Location</th>
                  <th scope="col" className="px-4 py-3 text-right">High Stockout</th>
                  <th scope="col" className="px-4 py-3 text-right">Med Stockout</th>
                  <th scope="col" className="px-4 py-3 text-right">Overstock</th>
                  <th scope="col" className="px-4 py-3 text-right">Severe Overstock</th>
                  <th scope="col" className="px-4 py-3 text-right">Spikes</th>
                  <th scope="col" className="px-4 py-3 text-right">Drops</th>
                  <th scope="col" className="px-4 py-3 text-right">Urgent Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border text-xs">
                {loading ? (
                  <tr>
                    <td colSpan={8} className="p-8 text-center text-muted-foreground">
                      <RefreshCw className="h-5 w-5 animate-spin mx-auto mb-2 text-primary" />
                      Loading store breakdown matrix...
                    </td>
                  </tr>
                ) : storeBreakdown.length === 0 ? (
                  <tr>
                    <td colSpan={8} className="p-6 text-center text-muted-foreground">
                      No store performance records found for active scope.
                    </td>
                  </tr>
                ) : (
                  storeBreakdown.map((st) => (
                    <tr key={st.store_id} className="hover:bg-muted/30 transition-colors">
                      <td className="px-4 py-3 font-semibold text-foreground">
                        <div>
                          {st.store_name}
                          <span className="block text-[11px] text-muted-foreground font-mono font-normal">
                            Code: {st.store_code}
                          </span>
                        </div>
                      </td>
                      <td className="px-4 py-3 text-right font-semibold text-destructive">
                        {st.high_stockouts}
                      </td>
                      <td className="px-4 py-3 text-right text-amber-600 font-medium">
                        {st.medium_stockouts}
                      </td>
                      <td className="px-4 py-3 text-right font-medium text-foreground">
                        {st.overstocked_items}
                      </td>
                      <td className="px-4 py-3 text-right text-amber-600 font-semibold">
                        {st.severe_overstock_count}
                      </td>
                      <td className="px-4 py-3 text-right text-emerald-600 font-semibold">
                        +{st.sales_spikes}
                      </td>
                      <td className="px-4 py-3 text-right text-destructive font-semibold">
                        -{st.sales_drops}
                      </td>
                      <td className="px-4 py-3 text-right">
                        <Badge
                          variant={st.urgent_action_count > 0 ? 'destructive' : 'secondary'}
                          className="font-mono"
                        >
                          {st.urgent_action_count} urgent
                        </Badge>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </Card>
      </div>

      {/* COPILOT FAST-LAUNCH ACTION STRIP */}
      <Card className="bg-primary/5 border-primary/20 shadow-xs">
        <CardContent className="p-5 flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-3.5">
            <div className="h-10 w-10 rounded-full bg-primary text-primary-foreground flex items-center justify-center shrink-0">
              <Bot className="h-5 w-5" />
            </div>
            <div>
              <h4 className="text-sm font-bold text-foreground">
                Ask Retail Copilot
              </h4>
              <p className="text-xs text-muted-foreground">
                Natural-language decisions grounded in verified SQLite data.
              </p>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            {[
              'Which products are at risk of running out?',
              'What inventory is overstocked?',
              'What should I do today?',
            ].map((prompt, i) => (
              <Button
                key={i}
                variant="outline"
                size="sm"
                onClick={() => navigate('/copilot')}
                className="text-xs bg-background hover:bg-muted"
              >
                {prompt}
              </Button>
            ))}
            <Link to="/copilot">
              <Button size="sm" className="gap-1.5 text-xs font-semibold">
                Open Copilot <ArrowRight className="h-3.5 w-3.5" />
              </Button>
            </Link>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export default Dashboard;
