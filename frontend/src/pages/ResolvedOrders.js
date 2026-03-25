import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';
import { CheckCircle, Search } from 'lucide-react';
import api from '../lib/api';
import { toast } from 'sonner';

const ResolvedOrders = () => {
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    fetchStats();
    fetchOrders();
  }, []);

  const fetchStats = async () => {
    try {
      const response = await api.get('/orders/resolved-orders/stats');
      setStats(response.data);
    } catch (err) {
      toast.error('Failed to fetch resolved orders statistics');
    }
  };

  const fetchOrders = async () => {
    setLoading(true);
    try {
      const response = await api.get('/orders/resolved-orders/');
      setOrders(response.data.orders || []);
    } catch (err) {
      toast.error('Failed to fetch resolved orders');
    } finally {
      setLoading(false);
    }
  };

  const filteredOrders = orders.filter(order =>
    order.order_number?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    order.customer_name?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const formatDate = (dateString) => {
    if (!dateString) return '-';
    return new Date(dateString).toLocaleDateString('en-IN', {
      day: '2-digit',
      month: 'short',
      year: 'numeric'
    });
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold font-[Manrope] flex items-center gap-3">
            <CheckCircle className="w-8 h-8 text-green-600" />
            Resolved Orders
          </h1>
          <p className="text-muted-foreground mt-1">
            Orders where issues were resolved (Part Damage, Full Damage, Hardware Missing, Minimal Installation Issue)
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <input
              type="text"
              placeholder="Search orders..."
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              className="pl-10 pr-4 py-2 border rounded-md w-64 focus:outline-none focus:ring-2 focus:ring-green-500"
            />
          </div>
        </div>
      </div>

      {/* Statistics Card */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card>
            <CardContent className="pt-6">
              <div className="text-3xl font-bold text-green-600">{stats.total_resolved || 0}</div>
              <div className="text-sm text-muted-foreground">Total Resolved</div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="text-3xl font-bold text-blue-600">{orders.filter(o => o.status === 'delivered').length}</div>
              <div className="text-sm text-muted-foreground">Delivered with Resolution</div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="text-3xl font-bold text-gray-600">{stats.recent_orders?.length || 0}</div>
              <div className="text-sm text-muted-foreground">Recent Resolutions</div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Orders List */}
      <Card>
        <CardHeader>
          <CardTitle className="font-[Manrope]">Resolved Orders</CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="text-center py-12 text-muted-foreground">Loading...</div>
          ) : filteredOrders.length === 0 ? (
            <div className="text-center py-12 text-muted-foreground">
              <CheckCircle className="w-12 h-12 mx-auto mb-3 opacity-30" />
              <p>No resolved orders found</p>
            </div>
          ) : (
            <div className="space-y-3">
              {filteredOrders.map(order => (
                <div
                  key={order.id}
                  onClick={() => navigate(`/orders/${order.id}`)}
                  className="p-4 border rounded-lg hover:bg-gray-50 cursor-pointer transition-colors"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3">
                        <span className="font-[JetBrains_Mono] font-medium text-lg">
                          {order.order_number}
                        </span>
                        <Badge variant="outline" className="text-green-600 border-green-300">
                          Resolved
                        </Badge>
                        <Badge variant="outline" className="text-blue-600 border-blue-300 capitalize">
                          {order.status}
                        </Badge>
                      </div>
                      <div className="mt-2 grid grid-cols-4 gap-4 text-sm">
                        <div>
                          <span className="text-muted-foreground">Customer:</span>{' '}
                          <span className="font-medium">{order.customer_name}</span>
                        </div>
                        <div>
                          <span className="text-muted-foreground">Channel:</span>{' '}
                          <span className="font-medium capitalize">{order.channel}</span>
                        </div>
                        <div>
                          <span className="text-muted-foreground">Order Date:</span>{' '}
                          <span className="font-medium">{formatDate(order.order_date)}</span>
                        </div>
                        <div>
                          <span className="text-muted-foreground">Amount:</span>{' '}
                          <span className="font-[JetBrains_Mono] font-medium">₹{order.price}</span>
                        </div>
                      </div>
                      {order.delivery_date && (
                        <div className="mt-2 text-xs text-muted-foreground">
                          <span className="font-medium">Delivered:</span> {formatDate(order.delivery_date)}
                        </div>
                      )}
                      {order.internal_notes && (
                        <div className="mt-1 text-xs text-green-700 bg-green-50 px-2 py-1 rounded-md inline-block">
                          {order.internal_notes}
                        </div>
                      )}
                    </div>
                    <Button variant="ghost" size="sm">View Details</Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Recent Resolutions Summary */}
      {stats && stats.recent_orders && stats.recent_orders.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="font-[Manrope] text-sm">Recent Resolutions</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {stats.recent_orders.slice(0, 5).map(order => (
                <div key={order.id} className="flex items-center justify-between text-sm py-2 border-b last:border-0">
                  <span className="font-[JetBrains_Mono]">{order.order_number}</span>
                  <span className="text-muted-foreground">{order.customer_name}</span>
                  <Badge variant="outline" className="text-xs">Resolved</Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default ResolvedOrders;
