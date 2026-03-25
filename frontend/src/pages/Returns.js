import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Input } from '../components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import api from '../lib/api';
import { toast } from 'sonner';
import { 
  RefreshCcw, 
  AlertTriangle, 
  Package, 
  TrendingUp, 
  Filter,
  Eye,
  CheckCircle2,
  XCircle
} from 'lucide-react';
import { format } from 'date-fns';
import { useNavigate } from 'react-router-dom';

export const Returns = () => {
  const [returns, setReturns] = useState([]);
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    fetchReturns();
    fetchAnalytics();
  }, [activeTab]);

  const fetchReturns = async () => {
    try {
      const params = {};
      // ONLY fetch open returns (exclude closed status)
      params.exclude_status = 'closed';
      
      if (activeTab === 'pfc') params.category = 'pfc';
      if (activeTab === 'resolved') params.category = 'resolved';
      if (activeTab === 'refunded') params.category = 'refunded';
      if (activeTab === 'fraud') params.category = 'fraud';
      if (searchTerm) params.reason_filter = searchTerm;

      const response = await api.get('/returns/', { params });
      setReturns(response.data.items || []);
    } catch (error) {
      toast.error('Failed to fetch returns');
    } finally {
      setLoading(false);
    }
  };

  const fetchAnalytics = async () => {
    try {
      const response = await api.get('/returns/analytics');
      setAnalytics(response.data);
    } catch (error) {
      console.error('Failed to fetch analytics');
    }
  };

  const takeAction = async (orderId, action) => {
    try {
      await api.post(`/returns/${orderId}/action?action=${action}`);
      toast.success(`Action completed: ${action}`);
      fetchReturns();
    } catch (error) {
      toast.error('Failed to complete action');
    }
  };

  const getStatusBadge = (category) => {
    if (!category) return <Badge variant="outline">Unknown</Badge>;
    
    if (category === 'fraud') {
      return <Badge className="bg-red-600 text-white">🔴 Fraud/Logistics</Badge>;
    }
    if (category === 'pfc') {
      return <Badge className="bg-green-600 text-white">🟢 PFC</Badge>;
    }
    if (category === 'resolved') {
      return <Badge className="bg-yellow-600 text-white">🟡 Resolved</Badge>;
    }
    if (category === 'refunded') {
      return <Badge className="bg-orange-600 text-white">🔴 Refunded</Badge>;
    }
    return <Badge variant="outline">{category}</Badge>;
  };

  const filteredReturns = returns.filter(r => 
    r.order_number?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    r.customer_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    r.cancellation_reason?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold font-[Manrope]">Open Returns</h1>
          <p className="text-muted-foreground mt-1">Manage in-progress return requests (closed returns moved to Cancelled/Resolved)</p>
        </div>
        <Button onClick={() => { fetchReturns(); fetchAnalytics(); }}>
          <RefreshCcw className="w-4 h-4 mr-2" />
          Refresh
        </Button>
      </div>

      {/* Analytics Cards */}
      {analytics && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Total Returns</p>
                  <p className="text-2xl font-bold">{analytics.summary.total_returns}</p>
                </div>
                <RefreshCcw className="w-8 h-8 text-muted-foreground" />
              </div>
              <p className="text-xs text-muted-foreground mt-2">
                {analytics.summary.return_rate}% of all orders
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">PFC (Pre-Cancel)</p>
                  <p className="text-2xl font-bold text-green-600">{analytics.summary.pfc_count}</p>
                </div>
                <XCircle className="w-8 h-8 text-green-600" />
              </div>
              <p className="text-xs text-muted-foreground mt-2">
                ₹{analytics.summary.pfc_loss?.toLocaleString()} loss
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Resolved (No Refund)</p>
                  <p className="text-2xl font-bold text-yellow-600">{analytics.summary.resolved_count}</p>
                </div>
                <CheckCircle2 className="w-8 h-8 text-yellow-600" />
              </div>
              <p className="text-xs text-muted-foreground mt-2">
                ₹{analytics.summary.resolved_cost?.toLocaleString()} cost
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Refunded</p>
                  <p className="text-2xl font-bold text-orange-600">{analytics.summary.refunded_count}</p>
                </div>
                <AlertTriangle className="w-8 h-8 text-orange-600" />
              </div>
              <p className="text-xs text-muted-foreground mt-2">
                ₹{analytics.summary.refunded_loss?.toLocaleString()} loss
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Fraud/Logistics</p>
                  <p className="text-2xl font-bold text-red-600">{analytics.summary.fraud_count}</p>
                </div>
                <AlertTriangle className="w-8 h-8 text-red-600" />
              </div>
              <p className="text-xs text-muted-foreground mt-2">
                ₹{analytics.summary.fraud_loss?.toLocaleString()} loss
              </p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Tabs */}
      <div className="flex items-center gap-2 border-b">
        <Button
          variant={activeTab === 'all' ? 'default' : 'ghost'}
          onClick={() => setActiveTab('all')}
        >
          All Returns
        </Button>
        <Button
          variant={activeTab === 'pfc' ? 'default' : 'ghost'}
          onClick={() => setActiveTab('pfc')}
          className="text-green-600"
        >
          🟢 PFC (Minimal Loss)
        </Button>
        <Button
          variant={activeTab === 'resolved' ? 'default' : 'ghost'}
          onClick={() => setActiveTab('resolved')}
          className="text-yellow-600"
        >
          🟡 Resolved (No Refund)
        </Button>
        <Button
          variant={activeTab === 'refunded' ? 'default' : 'ghost'}
          onClick={() => setActiveTab('refunded')}
          className="text-orange-600"
        >
          🔴 Refunded (Full Loss)
        </Button>
        <Button
          variant={activeTab === 'fraud' ? 'default' : 'ghost'}
          onClick={() => setActiveTab('fraud')}
          className="text-red-600"
        >
          ⚫ Fraud/Logistics
        </Button>
      </div>

      {/* Search */}
      <div className="flex items-center gap-4">
        <div className="flex-1 relative">
          <Input
            placeholder="Search by order number, customer, or reason..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pr-10"
          />
          <Filter className="w-4 h-4 absolute right-3 top-3 text-muted-foreground" />
        </div>
      </div>

      {/* Returns Table */}
      <Card>
        <CardHeader>
          <CardTitle className="font-[Manrope]">
            {activeTab === 'all' && 'All Returns'}
            {activeTab === 'pfc' && '🟢 PFC - Pre-Fulfillment Cancellations'}
            {activeTab === 'resolved' && '🟡 Resolved - No Refund Issued'}
            {activeTab === 'refunded' && '🔴 Refunded - Full Loss'}
            {activeTab === 'fraud' && '⚫ Fraud/Logistics Errors'}
          </CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="text-center py-12">
              <p className="text-muted-foreground">Loading returns...</p>
            </div>
          ) : filteredReturns.length === 0 ? (
            <div className="text-center py-12">
              <Package className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
              <p className="text-muted-foreground">No returns found</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b">
                    <th className="text-left py-3 px-4 text-xs font-bold text-muted-foreground uppercase">Order #</th>
                    <th className="text-left py-3 px-4 text-xs font-bold text-muted-foreground uppercase">Customer</th>
                    <th className="text-left py-3 px-4 text-xs font-bold text-muted-foreground uppercase">Product</th>
                    <th className="text-left py-3 px-4 text-xs font-bold text-muted-foreground uppercase">Reason</th>
                    <th className="text-left py-3 px-4 text-xs font-bold text-muted-foreground uppercase">Classification</th>
                    <th className="text-left py-3 px-4 text-xs font-bold text-muted-foreground uppercase">Amount</th>
                    <th className="text-right py-3 px-4 text-xs font-bold text-muted-foreground uppercase">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredReturns.map((ret) => (
                    <tr key={ret.id} className="border-b hover:bg-secondary/30">
                      <td className="py-4 px-4">
                        <span className="font-[JetBrains_Mono] text-sm font-medium">
                          {ret.order_number}
                        </span>
                      </td>
                      <td className="py-4 px-4">
                        <div>
                          <p className="text-sm font-medium">{ret.customer_name}</p>
                          <p className="text-xs text-muted-foreground">{ret.phone}</p>
                        </div>
                      </td>
                      <td className="py-4 px-4">
                        <div>
                          <p className="text-sm">{ret.product_name}</p>
                          <p className="text-xs text-muted-foreground font-[JetBrains_Mono]">{ret.sku}</p>
                        </div>
                      </td>
                      <td className="py-4 px-4">
                        <p className="text-sm">{ret.cancellation_reason || 'Not specified'}</p>
                      </td>
                      <td className="py-4 px-4">
                        {getStatusBadge(ret.category)}
                      </td>
                      <td className="py-4 px-4">
                        <div>
                          <span className="font-medium">₹{(ret.price || 0).toLocaleString()}</span>
                          <p className="text-xs text-muted-foreground">
                            Loss: ₹{(ret.refund_loss || 0).toLocaleString()}
                          </p>
                        </div>
                      </td>
                      <td className="py-4 px-4">
                        <div className="flex items-center justify-end gap-2">
                          {/* View Return Details - for return_requests */}
                          {ret.return_request_id ? (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => navigate(`/returns/${ret.return_request_id}`)}
                              title="View Return Details"
                            >
                              <Eye className="w-4 h-4" />
                            </Button>
                          ) : (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => navigate(`/orders/${ret.id}`)}
                              title="View Order"
                            >
                              <Eye className="w-4 h-4" />
                            </Button>
                          )}
                          {ret.smart_flags?.includes('pending_action') && (
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => takeAction(ret.id, 'approve_refund')}
                            >
                              <CheckCircle2 className="w-4 h-4" />
                            </Button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Top Problematic Products */}
      {analytics && analytics.top_products_by_loss && analytics.top_products_by_loss.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="font-[Manrope] flex items-center gap-2">
              <TrendingUp className="w-5 h-5" />
              Top Problematic Products (by Loss)
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {analytics.top_products_by_loss.map((product, idx) => (
                <div key={idx} className="flex items-center justify-between p-3 bg-secondary/20 rounded">
                  <span className="font-[JetBrains_Mono] text-sm">{product.sku}</span>
                  <Badge variant="destructive">₹{product.loss.toLocaleString()} loss</Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Pincode Analysis */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {analytics && analytics.top_problematic_pincodes && analytics.top_problematic_pincodes.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle className="font-[Manrope] text-lg">Top Return Pincodes</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {analytics.top_problematic_pincodes.slice(0, 5).map((pincode, idx) => (
                  <div key={idx} className="flex items-center justify-between p-2 bg-secondary/20 rounded">
                    <span className="font-medium">{pincode.pincode}</span>
                    <Badge>{pincode.count} returns</Badge>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {analytics && analytics.top_damage_pincodes && analytics.top_damage_pincodes.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle className="font-[Manrope] text-lg">Top Damage Pincodes</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {analytics.top_damage_pincodes.slice(0, 5).map((pincode, idx) => (
                  <div key={idx} className="flex items-center justify-between p-2 bg-secondary/20 rounded">
                    <span className="font-medium">{pincode.pincode}</span>
                    <Badge variant="destructive">{pincode.damage_count} damaged</Badge>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
};
