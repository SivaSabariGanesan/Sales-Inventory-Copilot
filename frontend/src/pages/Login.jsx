import React from 'react';
import { NavLink } from 'react-router-dom';
import { Layers, ShieldCheck, Lock, ArrowLeft } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import GoogleLoginButton from '@/components/auth/GoogleLoginButton';
import { useAuth } from '@/hooks/useAuth';

export function Login() {
  const { isOAuthConfigured, isLoading } = useAuth();

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-background px-4 py-12 sm:px-6 lg:px-8">
      <div className="w-full max-w-md space-y-8">
        {/* Brand Header */}
        <div className="text-center space-y-2">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-lg bg-primary text-primary-foreground shadow-sm">
            <Layers className="h-6 w-6" aria-hidden="true" />
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground">
            Retail Copilot
          </h1>
          <p className="text-sm text-muted-foreground">
            Enterprise Decision Support for Sales & Inventory Operations
          </p>
        </div>

        {/* Login Authentication Card */}
        <Card className="border-border bg-card shadow-sm">
          <CardHeader className="space-y-1 text-center pb-4">
            <CardTitle className="text-base font-semibold text-foreground">
              Sign in to your workspace
            </CardTitle>
            <CardDescription className="text-xs text-muted-foreground">
              Authenticate via enterprise single sign-on to access store networks and inventory telemetry.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6 pt-0">
            {/* Google OAuth Button Container */}
            <div className="pt-2">
              <GoogleLoginButton
                disabled={isLoading}
                oauthConfigured={isOAuthConfigured}
              />
            </div>

            {/* Architecture Info & Dev Navigation */}
            <div className="rounded-md border border-border bg-muted/30 p-3 text-xs space-y-2">
              <div className="flex items-center gap-1.5 font-semibold text-foreground">
                <Lock className="h-3.5 w-3.5 text-primary" aria-hidden="true" />
                <span>Enterprise Authentication Ready</span>
              </div>
              <p className="text-muted-foreground text-[11px] leading-relaxed">
                Authentication structure is configured. When OAuth credentials are provided, sessions are securely verified against the retail database.
              </p>
            </div>

            <div className="text-center pt-2">
              <NavLink to="/">
                <Button variant="ghost" size="sm" className="gap-1.5 text-xs text-muted-foreground hover:text-foreground">
                  <ArrowLeft className="h-3.5 w-3.5" />
                  Return to Workspace
                </Button>
              </NavLink>
            </div>
          </CardContent>
        </Card>

        {/* Security & Compliance Footer */}
        <div className="flex items-center justify-center gap-2 text-xs text-muted-foreground">
          <ShieldCheck className="h-4 w-4 text-emerald-600" aria-hidden="true" />
          <span>Track PS6 • Zero external tracking</span>
        </div>
      </div>
    </div>
  );
}

export default Login;
