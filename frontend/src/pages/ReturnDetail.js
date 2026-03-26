import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api from '../lib/api';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { toast } from 'sonner';
import {
  ArrowLeft, RefreshCcw, User, Calendar, Truck,
  CheckCircle, XCircle, Clock, Package, ChevronRight, Upload, Image as ImageIcon
} from 'lucide-react';

// 3-Type Workflow Stages - UPDATED: removed "closed", added "resolved" and "condition_checked"
const WORKFLOW_STAGES = {
  pre_dispatch: [
    { key: 'requested', label: 'Requested', icon: Clock },
    { key: 'approved', label: 'Approved', icon: CheckCircle },
    { key: 'rejected', label: 'Rejected', icon: XCircle },
    { key: 'resolved', label: 'Resolved', icon: CheckCircle }
  ],
  in_transit: [
    { key: 'requested', label: 'Requested', icon: Clock },
    { key: 'approved', label: 'Approved', icon: CheckCircle },
    { key: 'rto_in_transit', label: 'RTO In Transit', icon: Truck },
    { key: 'warehouse_received', label: 'Warehouse Received', icon: Package },
    { key: 'condition_checked', label: 'Condition Checked', icon: CheckCircle },
    { key: 'rejected', label: 'Rejected', icon: XCircle },
    { key: 'resolved', label: 'Resolved', icon: CheckCircle }
  ],
  post_delivery: [
    { key: 'requested', label: 'Requested', icon: Clock },
    { key: 'accepted', label: 'Accepted', icon: CheckCircle },
    { key: 'picked_up', label: 'Picked Up', icon: Truck },
    { key: 'pickup_in_transit', label: 'Pickup In Transit', icon: Truck },
    { key: 'warehouse_received', label: 'Warehouse Received', icon: Package },
    { key: 'condition_checked', label: 'Condition Checked', icon: CheckCircle },
    { key: 'rejected', label: 'Rejected', icon: XCircle },
    { key: 'resolved', label: 'Resolved', icon: CheckCircle }
  ]
};

const statusColors = {
  requested: 'bg-blue-100 text-blue-800',
  approved: 'bg-green-100 text-green-800',
  accepted: 'bg-green-100 text-green-800',
  rejected: 'bg-red-100 text-red-800',
  rto_in_transit: 'bg-orange-100 text-orange-800',
  picked_up: 'bg-blue-100 text-blue-800',
  pickup_in_transit: 'bg-orange-100 text-orange-800',
  pickup_not_required: 'bg-gray-100 text-gray-800',
  warehouse_received: 'bg-teal-100 text-teal-800',
  condition_checked: 'bg-yellow-100 text-yellow-800',
  resolved: 'bg-green-200 text-green-900',
  closed: 'bg-gray-100 text-gray-800'
};

export const ReturnDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [returnReq, setReturnReq] = useState(null);
  const [loading, setLoading] = useState(true);
  const [updating, setUpdating] = useState(false);
  const [showAdvanceModal, setShowAdvanceModal] = useState(false);
  const [workflowInfo, setWorkflowInfo] = useState(null);
  const [selectedNextStatus, setSelectedNextStatus] = useState('');
  const [conditionImages, setConditionImages] = useState([]);
  const [uploadingImages, setUploadingImages] = useState(false);
  const [advanceForm, setAdvanceForm] = useState({
    notes: '',
    // In-transit RTO fields
    rto_tracking_number: '',
    rto_courier: '',
    // Post-delivery pickup fields
    pickup_date: '',
    pickup_tracking_id: '',
    pickup_courier: '',
    pickup_not_required: false,
    // Warehouse fields
    warehouse_received_date: '',
    received_condition: '',
    condition_notes: '',
    // Rejection fields
    rejection_reason: '',
    // Refund fields
    refund_amount: '',
    refund_date: ''
  });

  useEffect(() => {
    fetchReturn();
  }, [id]);

  const fetchReturn = async () => {
    try {
      const res = await api.get(`/return-requests/${id}`);
      setReturnReq(res.data);
      
      // Fetch workflow stages
      try {
        const workflowRes = await api.get(`/return-requests/${id}/workflow-stages`);
        setWorkflowInfo(workflowRes.data);
      } catch (err) {
        console.error('Failed to fetch workflow stages:', err);
      }
    } catch (err) {
      toast.error('Failed to load return request');
    } finally {
      setLoading(false);
    }
  };

  // Handle image upload for condition check
  const handleImageUpload = async (e) => {
    const files = Array.from(e.target.files);
    if (files.length === 0) return;
    
    setUploadingImages(true);
    const uploadedUrls = [];
    
    for (const file of files) {
      try {
        const formData = new FormData();
        formData.append('file', file);
        
        const response = await api.post('/uploads/image', formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        });
        
        if (response.data?.url) {
          uploadedUrls.push(response.data.url);
        }
      } catch (err) {
        console.error('Failed to upload image:', err);
        toast.error(`Failed to upload ${file.name}`);
      }
    }
    
    setConditionImages(prev => [...prev, ...uploadedUrls]);
    setUploadingImages(false);
    
    if (uploadedUrls.length > 0) {
      toast.success(`${uploadedUrls.length} image(s) uploaded`);
    }
  };

  const removeImage = (index) => {
    setConditionImages(prev => prev.filter((_, i) => i !== index));
  };

  const handleAdvanceWorkflow = async () => {
    if (!selectedNextStatus) {
      toast.error('Please select next status');
      return;
    }
    
    // Validation for rejection
    if (selectedNextStatus === 'rejected' && !advanceForm.rejection_reason) {
      toast.error('Please provide a rejection reason');
      return;
    }
    
    // Validation for condition check
    if (selectedNextStatus === 'condition_checked' && !advanceForm.received_condition) {
      toast.error('Please select the received condition (mint or damaged)');
      return;
    }
    
    // Validation for warehouse_received in in_transit (RTO) - MUST have condition
    if (selectedNextStatus === 'warehouse_received' && returnReq.return_type === 'in_transit' && !advanceForm.received_condition) {
      toast.error('Please select the received condition for RTO warehouse check');
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
      
      // Add condition images if any
      if (conditionImages.length > 0) {
        params.append('condition_images', JSON.stringify(conditionImages));
      }

      await api.patch(`/return-requests/${id}/workflow/advance?${params.toString()}`);
      toast.success('Return workflow advanced successfully');
      setShowAdvanceModal(false);
      setSelectedNextStatus('');
      setConditionImages([]);
      setAdvanceForm({
        notes: '',
        rto_tracking_number: '',
        rto_courier: '',
        pickup_date: '',
        pickup_tracking_id: '',
        pickup_courier: '',
        pickup_not_required: false,
        warehouse_received_date: '',
        received_condition: '',
        condition_notes: '',
        rejection_reason: '',
        refund_amount: '',
        refund_date: ''
      });
      fetchReturn();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to advance workflow');
    } finally {
      setUpdating(false);
    }
  };

  const getCurrentStageIndex = () => {
    if (!returnReq || !returnReq.return_type) return 0;
    const stages = WORKFLOW_STAGES[returnReq.return_type] || [];
    return stages.findIndex(s => s.key === returnReq.return_status);
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
          <RefreshCcw className="w-8 h-8 animate-spin mx-auto mb-2 text-primary" />
          <p className="text-muted-foreground">Loading return details...</p>
        </div>
      </div>
    );
  }

  if (!returnReq) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <XCircle className="w-12 h-12 text-red-500 mx-auto mb-2" />
          <p className="text-muted-foreground">Return request not found</p>
        </div>
      </div>
    );
  }

  const currentStageIndex = getCurrentStageIndex();
  const stages = WORKFLOW_STAGES[returnReq.return_type] || [];
  const allowedTransitions = workflowInfo?.allowed_transitions || [];

  return (
    <div className="space-y-6 pb-12">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="sm" onClick={() => navigate('/returns')}>
            <ArrowLeft className="w-4 h-4 mr-2" />Back to Returns
          </Button>
          <div>
            <h1 className="text-3xl font-bold font-[Manrope] flex items-center gap-3">
              <RefreshCcw className="w-8 h-8 text-orange-600" />
              Return Request #{returnReq.id?.slice(0, 8)}
            </h1>
            <p className="text-muted-foreground mt-1">
              {workflowInfo?.workflow_description?.name || 'Return Workflow'}
            </p>
          </div>
        </div>
        <Badge className={`${statusColors[returnReq.return_status]} text-lg px-4 py-2`}>
          {returnReq.return_status?.replace(/_/g, ' ').toUpperCase()}
        </Badge>
      </div>

      {/* Workflow Progress */}
      <Card>
        <CardHeader>
          <CardTitle className="font-[Manrope]">
            Workflow Progress: {workflowInfo?.workflow_description?.name}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between mb-4">
            {stages.map((stage, index) => {
              const Icon = stage.icon;
              const isCompleted = index < currentStageIndex;
              const isCurrent = index === currentStageIndex;
              const isUpcoming = index > currentStageIndex;

              return (
                <React.Fragment key={stage.key}>
                  <div className="flex flex-col items-center">
                    <div
                      className={`w-12 h-12 rounded-full flex items-center justify-center ${
                        isCompleted
                          ? 'bg-green-500 text-white'
                          : isCurrent
                          ? 'bg-blue-500 text-white'
                          : 'bg-gray-200 text-gray-400'
                      }`}
                    >
                      <Icon className="w-6 h-6" />
                    </div>
                    <span className={`text-xs mt-2 text-center ${isCurrent ? 'font-bold' : ''}`}>
                      {stage.label}
                    </span>
                  </div>
                  {index < stages.length - 1 && (
                    <ChevronRight
                      className={`w-6 h-6 ${isCompleted ? 'text-green-500' : 'text-gray-300'}`}
                    />
                  )}
                </React.Fragment>
              );
            })}
          </div>

          {allowedTransitions.length > 0 && (
            <Button onClick={() => setShowAdvanceModal(true)} className="w-full">
              Advance Workflow
            </Button>
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
              <p className="font-[JetBrains_Mono] font-medium">{returnReq.order_number}</p>
            </div>
            <div>
              <span className="text-muted-foreground">Customer:</span>
              <p className="font-medium">{returnReq.customer_name}</p>
            </div>
            <div>
              <span className="text-muted-foreground">Phone:</span>
              <p className="font-[JetBrains_Mono]">{returnReq.phone}</p>
            </div>
            <div>
              <span className="text-muted-foreground">Requested Date:</span>
              <p>{formatDate(returnReq.requested_date)}</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Return Information */}
      <Card>
        <CardHeader><CardTitle className="font-[Manrope]">Return Information</CardTitle></CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div>
              <span className="text-muted-foreground">Return Type:</span>
              <Badge className="ml-2 capitalize">{returnReq.return_type?.replace(/_/g, ' ')}</Badge>
            </div>
            <div>
              <span className="text-muted-foreground">Cancellation Reason:</span>
              <p className="font-medium capitalize">{returnReq.cancellation_reason?.replace(/_/g, ' ') || '-'}</p>
            </div>
            {returnReq.notes && (
              <div>
                <span className="text-muted-foreground">Notes:</span>
                <p className="mt-1 p-3 bg-gray-50 rounded-md">{returnReq.notes}</p>
              </div>
            )}
            {returnReq.return_reason_details && (
              <div>
                <span className="text-muted-foreground">Details:</span>
                <p className="mt-1 p-3 bg-gray-50 rounded-md">{returnReq.return_reason_details}</p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Tracking Information (if applicable) */}
      {(returnReq.rto_tracking_number || returnReq.pickup_tracking_id) && (
        <Card>
          <CardHeader><CardTitle className="font-[Manrope]">Tracking Information</CardTitle></CardHeader>
          <CardContent>
            <div className="space-y-3">
              {returnReq.rto_tracking_number && (
                <div>
                  <span className="text-muted-foreground">RTO Tracking:</span>
                  <p className="font-[JetBrains_Mono] font-medium">{returnReq.rto_tracking_number}</p>
                  {returnReq.rto_courier && (
                    <p className="text-sm text-muted-foreground">Courier: {returnReq.rto_courier}</p>
                  )}
                </div>
              )}
              {returnReq.pickup_tracking_id && (
                <div>
                  <span className="text-muted-foreground">Pickup Tracking:</span>
                  <p className="font-[JetBrains_Mono] font-medium">{returnReq.pickup_tracking_id}</p>
                  {returnReq.pickup_courier && (
                    <p className="text-sm text-muted-foreground">Courier: {returnReq.pickup_courier}</p>
                  )}
                </div>
              )}
              {returnReq.pickup_date && (
                <div>
                  <span className="text-muted-foreground">Pickup Date:</span>
                  <p>{formatDate(returnReq.pickup_date)}</p>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Condition Check (if applicable) */}
      {returnReq.received_condition && (
        <Card>
          <CardHeader><CardTitle className="font-[Manrope]">Condition Check</CardTitle></CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div>
                <span className="text-muted-foreground">Received Condition:</span>
                <Badge className={`ml-2 ${returnReq.received_condition === 'mint' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                  {returnReq.received_condition?.toUpperCase()}
                </Badge>
              </div>
              {returnReq.condition_notes && (
                <div>
                  <span className="text-muted-foreground">Notes:</span>
                  <p className="mt-1 p-3 bg-gray-50 rounded-md">{returnReq.condition_notes}</p>
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
                  {allowedTransitions.map(status => (
                    <option key={status} value={status}>
                      {status.replace(/_/g, ' ').toUpperCase()}
                    </option>
                  ))}
                </select>
              </div>

              {/* Context-specific fields based on selected status */}
              {selectedNextStatus === 'rto_in_transit' && (
                <>
                  <div>
                    <label className="text-sm font-medium">RTO Tracking Number *</label>
                    <Input
                      value={advanceForm.rto_tracking_number}
                      onChange={e => setAdvanceForm({ ...advanceForm, rto_tracking_number: e.target.value })}
                      placeholder="Enter tracking number"
                    />
                  </div>
                  <div>
                    <label className="text-sm font-medium">RTO Courier</label>
                    <Input
                      value={advanceForm.rto_courier}
                      onChange={e => setAdvanceForm({ ...advanceForm, rto_courier: e.target.value })}
                      placeholder="e.g., Blue Dart, Delhivery"
                    />
                  </div>
                </>
              )}

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

              {/* Warehouse Received for In-Transit RTO - Show condition form */}
              {selectedNextStatus === 'warehouse_received' && returnReq.return_type === 'in_transit' && (
                <>
                  <div className="p-3 bg-orange-50 rounded-lg border border-orange-200 mb-3">
                    <p className="text-sm text-orange-800 font-medium">
                      RTO Warehouse Check - Please provide condition details
                    </p>
                  </div>
                  <div>
                    <label className="text-sm font-medium">Received Condition *</label>
                    <select
                      value={advanceForm.received_condition}
                      onChange={e => setAdvanceForm({ ...advanceForm, received_condition: e.target.value })}
                      className="w-full p-2 border rounded-md mt-1"
                    >
                      <option value="">-- Select Condition --</option>
                      <option value="mint">Mint Condition</option>
                      <option value="damaged">Damaged Condition</option>
                    </select>
                  </div>
                  <div>
                    <label className="text-sm font-medium">Condition Notes</label>
                    <textarea
                      value={advanceForm.condition_notes}
                      onChange={e => setAdvanceForm({ ...advanceForm, condition_notes: e.target.value })}
                      placeholder="Describe the condition of the returned product..."
                      className="w-full p-2 border rounded-md mt-1 min-h-[80px]"
                    />
                  </div>
                  {/* Image Upload */}
                  <div>
                    <label className="text-sm font-medium">Upload Images (Optional for mint, recommended for damaged)</label>
                    <div className="mt-2 border-2 border-dashed border-gray-300 rounded-lg p-4">
                      <input
                        type="file"
                        accept="image/*"
                        multiple
                        onChange={handleImageUpload}
                        className="hidden"
                        id="rto-damage-images"
                        disabled={uploadingImages}
                      />
                      <label
                        htmlFor="rto-damage-images"
                        className="flex flex-col items-center cursor-pointer"
                      >
                        {uploadingImages ? (
                          <RefreshCcw className="w-8 h-8 text-gray-400 animate-spin" />
                        ) : (
                          <Upload className="w-8 h-8 text-gray-400" />
                        )}
                        <span className="mt-2 text-sm text-gray-500">
                          {uploadingImages ? 'Uploading...' : 'Click to upload condition images'}
                        </span>
                      </label>
                    </div>
                    {conditionImages.length > 0 && (
                      <div className="mt-3 grid grid-cols-3 gap-2">
                        {conditionImages.map((url, idx) => (
                          <div key={idx} className="relative">
                            <img src={url} alt={`Condition ${idx + 1}`} className="w-full h-20 object-cover rounded" />
                            <button
                              onClick={() => removeImage(idx)}
                              className="absolute -top-2 -right-2 bg-red-500 text-white rounded-full w-5 h-5 text-xs"
                            >
                              ×
                            </button>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </>
              )}

              {selectedNextStatus === 'condition_checked' && (
                <>
                  <div>
                    <label className="text-sm font-medium">Received Condition *</label>
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
                  {/* Image Upload for Damaged Condition */}
                  {advanceForm.received_condition === 'damaged' && (
                    <div>
                      <label className="text-sm font-medium">Upload Damage Images</label>
                      <div className="mt-2 border-2 border-dashed border-gray-300 rounded-lg p-4">
                        <input
                          type="file"
                          accept="image/*"
                          multiple
                          onChange={handleImageUpload}
                          className="hidden"
                          id="damage-images"
                          disabled={uploadingImages}
                        />
                        <label
                          htmlFor="damage-images"
                          className="flex flex-col items-center cursor-pointer"
                        >
                          {uploadingImages ? (
                            <RefreshCcw className="w-8 h-8 text-gray-400 animate-spin" />
                          ) : (
                            <Upload className="w-8 h-8 text-gray-400" />
                          )}
                          <span className="mt-2 text-sm text-gray-500">
                            {uploadingImages ? 'Uploading...' : 'Click to upload damage images'}
                          </span>
                        </label>
                      </div>
                      {/* Preview uploaded images */}
                      {conditionImages.length > 0 && (
                        <div className="mt-3 grid grid-cols-3 gap-2">
                          {conditionImages.map((url, idx) => (
                            <div key={idx} className="relative">
                              <img src={url} alt={`Damage ${idx + 1}`} className="w-full h-20 object-cover rounded" />
                              <button
                                onClick={() => removeImage(idx)}
                                className="absolute -top-2 -right-2 bg-red-500 text-white rounded-full w-5 h-5 text-xs"
                              >
                                ×
                              </button>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                </>
              )}

              {/* Rejection Reason - Required when rejecting */}
              {selectedNextStatus === 'rejected' && (
                <div>
                  <label className="text-sm font-medium text-red-600">Rejection Reason *</label>
                  <textarea
                    value={advanceForm.rejection_reason}
                    onChange={e => setAdvanceForm({ ...advanceForm, rejection_reason: e.target.value })}
                    placeholder="Please provide a reason for rejection..."
                    className="w-full p-2 border border-red-300 rounded-md mt-1 min-h-[80px]"
                    required
                  />
                </div>
              )}

              {/* Refund fields for resolved status */}
              {selectedNextStatus === 'resolved' && (
                <>
                  <div>
                    <label className="text-sm font-medium">Refund Amount (Optional)</label>
                    <Input
                      type="number"
                      value={advanceForm.refund_amount}
                      onChange={e => setAdvanceForm({ ...advanceForm, refund_amount: e.target.value })}
                      placeholder="Enter refund amount"
                    />
                  </div>
                  <div>
                    <label className="text-sm font-medium">Refund Date (Optional)</label>
                    <Input
                      type="date"
                      value={advanceForm.refund_date}
                      onChange={e => setAdvanceForm({ ...advanceForm, refund_date: e.target.value })}
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

export default ReturnDetail;
