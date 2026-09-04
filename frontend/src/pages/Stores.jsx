import React, { useState, useEffect } from 'react';
import PageHeader from '@/components/common/PageHeader';
import SectionHeader from '@/components/common/SectionHeader';
import EmptyState from '@/components/common/EmptyState';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { fetchStores } from '@/services/stores';
import {
  Building2,
  MapPin,
  Package,
  Boxes,
  Search,
  RefreshCw,
  AlertCircle,
  CheckCircle2,
} from 'lucide-react';

export function Stores() {
  const [storesData, setStoresData] = useState({
    kpis: {
      total_locations: 0,
      regions_covered: 0,
      total_skus_stocked: 0,
      total_inventory_units: 0,
    },
    stores: [],
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');

  const loadStores = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchStores({ search: searchTerm });
      setStoresData(data);
    } catch (err) {
      setError(err.message || 'Unable to load store network from database.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadStores();
  }, []);

  const handleSearchKeyDown = (e) => {
    if (e.key === 'Enter') {
      loadStores();
    }
  };

  const { kpis, stores } = storesData;

  return (
    <div className="mx-auto w-full max-w-7xl px-4 py-6 sm:px-6 lg:px-8 space-y-6 sm:space-y-8">
      {/* Page Header */}
      <PageHeader
        title="Store Network"
        description="Physical retail outlets, regional distribution nodes, and multi-location inventory holdings."
        badge={
          <Badge variant="outline" className="font-mono bg-primary/10 text-primary border-primary/20">
            {loading ? '...' : `${kpis.total_locations} Active Stores`}
          </Badge>
        }
        actions={
          <Button
            variant="outline"
            size="sm"
            onClick={loadStores}
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
          <Button variant="outline" size="sm" onClick={loadStores} className="text-xs">
            Try Again
          </Button>
        </div>
      )}

      {/* Store Overview Metric Cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {[
          {
            title: 'Total Locations',
            value: loading ? '—' : kpis.total_locations,
            subtext: `${kpis.total_locations} active retail outlets`,
            icon: Building2,
            iconClass: 'text-blue-600 dark:text-blue-400 bg-blue-500/10',
          },
          {
            title: 'Regions Covered',
            value: loading ? '—' : kpis.regions_covered,
            subtext: 'Metropolitan trading zones',
            icon: MapPin,
            iconClass: 'text-emerald-600 dark:text-emerald-400 bg-emerald-500/10',
          },
          {
            title: 'SKUs Stocked',
            value: loading ? '—' : kpis.total_skus_stocked,
            subtext: 'Catalog products distributed',
            icon: Package,
            iconClass: 'text-indigo-600 dark:text-indigo-400 bg-indigo-500/10',
          },
          {
            title: 'Inventory Units',
            value: loading ? '—' : kpis.total_inventory_units.toLocaleString(),
            subtext: 'Total units held across network',
            icon: Boxes,
            iconClass: 'text-amber-600 dark:text-amber-400 bg-amber-500/10',
          },
        ].map((item, idx) => (
          <Card key={idx} className="bg-card shadow-xs">
            <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
              <CardTitle className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                {item.title}
              </CardTitle>
              <div className={`p-2 rounded-lg ${item.iconClass}`}>
                <item.icon className="h-4 w-4" aria-hidden="true" />
              </div>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold tracking-tight text-foreground">{item.value}</div>
              <p className="mt-1 text-xs text-muted-foreground">{item.subtext}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Store Directory Section */}
      <div className="space-y-4">
        <SectionHeader
          title="Locations Directory"
          description="Detailed register of retail locations, store codes, cities, and live inventory allocations."
        />

        {/* Search & Filter Toolbar */}
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 rounded-lg border border-border bg-card p-3 shadow-xs">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <input
              type="text"
              placeholder="Search stores by name, city, or store code..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              onKeyDown={handleSearchKeyDown}
              className="w-full rounded-md border border-input bg-background pl-9 pr-4 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-primary"
            />
          </div>

          <Button size="sm" onClick={loadStores} className="h-9 px-4 text-xs">
            Search
          </Button>
        </div>

        {/* Store Table */}
        <div className="overflow-hidden rounded-lg border border-border bg-card shadow-xs">
          <div className="overflow-x-auto">
            <table className="w-full min-w-[640px] text-left text-sm" role="table">
              <thead className="border-b border-border bg-muted/40 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                <tr>
                  <th scope="col" className="px-4 py-3">Store Code</th>
                  <th scope="col" className="px-4 py-3">Store Name</th>
                  <th scope="col" className="px-4 py-3">City / Region</th>
                  <th scope="col" className="px-4 py-3 text-right">SKUs Carried</th>
                  <th scope="col" className="px-4 py-3 text-right">Physical Units</th>
                  <th scope="col" className="px-4 py-3 text-center">Operating Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border/60">
                {loading ? (
                  <tr>
                    <td colSpan={6} className="py-12 text-center text-muted-foreground">
                      <div className="flex flex-col items-center justify-center gap-2">
                        <RefreshCw className="h-6 w-6 animate-spin text-primary" />
                        <p className="text-xs">Loading store network from database...</p>
                      </div>
                    </td>
                  </tr>
                ) : stores.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="p-0">
                      <EmptyState
                        icon={Building2}
                        title="No store locations found"
                        description={
                          searchTerm
                            ? 'No stores matched your search query. Try clearing the search term.'
                            : 'No store locations configured in the database.'
                        }
                        className="border-0 rounded-none bg-transparent py-12"
                      />
                    </td>
                  </tr>
                ) : (
                  stores.map((store) => (
                    <tr key={store.id} className="hover:bg-muted/30 transition-colors">
                      <td className="px-4 py-3.5">
                        <code className="rounded bg-muted px-2 py-0.5 font-mono text-xs font-semibold text-foreground">
                          {store.store_code}
                        </code>
                      </td>
                      <td className="px-4 py-3.5">
                        <div className="font-semibold text-foreground">{store.store_name}</div>
                        <div className="text-[11px] text-muted-foreground">Store ID: #{store.id}</div>
                      </td>
                      <td className="px-4 py-3.5">
                        <div className="flex items-center gap-1.5 text-xs text-foreground">
                          <MapPin className="h-3.5 w-3.5 text-muted-foreground" />
                          <span>{store.city}</span>
                        </div>
                      </td>
                      <td className="px-4 py-3.5 text-right font-mono font-medium text-foreground">
                        {store.total_skus || 0} SKUs
                      </td>
                      <td className="px-4 py-3.5 text-right font-mono font-semibold text-foreground">
                        {(store.total_inventory_units || 0).toLocaleString()} units
                      </td>
                      <td className="px-4 py-3.5 text-center">
                        <span className="inline-flex items-center gap-1 rounded-full bg-emerald-500/10 px-2.5 py-0.5 text-xs font-medium text-emerald-600 dark:text-emerald-400">
                          <CheckCircle2 className="h-3 w-3" />
                          {store.status}
                        </span>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
          {!loading && stores.length > 0 && (
            <div className="border-t border-border bg-muted/20 px-4 py-2.5 text-xs text-muted-foreground flex items-center justify-between">
              <span>Showing {stores.length} of {kpis.total_locations} retail locations</span>
              <span>Network Active</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default Stores;
