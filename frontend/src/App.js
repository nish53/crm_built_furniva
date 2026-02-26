import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { Toaster } from './components/ui/sonner';
import { Login } from './pages/Login';
import { Dashboard } from './pages/Dashboard';
import { Orders } from './pages/Orders';
import { OrderDetail } from './pages/OrderDetail';
import { NewOrder } from './pages/NewOrder';
import { WhatsAppCRM } from './pages/WhatsAppCRM';
import { Tasks } from './pages/Tasks';
import { Inventory } from './pages/Inventory';
import { Analytics } from './pages/Analytics';
import { ImportWizard } from './pages/ImportWizard';
import { HistoricalImport } from './pages/HistoricalImport';
import { MasterSKU } from './pages/MasterSKU';
import { Returns } from './pages/Returns';
import { Channels } from './pages/Channels';
import { Costing } from './pages/Costing';
import { Layout } from './components/Layout';
import './App.css';

const PrivateRoute = ({ children }) => {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    );
  }

  return user ? children : <Navigate to="/login" />;
};

const PublicRoute = ({ children }) => {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    );
  }

  return user ? <Navigate to="/dashboard" /> : children;
};

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route
            path="/login"
            element={
              <PublicRoute>
                <Login />
              </PublicRoute>
            }
          />
          <Route
            path="/"
            element={
              <PrivateRoute>
                <Layout />
              </PrivateRoute>
            }
          >
            <Route index element={<Navigate to="/dashboard" />} />
            <Route path="dashboard" element={<Dashboard />} />
            <Route path="orders" element={<Orders />} />
            <Route path="orders/new" element={<NewOrder />} />
            <Route path="orders/:id" element={<OrderDetail />} />
            <Route path="orders/import" element={<ImportWizard />} />
            <Route path="orders/import-historical" element={<HistoricalImport />} />
            <Route path="master-sku" element={<MasterSKU />} />
            <Route path="returns" element={<Returns />} />
            <Route path="channels" element={<Channels />} />
            <Route path="costing" element={<Costing />} />
            <Route path="whatsapp" element={<WhatsAppCRM />} />
            <Route path="tasks" element={<Tasks />} />
            <Route path="inventory" element={<Inventory />} />
            <Route path="analytics" element={<Analytics />} />
            <Route
              path="team"
              element={
                <div className="text-center py-12">
                  <h2 className="text-2xl font-bold font-[Manrope] mb-2">Team</h2>
                  <p className="text-muted-foreground">Coming soon...</p>
                </div>
              }
            />
          </Route>
        </Routes>
      </BrowserRouter>
      <Toaster position="top-right" />
    </AuthProvider>
  );
}

export default App;
