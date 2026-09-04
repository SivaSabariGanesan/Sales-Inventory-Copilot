import React, { useState, useEffect } from 'react';
import PageHeader from '@/components/common/PageHeader';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { fetchAuditLogs, fetchAuditLogDetail, fetchGeminiUsage } from '@/services/audit';
import {
  ShieldCheck,
  Search,
  Filter,
  RefreshCw,
  Eye,
  CheckCircle2,
  AlertTriangle,
  AlertCircle,
  Zap,
  Cpu,
  Database,
  Layers,
  Clock,
  Coins,
  ChevronLeft,
  ChevronRight,
  X,
  Code2,
  Terminal,
  Server,
  ArrowRight,
} from 'lucide-react';

export function AuditTrail() {
  const [logs, setLogs] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(15);
  const [totalPages, setTotalPages] = useState(1);
  const [loading, setLoading] = useState(false);
  const [usageLoading, setUsageLoading] = useState(false);
  const [usage, setUsage] = useState(null);

  // Filters
  const [search, setSearch] = useState('');
  const [intentFilter, setIntentFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [cacheHitFilter, setCacheHitFilter] = useState('');
  const [humanReviewFilter, setHumanReviewFilter] = useState('');

  // Selected Detail Modal
  const [selectedLogId, setSelectedLogId] = useState(null);
  const [detailModalOpen, setDetailModalOpen] = useState(false);
  const [detailData, setDetailData] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);

  // Load telemetry stats
  const loadUsageMetrics = async () => {
    setUsageLoading(true);
    try {
      const data = await fetchGeminiUsage();
      setUsage(data);
    } catch (err) {
      console.error('Failed to load usage metrics:', err);
    } finally {
      setUsageLoading(false);
    }
  };

  // Load audit logs
  const loadLogs = async () => {
    setLoading(true);
    try {
      const data = await fetchAuditLogs({
        page,
        pageSize,
        search: search.trim() || undefined,
        intent: intentFilter || undefined,
        status: statusFilter || undefined,
        cacheHit: cacheHitFilter !== '' ? cacheHitFilter : undefined,
        needsHumanReview: humanReviewFilter !== '' ? humanReviewFilter : undefined,
      });
      setLogs(data.logs || []);
      setTotal(data.total || 0);
      setTotalPages(data.total_pages || 1);
    } catch (err) {
      console.error('Failed to load audit logs:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadUsageMetrics();
  }, []);

  useEffect(() => {
    loadLogs();
  }, [page, pageSize, intentFilter, statusFilter, cacheHitFilter, humanReviewFilter]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    setPage(1);
    loadLogs();
  };

  const handleOpenDetail = async (logId) => {
    setSelectedLogId(logId);
    setDetailModalOpen(true);
    setDetailLoading(true);
    try {
      const detail = await fetchAuditLogDetail(logId);
      setDetailData(detail);
    } catch (err) {
      console.error('Failed to load audit detail:', err);
    } finally {
      setDetailLoading(false);
    }
  };

  const handleCloseDetail = () => {
    setDetailModalOpen(false);
    setDetailData(null);
    setSelectedLogId(null);
  };

  const getStatusBadge = (status, cacheHit, needsHumanReview) => {
    if (cacheHit) {
      return (
        <span className="inline-flex items-center gap-1 rounded-full bg-blue-50 px-2 py-0.5 text-xs font-semibold text-blue-700 dark:bg-blue-950/50 dark:text-blue-300">
          <Zap className="h-3 w-3" /> Cache Hit
        </span>
      );
    }
    if (needsHumanReview) {
      return (
        <span className="inline-flex items-center gap-1 rounded-full bg-amber-50 px-2 py-0.5 text-xs font-semibold text-amber-700 dark:bg-amber-950/50 dark:text-amber-300">
          <AlertTriangle className="h-3 w-3" /> Human Review
        </span>
      );
    }
    if (status === 'success') {
      return (
        <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2 py-0.5 text-xs font-semibold text-emerald-700 dark:bg-emerald-950/50 dark:text-emerald-300">
          <CheckCircle2 className="h-3 w-3" /> Success
        </span>
      );
    }
    if (status === 'fallback') {
      return (
        <span className="inline-flex items-center gap-1 rounded-full bg-purple-50 px-2 py-0.5 text-xs font-semibold text-purple-700 dark:bg-purple-950/50 dark:text-purple-300">
          <Layers className="h-3 w-3" /> Fallback
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1 rounded-full bg-rose-50 px-2 py-0.5 text-xs font-semibold text-rose-700 dark:bg-rose-950/50 dark:text-rose-300">
        <AlertCircle className="h-3 w-3" /> {status}
      </span>
    );
  };

  return (
    <div className="space-y-6 pb-12">
      {/* Header */}
      <PageHeader
        title="AI Audit Trail & Governance"
        description="Comprehensive audit logging, execution flow tracing, Gemini usage metrics, and deterministic cache verification."
      />

      {/* Top KPI Cards: Gemini Usage & Telemetry */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card className="border-border/60 bg-card shadow-xs">
          <CardContent className="p-5">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                Total Queries Logged
              </span>
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10 text-primary">
                <ShieldCheck className="h-4 w-4" />
              </div>
            </div>
            <div className="mt-3 flex items-baseline gap-2">
              <span className="text-2xl font-bold tracking-tight text-foreground">
                {usage ? usage.total_interactions.toLocaleString() : '0'}
              </span>
              <span className="text-xs text-muted-foreground">all-time requests</span>
            </div>
            <div className="mt-2 text-xs text-muted-foreground">
              Current Data Version: <span className="font-semibold text-foreground">v{usage ? usage.current_data_version : '1'}</span>
            </div>
          </CardContent>
        </Card>

        <Card className="border-border/60 bg-card shadow-xs">
          <CardContent className="p-5">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                Cache Hit Efficiency
              </span>
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-500/10 text-blue-500">
                <Zap className="h-4 w-4" />
              </div>
            </div>
            <div className="mt-3 flex items-baseline gap-2">
              <span className="text-2xl font-bold tracking-tight text-foreground">
                {usage ? `${usage.cache_hit_rate_pct}%` : '0%'}
              </span>
              <span className="text-xs text-muted-foreground">
                ({usage ? usage.total_cache_hits : 0} hits)
              </span>
            </div>
            <div className="mt-2 text-xs text-muted-foreground">
              Active cached entries: <span className="font-semibold text-foreground">{usage ? usage.active_cached_entries : 0}</span>
            </div>
          </CardContent>
        </Card>

        <Card className="border-border/60 bg-card shadow-xs">
          <CardContent className="p-5">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                Gemini Token Telemetry
              </span>
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-500/10 text-emerald-500">
                <Cpu className="h-4 w-4" />
              </div>
            </div>
            <div className="mt-3 flex items-baseline gap-2">
              <span className="text-2xl font-bold tracking-tight text-foreground">
                {usage ? (usage.total_input_tokens + usage.total_output_tokens).toLocaleString() : '0'}
              </span>
              <span className="text-xs text-muted-foreground">total tokens</span>
            </div>
            <div className="mt-2 flex items-center justify-between text-xs text-muted-foreground">
              <span>In: {usage ? usage.total_input_tokens.toLocaleString() : 0}</span>
              <span>Out: {usage ? usage.total_output_tokens.toLocaleString() : 0}</span>
              <span>Calls: {usage ? usage.total_gemini_calls : 0}</span>
            </div>
          </CardContent>
        </Card>

        <Card className="border-border/60 bg-card shadow-xs">
          <CardContent className="p-5">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                Cost Transparency
              </span>
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-amber-500/10 text-amber-500">
                <Coins className="h-4 w-4" />
              </div>
            </div>
            <div className="mt-3 flex items-baseline gap-2">
              <span className="text-xl font-bold tracking-tight text-foreground">
                {usage ? usage.estimated_cost_display : 'Cost unavailable'}
              </span>
            </div>
            <div className="mt-2 text-[11px] leading-tight text-muted-foreground">
              Deterministic tracking; no synthetic billing estimates fabricated.
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Filter & Table Card */}
      <Card className="border-border/60 bg-card shadow-xs">
        <CardHeader className="border-b border-border/40 pb-4">
          <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
            <div>
              <CardTitle className="text-base font-semibold text-foreground">
                Copilot Execution Logs
              </CardTitle>
              <p className="mt-1 text-xs text-muted-foreground">
                Immutable audit records with prompt version, data version, and deterministic evidence inspection.
              </p>
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  loadUsageMetrics();
                  loadLogs();
                }}
                disabled={loading}
                className="gap-1.5"
              >
                <RefreshCw className={`h-3.5 w-3.5 ${loading ? 'animate-spin' : ''}`} />
                Refresh Logs
              </Button>
            </div>
          </div>

          {/* Filter Controls */}
          <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-5">
            <form onSubmit={handleSearchSubmit} className="relative sm:col-span-2">
              <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search natural question..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-9 text-sm"
              />
            </form>

            <div>
              <select
                value={intentFilter}
                onChange={(e) => {
                  setIntentFilter(e.target.value);
                  setPage(1);
                }}
                className="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm shadow-xs focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
              >
                <option value="">All Intents</option>
                <option value="inventory_status">Inventory Status</option>
                <option value="stockout_risk">Stockout Risk</option>
                <option value="overstock">Overstock / Slow-Moving</option>
                <option value="sales_trend">Sales Trend</option>
                <option value="sales_anomaly">Sales Anomaly</option>
                <option value="reorder_recommendation">Reorder Recommendation</option>
                <option value="general_retail">General Retail</option>
                <option value="unknown">Unknown</option>
              </select>
            </div>

            <div>
              <select
                value={statusFilter}
                onChange={(e) => {
                  setStatusFilter(e.target.value);
                  setPage(1);
                }}
                className="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm shadow-xs focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
              >
                <option value="">All Statuses</option>
                <option value="success">Success</option>
                <option value="fallback">Fallback</option>
                <option value="human_review">Human Review</option>
                <option value="error">Error</option>
              </select>
            </div>

            <div className="flex gap-2">
              <select
                value={cacheHitFilter}
                onChange={(e) => {
                  setCacheHitFilter(e.target.value);
                  setPage(1);
                }}
                className="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm shadow-xs focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
              >
                <option value="">All Caches</option>
                <option value="true">Cache Hits Only</option>
                <option value="false">Live Gemini Only</option>
              </select>
            </div>
          </div>
        </CardHeader>

        {/* Audit Table */}
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="border-b border-border/60 bg-muted/40 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                <tr>
                  <th className="px-4 py-3">Timestamp</th>
                  <th className="px-4 py-3">User Question</th>
                  <th className="px-4 py-3">Intent & Confidence</th>
                  <th className="px-4 py-3">Status / Cache</th>
                  <th className="px-4 py-3">Tokens / Calls</th>
                  <th className="px-4 py-3">Latency</th>
                  <th className="px-4 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border/40">
                {loading ? (
                  <tr>
                    <td colSpan={7} className="px-4 py-12 text-center text-muted-foreground">
                      <div className="flex flex-col items-center justify-center gap-2">
                        <RefreshCw className="h-6 w-6 animate-spin text-primary" />
                        <span>Loading audit logs...</span>
                      </div>
                    </td>
                  </tr>
                ) : logs.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="px-4 py-12 text-center text-muted-foreground">
                      <div className="flex flex-col items-center justify-center gap-2">
                        <ShieldCheck className="h-8 w-8 text-muted-foreground/50" />
                        <span className="font-medium text-foreground">No audit logs found</span>
                        <span className="text-xs">Try clearing filters or asking Copilot a question.</span>
                      </div>
                    </td>
                  </tr>
                ) : (
                  logs.map((log) => (
                    <tr
                      key={log.id}
                      className="transition-colors hover:bg-muted/30"
                    >
                      <td className="whitespace-nowrap px-4 py-3 text-xs text-muted-foreground">
                        {new Date(log.timestamp).toLocaleString(undefined, {
                          month: 'short',
                          day: 'numeric',
                          hour: '2-digit',
                          minute: '2-digit',
                          second: '2-digit',
                        })}
                      </td>
                      <td className="max-w-xs truncate px-4 py-3 font-medium text-foreground">
                        <div className="truncate" title={log.question}>
                          {log.question}
                        </div>
                        {log.normalized_question !== log.question && (
                          <div className="truncate text-[11px] text-muted-foreground" title={log.normalized_question}>
                            Norm: {log.normalized_question}
                          </div>
                        )}
                      </td>
                      <td className="whitespace-nowrap px-4 py-3">
                        <div className="text-xs font-medium text-foreground">
                          {log.intent || 'unknown'}
                        </div>
                        <div className="text-[11px] text-muted-foreground">
                          {log.confidence !== null ? `${Math.round(log.confidence * 100)}% conf` : 'N/A'}
                        </div>
                      </td>
                      <td className="whitespace-nowrap px-4 py-3">
                        {getStatusBadge(log.status, log.cache_hit, log.needs_human_review)}
                      </td>
                      <td className="whitespace-nowrap px-4 py-3 text-xs text-muted-foreground">
                        {log.cache_hit ? (
                          <span className="text-blue-600 dark:text-blue-400 font-medium">0 tokens (Cached)</span>
                        ) : (
                          <div>
                            <span className="font-medium text-foreground">
                              {(log.input_tokens || 0) + (log.output_tokens || 0)} tok
                            </span>
                            <span className="text-[11px]"> ({log.gemini_calls || 0} API call)</span>
                          </div>
                        )}
                      </td>
                      <td className="whitespace-nowrap px-4 py-3 text-xs text-muted-foreground">
                        {log.response_time_ms !== null ? `${log.response_time_ms}ms` : '—'}
                      </td>
                      <td className="whitespace-nowrap px-4 py-3 text-right">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleOpenDetail(log.id)}
                          className="h-8 gap-1 px-2 text-xs font-medium"
                        >
                          <Eye className="h-3.5 w-3.5 text-muted-foreground" />
                          Inspect
                        </Button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          <div className="flex items-center justify-between border-t border-border/40 px-4 py-3 text-xs text-muted-foreground">
            <div>
              Showing <span className="font-medium text-foreground">{logs.length}</span> of{' '}
              <span className="font-medium text-foreground">{total}</span> interactions
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page <= 1 || loading}
                className="h-7 px-2"
              >
                <ChevronLeft className="h-3.5 w-3.5" />
                Previous
              </Button>
              <span>
                Page {page} of {totalPages}
              </span>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page >= totalPages || loading}
                className="h-7 px-2"
              >
                Next
                <ChevronRight className="h-3.5 w-3.5" />
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Execution Flow & Evidence Modal */}
      {detailModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-xs">
          <div className="relative flex max-h-[90vh] w-full max-w-4xl flex-col rounded-xl border border-border bg-card shadow-2xl overflow-hidden">
            {/* Modal Header */}
            <div className="flex items-center justify-between border-b border-border px-6 py-4">
              <div className="flex items-center gap-3">
                <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary/10 text-primary">
                  <ShieldCheck className="h-5 w-5" />
                </div>
                <div>
                  <h3 className="text-base font-semibold text-foreground">
                    Audit Log Trace #{selectedLogId}
                  </h3>
                  <p className="text-xs text-muted-foreground">
                    Deterministic pipeline verification, telemetry, and evidence ground truth.
                  </p>
                </div>
              </div>
              <button
                onClick={handleCloseDetail}
                className="rounded-md p-1.5 text-muted-foreground hover:bg-muted hover:text-foreground"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {/* Modal Body */}
            <div className="flex-1 overflow-y-auto p-6 space-y-6">
              {detailLoading || !detailData ? (
                <div className="flex flex-col items-center justify-center py-16 text-muted-foreground">
                  <RefreshCw className="h-8 w-8 animate-spin text-primary" />
                  <p className="mt-3 text-sm">Fetching audit detail and execution steps...</p>
                </div>
              ) : (
                <>
                  {/* Meta Overview Bar */}
                  <div className="grid grid-cols-2 gap-3 rounded-lg border border-border/60 bg-muted/30 p-4 sm:grid-cols-4 text-xs">
                    <div>
                      <span className="text-muted-foreground">Model & Prompt</span>
                      <p className="font-semibold text-foreground mt-0.5">
                        {detailData.model || 'gemini-2.5-flash'} ({detailData.prompt_version || 'v1.2.0'})
                      </p>
                    </div>
                    <div>
                      <span className="text-muted-foreground">Data Version</span>
                      <p className="font-semibold text-foreground mt-0.5">
                        v{detailData.data_version !== null ? detailData.data_version : '1'}
                      </p>
                    </div>
                    <div>
                      <span className="text-muted-foreground">Tokens & Calls</span>
                      <p className="font-semibold text-foreground mt-0.5">
                        {detailData.cache_hit ? '0 (Cache Hit)' : `${(detailData.input_tokens || 0) + (detailData.output_tokens || 0)} tokens (${detailData.gemini_calls} calls)`}
                      </p>
                    </div>
                    <div>
                      <span className="text-muted-foreground">Latency</span>
                      <p className="font-semibold text-foreground mt-0.5">
                        {detailData.response_time_ms} ms
                      </p>
                    </div>
                  </div>

                  {/* Question & Safe Cache Key */}
                  <div className="space-y-3">
                    <div>
                      <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                        User Question
                      </label>
                      <div className="mt-1 rounded-md border border-border bg-background p-3 text-sm font-medium text-foreground">
                        {detailData.question}
                      </div>
                    </div>

                    {detailData.cache_key && (
                      <div>
                        <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                          Deterministic Cache Key (SHA-256)
                        </label>
                        <div className="mt-1 flex items-center gap-2 rounded-md border border-border/80 bg-muted/40 px-3 py-2 text-xs font-mono text-muted-foreground truncate">
                          <Code2 className="h-3.5 w-3.5 shrink-0 text-primary" />
                          <span className="truncate">{detailData.cache_key}</span>
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Execution Steps Timeline */}
                  <div>
                    <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                      Execution Step Timeline
                    </label>
                    <div className="mt-2 space-y-2">
                      {detailData.parsed_execution_steps && detailData.parsed_execution_steps.length > 0 ? (
                        detailData.parsed_execution_steps.map((step, idx) => (
                          <div
                            key={idx}
                            className="flex items-start gap-3 rounded-lg border border-border/50 bg-background p-3 text-xs"
                          >
                            <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-primary/10 font-bold text-primary">
                              {idx + 1}
                            </div>
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center justify-between">
                                <span className="font-semibold capitalize text-foreground">
                                  {step.step ? step.step.replace(/_/g, ' ') : `Step ${idx + 1}`}
                                </span>
                                {step.status && (
                                  <Badge
                                    variant={step.status === 'success' ? 'default' : 'secondary'}
                                    className="text-[10px]"
                                  >
                                    {step.status}
                                  </Badge>
                                )}
                              </div>
                              {step.details && (
                                <p className="mt-1 text-muted-foreground whitespace-pre-wrap font-mono text-[11px]">
                                  {typeof step.details === 'object'
                                    ? JSON.stringify(step.details, null, 2)
                                    : String(step.details)}
                                </p>
                              )}
                            </div>
                          </div>
                        ))
                      ) : (
                        <p className="text-xs text-muted-foreground">No execution step trace recorded.</p>
                      )}
                    </div>
                  </div>

                  {/* Evidence Payload (Deterministic Data Source) */}
                  {detailData.parsed_evidence && (
                    <div>
                      <div className="flex items-center justify-between">
                        <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                          Grounded Evidence (Authoritative Python / SQLite Engine)
                        </label>
                        <Badge variant="outline" className="text-[10px] text-emerald-600 border-emerald-500/30">
                          Source of Truth
                        </Badge>
                      </div>
                      <div className="mt-2 max-h-56 overflow-y-auto rounded-lg border border-border bg-muted/40 p-3 font-mono text-xs text-foreground">
                        <pre>{JSON.stringify(detailData.parsed_evidence, null, 2)}</pre>
                      </div>
                    </div>
                  )}

                  {/* Copilot Response Answer */}
                  {detailData.copilot_response && (
                    <div>
                      <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                        Grounded Copilot Response
                      </label>
                      <div className="mt-2 rounded-lg border border-border bg-background p-4 text-sm text-foreground leading-relaxed">
                        {detailData.copilot_response}
                      </div>
                    </div>
                  )}

                  {/* Fallback Reason / Error Trace if present */}
                  {detailData.fallback_reason && (
                    <div className="rounded-lg border border-amber-500/30 bg-amber-500/10 p-4 text-xs text-amber-800 dark:text-amber-200">
                      <div className="flex items-center gap-2 font-semibold">
                        <AlertTriangle className="h-4 w-4 text-amber-600" />
                        Fallback Note
                      </div>
                      <p className="mt-1">{detailData.fallback_reason}</p>
                    </div>
                  )}
                </>
              )}
            </div>

            {/* Modal Footer */}
            <div className="flex items-center justify-end border-t border-border px-6 py-3">
              <Button variant="outline" size="sm" onClick={handleCloseDetail}>
                Close
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default AuditTrail;
