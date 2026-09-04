import React from 'react';
import PageHeader from '@/components/common/PageHeader';
import SectionHeader from '@/components/common/SectionHeader';
import EmptyState from '@/components/common/EmptyState';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  LayoutDashboard,
  AlertTriangle,
  TrendingUp,
  Package,
  Activity,
  ArrowUpRight,
} from 'lucide-react';

export function Dashboard() {
  return (
    <div className="mx-auto w-full max-w-7xl px-4 py-6 sm:px-6 lg:px-8 space-y-6 sm:space-y-8">
      {/* Page Header */}
      <PageHeader
        title="Executive Overview"
        description="Consolidated retail metrics, operational flags, and inventory health."
        badge={<Badge variant="muted">Live Workspace</Badge>}
      />

      {/* Overview Metric Shells */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {[
          { title: 'Total Revenue', icon: TrendingUp },
          { title: 'Units Sold', icon: ArrowUpRight },
          { title: 'Stock Valuation', icon: Package },
          { title: 'Inventory Turn Rate', icon: Activity },
        ].map((item, idx) => (
          <Card key={idx} className="bg-card transition-shadow hover:shadow-sm">
            <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
              <CardTitle className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                {item.title}
              </CardTitle>
              <item.icon className="h-4 w-4 text-muted-foreground" aria-hidden="true" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold tracking-tight text-muted-foreground/40">—</div>
              <p className="mt-1 text-xs text-muted-foreground">
                Awaiting transaction stream
              </p>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Attention / Action Flags Area */}
      <div className="space-y-3">
        <SectionHeader
          title="Operational Attention"
          description="Immediate inventory deficits, stockouts, or anomalies requiring review."
        />
        <EmptyState
          icon={AlertTriangle}
          title="No operational alerts detected"
          description="Stockout warnings, reorder suggestions, and margin flags will appear here."
        />
      </div>

      {/* Sales & Inventory Split Overview */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Sales Overview Area */}
        <div className="space-y-3">
          <SectionHeader
            title="Sales Performance"
            description="Revenue trends across active retail channels."
          />
          <Card>
            <CardContent className="p-4">
              <EmptyState
                icon={TrendingUp}
                title="Sales analytics disconnected"
                description="Analytics will appear here once sales data is connected."
              />
            </CardContent>
          </Card>
        </div>

        {/* Inventory Overview Area */}
        <div className="space-y-3">
          <SectionHeader
            title="Inventory Distribution"
            description="Current stock allocation across warehouses and stores."
          />
          <Card>
            <CardContent className="p-4">
              <EmptyState
                icon={Package}
                title="Inventory data pending"
                description="Stock levels and reorder alerts will display once inventory data is ingested."
              />
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Recent Activity Area */}
      <div className="space-y-3">
        <SectionHeader
          title="Recent System Activity"
          description="Audit trail of catalog syncs, order batches, and copilot triggers."
        />
        <Card>
          <CardContent className="p-4">
            <EmptyState
              icon={Activity}
              title="No recent activity logged"
              description="System events and sync activities will be recorded here."
            />
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

export default Dashboard;
