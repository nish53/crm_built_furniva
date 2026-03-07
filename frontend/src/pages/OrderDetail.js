import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api from '../lib/api';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { AutomationPanel } from '../components/AutomationPanel';
import { toast } from 'sonner';
import {
  ArrowLeft, Package, User, Calendar, Truck,
  CheckCircle, RefreshCcw, DollarSign, X, FileText, AlertTriangle,
  XCircle, AlertCircle, Phone, MapPin, Edit
} from 'lucide-react';
import { format } from 'date-fns';

export const OrderDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [order, setOrder] = useState(null);
  const [loading, setLoading] = useState(true);
  const [updating, setUpdating] = useState(false);
  const [showReturnModal, setShowReturnModal] = useState(false);
  const [showFinancialModal, setShowFinancialModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [financials, setFinancials] = useState(null);
  const [editForm, setEditForm] = useState({});

  const [returnForm, setReturnForm] = useState({
    return_type: 'return',
    return_reason: '',
    return_reason_details: '',
    damage_category: '',
    is_installation_related: false,
    replacement_items: ''
  });

  const [finForm, setFinForm] = useState({
    product_cost: '', shipping_cost: '', packaging_cost: '',
    installation_cost: '', marketplace_commission_rate: '15'
  });

  useEffect(() => { fetchOrder(); }, [id]);

  const fetchOrder = async () => {
    try {
      const res = await api.get(`/orders/${id}`);
      setOrder(res.data);
      try { const fRes = await api.get(`/financials/order/${id}`); setFinancials(fRes.data); }
      catch { setFinancials(null); }
    } catch { toast.error('Failed to fetch order'); }
    finally { setLoading(false); }
  };

  const updateOrderStatus = async (status) => {
    setUpdating(true);
    try {
      await api.patch(`/orders/${id}`, { status });
      toast.success(`Order ${status}`);
      fetchOrder();
    } catch { toast.error('Failed to update'); }
    finally { setUpdating(false); }
  };

  const updateDispatch = async () => {
    const tracking = prompt('Enter tracking number:');
    if (!tracking) return;
    const courier = prompt('Enter courier partner:');
    if (!courier) return;
    setUpdating(true);
    try {
      await api.patch(`/orders/${id}`, {
        status: 'dispatched', tracking_number: tracking,
        courier_partner: courier, dispatch_date: new Date().toISOString()
      });
      toast.success('Order dispatched');
      fetchOrder();
    } catch { toast.error('Failed to update'); }
    finally { setUpdating(false); }
  };

  const handleCreateReturn = async (e) => {
    e.preventDefault();
    try {
      await api.post('/return-requests/', {
        order_id: id,
        return_type: returnForm.return_type,
        return_reason: returnForm.return_reason,
        return_reason_details: returnForm.return_reason_details || null,
        damage_category: returnForm.damage_category || null,
        is_installation_related: returnForm.is_installation_related,
        replacement_items: returnForm.return_type === 'replacement' ? returnForm.replacement_items : null,
        damage_images: [],
        replacement_images: []
      });
      toast.success('Return request created');
      setShowReturnModal(false);
      setReturnForm({
        return_type: 'return',
        return_reason: '',
        return_reason_details: '',
        damage_category: '',
        is_installation_related: false,
        replacement_items: ''
      });
      fetchOrder();
    } catch (err) { toast.error(err.response?.data?.detail || 'Failed to create return'); }
  };

  const handleCalculateFinancials = async (e) => {
    e.preventDefault();
    try {
      const params = new URLSearchParams({
        product_cost: finForm.product_cost,
        shipping_cost: finForm.shipping_cost,
        packaging_cost: finForm.packaging_cost || '0',
        installation_cost: finForm.installation_cost || '0',
        marketplace_commission_rate: finForm.marketplace_commission_rate || '15'
      });
      const res = await api.post(`/financials/calculate/${id}?${params.toString()}`);
      setFinancials(res.data);
      toast.success('Financials calculated');
      setShowFinancialModal(false);
    } catch { toast.error('Failed to calculate financials'); }
  };

  const handleEditOrder = () => {
    setEditForm({
      status: order.status || '',
      tracking_number: order.tracking_number || '',
      courier_partner: order.courier_partner || '',
      customer_name: order.customer_name || '',
      phone: order.phone || '',
      phone_secondary: order.phone_secondary || '',
      city: order.city || '',
      state: order.state || '',
      pincode: order.pincode || '',
      shipping_address: order.shipping_address || '',
      instructions: order.instructions || '',
    });
    setShowEditModal(true);
  };

  const handleSaveEdit = async (e) => {
    e.preventDefault();
    setUpdating(true);
    try {
      await api.patch(`/orders/${id}`, editForm);
      toast.success('Order updated successfully');
      setShowEditModal(false);
      fetchOrder();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to update order');
    } finally {
      setUpdating(false);
    }
  };

  const safeDate = (d) => { if (!d) return null; try { return format(new Date(d), 'MMM dd, yyyy HH:mm'); } catch { return '-'; } };
  const safeDateShort = (d) => { if (!d) return '-'; try { return format(new Date(d), 'MMM dd, yyyy'); } catch { return '-'; } };

  if (loading) return (
    <div className="flex items-center justify-center h-[60vh]">
      <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-primary" />
    </div>
  );

  if (!order) return <div className="text-center py-12"><p className="text-muted-foreground">Order not found</p></div>;

  const statusColors = {
    pending: 'bg-yellow-100 text-yellow-800', confirmed: 'bg-blue-100 text-blue-800',
    dispatched: 'bg-indigo-100 text-indigo-800', delivered: 'bg-green-100 text-green-800',
    cancelled: 'bg-red-100 text-red-800', returned: 'bg-orange-100 text-orange-800',
  };

  // Communication checklist - correct workflow order, read-only (green/red)
  // Supports both old fields (dnp1_conf) and new historical fields (order_conf_calling, dnp_day1)
  const commChecklist = [
    { key: 'order_conf_calling', fallbackKey: 'dc1_called', label: 'Order Confirmation Call', dateKey: 'dc1_date' },
    { key: 'dispatch_conf_sent', fallbackKey: 'cp_sent', label: 'Order Confirmation Message Sent' },
    { key: 'dnp_day1', fallbackKey: 'dnp1_conf', label: 'DNP Day 1 (Did Not Pick)' },
    { key: 'confirmed_day1', label: 'Confirmed on Day 1' },
    { key: 'dnp_day2', fallbackKey: 'dnp2_conf', label: 'DNP Day 2' },
    { key: 'confirmed_day2', label: 'Confirmed on Day 2' },
    { key: 'dnp_day3', fallbackKey: 'dnp3_conf', label: 'DNP Day 3' },
    { key: 'confirmed_day3', label: 'Confirmed on Day 3' },
    { key: 'dp_conf', label: 'Dispatch Confirmation' },
    { key: 'deliver_conf', label: 'Delivery Confirmation' },
    { key: 'install_conf', label: 'Installation Confirmation' },
    { key: 'review_conf', label: 'Review Request' },
  ];

  return (
    <div className="space-y-6" data-testid="order-detail-page">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button variant="ghost" onClick={() => navigate('/orders')} data-testid="back-button">
          <ArrowLeft className="w-4 h-4 mr-2" />Back
        </Button>
        <div className="flex-1">
          <h1 className="text-3xl font-bold font-[Manrope] tracking-tight">Order {order.order_number}</h1>
          <p className="text-muted-foreground mt-1">{safeDate(order.order_date)}</p>
        </div>
        <Badge className={statusColors[order.status] || 'bg-gray-100 text-gray-800'}>{order.status?.toUpperCase()}</Badge>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column */}
        <div className="lg:col-span-2 space-y-6">
          {/* Order Info */}
          <Card data-testid="order-info-card">
            <CardHeader><CardTitle className="font-[Manrope] flex items-center gap-2"><Package className="w-5 h-5" />Order Information</CardTitle></CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4 text-sm">
                <InfoField label="Order Number" value={order.order_number} mono />
                <InfoField label="Channel" value={order.channel?.toUpperCase()} />
                <InfoField label="SKU" value={order.sku} mono />
                <InfoField label="Master SKU" value={order.master_sku || '-'} mono />
                <InfoField label="ASIN" value={order.asin || '-'} mono />
                <InfoField label="Product" value={order.product_name} />
                <InfoField label="Quantity" value={order.quantity} />
                <InfoField label="Price" value={`₹${(order.price || 0).toLocaleString()}`} />
                <InfoField label="Item Tax" value={order.item_tax ? `₹${order.item_tax}` : '-'} />
                <InfoField label="Shipping Price" value={order.shipping_price ? `₹${order.shipping_price}` : '-'} />
                <InfoField label="Total" value={order.total_amount ? `₹${order.total_amount.toLocaleString()}` : '-'} />
                <InfoField label="Dispatch By" value={safeDateShort(order.dispatch_by)} />
                <InfoField label="Delivery By" value={safeDateShort(order.delivery_by)} />
                {order.delivery_date && <InfoField label="Actual Delivery Date" value={safeDateShort(order.delivery_date)} />}
                {order.cancellation_reason && <InfoField label="Cancellation/Return Reason" value={order.cancellation_reason} />}
                <InfoField label="Payment" value={order.payment_method || '-'} />
                <InfoField label="Fulfillment" value={order.fulfillment_channel || '-'} />
                <InfoField label="Sales Channel" value={order.sales_channel || '-'} />
                <InfoField label="Ship Service" value={order.ship_service_level || '-'} />
                {order.is_prime && <Badge className="self-center bg-blue-100 text-blue-800">Prime</Badge>}
                {order.is_business_order && <Badge className="self-center bg-purple-100 text-purple-800">Business</Badge>}
              </div>

              {order.master_status?.length > 0 && (
                <div className="mt-4">
                  <p className="text-xs text-muted-foreground mb-2">Master Status</p>
                  <div className="flex flex-wrap gap-1.5">
                    {order.master_status.map((s, i) => <Badge key={i} variant="outline" className="text-xs capitalize">{s.replace(/_/g, ' ')}</Badge>)}
                  </div>
                </div>
              )}

              {(order.tracking_number || order.courier_partner) && (
                <div className="mt-4 p-3 bg-primary/5 rounded-lg">
                  <p className="text-xs text-muted-foreground mb-1">Tracking</p>
                  <p className="font-[JetBrains_Mono] font-medium">{order.tracking_number || '-'}</p>
                  {order.courier_partner && <p className="text-xs text-muted-foreground mt-1">via {order.courier_partner}</p>}
                  {order.pickup_status && <p className="text-xs mt-1">Pickup: <span className="font-medium">{order.pickup_status}</span></p>}
                </div>
              )}

              {order.instructions && (
                <div className="mt-4">
                  <p className="text-xs text-muted-foreground mb-1">Instructions</p>
                  <p className="text-sm bg-muted p-2 rounded">{order.instructions}</p>
                </div>
              )}
            </CardContent>
          </Card>


          {/* Timeline */}
          <Card data-testid="timeline-card">
            <CardHeader><CardTitle className="font-[Manrope] flex items-center gap-2"><Calendar className="w-5 h-5" />Timeline</CardTitle></CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-3 text-sm">
                <TimelineItem label="Order Date" date={safeDateShort(order.order_date)} active />
                <TimelineItem label="Dispatch Date" date={safeDateShort(order.dispatch_date)} active={!!order.dispatch_date} />
                <TimelineItem label="Pickup Date" date={safeDateShort(order.pickup_date)} active={!!order.pickup_date} />
                <TimelineItem label="In Transit" date={safeDateShort(order.in_transit_date)} active={!!order.in_transit_date} />
                <TimelineItem label="Out for Delivery" date={safeDateShort(order.out_for_delivery_date)} active={!!order.out_for_delivery_date} />
                <TimelineItem label="Delivered" date={safeDateShort(order.delivery_date || order.delivered_date)} active={!!(order.delivery_date || order.delivered_date)} />
                {order.return_requested && <>
                  <TimelineItem label="Return Requested" date={safeDateShort(order.return_date)} active warn />
                  <TimelineItem label="RTO Initiated" date={safeDateShort(order.rto_initiated_date)} active={!!order.rto_initiated_date} warn />
                  <TimelineItem label="RTO Delivered" date={safeDateShort(order.rto_delivered_date)} active={!!order.rto_delivered_date} warn />
                </>}
              </div>
            </CardContent>
          </Card>

          {/* Customer */}
          <Card data-testid="customer-info-card">
            <CardHeader><CardTitle className="font-[Manrope] flex items-center gap-2"><User className="w-5 h-5" />Customer</CardTitle></CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <InfoField label="Name" value={order.customer_name} />
                <InfoField label="Phone" value={order.phone} mono />
                {order.phone_secondary && <InfoField label="Phone 2" value={order.phone_secondary} mono />}
                {order.email && <InfoField label="Email" value={order.email} />}
                <div className="col-span-2">
                  <p className="text-xs text-muted-foreground">Shipping Address</p>
                  <p className="text-sm font-medium">
                    {[order.shipping_address_line1, order.shipping_address_line2, order.landmark].filter(Boolean).join(', ') || order.shipping_address || order.billing_address || '-'}
                  </p>
                  <p className="text-xs text-muted-foreground mt-0.5">{[order.city, order.state, order.pincode].filter(Boolean).join(', ')}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Financials */}
          {financials && (
            <Card data-testid="financial-card">
              <CardHeader><CardTitle className="font-[Manrope] flex items-center gap-2"><DollarSign className="w-5 h-5" />Financials</CardTitle></CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  <FinBox label="Selling Price" value={`₹${financials.selling_price}`} />
                  <FinBox label="Commission" value={`₹${financials.marketplace_commission}`} sub />
                  <FinBox label="Net Revenue" value={`₹${financials.net_revenue}`} />
                  <FinBox label="Total Cost" value={`₹${financials.total_cost}`} sub />
                  <FinBox label="Gross Profit" value={`₹${financials.gross_profit}`} highlight={financials.gross_profit > 0} warn={financials.gross_profit < 0} />
                  <FinBox label="Margin" value={`${financials.profit_margin}%`} highlight={financials.profit_margin > 0} />
                  <FinBox label="Product Cost" value={`₹${financials.product_cost}`} />
                  <FinBox label="Shipping Cost" value={`₹${financials.shipping_cost}`} />
                </div>
              </CardContent>
            </Card>
          )}
        </div>

        {/* Right Column */}
        <div className="space-y-6">
          {/* Quick Actions */}
          <Card data-testid="quick-actions-card">
            <CardHeader><CardTitle className="font-[Manrope]">Quick Actions</CardTitle></CardHeader>
            <CardContent className="space-y-2">
              <Button variant="outline" className="w-full" onClick={handleEditOrder} data-testid="edit-order-button">
                <Edit className="w-4 h-4 mr-2" />Edit Order
              </Button>
              
              {order.status === 'pending' && (
                <Button className="w-full" onClick={() => updateOrderStatus('confirmed')} disabled={updating} data-testid="confirm-order-button">
                  <CheckCircle className="w-4 h-4 mr-2" />Confirm Order
                </Button>
              )}
              {order.status === 'confirmed' && (
                <Button className="w-full" onClick={updateDispatch} disabled={updating} data-testid="dispatch-order-button">
                  <Truck className="w-4 h-4 mr-2" />Mark Dispatched
                </Button>
              )}
              {order.status === 'dispatched' && (
                <Button className="w-full" onClick={() => updateOrderStatus('delivered')} disabled={updating} data-testid="deliver-order-button">
                  <CheckCircle className="w-4 h-4 mr-2" />Mark Delivered
                </Button>
              )}

              {/* Return Actions - Always visible for actionable statuses */}
              {!order.return_requested && (
                <Button variant="outline" className="w-full border-orange-300 text-orange-700 hover:bg-orange-50" onClick={() => setShowReturnModal(true)} data-testid="create-return-button">
                  <RefreshCcw className="w-4 h-4 mr-2" />Create Return Request
                </Button>
              )}
              {order.return_requested && !order.replacement_order_id && (
                <Button variant="outline" className="w-full border-orange-300 text-orange-700 hover:bg-orange-50" onClick={() => {
                  setReturnForm({ ...returnForm, return_reason: 'customer_changed_mind' });
                  setShowReturnModal(true);
                }} data-testid="create-replacement-button">
                  <RefreshCcw className="w-4 h-4 mr-2" />Request Replacement
                </Button>
              )}
              {order.return_requested && (
                <Button variant="outline" className="w-full" onClick={() => navigate('/returns')} data-testid="view-returns-button">
                  <AlertTriangle className="w-4 h-4 mr-2" />View Returns
                </Button>
              )}

              <Button variant="outline" className="w-full" onClick={() => setShowFinancialModal(true)} data-testid="calculate-financials-button">
                <DollarSign className="w-4 h-4 mr-2" />{financials ? 'Recalculate' : 'Calculate'} Financials
              </Button>
            </CardContent>
          </Card>

          {/* Communication Checklist - READ ONLY, green/red indicators */}
          <Card data-testid="communication-card">
            <CardHeader>
              <CardTitle className="font-[Manrope] text-sm">Communication Status</CardTitle>
              <p className="text-xs text-muted-foreground">Automated via WhatsApp CRM</p>
            </CardHeader>
            <CardContent className="space-y-2">
              {commChecklist.map(({ key, fallbackKey, label, dateKey }) => {
                const done = !!order[key] || (fallbackKey && !!order[fallbackKey]);
                const dateVal = dateKey ? order[dateKey] : null;
                return (
                  <div key={key} className="flex items-center justify-between text-sm" data-testid={`comm-${key}`}>
                    <div className="flex items-center gap-2">
                      <div className={`w-2.5 h-2.5 rounded-full ${done ? 'bg-green-500' : 'bg-red-400'}`} />
                      <span className={done ? 'text-foreground' : 'text-muted-foreground'}>{label}</span>
                    </div>
                    {dateVal && <span className="text-xs text-muted-foreground">{safeDateShort(dateVal)}</span>}
                    {!dateVal && <span className="text-xs text-muted-foreground">{done ? 'Done' : 'Pending'}</span>}
                  </div>
                );
              })}
              <div className="pt-2 border-t border-border/50 space-y-2 mt-2">
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Assembly Type</span>
                  <span className="font-medium">{order.assembly_type || 'Not set'}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Paid Assembly</span>
                  <Badge variant={order.paid_assembly ? 'default' : 'outline'} className="text-xs">{order.paid_assembly ? 'Yes' : 'No'}</Badge>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Return Status */}
          {order.return_requested && (
            <Card className="border-orange-200" data-testid="return-status-card">
              <CardHeader>
                <CardTitle className="font-[Manrope] flex items-center gap-2 text-orange-700">
                  <RefreshCcw className="w-5 h-5" />Return Info
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2 text-sm">
                <InfoField label="Reason" value={order.return_reason || '-'} />
                <InfoField label="Status" value={order.return_status || 'Requested'} />
                <InfoField label="Return Tracking" value={order.return_tracking_number || '-'} mono />
                {order.refund_amount && <InfoField label="Refund" value={`₹${order.refund_amount}`} />}
              </CardContent>
            </Card>
          )}

          {order.internal_notes && (
            <Card>
              <CardHeader><CardTitle className="font-[Manrope] flex items-center gap-2"><FileText className="w-5 h-5" />Internal Notes</CardTitle></CardHeader>
              <CardContent><p className="text-sm whitespace-pre-wrap">{order.internal_notes}</p></CardContent>
            </Card>
          )}

          <AutomationPanel orderId={id} />
        </div>
      </div>

      {/* ===== CREATE RETURN MODAL ===== */}
      {showReturnModal && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4" data-testid="return-modal">
          <Card className="w-full max-w-lg max-h-[90vh] overflow-y-auto">
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle className="font-[Manrope]">Create Return/Replacement Request</CardTitle>
              <Button variant="ghost" size="sm" onClick={() => setShowReturnModal(false)}><X className="w-4 h-4" /></Button>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleCreateReturn} className="space-y-4">
                <div>
                  <label className="text-xs font-medium text-muted-foreground">Request Type *</label>
                  <Select value={returnForm.return_type} onValueChange={v => setReturnForm({ ...returnForm, return_type: v })}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="return">Return (Refund)</SelectItem>
                      <SelectItem value="replacement">Replacement</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                
                <div>
                  <label className="text-xs font-medium text-muted-foreground">Return Reason *</label>
                  <Select value={returnForm.return_reason} onValueChange={v => setReturnForm({ ...returnForm, return_reason: v })}>
                    <SelectTrigger data-testid="return-reason-select"><SelectValue placeholder="Select reason" /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="PFC">PFC (Pre-Fulfillment Cancel)</SelectItem>
                      <SelectItem value="Delay">Delay</SelectItem>
                      <SelectItem value="Damage">Damage</SelectItem>
                      <SelectItem value="damaged and pending">Damaged and Pending</SelectItem>
                      <SelectItem value="damaged and replaced">Damaged and Replaced</SelectItem>
                      <SelectItem value="Hardware Missing">Hardware Missing</SelectItem>
                      <SelectItem value="Customer Issue">Customer Issue</SelectItem>
                      <SelectItem value="Fraud">Fraud</SelectItem>
                      <SelectItem value="cancelled and delivered">Cancelled and Delivered</SelectItem>
                      <SelectItem value="Status Pending">Status Pending</SelectItem>
                      <SelectItem value="Defective Product">Defective Product</SelectItem>
                      <SelectItem value="Damaged in Transit">Damaged in Transit</SelectItem>
                      <SelectItem value="Wrong Item Delivered">Wrong Item Delivered</SelectItem>
                      <SelectItem value="Not as Described">Not as Described</SelectItem>
                      <SelectItem value="Size Issue">Size Issue</SelectItem>
                      <SelectItem value="Quality Issue">Quality Issue</SelectItem>
                      <SelectItem value="Customer Changed Mind">Customer Changed Mind</SelectItem>
                      <SelectItem value="Delivery Delay">Delivery Delay</SelectItem>
                      <SelectItem value="Other">Other</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                
                <div>
                  <label className="text-xs font-medium text-muted-foreground">Damage Category</label>
                  <Select value={returnForm.damage_category} onValueChange={v => setReturnForm({ ...returnForm, damage_category: v })}>
                    <SelectTrigger><SelectValue placeholder="Select (optional)" /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="No Damage">No Damage</SelectItem>
                      <SelectItem value="Scratch">Scratch</SelectItem>
                      <SelectItem value="Crack">Crack</SelectItem>
                      <SelectItem value="Dent">Dent</SelectItem>
                      <SelectItem value="Broken">Broken</SelectItem>
                      <SelectItem value="Missing Parts">Missing Parts</SelectItem>
                      <SelectItem value="Packaging Damage">Packaging Damage</SelectItem>
                      <SelectItem value="Hardware Missing">Hardware Missing</SelectItem>
                      <SelectItem value="Parts Missing">Parts Missing</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                
                {returnForm.return_type === 'replacement' && (
                  <div>
                    <label className="text-xs font-medium text-muted-foreground">What needs to be replaced? *</label>
                    <Input 
                      value={returnForm.replacement_items}
                      onChange={e => setReturnForm({ ...returnForm, replacement_items: e.target.value })}
                      placeholder="e.g., Left door hinge, screws, etc."
                      required={returnForm.return_type === 'replacement'}
                    />
                  </div>
                )}
                
                <div>
                  <label className="text-xs font-medium text-muted-foreground">Details</label>
                  <Input value={returnForm.return_reason_details}
                    onChange={e => setReturnForm({ ...returnForm, return_reason_details: e.target.value })}
                    placeholder="Additional details..." data-testid="return-details-input" />
                </div>
                
                <label className="flex items-center gap-2 text-sm cursor-pointer">
                  <input type="checkbox" checked={returnForm.is_installation_related}
                    onChange={e => setReturnForm({ ...returnForm, is_installation_related: e.target.checked })} className="rounded border-input" />
                  Installation related issue
                </label>
                
                <div className="flex gap-3">
                  <Button type="button" variant="outline" onClick={() => setShowReturnModal(false)} className="flex-1">Cancel</Button>
                  <Button type="submit" className="flex-1" disabled={!returnForm.return_reason || (returnForm.return_type === 'replacement' && !returnForm.replacement_items)} data-testid="submit-return-btn">
                    Create {returnForm.return_type === 'replacement' ? 'Replacement' : 'Return'}
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>
        </div>
      )}

      {/* ===== FINANCIAL CALCULATION MODAL ===== */}
      {showFinancialModal && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4" data-testid="financial-modal">
          <Card className="w-full max-w-lg">
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle className="font-[Manrope]">Calculate Financials</CardTitle>
              <Button variant="ghost" size="sm" onClick={() => setShowFinancialModal(false)}><X className="w-4 h-4" /></Button>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleCalculateFinancials} className="space-y-4">
                <p className="text-sm text-muted-foreground">
                  Selling Price: <span className="font-medium text-foreground font-[JetBrains_Mono]">₹{order.price}</span>
                </p>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="text-xs font-medium text-muted-foreground">Product Cost *</label>
                    <Input type="number" step="0.01" required value={finForm.product_cost}
                      onChange={e => setFinForm({ ...finForm, product_cost: e.target.value })} placeholder="0.00" data-testid="input-product-cost" />
                  </div>
                  <div>
                    <label className="text-xs font-medium text-muted-foreground">Shipping Cost *</label>
                    <Input type="number" step="0.01" required value={finForm.shipping_cost}
                      onChange={e => setFinForm({ ...finForm, shipping_cost: e.target.value })} placeholder="0.00" />
                  </div>
                  <div>
                    <label className="text-xs font-medium text-muted-foreground">Packaging Cost</label>
                    <Input type="number" step="0.01" value={finForm.packaging_cost}
                      onChange={e => setFinForm({ ...finForm, packaging_cost: e.target.value })} placeholder="0.00" />
                  </div>
                  <div>
                    <label className="text-xs font-medium text-muted-foreground">Installation Cost</label>
                    <Input type="number" step="0.01" value={finForm.installation_cost}
                      onChange={e => setFinForm({ ...finForm, installation_cost: e.target.value })} placeholder="0.00" />
                  </div>
                  <div className="col-span-2">
                    <label className="text-xs font-medium text-muted-foreground">Commission Rate (%)</label>
                    <Input type="number" step="0.1" value={finForm.marketplace_commission_rate}
                      onChange={e => setFinForm({ ...finForm, marketplace_commission_rate: e.target.value })} placeholder="15" />
                  </div>
                </div>
                <div className="flex gap-3">
                  <Button type="button" variant="outline" onClick={() => setShowFinancialModal(false)} className="flex-1">Cancel</Button>
                  <Button type="submit" className="flex-1" data-testid="calculate-financials-submit">Calculate</Button>
                </div>
              </form>
            </CardContent>
          </Card>
        </div>
      )}

      {/* ===== EDIT ORDER MODAL ===== */}
      {showEditModal && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4" data-testid="edit-order-modal">
          <Card className="w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle className="font-[Manrope]">Edit Order</CardTitle>
              <Button variant="ghost" size="sm" onClick={() => setShowEditModal(false)}><X className="w-4 h-4" /></Button>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSaveEdit} className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-xs font-medium text-muted-foreground">Status</label>
                    <Select value={editForm.status} onValueChange={v => setEditForm({ ...editForm, status: v })}>
                      <SelectTrigger><SelectValue /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="pending">Pending</SelectItem>
                        <SelectItem value="confirmed">Confirmed</SelectItem>
                        <SelectItem value="dispatched">Dispatched</SelectItem>
                        <SelectItem value="delivered">Delivered</SelectItem>
                        <SelectItem value="cancelled">Cancelled</SelectItem>
                        <SelectItem value="returned">Returned</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <label className="text-xs font-medium text-muted-foreground">Tracking Number</label>
                    <Input value={editForm.tracking_number} onChange={e => setEditForm({ ...editForm, tracking_number: e.target.value })} placeholder="Tracking number" />
                  </div>
                  <div>
                    <label className="text-xs font-medium text-muted-foreground">Courier Partner</label>
                    <Input value={editForm.courier_partner} onChange={e => setEditForm({ ...editForm, courier_partner: e.target.value })} placeholder="Courier partner" />
                  </div>
                  <div>
                    <label className="text-xs font-medium text-muted-foreground">Customer Name</label>
                    <Input value={editForm.customer_name} onChange={e => setEditForm({ ...editForm, customer_name: e.target.value })} placeholder="Customer name" />
                  </div>
                  <div>
                    <label className="text-xs font-medium text-muted-foreground">Phone</label>
                    <Input value={editForm.phone} onChange={e => setEditForm({ ...editForm, phone: e.target.value })} placeholder="Phone" />
                  </div>
                  <div>
                    <label className="text-xs font-medium text-muted-foreground">Alternate Phone</label>
                    <Input value={editForm.phone_secondary} onChange={e => setEditForm({ ...editForm, phone_secondary: e.target.value })} placeholder="Alternate phone" />
                  </div>
                  <div className="col-span-2">
                    <label className="text-xs font-medium text-muted-foreground">Shipping Address</label>
                    <Input value={editForm.shipping_address} onChange={e => setEditForm({ ...editForm, shipping_address: e.target.value })} placeholder="Shipping address" />
                  </div>
                  <div>
                    <label className="text-xs font-medium text-muted-foreground">City</label>
                    <Input value={editForm.city} onChange={e => setEditForm({ ...editForm, city: e.target.value })} placeholder="City" />
                  </div>
                  <div>
                    <label className="text-xs font-medium text-muted-foreground">State</label>
                    <Input value={editForm.state} onChange={e => setEditForm({ ...editForm, state: e.target.value })} placeholder="State" />
                  </div>
                  <div>
                    <label className="text-xs font-medium text-muted-foreground">Pincode</label>
                    <Input value={editForm.pincode} onChange={e => setEditForm({ ...editForm, pincode: e.target.value })} placeholder="Pincode" />
                  </div>
                  <div className="col-span-2">
                    <label className="text-xs font-medium text-muted-foreground">Instructions</label>
                    <Input value={editForm.instructions} onChange={e => setEditForm({ ...editForm, instructions: e.target.value })} placeholder="Special instructions" />
                  </div>
                </div>
                <div className="flex gap-3">
                  <Button type="button" variant="outline" onClick={() => setShowEditModal(false)} className="flex-1">Cancel</Button>
                  <Button type="submit" className="flex-1" disabled={updating}>Save Changes</Button>
                </div>
              </form>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
};

const InfoField = ({ label, value, mono }) => (
  <div>
    <p className="text-xs text-muted-foreground">{label}</p>
    <p className={`text-sm font-medium ${mono ? 'font-[JetBrains_Mono]' : ''}`}>{value || '-'}</p>
  </div>
);

const TimelineItem = ({ label, date, active, warn }) => (
  <div className={`p-2 rounded-lg border text-center ${active ? (warn ? 'border-orange-200 bg-orange-50' : 'border-primary/20 bg-primary/5') : 'border-border/40 bg-muted/30 opacity-50'}`}>
    <p className="text-xs text-muted-foreground">{label}</p>
    <p className="text-sm font-medium">{date}</p>
  </div>
);

const FinBox = ({ label, value, sub, highlight, warn }) => (
  <div className={`p-2.5 rounded-lg text-center ${highlight ? 'bg-green-50 border border-green-200' : warn ? 'bg-red-50 border border-red-200' : sub ? 'bg-orange-50/50' : 'bg-secondary/40'}`}>
    <p className="text-xs text-muted-foreground">{label}</p>
    <p className={`text-sm font-bold font-[JetBrains_Mono] ${highlight ? 'text-green-700' : warn ? 'text-red-700' : ''}`}>{value}</p>
  </div>
);
