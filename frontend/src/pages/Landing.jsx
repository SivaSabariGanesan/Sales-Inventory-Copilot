import React from 'react';
import { Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent } from '@/components/ui/card';
import {
  Sparkles,
  ShieldCheck,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  Package,
  Layers,
  Building2,
  Bot,
  Zap,
  ArrowRight,
  Database,
  BarChart3,
  Cpu,
  CheckCircle2,
  Lock,
  Boxes,
  MapPin,
  ExternalLink,
} from 'lucide-react';

export function Landing() {
  const features = [
    {
      icon: AlertTriangle,
      iconColor: 'text-rose-500 bg-rose-500/10 border-rose-500/20',
      title: 'Stock-Out Risk Detection',
      badge: 'Feature 1',
      description:
        'Deterministic calculation of runout horizons based on 14-day sales velocity and replenishment lead times. Automatically flags High and Medium urgency risks with exact days of stock remaining.',
      link: '/inventory',
      stats: '6 High Urgency Risks Identified',
    },
    {
      icon: Package,
      iconColor: 'text-amber-500 bg-amber-500/10 border-amber-500/20',
      title: 'Overstock & Slow-Moving Detection',
      badge: 'Feature 2',
      description:
        'Identifies excess inventory holding and dead capital. Computes carrying cost at risk and days of holding beyond the 45-day threshold to recommend inventory rebalancing.',
      link: '/inventory',
      stats: '15 Overstocked SKUs Monitored',
    },
    {
      icon: TrendingUp,
      iconColor: 'text-blue-500 bg-blue-500/10 border-blue-500/20',
      title: 'Sales Velocity Anomalies',
      badge: 'Feature 3',
      description:
        'Detects sudden sales spikes (+50%) and demand drops (-40%) by contrasting 7-day velocity against 30-day baseline sales per store SKU.',
      link: '/sales',
      stats: 'Real-time Demand Volatility',
    },
    {
      icon: Bot,
      iconColor: 'text-indigo-500 bg-indigo-500/10 border-indigo-500/20',
      title: 'Gemini Natural-Language Copilot',
      badge: 'Feature 4',
      description:
        'Ask questions in plain English. Powered by Google Gemini 2.5 Flash for natural-language intent classification and explanation, strictly grounded in deterministic SQLite metrics.',
      link: '/copilot',
      stats: '100% Evidence Grounded',
    },
    {
      icon: Zap,
      iconColor: 'text-emerald-500 bg-emerald-500/10 border-emerald-500/20',
      title: 'Action Recommendations',
      badge: 'Feature 5',
      description:
        'Automated operational playbooks ranking daily decisions (Replenish, Markdown, Rebalance, Promote, Hold) with priority scoring and quantified business evidence.',
      link: '/dashboard',
      stats: 'Today’s Attention Queue',
    },
    {
      icon: ShieldCheck,
      iconColor: 'text-purple-500 bg-purple-500/10 border-purple-500/20',
      title: 'Safe Refusal & Human Escalation',
      badge: 'Feature 6',
      description:
        'Zero hallucination guarantee. Ambiguous or unsupported questions trigger safe refusals with explicit recommendations for human manager review.',
      link: '/copilot',
      stats: 'Zero Fabrication Guarantee',
    },
  ];

  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col selection:bg-primary/20 selection:text-primary">
      {/* Navigation Bar */}
      <header className="sticky top-0 z-50 w-full border-b border-border/80 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary text-primary-foreground shadow-sm">
              <Boxes className="h-5 w-5" />
            </div>
            <div>
              <span className="font-bold text-base tracking-tight text-foreground">Retail Copilot</span>
              <span className="hidden sm:inline-block ml-2 text-xs font-mono px-1.5 py-0.5 rounded bg-muted text-muted-foreground border border-border">
                Track PS6
              </span>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <Link to="/dashboard">
              <Button size="sm" className="h-9 px-4 text-xs font-medium gap-1.5 shadow-sm">
                Launch Executive App
                <ArrowRight className="h-3.5 w-3.5" />
              </Button>
            </Link>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="relative overflow-hidden pt-12 pb-16 md:pt-20 md:pb-24 border-b border-border/40">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 relative z-10">
          <div className="flex flex-col items-center text-center max-w-3xl mx-auto space-y-6">
            <div className="inline-flex items-center gap-2 rounded-full border border-primary/20 bg-primary/10 px-3.5 py-1 text-xs font-medium text-primary">
              <Sparkles className="h-3.5 w-3.5" />
              <span>Deterministic Analytics + Grounded Gemini AI</span>
            </div>

            <h1 className="text-4xl sm:text-5xl md:text-6xl font-extrabold tracking-tight text-foreground leading-[1.15]">
              Intelligent Sales & Inventory Decision Support
            </h1>

            <p className="text-base sm:text-lg text-muted-foreground leading-relaxed max-w-2xl">
              An enterprise retail decision-support platform designed to eliminate stock-outs, reduce holding costs of slow-moving inventory, detect velocity anomalies, and deliver evidence-grounded AI intelligence.
            </p>

            {/* CTA Group */}
            <div className="flex flex-wrap items-center justify-center gap-3 pt-2">
              <Link to="/dashboard">
                <Button size="lg" className="h-11 px-6 text-sm font-semibold gap-2 shadow-md">
                  <BarChart3 className="h-4 w-4" />
                  Open Executive Dashboard
                </Button>
              </Link>
              <Link to="/copilot">
                <Button size="lg" variant="outline" className="h-11 px-6 text-sm font-semibold gap-2 border-border">
                  <Bot className="h-4 w-4 text-primary" />
                  Query AI Copilot
                </Button>
              </Link>
            </div>

            {/* Quick Metrics Ticker */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 w-full pt-8 border-t border-border/60">
              <div className="p-3 rounded-lg bg-card/60 border border-border/60">
                <div className="text-2xl font-bold text-foreground">4</div>
                <div className="text-xs text-muted-foreground font-medium">Chennai Outlets</div>
              </div>
              <div className="p-3 rounded-lg bg-card/60 border border-border/60">
                <div className="text-2xl font-bold text-foreground">90</div>
                <div className="text-xs text-muted-foreground font-medium">Tracked SKUs</div>
              </div>
              <div className="p-3 rounded-lg bg-card/60 border border-border/60">
                <div className="text-2xl font-bold text-foreground">39,943</div>
                <div className="text-xs text-muted-foreground font-medium">Sales Records</div>
              </div>
              <div className="p-3 rounded-lg bg-card/60 border border-border/60">
                <div className="text-2xl font-bold text-emerald-600 dark:text-emerald-400">100%</div>
                <div className="text-xs text-muted-foreground font-medium">Grounding Accuracy</div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Architecture Highlights Section */}
      <section className="py-14 bg-muted/20 border-b border-border/60">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-2xl mx-auto mb-12 space-y-2">
            <h2 className="text-2xl sm:text-3xl font-bold tracking-tight text-foreground">
              Deterministic 3-Tier Architecture
            </h2>
            <p className="text-sm text-muted-foreground">
              Mathematical guarantees backed by SQLite and Python. AI only synthesizes verified evidence.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <Card className="bg-card shadow-xs border-border relative overflow-hidden">
              <div className="p-6 space-y-4">
                <div className="h-10 w-10 rounded-lg bg-blue-500/10 text-blue-600 dark:text-blue-400 flex items-center justify-center">
                  <Database className="h-5 w-5" />
                </div>
                <h3 className="text-lg font-semibold text-foreground">1. Deterministic Data Layer</h3>
                <p className="text-xs text-muted-foreground leading-relaxed">
                  Pure SQLite relational schema maintaining real-time transaction records across stores, inventory levels, catalog definitions, and historical demand.
                </p>
              </div>
            </Card>

            <Card className="bg-card shadow-xs border-border relative overflow-hidden">
              <div className="p-6 space-y-4">
                <div className="h-10 w-10 rounded-lg bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 flex items-center justify-center">
                  <Cpu className="h-5 w-5" />
                </div>
                <h3 className="text-lg font-semibold text-foreground">2. Python Analytics Engine</h3>
                <p className="text-xs text-muted-foreground leading-relaxed">
                  Mathematical computation of runout horizons, excess stock carrying cost, rolling baseline velocity, and priority scoring without LLM hallucinations.
                </p>
              </div>
            </Card>

            <Card className="bg-card shadow-xs border-border relative overflow-hidden">
              <div className="p-6 space-y-4">
                <div className="h-10 w-10 rounded-lg bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 flex items-center justify-center">
                  <Sparkles className="h-5 w-5" />
                </div>
                <h3 className="text-lg font-semibold text-foreground">3. Gemini 2.5 Flash NLG</h3>
                <p className="text-xs text-muted-foreground leading-relaxed">
                  Natural language understanding maps manager inquiries to analytics queries, explaining evidence numbers clearly and refusing unsupported questions safely.
                </p>
              </div>
            </Card>
          </div>
        </div>
      </section>

      {/* Feature Showcase Grid */}
      <section className="py-16">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-2xl mx-auto mb-12 space-y-2">
            <h2 className="text-2xl sm:text-3xl font-bold tracking-tight text-foreground">
              Full Spectrum Decision Intelligence
            </h2>
            <p className="text-sm text-muted-foreground">
              Every feature is built for retail store managers to solve real-world operational challenges.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {features.map((feat, idx) => (
              <Card key={idx} className="bg-card shadow-xs border-border flex flex-col justify-between hover:shadow-md transition-shadow">
                <CardContent className="p-6 space-y-4">
                  <div className="flex items-center justify-between">
                    <div className={`p-2.5 rounded-lg border ${feat.iconColor}`}>
                      <feat.icon className="h-5 w-5" />
                    </div>
                    <Badge variant="outline" className="text-[11px] font-mono">
                      {feat.badge}
                    </Badge>
                  </div>
                  <div>
                    <h3 className="text-base font-semibold text-foreground mb-1.5">{feat.title}</h3>
                    <p className="text-xs text-muted-foreground leading-relaxed">{feat.description}</p>
                  </div>
                </CardContent>
                <div className="border-t border-border/60 px-6 py-3 bg-muted/20 flex items-center justify-between text-xs">
                  <span className="font-mono text-muted-foreground">{feat.stats}</span>
                  <Link to={feat.link} className="font-medium text-primary hover:underline inline-flex items-center gap-1">
                    Explore <ArrowRight className="h-3 w-3" />
                  </Link>
                </div>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="mt-auto border-t border-border bg-card py-8 text-xs text-muted-foreground">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <Boxes className="h-4 w-4 text-primary" />
            <span className="font-semibold text-foreground">Retail Sales & Inventory Copilot</span>
            <span className="text-muted-foreground">• Track PS6</span>
          </div>
          <div className="flex items-center gap-6">
            <Link to="/dashboard" className="hover:text-foreground transition-colors">Dashboard</Link>
            <Link to="/inventory" className="hover:text-foreground transition-colors">Inventory</Link>
            <Link to="/sales" className="hover:text-foreground transition-colors">Sales</Link>
            <Link to="/copilot" className="hover:text-foreground transition-colors">Copilot</Link>
            <Link to="/settings" className="hover:text-foreground transition-colors">Settings</Link>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default Landing;
