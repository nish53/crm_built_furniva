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
  XCircle, AlertCircle, Phone, MapPin, Edit, Undo2, Calculator, History
} from 'lucide-react';
import { format } from 'date-fns';

export const OrderDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [order, setOrder] = useState(null);
  const [loading, setLoading] = useState(true);
  const [updating, setUpdating] = useState(false);
  const [showReturnModal, setShowReturnModal] = useState(false);
  const [showReplacementModal, setShowReplacementModal] = useState(false);
  const [showFinancialModal, setShowFinancialModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showCancelModal, setShowCancelModal] = useState(false);
  const [financials, setFinancials] = useState(null);
  const [editForm, setEditForm] = useState({});
  const [cancellationReason, setCancellationReason] = useState('');
  const [lossData, setLossData] = useState(null);
  const [loadingLoss, setLoadingLoss] = useState(false);
  const [editHistory, setEditHistory] = useState([]);
  const [showEditHistory, setShowEditHistory] = useState(false);
  const [returnRequest, setReturnRequest] = useState(null);
  const [replacementRequest, setReplacementRequest] = useState(null);

  const [returnForm, setReturnForm] = useState({
    return_reason: '',
    return_reason_details: '',
    damage_category: '',
    is_installation_related: false
  });

  const [replacementForm, setReplacementForm] = useState({
    replacement_reason: 'damaged',
    replacement_type: 'full_replacement',  // NEW: full or partial
    damage_description: '',
    damage_images: [],
    notes: '',  // NEW: additional notes
    difference_amount: ''  // NEW: for customer_change_of_mind upsell
  });

  const [finForm, setFinForm] = useState({
    product_cost: '', shipping_cost: '', packaging_cost: '',
    installation_cost: '', marketplace_commission_rate: '15'
  });

  useEffect(() => { fetchOrder(); fetchLossData(); fetchEditHistory(); fetchReturnReplacement(); }, [id]);

  const fetchOrder = async () => {
    try {
      const res = await api.get(`/orders/${id}`);
      setOrder(res.data);
      try { const fRes = await api.get(`/financials/order/${id}`); setFinancials(fRes.data); }
      catch { setFinancials(null); }
    } catch { toast.error('Failed to fetch order'); }
    finally { setLoading(false); }
  };

  const fetchLossData = async () => {
    try {
      // Loss data is stored directly on the order, so we just read from order
      // But we can also call the loss calculation endpoint if needed
    } catch (err) {
      console.error('Failed to fetch loss data');
    }
  };

  const fetchEditHistory = async () => {
    try {
      const res = await api.get(`/edit-history/order/${id}`);
      setEditHistory(res.data || []);
    } catch (err) {
      setEditHistory([]);
    }
  };

  const fetchReturnReplacement = async () => {
    try {
      // Fetch return request for this order
      const returnRes = await api.get(`/return-requests/?order_id=${id}`);
      if (returnRes.data && returnRes.data.length > 0) {
        setReturnRequest(returnRes.data[0]); // Get latest return request
      }
    } catch (err) {
      console.log('No return request found for this order');
    }
    
    try {
      // Fetch replacement request for this order
      const replaceRes = await api.get(`/replacement-requests/?order_id=${id}`);
      if (replaceRes.data && replaceRes.data.length > 0) {
        setReplacementRequest(replaceRes.data[0]); // Get latest replacement request
      }
    } catch (err) {
      console.log('No replacement request found for this order');
    }
  };

  const handleCalculateLoss = async () => {
    setLoadingLoss(true);
    try {
      const res = await api.post(`/loss/calculate/${id}`);
      setLossData(res.data);
      toast.success('Loss calculated successfully');
      fetchOrder(); // Refresh to get updated loss fields
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to calculate loss');
    } finally {
      setLoadingLoss(false);
    }
  };

  const handleUndoStatus = async () => {
    if (!order?.previous_status) {
      toast.error('No previous status to revert to');
      return;
    }
    setUpdating(true);
    try {
      await api.patch(`/orders/${id}/undo-status`);
      toast.success('Status reverted successfully');
      fetchOrder();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to undo status');
    } finally {
      setUpdating(false);
    }
  };

  const handleCancelOrder = async () => {
    if (!cancellationReason) {
      toast.error('Please select a cancellation reason');
      return;
    }
    setUpdating(true);
    try {
      // Create a return request instead of directly cancelling
      const params = new URLSearchParams({
        cancellation_reason: cancellationReason,
        notes: returnForm.return_reason_details || ''
      });
      
      await api.post(`/return-requests/?${params.toString()}`, {
        order_id: id,
        return_reason: cancellationReason,
        return_reason_details: returnForm.return_reason_details || null,
        damage_category: null,
        is_installation_related: false,
        damage_images: []
      });
      
      toast.success('Return request created - order will be cancelled after workflow completion');
      setShowCancelModal(false);
      setCancellationReason('');
      fetchOrder();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to create return request');
    } finally {
      setUpdating(false);
    }
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
      // NEW: Pass cancellation_reason and notes as query parameters
      const params = new URLSearchParams({
        cancellation_reason: returnForm.return_reason,
        notes: returnForm.return_reason_details || ''
      });
      
      await api.post(`/return-requests/?${params.toString()}`, {
        order_id: id,
        return_reason: returnForm.return_reason,
        return_reason_details: returnForm.return_reason_details || null,
        damage_category: returnForm.damage_category || null,
        is_installation_related: returnForm.is_installation_related,
        damage_images: []
      });
      toast.success('Return request created successfully');
      setShowReturnModal(false);
      setReturnForm({
        return_reason: '',
        return_reason_details: '',
        damage_category: '',
        is_installation_related: false
      });
      fetchOrder();
    } catch (err) { 
      // Handle validation errors properly
      let errorMsg = 'Failed to create return';
      if (err.response?.data?.detail) {
        if (Array.isArray(err.response.data.detail)) {
          errorMsg = err.response.data.detail.map(e => e.msg || e).join(', ');
        } else if (typeof err.response.data.detail === 'string') {
          errorMsg = err.response.data.detail;
        }
      }
      toast.error(errorMsg); 
    }
  };

  const handleCreateReplacement = async (e) => {
    e.preventDefault();
    
    // Only validate damage description and images for 'damaged' reason
    if (replacementForm.replacement_reason === 'damaged') {
      if (!replacementForm.damage_description.trim()) {
        toast.error('Please describe the damage');
        return;
      }
      if (!replacementForm.damage_images || replacementForm.damage_images.length === 0) {
        toast.error('Please upload at least one damage image');
        return;
      }
    }
    
    // Set default replacement_type for non-damaged/quality reasons
    let replacement_type = replacementForm.replacement_type || 'full_replacement';
    if (replacementForm.replacement_reason === 'wrong_product_sent' || replacementForm.replacement_reason === 'customer_change_of_mind') {
      replacement_type = 'full_replacement';
    }
    
    try {
      await api.post('/replacement-requests/', {
        order_id: id,
        replacement_reason: replacementForm.replacement_reason,
        replacement_type: replacement_type,
        damage_description: replacementForm.damage_description || 'N/A',
        damage_images: replacementForm.damage_images || [],
        notes: replacementForm.notes || null,
        difference_amount: replacementForm.difference_amount ? parseFloat(replacementForm.difference_amount) : null
      });
      toast.success('Replacement request created successfully');
      setShowReplacementModal(false);
      setReplacementForm({
        replacement_reason: 'damaged',
        replacement_type: 'full_replacement',
        damage_description: '',
        damage_images: [],
        notes: '',
        difference_amount: ''
      });
      fetchOrder();
    } catch (err) { 
      toast.error(err.response?.data?.detail || 'Failed to create replacement'); 
    }
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


          {/* Timeline - Order Lifecycle Only */}
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
                {order.status === 'cancelled' && (
                  <TimelineItem label="Cancelled" date={safeDateShort(order.cancelled_at)} active warn />
                )}
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


          {/* Unified Return/Replacement History Card - Single source of truth */}
          {(order.return_requested || order.replacement_requested || returnRequest || replacementRequest) && (
            <Card data-testid="order-history-card" className="border-amber-200 bg-gradient-to-br from-amber-50/50 to-orange-50/30">
              <CardHeader>
                <CardTitle className="font-[Manrope] flex items-center gap-2 text-amber-800">
                  <AlertTriangle className="w-5 h-5" />
                  Order History & Status
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Active Issues Summary */}
                <div className="flex flex-wrap gap-2">
                  {(order.return_requested || returnRequest) && (
                    <Badge className="bg-orange-600 text-white">
                      <RefreshCcw className="w-3 h-3 mr-1" />
                      RETURN {returnRequest?.return_status ? `• ${returnRequest.return_status.replace(/_/g, ' ')}` : ''}
                    </Badge>
                  )}
                  {(order.replacement_requested || replacementRequest) && (
                    <Badge className="bg-blue-600 text-white">
                      <Package className="w-3 h-3 mr-1" />
                      REPLACEMENT {replacementRequest?.replacement_status ? `• ${replacementRequest.replacement_status.replace(/_/g, ' ')}` : ''}
                    </Badge>
                  )}
                </div>

                {/* Return Milestones Section */}
                {(returnRequest || order.return_requested) && (
                  <div className="space-y-2">
                    <div className="flex items-center gap-2 text-sm font-medium text-orange-700 border-b border-orange-200 pb-1">
                      <RefreshCcw className="w-4 h-4" />
                      Return Timeline
                      {order.return_reason && (
                        <span className="text-xs font-normal text-orange-600 ml-auto">
                          Reason: {order.return_reason || order.cancellation_reason}
                        </span>
                      )}
                    </div>
                    <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                      <MilestoneItem 
                        label="Return Requested" 
                        date={safeDateShort(returnRequest?.requested_date || order.return_date)} 
                        active={!!(returnRequest?.requested_date || order.return_date)}
                        type="return"
                      />
                      <MilestoneItem 
                        label="RTO Initiated" 
                        date={safeDateShort(returnRequest?.return_initiated_date || order.rto_initiated_date)} 
                        active={!!(returnRequest?.return_initiated_date || order.rto_initiated_date)}
                        type="return"
                      />
                      <MilestoneItem 
                        label="Warehouse Received" 
                        date={safeDateShort(returnRequest?.warehouse_received_date || order.rto_warehouse_received_date)} 
                        active={!!(returnRequest?.warehouse_received_date || order.rto_warehouse_received_date)}
                        type="return"
                      />
                      <MilestoneItem 
                        label="Condition Checked" 
                        date={returnRequest?.qc_condition ? `✓ ${returnRequest.qc_condition}` : safeDateShort(returnRequest?.qc_inspection_date)} 
                        active={!!(returnRequest?.qc_inspection_date || returnRequest?.qc_condition || order.rto_received_condition)}
                        type="return"
                      />
                      <MilestoneItem 
                        label="Refund Processed" 
                        date={returnRequest?.refund_processed_amount ? `₹${returnRequest.refund_processed_amount}` : safeDateShort(returnRequest?.refund_processed_date || order.refund_date)} 
                        active={!!(returnRequest?.refund_processed_date || order.refund_date)}
                        type="return"
                        highlight
                      />
                      <MilestoneItem 
                        label="Return Closed" 
                        date={safeDateShort(returnRequest?.closed_date)} 
                        active={returnRequest?.return_status === 'closed'}
                        type="return"
                        highlight
                      />
                    </div>
                    {returnRequest && (
                      <Button
                        variant="outline"
                        size="sm"
                        className="w-full mt-2 border-orange-300 text-orange-700 hover:bg-orange-50"
                        onClick={() => navigate(`/returns/${returnRequest.id}`)}
                      >
                        View Full Return Details →
                      </Button>
                    )}
                  </div>
                )}

                {/* Replacement Milestones Section */}
                {(replacementRequest || order.replacement_requested) && (
                  <div className="space-y-2">
                    <div className="flex items-center gap-2 text-sm font-medium text-blue-700 border-b border-blue-200 pb-1">
                      <Package className="w-4 h-4" />
                      Replacement Timeline
                      {(order.replacement_reason || replacementRequest?.replacement_reason) && (
                        <span className="text-xs font-normal text-blue-600 ml-auto">
                          Reason: {replacementRequest?.replacement_reason || order.replacement_reason}
                        </span>
                      )}
                    </div>
                    
                    {/* Pickup Track */}
                    <p className="text-xs text-muted-foreground font-medium">🔄 Old Product Pickup</p>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                      <MilestoneItem 
                        label="Pickup Approved" 
                        date={safeDateShort(replacementRequest?.pickup_approved_date)} 
                        active={replacementRequest?.pickup_approved}
                        type="replacement"
                      />
                      <MilestoneItem 
                        label="Old Item Picked Up" 
                        date={replacementRequest?.pickup_tracking_id ? `${safeDateShort(replacementRequest?.pickup_date)} • ${replacementRequest.pickup_tracking_id}` : safeDateShort(replacementRequest?.pickup_date)} 
                        active={!!replacementRequest?.pickup_date || !!replacementRequest?.pickup_tracking_id}
                        type="replacement"
                      />
                      <MilestoneItem 
                        label="Warehouse Received" 
                        date={safeDateShort(replacementRequest?.warehouse_received_date)} 
                        active={!!replacementRequest?.warehouse_received_date}
                        type="replacement"
                      />
                      <MilestoneItem 
                        label="Condition Checked" 
                        date={replacementRequest?.received_condition ? `✓ ${replacementRequest.received_condition}` : '-'} 
                        active={!!replacementRequest?.received_condition}
                        type="replacement"
                      />
                    </div>

                    {/* Shipment Track */}
                    <p className="text-xs text-muted-foreground font-medium mt-2">📦 New Product Shipment</p>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                      <MilestoneItem 
                        label="Replacement Approved" 
                        date={safeDateShort(replacementRequest?.replacement_approved_date)} 
                        active={replacementRequest?.replacement_approved}
                        type="replacement"
                      />
                      <MilestoneItem 
                        label="Replacement Shipped" 
                        date={replacementRequest?.new_tracking_id ? `${safeDateShort(replacementRequest?.ship_date)} • ${replacementRequest.new_tracking_id}` : safeDateShort(replacementRequest?.ship_date)} 
                        active={!!replacementRequest?.ship_date || !!replacementRequest?.new_tracking_id}
                        type="replacement"
                        highlight
                      />
                      <MilestoneItem 
                        label="Delivered" 
                        date={safeDateShort(replacementRequest?.delivered_date)} 
                        active={!!replacementRequest?.delivered_date}
                        type="replacement"
                        highlight
                      />
                      <MilestoneItem 
                        label="Resolved" 
                        date={safeDateShort(replacementRequest?.resolved_date)} 
                        active={replacementRequest?.replacement_status === 'resolved'}
                        type="replacement"
                        highlight
                      />
                    </div>

                    {replacementRequest && (
                      <Button
                        variant="outline"
                        size="sm"
                        className="w-full mt-2 border-blue-300 text-blue-700 hover:bg-blue-50"
                        onClick={() => navigate(`/replacements/${replacementRequest.id}`)}
                      >
                        View Full Replacement Details →
                      </Button>
                    )}
                  </div>
                )}
              </CardContent>
            </Card>
          )}


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
              
              {/* Undo Status Button - shows when previous_status exists */}
              {order.previous_status && (
                <Button 
                  variant="outline" 
                  className="w-full border-yellow-300 text-yellow-700 hover:bg-yellow-50" 
                  onClick={handleUndoStatus} 
                  disabled={updating}
                  data-testid="undo-status-button"
                >
                  <Undo2 className="w-4 h-4 mr-2" />Undo Status (Revert to {order.previous_status})
                </Button>
              )}
              
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

              {/* CONTEXT-DEPENDENT ACTION BUTTONS BASED ON ORDER STATUS */}
              
              {/* PRE-DISPATCH: Cancel Order button (for pending/confirmed orders) */}
              {(order.status === 'pending' || order.status === 'confirmed') && !order.return_requested && !order.cancelled_at && (
                <Button 
                  variant="outline" 
                  className="w-full border-red-300 text-red-700 hover:bg-red-50" 
                  onClick={() => setShowCancelModal(true)} 
                  disabled={updating}
                  data-testid="cancel-order-button"
                >
                  <XCircle className="w-4 h-4 mr-2" />Cancel Order (Pre-Dispatch)
                </Button>
              )}

              {/* IN-TRANSIT: Cancel/RTO button (for dispatched/in_transit/out_for_delivery orders) */}
              {(order.status === 'dispatched' || order.status === 'in_transit' || order.status === 'out_for_delivery') && !order.return_requested && !order.cancelled_at && (
                <Button 
                  variant="outline" 
                  className="w-full border-orange-300 text-orange-700 hover:bg-orange-50" 
                  onClick={() => setShowCancelModal(true)} 
                  disabled={updating}
                  data-testid="cancel-rto-button"
                >
                  <XCircle className="w-4 h-4 mr-2" />Cancel / RTO (In-Transit)
                </Button>
              )}

              {/* POST-DELIVERY: Return Request button */}
              {order.status === 'delivered' && !order.return_requested && !order.replacement_requested && (
                <Button 
                  variant="outline" 
                  className="w-full border-orange-300 text-orange-700 hover:bg-orange-50" 
                  onClick={() => setShowReturnModal(true)} 
                  disabled={updating}
                  data-testid="create-return-button"
                >
                  <RefreshCcw className="w-4 h-4 mr-2" />Create Return Request
                </Button>
              )}

              {/* POST-DELIVERY: Replacement Request button */}
              {order.status === 'delivered' && !order.return_requested && !order.replacement_requested && (
                <Button 
                  variant="outline" 
                  className="w-full border-blue-300 text-blue-700 hover:bg-blue-50" 
                  onClick={() => setShowReplacementModal(true)} 
                  disabled={updating}
                  data-testid="create-replacement-button"
                >
                  <Package className="w-4 h-4 mr-2" />Create Replacement Request
                </Button>
              )}

              {order.return_requested && (
                <div className="space-y-2">
                  <Badge variant="outline" className="text-orange-600 border-orange-400">Return Requested</Badge>
                  <Button variant="outline" className="w-full" onClick={() => navigate('/returns')} data-testid="view-returns-button">
                    <AlertTriangle className="w-4 h-4 mr-2" />View Returns
                  </Button>
                </div>
              )}
              {order.replacement_requested && (
                <Badge variant="outline" className="text-blue-600 border-blue-400">Replacement Requested</Badge>
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

          {/* Loss Calculation Card */}
          {(order.status === 'cancelled' || order.status === 'returned' || order.return_requested || order.loss_category) && (
            <Card data-testid="loss-calculation-card">
              <CardHeader>
                <CardTitle className="font-[Manrope] flex items-center gap-2 text-sm">
                  <Calculator className="w-4 h-4" />Loss Calculation
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {order.loss_category ? (
                  <>
                    <div className="flex justify-between items-center">
                      <span className="text-xs text-muted-foreground">Category</span>
                      <Badge className={`text-xs ${
                        order.loss_category === 'pfc' ? 'bg-green-100 text-green-800' :
                        order.loss_category === 'resolved' ? 'bg-yellow-100 text-yellow-800' :
                        order.loss_category === 'refunded' ? 'bg-orange-100 text-orange-800' :
                        order.loss_category === 'fraud' ? 'bg-red-100 text-red-800' :
                        'bg-gray-100 text-gray-800'
                      }`}>
                        {order.loss_category?.toUpperCase()}
                      </Badge>
                    </div>
                    <div className="grid grid-cols-2 gap-2 text-sm">
                      <div>
                        <p className="text-xs text-muted-foreground">Outbound Logistics</p>
                        <p className="font-medium font-[JetBrains_Mono]">₹{order.logistics_cost_outbound || 0}</p>
                      </div>
                      <div>
                        <p className="text-xs text-muted-foreground">Return Logistics</p>
                        <p className="font-medium font-[JetBrains_Mono]">₹{order.logistics_cost_return || 0}</p>
                      </div>
                      <div>
                        <p className="text-xs text-muted-foreground">Product Cost</p>
                        <p className="font-medium font-[JetBrains_Mono]">₹{order.product_cost || 0}</p>
                      </div>
                      <div>
                        <p className="text-xs text-muted-foreground">Replacement Parts</p>
                        <p className="font-medium font-[JetBrains_Mono]">₹{order.replacement_parts_cost || 0}</p>
                      </div>
                    </div>
                    <div className="pt-2 border-t">
                      <div className="flex justify-between items-center">
                        <span className="font-medium">Total Loss</span>
                        <span className="font-bold text-red-600 font-[JetBrains_Mono]">₹{order.total_loss || 0}</span>
                      </div>
                      <p className="text-xs text-muted-foreground mt-1">
                        {order.loss_calculation_method === 'manual' ? 'Manually edited' : 'Auto-calculated'}
                        {order.loss_edited_by && ` by ${order.loss_edited_by}`}
                      </p>
                    </div>
                  </>
                ) : (
                  <p className="text-xs text-muted-foreground text-center py-2">
                    Loss not calculated yet
                  </p>
                )}
                <Button 
                  variant="outline" 
                  size="sm" 
                  className="w-full" 
                  onClick={handleCalculateLoss}
                  disabled={loadingLoss}
                >
                  <Calculator className="w-3 h-3 mr-2" />
                  {loadingLoss ? 'Calculating...' : (order.loss_category ? 'Recalculate' : 'Calculate Loss')}
                </Button>
              </CardContent>
            </Card>
          )}

          {/* Edit History Card */}
          {editHistory.length > 0 && (
            <Card data-testid="edit-history-card">
              <CardHeader className="cursor-pointer" onClick={() => setShowEditHistory(!showEditHistory)}>
                <CardTitle className="font-[Manrope] flex items-center justify-between text-sm">
                  <div className="flex items-center gap-2">
                    <History className="w-4 h-4" />Edit History
                  </div>
                  <Badge variant="outline" className="text-xs">{editHistory.length} changes</Badge>
                </CardTitle>
              </CardHeader>
              {showEditHistory && (
                <CardContent className="space-y-3 max-h-64 overflow-y-auto">
                  {editHistory.slice(0, 10).map((entry, idx) => (
                    <div key={idx} className="text-xs border-l-2 border-primary/20 pl-3 py-1">
                      <p className="text-muted-foreground">
                        {safeDate(entry.edited_at)} by {entry.edited_by}
                      </p>
                      <div className="mt-1 space-y-1">
                        {entry.changes?.map((change, cIdx) => (
                          <div key={cIdx} className="flex gap-2">
                            <span className="font-medium">{change.field_name}:</span>
                            <span className="text-red-600 line-through">{String(change.old_value || '-')}</span>
                            <span>→</span>
                            <span className="text-green-600">{String(change.new_value || '-')}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </CardContent>
              )}
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

      {/* ===== CREATE RETURN MODAL (POST-DELIVERY ONLY) ===== */}
      {showReturnModal && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4" data-testid="return-modal">
          <Card className="w-full max-w-lg max-h-[90vh] overflow-y-auto">
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle className="font-[Manrope]">Create Return Request (Post-Delivery)</CardTitle>
              <Button variant="ghost" size="sm" onClick={() => setShowReturnModal(false)}><X className="w-4 h-4" /></Button>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleCreateReturn} className="space-y-4">
                <div className="bg-blue-50 p-3 rounded-md border border-blue-200 mb-4">
                  <p className="text-xs text-blue-800">
                    Order has been delivered. Select return reason for post-delivery return.
                  </p>
                </div>

                <div>
                  <label className="text-xs font-medium text-muted-foreground">Return Reason *</label>
                  <Select value={returnForm.return_reason} onValueChange={v => setReturnForm({ ...returnForm, return_reason: v })}>
                    <SelectTrigger data-testid="return-reason-select"><SelectValue placeholder="Select reason" /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="damage">Damage</SelectItem>
                      <SelectItem value="customer_issues_except_quality">Customer Issues (Except Quality)</SelectItem>
                      <SelectItem value="hardware_missing">Hardware Missing</SelectItem>
                      <SelectItem value="defective_product">Defective Product</SelectItem>
                      <SelectItem value="fraud_customer">Fraud Customer</SelectItem>
                      <SelectItem value="wrong_product_sent">Wrong Product Sent</SelectItem>
                      <SelectItem value="customer_quality_issues">Customer Quality Issues</SelectItem>
                      <SelectItem value="product_delayed_customer_accepted">Product Delayed & Customer Accepted</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                
                {/* DAMAGE CATEGORY - ONLY SHOW IF DAMAGE REASON SELECTED */}
                {returnForm.return_reason === 'damage' && (
                  <div>
                    <label className="text-xs font-medium text-muted-foreground">Damage Category (Optional)</label>
                    <Select value={returnForm.damage_category} onValueChange={v => setReturnForm({ ...returnForm, damage_category: v })}>
                      <SelectTrigger><SelectValue placeholder="Select if applicable" /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="Dent">Dent</SelectItem>
                        <SelectItem value="Broken">Broken</SelectItem>
                        <SelectItem value="Scratches">Scratches</SelectItem>
                        <SelectItem value="Crack">Crack</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                )}
                
                <div>
                  <label className="text-xs font-medium text-muted-foreground">Additional Notes (Optional)</label>
                  <Input value={returnForm.return_reason_details}
                    onChange={e => setReturnForm({ ...returnForm, return_reason_details: e.target.value })}
                    placeholder="Add any additional details..." data-testid="return-details-input" />
                </div>
                
                <label className="flex items-center gap-2 text-sm cursor-pointer">
                  <input type="checkbox" checked={returnForm.is_installation_related}
                    onChange={e => setReturnForm({ ...returnForm, is_installation_related: e.target.checked })} className="rounded border-input" />
                  Installation related issue
                </label>
                
                <div className="flex gap-3">
                  <Button type="button" variant="outline" onClick={() => setShowReturnModal(false)} className="flex-1">Cancel</Button>
                  <Button type="submit" className="flex-1" disabled={!returnForm.return_reason} data-testid="submit-return-btn">
                    Create Return
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


      {/* ===== REPLACEMENT REQUEST MODAL ===== */}
      {showReplacementModal && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4" data-testid="replacement-modal">
          <Card className="w-full max-w-lg max-h-[90vh] overflow-y-auto">
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle className="font-[Manrope] flex items-center gap-2">
                <Package className="w-5 h-5 text-blue-600" />
                Create Replacement Request
              </CardTitle>
              <Button variant="ghost" size="sm" onClick={() => setShowReplacementModal(false)}><X className="w-4 h-4" /></Button>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleCreateReplacement} className="space-y-4">
                <div>
                  <label className="text-xs font-medium text-muted-foreground">Replacement Reason *</label>
                  <Select value={replacementForm.replacement_reason} onValueChange={v => setReplacementForm({ ...replacementForm, replacement_reason: v })}>
                    <SelectTrigger data-testid="replacement-reason-select"><SelectValue placeholder="Select reason" /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="damaged">Damaged</SelectItem>
                      <SelectItem value="quality">Quality</SelectItem>
                      <SelectItem value="wrong_product_sent">Wrong Product Sent</SelectItem>
                      <SelectItem value="customer_change_of_mind">Customer Change of Mind</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                
                {/* REPLACEMENT TYPE SELECTION (Full or Partial) */}
                {(replacementForm.replacement_reason === 'damaged' || replacementForm.replacement_reason === 'quality') && (
                  <div>
                    <label className="text-xs font-medium text-muted-foreground">Replacement Type *</label>
                    <Select value={replacementForm.replacement_type} onValueChange={v => setReplacementForm({ ...replacementForm, replacement_type: v })}>
                      <SelectTrigger data-testid="replacement-type-select"><SelectValue placeholder="Select type" /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="full_replacement">Full Replacement</SelectItem>
                        <SelectItem value="partial_replacement">Partial Replacement (Parts Only)</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                )}
                
                {/* DIFFERENCE AMOUNT FOR CUSTOMER CHANGE OF MIND (UPSELL) */}
                {replacementForm.replacement_reason === 'customer_change_of_mind' && (
                  <div>
                    <label className="text-xs font-medium text-muted-foreground">Difference Amount (₹) *</label>
                    <Input 
                      type="number" 
                      step="0.01"
                      value={replacementForm.difference_amount || ''}
                      onChange={e => setReplacementForm({ ...replacementForm, difference_amount: e.target.value })}
                      placeholder="Enter amount if upselling, or 0"
                      required
                    />
                    <p className="text-xs text-muted-foreground mt-1">Enter difference amount if customer is upgrading to a higher-priced product</p>
                  </div>
                )}
                
                {/* DAMAGE DESCRIPTION AND IMAGES - ONLY FOR 'damaged' REASON */}
                {replacementForm.replacement_reason === 'damaged' && (
                  <>
                    <div>
                      <label className="text-xs font-medium text-muted-foreground">What is damaged? Describe in detail *</label>
                      <textarea 
                        value={replacementForm.damage_description}
                        onChange={e => setReplacementForm({ ...replacementForm, damage_description: e.target.value })}
                        placeholder="Example: Left door hinge is broken, screw holes are stripped, glass shelf has crack on corner..."
                        className="w-full min-h-[100px] p-2 border rounded-md"
                        required
                        data-testid="damage-description-input"
                      />
                    </div>
                    
                    <div>
                      <label className="text-xs font-medium text-muted-foreground">Upload Images * (at least 1 required)</label>
                      <input 
                        type="file" 
                        accept="image/*" 
                        multiple
                        onChange={(e) => {
                          const files = Array.from(e.target.files);
                          const fileUrls = files.map(f => f.name);
                          setReplacementForm({ ...replacementForm, damage_images: fileUrls });
                        }}
                        className="w-full p-2 border rounded-md"
                        data-testid="damage-images-input"
                      />
                      <p className="text-xs text-muted-foreground mt-1">
                        {replacementForm.damage_images.length > 0 ? `${replacementForm.damage_images.length} image(s) selected` : 'No images selected'}
                      </p>
                    </div>
                  </>
                )}
                
                {/* NOTES FIELD */}
                <div>
                  <label className="text-xs font-medium text-muted-foreground">Additional Notes (Optional)</label>
                  <Input 
                    value={replacementForm.notes}
                    onChange={e => setReplacementForm({ ...replacementForm, notes: e.target.value })}
                    placeholder="Any additional information..."
                  />
                </div>
                
                <div className="bg-blue-50 p-3 rounded-md">
                  <p className="text-sm text-blue-800 font-medium">Replacement Workflow:</p>
                  <ol className="text-xs text-blue-700 mt-2 space-y-1 list-decimal list-inside">
                    <li>Replacement Pending</li>
                    <li>Priority Review</li>
                    <li>Ship Replacement</li>
                    <li>Tracking Added</li>
                    <li>Delivered</li>
                    <li>Issue Resolved</li>
                  </ol>
                </div>
                
                <div className="flex gap-3">
                  <Button type="button" variant="outline" onClick={() => setShowReplacementModal(false)} className="flex-1">Cancel</Button>
                  <Button 
                    type="submit" 
                    className="flex-1 bg-blue-600 hover:bg-blue-700" 
                    disabled={!replacementForm.replacement_reason}
                    data-testid="submit-replacement-btn"
                  >
                    Create Replacement Request
                  </Button>
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

      {/* ===== CANCEL ORDER MODAL (CONTEXT-DEPENDENT REASONS) ===== */}
      {showCancelModal && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4" data-testid="cancel-order-modal">
          <Card className="w-full max-w-md">
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle className="font-[Manrope] text-red-700 flex items-center gap-2">
                <XCircle className="w-5 h-5" />
                {order?.status === 'pending' || order?.status === 'confirmed' 
                  ? 'Cancel Order (Pre-Dispatch)' 
                  : 'Cancel / RTO (In-Transit)'}
              </CardTitle>
              <Button variant="ghost" size="sm" onClick={() => { setShowCancelModal(false); setCancellationReason(''); }}><X className="w-4 h-4" /></Button>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="bg-red-50 p-3 rounded-md border border-red-200">
                <p className="text-sm text-red-800">
                  <span className="font-medium">Order:</span> {order?.order_number}
                </p>
                <p className="text-xs text-red-600 mt-1">
                  {order?.status === 'pending' || order?.status === 'confirmed'
                    ? 'Order has not been dispatched yet. Select pre-dispatch cancellation reason.'
                    : 'Order is in transit. This will create an RTO (Return to Origin) request.'}
                </p>
              </div>
              
              <div>
                <label className="text-xs font-medium text-muted-foreground">Cancellation Reason *</label>
                <Select value={cancellationReason} onValueChange={setCancellationReason}>
                  <SelectTrigger data-testid="cancellation-reason-select">
                    <SelectValue placeholder="Select a reason" />
                  </SelectTrigger>
                  <SelectContent>
                    {/* PRE-DISPATCH REASONS */}
                    {(order?.status === 'pending' || order?.status === 'confirmed') && (
                      <>
                        <SelectItem value="change_of_mind">Change of Mind</SelectItem>
                        <SelectItem value="found_better_pricing">Found Better Pricing</SelectItem>
                        <SelectItem value="ordered_mistakenly">Ordered Mistakenly</SelectItem>
                        <SelectItem value="wants_to_customize">Wants to Customize</SelectItem>
                        <SelectItem value="did_not_specify">Did Not Specify</SelectItem>
                        <SelectItem value="customer_not_available">Customer not Available</SelectItem>
                      </>
                    )}
                    
                    {/* IN-TRANSIT REASONS */}
                    {(order?.status === 'dispatched' || order?.status === 'in_transit' || order?.status === 'out_for_delivery') && (
                      <>
                        <SelectItem value="customer_refused_doorstep">Customer Refused at Doorstep</SelectItem>
                        <SelectItem value="customer_unavailable">Customer Unavailable</SelectItem>
                        <SelectItem value="delay">Delay</SelectItem>
                      </>
                    )}
                  </SelectContent>
                </Select>
              </div>
              
              {/* NOTES FIELD */}
              <div>
                <label className="text-xs font-medium text-muted-foreground">Additional Notes (Optional)</label>
                <Input 
                  placeholder="Add any additional details..." 
                  value={returnForm.return_reason_details}
                  onChange={e => setReturnForm({ ...returnForm, return_reason_details: e.target.value })}
                />
              </div>
              
              <div className="flex gap-3">
                <Button type="button" variant="outline" onClick={() => { setShowCancelModal(false); setCancellationReason(''); }} className="flex-1">
                  Back
                </Button>
                <Button 
                  onClick={handleCancelOrder} 
                  className="flex-1 bg-red-600 hover:bg-red-700" 
                  disabled={!cancellationReason || updating}
                  data-testid="confirm-cancel-btn"
                >
                  {updating ? 'Cancelling...' : 'Confirm Cancel'}
                </Button>
              </div>
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

const MilestoneItem = ({ label, date, active, type, highlight }) => {
  // Different colors for return (orange) vs replacement (blue)
  const getStyles = () => {
    if (!active) {
      return 'border-gray-200 bg-gray-50/50 opacity-50';
    }
    if (highlight && active) {
      return type === 'return' 
        ? 'border-green-300 bg-green-50 ring-2 ring-green-200' 
        : 'border-green-300 bg-green-50 ring-2 ring-green-200';
    }
    return type === 'return'
      ? 'border-orange-200 bg-orange-50'
      : 'border-blue-200 bg-blue-50';
  };

  const getTextColor = () => {
    if (!active) return 'text-gray-400';
    if (highlight) return 'text-green-700 font-semibold';
    return type === 'return' ? 'text-orange-800' : 'text-blue-800';
  };

  return (
    <div className={`p-2.5 rounded-lg border text-center transition-all ${getStyles()}`}>
      <p className="text-xs text-muted-foreground mb-0.5">{label}</p>
      <p className={`text-sm font-medium ${getTextColor()}`}>
        {active ? (date || '✓') : '-'}
      </p>
    </div>
  );
};
