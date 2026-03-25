import React from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Button } from '../components/ui/button';
import {
  LayoutDashboard,
  Package,
  CheckSquare,
  BarChart3,
  Archive,
  Users,
  LogOut,
  Menu,
  X,
  MessageSquare,
  RefreshCcw,
  DollarSign,
  Layers,
  Settings,
  FileText,
  XCircle,
  CheckCircle,
} from 'lucide-react';
import { useState } from 'react';

export const Layout = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const navigation = [
    { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
    { name: 'Orders', href: '/orders', icon: Package },
    { name: 'Inventory', href: '/inventory', icon: Archive },
    { name: 'Cancelled Orders', href: '/cancelled-orders', icon: XCircle },
    { name: 'Resolved Orders', href: '/resolved-orders', icon: CheckCircle },
    { name: 'Returns', href: '/returns', icon: RefreshCcw },
    { name: 'Replacements', href: '/replacements', icon: Package },
    { name: 'Claims', href: '/claims', icon: FileText },
    { name: 'Costing', href: '/costing', icon: DollarSign },
    { name: 'Channels', href: '/channels', icon: Layers },
    { name: 'Tasks', href: '/tasks', icon: CheckSquare },
    { name: 'Analytics', href: '/analytics', icon: BarChart3 },
    { name: 'WhatsApp', href: '/whatsapp', icon: MessageSquare },
    { name: 'Settings', href: '/settings', icon: Settings },
    { name: 'Team', href: '/team', icon: Users },
  ];

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Mobile sidebar backdrop */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`fixed top-0 left-0 z-50 h-screen w-64 bg-card border-r border-border transition-transform duration-300 ${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        } lg:translate-x-0`}
        data-testid="sidebar"
      >
        <div className="flex flex-col h-full">
          <div className="h-16 flex items-center justify-between px-6 border-b border-border">
            <div className="flex items-center gap-3">
              <img src="/furni-logo.png" alt="Furniva" className="h-10" />
              <h2 className="text-lg font-bold font-[Manrope] text-foreground">Furniva</h2>
            </div>
            <button
              className="lg:hidden"
              onClick={() => setSidebarOpen(false)}
              data-testid="close-sidebar-button"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          <nav className="flex-1 px-3 py-4 space-y-1">
            {navigation.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname.startsWith(item.href);
              return (
                <button
                  key={item.name}
                  onClick={() => {
                    navigate(item.href);
                    setSidebarOpen(false);
                  }}
                  className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors duration-150 ${
                    isActive
                      ? 'bg-primary text-primary-foreground shadow-sm'
                      : 'text-muted-foreground hover:bg-secondary hover:text-foreground'
                  }`}
                  data-testid={`nav-${item.name.toLowerCase()}`}
                >
                  <Icon className="w-5 h-5" />
                  {item.name}
                </button>
              );
            })}
          </nav>

          <div className="p-4 border-t border-border">
            <div className="flex items-center gap-3 mb-3">
              <div className="w-10 h-10 bg-primary/10 rounded-full flex items-center justify-center">
                <span className="text-sm font-bold text-primary">
                  {user?.name?.charAt(0)?.toUpperCase()}
                </span>
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-foreground truncate">{user?.name}</p>
                <p className="text-xs text-muted-foreground truncate">{user?.email}</p>
              </div>
            </div>
            <Button
              variant="outline"
              className="w-full"
              onClick={handleLogout}
              data-testid="logout-button"
            >
              <LogOut className="w-4 h-4 mr-2" />
              Logout
            </Button>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <div className="lg:pl-64">
        {/* Top bar */}
        <header className="h-16 bg-card border-b border-border sticky top-0 z-30">
          <div className="h-full px-4 flex items-center justify-between">
            <button
              className="lg:hidden"
              onClick={() => setSidebarOpen(true)}
              data-testid="open-sidebar-button"
            >
              <Menu className="w-6 h-6" />
            </button>
            <div className="flex-1" />
          </div>
        </header>

        {/* Page content */}
        <main className="p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
};
