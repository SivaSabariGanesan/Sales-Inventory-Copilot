import React from 'react';
import PageContainer from '@/components/layout/PageContainer';
import { Bot } from 'lucide-react';

export function CopilotPage() {
  return (
    <PageContainer
      title="Retail Copilot"
      subtitle="AI-assisted retail insights, anomaly detection, and operational recommendations."
    >
      <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
        <div className="flex items-center gap-3 text-muted-foreground">
          <Bot className="h-5 w-5 text-secondary" />
          <span className="text-sm font-medium">Copilot intelligence interface placeholder</span>
        </div>
      </div>
    </PageContainer>
  );
}

export default CopilotPage;
