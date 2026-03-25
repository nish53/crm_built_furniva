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
  ChevronRight, AlertTriangle, FileText, Search, DollarSign,
  ShieldCheck, Warehouse, ClipboardCheck, FileCheck, Lock
} from 'lucide-react';
import { format } from 'date-fns';

// Full 12-stage return workflow
const WORKFLOW_STAGES = [
  { key: 'requested', label: 'Requested', icon: Clock },
  { key: 'feedback_check', label: 'Feedback Check', icon: Search },
  { key: 'claim_filed', label: 'Claim Filed', icon: FileText },
  { key: 'authorized', label: 'Authorized', icon: ShieldCheck },
  { key: 'return_initiated', label: 'Return Initiated', icon: RefreshCcw },
  { key: 'in_transit', label: 'In Transit', icon: Truck },
  { key: 'warehouse_received', label: 'Warehouse', icon: Warehouse },
  { key: 'qc_inspection', label: 'QC Inspection', icon: ClipboardCheck },
  { key: 'claim_filing', label: 'Claim Filing', icon: FileCheck },
  { key: 'claim_status', label: 'Claim Status', icon: FileText },
  { key: 'refund_processed', label: 'Refund', icon: DollarSign },
  { key: 'closed', label: 'Closed', icon: Lock },
];

// Terminal statuses that stop the workflow
const TERMINAL_STATUSES = ['closed', 'rejected', 'cancelled'];

// Status color map
const statusColors = {
  requested: 'bg-blue-100 text-blue-800',
  feedback_check: 'bg-purple-100 text-purple-800',
  claim_filed: 'bg-indigo-100 text-indigo-800',
  authorized: 'bg-teal-100 text-teal-800',
  return_initiated: 'bg-cyan-100 text-cyan-800',
  in_transit: 'bg-orange-100 text-orange-800',
  warehouse_received: 'bg-amber-100 text-amber-800',
  qc_inspection: 'bg-yellow-100 text-yellow-800',
  claim_filing: 'bg-lime-100 text-lime-800',
  claim_status: 'bg-emerald-100 text-emerald-800',
  refund_processed: 'bg-green-100 text-green-800',
  closed: 'bg-gray-100 text-gray-800',
  rejected: 'bg-red-100 text-red-800',
  cancelled: 'bg-red-100 text-red-800',
  // Legacy
  approved: 'bg-green-100 text-green-800',
  pickup_scheduled: 'bg-blue-100 text-blue-800',
  received: 'bg-teal-100 text-teal-800',
  inspected: 'bg-yellow-100 text-yellow-800',
  refunded: 'bg-green-100 text-green-800',
  replaced: 'bg-green-100 text-green-800',
};

export const ReturnDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [returnReq, setReturnReq] = useState(null);
  const [loading, setLoading] = useState(true);
  const [updating, setUpdating] = useState(false);
  const [showAdvanceModal, setShowAdvanceModal] = useState(false);
  const [allowedTransitions, setAllowedTransitions] = useState([]);
  const [selectedNextStatus, setSelectedNextStatus] = useState('');
  const [advanceForm, setAdvanceForm] = useState({
    tracking_number: '',
    courier_partner: '',
    notes: '',
    refund_amount: '',
    pickup_date: '',
    feedback_outcome: '',
    claim_reference: '',
    claim_platform: '',
    claim_amount: '',
    return_method: '',
    qc_result: '',
    qc_damage_found: '',
    claim_status_result: '',
    claim_approved_amount: '',
    refund_method: '',
    refund_transaction_id: '',
    resolution_summary: ''
  });

  useEffect(() => {
    fetchReturn();
  }, [id]);

  const fetchReturn = async () => {
    try {
      const res = await api.get(`/return-requests/${id}`);
      setReturnReq(res.data);
      // Also fetch allowed transitions
      try {
        const stagesRes = await api.get(`/return-requests/${id}/workflow-stages`);
        setAllowedTransitions(stagesRes.data.allowed_transitions || []);
      } catch (e) {
        // May fail if endpoint doesn't exist yet - fallback
        setAllowedTransitions([]);
      }
    } catch (err) {
      toast.error('Failed to fetch return request');
    } finally {
      setLoading(false);
    }
  };

  const getStageIndex = (status) => {
    const idx = WORKFLOW_STAGES.findIndex(s => s.key === status);
    return idx >= 0 ? idx : -1;
  };

  const handleAdvanceWorkflow = async () => {
    if (!returnReq || !selectedNextStatus) {
      toast.error('Please select next status');
      return;
    }

    // Validate required fields
    if (selectedNextStatus === 'in_transit' && !advanceForm.tracking_number) {
      toast.error('Tracking number is required');
      return;
    }

    setUpdating(true);
    try {
      const params = new URLSearchParams({ next_status: selectedNextStatus });
      
      // Add all non-empty form fields
      Object.entries(advanceForm).forEach(([key, val]) => {
        if (val && val.toString().trim()) {
          params.append(key, val);
        }
      });

      await api.patch(`/return-requests/${id}/workflow/advance?${params.toString()}`);
      toast.success(`Status advanced to ${selectedNextStatus.replace(/_/g, ' ')}`);
      setShowAdvanceModal(false);
      setSelectedNextStatus('');
      resetAdvanceForm();
      fetchReturn();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to advance workflow');
    } finally {
      setUpdating(false);
    }
  };

  const resetAdvanceForm = () => {
    setAdvanceForm({
      tracking_number: '', courier_partner: '', notes: '', refund_amount: '',
      pickup_date: '', feedback_outcome: '', claim_reference: '', claim_platform: '',
      claim_amount: '', return_method: '', qc_result: '', qc_damage_found: '',
      claim_status_result: '', claim_approved_amount: '', refund_method: '',
      refund_transaction_id: '', resolution_summary: ''
    });
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

  const handleQcImageUpload = async (e) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    const formData = new FormData();
    Array.from(files).forEach(f => formData.append('files', f));

    try {
      const res = await api.post('/uploads/damage-images/bulk', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      const urls = res.data.uploaded.map(u => u.url);
      if (urls.length > 0) {
        await api.patch(`/return-requests/${id}/qc-images`, urls);
        toast.success(`${urls.length} QC images uploaded`);
        fetchReturn();
      }
    } catch (err) {
      toast.error('Failed to upload QC images');
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
  const isTerminal = TERMINAL_STATUSES.includes(returnReq.return_status);
  const canAdvance = allowedTransitions.length > 0 && !isTerminal;

  // Render stage-specific form fields in the advance modal
  const renderStageFields = () => {
    if (!selectedNextStatus) return null;

    switch (selectedNextStatus) {
      case 'feedback_check':
        return (
          <>
            <div>
              <label className="text-xs font-medium text-muted-foreground">Feedback Outcome</label>
              <Select value={advanceForm.feedback_outcome} onValueChange={v => setAdvanceForm({...advanceForm, feedback_outcome: v})}>
                <SelectTrigger><SelectValue placeholder="Select outcome" /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="proceed">Proceed with Return</SelectItem>
                  <SelectItem value="resolved_at_feedback">Resolved at Feedback</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </>
        );
      case 'claim_filed':
        return (
          <>
            <div>
              <label className="text-xs font-medium text-muted-foreground">Claim Platform</label>
              <Select value={advanceForm.claim_platform} onValueChange={v => setAdvanceForm({...advanceForm, claim_platform: v})}>
                <SelectTrigger><SelectValue placeholder="Select platform" /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="amazon">Amazon</SelectItem>
                  <SelectItem value="flipkart">Flipkart</SelectItem>
                  <SelectItem value="courier">Courier Company</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <label className="text-xs font-medium text-muted-foreground">Claim Reference</label>
              <Input value={advanceForm.claim_reference} onChange={e => setAdvanceForm({...advanceForm, claim_reference: e.target.value})} placeholder="Claim reference number" />
            </div>
            <div>
              <label className="text-xs font-medium text-muted-foreground">Claim Amount</label>
              <Input type="number" step="0.01" value={advanceForm.claim_amount} onChange={e => setAdvanceForm({...advanceForm, claim_amount: e.target.value})} placeholder="Amount" />
            </div>
          </>
        );
      case 'authorized':
        return null; // Just notes
      case 'return_initiated':
        return (
          <div>
            <label className="text-xs font-medium text-muted-foreground">Return Method</label>
            <Select value={advanceForm.return_method} onValueChange={v => setAdvanceForm({...advanceForm, return_method: v})}>
              <SelectTrigger><SelectValue placeholder="Select method" /></SelectTrigger>
              <SelectContent>
                <SelectItem value="courier_pickup">Courier Pickup</SelectItem>
                <SelectItem value="customer_drop">Customer Drop-off</SelectItem>
                <SelectItem value="reverse_logistics">Reverse Logistics</SelectItem>
              </SelectContent>
            </Select>
          </div>
        );
      case 'in_transit':
        return (
          <>
            <div>
              <label className="text-xs font-medium text-muted-foreground">Tracking Number *</label>
              <Input value={advanceForm.tracking_number} onChange={e => setAdvanceForm({...advanceForm, tracking_number: e.target.value})} placeholder="Enter tracking number" />
            </div>
            <div>
              <label className="text-xs font-medium text-muted-foreground">Courier Partner</label>
              <Input value={advanceForm.courier_partner} onChange={e => setAdvanceForm({...advanceForm, courier_partner: e.target.value})} placeholder="Delhivery, BlueDart, etc." />
            </div>
          </>
        );
      case 'warehouse_received':
        return null; // Just notes
      case 'qc_inspection':
        return (
          <>
            <div>
              <label className="text-xs font-medium text-muted-foreground">QC Result</label>
              <Select value={advanceForm.qc_result} onValueChange={v => setAdvanceForm({...advanceForm, qc_result: v})}>
                <SelectTrigger><SelectValue placeholder="Select QC result" /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="pass">Pass - No Damage</SelectItem>
                  <SelectItem value="fail">Fail - Damaged</SelectItem>
                  <SelectItem value="partial">Partial Damage</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <label className="text-xs font-medium text-muted-foreground">Damage Found</label>
              <Input value={advanceForm.qc_damage_found} onChange={e => setAdvanceForm({...advanceForm, qc_damage_found: e.target.value})} placeholder="Describe damage found" />
            </div>
          </>
        );
      case 'claim_filing':
        return (
          <>
            <div>
              <label className="text-xs font-medium text-muted-foreground">Filing Platform</label>
              <Select value={advanceForm.claim_platform} onValueChange={v => setAdvanceForm({...advanceForm, claim_platform: v})}>
                <SelectTrigger><SelectValue placeholder="Select platform" /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="amazon">Amazon</SelectItem>
                  <SelectItem value="flipkart">Flipkart</SelectItem>
                  <SelectItem value="courier">Courier Company</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <label className="text-xs font-medium text-muted-foreground">Claim Reference</label>
              <Input value={advanceForm.claim_reference} onChange={e => setAdvanceForm({...advanceForm, claim_reference: e.target.value})} placeholder="Filing reference" />
            </div>
            <div>
              <label className="text-xs font-medium text-muted-foreground">Filing Amount</label>
              <Input type="number" step="0.01" value={advanceForm.claim_amount} onChange={e => setAdvanceForm({...advanceForm, claim_amount: e.target.value})} placeholder="Amount" />
            </div>
          </>
        );
      case 'claim_status':
        return (
          <>
            <div>
              <label className="text-xs font-medium text-muted-foreground">Claim Result</label>
              <Select value={advanceForm.claim_status_result} onValueChange={v => setAdvanceForm({...advanceForm, claim_status_result: v})}>
                <SelectTrigger><SelectValue placeholder="Select result" /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="approved">Approved</SelectItem>
                  <SelectItem value="rejected">Rejected</SelectItem>
                  <SelectItem value="partial">Partially Approved</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <label className="text-xs font-medium text-muted-foreground">Approved Amount</label>
              <Input type="number" step="0.01" value={advanceForm.claim_approved_amount} onChange={e => setAdvanceForm({...advanceForm, claim_approved_amount: e.target.value})} placeholder="Amount" />
            </div>
          </>
        );
      case 'refund_processed':
        return (
          <>
            <div>
              <label className="text-xs font-medium text-muted-foreground">Refund Amount</label>
              <Input type="number" step="0.01" value={advanceForm.refund_amount} onChange={e => setAdvanceForm({...advanceForm, refund_amount: e.target.value})} placeholder="Enter refund amount" />
            </div>
            <div>
              <label className="text-xs font-medium text-muted-foreground">Refund Method</label>
              <Select value={advanceForm.refund_method} onValueChange={v => setAdvanceForm({...advanceForm, refund_method: v})}>
                <SelectTrigger><SelectValue placeholder="Select method" /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="bank_transfer">Bank Transfer</SelectItem>
                  <SelectItem value="original_payment">Original Payment Method</SelectItem>
                  <SelectItem value="store_credit">Store Credit</SelectItem>
                  <SelectItem value="upi">UPI</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <label className="text-xs font-medium text-muted-foreground">Transaction ID</label>
              <Input value={advanceForm.refund_transaction_id} onChange={e => setAdvanceForm({...advanceForm, refund_transaction_id: e.target.value})} placeholder="Transaction reference" />
            </div>
          </>
        );
      case 'closed':
        return (
          <div>
            <label className="text-xs font-medium text-muted-foreground">Resolution Summary</label>
            <Input value={advanceForm.resolution_summary} onChange={e => setAdvanceForm({...advanceForm, resolution_summary: e.target.value})} placeholder="Summary of resolution" />
          </div>
        );
      // Legacy statuses
      case 'pickup_scheduled':
        return (
          <div>
            <label className="text-xs font-medium text-muted-foreground">Pickup Date *</label>
            <Input type="date" value={advanceForm.pickup_date} onChange={e => setAdvanceForm({...advanceForm, pickup_date: e.target.value})} />
          </div>
        );
      default:
        return null;
    }
  };

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
          <p className="text-muted-foreground mt-1">
            Created {safeDate(returnReq.created_at)}
            {returnReq.category && (
              <Badge className="ml-2" variant="outline">{returnReq.category?.toUpperCase()}</Badge>
            )}
          </p>
        </div>
        <Badge className={`text-sm px-3 py-1 ${statusColors[returnReq.return_status] || 'bg-gray-100 text-gray-800'}`}>
          {returnReq.return_status?.replace(/_/g, ' ').toUpperCase()}
        </Badge>
      </div>

      {/* Visual Stepper */}
      <Card>
        <CardHeader>
          <CardTitle className="font-[Manrope] text-lg">Workflow Progress</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center overflow-x-auto pb-2 gap-1">
            {WORKFLOW_STAGES.map((stage, idx) => {
              const Icon = stage.icon;
              const isCompleted = currentStageIdx >= 0 && idx < currentStageIdx;
              const isCurrent = stage.key === returnReq.return_status;
              const isPending = currentStageIdx >= 0 ? idx > currentStageIdx : true;

              return (
                <React.Fragment key={stage.key}>
                  <div className="flex flex-col items-center min-w-[70px]">
                    <div
                      className={`w-9 h-9 rounded-full flex items-center justify-center border-2 transition-colors ${
                        isCompleted ? 'bg-green-500 border-green-500 text-white' :
                        isCurrent ? 'bg-primary border-primary text-white' :
                        'bg-muted border-border text-muted-foreground'
                      }`}
                    >
                      {isCompleted ? <CheckCircle className="w-4 h-4" /> : <Icon className="w-4 h-4" />}
                    </div>
                    <span className={`text-[10px] mt-1.5 text-center leading-tight ${
                      isCurrent ? 'font-medium text-foreground' : 'text-muted-foreground'
                    }`}>
                      {stage.label}
                    </span>
                  </div>
                  {idx < WORKFLOW_STAGES.length - 1 && (
                    <div className={`h-0.5 w-4 flex-shrink-0 mt-[-12px] ${
                      isCompleted ? 'bg-green-500' : 'bg-border'
                    }`} />
                  )}
                </React.Fragment>
              );
            })}
          </div>
          {/* Show if status is legacy (not in main workflow) */}
          {currentStageIdx === -1 && !isTerminal && (
            <p className="text-xs text-muted-foreground mt-2 text-center italic">
              Current status "{returnReq.return_status?.replace(/_/g, ' ')}" is a legacy status
            </p>
          )}
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
                <InfoField label="Category" value={returnReq.category?.toUpperCase() || '-'} />
                <InfoField label="Requested Date" value={safeDate(returnReq.requested_date)} />
                <InfoField label="Tracking Number" value={returnReq.return_tracking_number || '-'} mono />
                <InfoField label="Courier" value={returnReq.courier_partner || '-'} />
                <InfoField label="Return Method" value={returnReq.return_method?.replace(/_/g, ' ') || '-'} />
                <InfoField label="Refund Amount" value={returnReq.refund_processed_amount || returnReq.refund_amount ? `₹${returnReq.refund_processed_amount || returnReq.refund_amount}` : '-'} />
                <InfoField label="Refund Method" value={returnReq.refund_processed_method || returnReq.refund_method || '-'} />
                <InfoField label="QC Result" value={returnReq.qc_result?.replace(/_/g, ' ') || '-'} />
                <InfoField label="Claim Reference" value={returnReq.claim_reference || returnReq.claim_filing_reference || '-'} mono />
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
              {returnReq.resolution_summary && (
                <div className="mt-4 p-3 bg-green-50 rounded-lg border border-green-200">
                  <p className="text-xs text-green-700 mb-1">Resolution Summary</p>
                  <p className="text-sm text-green-900">{returnReq.resolution_summary}</p>
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
                      <img src={img} alt={`Damage ${idx + 1}`}
                        className="w-full h-32 object-cover rounded-lg border hover:opacity-80 transition-opacity"
                      />
                    </a>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* QC Images */}
          {returnReq.qc_images && returnReq.qc_images.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="font-[Manrope] flex items-center gap-2">
                  <ClipboardCheck className="w-5 h-5" />QC Inspection Images
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  {returnReq.qc_images.map((img, idx) => (
                    <a key={idx} href={img} target="_blank" rel="noopener noreferrer">
                      <img src={img} alt={`QC ${idx + 1}`}
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
                  {[...returnReq.status_history].reverse().map((entry, idx) => (
                    <div key={idx} className="flex items-start gap-3 text-sm border-l-2 border-primary/20 pl-4 py-2">
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <span className="font-medium">
                            {entry.from_status ? entry.from_status.replace(/_/g, ' ') : 'Created'} → {entry.to_status?.replace(/_/g, ' ')}
                          </span>
                          {entry.is_undo && <Badge variant="outline" className="text-xs">Undo</Badge>}
                        </div>
                        <p className="text-xs text-muted-foreground mt-0.5">
                          {safeDate(entry.changed_at)} by {entry.changed_by}
                        </p>
                        {entry.notes && (
                          <p className="text-xs text-muted-foreground mt-1 italic">{entry.notes}</p>
                        )}
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
              {/* Quick Action Buttons - Show direct approve/reject/close for early stages */}
              {allowedTransitions.includes('approved') && (
                <Button
                  className="w-full bg-green-600 hover:bg-green-700"
                  onClick={() => {
                    setSelectedNextStatus('approved');
                    setShowAdvanceModal(true);
                  }}
                  disabled={updating}
                >
                  <CheckCircle className="w-4 h-4 mr-2" />Approve Return
                </Button>
              )}

              {allowedTransitions.includes('rejected') && (
                <Button
                  variant="destructive"
                  className="w-full"
                  onClick={() => {
                    setSelectedNextStatus('rejected');
                    setShowAdvanceModal(true);
                  }}
                  disabled={updating}
                >
                  <XCircle className="w-4 h-4 mr-2" />Reject Return
                </Button>
              )}

              {allowedTransitions.includes('closed') && (
                <Button
                  variant="outline"
                  className="w-full border-gray-400"
                  onClick={() => {
                    setSelectedNextStatus('closed');
                    setShowAdvanceModal(true);
                  }}
                  disabled={updating}
                >
                  <Lock className="w-4 h-4 mr-2" />Close Return
                </Button>
              )}

              {/* Advance Workflow - for all other transitions */}
              {canAdvance && allowedTransitions.filter(t => !['approved', 'rejected', 'closed'].includes(t)).length > 0 && (
                <Button
                  variant="outline"
                  className="w-full"
                  onClick={() => {
                    const otherTransitions = allowedTransitions.filter(t => !['approved', 'rejected', 'closed'].includes(t));
                    setSelectedNextStatus(otherTransitions[0] || '');
                    setShowAdvanceModal(true);
                  }}
                  disabled={updating}
                >
                  <ChevronRight className="w-4 h-4 mr-2" />
                  Advance Workflow
                </Button>
              )}
              
              {returnReq.previous_status && (
                <Button variant="outline" className="w-full" onClick={handleUndo} disabled={updating}>
                  <Undo2 className="w-4 h-4 mr-2" />Undo Last Change
                </Button>
              )}

              <Button variant="outline" className="w-full" onClick={() => navigate(`/orders/${returnReq.order_id}`)}>
                <Package className="w-4 h-4 mr-2" />View Order
              </Button>

              {/* QC Image Upload */}
              {['qc_inspection', 'warehouse_received', 'inspected'].includes(returnReq.return_status) && (
                <div>
                  <label className="text-xs font-medium text-muted-foreground block mb-1">Upload QC Images</label>
                  <Input type="file" multiple accept="image/*" onChange={handleQcImageUpload} className="text-xs" />
                </div>
              )}

              {returnReq.return_status === 'closed' && (
                <div className="p-3 bg-green-50 rounded-lg border border-green-200 text-center">
                  <CheckCircle className="w-6 h-6 text-green-600 mx-auto mb-1" />
                  <p className="text-sm font-medium text-green-800">Return Closed</p>
                </div>
              )}

              {returnReq.return_status === 'rejected' && (
                <div className="p-3 bg-red-50 rounded-lg border border-red-200 text-center">
                  <XCircle className="w-6 h-6 text-red-600 mx-auto mb-1" />
                  <p className="text-sm font-medium text-red-800">Return Rejected</p>
                </div>
              )}

              {returnReq.return_status === 'cancelled' && (
                <div className="p-3 bg-red-50 rounded-lg border border-red-200 text-center">
                  <XCircle className="w-6 h-6 text-red-600 mx-auto mb-1" />
                  <p className="text-sm font-medium text-red-800">Return Cancelled</p>
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
                  <span className="font-mono text-xs">{returnReq.batch_number}</span>
                </div>
              )}
              {returnReq.authorized_by && (
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Authorized By</span>
                  <span className="text-xs">{returnReq.authorized_by}</span>
                </div>
              )}
              {returnReq.qc_inspector && (
                <div className="flex justify-between">
                  <span className="text-muted-foreground">QC Inspector</span>
                  <span className="text-xs">{returnReq.qc_inspector}</span>
                </div>
              )}
              {returnReq.refund_transaction_id && (
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Transaction ID</span>
                  <span className="font-mono text-xs">{returnReq.refund_transaction_id}</span>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Advance Workflow Modal */}
      {showAdvanceModal && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <Card className="w-full max-w-md max-h-[80vh] overflow-y-auto">
            <CardHeader>
              <CardTitle className="font-[Manrope]">Advance Workflow</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="text-xs font-medium text-muted-foreground">Next Status *</label>
                <Select value={selectedNextStatus} onValueChange={setSelectedNextStatus}>
                  <SelectTrigger><SelectValue placeholder="Select next status" /></SelectTrigger>
                  <SelectContent>
                    {allowedTransitions.map(t => (
                      <SelectItem key={t} value={t}>{t.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {renderStageFields()}

              <div>
                <label className="text-xs font-medium text-muted-foreground">Notes</label>
                <Input
                  value={advanceForm.notes}
                  onChange={(e) => setAdvanceForm({...advanceForm, notes: e.target.value})}
                  placeholder="Optional notes..."
                />
              </div>

              <div className="flex gap-3 pt-2">
                <Button variant="outline" className="flex-1" onClick={() => { setShowAdvanceModal(false); setSelectedNextStatus(''); resetAdvanceForm(); }}>
                  Cancel
                </Button>
                <Button className="flex-1" onClick={handleAdvanceWorkflow} disabled={updating || !selectedNextStatus}>
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
