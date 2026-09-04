import React, { useState, useEffect } from 'react';
import PageHeader from '@/components/common/PageHeader';
import SectionHeader from '@/components/common/SectionHeader';
import { Card, CardContent } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  fetchGeminiSettings,
  saveGeminiSettings,
  testGeminiConnection,
} from '@/services/settings';
import {
  CheckCircle2,
  AlertCircle,
  Sparkles,
  Key,
  ShieldCheck,
  RefreshCw,
  Eye,
  EyeOff,
  Zap,
} from 'lucide-react';

export function Settings() {
  const [settingsData, setSettingsData] = useState({
    configured: false,
    masked_key: null,
    model: 'gemini-2.5-flash',
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Form State (transient only during entry)
  const [inputKey, setInputKey] = useState('');
  const [showKey, setShowKey] = useState(false);
  const [saving, setSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  // Test Connection State
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState(null);

  const loadSettings = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchGeminiSettings();
      setSettingsData(data);
    } catch (err) {
      setError(err.message || 'Unable to connect to backend settings service.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSettings();
  }, []);

  const handleSave = async (e) => {
    e.preventDefault();
    if (!inputKey || inputKey.trim().length < 5) {
      setError('Please enter a valid Gemini API key (minimum 5 characters).');
      return;
    }

    setSaving(true);
    setError(null);
    setSaveSuccess(false);
    setTestResult(null);

    try {
      const updated = await saveGeminiSettings({ apiKey: inputKey.trim() });
      setSettingsData(updated);
      setInputKey(''); // Clear raw key from form state immediately after save
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 5000);
    } catch (err) {
      setError(err.message || 'Failed to update Gemini API key.');
    } finally {
      setSaving(false);
    }
  };

  const handleTestConnection = async () => {
    setTesting(true);
    setTestResult(null);
    setError(null);

    try {
      const res = await testGeminiConnection();
      setTestResult(res);
    } catch (err) {
      setTestResult({
        success: false,
        message: err.message || 'Connection test failed. Unable to reach backend.',
      });
    } finally {
      setTesting(false);
    }
  };

  return (
    <div className="mx-auto w-full max-w-4xl px-4 py-6 sm:px-6 lg:px-8 space-y-6 sm:space-y-8">
      {/* Page Header */}
      <PageHeader
        title="System Settings"
        description="Workspace preferences, AI configuration, and security controls."
        badge={<Badge variant="outline" className="font-mono text-xs">Production Edition</Badge>}
      />

      {/* Backend / Global Error Banner */}
      {error && (
        <div className="flex items-center justify-between rounded-lg border border-red-500/20 bg-red-500/10 p-4 text-sm text-red-700 dark:text-red-400">
          <div className="flex items-center gap-2">
            <AlertCircle className="h-5 w-5 flex-shrink-0" />
            <span>{error}</span>
          </div>
          <Button variant="outline" size="sm" onClick={loadSettings} className="text-xs">
            Retry
          </Button>
        </div>
      )}

      {/* AI Configuration Section */}
      <div className="space-y-4">
        <SectionHeader
          title="AI Configuration"
          description="Manage Google Gemini API connectivity and intelligence parameters used by the Copilot."
        />

        <Card className="bg-card shadow-xs border-border">
          <CardContent className="p-4 sm:p-6 space-y-6">
            {/* Header & Status Indicator */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-border">
              <div className="flex items-center gap-3">
                <div className="p-2.5 rounded-lg bg-primary/10 text-primary">
                  <Sparkles className="h-5 w-5" />
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-foreground">Gemini API Key</h3>
                  <p className="text-xs text-muted-foreground">
                    Configure the Gemini API key used by the Copilot.
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-2">
                {settingsData.configured ? (
                  <Badge variant="secondary" className="gap-1.5 font-medium text-emerald-600 dark:text-emerald-400 bg-emerald-500/10 border-emerald-500/20">
                    <CheckCircle2 className="h-3.5 w-3.5" />
                    Key Configured
                  </Badge>
                ) : (
                  <Badge variant="outline" className="gap-1.5 font-medium text-amber-600 dark:text-amber-400 bg-amber-500/10 border-amber-500/20">
                    <AlertCircle className="h-3.5 w-3.5" />
                    No Key Configured
                  </Badge>
                )}
              </div>
            </div>

            {/* Currently Active Masked Key */}
            {settingsData.configured && (
              <div className="rounded-lg bg-muted/40 p-3.5 border border-border/80 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  <Key className="h-4 w-4 text-muted-foreground" />
                  <span className="text-xs text-muted-foreground font-medium">Active Server Key:</span>
                  <code className="rounded bg-background px-2.5 py-1 font-mono text-xs font-semibold text-foreground border border-border">
                    {settingsData.masked_key || '••••••••••••••••'}
                  </code>
                </div>
                <span className="text-[11px] font-mono text-muted-foreground">
                  Model: {settingsData.model}
                </span>
              </div>
            )}

            {/* Key Input & Save Form */}
            <form onSubmit={handleSave} className="space-y-4">
              <div className="space-y-1.5">
                <label htmlFor="gemini-key-input" className="text-xs font-semibold text-foreground">
                  {settingsData.configured ? 'Update API Key' : 'Enter Gemini API Key'}
                </label>
                <div className="relative flex items-center">
                  <Input
                    id="gemini-key-input"
                    type={showKey ? 'text' : 'password'}
                    placeholder={settingsData.configured ? 'Paste new Gemini API key to update...' : 'AIzaSy... or AQ.Ab8...'}
                    value={inputKey}
                    onChange={(e) => setInputKey(e.target.value)}
                    disabled={saving || loading}
                    className="pr-10 font-mono text-sm bg-background"
                  />
                  <button
                    type="button"
                    onClick={() => setShowKey(!showKey)}
                    className="absolute right-3 text-muted-foreground hover:text-foreground transition-colors"
                    tabIndex={-1}
                  >
                    {showKey ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
              </div>

              {saveSuccess && (
                <div className="flex items-center gap-2 rounded-md bg-emerald-500/10 border border-emerald-500/20 p-2.5 text-xs text-emerald-600 dark:text-emerald-400">
                  <CheckCircle2 className="h-4 w-4 flex-shrink-0" />
                  <span>Gemini API key saved securely on server!</span>
                </div>
              )}

              {/* Action Buttons */}
              <div className="flex flex-wrap items-center justify-between gap-3 pt-2">
                <div className="flex items-center gap-2">
                  <Button
                    type="submit"
                    disabled={saving || !inputKey.trim()}
                    className="h-9 px-4 text-xs font-medium gap-1.5"
                  >
                    {saving && <RefreshCw className="h-3.5 w-3.5 animate-spin" />}
                    Save Key
                  </Button>

                  <Button
                    type="button"
                    variant="outline"
                    onClick={handleTestConnection}
                    disabled={testing || !settingsData.configured}
                    className="h-9 px-4 text-xs font-medium gap-1.5"
                  >
                    <Zap className={`h-3.5 w-3.5 ${testing ? 'animate-pulse text-primary' : ''}`} />
                    {testing ? 'Testing...' : 'Test Connection'}
                  </Button>
                </div>

                {/* Test Connection Result Indicator */}
                {testResult && (
                  <div className="flex items-center gap-2">
                    {testResult.success ? (
                      <Badge className="bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border border-emerald-500/30 gap-1.5 py-1 px-3 text-xs font-medium">
                        <CheckCircle2 className="h-3.5 w-3.5" />
                        Connected
                      </Badge>
                    ) : (
                      <Badge variant="destructive" className="gap-1.5 py-1 px-3 text-xs font-medium">
                        <AlertCircle className="h-3.5 w-3.5" />
                        Connection failed
                      </Badge>
                    )}
                  </div>
                )}
              </div>

              {/* Extended Connection Error Message if failed */}
              {testResult && !testResult.success && (
                <p className="text-xs text-red-600 dark:text-red-400 bg-red-500/10 p-2.5 rounded-md border border-red-500/20">
                  {testResult.message}
                </p>
              )}
            </form>

            {/* Security Guarantee Note */}
            <div className="flex items-start gap-2.5 rounded-lg bg-blue-500/5 border border-blue-500/15 p-3 text-xs text-muted-foreground">
              <ShieldCheck className="h-4 w-4 text-blue-600 dark:text-blue-400 flex-shrink-0 mt-0.5" />
              <span>
                Your API key is stored securely on the server and is never exposed to the browser. All natural-language queries are evaluated with strict evidence grounding.
              </span>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* General Settings */}
      <div className="space-y-4">
        <SectionHeader
          title="General Configuration"
          description="Workspace identity, default currency, and operational timezone."
        />
        <Card className="bg-card shadow-xs">
          <CardContent className="p-4 sm:p-6 space-y-4">
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div className="space-y-1.5">
                <label htmlFor="settings-workspace" className="text-xs font-semibold text-foreground">
                  Workspace Name
                </label>
                <Input
                  id="settings-workspace"
                  defaultValue="Retail Copilot - Main"
                  disabled
                  className="bg-muted/30"
                />
              </div>
              <div className="space-y-1.5">
                <label htmlFor="settings-currency" className="text-xs font-semibold text-foreground">
                  Default Currency
                </label>
                <Input
                  id="settings-currency"
                  defaultValue="USD ($)"
                  disabled
                  className="bg-muted/30"
                />
              </div>
              <div className="space-y-1.5">
                <label htmlFor="settings-tz" className="text-xs font-semibold text-foreground">
                  Timezone
                </label>
                <Input
                  id="settings-tz"
                  defaultValue="UTC (Coordinated Universal Time)"
                  disabled
                  className="bg-muted/30"
                />
              </div>
              <div className="space-y-1.5">
                <label htmlFor="settings-method" className="text-xs font-semibold text-foreground">
                  Inventory Analytics Engine
                </label>
                <Input
                  id="settings-method"
                  defaultValue="Deterministic SQLite + Gemini 2.5 Flash"
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
        <Card className="bg-card shadow-xs">
          <CardContent className="p-4 sm:p-6 space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm font-semibold text-foreground">Color Scheme</div>
                <div className="text-xs text-muted-foreground">
                  Enterprise Slate & Navy (Default)
                </div>
              </div>
              <Badge variant="secondary" className="gap-1 font-semibold">
                <CheckCircle2 className="h-3 w-3" aria-hidden="true" />
                Active Theme
              </Badge>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

export default Settings;
