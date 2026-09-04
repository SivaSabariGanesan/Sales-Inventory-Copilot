import React, { useState, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import PageHeader from '@/components/common/PageHeader';
import SectionHeader from '@/components/common/SectionHeader';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  fetchImportStatus,
  previewSingleCsv,
  previewAllCsv,
  importSingleDataset,
  importAllCombined,
  getTemplateUrl,
  resetToDemoData,
} from '@/services/dataImport';
import {
  Upload,
  FileSpreadsheet,
  CheckCircle2,
  AlertCircle,
  AlertTriangle,
  RefreshCw,
  Download,
  Database,
  Layers,
  Building2,
  Tag,
  TrendingUp,
  Package,
  RotateCcw,
  ArrowRight,
  HelpCircle,
  Eye,
  X,
  FileText,
  Boxes,
} from 'lucide-react';

export function DataImport() {
  const [status, setStatus] = useState({
    stores_count: 0,
    products_count: 0,
    sales_count: 0,
    inventory_count: 0,
  });
  const [activeTab, setActiveTab] = useState('method-a'); // 'method-a' or 'method-b'
  const [globalError, setGlobalError] = useState(null);
  const [globalSuccess, setGlobalSuccess] = useState(null);
  const [resetting, setResetting] = useState(false);
  const [showResetModal, setShowResetModal] = useState(false);

  // Method A State (per dataset card)
  const [methodAState, setMethodAState] = useState({
    products: { file: null, preview: null, loading: false, importing: false, success: null, error: null },
    stores: { file: null, preview: null, loading: false, importing: false, success: null, error: null },
    sales: { file: null, preview: null, loading: false, importing: false, success: null, error: null },
    inventory: { file: null, preview: null, loading: false, importing: false, success: null, error: null },
  });

  // Method B State (all.csv)
  const [allCsvFile, setAllCsvFile] = useState(null);
  const [allPreview, setAllPreview] = useState(null);
  const [allLoading, setAllLoading] = useState(false);
  const [allImporting, setAllImporting] = useState(false);
  const [allSuccess, setAllSuccess] = useState(null);
  const [allError, setAllError] = useState(null);

  // Preview Modal State
  const [modalPreview, setModalPreview] = useState(null);

  const loadStatus = async () => {
    try {
      const data = await fetchImportStatus();
      setStatus(data);
    } catch (err) {
      console.error('Failed to load database status:', err);
    }
  };

  useEffect(() => {
    loadStatus();
  }, []);

  // Method A Handlers
  const handleFileSelect = (datasetType, e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setMethodAState((prev) => ({
      ...prev,
      [datasetType]: {
        ...prev[datasetType],
        file,
        preview: null,
        error: null,
        success: null,
      },
    }));
  };

  const handleValidateSingle = async (datasetType) => {
    const state = methodAState[datasetType];
    if (!state.file) return;

    setMethodAState((prev) => ({
      ...prev,
      [datasetType]: { ...prev[datasetType], loading: true, error: null },
    }));

    try {
      const preview = await previewSingleCsv(state.file, datasetType);
      setMethodAState((prev) => ({
        ...prev,
        [datasetType]: {
          ...prev[datasetType],
          loading: false,
          preview,
          error: preview.valid ? null : `Validation found ${preview.errors.length} issue(s).`,
        },
      }));
    } catch (err) {
      setMethodAState((prev) => ({
        ...prev,
        [datasetType]: { ...prev[datasetType], loading: false, error: err.message },
      }));
    }
  };

  const handleImportSingle = async (datasetType) => {
    const state = methodAState[datasetType];
    if (!state.file) return;

    setMethodAState((prev) => ({
      ...prev,
      [datasetType]: { ...prev[datasetType], importing: true, error: null, success: null },
    }));

    try {
      const result = await importSingleDataset(state.file, datasetType);
      setMethodAState((prev) => ({
        ...prev,
        [datasetType]: {
          ...prev[datasetType],
          importing: false,
          success: result.message,
          file: null,
          preview: null,
        },
      }));
      loadStatus();
    } catch (err) {
      setMethodAState((prev) => ({
        ...prev,
        [datasetType]: { ...prev[datasetType], importing: false, error: err.message },
      }));
    }
  };

  // Method B Handlers
  const handleAllFileSelect = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setAllCsvFile(file);
    setAllPreview(null);
    setAllError(null);
    setAllSuccess(null);
  };

  const handleValidateAll = async () => {
    if (!allCsvFile) return;
    setAllLoading(true);
    setAllError(null);
    setAllSuccess(null);

    try {
      const preview = await previewAllCsv(allCsvFile);
      setAllPreview(preview);
      if (!preview.valid) {
        setAllError(`Validation failed with ${preview.errors.length} issue(s). Review errors below.`);
      }
    } catch (err) {
      setAllError(err.message);
    } finally {
      setAllLoading(false);
    }
  };

  const handleImportAll = async () => {
    if (!allCsvFile) return;
    setAllImporting(true);
    setAllError(null);

    try {
      const result = await importAllCombined(allCsvFile);
      setAllSuccess(result);
      setAllCsvFile(null);
      setAllPreview(null);
      loadStatus();
    } catch (err) {
      setAllError(err.message);
    } finally {
      setAllImporting(false);
    }
  };

  // Reset to Demo Data
  const handleResetDemo = async () => {
    setResetting(true);
    setGlobalError(null);
    setShowResetModal(false);

    try {
      const res = await resetToDemoData();
      setGlobalSuccess(res.message);
      loadStatus();
      setTimeout(() => setGlobalSuccess(null), 6000);
    } catch (err) {
      setGlobalError(err.message || 'Failed to reset demo dataset.');
    } finally {
      setResetting(false);
    }
  };

  const separateCards = [
    {
      id: 'products',
      name: 'Products Catalog',
      icon: Tag,
      iconColor: 'text-blue-600 dark:text-blue-400 bg-blue-500/10',
      description: 'Import master merchandise, SKUs, category classifications, and pricing margins.',
      template: 'products',
      columns: 'sku, product_name, category, unit_price, reorder_level',
    },
    {
      id: 'stores',
      name: 'Store Network',
      icon: Building2,
      iconColor: 'text-indigo-600 dark:text-indigo-400 bg-indigo-500/10',
      description: 'Import physical retail locations, store codes, and regional operating outlets.',
      template: 'stores',
      columns: 'store_code, store_name, city',
    },
    {
      id: 'sales',
      name: 'Sales Transactions',
      icon: TrendingUp,
      iconColor: 'text-emerald-600 dark:text-emerald-400 bg-emerald-500/10',
      description: 'Import historical sales orders with dates, stores, SKUs, quantities, and revenues.',
      template: 'sales',
      columns: 'sale_date, store_code, sku, quantity, unit_price, revenue',
    },
    {
      id: 'inventory',
      name: 'Inventory Stock Levels',
      icon: Package,
      iconColor: 'text-amber-600 dark:text-amber-400 bg-amber-500/10',
      description: 'Import current on-hand unit balances across all physical store locations.',
      template: 'inventory',
      columns: 'store_code, sku, stock_quantity',
    },
  ];

  return (
    <div className="mx-auto w-full max-w-7xl px-4 py-6 sm:px-6 lg:px-8 space-y-6 sm:space-y-8">
      {/* Page Header */}
      <PageHeader
        title="Import Retail Data"
        description="Upload your retail datasets via separate CSV files or one combined all.csv to power inventory forecasting, sales analytics, and Copilot intelligence."
        badge={
          <Badge variant="outline" className="font-mono bg-primary/10 text-primary border-primary/20">
            Database Ingestion Active
          </Badge>
        }
        actions={
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowResetModal(true)}
            disabled={resetting}
            className="h-9 gap-1.5 text-xs font-medium text-muted-foreground hover:text-foreground"
          >
            <RotateCcw className={`h-3.5 w-3.5 ${resetting ? 'animate-spin text-primary' : ''}`} />
            Reset Demo Data
          </Button>
        }
      />

      {/* Global Alerts */}
      {globalSuccess && (
        <div className="flex items-center justify-between rounded-lg border border-emerald-500/20 bg-emerald-500/10 p-4 text-sm text-emerald-700 dark:text-emerald-400">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="h-5 w-5 flex-shrink-0" />
            <span>{globalSuccess}</span>
          </div>
          <Button variant="outline" size="sm" onClick={() => setGlobalSuccess(null)} className="text-xs">
            Dismiss
          </Button>
        </div>
      )}

      {globalError && (
        <div className="flex items-center justify-between rounded-lg border border-red-500/20 bg-red-500/10 p-4 text-sm text-red-700 dark:text-red-400">
          <div className="flex items-center gap-2">
            <AlertCircle className="h-5 w-5 flex-shrink-0" />
            <span>{globalError}</span>
          </div>
          <Button variant="outline" size="sm" onClick={() => setGlobalError(null)} className="text-xs">
            Dismiss
          </Button>
        </div>
      )}

      {/* Database Status Bar */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <Card className="bg-card shadow-xs">
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Active Stores</p>
              <h3 className="text-2xl font-bold tracking-tight text-foreground">{status.stores_count}</h3>
            </div>
            <Building2 className="h-5 w-5 text-muted-foreground" />
          </CardContent>
        </Card>
        <Card className="bg-card shadow-xs">
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Master SKUs</p>
              <h3 className="text-2xl font-bold tracking-tight text-foreground">{status.products_count}</h3>
            </div>
            <Tag className="h-5 w-5 text-muted-foreground" />
          </CardContent>
        </Card>
        <Card className="bg-card shadow-xs">
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Sales Records</p>
              <h3 className="text-2xl font-bold tracking-tight text-foreground">{status.sales_count.toLocaleString()}</h3>
            </div>
            <TrendingUp className="h-5 w-5 text-muted-foreground" />
          </CardContent>
        </Card>
        <Card className="bg-card shadow-xs">
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Inventory SKUs</p>
              <h3 className="text-2xl font-bold tracking-tight text-foreground">{status.inventory_count}</h3>
            </div>
            <Package className="h-5 w-5 text-muted-foreground" />
          </CardContent>
        </Card>
      </div>

      {/* Import Method Tabs */}
      <div className="space-y-4">
        <div className="flex border-b border-border">
          <button
            onClick={() => setActiveTab('method-a')}
            className={`flex items-center gap-2 px-6 py-3 text-sm font-semibold border-b-2 transition-colors ${
              activeTab === 'method-a'
                ? 'border-primary text-primary'
                : 'border-transparent text-muted-foreground hover:text-foreground'
            }`}
          >
            <Layers className="h-4 w-4" />
            Method A — Separate CSV Files
          </button>
          <button
            onClick={() => setActiveTab('method-b')}
            className={`flex items-center gap-2 px-6 py-3 text-sm font-semibold border-b-2 transition-colors ${
              activeTab === 'method-b'
                ? 'border-primary text-primary'
                : 'border-transparent text-muted-foreground hover:text-foreground'
            }`}
          >
            <FileSpreadsheet className="h-4 w-4" />
            Method B — One Combined all.csv
          </button>
        </div>

        {/* METHOD A: SEPARATE CSV UPLOADS */}
        {activeTab === 'method-a' && (
          <div className="space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
              <SectionHeader
                title="Separate Dataset Uploads"
                description="Upload Products and Stores before Sales and Inventory records so relational references resolve seamlessly."
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {separateCards.map((card) => {
                const state = methodAState[card.id];
                return (
                  <Card key={card.id} className="bg-card shadow-xs border-border flex flex-col justify-between">
                    <CardHeader className="pb-3">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <div className={`p-2.5 rounded-lg ${card.iconColor}`}>
                            <card.icon className="h-5 w-5" />
                          </div>
                          <div>
                            <CardTitle className="text-base font-semibold">{card.name}</CardTitle>
                            <span className="text-[11px] font-mono text-muted-foreground">{card.columns}</span>
                          </div>
                        </div>
                        <a
                          href={getTemplateUrl(card.template)}
                          download
                          className="inline-flex items-center gap-1 text-xs text-primary hover:underline font-medium"
                          title="Download Starter Template"
                        >
                          <Download className="h-3.5 w-3.5" />
                          Template
                        </a>
                      </div>
                      <p className="text-xs text-muted-foreground mt-2">{card.description}</p>
                    </CardHeader>

                    <CardContent className="space-y-4 pt-2">
                      {/* File Selection Box */}
                      <div className="rounded-lg border-2 border-dashed border-border p-4 text-center hover:bg-muted/20 transition-colors">
                        <input
                          type="file"
                          accept=".csv,text/csv"
                          id={`file-input-${card.id}`}
                          className="hidden"
                          onChange={(e) => handleFileSelect(card.id, e)}
                        />
                        <label
                          htmlFor={`file-input-${card.id}`}
                          className="cursor-pointer flex flex-col items-center justify-center gap-1.5"
                        >
                          <Upload className="h-6 w-6 text-muted-foreground" />
                          <span className="text-xs font-semibold text-foreground">
                            {state.file ? state.file.name : `Choose ${card.name} CSV`}
                          </span>
                          <span className="text-[11px] text-muted-foreground">
                            {state.file ? `${(state.file.size / 1024).toFixed(1)} KB` : 'Click to browse file'}
                          </span>
                        </label>
                      </div>

                      {/* Success / Error Banners */}
                      {state.success && (
                        <div className="rounded-md bg-emerald-500/10 border border-emerald-500/20 p-2.5 text-xs text-emerald-600 dark:text-emerald-400 flex items-center gap-2">
                          <CheckCircle2 className="h-4 w-4 flex-shrink-0" />
                          <span>{state.success}</span>
                        </div>
                      )}

                      {state.error && (
                        <div className="rounded-md bg-red-500/10 border border-red-500/20 p-2.5 text-xs text-red-600 dark:text-red-400 flex items-center gap-2">
                          <AlertCircle className="h-4 w-4 flex-shrink-0" />
                          <span className="truncate">{state.error}</span>
                        </div>
                      )}

                      {/* Preview Summary */}
                      {state.preview && (
                        <div className="rounded-lg bg-muted/40 p-3 border border-border space-y-2 text-xs">
                          <div className="flex items-center justify-between">
                            <span className="font-semibold text-foreground">
                              {state.preview.total_rows} row(s) detected
                            </span>
                            {state.preview.valid ? (
                              <Badge className="bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border border-emerald-500/30 text-[10px]">
                                Ready to Import
                              </Badge>
                            ) : (
                              <Badge variant="destructive" className="text-[10px]">
                                {state.preview.errors.length} Error(s)
                              </Badge>
                            )}
                          </div>

                          <div className="flex items-center gap-2 pt-1">
                            <Button
                              type="button"
                              variant="ghost"
                              size="sm"
                              onClick={() => setModalPreview(state.preview)}
                              className="h-7 text-xs px-2 gap-1 text-muted-foreground hover:text-foreground"
                            >
                              <Eye className="h-3.5 w-3.5" />
                              View Preview Table
                            </Button>
                          </div>
                        </div>
                      )}

                      {/* Action Buttons */}
                      <div className="flex items-center justify-between gap-2 pt-2 border-t border-border">
                        <Button
                          type="button"
                          variant="outline"
                          size="sm"
                          onClick={() => handleValidateSingle(card.id)}
                          disabled={!state.file || state.loading || state.importing}
                          className="h-8 text-xs font-medium gap-1.5"
                        >
                          {state.loading && <RefreshCw className="h-3 w-3 animate-spin" />}
                          Validate & Preview
                        </Button>

                        <Button
                          type="button"
                          size="sm"
                          onClick={() => handleImportSingle(card.id)}
                          disabled={!state.preview || !state.preview.valid || state.importing}
                          className="h-8 text-xs font-medium gap-1.5"
                        >
                          {state.importing && <RefreshCw className="h-3 w-3 animate-spin" />}
                          Import {card.name.split(' ')[0]}
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          </div>
        )}

        {/* METHOD B: COMBINED ALL.CSV */}
        {activeTab === 'method-b' && (
          <div className="space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
              <SectionHeader
                title="Single Combined all.csv Ingestion"
                description="Upload all four datasets (Products, Stores, Sales, Inventory) in a single file using the data_type column."
              />
              <a
                href={getTemplateUrl('all')}
                download
                className="inline-flex items-center gap-1.5 text-xs text-primary font-semibold hover:underline"
              >
                <Download className="h-4 w-4" />
                Download all.csv Template
              </a>
            </div>

            <Card className="bg-card shadow-xs border-border">
              <CardContent className="p-6 space-y-6">
                {/* Drag and Drop Zone */}
                <div className="rounded-xl border-2 border-dashed border-border p-8 text-center hover:bg-muted/20 transition-colors">
                  <input
                    type="file"
                    accept=".csv,text/csv"
                    id="all-file-input"
                    className="hidden"
                    onChange={handleAllFileSelect}
                  />
                  <label htmlFor="all-file-input" className="cursor-pointer flex flex-col items-center justify-center gap-2">
                    <FileSpreadsheet className="h-10 w-10 text-primary/80" />
                    <div>
                      <span className="text-sm font-semibold text-foreground">
                        {allCsvFile ? allCsvFile.name : 'Choose all.csv combined file'}
                      </span>
                      <p className="text-xs text-muted-foreground mt-0.5">
                        {allCsvFile
                          ? `${(allCsvFile.size / 1024).toFixed(1)} KB selected`
                          : 'Supports product, store, sale, and inventory rows'}
                      </p>
                    </div>
                  </label>
                </div>

                {/* Validation / Error Banners */}
                {allError && (
                  <div className="rounded-lg bg-red-500/10 border border-red-500/20 p-4 text-xs text-red-600 dark:text-red-400 space-y-2">
                    <div className="flex items-center gap-2 font-semibold">
                      <AlertCircle className="h-4 w-4 flex-shrink-0" />
                      <span>{allError}</span>
                    </div>
                    {allPreview && allPreview.errors.length > 0 && (
                      <ul className="list-disc list-inside space-y-1 pl-1 text-[11px]">
                        {allPreview.errors.slice(0, 5).map((err, idx) => (
                          <li key={idx}>
                            Row {err.row_number}: {err.message}
                          </li>
                        ))}
                        {allPreview.errors.length > 5 && (
                          <li className="font-semibold text-muted-foreground">
                            ... and {allPreview.errors.length - 5} more issues.
                          </li>
                        )}
                      </ul>
                    )}
                  </div>
                )}

                {allSuccess && (
                  <div className="rounded-lg bg-emerald-500/10 border border-emerald-500/20 p-5 text-emerald-700 dark:text-emerald-400 space-y-3">
                    <div className="flex items-center gap-2 font-bold text-sm">
                      <CheckCircle2 className="h-5 w-5 flex-shrink-0" />
                      <span>Data Import Complete</span>
                    </div>
                    <p className="text-xs">{allSuccess.message}</p>
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-1 font-mono text-xs">
                      <div className="bg-card/80 p-2 rounded border border-border">
                        ✓ {allSuccess.imported_counts.products || 0} Products
                      </div>
                      <div className="bg-card/80 p-2 rounded border border-border">
                        ✓ {allSuccess.imported_counts.stores || 0} Stores
                      </div>
                      <div className="bg-card/80 p-2 rounded border border-border">
                        ✓ {allSuccess.imported_counts.sales || 0} Sales Records
                      </div>
                      <div className="bg-card/80 p-2 rounded border border-border">
                        ✓ {allSuccess.imported_counts.inventory || 0} Inventory SKUs
                      </div>
                    </div>
                    <div className="pt-2 flex items-center gap-3">
                      <Link to="/">
                        <Button size="sm" className="h-8 text-xs font-semibold gap-1">
                          View Dashboard <ArrowRight className="h-3.5 w-3.5" />
                        </Button>
                      </Link>
                    </div>
                  </div>
                )}

                {/* Detected Datasets Breakdown */}
                {allPreview && (
                  <div className="space-y-4 pt-2">
                    <div className="flex items-center justify-between">
                      <h4 className="text-sm font-semibold text-foreground">
                        Batch Summary ({allPreview.total_rows} total rows)
                      </h4>
                      {allPreview.valid ? (
                        <Badge className="bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border border-emerald-500/30 gap-1">
                          <CheckCircle2 className="h-3.5 w-3.5" /> Validation Successful
                        </Badge>
                      ) : (
                        <Badge variant="destructive" className="gap-1">
                          <AlertCircle className="h-3.5 w-3.5" /> Validation Issues Found
                        </Badge>
                      )}
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
                      {Object.entries(allPreview.datasets).map(([type, p]) => (
                        <div key={type} className="rounded-lg border border-border bg-muted/20 p-3.5 space-y-1.5">
                          <div className="flex items-center justify-between">
                            <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                              {type}
                            </span>
                            {p.valid ? (
                              <CheckCircle2 className="h-4 w-4 text-emerald-500" />
                            ) : (
                              <AlertCircle className="h-4 w-4 text-rose-500" />
                            )}
                          </div>
                          <div className="text-xl font-bold text-foreground">{p.total_rows} rows</div>
                          <Button
                            type="button"
                            variant="ghost"
                            size="sm"
                            onClick={() => setModalPreview(p)}
                            className="h-6 text-[11px] px-0 text-primary hover:underline"
                          >
                            Preview {type}
                          </Button>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Actions */}
                <div className="flex items-center justify-between pt-4 border-t border-border">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={handleValidateAll}
                    disabled={!allCsvFile || allLoading || allImporting}
                    className="h-9 px-4 text-xs font-semibold gap-1.5"
                  >
                    {allLoading && <RefreshCw className="h-3.5 w-3.5 animate-spin" />}
                    Validate all.csv
                  </Button>

                  <Button
                    type="button"
                    onClick={handleImportAll}
                    disabled={!allPreview || !allPreview.valid || allImporting}
                    className="h-9 px-5 text-xs font-semibold gap-1.5"
                  >
                    {allImporting && <RefreshCw className="h-3.5 w-3.5 animate-spin" />}
                    Import All Data (Atomic Commit)
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>
        )}
      </div>

      {/* Templates & Guidance Section */}
      <div className="space-y-4 pt-4">
        <SectionHeader
          title="CSV Templates & Guidelines"
          description="Download exact starter templates formatted for seamless validation."
        />

        <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
          {[
            { name: 'Products Template', file: 'products' },
            { name: 'Stores Template', file: 'stores' },
            { name: 'Sales Template', file: 'sales' },
            { name: 'Inventory Template', file: 'inventory' },
            { name: 'All.csv Template', file: 'all' },
          ].map((t) => (
            <a
              key={t.file}
              href={getTemplateUrl(t.file)}
              download
              className="rounded-lg border border-border bg-card p-3 text-center hover:border-primary/50 transition-colors group flex flex-col items-center justify-center gap-1.5 shadow-xs"
            >
              <FileText className="h-5 w-5 text-muted-foreground group-hover:text-primary transition-colors" />
              <span className="text-xs font-medium text-foreground">{t.name}</span>
              <span className="text-[10px] text-muted-foreground font-mono">.csv</span>
            </a>
          ))}
        </div>
      </div>

      {/* Preview Table Modal */}
      {modalPreview && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-xs p-4">
          <div className="w-full max-w-4xl rounded-xl border border-border bg-card shadow-lg flex flex-col max-h-[85vh] overflow-hidden">
            <div className="flex items-center justify-between border-b border-border p-4">
              <div>
                <h3 className="text-sm font-semibold text-foreground uppercase tracking-wide">
                  Preview: {modalPreview.dataset_type} ({modalPreview.total_rows} total rows)
                </h3>
                <p className="text-xs text-muted-foreground">Showing first 5 sample records from {modalPreview.filename}</p>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setModalPreview(null)}
                className="h-8 w-8 p-0 rounded-full"
              >
                <X className="h-4 w-4" />
              </Button>
            </div>

            <div className="p-4 overflow-auto space-y-4">
              {modalPreview.sample_rows.length > 0 ? (
                <div className="overflow-x-auto rounded border border-border">
                  <table className="w-full text-left text-xs">
                    <thead className="border-b border-border bg-muted/40 font-semibold uppercase text-muted-foreground">
                      <tr>
                        {modalPreview.columns.map((c) => (
                          <th key={c} className="p-2.5">{c}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-border">
                      {modalPreview.sample_rows.map((row, rIdx) => (
                        <tr key={rIdx} className="hover:bg-muted/30 font-mono">
                          {modalPreview.columns.map((col) => (
                            <td key={col} className="p-2.5 truncate max-w-[200px]">
                              {row[col] !== undefined ? String(row[col]) : '—'}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <p className="text-xs text-muted-foreground py-4 text-center">No rows parsed in dataset.</p>
              )}

              {/* Error list if any */}
              {modalPreview.errors.length > 0 && (
                <div className="rounded-lg bg-red-500/10 border border-red-500/20 p-3 space-y-1.5">
                  <span className="font-semibold text-xs text-red-600 dark:text-red-400">
                    Validation Errors ({modalPreview.errors.length}):
                  </span>
                  <ul className="list-disc list-inside text-xs text-red-600 dark:text-red-400 space-y-0.5 max-h-36 overflow-y-auto">
                    {modalPreview.errors.map((err, eIdx) => (
                      <li key={eIdx}>
                        Row {err.row_number} ({err.field}): {err.message}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>

            <div className="border-t border-border p-3 flex justify-end bg-muted/20">
              <Button size="sm" variant="outline" onClick={() => setModalPreview(null)} className="text-xs">
                Close Preview
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Confirmation Modal for Reset Demo */}
      {showResetModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-xs p-4">
          <div className="w-full max-w-md rounded-xl border border-border bg-card p-6 shadow-xl space-y-4">
            <div className="flex items-center gap-3 text-amber-600 dark:text-amber-400">
              <AlertTriangle className="h-6 w-6" />
              <h3 className="text-base font-bold text-foreground">Reset to Demo Dataset?</h3>
            </div>
            <p className="text-xs text-muted-foreground leading-relaxed">
              This action will restore the database to the default synthetic seeded dataset (4 stores, 90 products, 39,943 sales transactions, 360 inventory records). Any custom uploaded records will be replaced.
            </p>
            <div className="flex items-center justify-end gap-2 pt-2">
              <Button variant="outline" size="sm" onClick={() => setShowResetModal(false)} className="text-xs">
                Cancel
              </Button>
              <Button size="sm" variant="destructive" onClick={handleResetDemo} className="text-xs">
                Yes, Reset Data
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default DataImport;
