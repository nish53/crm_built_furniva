import React, { useEffect, useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import api from '../lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Package, Clock, TrendingUp, AlertCircle, Phone, Archive, FileText } from 'lucide-react';
import { format } from 'date-fns';

export const Dashboard = () => {
  const { user } = useAuth();
  const [stats, setStats] = useState(null);
  const [recentOrders, setRecentOrders] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
  }, []);

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
      title: 'Total Orders',
      value: stats.total_orders,
      icon: Package,
      color: 'text-primary',
      bgColor: 'bg-primary/10',
    },
    {
      title: 'Pending Orders',
      value: stats.pending_orders,
      icon: Clock,
      color: 'text-accent',
      bgColor: 'bg-accent/10',
    },
    {
      title: 'Dispatched Today',
      value: stats.dispatched_today,
      icon: TrendingUp,
      color: 'text-primary',
      bgColor: 'bg-primary/10',
    },
    {
      title: 'Pending Tasks',
      value: stats.pending_tasks,
      icon: FileText,
      color: 'text-muted-foreground',
      bgColor: 'bg-muted',
    },
    {
      title: 'Pending Calls',
      value: stats.pending_calls,
      icon: Phone,
      color: 'text-accent',
      bgColor: 'bg-accent/10',
    },
    {
      title: 'Low Stock Items',
      value: stats.low_stock_items,
      icon: Archive,
      color: 'text-destructive',
      bgColor: 'bg-destructive/10',
    },
    {
      title: 'Pending Claims',
      value: stats.pending_claims,
      icon: AlertCircle,
      color: 'text-destructive',
      bgColor: 'bg-destructive/10',
    },
    {
      title: 'Revenue Today',
      value: `₹${stats.revenue_today.toLocaleString()}`,
      icon: TrendingUp,
      color: 'text-primary',
      bgColor: 'bg-primary/10',
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

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {statCards.map((stat, index) => {
          const Icon = stat.icon;
          return (
            <Card key={index} className="border-border/60 hover:shadow-md transition-shadow duration-200" data-testid={`stat-card-${index}`}>
              <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  {stat.title}
                </CardTitle>
                <div className={`p-2 rounded-lg ${stat.bgColor}`}>
                  <Icon className={`h-4 w-4 ${stat.color}`} />
                </div>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold font-[Manrope]">{stat.value}</div>
              </CardContent>
            </Card>
          );
        })}
      </div>

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
                  className="flex items-center justify-between p-4 border border-border/40 rounded-lg hover:bg-secondary/30 transition-colors duration-150"
                  data-testid={`order-item-${order.id}`}
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
                    <p className="text-sm font-medium">₹{order.price.toLocaleString()}</p>
                    <p className="text-xs text-muted-foreground">
                      {format(new Date(order.order_date), 'MMM dd, yyyy')}
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
