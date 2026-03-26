import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api from '../lib/api';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { toast } from 'sonner';
import {
  ArrowLeft, Package, User, Calendar, Truck,
  CheckCircle, XCircle, Clock, ChevronRight, Box, Undo2, ShieldCheck
} from 'lucide-react';

// Replacement Workflow - DUAL TIMELINE STAGES
const PICKUP_STAGES = [
  { key: 'pickup_scheduled', label: 'Pickup Scheduled', icon: Clock },
  { key: 'picked_up', label: 'Picked Up', icon: Truck },
  { key: 'pickup_in_transit', label: 'In Transit', icon: Truck },
  { key: 'warehouse_received', label: 'Warehouse', icon: Package },
  { key: 'condition_checked', label: 'Condition Check', icon: CheckCircle }
];

const SHIPMENT_STAGES = [
  { key: 'approved', label: 'Approved', icon: CheckCircle },
  { key: 'new_shipment_dispatched', label: 'Dispatched', icon: Truck },
  { key: 'parts_shipped', label: 'Parts Shipped', icon: Box },
  { key: 'delivered', label: 'Delivered', icon: CheckCircle },
  { key: 'resolved', label: 'Resolved', icon: XCircle }
];

const statusColors = {
  requested: 'bg-blue-100 text-blue-800',
  approved: 'bg-green-100 text-green-800',
  rejected: 'bg-red-100 text-red-800',
  picked_up: 'bg-blue-100 text-blue-800',
  pickup_in_transit: 'bg-orange-100 text-orange-800',
  pickup_not_required: 'bg-gray-100 text-gray-800',
  warehouse_received: 'bg-teal-100 text-teal-800',
  new_shipment_dispatched: 'bg-orange-100 text-orange-800',
  parts_shipped: 'bg-yellow-100 text-yellow-800',
  delivered: 'bg-green-100 text-green-800',
  resolved: 'bg-gray-100 text-gray-800'
};

export const ReplacementDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [replacement, setReplacement] = useState(null);
  const [loading, setLoading] = useState(true);
  const [updating, setUpdating] = useState(false);
  const [showAdvanceModal, setShowAdvanceModal] = useState(false);
  const [selectedNextStatus, setSelectedNextStatus] = useState('');
  const [advanceForm, setAdvanceForm] = useState({
    notes: '',
    // Pickup fields
    pickup_date: '',
    pickup_tracking_id: '',
    pickup_courier: '',
    pickup_not_required: false,
    // Warehouse fields
    warehouse_received_date: '',
    received_condition: '',
    condition_notes: '',
    // New shipment fields
    new_tracking_id: '',
    new_courier: '',
    items_sent_description: '',
    // Parts fields (partial replacement)
    parts_description: '',
    parts_tracking_id: '',
    parts_courier: '',
    // Delivery
    delivered_date: '',
    delivery_confirmed: false
  });

  useEffect(() => {
    fetchReplacement();
  }, [id]);

  const fetchReplacement = async () => {
    try {
      const res = await api.get(`/replacement-requests/${id}`);
      setReplacement(res.data);
    } catch (err) {
      toast.error('Failed to load replacement request');
    } finally {
      setLoading(false);
    }
  };

  const handleAdvanceWorkflow = async () => {
    if (!selectedNextStatus) {
      toast.error('Please select next status');
      return;
    }

    setUpdating(true);
    try {
      const params = new URLSearchParams({
        next_status: selectedNextStatus,
        ...Object.fromEntries(
          Object.entries(advanceForm).filter(([_, v]) => v !== '' && v !== false)
        )
      });

      await api.patch(`/replacement-requests/${id}/advance?${params.toString()}`);
      toast.success('Replacement workflow advanced successfully');
      setShowAdvanceModal(false);
      setSelectedNextStatus('');
      setAdvanceForm({
        notes: '',
        pickup_date: '',
        pickup_tracking_id: '',
        pickup_courier: '',
        pickup_not_required: false,
        warehouse_received_date: '',
        received_condition: '',
        condition_notes: '',
        new_tracking_id: '',
        new_courier: '',
        items_sent_description: '',
        parts_description: '',
        parts_tracking_id: '',
        parts_courier: '',
        delivered_date: '',
        delivery_confirmed: false
      });
      fetchReplacement();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to advance workflow');
    } finally {
      setUpdating(false);
    }
  };

  // Bug #3: Undo functionality
  const handleUndo = async () => {
    if (!window.confirm('Are you sure you want to undo the last status change?')) {
      return;
    }
    
    setUpdating(true);
    try {
      await api.patch(`/replacement-requests/${id}/undo`);
      toast.success('Status undone successfully');
      fetchReplacement();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to undo status');
    } finally {
      setUpdating(false);
    }
  };

  // Bug #6: Dual Approval - Approve Pickup
  const handleApprovePickup = async () => {
    setUpdating(true);
    try {
      await api.patch(`/replacement-requests/${id}/approve-pickup`);
      toast.success('Pickup approved successfully');
      fetchReplacement();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to approve pickup');
    } finally {
      setUpdating(false);
    }
  };

  // Bug #6: Dual Approval - Approve Replacement
  const handleApproveReplacement = async () => {
    setUpdating(true);
    try {
      await api.patch(`/replacement-requests/${id}/approve-replacement`);
      toast.success('Replacement shipment approved successfully');
      fetchReplacement();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to approve replacement');
    } finally {
      setUpdating(false);
    }
  };

  const getCurrentStageIndex = () => {
    if (!replacement) return 0;
    // This is kept for backward compatibility but not used in dual timeline
    return 0;
  };

  const getPickupProgress = () => {
    if (!replacement) return -1;
    const pickupStatuses = ['pickup_scheduled', 'picked_up', 'pickup_in_transit', 'warehouse_received', 'condition_checked'];
    return pickupStatuses.indexOf(replacement.replacement_status);
  };

  const getShipmentProgress = () => {
    if (!replacement) return -1;
    // Match the SHIPMENT_STAGES array exactly (no 'requested')
    const shipmentStatuses = ['approved', 'new_shipment_dispatched', 'parts_shipped', 'delivered', 'resolved'];
    return shipmentStatuses.indexOf(replacement.replacement_status);
  };

  const isPickupPhase = () => {
    if (!replacement) return false;
    const pickupStatuses = ['pickup_scheduled', 'picked_up', 'pickup_in_transit', 'warehouse_received', 'condition_checked'];
    return pickupStatuses.includes(replacement.replacement_status);
  };

  const isShipmentPhase = () => {
    if (!replacement) return false;
    const shipmentStatuses = ['requested', 'approved', 'new_shipment_dispatched', 'parts_shipped', 'delivered', 'resolved'];
    return shipmentStatuses.includes(replacement.replacement_status);
  };

  const formatDate = (dateString) => {
    if (!dateString) return '-';
    return new Date(dateString).toLocaleDateString('en-IN', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <Package className="w-8 h-8 animate-spin mx-auto mb-2 text-primary" />
          <p className="text-muted-foreground">Loading replacement details...</p>
        </div>
      </div>
    );
  }

  if (!replacement) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <XCircle className="w-12 h-12 text-red-500 mx-auto mb-2" />
          <p className="text-muted-foreground">Replacement request not found</p>
        </div>
      </div>
    );
  }

  const currentStageIndex = getCurrentStageIndex();

  return (
    <div className="space-y-6 pb-12">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="sm" onClick={() => navigate('/replacements')}>
            <ArrowLeft className="w-4 h-4 mr-2" />Back to Replacements
          </Button>
          <div>
            <h1 className="text-3xl font-bold font-[Manrope] flex items-center gap-3">
              <Package className="w-8 h-8 text-blue-600" />
              Replacement Request #{replacement.id?.slice(0, 8)}
            </h1>
            <p className="text-muted-foreground mt-1">
              {replacement.replacement_type === 'full_replacement' ? 'Full Replacement' : 'Partial Replacement'}
            </p>
          </div>
        </div>
        <Badge className={`${statusColors[replacement.replacement_status]} text-lg px-4 py-2`}>
          {replacement.replacement_status?.replace(/_/g, ' ').toUpperCase()}
        </Badge>
      </div>

      {/* Dual Timeline Workflow Progress */}
      <Card>
        <CardHeader>
          <CardTitle className="font-[Manrope]">Replacement Workflow - Dual Timeline</CardTitle>
          <p className="text-sm text-muted-foreground mt-1">
            Two parallel processes: Old product pickup & New product shipment
          </p>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Track 1: Old Product Pickup */}
          <div className="border-l-4 border-orange-400 pl-4">
            <h3 className="font-semibold text-orange-700 mb-3 flex items-center gap-2">
              <Package className="w-5 h-5" />
              Track 1: Old Product Return
            </h3>
            <div className="flex items-center gap-2 overflow-x-auto pb-2">
              {PICKUP_STAGES.map((stage, index) => {
                const Icon = stage.icon;
                const pickupIndex = getPickupProgress();
                const isCompleted = pickupIndex >= index && pickupIndex !== -1;
                const isCurrent = pickupIndex === index;

                return (
                  <React.Fragment key={stage.key}>
                    <div className="flex flex-col items-center min-w-[80px]">
                      <div
                        className={`w-10 h-10 rounded-full flex items-center justify-center ${
                          isCompleted
                            ? 'bg-orange-500 text-white'
                            : isCurrent
                            ? 'bg-orange-400 text-white ring-2 ring-orange-300'
                            : 'bg-gray-200 text-gray-400'
                        }`}
                      >
                        <Icon className="w-5 h-5" />
                      </div>
                      <span className={`text-xs mt-1 text-center ${isCurrent ? 'font-bold text-orange-700' : ''}`}>
                        {stage.label}
                      </span>
                    </div>
                    {index < PICKUP_STAGES.length - 1 && (
                      <ChevronRight
                        className={`w-5 h-5 flex-shrink-0 ${isCompleted ? 'text-orange-500' : 'text-gray-300'}`}
                      />
                    )}
                  </React.Fragment>
                );
              })}
            </div>
            {replacement.pickup_tracking_id && (
              <div className="mt-3 bg-orange-50 p-2 rounded text-sm">
                <span className="font-medium">Pickup Tracking:</span> {replacement.pickup_tracking_id}
                {replacement.pickup_courier && ` • ${replacement.pickup_courier}`}
              </div>
            )}
          </div>

          {/* Track 2: New Product Shipment */}
          <div className="border-l-4 border-green-400 pl-4">
            <h3 className="font-semibold text-green-700 mb-3 flex items-center gap-2">
              <Truck className="w-5 h-5" />
              Track 2: Replacement Shipment
            </h3>
            <div className="flex items-center gap-2 overflow-x-auto pb-2">
              {SHIPMENT_STAGES.map((stage, index) => {
                const Icon = stage.icon;
                const shipmentIndex = getShipmentProgress();
                const isCompleted = shipmentIndex >= index && shipmentIndex !== -1;
                const isCurrent = shipmentIndex === index;

                return (
                  <React.Fragment key={stage.key}>
                    <div className="flex flex-col items-center min-w-[80px]">
                      <div
                        className={`w-10 h-10 rounded-full flex items-center justify-center ${
                          isCompleted
                            ? 'bg-green-500 text-white'
                            : isCurrent
                            ? 'bg-green-400 text-white ring-2 ring-green-300'
                            : 'bg-gray-200 text-gray-400'
                        }`}
                      >
                        <Icon className="w-5 h-5" />
                      </div>
                      <span className={`text-xs mt-1 text-center ${isCurrent ? 'font-bold text-green-700' : ''}`}>
                        {stage.label}
                      </span>
                    </div>
                    {index < SHIPMENT_STAGES.length - 1 && (
                      <ChevronRight
                        className={`w-5 h-5 flex-shrink-0 ${isCompleted ? 'text-green-500' : 'text-gray-300'}`}
                      />
                    )}
                  </React.Fragment>
                );
              })}
            </div>
            {replacement.new_tracking_id && (
              <div className="mt-3 bg-green-50 p-2 rounded text-sm">
                <span className="font-medium">Shipment Tracking:</span> {replacement.new_tracking_id}
                {replacement.new_courier && ` • ${replacement.new_courier}`}
              </div>
            )}
            {replacement.parts_tracking_id && (
              <div className="mt-2 bg-green-50 p-2 rounded text-sm">
                <span className="font-medium">Parts Tracking:</span> {replacement.parts_tracking_id}
                {replacement.parts_courier && ` • ${replacement.parts_courier}`}
              </div>
            )}
          </div>

          {/* Action Buttons - Bug #3 Undo and Bug #6 Dual Approval */}
          <div className="flex flex-wrap gap-3 mt-4">
            {/* Advance Workflow Button */}
            {replacement.replacement_status !== 'resolved' && replacement.replacement_status !== 'rejected' && (
              <Button onClick={() => setShowAdvanceModal(true)} className="flex-1">
                Advance Workflow
              </Button>
            )}
            
            {/* Undo Button - Bug #3 */}
            {replacement.previous_status && (
              <Button 
                variant="outline" 
                onClick={handleUndo}
                disabled={updating}
                className="flex items-center gap-2"
              >
                <Undo2 className="w-4 h-4" />
                Undo to {replacement.previous_status}
              </Button>
            )}
          </div>

          {/* Dual Approval Section - Bug #6 */}
          {replacement.replacement_status === 'requested' && (
            <div className="mt-4 p-4 bg-blue-50 rounded-lg border border-blue-200">
              <h4 className="font-semibold text-blue-800 mb-3 flex items-center gap-2">
                <ShieldCheck className="w-5 h-5" />
                Dual Approval Required
              </h4>
              <div className="grid grid-cols-2 gap-4">
                {/* Pickup Approval */}
                <div className="p-3 bg-white rounded border">
                  <p className="text-sm font-medium mb-2">Pickup Approval</p>
                  <p className="text-xs text-muted-foreground mb-3">
                    Approve collection of old/damaged product from customer
                  </p>
                  {replacement.pickup_approved ? (
                    <Badge className="bg-green-100 text-green-800">
                      <CheckCircle className="w-3 h-3 mr-1" />
                      Approved by {replacement.pickup_approved_by}
                    </Badge>
                  ) : (
                    <Button 
                      size="sm" 
                      variant="outline"
                      onClick={handleApprovePickup}
                      disabled={updating}
                      className="w-full"
                    >
                      Approve Pickup
                    </Button>
                  )}
                </div>
                
                {/* Replacement Approval */}
                <div className="p-3 bg-white rounded border">
                  <p className="text-sm font-medium mb-2">Replacement Approval</p>
                  <p className="text-xs text-muted-foreground mb-3">
                    Approve sending new replacement product to customer
                  </p>
                  {replacement.replacement_approved ? (
                    <Badge className="bg-green-100 text-green-800">
                      <CheckCircle className="w-3 h-3 mr-1" />
                      Approved by {replacement.replacement_approved_by}
                    </Badge>
                  ) : (
                    <Button 
                      size="sm" 
                      variant="outline"
                      onClick={handleApproveReplacement}
                      disabled={updating}
                      className="w-full"
                    >
                      Approve Replacement
                    </Button>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Show approval status for non-requested states */}
          {replacement.replacement_status !== 'requested' && (replacement.pickup_approved || replacement.replacement_approved) && (
            <div className="mt-4 flex gap-4">
              {replacement.pickup_approved && (
                <Badge variant="outline" className="text-green-700">
                  <CheckCircle className="w-3 h-3 mr-1" />
                  Pickup Approved
                </Badge>
              )}
              {replacement.replacement_approved && (
                <Badge variant="outline" className="text-green-700">
                  <CheckCircle className="w-3 h-3 mr-1" />
                  Replacement Approved
                </Badge>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Order Details */}
      <Card>
        <CardHeader><CardTitle className="font-[Manrope]">Order Details</CardTitle></CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <span className="text-muted-foreground">Order Number:</span>
              <p className="font-[JetBrains_Mono] font-medium">{replacement.order_number}</p>
            </div>
            <div>
              <span className="text-muted-foreground">Customer:</span>
              <p className="font-medium">{replacement.customer_name}</p>
            </div>
            <div>
              <span className="text-muted-foreground">Phone:</span>
              <p className="font-[JetBrains_Mono]">{replacement.phone}</p>
            </div>
            <div>
              <span className="text-muted-foreground">Requested Date:</span>
              <p>{formatDate(replacement.requested_date)}</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Replacement Information */}
      <Card>
        <CardHeader><CardTitle className="font-[Manrope]">Replacement Information</CardTitle></CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div>
              <span className="text-muted-foreground">Replacement Type:</span>
              <Badge className="ml-2">
                {replacement.replacement_type === 'full_replacement' ? 'FULL REPLACEMENT' : 'PARTIAL REPLACEMENT'}
              </Badge>
            </div>
            <div>
              <span className="text-muted-foreground">Reason:</span>
              <p className="font-medium capitalize">{replacement.replacement_reason?.replace(/_/g, ' ') || '-'}</p>
            </div>
            {replacement.difference_amount && replacement.difference_amount > 0 && (
              <div>
                <span className="text-muted-foreground">Difference Amount:</span>
                <p className="font-[JetBrains_Mono] font-medium text-lg">₹{replacement.difference_amount}</p>
                <p className="text-xs text-muted-foreground">Customer upgrading to higher-priced product</p>
              </div>
            )}
            {replacement.damage_description && (
              <div>
                <span className="text-muted-foreground">Description:</span>
                <p className="mt-1 p-3 bg-gray-50 rounded-md">{replacement.damage_description}</p>
              </div>
            )}
            {replacement.notes && (
              <div>
                <span className="text-muted-foreground">Notes:</span>
                <p className="mt-1 p-3 bg-gray-50 rounded-md">{replacement.notes}</p>
              </div>
            )}
            {replacement.damage_images && replacement.damage_images.length > 0 && (
              <div>
                <span className="text-muted-foreground">Images:</span>
                <div className="mt-2 flex gap-2">
                  {replacement.damage_images.map((img, idx) => (
                    <Badge key={idx} variant="outline" className="text-xs">
                      Image {idx + 1}
                    </Badge>
                  ))}
                </div>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Pickup Information (if applicable) */}
      {(replacement.pickup_tracking_id || replacement.pickup_not_required) && (
        <Card>
          <CardHeader><CardTitle className="font-[Manrope]">Pickup Information</CardTitle></CardHeader>
          <CardContent>
            {replacement.pickup_not_required ? (
              <Badge variant="outline" className="text-gray-600">Pickup Not Required</Badge>
            ) : (
              <div className="space-y-3">
                {replacement.pickup_tracking_id && (
                  <div>
                    <span className="text-muted-foreground">Pickup Tracking:</span>
                    <p className="font-[JetBrains_Mono] font-medium">{replacement.pickup_tracking_id}</p>
                    {replacement.pickup_courier && (
                      <p className="text-sm text-muted-foreground">Courier: {replacement.pickup_courier}</p>
                    )}
                  </div>
                )}
                {replacement.pickup_date && (
                  <div>
                    <span className="text-muted-foreground">Pickup Date:</span>
                    <p>{formatDate(replacement.pickup_date)}</p>
                  </div>
                )}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* New Shipment / Parts Information */}
      {(replacement.new_tracking_id || replacement.parts_tracking_id) && (
        <Card>
          <CardHeader>
            <CardTitle className="font-[Manrope]">
              {replacement.replacement_type === 'partial_replacement' ? 'Parts Shipment' : 'New Product Shipment'}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {replacement.new_tracking_id && (
                <div>
                  <span className="text-muted-foreground">Tracking Number:</span>
                  <p className="font-[JetBrains_Mono] font-medium">{replacement.new_tracking_id}</p>
                  {replacement.new_courier && (
                    <p className="text-sm text-muted-foreground">Courier: {replacement.new_courier}</p>
                  )}
                </div>
              )}
              {replacement.parts_tracking_id && (
                <div>
                  <span className="text-muted-foreground">Parts Tracking:</span>
                  <p className="font-[JetBrains_Mono] font-medium">{replacement.parts_tracking_id}</p>
                  {replacement.parts_courier && (
                    <p className="text-sm text-muted-foreground">Courier: {replacement.parts_courier}</p>
                  )}
                </div>
              )}
              {replacement.items_sent_description && (
                <div>
                  <span className="text-muted-foreground">Items Sent:</span>
                  <p className="mt-1 p-3 bg-gray-50 rounded-md">{replacement.items_sent_description}</p>
                </div>
              )}
              {replacement.parts_description && (
                <div>
                  <span className="text-muted-foreground">Parts Description:</span>
                  <p className="mt-1 p-3 bg-gray-50 rounded-md">{replacement.parts_description}</p>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Advance Workflow Modal */}
      {showAdvanceModal && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <Card className="w-full max-w-lg max-h-[90vh] overflow-y-auto">
            <CardHeader>
              <CardTitle className="font-[Manrope]">Advance Workflow</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="text-sm font-medium">Select Next Status *</label>
                <select
                  value={selectedNextStatus}
                  onChange={e => setSelectedNextStatus(e.target.value)}
                  className="w-full p-2 border rounded-md mt-1"
                >
                  <option value="">-- Select --</option>
                  <option value="approved">Approved</option>
                  <option value="rejected">Rejected</option>
                  <option value="picked_up">Picked Up</option>
                  <option value="pickup_not_required">Pickup Not Required</option>
                  <option value="warehouse_received">Warehouse Received</option>
                  <option value="new_shipment_dispatched">New Shipment Dispatched</option>
                  <option value="parts_shipped">Parts Shipped</option>
                  <option value="delivered">Delivered</option>
                  <option value="resolved">Resolved</option>
                </select>
              </div>

              {/* Context-specific fields */}
              {selectedNextStatus === 'picked_up' && (
                <>
                  <div>
                    <label className="text-sm font-medium">Pickup Date</label>
                    <Input
                      type="date"
                      value={advanceForm.pickup_date}
                      onChange={e => setAdvanceForm({ ...advanceForm, pickup_date: e.target.value })}
                    />
                  </div>
                  <div>
                    <label className="text-sm font-medium">Pickup Tracking ID</label>
                    <Input
                      value={advanceForm.pickup_tracking_id}
                      onChange={e => setAdvanceForm({ ...advanceForm, pickup_tracking_id: e.target.value })}
                      placeholder="Enter tracking ID"
                    />
                  </div>
                  <div>
                    <label className="text-sm font-medium">Pickup Courier</label>
                    <Input
                      value={advanceForm.pickup_courier}
                      onChange={e => setAdvanceForm({ ...advanceForm, pickup_courier: e.target.value })}
                      placeholder="e.g., Blue Dart, Delhivery"
                    />
                  </div>
                </>
              )}

              {selectedNextStatus === 'warehouse_received' && (
                <>
                  <div>
                    <label className="text-sm font-medium">Received Condition</label>
                    <select
                      value={advanceForm.received_condition}
                      onChange={e => setAdvanceForm({ ...advanceForm, received_condition: e.target.value })}
                      className="w-full p-2 border rounded-md mt-1"
                    >
                      <option value="">-- Select --</option>
                      <option value="mint">Mint Condition</option>
                      <option value="damaged">Damaged Condition</option>
                    </select>
                  </div>
                  <div>
                    <label className="text-sm font-medium">Condition Notes</label>
                    <textarea
                      value={advanceForm.condition_notes}
                      onChange={e => setAdvanceForm({ ...advanceForm, condition_notes: e.target.value })}
                      placeholder="Describe the condition..."
                      className="w-full p-2 border rounded-md mt-1 min-h-[80px]"
                    />
                  </div>
                </>
              )}

              {selectedNextStatus === 'new_shipment_dispatched' && (
                <>
                  <div>
                    <label className="text-sm font-medium">New Tracking ID *</label>
                    <Input
                      value={advanceForm.new_tracking_id}
                      onChange={e => setAdvanceForm({ ...advanceForm, new_tracking_id: e.target.value })}
                      placeholder="Enter tracking ID"
                    />
                  </div>
                  <div>
                    <label className="text-sm font-medium">Courier</label>
                    <Input
                      value={advanceForm.new_courier}
                      onChange={e => setAdvanceForm({ ...advanceForm, new_courier: e.target.value })}
                      placeholder="e.g., Blue Dart, Delhivery"
                    />
                  </div>
                  <div>
                    <label className="text-sm font-medium">Items Being Sent</label>
                    <textarea
                      value={advanceForm.items_sent_description}
                      onChange={e => setAdvanceForm({ ...advanceForm, items_sent_description: e.target.value })}
                      placeholder="Describe what's being sent..."
                      className="w-full p-2 border rounded-md mt-1 min-h-[80px]"
                    />
                  </div>
                </>
              )}

              {selectedNextStatus === 'parts_shipped' && (
                <>
                  <div>
                    <label className="text-sm font-medium">Parts Tracking ID *</label>
                    <Input
                      value={advanceForm.parts_tracking_id}
                      onChange={e => setAdvanceForm({ ...advanceForm, parts_tracking_id: e.target.value })}
                      placeholder="Enter tracking ID"
                    />
                  </div>
                  <div>
                    <label className="text-sm font-medium">Parts Courier</label>
                    <Input
                      value={advanceForm.parts_courier}
                      onChange={e => setAdvanceForm({ ...advanceForm, parts_courier: e.target.value })}
                      placeholder="e.g., Blue Dart, Delhivery"
                    />
                  </div>
                  <div>
                    <label className="text-sm font-medium">Parts Description</label>
                    <textarea
                      value={advanceForm.parts_description}
                      onChange={e => setAdvanceForm({ ...advanceForm, parts_description: e.target.value })}
                      placeholder="Describe the parts being sent..."
                      className="w-full p-2 border rounded-md mt-1 min-h-[80px]"
                    />
                  </div>
                </>
              )}

              <div>
                <label className="text-sm font-medium">Notes (Optional)</label>
                <textarea
                  value={advanceForm.notes}
                  onChange={e => setAdvanceForm({ ...advanceForm, notes: e.target.value })}
                  placeholder="Add any additional notes..."
                  className="w-full p-2 border rounded-md mt-1 min-h-[60px]"
                />
              </div>

              <div className="flex gap-3">
                <Button
                  variant="outline"
                  onClick={() => {
                    setShowAdvanceModal(false);
                    setSelectedNextStatus('');
                  }}
                  className="flex-1"
                >
                  Cancel
                </Button>
                <Button
                  onClick={handleAdvanceWorkflow}
                  disabled={!selectedNextStatus || updating}
                  className="flex-1"
                >
                  {updating ? 'Updating...' : 'Advance'}
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
};

export default ReplacementDetail;
