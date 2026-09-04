import React from 'react';
import PageContainer from '@/components/layout/PageContainer';
import { Settings } from 'lucide-react';

export function SettingsPage() {
  return (
    <PageContainer
      title="System Settings"
      subtitle="Application configuration, threshold parameters, and system preferences."
    >
      <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
        <div className="flex items-center gap-3 text-muted-foreground">
          <Settings className="h-5 w-5 text-primary" />
          <span className="text-sm font-medium">Settings module placeholder</span>
        </div>
      </div>
    </PageContainer>
  );
}

export default SettingsPage;
