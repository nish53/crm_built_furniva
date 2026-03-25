import React, { useEffect, useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';
import api from '../lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Package, Clock, TrendingUp, AlertCircle, Phone, Archive, FileText } from 'lucide-react';
import { format } from 'date-fns';
import { PriorityCards } from '../components/PriorityCards';

export const Dashboard = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);
  const [recentOrders, setRecentOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [revenuePeriod, setRevenuePeriod] = useState('today'); // today, 30days, year, lifetime
  const [revenueMetric, setRevenueMetric] = useState('amount'); // amount, units
  const [revenueData, setRevenueData] = useState({ amount: 0, units: 0 });

  useEffect(() => {
    fetchDashboardData();
  }, []);

  useEffect(() => {
    fetchRevenueData();
  }, [revenuePeriod]);

  const fetchRevenueData = async () => {
    try {
      const response = await api.get(`/dashboard/revenue/${revenuePeriod}`);
      setRevenueData(response.data);
    } catch (error) {
      console.error('Failed to fetch revenue data:', error);
      setRevenueData({ amount: 0, units: 0 });
    }
  };

  const fetchDashboardData = async () => {
    try {
      const [statsRes, ordersRes] = await Promise.all([
        api.get('/dashboard/stats'),
        api.get('/dashboard/recent-orders'),
      ]);
      setStats(statsRes.data);
      setRecentOrders(ordersRes.data);
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const statCards = stats ? [
    {
      title: 'Revenue Today',
      value: `₹${stats.revenue_today.toLocaleString()}`,
      icon: TrendingUp,
      color: 'text-green-600',
      bgColor: 'bg-green-100',
      gradient: 'from-green-50 to-green-100',
      clickable: false,
      hasDropdown: true, // Special handling for revenue
    },
    {
      title: 'Open Returns',
      value: stats.open_returns || 0,
      icon: Package,
      color: 'text-orange-600',
      bgColor: 'bg-orange-100',
      gradient: 'from-orange-50 to-orange-100',
      onClick: () => navigate('/returns'),
      clickable: true,
    },
    {
      title: 'Open Replacements',
      value: stats.open_replacements || 0,
      icon: Package,
      color: 'text-blue-600',
      bgColor: 'bg-blue-100',
      gradient: 'from-blue-50 to-blue-100',
      onClick: () => navigate('/replacements'),
      clickable: true,
    },
    {
      title: 'Pending Orders',
      value: stats.pending_orders,
      subtitle: 'Not yet dispatched',
      icon: Clock,
      color: 'text-amber-600',
      bgColor: 'bg-amber-100',
      gradient: 'from-amber-50 to-amber-100',
      onClick: () => navigate('/orders?status=pending'),
      clickable: true,
    },
    {
      title: 'Pending Confirmation',
      value: stats.pending_calls,
      subtitle: 'Needs confirmation urgently',
      icon: Phone,
      color: 'text-red-600',
      bgColor: 'bg-red-100',
      gradient: 'from-red-50 to-red-100',
      onClick: () => navigate('/orders?status=pending&confirmed=false'),
      clickable: true,
    },
    // REMOVED: Total Orders tile
    {
      title: 'Dispatched Today',
      value: stats.dispatched_today,
      icon: TrendingUp,
      color: 'text-emerald-600',
      bgColor: 'bg-emerald-100',
      gradient: 'from-emerald-50 to-emerald-100',
      onClick: () => navigate('/orders?dispatched_today=true'),
      clickable: true,
    },
    {
      title: 'Pending Tasks',
      value: stats.pending_tasks,
      icon: FileText,
      color: 'text-purple-600',
      bgColor: 'bg-purple-100',
      gradient: 'from-purple-50 to-purple-100',
      onClick: () => navigate('/tasks?status=pending'),
      clickable: true,
    },
    {
      title: 'Low Stock Items',
      value: stats.low_stock_items,
      subtitle: 'Below reorder level',
      icon: Archive,
      color: 'text-rose-600',
      bgColor: 'bg-rose-100',
      gradient: 'from-rose-50 to-rose-100',
      onClick: () => navigate('/products', { state: { filterLowStock: true } }),
      clickable: true,
    },
    {
      title: 'Pending Claims',
      value: stats.pending_claims,
      icon: AlertCircle,
      color: 'text-violet-600',
      bgColor: 'bg-violet-100',
      gradient: 'from-violet-50 to-violet-100',
      onClick: () => navigate('/claims', { state: { filterStatus: 'filed' } }),
      clickable: true,
    },
  ] : [];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="dashboard-container">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold font-[Manrope] text-foreground tracking-tight">
            Welcome back, {user?.name}
          </h1>
          <p className="text-muted-foreground mt-1">Here's what's happening with your business today.</p>
        </div>
      </div>

      {/* Revenue Card - Special with Dropdown */}
      <Card className="border-0 shadow-lg bg-gradient-to-br from-green-50 to-green-100 col-span-1 md:col-span-2">
        <CardContent className="p-6">
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-2">
                <p className="text-sm font-medium text-muted-foreground">Revenue</p>
                <select 
                  value={revenuePeriod}
                  onChange={(e) => setRevenuePeriod(e.target.value)}
                  className="text-xs border rounded px-2 py-1 bg-white"
                  onClick={(e) => e.stopPropagation()}
                >
                  <option value="today">Today</option>
                  <option value="30days">Last 30 Days</option>
                  <option value="year">This Year</option>
                  <option value="lifetime">Lifetime</option>
                </select>
                <button
                  onClick={() => setRevenueMetric(revenueMetric === 'amount' ? 'units' : 'amount')}
                  className="text-xs border rounded px-2 py-1 bg-white hover:bg-gray-50"
                >
                  {revenueMetric === 'amount' ? '₹ Amount' : '📦 Units'}
                </button>
              </div>
              <div className="text-4xl font-bold font-[Manrope] text-green-600 mt-2 mb-1">
                {revenueMetric === 'amount' 
                  ? `₹${revenueData.amount.toLocaleString()}` 
                  : `${revenueData.units.toLocaleString()} units`
                }
              </div>
              <p className="text-xs text-muted-foreground mt-1">
                {revenuePeriod === 'today' && 'Orders placed today'}
                {revenuePeriod === '30days' && 'Last 30 days performance'}
                {revenuePeriod === 'year' && 'Year-to-date revenue'}
                {revenuePeriod === 'lifetime' && 'Total all-time revenue'}
              </p>
            </div>
            <div className="p-3 rounded-xl bg-green-100 shadow-sm">
              <TrendingUp className="h-6 w-6 text-green-600" />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Other Tiles */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
        {statCards.slice(1).map((stat, index) => {
          const Icon = stat.icon;
          return (
            <Card 
              key={index} 
              className={`border-0 shadow-lg hover:shadow-xl transition-all duration-300 bg-gradient-to-br ${stat.gradient} ${stat.clickable ? 'cursor-pointer hover:scale-105 hover:border-2 hover:border-primary/30' : ''}`}
              data-testid={`stat-card-${index}`}
              onClick={stat.clickable ? stat.onClick : undefined}
            >
              <CardContent className="p-6">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <p className="text-sm font-medium text-muted-foreground mb-1">
                      {stat.title}
                    </p>
                    <div className="text-3xl font-bold font-[Manrope] mt-2 mb-1" style={{ color: stat.color.replace('text-', '') }}>
                      {stat.value}
                    </div>
                    {stat.subtitle && (
                      <p className="text-xs text-muted-foreground mt-1">{stat.subtitle}</p>
                    )}
                  </div>
                  <div className={`p-3 rounded-xl ${stat.bgColor} shadow-sm`}>
                    <Icon className={`h-6 w-6 ${stat.color}`} />
                  </div>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Priority Alerts */}
      <PriorityCards />

      <Card className="border-border/60" data-testid="recent-orders-card">
        <CardHeader>
          <CardTitle className="font-[Manrope]">Recent Orders</CardTitle>
        </CardHeader>
        <CardContent>
          {recentOrders.length === 0 ? (
            <p className="text-muted-foreground text-center py-8">No orders yet</p>
          ) : (
            <div className="space-y-4">
              {recentOrders.map((order) => (
                <div
                  key={order.id}
                  className="flex items-center justify-between p-4 border border-border/40 rounded-lg hover:bg-secondary/30 transition-colors duration-150 cursor-pointer"
                  data-testid={`order-item-${order.id}`}
                  onClick={() => navigate(`/orders/${order.id}`)}
                >
                  <div className="flex-1">
                    <div className="flex items-center gap-3">
                      <p className="font-medium font-[JetBrains_Mono] text-sm">{order.order_number}</p>
                      <span className={`px-2.5 py-0.5 rounded-full text-xs font-medium uppercase tracking-wide ${
                        order.status === 'pending' ? 'bg-accent/20 text-accent' :
                        order.status === 'dispatched' ? 'bg-primary/20 text-primary' :
                        order.status === 'delivered' ? 'bg-primary/30 text-primary' :
                        'bg-muted text-muted-foreground'
                      }`}>
                        {order.status}
                      </span>
                      <span className="text-xs text-muted-foreground uppercase tracking-wider">{order.channel}</span>
                    </div>
                    <p className="text-sm text-muted-foreground mt-1">{order.customer_name} • {order.product_name}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-medium">₹{(order.price || 0).toLocaleString()}</p>
                    <p className="text-xs text-muted-foreground">
                      {order.order_date && !isNaN(new Date(order.order_date).getTime()) 
                        ? format(new Date(order.order_date), 'MMM dd, yyyy')
                        : 'N/A'}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};
