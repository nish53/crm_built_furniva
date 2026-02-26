import React, { useEffect, useState } from 'react';
import api from '../lib/api';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select';
import { Badge } from '../components/ui/badge';
import { toast } from 'sonner';
import {
  Search,
  Filter,
  Download,
  Upload,
  Plus,
  Eye,
  Edit,
  Package,
  Truck,
  CheckCircle,
  XCircle,
  RefreshCcw,
  Trash2,
  Check,
  AlertTriangle,
} from 'lucide-react';
import { format } from 'date-fns';
import { useNavigate } from 'react-router-dom';

export const Orders = () => {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [channelFilter, setChannelFilter] = useState('all');
  const [masterSkuFilter, setMasterSkuFilter] = useState('');
  const [cityFilter, setCityFilter] = useState('');
  const [stateFilter, setStateFilter] = useState('');
  const [minPrice, setMinPrice] = useState('');
  const [maxPrice, setMaxPrice] = useState('');
  const [showAdvancedFilters, setShowAdvancedFilters] = useState(false);
  const [selectedOrders, setSelectedOrders] = useState([]);
  const [showBulkActions, setShowBulkActions] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    fetchOrders();
  }, [statusFilter, channelFilter, masterSkuFilter, cityFilter, stateFilter, minPrice, maxPrice]);

  const fetchOrders = async () => {
    try {
      const params = {};
      if (statusFilter !== 'all') params.status = statusFilter;
      if (channelFilter !== 'all') params.channel = channelFilter;
      if (searchTerm) params.search = searchTerm;

      const response = await api.get('/orders/', { params });
      setOrders(response.data);
    } catch (error) {
      toast.error('Failed to fetch orders');
    } finally {
      setLoading(false);
    }
  };

  const handleSelectAll = (e) => {
    if (e.target.checked) {
      setSelectedOrders(orders.map(o => o.id));
    } else {
      setSelectedOrders([]);
    }
  };

  const handleSelectOrder = (orderId) => {
    setSelectedOrders(prev => {
      if (prev.includes(orderId)) {
        return prev.filter(id => id !== orderId);
      } else {
        return [...prev, orderId];
      }
    });
  };

  const handleBulkDelete = async () => {
    if (selectedOrders.length === 0) {
      toast.error('No orders selected');
      return;
    }

    if (!window.confirm(`Are you sure you want to delete ${selectedOrders.length} order(s)? This action cannot be undone.`)) {
      return;
    }

    try {
      await api.post('/orders/bulk-delete', selectedOrders);
      toast.success(`Successfully deleted ${selectedOrders.length} order(s)`);
      setSelectedOrders([]);
      fetchOrders();
    } catch (error) {
      toast.error('Failed to delete orders');
    }
  };

  const handleBulkUpdateStatus = async (newStatus) => {
    if (selectedOrders.length === 0) {
      toast.error('No orders selected');
      return;
    }

    try {
      await api.post('/orders/bulk-update', {
        order_ids: selectedOrders,
        update_fields: { status: newStatus }
      });
      toast.success(`Successfully updated ${selectedOrders.length} order(s) to ${newStatus}`);
      setSelectedOrders([]);
      fetchOrders();
    } catch (error) {
      toast.error('Failed to update orders');
    }
  };

  const handleBulkUpdateChannel = async (newChannel) => {
    if (selectedOrders.length === 0) {
      toast.error('No orders selected');
      return;
    }

    try {
      await api.post('/orders/bulk-update-channel', {
        order_ids: selectedOrders,
        channel: newChannel
      });
      toast.success(`Successfully updated ${selectedOrders.length} order(s) to ${newChannel}`);
      setSelectedOrders([]);
      fetchOrders();
    } catch (error) {
      toast.error('Failed to update channel');
    }
  };

  const handleSearch = (e) => {
    e.preventDefault();
    fetchOrders();
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'pending':
        return <Package className="w-4 h-4" />;
      case 'confirmed':
        return <CheckCircle className="w-4 h-4" />;
      case 'dispatched':
        return <Truck className="w-4 h-4" />;
      case 'delivered':
        return <CheckCircle className="w-4 h-4" />;
      case 'cancelled':
        return <XCircle className="w-4 h-4" />;
      case 'returned':
        return <RefreshCcw className="w-4 h-4" />;
      default:
        return <Package className="w-4 h-4" />;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'pending':
        return 'bg-accent/20 text-accent border-accent/30';
      case 'confirmed':
        return 'bg-primary/20 text-primary border-primary/30';
      case 'dispatched':
        return 'bg-primary/30 text-primary border-primary/40';
      case 'delivered':
        return 'bg-primary/40 text-primary border-primary/50';
      case 'cancelled':
        return 'bg-destructive/20 text-destructive border-destructive/30';
      case 'returned':
        return 'bg-muted text-muted-foreground border-muted-foreground/30';
      default:
        return 'bg-muted text-muted-foreground border-border';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="orders-page">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold font-[Manrope] text-foreground tracking-tight">
            Orders Management
          </h1>
          <p className="text-muted-foreground mt-1">
            View and manage all your orders across channels
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            data-testid="import-csv-button"
            variant="outline"
            onClick={() => navigate('/orders/import')}
          >
            <Upload className="w-4 h-4 mr-2" />
            Import Orders
          </Button>
          <Button
            variant="outline"
            onClick={() => navigate('/orders/import-historical')}
          >
            <Upload className="w-4 h-4 mr-2" />
            Import Historical
          </Button>
          <Button
            data-testid="add-order-button"
            onClick={() => navigate('/orders/new')}
          >
            <Plus className="w-4 h-4 mr-2" />
            Add Order
          </Button>
        </div>
      </div>

      {/* Bulk Actions Bar */}
      {selectedOrders.length > 0 && (
        <Card className="border-primary/50 bg-primary/5">
          <CardContent className="py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <span className="font-medium">
                  {selectedOrders.length} order(s) selected
                </span>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setSelectedOrders([])}
                >
                  Clear Selection
                </Button>
              </div>
              <div className="flex items-center gap-2">
                <Select onValueChange={handleBulkUpdateStatus}>
                  <SelectTrigger className="w-[160px]">
                    <SelectValue placeholder="Update Status" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="pending">Pending</SelectItem>
                    <SelectItem value="confirmed">Confirmed</SelectItem>
                    <SelectItem value="dispatched">Dispatched</SelectItem>
                    <SelectItem value="delivered">Delivered</SelectItem>
                    <SelectItem value="cancelled">Cancelled</SelectItem>
                  </SelectContent>
                </Select>
                <Select onValueChange={(channel) => handleBulkUpdateChannel(channel)}>
                  <SelectTrigger className="w-[160px]">
                    <SelectValue placeholder="Update Channel" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="amazon">Amazon</SelectItem>
                    <SelectItem value="flipkart">Flipkart</SelectItem>
                    <SelectItem value="whatsapp">WhatsApp</SelectItem>
                    <SelectItem value="website">Website</SelectItem>
                    <SelectItem value="phone">Phone</SelectItem>
                  </SelectContent>
                </Select>
                <Button
                  variant="destructive"
                  size="sm"
                  onClick={handleBulkDelete}
                >
                  <Trash2 className="w-4 h-4 mr-2" />
                  Delete Selected
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      <Card className="border-border/60">
        <CardContent className="pt-6">
          <div className="flex flex-col lg:flex-row gap-4">
            <form onSubmit={handleSearch} className="flex-1 flex gap-2">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground w-4 h-4" />
                <Input
                  data-testid="search-orders-input"
                  placeholder="Search by order number, customer, phone, tracking..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
              <Button type="submit" data-testid="search-button">
                Search
              </Button>
            </form>

            <div className="flex gap-2">
              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger className="w-[150px]" data-testid="status-filter">
                  <SelectValue placeholder="Status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Status</SelectItem>
                  <SelectItem value="pending">Pending</SelectItem>
                  <SelectItem value="confirmed">Confirmed</SelectItem>
                  <SelectItem value="dispatched">Dispatched</SelectItem>
                  <SelectItem value="delivered">Delivered</SelectItem>
                  <SelectItem value="cancelled">Cancelled</SelectItem>
                  <SelectItem value="returned">Returned</SelectItem>
                </SelectContent>
              </Select>

              <Select value={channelFilter} onValueChange={setChannelFilter}>
                <SelectTrigger className="w-[150px]" data-testid="channel-filter">
                  <SelectValue placeholder="Channel" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Channels</SelectItem>
                  <SelectItem value="amazon">Amazon</SelectItem>
                  <SelectItem value="flipkart">Flipkart</SelectItem>
                  <SelectItem value="whatsapp">WhatsApp</SelectItem>
                  <SelectItem value="website">Website</SelectItem>
                  <SelectItem value="phone">Phone</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card className="border-border/60">
        <CardHeader>
          <CardTitle className="font-[Manrope]">
            Orders ({orders.length})
          </CardTitle>
        </CardHeader>
        <CardContent>
          {orders.length === 0 ? (
            <div className="text-center py-12" data-testid="no-orders-message">
              <Package className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
              <p className="text-muted-foreground">No orders found</p>
              <Button
                variant="outline"
                className="mt-4"
                onClick={() => navigate('/orders/new')}
              >
                <Plus className="w-4 h-4 mr-2" />
                Add Your First Order
              </Button>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full" data-testid="orders-table">
                <thead>
                  <tr className="border-b border-border">
                    <th className="text-left py-3 px-4 w-12">
                      <input
                        type="checkbox"
                        checked={selectedOrders.length === orders.length && orders.length > 0}
                        onChange={handleSelectAll}
                        className="rounded border-border"
                      />
                    </th>
                    <th className="text-left py-3 px-4 text-xs font-bold text-muted-foreground uppercase tracking-wider">
                      Order #
                    </th>
                    <th className="text-left py-3 px-4 text-xs font-bold text-muted-foreground uppercase tracking-wider">
                      Customer
                    </th>
                    <th className="text-left py-3 px-4 text-xs font-bold text-muted-foreground uppercase tracking-wider">
                      Product
                    </th>
                    <th className="text-left py-3 px-4 text-xs font-bold text-muted-foreground uppercase tracking-wider">
                      Channel
                    </th>
                    <th className="text-left py-3 px-4 text-xs font-bold text-muted-foreground uppercase tracking-wider">
                      Status
                    </th>
                    <th className="text-left py-3 px-4 text-xs font-bold text-muted-foreground uppercase tracking-wider">
                      Dispatch By
                    </th>
                    <th className="text-right py-3 px-4 text-xs font-bold text-muted-foreground uppercase tracking-wider">
                      Amount
                    </th>
                    <th className="text-right py-3 px-4 text-xs font-bold text-muted-foreground uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {orders.map((order) => (
                    <tr
                      key={order.id}
                      className="border-b border-border/40 hover:bg-secondary/30 transition-colors duration-150"
                      data-testid={`order-row-${order.id}`}
                    >
                      <td className="py-4 px-4">
                        <input
                          type="checkbox"
                          checked={selectedOrders.includes(order.id)}
                          onChange={() => handleSelectOrder(order.id)}
                          className="rounded border-border"
                        />
                      </td>
                      <td className="py-4 px-4">
                        <span className="font-[JetBrains_Mono] text-sm font-medium">
                          {order.order_number}
                        </span>
                      </td>
                      <td className="py-4 px-4">
                        <div>
                          <p className="text-sm font-medium">{order.customer_name}</p>
                          <p className="text-xs text-muted-foreground">{order.phone}</p>
                        </div>
                      </td>
                      <td className="py-4 px-4">
                        {order.master_sku ? (
                          <div>
                            <p className="font-medium text-sm">{order.master_sku}</p>
                            <p className="text-xs text-muted-foreground">{order.product_name}</p>
                          </div>
                        ) : (
                          <div className="flex items-center gap-2">
                            <AlertTriangle className="w-4 h-4 text-yellow-600" />
                            <span className="text-xs text-yellow-700 font-medium">SKU Not Mapped</span>
                          </div>
                        )}
                      </td>
                      <td className="py-4 px-4">
                        <span className="text-xs uppercase tracking-wider text-muted-foreground">
                          {order.channel}
                        </span>
                      </td>
                      <td className="py-4 px-4">
                        <Badge
                          variant="outline"
                          className={`${getStatusColor(order.status)} flex items-center gap-1 w-fit`}
                        >
                          {getStatusIcon(order.status)}
                          {order.status}
                        </Badge>
                      </td>
                      <td className="py-4 px-4">
                        <span className="text-sm text-muted-foreground">
                          {order.dispatch_by && !isNaN(new Date(order.dispatch_by).getTime())
                            ? format(new Date(order.dispatch_by), 'MMM dd, yyyy')
                            : 'N/A'}
                        </span>
                      </td>
                      <td className="py-4 px-4 text-right">
                        <span className="text-sm font-medium">
                          ₹{(order.price || 0).toLocaleString()}
                        </span>
                      </td>
                      <td className="py-4 px-4 text-right">
                        <div className="flex justify-end gap-2">
                          <Button
                            data-testid={`view-order-${order.id}`}
                            variant="ghost"
                            size="sm"
                            onClick={() => navigate(`/orders/${order.id}`)}
                          >
                            <Eye className="w-4 h-4" />
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
