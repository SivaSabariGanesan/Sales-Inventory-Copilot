import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from '@/hooks/useAuth';
import AppShell from '@/components/layout/AppShell';
import Dashboard from '@/pages/Dashboard';
import Copilot from '@/pages/Copilot';
import Inventory from '@/pages/Inventory';
import Sales from '@/pages/Sales';
import Products from '@/pages/Products';
import Stores from '@/pages/Stores';
import Settings from '@/pages/Settings';
import Login from '@/pages/Login';

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          {/* Public Authentication Route */}
          <Route path="/login" element={<Login />} />

          {/* Application Workspace Routes */}
          <Route element={<AppShell />}>
            <Route path="/" element={<Dashboard />} />
            <Route path="/copilot" element={<Copilot />} />
            <Route path="/inventory" element={<Inventory />} />
            <Route path="/sales" element={<Sales />} />
            <Route path="/products" element={<Products />} />
            <Route path="/stores" element={<Stores />} />
            <Route path="/settings" element={<Settings />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
