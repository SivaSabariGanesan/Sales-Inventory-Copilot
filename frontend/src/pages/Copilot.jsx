import React, { useState, useRef, useEffect } from 'react';
import PageHeader from '@/components/common/PageHeader';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { queryCopilot } from '@/services/copilot';
import {
  Bot,
  User,
  Send,
  Sparkles,
  AlertTriangle,
  CheckCircle2,
  HelpCircle,
  Clock,
  Database,
  ArrowRight,
  RefreshCw,
  Trash2,
  TrendingUp,
  TrendingDown,
  Layers,
  Info,
} from 'lucide-react';

const SUGGESTED_QUESTIONS = [
  'Which products are at risk of running out?',
  'What inventory is overstocked?',
  'Which products had sales spikes?',
  'Which products had sales drops?',
  'What needs my attention today?',
];

export function Copilot() {
  const [messages, setMessages] = useState([]);
  const [inputQuestion, setInputQuestion] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const chatBottomRef = useRef(null);

  const scrollToBottom = () => {
    chatBottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const handleAsk = async (questionToAsk) => {
    const q = (questionToAsk || inputQuestion).trim();
    if (!q || loading) return;

    setInputQuestion('');
    setError(null);
    setLoading(true);

    const userMessage = {
      id: Date.now(),
      sender: 'user',
      text: q,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMessage]);

    try {
      const response = await queryCopilot(q);
      const botMessage = {
        id: Date.now() + 1,
        sender: 'copilot',
        data: response,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages((prev) => [...prev, botMessage]);
    } catch (err) {
      setError(err.message || 'Failed to get answer from Copilot.');
      const errorMessage = {
        id: Date.now() + 1,
        sender: 'copilot',
        isError: true,
        text: err.message || 'Copilot could not process the request. Please try again.',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleAsk();
    }
  };

  const clearChat = () => {
    setMessages([]);
    setError(null);
  };

  const getIntentBadge = (intent, confidence) => {
    let variant = 'secondary';
    if (intent === 'STOCKOUT_RISK') variant = 'destructive';
    else if (intent === 'OVERSTOCK') variant = 'default';
    else if (intent === 'SALES_SPIKE') variant = 'outline';

    return (
      <div className="flex items-center gap-1.5">
        <Badge variant={variant} className="text-[11px] font-mono uppercase tracking-wide">
          {intent.replace('_', ' ')}
        </Badge>
        {confidence !== undefined && (
          <span className="text-[10px] text-muted-foreground font-mono">
            ({Math.round(confidence * 100)}% match)
          </span>
        )}
      </div>
    );
  };

  return (
    <div className="mx-auto flex min-h-[calc(100vh-4rem)] max-w-7xl flex-col px-4 py-6 sm:px-6 lg:px-8 space-y-4">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
        <PageHeader
          title="Retail Copilot"
          description="Ask natural-language questions about sales trends, inventory risks, and store performance."
          badge={<Badge variant="default" className="bg-primary/90 flex items-center gap-1"><Sparkles className="h-3 w-3" /> Grounded Intelligence</Badge>}
        />
        {messages.length > 0 && (
          <Button
            variant="outline"
            size="sm"
            onClick={clearChat}
            className="self-start sm:self-auto gap-1.5 text-xs text-muted-foreground hover:text-foreground"
          >
            <Trash2 className="h-3.5 w-3.5" />
            Clear Conversation
          </Button>
        )}
      </div>

      {/* Main Chat Workspace */}
      <Card className="flex flex-1 flex-col overflow-hidden shadow-sm border border-border min-h-[500px]">
        {/* Messages Scroll Area */}
        <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-6">
          {messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full py-12 text-center max-w-xl mx-auto space-y-6">
              <div className="h-14 w-14 rounded-full bg-primary/10 flex items-center justify-center text-primary shadow-xs">
                <Bot className="h-7 w-7" />
              </div>
              <div className="space-y-1.5">
                <h3 className="text-lg font-semibold text-foreground">
                  Ask Retail Copilot
                </h3>
                <p className="text-sm text-muted-foreground leading-relaxed">
                  Query stock-out risks, overstocked items, sales anomalies, or specific store performance backed by deterministic SQLite metrics.
                </p>
              </div>

              {/* Suggested Questions */}
              <div className="w-full space-y-2 text-left pt-2">
                <div className="text-[11px] font-bold uppercase tracking-wider text-muted-foreground px-1">
                  Suggested Questions:
                </div>
                <div className="grid grid-cols-1 gap-2">
                  {SUGGESTED_QUESTIONS.map((prompt, idx) => (
                    <button
                      key={idx}
                      type="button"
                      onClick={() => handleAsk(prompt)}
                      className="flex items-center justify-between rounded-lg border border-border/80 bg-muted/30 px-3.5 py-2.5 text-xs text-foreground font-medium transition-colors hover:bg-accent hover:text-accent-foreground text-left group"
                    >
                      <span className="pr-2">{prompt}</span>
                      <ArrowRight className="h-3.5 w-3.5 text-muted-foreground group-hover:text-primary transition-transform group-hover:translate-x-0.5 shrink-0" />
                    </button>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            messages.map((msg) => (
              <div
                key={msg.id}
                className={`flex gap-3 max-w-4xl ${
                  msg.sender === 'user' ? 'ml-auto justify-end' : 'mr-auto justify-start'
                }`}
              >
                {msg.sender === 'copilot' && (
                  <div className="h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center text-primary shrink-0 mt-1">
                    <Bot className="h-4 w-4" />
                  </div>
                )}

                <div className={`space-y-3 ${msg.sender === 'user' ? 'max-w-xl' : 'w-full'}`}>
                  {/* User Bubble */}
                  {msg.sender === 'user' ? (
                    <div className="rounded-2xl rounded-tr-xs bg-primary px-4 py-2.5 text-sm text-primary-foreground shadow-xs">
                      {msg.text}
                    </div>
                  ) : msg.isError ? (
                    /* Error Bubble */
                    <div className="rounded-xl border border-destructive/30 bg-destructive/5 p-4 text-sm text-destructive space-y-1">
                      <div className="font-semibold flex items-center gap-1.5">
                        <AlertTriangle className="h-4 w-4" /> Error
                      </div>
                      <p>{msg.text}</p>
                    </div>
                  ) : (
                    /* Copilot Grounded Answer Card */
                    <div className="rounded-xl border border-border bg-card p-5 shadow-xs space-y-4">
                      {/* Intent & Confidence Header */}
                      <div className="flex flex-wrap items-center justify-between gap-2 border-b pb-3">
                        <div className="flex items-center gap-2">
                          <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                            Detected Intent:
                          </span>
                          {getIntentBadge(msg.data.intent, msg.data.confidence)}
                        </div>
                        <span className="text-[11px] text-muted-foreground">
                          {msg.timestamp}
                        </span>
                      </div>

                      {/* Natural Language Grounded Answer */}
                      <div className="text-sm text-foreground leading-relaxed whitespace-pre-line font-normal">
                        {msg.data.answer}
                      </div>

                      {/* Human Review Alert if needed */}
                      {msg.data.needs_human_review && (
                        <div className="rounded-md border border-amber-500/30 bg-amber-500/10 p-3 text-xs text-amber-900 dark:text-amber-200 flex items-start gap-2">
                          <AlertTriangle className="h-4 w-4 text-amber-600 shrink-0 mt-0.5" />
                          <div>
                            <span className="font-semibold block">Manager Review Recommended</span>
                            This request involves ambiguous criteria or limited historical data. Please verify against underlying telemetry.
                          </div>
                        </div>
                      )}

                      {/* Actionable Insights */}
                      {msg.data.insights && msg.data.insights.length > 0 && (
                        <div className="space-y-1.5 pt-1">
                          <div className="text-xs font-semibold text-muted-foreground uppercase tracking-wider flex items-center gap-1.5">
                            <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600" />
                            Key Observations & Numbers
                          </div>
                          <ul className="grid grid-cols-1 gap-1 pl-4 text-xs text-foreground list-disc marker:text-primary">
                            {msg.data.insights.map((insight, i) => (
                              <li key={i}>{insight}</li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {/* Structured Evidence Cards / Table */}
                      {msg.data.evidence && msg.data.evidence.length > 0 && (
                        <div className="space-y-2 pt-2 border-t">
                          <div className="text-xs font-semibold text-muted-foreground uppercase tracking-wider flex items-center gap-1.5">
                            <Database className="h-3.5 w-3.5 text-primary" />
                            Grounded Evidence ({msg.data.evidence.length} records)
                          </div>
                          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                            {msg.data.evidence.map((item, i) => (
                              <div
                                key={i}
                                className="rounded-md border border-border/80 bg-muted/20 p-3 space-y-1 text-xs"
                              >
                                <div className="flex items-center justify-between gap-1">
                                  <span className="font-semibold text-foreground truncate">
                                    {item.product}
                                  </span>
                                  <Badge variant="outline" className="text-[10px] shrink-0 font-mono">
                                    {item.status}
                                  </Badge>
                                </div>
                                <div className="text-muted-foreground text-[11px] font-mono">
                                  {item.store} {item.sku ? `· ${item.sku}` : ''}
                                </div>
                                <div className="flex items-center justify-between pt-1 border-t text-[11px]">
                                  <span className="text-muted-foreground">{item.metric_label}:</span>
                                  <span className="font-semibold text-foreground font-mono">
                                    {item.metric_value}
                                  </span>
                                </div>
                                {item.details && (
                                  <div className="text-[11px] text-muted-foreground italic">
                                    {item.details}
                                  </div>
                                )}
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Assumptions & Calculation Windows */}
                      {msg.data.assumptions && msg.data.assumptions.length > 0 && (
                        <div className="rounded-md bg-muted/40 p-2.5 text-[11px] text-muted-foreground flex items-center gap-2">
                          <Clock className="h-3.5 w-3.5 shrink-0" />
                          <span>{msg.data.assumptions.join(' ')}</span>
                        </div>
                      )}

                      {/* Limitations */}
                      {msg.data.limitations && msg.data.limitations.length > 0 && (
                        <div className="text-[11px] text-muted-foreground/80 flex items-center gap-1.5">
                          <Info className="h-3.5 w-3.5 shrink-0" />
                          <span>Limitations: {msg.data.limitations.join(', ')}</span>
                        </div>
                      )}
                    </div>
                  )}
                </div>

                {msg.sender === 'user' && (
                  <div className="h-8 w-8 rounded-full bg-muted flex items-center justify-center text-muted-foreground shrink-0 mt-1">
                    <User className="h-4 w-4" />
                  </div>
                )}
              </div>
            ))
          )}

          {/* Loading Indicator */}
          {loading && (
            <div className="flex gap-3 max-w-4xl mr-auto justify-start">
              <div className="h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center text-primary shrink-0">
                <Bot className="h-4 w-4" />
              </div>
              <div className="rounded-xl border border-border bg-card p-4 shadow-xs flex items-center gap-3 text-sm text-muted-foreground">
                <RefreshCw className="h-4 w-4 animate-spin text-primary" />
                <span>Analyzing your retail data and synthesizing deterministic evidence...</span>
              </div>
            </div>
          )}

          <div ref={chatBottomRef} />
        </div>

        {/* Input Bar */}
        <div className="border-t border-border bg-card/80 backdrop-blur-xs p-3 sm:p-4">
          <div className="mx-auto flex max-w-3xl items-center gap-2">
            <div className="relative flex-1">
              <label htmlFor="copilot-input" className="sr-only">
                Ask Retail Copilot
              </label>
              <Input
                id="copilot-input"
                type="text"
                placeholder="Ask about your sales or inventory (e.g. Which products are at risk of running out?)..."
                value={inputQuestion}
                onChange={(e) => setInputQuestion(e.target.value)}
                onKeyDown={handleKeyDown}
                disabled={loading}
                className="h-11 pl-4 pr-10 text-sm bg-background"
              />
            </div>
            <Button
              onClick={() => handleAsk()}
              disabled={loading || !inputQuestion.trim()}
              className="h-11 px-4 gap-2 shrink-0 font-medium"
            >
              <Send className="h-4 w-4" />
              <span className="hidden sm:inline">Ask Copilot</span>
            </Button>
          </div>
          <div className="mt-2 text-center text-[11px] text-muted-foreground">
            Copilot maps questions to deterministic SQLite analytics. Numbers are never fabricated.
          </div>
        </div>
      </Card>
    </div>
  );
}

export default Copilot;
