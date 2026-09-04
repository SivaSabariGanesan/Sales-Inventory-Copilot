import React from 'react';
import PageHeader from '@/components/common/PageHeader';
import SectionHeader from '@/components/common/SectionHeader';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Settings as SettingsIcon, Sliders, Palette, Info, CheckCircle2 } from 'lucide-react';

export function Settings() {
  return (
    <div className="mx-auto w-full max-w-4xl px-4 py-6 sm:px-6 lg:px-8 space-y-8">
      {/* Page Header */}
      <PageHeader
        title="System Settings"
        description="Workspace preferences, appearance themes, and environment details."
        badge={<Badge variant="outline">Enterprise Edition</Badge>}
      />

      {/* General Settings */}
      <div className="space-y-4">
        <SectionHeader
          title="General Configuration"
          description="Workspace identity, default currency, and operational timezone."
        />
        <Card>
          <CardContent className="p-6 space-y-4">
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-foreground">
                  Workspace Name
                </label>
                <Input
                  defaultValue="Retail Copilot - Main"
                  disabled
                  className="bg-muted/30"
                />
              </div>
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-foreground">
                  Default Currency
                </label>
                <Input
                  defaultValue="USD ($)"
                  disabled
                  className="bg-muted/30"
                />
              </div>
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-foreground">
                  Timezone
                </label>
                <Input
                  defaultValue="UTC (Coordinated Universal Time)"
                  disabled
                  className="bg-muted/30"
                />
              </div>
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-foreground">
                  Inventory Reorder Threshold Method
                </label>
                <Input
                  defaultValue="Dynamic Lead Time (AI Predicted)"
                  disabled
                  className="bg-muted/30"
                />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Appearance Section */}
      <div className="space-y-4">
        <SectionHeader
          title="Appearance & Theme"
          description="Visual styling and density controls."
        />
        <Card>
          <CardContent className="p-6 space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm font-medium text-foreground">Color Scheme</div>
                <div className="text-xs text-muted-foreground">
                  Enterprise Slate & Navy (Default)
                </div>
              </div>
              <Badge variant="secondary" className="gap-1">
                <CheckCircle2 className="h-3 w-3" />
                Active Theme
              </Badge>
            </div>

            <div className="flex items-center justify-between border-t border-border pt-4">
              <div>
                <div className="text-sm font-medium text-foreground">Display Density</div>
                <div className="text-xs text-muted-foreground">
                  Compact / Data-oriented layout
                </div>
              </div>
              <span className="text-xs font-medium text-muted-foreground">Standard</span>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Application Information */}
      <div className="space-y-4">
        <SectionHeader
          title="Application Information"
          description="Build version, environment identifiers, and platform status."
        />
        <Card>
          <CardContent className="p-6">
            <dl className="grid grid-cols-1 gap-x-4 gap-y-3 sm:grid-cols-2 text-xs">
              <div>
                <dt className="text-muted-foreground">Application Name</dt>
                <dd className="font-semibold text-foreground mt-0.5">Retail Sales & Inventory Copilot</dd>
              </div>
              <div>
                <dt className="text-muted-foreground">Track Identifier</dt>
                <dd className="font-semibold text-foreground mt-0.5">PS6</dd>
              </div>
              <div>
                <dt className="text-muted-foreground">Backend Engine</dt>
                <dd className="font-semibold text-foreground mt-0.5">Python 3.11 • FastAPI • Uvicorn</dd>
              </div>
              <div>
                <dt className="text-muted-foreground">Frontend Foundation</dt>
                <dd className="font-semibold text-foreground mt-0.5">React 18 • Vite 5 • Tailwind CSS • shadcn/ui</dd>
              </div>
              <div>
                <dt className="text-muted-foreground">Environment</dt>
                <dd className="font-semibold text-foreground mt-0.5">Production Ready / Local Scaffolding</dd>
              </div>
              <div>
                <dt className="text-muted-foreground">Status</dt>
                <dd className="font-semibold text-emerald-600 mt-0.5">All Systems Operational</dd>
              </div>
            </dl>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

export default Settings;
