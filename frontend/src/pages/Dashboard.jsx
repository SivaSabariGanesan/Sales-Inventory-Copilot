import React, { useState, useEffect } from 'react';
import PageHeader from '@/components/common/PageHeader';
import SectionHeader from '@/components/common/SectionHeader';
import EmptyState from '@/components/common/EmptyState';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { fetchTodaysAttention, fetchRecommendations } from '@/services/recommendations';
import {
  AlertTriangle,
  AlertCircle,
  TrendingUp,
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
} from 'lucide-react';
import { Link } from 'react-router-dom';

export function Dashboard() {
  const [attentionData, setAttentionData] = useState(null);
  const [summaryData, setSummaryData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [expandedCards, setExpandedCards] = useState(new Set());

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [todayRes, allRecsRes] = await Promise.all([
        fetchTodaysAttention(6),
        fetchRecommendations(),
      ]);
      setAttentionData(todayRes);
      setSummaryData(allRecsRes);
    } catch (err) {
      setError(err.message || 'Unable to load executive dashboard recommendations.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const toggleCard = (id) => {
    setExpandedCards((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const summary = summaryData?.summary || {
    high_priority_count: 0,
    medium_priority_count: 0,
    low_priority_count: 0,
    review_count: 0,
    total_recommendations: 0,
  };

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
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
        <PageHeader
          title="Executive Decision Dashboard"
          description="Action recommendations and operational priorities grounded in real-time retail intelligence."
          badge={<Badge variant="default" className="bg-primary/90">Deterministic Analytics</Badge>}
        />
        <Button
          variant="outline"
          size="sm"
          onClick={loadData}
          disabled={loading}
          className="self-start sm:self-auto gap-1.5"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${loading ? 'animate-spin' : ''}`} />
          Refresh Feed
        </Button>
      </div>

      {/* Overview KPI Cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {/* Urgent High Priority Actions */}
        <Card className="bg-card shadow-sm border-l-4 border-l-destructive">
          <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
            <CardTitle className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
              Urgent Actions (High)
            </CardTitle>
            <ShieldAlert className="h-4 w-4 text-destructive" aria-hidden="true" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold tracking-tight text-destructive">
              {loading ? '...' : summary.high_priority_count}
            </div>
            <p className="mt-1 text-xs text-muted-foreground">
              Critical stockouts requiring immediate reorder
            </p>
          </CardContent>
        </Card>

        {/* Medium Priority Decisions */}
        <Card className="bg-card shadow-sm border-l-4 border-l-amber-500">
          <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
            <CardTitle className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
              Planned Decisions (Med)
            </CardTitle>
            <AlertTriangle className="h-4 w-4 text-amber-500" aria-hidden="true" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold tracking-tight text-amber-600">
              {loading ? '...' : summary.medium_priority_count}
            </div>
            <p className="mt-1 text-xs text-muted-foreground">
              Impending stockouts, overstock, or anomaly shifts
            </p>
          </CardContent>
        </Card>

        {/* Manager Review Items */}
        <Card className="bg-card shadow-sm border-l-4 border-l-indigo-500">
          <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
            <CardTitle className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
              Human Review Needed
            </CardTitle>
            <HelpCircle className="h-4 w-4 text-indigo-500" aria-hidden="true" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold tracking-tight text-indigo-600">
              {loading ? '...' : summary.review_count}
            </div>
            <p className="mt-1 text-xs text-muted-foreground">
              No recent demand or sales declines needing context
            </p>
          </CardContent>
        </Card>

        {/* Total Recommendations */}
        <Card className="bg-card shadow-sm border-l-4 border-l-blue-500">
          <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
            <CardTitle className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
              Total Action Items
            </CardTitle>
            <Activity className="h-4 w-4 text-blue-500" aria-hidden="true" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold tracking-tight">
              {loading ? '...' : summary.total_recommendations}
            </div>
            <p className="mt-1 text-xs text-muted-foreground">
              Deduplicated alerts across active store network
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Error state */}
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

      {/* NEEDS ATTENTION TODAY SECTION */}
      <div className="space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
          <SectionHeader
            title="Needs Attention Today"
            description="Highest-priority action items synthesized from deterministic stock-out, overstock, and sales velocity models."
          />
          <Link to="/inventory">
            <Button variant="ghost" size="sm" className="gap-1 text-xs text-muted-foreground hover:text-foreground">
              View All Inventory Risks <ArrowRight className="h-3.5 w-3.5" />
            </Button>
          </Link>
        </div>

        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {[1, 2, 3].map((i) => (
              <Card key={i} className="animate-pulse bg-muted/30 h-48" />
            ))}
          </div>
        ) : !attentionData?.results || attentionData.results.length === 0 ? (
          <Card className="p-8">
            <EmptyState
              icon={CheckCircle2}
              title="All systems optimal"
              description="No urgent stockout, overstock, or anomalous conditions detected across the network."
            />
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {attentionData.results.map((item) => {
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

                      {/* Human Review banner */}
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
                        <span>Numerical Evidence & Assumptions</span>
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

      {/* Quick Navigation Split */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3 pt-2">
        <Link to="/inventory">
          <Card className="hover:border-primary/50 transition-colors p-4 flex items-center justify-between cursor-pointer">
            <div>
              <h4 className="text-sm font-semibold">Stock-Out Risks</h4>
              <p className="text-xs text-muted-foreground">Monitor low stock and replenishment urgency</p>
            </div>
            <ArrowRight className="h-4 w-4 text-muted-foreground" />
          </Card>
        </Link>
        <Link to="/sales">
          <Card className="hover:border-primary/50 transition-colors p-4 flex items-center justify-between cursor-pointer">
            <div>
              <h4 className="text-sm font-semibold">Sales Velocity Signals</h4>
              <p className="text-xs text-muted-foreground">Inspect sudden spikes and drops vs 30d baseline</p>
            </div>
            <ArrowRight className="h-4 w-4 text-muted-foreground" />
          </Card>
        </Link>
        <Link to="/copilot">
          <Card className="hover:border-primary/50 transition-colors p-4 flex items-center justify-between cursor-pointer">
            <div>
              <h4 className="text-sm font-semibold">Ask Retail Copilot</h4>
              <p className="text-xs text-muted-foreground">Natural language queries with grounded answers</p>
            </div>
            <ArrowRight className="h-4 w-4 text-muted-foreground" />
          </Card>
        </Link>
      </div>
    </div>
  );
}

export default Dashboard;
