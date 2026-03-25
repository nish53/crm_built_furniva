import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api from '../lib/api';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { toast } from 'sonner';
import {
  ArrowLeft, RefreshCcw, User, Calendar, Truck,
  CheckCircle, XCircle, Clock, Package, Camera, Undo2,
  ChevronRight, AlertTriangle, FileText
} from 'lucide-react';
import { format } from 'date-fns';

// Return workflow stages in order
const WORKFLOW_STAGES = [
  { key: 'requested', label: 'Requested', icon: Clock },
  { key: 'approved', label: 'Approved', icon: CheckCircle },
  { key: 'pickup_scheduled', label: 'Pickup Scheduled', icon: Calendar },
  { key: 'in_transit', label: 'In Transit', icon: Truck },
  { key: 'received', label: 'Received', icon: Package },
  { key: 'inspected', label: 'Inspected', icon: FileText },
  { key: 'refunded', label: 'Refunded', icon: CheckCircle },
];

export const ReturnDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [returnReq, setReturnReq] = useState(null);
  const [loading, setLoading] = useState(true);
  const [updating, setUpdating] = useState(false);
  const [showAdvanceModal, setShowAdvanceModal] = useState(false);
  const [advanceForm, setAdvanceForm] = useState({
    pickup_date: '',
    tracking_number: '',
    courier_partner: '',
    notes: '',
    refund_amount: ''
  });

  useEffect(() => {
    fetchReturn();
  }, [id]);

  const fetchReturn = async () => {
    try {
      const res = await api.get(`/return-requests/${id}`);
      setReturnReq(res.data);
    } catch (err) {
      toast.error('Failed to fetch return request');
    } finally {
      setLoading(false);
    }
  };

  const getStageIndex = (status) => {
    const idx = WORKFLOW_STAGES.findIndex(s => s.key === status);
    return idx >= 0 ? idx : 0;
  };

  const getNextStatus = (currentStatus) => {
    const currentIdx = getStageIndex(currentStatus);
    if (currentIdx < WORKFLOW_STAGES.length - 1) {
      return WORKFLOW_STAGES[currentIdx + 1].key;
    }
    return null;
  };

  const handleAdvanceWorkflow = async () => {
    if (!returnReq) return;
    
    const nextStatus = getNextStatus(returnReq.return_status);
    if (!nextStatus) {
      toast.error('Return is already at final stage');
      return;
    }

    // Validate required fields based on next status
    if (nextStatus === 'pickup_scheduled' && !advanceForm.pickup_date) {
      toast.error('Pickup date is required');
      return;
    }
    if (nextStatus === 'in_transit' && !advanceForm.tracking_number) {
      toast.error('Tracking number is required');
      return;
    }

    setUpdating(true);
    try {
      const params = new URLSearchParams({ status: nextStatus });
      if (advanceForm.pickup_date) params.append('pickup_date', advanceForm.pickup_date);
      if (advanceForm.tracking_number) params.append('tracking_number', advanceForm.tracking_number);
      if (advanceForm.courier_partner) params.append('courier_partner', advanceForm.courier_partner);
      if (advanceForm.notes) params.append('notes', advanceForm.notes);
      if (advanceForm.refund_amount) params.append('refund_amount', advanceForm.refund_amount);

      await api.patch(`/return-requests/${id}/status?${params.toString()}`);
      toast.success(`Status updated to ${nextStatus.replace('_', ' ')}`);
      setShowAdvanceModal(false);
      setAdvanceForm({ pickup_date: '', tracking_number: '', courier_partner: '', notes: '', refund_amount: '' });
      fetchReturn();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to advance workflow');
    } finally {
      setUpdating(false);
    }
  };

  const handleUndo = async () => {
    if (!returnReq?.previous_status) {
      toast.error('No previous status to revert to');
      return;
    }
    setUpdating(true);
    try {
      await api.patch(`/return-requests/${id}/undo`);
      toast.success('Status reverted successfully');
      fetchReturn();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to undo status');
    } finally {
      setUpdating(false);
    }
  };

  const safeDate = (d) => {
    if (!d) return '-';
    try { return format(new Date(d), 'MMM dd, yyyy HH:mm'); }
    catch { return '-'; }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-[60vh]">
        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-primary" />
      </div>
    );
  }

  if (!returnReq) {
    return (
      <div className="text-center py-12">
        <p className="text-muted-foreground">Return request not found</p>
      </div>
    );
  }

  const currentStageIdx = getStageIndex(returnReq.return_status);
  const nextStatus = getNextStatus(returnReq.return_status);
  const isRejected = returnReq.return_status === 'rejected';
  const isClosed = returnReq.return_status === 'refunded' || returnReq.return_status === 'replaced';

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button variant="ghost" onClick={() => navigate('/returns')}>
          <ArrowLeft className="w-4 h-4 mr-2" />Back
        </Button>
        <div className="flex-1">
          <h1 className="text-2xl font-bold font-[Manrope] tracking-tight">
            Return #{returnReq.order_number}
          </h1>
          <p className="text-muted-foreground mt-1">Created {safeDate(returnReq.created_at)}</p>
        </div>
        <Badge 
          className={`text-sm px-3 py-1 ${
            isRejected ? 'bg-red-100 text-red-800' :
            isClosed ? 'bg-green-100 text-green-800' :
            'bg-blue-100 text-blue-800'
          }`}
        >
          {returnReq.return_status?.replace('_', ' ').toUpperCase()}
        </Badge>
      </div>

      {/* Visual Stepper */}
      <Card>
        <CardHeader>
          <CardTitle className="font-[Manrope] text-lg">Workflow Progress</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between overflow-x-auto pb-2">
            {WORKFLOW_STAGES.map((stage, idx) => {
              const Icon = stage.icon;
              const isCompleted = idx < currentStageIdx;
              const isCurrent = idx === currentStageIdx;
              const isPending = idx > currentStageIdx;

              return (
                <React.Fragment key={stage.key}>
                  <div className="flex flex-col items-center min-w-[80px]">
                    <div
                      className={`w-10 h-10 rounded-full flex items-center justify-center border-2 transition-colors ${
                        isCompleted ? 'bg-green-500 border-green-500 text-white' :
                        isCurrent ? 'bg-primary border-primary text-white' :
                        'bg-muted border-border text-muted-foreground'
                      }`}
                    >
                      {isCompleted ? <CheckCircle className="w-5 h-5" /> : <Icon className="w-5 h-5" />}
                    </div>
                    <span className={`text-xs mt-2 text-center ${
                      isCurrent ? 'font-medium text-foreground' : 'text-muted-foreground'
                    }`}>
                      {stage.label}
                    </span>
                  </div>
                  {idx < WORKFLOW_STAGES.length - 1 && (
                    <ChevronRight className={`w-5 h-5 mx-1 flex-shrink-0 ${
                      idx < currentStageIdx ? 'text-green-500' : 'text-muted-foreground/30'
                    }`} />
                  )}
                </React.Fragment>
              );
            })}
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Details */}
        <div className="lg:col-span-2 space-y-6">
          {/* Return Info */}
          <Card>
            <CardHeader>
              <CardTitle className="font-[Manrope] flex items-center gap-2">
                <RefreshCcw className="w-5 h-5" />Return Information
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4 text-sm">
                <InfoField label="Order Number" value={returnReq.order_number} mono />
                <InfoField label="Return Reason" value={returnReq.return_reason} />
                <InfoField label="Damage Category" value={returnReq.damage_category || '-'} />
                <InfoField label="Requested Date" value={safeDate(returnReq.requested_date)} />
                <InfoField label="Approved Date" value={safeDate(returnReq.approved_date)} />
                <InfoField label="Pickup Date" value={safeDate(returnReq.pickup_date)} />
                <InfoField label="Tracking Number" value={returnReq.return_tracking_number || '-'} mono />
                <InfoField label="Courier" value={returnReq.courier_partner || '-'} />
                <InfoField label="Received Date" value={safeDate(returnReq.received_date)} />
                <InfoField label="Inspection Date" value={safeDate(returnReq.inspection_date)} />
                <InfoField label="Refund Amount" value={returnReq.refund_amount ? `₹${returnReq.refund_amount}` : '-'} />
                <InfoField label="Refund Date" value={safeDate(returnReq.refund_date)} />
              </div>
              {returnReq.return_reason_details && (
                <div className="mt-4 p-3 bg-muted/50 rounded-lg">
                  <p className="text-xs text-muted-foreground mb-1">Details</p>
                  <p className="text-sm">{returnReq.return_reason_details}</p>
                </div>
              )}
              {returnReq.qc_notes && (
                <div className="mt-4 p-3 bg-orange-50 rounded-lg border border-orange-200">
                  <p className="text-xs text-orange-700 mb-1">QC Notes</p>
                  <p className="text-sm text-orange-900">{returnReq.qc_notes}</p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Customer Info */}
          <Card>
            <CardHeader>
              <CardTitle className="font-[Manrope] flex items-center gap-2">
                <User className="w-5 h-5" />Customer
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <InfoField label="Name" value={returnReq.customer_name} />
                <InfoField label="Phone" value={returnReq.phone} mono />
              </div>
            </CardContent>
          </Card>

          {/* Damage Images */}
          {returnReq.damage_images && returnReq.damage_images.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="font-[Manrope] flex items-center gap-2">
                  <Camera className="w-5 h-5" />Damage Images
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  {returnReq.damage_images.map((img, idx) => (
                    <a key={idx} href={img} target="_blank" rel="noopener noreferrer">
                      <img
                        src={img}
                        alt={`Damage ${idx + 1}`}
                        className="w-full h-32 object-cover rounded-lg border hover:opacity-80 transition-opacity"
                      />
                    </a>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Status History */}
          {returnReq.status_history && returnReq.status_history.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="font-[Manrope] flex items-center gap-2">
                  <Clock className="w-5 h-5" />Status History
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {returnReq.status_history.map((entry, idx) => (
                    <div key={idx} className="flex items-start gap-3 text-sm border-l-2 border-primary/20 pl-4 py-2">
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <span className="font-medium">
                            {entry.from_status?.replace('_', ' ')} → {entry.to_status?.replace('_', ' ')}
                          </span>
                          {entry.is_undo && <Badge variant="outline" className="text-xs">Undo</Badge>}
                        </div>
                        <p className="text-xs text-muted-foreground mt-0.5">
                          {safeDate(entry.changed_at)} by {entry.changed_by}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </div>

        {/* Right Column - Actions */}
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="font-[Manrope]">Actions</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {!isClosed && !isRejected && nextStatus && (
                <Button
                  className="w-full"
                  onClick={() => setShowAdvanceModal(true)}
                  disabled={updating}
                >
                  <ChevronRight className="w-4 h-4 mr-2" />
                  Advance to {nextStatus.replace('_', ' ')}
                </Button>
              )}
              
              {returnReq.previous_status && (
                <Button
                  variant="outline"
                  className="w-full"
                  onClick={handleUndo}
                  disabled={updating}
                >
                  <Undo2 className="w-4 h-4 mr-2" />Undo Last Change
                </Button>
              )}

              <Button
                variant="outline"
                className="w-full"
                onClick={() => navigate(`/orders/${returnReq.order_id}`)}
              >
                <Package className="w-4 h-4 mr-2" />View Order
              </Button>

              {isClosed && (
                <div className="p-3 bg-green-50 rounded-lg border border-green-200 text-center">
                  <CheckCircle className="w-6 h-6 text-green-600 mx-auto mb-1" />
                  <p className="text-sm font-medium text-green-800">Return Completed</p>
                </div>
              )}

              {isRejected && (
                <div className="p-3 bg-red-50 rounded-lg border border-red-200 text-center">
                  <XCircle className="w-6 h-6 text-red-600 mx-auto mb-1" />
                  <p className="text-sm font-medium text-red-800">Return Rejected</p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Quick Info */}
          <Card>
            <CardHeader>
              <CardTitle className="font-[Manrope] text-sm">Quick Info</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Installation Related</span>
                <Badge variant={returnReq.is_installation_related ? 'default' : 'outline'}>
                  {returnReq.is_installation_related ? 'Yes' : 'No'}
                </Badge>
              </div>
              {returnReq.batch_number && (
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Batch</span>
                  <span className="font-mono">{returnReq.batch_number}</span>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Advance Workflow Modal */}
      {showAdvanceModal && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <Card className="w-full max-w-md">
            <CardHeader>
              <CardTitle className="font-[Manrope]">
                Advance to: {nextStatus?.replace('_', ' ')}
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {nextStatus === 'pickup_scheduled' && (
                <div>
                  <label className="text-xs font-medium text-muted-foreground">Pickup Date *</label>
                  <Input
                    type="date"
                    value={advanceForm.pickup_date}
                    onChange={(e) => setAdvanceForm({ ...advanceForm, pickup_date: e.target.value })}
                  />
                </div>
              )}

              {nextStatus === 'in_transit' && (
                <>
                  <div>
                    <label className="text-xs font-medium text-muted-foreground">Tracking Number *</label>
                    <Input
                      value={advanceForm.tracking_number}
                      onChange={(e) => setAdvanceForm({ ...advanceForm, tracking_number: e.target.value })}
                      placeholder="Enter tracking number"
                    />
                  </div>
                  <div>
                    <label className="text-xs font-medium text-muted-foreground">Courier Partner</label>
                    <Input
                      value={advanceForm.courier_partner}
                      onChange={(e) => setAdvanceForm({ ...advanceForm, courier_partner: e.target.value })}
                      placeholder="Delhivery, BlueDart, etc."
                    />
                  </div>
                </>
              )}

              {nextStatus === 'refunded' && (
                <div>
                  <label className="text-xs font-medium text-muted-foreground">Refund Amount</label>
                  <Input
                    type="number"
                    step="0.01"
                    value={advanceForm.refund_amount}
                    onChange={(e) => setAdvanceForm({ ...advanceForm, refund_amount: e.target.value })}
                    placeholder="Enter refund amount"
                  />
                </div>
              )}

              <div>
                <label className="text-xs font-medium text-muted-foreground">Notes</label>
                <Input
                  value={advanceForm.notes}
                  onChange={(e) => setAdvanceForm({ ...advanceForm, notes: e.target.value })}
                  placeholder="Optional notes..."
                />
              </div>

              <div className="flex gap-3 pt-2">
                <Button
                  variant="outline"
                  className="flex-1"
                  onClick={() => setShowAdvanceModal(false)}
                >
                  Cancel
                </Button>
                <Button
                  className="flex-1"
                  onClick={handleAdvanceWorkflow}
                  disabled={updating}
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

const InfoField = ({ label, value, mono }) => (
  <div>
    <p className="text-xs text-muted-foreground">{label}</p>
    <p className={`text-sm font-medium ${mono ? 'font-[JetBrains_Mono]' : ''}`}>{value || '-'}</p>
  </div>
);
