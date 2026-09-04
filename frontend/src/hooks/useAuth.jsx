import React, { createContext, useContext, useState, useEffect } from 'react';
import { fetchAuthStatus } from '@/services/auth';

const AuthContext = createContext({
  user: null,
  isAuthenticated: false,
  isOAuthConfigured: false,
  isLoading: true,
  statusMessage: '',
  refreshAuth: async () => {},
});

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isOAuthConfigured, setIsOAuthConfigured] = useState(false);
  const [statusMessage, setStatusMessage] = useState('');
  const [isLoading, setIsLoading] = useState(true);

  const refreshAuth = async () => {
    setIsLoading(true);
    try {
      const data = await fetchAuthStatus();
      setUser(data.user || null);
      setIsAuthenticated(Boolean(data.authenticated));
      setIsOAuthConfigured(Boolean(data.oauth_configured));
      setStatusMessage(data.message || '');
    } catch {
      setIsAuthenticated(false);
      setUser(null);
      setIsOAuthConfigured(false);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    refreshAuth();
  }, []);

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated,
        isOAuthConfigured,
        isLoading,
        statusMessage,
        refreshAuth,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

export default useAuth;
