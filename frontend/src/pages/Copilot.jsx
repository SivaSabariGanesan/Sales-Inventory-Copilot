import React from 'react';
import PageHeader from '@/components/common/PageHeader';
import EmptyState from '@/components/common/EmptyState';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Bot, Send, Sparkles, HelpCircle, ArrowRight } from 'lucide-react';

export function Copilot() {
  return (
    <div className="mx-auto flex h-[calc(100vh-4rem)] max-w-7xl flex-col px-4 py-6 sm:px-6 lg:px-8">
      {/* Page Header */}
      <PageHeader
        title="Retail Copilot Intelligence"
        description="Conversational decision support for sales trajectory, reorder forecasting, and retail diagnostics."
        badge={<Badge variant="secondary">Gemini Ready</Badge>}
      />

      {/* Main Conversation / Workspace Area */}
      <div className="flex flex-1 flex-col overflow-hidden rounded-lg border border-border bg-card shadow-xs">
        {/* Workspace Conversation Canvas */}
        <div className="flex flex-1 flex-col items-center justify-center p-6 overflow-y-auto">
          <div className="max-w-md w-full space-y-4 text-center">
            <EmptyState
              icon={Bot}
              title="Retail Copilot Workspace"
              description="Ask questions about your sales and inventory data."
              className="border-0 bg-transparent py-6"
            />

            {/* Suggested Prompt Wireframes */}
            <div className="space-y-2 text-left">
              <div className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
                Suggested exploration topics:
              </div>
              <div className="grid gap-2 text-xs">
                {[
                  'Which SKUs have highest stockout risk this month?',
                  'Compare weekly sales velocity across regional stores',
                  'Identify top margin contributors in summer inventory',
                ].map((prompt, idx) => (
                  <div
                    key={idx}
                    className="flex items-center justify-between rounded-md border border-border bg-muted/30 px-3 py-2 text-muted-foreground"
                  >
                    <span className="truncate">{prompt}</span>
                    <ArrowRight className="h-3.5 w-3.5 shrink-0 text-muted-foreground/60" />
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Inert Message Input Bar */}
        <div className="border-t border-border bg-muted/20 p-4">
          <div className="mx-auto flex max-w-3xl items-center gap-2">
            <div className="relative flex-1">
              <Input
                type="text"
                placeholder="Ask Retail Copilot (e.g., analyze low stock items or sales trends)..."
                className="h-11 pl-4 pr-10 text-sm bg-background"
                disabled
              />
            </div>
            <Button size="icon" className="h-11 w-11 shrink-0" disabled>
              <Send className="h-4 w-4" />
            </Button>
          </div>
          <div className="mt-2 text-center text-[11px] text-muted-foreground">
            Copilot responds based on active inventory, transactions, and store telemetry.
          </div>
        </div>
      </div>
    </div>
  );
}

export default Copilot;
