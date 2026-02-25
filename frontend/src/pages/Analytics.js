import React, { useEffect, useState } from 'react';
import api from '../lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { BarChart, Bar, LineChart, Line, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { TrendingUp, Package, DollarSign, AlertCircle } from 'lucide-react';

export const Analytics = () => {
  const [overview, setOverview] = useState(null);
  const [salesTrend, setSalesTrend] = useState([]);
  const [topProducts, setTopProducts] = useState([]);
  const [channelPerformance, setChannelPerformance] = useState([]);
  const [returnsAnalysis, setReturnsAnalysis] = useState(null);
  const [loading, setLoading] = useState(true);
  const [period, setPeriod] = useState('30');

  useEffect(() => {
    fetchAnalytics();
  }, [period]);

  const fetchAnalytics = async () => {
    try {
      const [overviewRes, trendRes, productsRes, channelsRes, returnsRes] = await Promise.all([
        api.get(`/analytics/overview?days=${period}`),
        api.get(`/analytics/sales-trend?days=${period}`),
        api.get('/analytics/top-products?limit=10'),
        api.get('/analytics/channel-performance'),
        api.get('/analytics/returns-analysis'),
      ]);

      setOverview(overviewRes.data);
      setSalesTrend(trendRes.data);
      setTopProducts(productsRes.data);
      setChannelPerformance(channelsRes.data);
      setReturnsAnalysis(returnsRes.data);
    } catch (error) {
      console.error('Failed to fetch analytics');
    } finally {
      setLoading(false);
    }
  };

  const COLORS = ['#1A4D2E', '#FF6B35', '#F7B32B', '#4ECDC4', '#95E1D3'];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="analytics-page">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold font-[Manrope] text-foreground tracking-tight">
            Analytics & Reports
          </h1>
          <p className="text-muted-foreground mt-1">
            Insights into your business performance
          </p>
        </div>
        <Select value={period} onValueChange={setPeriod}>
          <SelectTrigger className="w-[180px]">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="7">Last 7 days</SelectItem>
            <SelectItem value="30">Last 30 days</SelectItem>
            <SelectItem value="90">Last 90 days</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Overview Stats */}
      {overview && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card className="border-border/60">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">Total Orders</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-between">
                <div className="text-2xl font-bold font-[Manrope]">{overview.total_orders}</div>
                <Package className="w-8 h-8 text-primary opacity-20" />
              </div>
            </CardContent>
          </Card>

          <Card className="border-border/60">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">Total Revenue</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-between">
                <div className="text-2xl font-bold font-[Manrope]">₹{overview.total_revenue.toLocaleString()}</div>
                <DollarSign className="w-8 h-8 text-primary opacity-20" />
              </div>
            </CardContent>
          </Card>

          <Card className="border-border/60">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">Avg Order Value</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-between">
                <div className="text-2xl font-bold font-[Manrope]">₹{overview.average_order_value.toLocaleString()}</div>
                <TrendingUp className="w-8 h-8 text-primary opacity-20" />
              </div>
            </CardContent>
          </Card>

          <Card className="border-border/60">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">Period</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold font-[Manrope]">{overview.period_days} days</div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Sales Trend */}
      <Card className="border-border/60">
        <CardHeader>
          <CardTitle className="font-[Manrope]">Sales Trend</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={salesTrend}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis dataKey="_id" stroke="#6b7280" />
              <YAxis stroke="#6b7280" />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="revenue" stroke="#1A4D2E" strokeWidth={2} name="Revenue (₹)" />
              <Line type="monotone" dataKey="orders" stroke="#FF6B35" strokeWidth={2} name="Orders" />
            </LineChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Top Products */}
        <Card className="border-border/60">
          <CardHeader>
            <CardTitle className="font-[Manrope]">Top Products</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={topProducts.slice(0, 5)}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis dataKey="_id" stroke="#6b7280" />
                <YAxis stroke="#6b7280" />
                <Tooltip />
                <Bar dataKey="total_revenue" fill="#1A4D2E" name="Revenue (₹)" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Channel Performance */}
        <Card className="border-border/60">
          <CardHeader>
            <CardTitle className="font-[Manrope]">Channel Performance</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={channelPerformance}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={(entry) => `${entry._id}: ₹${entry.total_revenue.toLocaleString()}`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="total_revenue"
                >
                  {channelPerformance.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Channel Details Table */}
      <Card className="border-border/60">
        <CardHeader>
          <CardTitle className="font-[Manrope]">Channel Details</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-border">
                  <th className="text-left py-3 px-4 text-xs font-bold text-muted-foreground uppercase">Channel</th>
                  <th className="text-right py-3 px-4 text-xs font-bold text-muted-foreground uppercase">Orders</th>
                  <th className="text-right py-3 px-4 text-xs font-bold text-muted-foreground uppercase">Revenue</th>
                  <th className="text-right py-3 px-4 text-xs font-bold text-muted-foreground uppercase">Avg Order</th>
                  <th className="text-right py-3 px-4 text-xs font-bold text-muted-foreground uppercase">Return Rate</th>
                </tr>
              </thead>
              <tbody>
                {channelPerformance.map((channel) => (
                  <tr key={channel._id} className="border-b border-border/40 hover:bg-secondary/30">
                    <td className="py-4 px-4 font-medium uppercase">{channel._id}</td>
                    <td className="py-4 px-4 text-right">{channel.total_orders}</td>
                    <td className="py-4 px-4 text-right font-medium">₹{channel.total_revenue.toLocaleString()}</td>
                    <td className="py-4 px-4 text-right">₹{Math.round(channel.avg_order_value).toLocaleString()}</td>
                    <td className="py-4 px-4 text-right">
                      <span className={channel.return_rate > 5 ? 'text-destructive font-medium' : ''}>
                        {channel.return_rate}%
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Returns Analysis */}
      {returnsAnalysis && returnsAnalysis.by_product.length > 0 && (
        <Card className="border-border/60">
          <CardHeader>
            <CardTitle className="font-[Manrope] flex items-center gap-2">
              <AlertCircle className="w-5 h-5 text-destructive" />
              Returns Analysis
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div>
                <h3 className="font-semibold mb-2">Top Returned Products</h3>
                <div className="space-y-2">
                  {returnsAnalysis.by_product.slice(0, 5).map((item) => (
                    <div key={item._id} className="flex items-center justify-between p-2 bg-secondary/30 rounded">
                      <div>
                        <p className="font-medium text-sm">{item.product_name}</p>
                        <p className="text-xs text-muted-foreground">SKU: {item._id}</p>
                      </div>
                      <span className="text-destructive font-medium">{item.return_count} returns</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};
