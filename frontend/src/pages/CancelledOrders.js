import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';
import { XCircle, Search, Filter } from 'lucide-react';
import api from '../lib/api';
import { toast } from 'sonner';

const CancelledOrders = () => {
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    fetchStats();
    fetchOrders();
  }, [activeTab]);

  const fetchStats = async () => {
    try {
      const response = await api.get('/orders/cancelled-orders/stats');
      setStats(response.data);
    } catch (err) {
      toast.error('Failed to fetch cancelled orders statistics');
    }
  };

  const fetchOrders = async () => {
    setLoading(true);
    try {
      const params = activeTab === 'all' ? '' : `?reason=${activeTab}`;
      const response = await api.get(`/orders/cancelled-orders/${params}`);
      setOrders(response.data.orders || []);
    } catch (err) {
      toast.error('Failed to fetch cancelled orders');
    } finally {
      setLoading(false);
    }
  };

  const filteredOrders = orders.filter(order =>
    order.order_number?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    order.customer_name?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const reasonTabs = [
    { key: 'all', label: 'All Cancelled', color: 'gray' },
    { key: 'no_status', label: 'No Status', color: 'gray' },
    { key: 'in_transit', label: 'RTO (In-Transit)', color: 'blue' },
    { key: 'pre_dispatch', label: 'Pre-Dispatch', color: 'purple' },
    { key: 'post_delivery', label: 'Post-Delivery', color: 'orange' },
    { key: 'damage', label: 'Damage', color: 'red' },
    { key: 'customer_issues_except_quality', label: 'Customer Issues', color: 'orange' },
    { key: 'hardware_missing', label: 'Hardware Missing', color: 'yellow' },
    { key: 'defective_product', label: 'Defective Product', color: 'red' },
    { key: 'fraud_customer', label: 'Fraud Customer', color: 'purple' },
    { key: 'wrong_product_sent', label: 'Wrong Product', color: 'blue' },
    { key: 'customer_quality_issues', label: 'Quality Issues', color: 'orange' },
    { key: 'product_delayed_customer_accepted', label: 'Product Delayed', color: 'yellow' },
    { key: 'did_not_specify', label: 'Did Not Specify (PFC)', color: 'gray' },
    { key: 'change_of_mind', label: 'Change of Mind', color: 'blue' },
    { key: 'found_better_pricing', label: 'Better Pricing', color: 'green' },
    { key: 'customer_refused_doorstep', label: 'Customer Refused', color: 'red' },
    { key: 'customer_unavailable', label: 'Customer Unavailable', color: 'orange' },
    { key: 'delay', label: 'Delay', color: 'yellow' }
  ];

  const getReasonCount = (reason) => {
    if (!stats || !stats.by_reason) return 0;
    if (reason === 'all') return stats.total_cancelled || 0;
    return stats.by_reason[reason]?.count || 0;
  };

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
            <XCircle className="w-8 h-8 text-red-600" />
            Cancelled Orders
          </h1>
          <p className="text-muted-foreground mt-1">
            View all cancelled orders grouped by cancellation reason
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
              className="pl-10 pr-4 py-2 border rounded-md w-64 focus:outline-none focus:ring-2 focus:ring-red-500"
            />
          </div>
        </div>
      </div>

      {/* Statistics Cards */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="pt-6">
              <div className="text-3xl font-bold text-red-600">{stats.total_cancelled || 0}</div>
              <div className="text-sm text-muted-foreground">Total Cancelled Orders</div>
              <div className="text-xs text-gray-500 mt-1">100%</div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="text-3xl font-bold text-orange-600">
                {(getReasonCount('damage') + getReasonCount('customer_issues_except_quality') + 
                  getReasonCount('hardware_missing') + getReasonCount('defective_product') + 
                  getReasonCount('fraud_customer') + getReasonCount('wrong_product_sent') + 
                  getReasonCount('customer_quality_issues') + getReasonCount('product_delayed_customer_accepted'))}
              </div>
              <div className="text-sm text-muted-foreground">Returns % (Post-Delivery)</div>
              <div className="text-xs text-gray-500 mt-1">
                {stats.total_cancelled > 0 
                  ? ((((getReasonCount('damage') + getReasonCount('customer_issues_except_quality') + 
                        getReasonCount('hardware_missing') + getReasonCount('defective_product') + 
                        getReasonCount('fraud_customer') + getReasonCount('wrong_product_sent') + 
                        getReasonCount('customer_quality_issues') + getReasonCount('product_delayed_customer_accepted')) / stats.total_cancelled) * 100).toFixed(1))
                  : 0}%
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="text-3xl font-bold text-blue-600">
                {(getReasonCount('customer_refused_doorstep') + getReasonCount('customer_unavailable') + getReasonCount('delay') + getReasonCount('in_transit'))}
              </div>
              <div className="text-sm text-muted-foreground">RTO Pre-Delivery (Excluding PFC)</div>
              <div className="text-xs text-gray-500 mt-1">
                {stats.total_cancelled > 0 
                  ? ((((getReasonCount('customer_refused_doorstep') + getReasonCount('customer_unavailable') + getReasonCount('delay') + getReasonCount('in_transit')) / stats.total_cancelled) * 100).toFixed(1))
                  : 0}%
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="text-3xl font-bold text-gray-600">{getReasonCount('did_not_specify')}</div>
              <div className="text-sm text-muted-foreground">Pre-Fulfillment Cancellations (PFC)</div>
              <div className="text-xs text-gray-500 mt-1">
                {stats.total_cancelled > 0 
                  ? (((getReasonCount('did_not_specify') / stats.total_cancelled) * 100).toFixed(1))
                  : 0}%
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Tabs */}
      <Card>
        <CardHeader className="border-b">
          <div className="flex items-center gap-2 flex-wrap">
            {reasonTabs.map(tab => (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key)}
                className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                  activeTab === tab.key
                    ? 'bg-red-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                {tab.label}
                <span className="ml-2 px-2 py-0.5 rounded-full bg-white/20 text-xs">
                  {getReasonCount(tab.key)}
                </span>
              </button>
            ))}
          </div>
        </CardHeader>
        <CardContent className="pt-6">
          {loading ? (
            <div className="text-center py-12 text-muted-foreground">Loading...</div>
          ) : filteredOrders.length === 0 ? (
            <div className="text-center py-12 text-muted-foreground">
              <XCircle className="w-12 h-12 mx-auto mb-3 opacity-30" />
              <p>No cancelled orders found</p>
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
                        <Badge variant="outline" className="text-red-600 border-red-300">
                          Cancelled
                        </Badge>
                        {order.cancellation_reason && (
                          <Badge variant="outline" className="capitalize">
                            {order.cancellation_reason.replace(/_/g, ' ')}
                          </Badge>
                        )}
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
                      {order.internal_notes && (
                        <div className="mt-2 text-xs text-muted-foreground italic">
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
    </div>
  );
};

export default CancelledOrders;
