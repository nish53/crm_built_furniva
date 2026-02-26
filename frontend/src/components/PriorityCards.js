import React, { useEffect, useState } from 'react';
import api from '../lib/api';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { AlertTriangle, Package, Clock, Tag } from 'lucide-react';
import { format } from 'date-fns';
import { useNavigate } from 'react-router-dom';
import { toast } from 'sonner';

export const PriorityCards = () => {
  const [dispatchPending, setDispatchPending] = useState(null);
  const [delayedOrders, setDelayedOrders] = useState(null);
  const [unmappedSkus, setUnmappedSkus] = useState(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    fetchPriorityData();
  }, []);

  const fetchPriorityData = async () => {
    try {
      const [dispatchRes, delayedRes, skuRes] = await Promise.all([
        api.get('/dashboard/priority/dispatch-pending-today'),
        api.get('/dashboard/priority/delayed-orders'),
        api.get('/dashboard/priority/unmapped-skus'),
      ]);
      setDispatchPending(dispatchRes.data);
      setDelayedOrders(delayedRes.data);
      setUnmappedSkus(skuRes.data);
    } catch (error) {
      console.error('Failed to fetch priority data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleFakeShip = async (orderId) => {
    const trackingId = prompt('Enter fake tracking ID:');
    if (!trackingId) return;

    try {
      await api.post(`/dashboard/orders/${orderId}/fake-ship?tracking_id=${trackingId}`);
      toast.success('Order marked as fake shipped');
      fetchPriorityData();
    } catch (error) {
      toast.error('Failed to fake ship order');
    }
  };

  if (loading) {
    return null;
  }

  return (
    <div className="space-y-4">
      {/* Dispatch Pending Today */}
      {dispatchPending && dispatchPending.count > 0 && (
        <Card className="border-orange-500/50 bg-orange-50/50 dark:bg-orange-950/20">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <AlertTriangle className="w-5 h-5 text-orange-600" />
                <CardTitle className="text-orange-900 dark:text-orange-100">
                  {dispatchPending.message}
                </CardTitle>
              </div>
              <Badge variant="destructive">{dispatchPending.count}</Badge>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {dispatchPending.orders.slice(0, 5).map((order) => (
                <div key={order.id} className="flex items-center justify-between p-3 bg-white dark:bg-gray-800 rounded-lg border">
                  <div className="flex-1">
                    <p className="font-medium text-sm">{order.order_number}</p>
                    <p className="text-xs text-muted-foreground">{order.customer_name}</p>
                  </div>
                  <div className="flex gap-2">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleFakeShip(order.id)}
                    >
                      Fake Ship
                    </Button>
                    <Button
                      size="sm"
                      onClick={() => navigate(`/orders/${order.id}`)}
                    >
                      View
                    </Button>
                  </div>
                </div>
              ))}
            </div>
            {dispatchPending.count > 5 && (
              <Button
                variant="link"
                className="mt-2 w-full"
                onClick={() => navigate('/orders')}
              >
                View all {dispatchPending.count} orders
              </Button>
            )}
          </CardContent>
        </Card>
      )}

      {/* Delayed Orders */}
      {delayedOrders && delayedOrders.count > 0 && (
        <Card className="border-red-500/50 bg-red-50/50 dark:bg-red-950/20">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Clock className="w-5 h-5 text-red-600" />
                <CardTitle className="text-red-900 dark:text-red-100">
                  {delayedOrders.message}
                </CardTitle>
              </div>
              <Badge variant="destructive">{delayedOrders.count}</Badge>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {delayedOrders.orders.slice(0, 5).map((order) => (
                <div key={order.id} className="flex items-center justify-between p-3 bg-white dark:bg-gray-800 rounded-lg border">
                  <div className="flex-1">
                    <p className="font-medium text-sm">{order.order_number}</p>
                    <p className="text-xs text-muted-foreground">
                      Expected: {order.delivery_by && format(new Date(order.delivery_by), 'MMM dd, yyyy')}
                    </p>
                  </div>
                  <Button
                    size="sm"
                    onClick={() => navigate(`/orders/${order.id}`)}
                  >
                    View
                  </Button>
                </div>
              ))}
            </div>
            {delayedOrders.count > 5 && (
              <Button
                variant="link"
                className="mt-2 w-full"
                onClick={() => navigate('/orders')}
              >
                View all {delayedOrders.count} orders
              </Button>
            )}
          </CardContent>
        </Card>
      )}

      {/* Unmapped SKUs */}
      {unmappedSkus && unmappedSkus.count > 0 && (
        <Card className="border-yellow-500/50 bg-yellow-50/50 dark:bg-yellow-950/20">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Tag className="w-5 h-5 text-yellow-600" />
                <CardTitle className="text-yellow-900 dark:text-yellow-100">
                  {unmappedSkus.message}
                </CardTitle>
              </div>
              <Badge className="bg-yellow-600">{unmappedSkus.count}</Badge>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {unmappedSkus.unmapped_skus.slice(0, 5).map((item, idx) => (
                <div key={idx} className="flex items-center justify-between p-3 bg-white dark:bg-gray-800 rounded-lg border">
                  <div className="flex-1">
                    <p className="font-medium text-sm">{item.sku}</p>
                    <p className="text-xs text-muted-foreground">
                      {item.channel} • {item.order_count} orders
                    </p>
                  </div>
                  <Button
                    size="sm"
                    onClick={() => navigate('/master-sku')}
                  >
                    Map SKU
                  </Button>
                </div>
              ))}
            </div>
            {unmappedSkus.count > 5 && (
              <Button
                variant="link"
                className="mt-2 w-full"
                onClick={() => navigate('/master-sku')}
              >
                View all {unmappedSkus.count} SKUs
              </Button>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
};
