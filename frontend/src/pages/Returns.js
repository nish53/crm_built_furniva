import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Input } from '../components/ui/input';
import api from '../lib/api';
import { toast } from 'sonner';
import { 
  RefreshCcw, 
  Package, 
  Filter,
  Eye,
  Trash2,
  AlertCircle,
  CheckCircle,
  Clock,
  TrendingUp
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export const Returns = () => {
  const [returns, setReturns] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [analytics, setAnalytics] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    fetchReturns();
    fetchAnalytics();
  }, []);

  const fetchReturns = async () => {
    try {
      // Use open_only=true to exclude both closed AND rejected returns
      const params = { open_only: true };
      if (searchTerm) params.search = searchTerm;

      const response = await api.get('/return-requests/', { params });
      setReturns(response.data || []);
    } catch (error) {
      toast.error('Failed to fetch open returns');
    } finally {
      setLoading(false);
    }
  };

  const fetchAnalytics = async () => {
    try {
      const response = await api.get('/return-requests/analytics/dashboard');
      setAnalytics(response.data);
    } catch (error) {
      console.error('Failed to fetch analytics:', error);
    }
  };

  const handleDelete = async (returnId) => {
    if (!window.confirm('Are you sure you want to delete this return request? This action cannot be undone.')) {
      return;
    }

    try {
      console.log('Deleting return:', returnId);
      const response = await api.delete(`/return-requests/${returnId}`);
      console.log('Delete response:', response.data);
      toast.success('Return request deleted successfully');
      fetchReturns();
    } catch (error) {
      console.error('Delete error:', error.response?.data || error.message);
      toast.error(error.response?.data?.detail || 'Failed to delete return request');
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
          <p className="text-muted-foreground mt-1">Manage in-progress return requests (excluding closed returns)</p>
        </div>
        <Button onClick={() => { fetchReturns(); fetchAnalytics(); }}>
          <RefreshCcw className="w-4 h-4 mr-2" />
          Refresh
        </Button>
      </div>

      {/* Analytics Dashboard - Reason Wise (Bug #1) */}
      {analytics && (
        <div className="space-y-4">
          {/* Summary Cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-muted-foreground">Total Open</p>
                    <p className="text-2xl font-bold">{analytics.total_open}</p>
                  </div>
                  <Package className="w-8 h-8 text-blue-500" />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-muted-foreground">Pending Action</p>
                    <p className="text-2xl font-bold text-orange-600">{analytics.pending_action}</p>
                  </div>
                  <Clock className="w-8 h-8 text-orange-500" />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-muted-foreground">Total Closed</p>
                    <p className="text-2xl font-bold text-green-600">{analytics.total_closed}</p>
                  </div>
                  <CheckCircle className="w-8 h-8 text-green-500" />
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Reason-Wise Tiles (Bug #3 - Replace "Reasons Tracked" with individual tiles) */}
          {analytics.by_reason && analytics.by_reason.length > 0 && (
            <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3">
              {analytics.by_reason.slice(0, 6).map((item, idx) => (
                <Card 
                  key={idx} 
                  className="cursor-pointer hover:bg-secondary/50 transition-colors"
                  onClick={() => setSearchTerm(item.reason)}
                >
                  <CardContent className="pt-4 pb-3">
                    <p className="text-xs text-muted-foreground truncate mb-1" title={item.reason}>
                      {item.reason?.length > 20 ? item.reason.substring(0, 20) + '...' : item.reason || 'Not Specified'}
                    </p>
                    <p className="text-xl font-bold">{item.count}</p>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </div>
      )}

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
            Open Return Requests
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
                    <th className="text-left py-3 px-4 text-xs font-bold text-muted-foreground uppercase">Status</th>
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
                        <p className="text-sm">{ret.return_reason || ret.cancellation_reason || 'Not specified'}</p>
                      </td>
                      <td className="py-4 px-4">
                        <Badge variant="outline" className="capitalize">
                          {ret.return_status?.replace(/_/g, ' ') || 'Pending'}
                        </Badge>
                      </td>
                      <td className="py-4 px-4">
                        <div className="flex items-center justify-end gap-2">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => navigate(`/returns/${ret.id}`)}
                            title="View Return Details"
                          >
                            <Eye className="w-4 h-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleDelete(ret.id)}
                            title="Delete Return Request"
                            className="text-red-600 hover:text-red-700 hover:bg-red-50"
                          >
                            <Trash2 className="w-4 h-4" />
                          </Button>
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
    </div>
  );
};
