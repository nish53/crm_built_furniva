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
      if (activeTab === 'fraud') params.fraud_only = true;
      if (activeTab === 'damage') params.damage_only = true;
      if (activeTab === 'pending') params.pending_only = true;
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

  const getStatusBadge = (flags) => {
    if (!flags || flags.length === 0) return <Badge variant="outline">Unknown</Badge>;
    
    if (flags.includes('fraud')) {
      return <Badge className="bg-red-500">Fraud Alert</Badge>;
    }
    if (flags.includes('pfc')) {
      return <Badge className="bg-orange-500">Pre-Cancel</Badge>;
    }
    if (flags.includes('replacement')) {
      return <Badge className="bg-blue-500">Replacement</Badge>;
    }
    if (flags.includes('damage')) {
      return <Badge className="bg-yellow-500">Damaged</Badge>;
    }
    if (flags.includes('pending_action')) {
      return <Badge className="bg-purple-500">Pending Action</Badge>;
    }
    return <Badge variant="outline">{flags[0]}</Badge>;
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
          <h1 className="text-3xl font-bold font-[Manrope]">Returns & Claims</h1>
          <p className="text-muted-foreground mt-1">Manage cancellations, returns, and fraudulent orders</p>
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
                  <p className="text-sm text-muted-foreground">Fraud Cases</p>
                  <p className="text-2xl font-bold text-red-500">{analytics.summary.fraud_count}</p>
                </div>
                <AlertTriangle className="w-8 h-8 text-red-500" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Damaged</p>
                  <p className="text-2xl font-bold text-yellow-600">{analytics.summary.damage_count}</p>
                </div>
                <Package className="w-8 h-8 text-yellow-600" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Replacements</p>
                  <p className="text-2xl font-bold text-blue-500">{analytics.summary.replacement_count}</p>
                </div>
                <RefreshCcw className="w-8 h-8 text-blue-500" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Pre-Cancel</p>
                  <p className="text-2xl font-bold text-orange-500">{analytics.summary.pfc_count}</p>
                </div>
                <XCircle className="w-8 h-8 text-orange-500" />
              </div>
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
          variant={activeTab === 'fraud' ? 'default' : 'ghost'}
          onClick={() => setActiveTab('fraud')}
        >
          Fraudulent
        </Button>
        <Button
          variant={activeTab === 'damage' ? 'default' : 'ghost'}
          onClick={() => setActiveTab('damage')}
        >
          Damaged
        </Button>
        <Button
          variant={activeTab === 'pending' ? 'default' : 'ghost'}
          onClick={() => setActiveTab('pending')}
        >
          Pending Action
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
            {activeTab === 'fraud' && 'Fraudulent Orders'}
            {activeTab === 'damage' && 'Damaged Products'}
            {activeTab === 'pending' && 'Pending Action'}
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
                        {getStatusBadge(ret.smart_flags)}
                      </td>
                      <td className="py-4 px-4">
                        <span className="font-medium">₹{(ret.price || 0).toLocaleString()}</span>
                      </td>
                      <td className="py-4 px-4">
                        <div className="flex items-center justify-end gap-2">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => navigate(`/orders/${ret.id}`)}
                          >
                            <Eye className="w-4 h-4" />
                          </Button>
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
      {analytics && analytics.top_problematic_products.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="font-[Manrope] flex items-center gap-2">
              <TrendingUp className="w-5 h-5" />
              Top Problematic Products
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {analytics.top_problematic_products.map((product, idx) => (
                <div key={idx} className="flex items-center justify-between p-3 bg-secondary/20 rounded">
                  <span className="font-[JetBrains_Mono] text-sm">{product.sku}</span>
                  <Badge variant="destructive">{product.count} returns</Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};
