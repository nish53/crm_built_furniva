import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api from '../lib/api';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { toast } from 'sonner';
import { ArrowLeft, Package, User, MapPin, Phone, Calendar, Truck, CheckCircle } from 'lucide-react';
import { format } from 'date-fns';

export const OrderDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [order, setOrder] = useState(null);
  const [loading, setLoading] = useState(true);
  const [updating, setUpdating] = useState(false);

  useEffect(() => {
    fetchOrder();
  }, [id]);

  const fetchOrder = async () => {
    try {
      const response = await api.get(`/orders/${id}`);
      setOrder(response.data);
    } catch (error) {
      toast.error('Failed to fetch order details');
    } finally {
      setLoading(false);
    }
  };

  const updateOrderStatus = async (status) => {
    setUpdating(true);
    try {
      await api.patch(`/orders/${id}`, { status });
      toast.success(`Order ${status}`);
      fetchOrder();
    } catch (error) {
      toast.error('Failed to update order');
    } finally {
      setUpdating(false);
    }
  };

  const updateDispatch = async (trackingNumber, courierPartner) => {
    setUpdating(true);
    try {
      await api.patch(`/orders/${id}`, {
        status: 'dispatched',
        tracking_number: trackingNumber,
        courier_partner: courierPartner,
        dispatch_date: new Date().toISOString(),
      });
      toast.success('Order marked as dispatched');
      fetchOrder();
    } catch (error) {
      toast.error('Failed to update dispatch');
    } finally {
      setUpdating(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    );
  }

  if (!order) {
    return (
      <div className="text-center py-12">
        <p className="text-muted-foreground">Order not found</p>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="order-detail-page">
      <div className="flex items-center gap-4">
        <Button variant="ghost" onClick={() => navigate('/orders')} data-testid="back-button">
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back
        </Button>
        <div className="flex-1">
          <h1 className="text-3xl font-bold font-[Manrope] text-foreground tracking-tight">
            Order {order.order_number}
          </h1>
          <p className="text-muted-foreground mt-1">
            {format(new Date(order.order_date), 'MMMM dd, yyyy HH:mm')}
          </p>
        </div>
        <Badge
          className={`${
            order.status === 'pending' ? 'bg-accent/20 text-accent' :
            order.status === 'dispatched' ? 'bg-primary/20 text-primary' :
            order.status === 'delivered' ? 'bg-primary/30 text-primary' :
            'bg-muted text-muted-foreground'
          } text-sm`}
        >
          {order.status}
        </Badge>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <Card className="border-border/60" data-testid="order-info-card">
            <CardHeader>
              <CardTitle className="font-[Manrope] flex items-center gap-2">
                <Package className="w-5 h-5" />
                Order Information
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-muted-foreground">Order Number</p>
                  <p className="font-[JetBrains_Mono] font-medium">{order.order_number}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Channel</p>
                  <p className="font-medium uppercase">{order.channel}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">SKU</p>
                  <p className="font-[JetBrains_Mono]">{order.sku}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">ASIN</p>
                  <p className="font-[JetBrains_Mono]">{order.asin || 'N/A'}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Product</p>
                  <p className="font-medium">{order.product_name}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Quantity</p>
                  <p className="font-medium">{order.quantity}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Price</p>
                  <p className="font-medium text-lg">₹{order.price.toLocaleString()}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Dispatch By</p>
                  <p className="font-medium text-accent">
                    {format(new Date(order.dispatch_by), 'MMM dd, yyyy')}
                  </p>
                </div>
              </div>

              {order.tracking_number && (
                <div className="mt-4 p-4 bg-primary/5 rounded-lg">
                  <p className="text-sm text-muted-foreground mb-1">Tracking Information</p>
                  <p className="font-[JetBrains_Mono] font-medium text-lg">{order.tracking_number}</p>
                  {order.courier_partner && (
                    <p className="text-sm text-muted-foreground mt-1">via {order.courier_partner}</p>
                  )}
                </div>
              )}

              {order.instructions && (
                <div>
                  <p className="text-sm text-muted-foreground mb-1">Instructions</p>
                  <p className="text-sm">{order.instructions}</p>
                </div>
              )}
            </CardContent>
          </Card>

          <Card className="border-border/60" data-testid="customer-info-card">
            <CardHeader>
              <CardTitle className="font-[Manrope] flex items-center gap-2">
                <User className="w-5 h-5" />
                Customer Information
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex items-start gap-3">
                <User className="w-4 h-4 text-muted-foreground mt-1" />
                <div>
                  <p className="text-sm text-muted-foreground">Customer Name</p>
                  <p className="font-medium">{order.customer_name}</p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <Phone className="w-4 h-4 text-muted-foreground mt-1" />
                <div>
                  <p className="text-sm text-muted-foreground">Phone</p>
                  <p className="font-medium font-[JetBrains_Mono]">{order.phone}</p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <MapPin className="w-4 h-4 text-muted-foreground mt-1" />
                <div>
                  <p className="text-sm text-muted-foreground">Shipping Address</p>
                  <p className="text-sm">{order.shipping_address || order.billing_address}</p>
                  <p className="text-sm">
                    {order.city}, {order.state} - {order.pincode}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="space-y-6">
          <Card className="border-border/60" data-testid="quick-actions-card">
            <CardHeader>
              <CardTitle className="font-[Manrope]">Quick Actions</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {order.status === 'pending' && (
                <Button
                  data-testid="confirm-order-button"
                  className="w-full"
                  onClick={() => updateOrderStatus('confirmed')}
                  disabled={updating}
                >
                  <CheckCircle className="w-4 h-4 mr-2" />
                  Confirm Order
                </Button>
              )}
              {order.status === 'confirmed' && (
                <Button
                  data-testid="dispatch-order-button"
                  className="w-full"
                  onClick={() => {
                    const tracking = prompt('Enter tracking number:');
                    const courier = prompt('Enter courier partner:');
                    if (tracking && courier) {
                      updateDispatch(tracking, courier);
                    }
                  }}
                  disabled={updating}
                >
                  <Truck className="w-4 h-4 mr-2" />
                  Mark as Dispatched
                </Button>
              )}
              {order.status === 'dispatched' && (
                <Button
                  data-testid="deliver-order-button"
                  className="w-full"
                  onClick={() => updateOrderStatus('delivered')}
                  disabled={updating}
                >
                  <CheckCircle className="w-4 h-4 mr-2" />
                  Mark as Delivered
                </Button>
              )}
            </CardContent>
          </Card>

          <Card className="border-border/60" data-testid="communication-card">
            <CardHeader>
              <CardTitle className="font-[Manrope]">Communication</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm">DC1 Called</span>
                <Badge variant={order.dc1_called ? 'default' : 'outline'}>
                  {order.dc1_called ? 'Yes' : 'No'}
                </Badge>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm">CP Sent</span>
                <Badge variant={order.cp_sent ? 'default' : 'outline'}>
                  {order.cp_sent ? 'Yes' : 'No'}
                </Badge>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm">DNP1 Conf</span>
                <Badge variant={order.dnp1_conf ? 'default' : 'outline'}>
                  {order.dnp1_conf ? 'Yes' : 'No'}
                </Badge>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm">Assembly Type</span>
                <span className="text-sm font-medium">{order.assembly_type || 'Not set'}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm">Paid Assembly</span>
                <Badge variant={order.paid_assembly ? 'default' : 'outline'}>
                  {order.paid_assembly ? 'Yes' : 'No'}
                </Badge>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};
