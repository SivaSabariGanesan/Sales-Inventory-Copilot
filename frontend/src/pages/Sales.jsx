import React from 'react';
import PageHeader from '@/components/common/PageHeader';
import SectionHeader from '@/components/common/SectionHeader';
import EmptyState from '@/components/common/EmptyState';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  TrendingUp,
  DollarSign,
  ShoppingCart,
  Percent,
  BarChart3,
  Tag,
  Building2,
} from 'lucide-react';

export function Sales() {
  return (
    <div className="mx-auto w-full max-w-7xl px-4 py-6 sm:px-6 lg:px-8 space-y-6 sm:space-y-8">
      {/* Page Header */}
      <PageHeader
        title="Sales Analytics"
        description="Analyze revenue velocity, basket size, and channel sales distributions."
        badge={<Badge variant="outline">Offline</Badge>}
      />

      {/* Sales KPI Shells */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {[
          { title: 'Gross Revenue', icon: DollarSign },
          { title: 'Total Orders', icon: ShoppingCart },
          { title: 'Avg Order Value', icon: TrendingUp },
          { title: 'Gross Margin %', icon: Percent },
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
                Awaiting transaction dataset
              </p>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Sales Trend Area */}
      <div className="space-y-3">
        <SectionHeader
          title="Revenue & Demand Trajectory"
          description="Historical revenue curves and seasonal trend variations."
        />
        <Card>
          <CardContent className="p-4">
            <EmptyState
              icon={BarChart3}
              title="Sales trend analytics unavailable"
              description="Sales trend curves and seasonality models will populate once transaction data is connected."
            />
          </CardContent>
        </Card>
      </div>

      {/* Product & Store Performance Split */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Product Performance Area */}
        <div className="space-y-3">
          <SectionHeader
            title="Product Performance"
            description="Top grossing items and velocity leaders."
          />
          <Card>
            <CardContent className="p-4">
              <EmptyState
                icon={Tag}
                title="No product sales data"
                description="SKU velocity and product revenue rankings will appear here."
              />
            </CardContent>
          </Card>
        </div>

        {/* Store Performance Area */}
        <div className="space-y-3">
          <SectionHeader
            title="Store Network Breakdown"
            description="Regional revenue contributions and store footfall metrics."
          />
          <Card>
            <CardContent className="p-4">
              <EmptyState
                icon={Building2}
                title="No store sales data"
                description="Comparative store performance and regional sales charts will display once populated."
              />
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

export default Sales;
