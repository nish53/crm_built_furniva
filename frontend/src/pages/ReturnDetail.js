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
  ArrowLeft, Check, Circle, ChevronRight, AlertCircle, Upload, X, FileText
} from 'lucide-react';
import { format } from 'date-fns';

const WORKFLOW_STAGES = [
  { key: 'requested', label: '1. Requested', color: 'bg-yellow-500' },
  { key: 'feedback_check', label: '2. Feedback Check', color: 'bg-orange-500' },
  { key: 'claim_filed', label: '3. Claim Filed', color: 'bg-red-500' },
  { key: 'authorized', label: '4. Authorized', color: 'bg-blue-500' },
  { key: 'return_initiated', label: '5. Return Initiated', color: 'bg-purple-500' },
  { key: 'in_transit', label: '6. In Transit', color: 'bg-indigo-500' },
  { key: 'warehouse_received', label: '7. Received', color: 'bg-cyan-500' },
  { key: 'qc_inspection', label: '8. QC Inspection', color: 'bg-teal-500' },
  { key: 'claim_filing', label: '9. Claim Filing', color: 'bg-amber-500' },
  { key: 'claim_status', label: '10. Claim Status', color: 'bg-lime-500' },
  { key: 'refund_processed', label: '11. Refund Processed', color: 'bg-green-500' },
  { key: 'closed', label: '12. Closed', color: 'bg-gray-700' }
];

export const ReturnDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [returnReq, setReturnReq] = useState(null);
  const [loading, setLoading] = useState(true);
  const [nextStages, setNextStages] = useState([]);
  const [showAdvanceModal, setShowAdvanceModal] = useState(false);
  const [selectedNextStage, setSelectedNextStage] = useState('');
  const [stageFormData, setStageFormData] = useState({});
  const [uploadingImages, setUploadingImages] = useState(false);
  const [qcImages, setQcImages] = useState([]);

  useEffect(() => {
    if (id) {
      fetchReturnDetail();
      fetchNextStages();
    }
  }, [id]);

  const fetchReturnDetail = async () => {
    try {
      const res = await api.get(`/returns/${id}`);
      setReturnReq(res.data);
    } catch (error) {
      toast.error('Failed to fetch return details');
    } finally {
      setLoading(false);
    }
  };

  const fetchNextStages = async () => {
    try {
      const res = await api.get(`/returns/${id}/workflow-stages`);
      setNextStages(res.data.next_stages || []);
    } catch (error) {
      console.error('Failed to fetch next stages');
    }
  };

  const handleAdvanceWorkflow = async (e) => {
    e.preventDefault();
    
    try {
      // Upload QC images first if any
      if (qcImages.length > 0 && (selectedNextStage === 'qc_inspection' || selectedNextStage === 'claim_filing')) {
        setUploadingImages(true);
        const formData = new FormData();
        qcImages.forEach(file => formData.append('files', file));
        
        const uploadRes = await api.post('/uploads/damage-images/bulk', formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        });
        
        const imageUrls = uploadRes.data.images.map(img => img.image_url);
        
        // Add images to return
        await api.patch(`/returns/${id}/qc-images`, { image_urls: imageUrls });
        
        setUploadingImages(false);
        setQcImages([]);
      }
      
      // Build query params
      const params = new URLSearchParams({ new_status: selectedNextStage });
      Object.keys(stageFormData).forEach(key => {
        if (stageFormData[key] !== undefined && stageFormData[key] !== '') {
          params.append(key, stageFormData[key]);
        }
      });
      
      await api.patch(`/returns/${id}/workflow/advance?${params.toString()}`);
      toast.success('Workflow advanced successfully');
      setShowAdvanceModal(false);
      setSelectedNextStage('');
      setStageFormData({});
      fetchReturnDetail();
      fetchNextStages();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to advance workflow');
    }
  };

  const getCurrentStageIndex = () => {
    if (!returnReq) return -1;
    return WORKFLOW_STAGES.findIndex(s => s.key === returnReq.return_status);
  };

  const renderStageForm = () => {
    if (!selectedNextStage) return null;

    switch (selectedNextStage) {
      case 'feedback_check':
        return (
          <div className="space-y-3">
            <div>
              <label className="text-sm font-medium">Has Negative Feedback? *</label>
              <Select value={stageFormData.has_negative_feedback} onValueChange={v => setStageFormData({...stageFormData, has_negative_feedback: v})}>
                <SelectTrigger><SelectValue placeholder="Select" /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="true">Yes</SelectItem>
                  <SelectItem value="false">No</SelectItem>
                </SelectContent>
              </Select>
            </div>
            {stageFormData.has_negative_feedback === 'true' && (
              <>
                <div>
                  <label className="text-sm font-medium">Platform</label>
                  <Select value={stageFormData.feedback_platform} onValueChange={v => setStageFormData({...stageFormData, feedback_platform: v})}>
                    <SelectTrigger><SelectValue placeholder="Select platform" /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="amazon">Amazon</SelectItem>
                      <SelectItem value="flipkart">Flipkart</SelectItem>
                      <SelectItem value="google">Google Reviews</SelectItem>
                      <SelectItem value="other">Other</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <label className="text-sm font-medium">Feedback Details</label>
                  <Input value={stageFormData.feedback_details || ''} onChange={e => setStageFormData({...stageFormData, feedback_details: e.target.value})} placeholder="Details..." />
                </div>
              </>
            )}
          </div>
        );

      case 'claim_filed':
        return (
          <div className="space-y-3">
            <div>
              <label className="text-sm font-medium">Customer Claim Filed? *</label>
              <Select value={stageFormData.customer_claim_filed} onValueChange={v => setStageFormData({...stageFormData, customer_claim_filed: v})}>
                <SelectTrigger><SelectValue placeholder="Select" /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="true">Yes</SelectItem>
                  <SelectItem value="false">No</SelectItem>
                </SelectContent>
              </Select>
            </div>
            {stageFormData.customer_claim_filed === 'true' && (
              <>
                <div>
                  <label className="text-sm font-medium">Claim Type</label>
                  <Select value={stageFormData.customer_claim_type} onValueChange={v => setStageFormData({...stageFormData, customer_claim_type: v})}>
                    <SelectTrigger><SelectValue placeholder="Select type" /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="a_to_z">Amazon A-to-Z</SelectItem>
                      <SelectItem value="safe_t">Flipkart Safe-T</SelectItem>
                      <SelectItem value="chargeback">Credit Card Chargeback</SelectItem>
                      <SelectItem value="other">Other</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <label className="text-sm font-medium">Claim ID/Reference</label>
                  <Input value={stageFormData.customer_claim_id || ''} onChange={e => setStageFormData({...stageFormData, customer_claim_id: e.target.value})} placeholder="Claim reference number" />
                </div>
              </>
            )}
          </div>
        );

      case 'authorized':
        return (
          <div className="space-y-3">
            <div>
              <label className="text-sm font-medium">Authorization Type *</label>
              <Select value={stageFormData.authorization_type} onValueChange={v => setStageFormData({...stageFormData, authorization_type: v})}>
                <SelectTrigger><SelectValue placeholder="Select" /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="auto">Auto-Authorized (Marketplace)</SelectItem>
                  <SelectItem value="manual">Manually Authorized</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        );

      case 'return_initiated':
        return (
          <div className="space-y-3">
            <div>
              <label className="text-sm font-medium">Return Tracking Number *</label>
              <Input value={stageFormData.return_tracking_number || ''} onChange={e => setStageFormData({...stageFormData, return_tracking_number: e.target.value})} placeholder="Tracking number" required />
            </div>
            <div>
              <label className="text-sm font-medium">Courier Partner</label>
              <Input value={stageFormData.courier_partner || ''} onChange={e => setStageFormData({...stageFormData, courier_partner: e.target.value})} placeholder="Courier name" />
            </div>
          </div>
        );

      case 'warehouse_received':
        return (
          <div className="space-y-3">
            <div>
              <label className="text-sm font-medium">Received By</label>
              <Input value={stageFormData.received_by || ''} onChange={e => setStageFormData({...stageFormData, received_by: e.target.value})} placeholder="Staff name (optional)" />
            </div>
          </div>
        );

      case 'qc_inspection':
        return (
          <div className="space-y-3">
            <div>
              <label className="text-sm font-medium">QC Passed? *</label>
              <Select value={stageFormData.qc_passed} onValueChange={v => setStageFormData({...stageFormData, qc_passed: v})}>
                <SelectTrigger><SelectValue placeholder="Select" /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="true">Yes - Good Condition</SelectItem>
                  <SelectItem value="false">No - Damaged/Defective</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <label className="text-sm font-medium">Damage Severity</label>
              <Select value={stageFormData.damage_severity} onValueChange={v => setStageFormData({...stageFormData, damage_severity: v})}>
                <SelectTrigger><SelectValue placeholder="Select" /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="none">No Damage</SelectItem>
                  <SelectItem value="minor">Minor</SelectItem>
                  <SelectItem value="moderate">Moderate</SelectItem>
                  <SelectItem value="severe">Severe</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <label className="text-sm font-medium">Product Condition</label>
              <Select value={stageFormData.product_condition} onValueChange={v => setStageFormData({...stageFormData, product_condition: v})}>
                <SelectTrigger><SelectValue placeholder="Select" /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="sellable">Sellable (Resell)</SelectItem>
                  <SelectItem value="refurbish_needed">Refurbish Needed</SelectItem>
                  <SelectItem value="scrap">Scrap/Dispose</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <label className="text-sm font-medium">QC Notes</label>
              <Input value={stageFormData.qc_notes || ''} onChange={e => setStageFormData({...stageFormData, qc_notes: e.target.value})} placeholder="Inspection notes" />
            </div>
            <div>
              <label className="text-sm font-medium">QC Images</label>
              <Input type="file" multiple accept="image/*" onChange={e => setQcImages(Array.from(e.target.files || []))} />
              {qcImages.length > 0 && <p className="text-xs text-muted-foreground mt-1">{qcImages.length} file(s) selected</p>}
            </div>
          </div>
        );

      case 'claim_filing':
        return (
          <div className="space-y-3">
            <div>
              <label className="text-sm font-medium">Claim Type *</label>
              <Select value={stageFormData.claim_type} onValueChange={v => setStageFormData({...stageFormData, claim_type: v})}>
                <SelectTrigger><SelectValue placeholder="Select" /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="courier_damage">Courier Damage Claim</SelectItem>
                  <SelectItem value="insurance">Insurance Claim</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <label className="text-sm font-medium">Claim Amount (₹) *</label>
              <Input type="number" step="0.01" value={stageFormData.claim_amount || ''} onChange={e => setStageFormData({...stageFormData, claim_amount: e.target.value})} placeholder="Amount" required />
            </div>
            <div>
              <label className="text-sm font-medium">Claim Against (Courier Name)</label>
              <Input value={stageFormData.claim_against || ''} onChange={e => setStageFormData({...stageFormData, claim_against: e.target.value})} placeholder="Courier partner" />
            </div>
            <div>
              <label className="text-sm font-medium">Claim Reference</label>
              <Input value={stageFormData.claim_reference || ''} onChange={e => setStageFormData({...stageFormData, claim_reference: e.target.value})} placeholder="Claim ticket/reference number" />
            </div>
          </div>
        );

      case 'claim_status':
        return (
          <div className="space-y-3">
            <div>
              <label className="text-sm font-medium">Claim Status *</label>
              <Select value={stageFormData.claim_status_update} onValueChange={v => setStageFormData({...stageFormData, claim_status_update: v})}>
                <SelectTrigger><SelectValue placeholder="Select" /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="approved">Approved</SelectItem>
                  <SelectItem value="partial">Partially Approved</SelectItem>
                  <SelectItem value="rejected">Rejected</SelectItem>
                </SelectContent>
              </Select>
            </div>
            {(stageFormData.claim_status_update === 'approved' || stageFormData.claim_status_update === 'partial') && (
              <div>
                <label className="text-sm font-medium">Approved Amount (₹)</label>
                <Input type="number" step="0.01" value={stageFormData.claim_approved_amount || ''} onChange={e => setStageFormData({...stageFormData, claim_approved_amount: e.target.value})} placeholder="Approved amount" />
              </div>
            )}
          </div>
        );

      case 'refund_processed':
        return (
          <div className="space-y-3">
            <div>
              <label className="text-sm font-medium">Refund Amount (₹) *</label>
              <Input type="number" step="0.01" value={stageFormData.refund_amount || ''} onChange={e => setStageFormData({...stageFormData, refund_amount: e.target.value})} placeholder="Refund amount" required />
            </div>
            <div>
              <label className="text-sm font-medium">Refund Method</label>
              <Select value={stageFormData.refund_method} onValueChange={v => setStageFormData({...stageFormData, refund_method: v})}>
                <SelectTrigger><SelectValue placeholder="Select method" /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="original_payment">Original Payment Method</SelectItem>
                  <SelectItem value="bank_transfer">Bank Transfer</SelectItem>
                  <SelectItem value="cash">Cash</SelectItem>
                  <SelectItem value="store_credit">Store Credit</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <label className="text-sm font-medium">Refund Reference</label>
              <Input value={stageFormData.refund_reference || ''} onChange={e => setStageFormData({...stageFormData, refund_reference: e.target.value})} placeholder="Transaction reference" />
            </div>
          </div>
        );

      case 'closed':
        return (
          <div className="space-y-3">
            <div>
              <label className="text-sm font-medium">Resolution *</label>
              <Select value={stageFormData.resolution} onValueChange={v => setStageFormData({...stageFormData, resolution: v})}>
                <SelectTrigger><SelectValue placeholder="Select" /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="refunded">Refunded</SelectItem>
                  <SelectItem value="replaced">Replaced</SelectItem>
                  <SelectItem value="repaired">Repaired</SelectItem>
                  <SelectItem value="customer_kept">Customer Kept Product</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  const safeDate = (d) => {
    if (!d) return null;
    try { return format(new Date(d), 'MMM dd, yyyy HH:mm'); } catch { return '-'; }
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
        <Button onClick={() => navigate('/returns')} className="mt-4">Back to Returns</Button>
      </div>
    );
  }

  const currentStageIndex = getCurrentStageIndex();

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button variant="ghost" onClick={() => navigate('/returns')}>
          <ArrowLeft className="w-4 h-4 mr-2" />Back
        </Button>
        <div className="flex-1">
          <h1 className="text-3xl font-bold font-[Manrope]">Return: {returnReq.order_number}</h1>
          <p className="text-muted-foreground mt-1">{safeDate(returnReq.requested_date)}</p>
        </div>
      </div>

      {/* Workflow Progress */}
      <Card>
        <CardHeader>
          <CardTitle className="font-[Manrope]">Workflow Progress</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="relative">
            {/* Progress line */}
            <div className="absolute top-5 left-0 right-0 h-0.5 bg-border" style={{ width: `${(currentStageIndex / (WORKFLOW_STAGES.length - 1)) * 100}%` }} />
            
            {/* Stages */}
            <div className="relative flex justify-between">
              {WORKFLOW_STAGES.map((stage, idx) => {
                const isActive = idx === currentStageIndex;
                const isComplete = idx < currentStageIndex;
                const isFuture = idx > currentStageIndex;
                
                return (
                  <div key={stage.key} className="flex flex-col items-center" style={{ width: '8.33%' }}>
                    <div className={`w-10 h-10 rounded-full flex items-center justify-center border-2 ${
                      isComplete ? 'bg-green-500 border-green-500 text-white' :
                      isActive ? `${stage.color} border-white text-white` :
                      'bg-white border-border text-muted-foreground'
                    }`}>
                      {isComplete ? <Check className="w-5 h-5" /> : <Circle className="w-3 h-3" fill={isActive ? 'white' : 'none'} />}
                    </div>
                    <p className={`text-xs mt-2 text-center ${isActive ? 'font-semibold' : ''} ${isFuture ? 'text-muted-foreground' : ''}`}>
                      {stage.label.split('. ')[1]}
                    </p>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Current Status */}
          <div className="mt-6 p-4 bg-primary/5 rounded-lg">
            <p className="text-sm text-muted-foreground">Current Status</p>
            <p className="text-lg font-bold">{WORKFLOW_STAGES[currentStageIndex]?.label}</p>
          </div>

          {/* Advance Workflow */}
          {nextStages.length > 0 && (
            <div className="mt-4">
              <p className="text-sm font-medium mb-2">Next Steps Available:</p>
              <div className="flex gap-2 flex-wrap">
                {nextStages.map(stage => (
                  <Button key={stage} size="sm" onClick={() => { setSelectedNextStage(stage); setShowAdvanceModal(true); }}>
                    {WORKFLOW_STAGES.find(s => s.key === stage)?.label.split('. ')[1] || stage}
                    <ChevronRight className="w-4 h-4 ml-1" />
                  </Button>
                ))}
              </div>
            </div>
          )}
          
          {nextStages.length === 0 && returnReq.return_status === 'closed' && (
            <div className="mt-4 p-3 bg-green-50 border border-green-200 rounded-lg text-sm text-green-800">
              ✓ Return workflow complete
            </div>
          )}
        </CardContent>
      </Card>

      {/* Return Details */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="font-[Manrope] text-lg">Return Information</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            <div className="grid grid-cols-2 gap-3">
              <div><p className="text-muted-foreground">Customer</p><p className="font-medium">{returnReq.customer_name}</p></div>
              <div><p className="text-muted-foreground">Phone</p><p className="font-medium font-[JetBrains_Mono]">{returnReq.phone}</p></div>
              <div><p className="text-muted-foreground">Reason</p><p className="font-medium capitalize">{returnReq.return_reason?.replace(/_/g, ' ')}</p></div>
              <div><p className="text-muted-foreground">Damage Category</p><p className="font-medium capitalize">{returnReq.damage_category?.replace(/_/g, ' ') || '-'}</p></div>
            </div>
            {returnReq.return_reason_details && (
              <div><p className="text-muted-foreground">Details</p><p>{returnReq.return_reason_details}</p></div>
            )}
            {returnReq.is_installation_related && (
              <Badge variant="outline" className="text-xs">Installation Related</Badge>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="font-[Manrope] text-lg">Workflow Details</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            {returnReq.authorized_date && <div className="flex justify-between"><span className="text-muted-foreground">Authorized:</span><span>{safeDate(returnReq.authorized_date)}</span></div>}
            {returnReq.return_tracking_number && <div className="flex justify-between"><span className="text-muted-foreground">Tracking:</span><span className="font-[JetBrains_Mono]">{returnReq.return_tracking_number}</span></div>}
            {returnReq.warehouse_received_date && <div className="flex justify-between"><span className="text-muted-foreground">Received:</span><span>{safeDate(returnReq.warehouse_received_date)}</span></div>}
            {returnReq.qc_passed !== null && <div className="flex justify-between"><span className="text-muted-foreground">QC Passed:</span><Badge variant={returnReq.qc_passed ? 'default' : 'destructive'}>{returnReq.qc_passed ? 'Yes' : 'No'}</Badge></div>}
            {returnReq.claim_amount && <div className="flex justify-between"><span className="text-muted-foreground">Claim Amount:</span><span>₹{returnReq.claim_amount}</span></div>}
            {returnReq.refund_amount && <div className="flex justify-between"><span className="text-muted-foreground">Refund Amount:</span><span className="font-semibold text-green-600">₹{returnReq.refund_amount}</span></div>}
          </CardContent>
        </Card>
      </div>

      {/* Damage Images */}
      {returnReq.damage_images?.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="font-[Manrope] text-lg">Damage/QC Images</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-3 md:grid-cols-4 gap-3">
              {returnReq.damage_images.map((img, idx) => (
                <img key={idx} src={img} alt={`Damage ${idx + 1}`} className="w-full h-32 object-cover rounded-lg border cursor-pointer hover:opacity-80" onClick={() => window.open(img, '_blank')} />
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Status History */}
      {returnReq.status_history?.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="font-[Manrope] text-lg">Status History</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {returnReq.status_history.map((h, i) => (
                <div key={i} className="flex items-center justify-between p-2 bg-secondary/30 rounded text-xs">
                  <div className="flex items-center gap-2">
                    <span className="capitalize">{h.from_status?.replace(/_/g, ' ')}</span>
                    <ChevronRight className="w-3 h-3" />
                    <span className="font-medium capitalize">{h.to_status?.replace(/_/g, ' ')}</span>
                  </div>
                  <span className="text-muted-foreground">{safeDate(h.changed_at)}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Advance Workflow Modal */}
      {showAdvanceModal && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <Card className="w-full max-w-md max-h-[90vh] overflow-y-auto">
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle className="font-[Manrope] text-base">
                  Advance to: {WORKFLOW_STAGES.find(s => s.key === selectedNextStage)?.label}
                </CardTitle>
                <p className="text-xs text-muted-foreground mt-1">
                  <AlertCircle className="w-3 h-3 inline mr-1" />Fill required information
                </p>
              </div>
              <Button variant="ghost" size="sm" onClick={() => { setShowAdvanceModal(false); setSelectedNextStage(''); setStageFormData({}); }}>
                <X className="w-4 h-4" />
              </Button>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleAdvanceWorkflow} className="space-y-4">
                {renderStageForm()}
                
                <div>
                  <label className="text-sm font-medium">Internal Notes</label>
                  <Input value={stageFormData.notes || ''} onChange={e => setStageFormData({...stageFormData, notes: e.target.value})} placeholder="Optional notes" />
                </div>
                
                <div className="flex gap-3 pt-4 border-t">
                  <Button type="button" variant="outline" onClick={() => { setShowAdvanceModal(false); setSelectedNextStage(''); setStageFormData({}); }} className="flex-1">Cancel</Button>
                  <Button type="submit" className="flex-1" disabled={uploadingImages}>
                    {uploadingImages ? 'Uploading...' : 'Advance Workflow'}
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
};
