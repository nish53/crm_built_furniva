import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api from '../lib/api';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { toast } from 'sonner';
import {
  ArrowLeft, Package, Clock, CheckCircle2, Truck, AlertTriangle,
  Camera, User, Calendar, Wrench, X, ChevronRight, MapPin, Undo2
} from 'lucide-react';
import { format } from 'date-fns';

// Replacement workflow stages
const WORKFLOW_STAGES = [
  { key: 'Replacement Pending', label: 'Pending', icon: Clock },
  { key: 'Priority Review', label: 'Priority Review', icon: AlertTriangle },
  { key: 'Ship Replacement', label: 'Ship', icon: Package },
  { key: 'Tracking Added', label: 'In Transit', icon: Truck },
  { key: 'Delivered', label: 'Delivered', icon: MapPin },
  { key: 'Issue Resolved', label: 'Resolved', icon: CheckCircle2 },
];

const TERMINAL_STATUSES = ['Issue Resolved', 'Issue Not Resolved'];

const statusColors = {
  'Replacement Pending': 'bg-orange-100 text-orange-800',
  'Priority Review': 'bg-red-100 text-red-800',
  'Ship Replacement': 'bg-blue-100 text-blue-800',
  'Tracking Added': 'bg-cyan-100 text-cyan-800',
  'Delivered': 'bg-green-100 text-green-800',
  'Issue Resolved': 'bg-emerald-100 text-emerald-800',
  'Issue Not Resolved': 'bg-red-100 text-red-800',
};

const getNextActions = (status) => {
  switch (status) {
    case 'Replacement Pending':
      return [
        { label: 'Mark Priority', status: 'Priority Review' },
        { label: 'Ship Replacement', status: 'Ship Replacement' },
      ];
    case 'Priority Review':
      return [{ label: 'Ship Replacement', status: 'Ship Replacement' }];
    case 'Ship Replacement':
      return [{ label: 'Add Tracking', status: 'Tracking Added', needsTracking: true }];
    case 'Tracking Added':
      return [{ label: 'Mark Delivered', status: 'Delivered' }];
    case 'Delivered':
      return [
        { label: 'Issue Resolved', status: 'Issue Resolved', needsNotes: true },
        { label: 'Not Resolved', status: 'Issue Not Resolved', needsNotes: true },
      ];
    default:
      return [];
  }
};

export const ReplacementDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [replacement, setReplacement] = useState(null);
  const [loading, setLoading] = useState(true);
  const [updating, setUpdating] = useState(false);
  const [showActionModal, setShowActionModal] = useState(false);
  const [selectedAction, setSelectedAction] = useState(null);
  const [trackingNumber, setTrackingNumber] = useState('');
  const [courierPartner, setCourierPartner] = useState('');
  const [resolutionNotes, setResolutionNotes] = useState('');

  useEffect(() => {
    fetchReplacement();
  }, [id]);

  const fetchReplacement = async () => {
    try {
      const res = await api.get(`/replacement-requests/${id}`);
      setReplacement(res.data);
    } catch (err) {
      toast.error('Failed to fetch replacement details');
    } finally {
      setLoading(false);
    }
  };

  const handleStatusUpdate = async () => {
    if (!selectedAction) return;
    if (selectedAction.needsTracking && !trackingNumber) {
      toast.error('Tracking number is required');
      return;
    }
    setUpdating(true);
    try {
      const params = { new_status: selectedAction.status };
      if (trackingNumber) params.tracking_number = trackingNumber;
      if (courierPartner) params.courier_partner = courierPartner;
      if (resolutionNotes) params.resolution_notes = resolutionNotes;

      await api.patch(`/replacement-requests/${id}/status`, null, { params });
      toast.success(`Status updated to: ${selectedAction.status}`);
      setShowActionModal(false);
      setSelectedAction(null);
      setTrackingNumber('');
      setCourierPartner('');
      setResolutionNotes('');
      fetchReplacement();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to update status');
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

  if (!replacement) {
    return (
      <div className="text-center py-12">
        <p className="text-muted-foreground">Replacement request not found</p>
      </div>
    );
  }

  const currentStageIdx = WORKFLOW_STAGES.findIndex(s => s.key === replacement.replacement_status);
  const isTerminal = TERMINAL_STATUSES.includes(replacement.replacement_status);
  const actions = getNextActions(replacement.replacement_status);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button variant="ghost" onClick={() => navigate('/replacements')}>
          <ArrowLeft className="w-4 h-4 mr-2" />Back
        </Button>
        <div className="flex-1">
          <h1 className="text-2xl font-bold font-[Manrope] tracking-tight">
            Replacement #{replacement.order_number}
          </h1>
          <p className="text-muted-foreground mt-1">
            Created {safeDate(replacement.created_at)}
          </p>
        </div>
        <Badge className={`text-sm px-3 py-1 ${statusColors[replacement.replacement_status] || 'bg-gray-100 text-gray-800'}`}>
          {replacement.replacement_status}
        </Badge>
      </div>

      {/* Visual Stepper */}
      <Card>
        <CardHeader>
          <CardTitle className="font-[Manrope] text-lg">Workflow Progress</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center overflow-x-auto pb-2 gap-2">
            {WORKFLOW_STAGES.map((stage, idx) => {
              const Icon = stage.icon;
              const isCompleted = currentStageIdx >= 0 && idx < currentStageIdx;
              const isCurrent = stage.key === replacement.replacement_status;
              const isPending = currentStageIdx >= 0 ? idx > currentStageIdx : true;

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
                      {isCompleted ? <CheckCircle2 className="w-5 h-5" /> : <Icon className="w-5 h-5" />}
                    </div>
                    <span className={`text-xs mt-2 text-center leading-tight ${
                      isCurrent ? 'font-medium text-foreground' : 'text-muted-foreground'
                    }`}>
                      {stage.label}
                    </span>
                  </div>
                  {idx < WORKFLOW_STAGES.length - 1 && (
                    <div className={`h-0.5 w-6 flex-shrink-0 mt-[-16px] ${
                      isCompleted ? 'bg-green-500' : 'bg-border'
                    }`} />
                  )}
                </React.Fragment>
              );
            })}
          </div>
          {replacement.replacement_status === 'Issue Not Resolved' && (
            <div className="mt-3 p-3 bg-red-50 rounded-lg border border-red-200 text-center">
              <X className="w-5 h-5 text-red-600 mx-auto mb-1" />
              <p className="text-sm font-medium text-red-800">Issue Not Resolved - Needs Follow-up</p>
            </div>
          )}
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Info */}
        <div className="lg:col-span-2 space-y-6">
          {/* Replacement Info */}
          <Card>
            <CardHeader>
              <CardTitle className="font-[Manrope] flex items-center gap-2">
                <Wrench className="w-5 h-5" />Replacement Information
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4 text-sm">
                <InfoField label="Order Number" value={replacement.order_number} mono />
                <InfoField label="Reason" value={replacement.replacement_reason} />
                <InfoField label="Requested" value={safeDate(replacement.requested_date)} />
                <InfoField label="Tracking" value={replacement.tracking_number || '-'} mono />
                <InfoField label="Courier" value={replacement.courier_partner || '-'} />
                <InfoField label="Replacement Cost" value={replacement.replacement_cost ? `\u20B9${replacement.replacement_cost}` : '-'} />
                <InfoField label="Priority Review" value={safeDate(replacement.priority_review_date)} />
                <InfoField label="Ship Date" value={safeDate(replacement.ship_date)} />
                <InfoField label="Delivered" value={safeDate(replacement.delivered_date)} />
              </div>
              <div className="mt-4 p-3 bg-muted/50 rounded-lg">
                <p className="text-xs text-muted-foreground mb-1">Damage Description</p>
                <p className="text-sm">{replacement.damage_description}</p>
              </div>
              {replacement.resolution_notes && (
                <div className="mt-3 p-3 bg-green-50 rounded-lg border border-green-200">
                  <p className="text-xs text-green-700 mb-1">Resolution Notes</p>
                  <p className="text-sm text-green-900">{replacement.resolution_notes}</p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Customer */}
          <Card>
            <CardHeader>
              <CardTitle className="font-[Manrope] flex items-center gap-2">
                <User className="w-5 h-5" />Customer
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <InfoField label="Name" value={replacement.customer_name} />
                <InfoField label="Phone" value={replacement.phone} mono />
              </div>
            </CardContent>
          </Card>

          {/* Damage Images */}
          {replacement.damage_images && replacement.damage_images.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="font-[Manrope] flex items-center gap-2">
                  <Camera className="w-5 h-5" />Damage Images
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  {replacement.damage_images.map((img, idx) => (
                    <a key={idx} href={img} target="_blank" rel="noopener noreferrer">
                      <img
                        src={img}
                        alt={`Damage ${idx + 1}`}
                        className="w-full h-32 object-cover rounded-lg border hover:opacity-80 transition-opacity"
                        onError={(e) => { e.target.style.display = 'none'; e.target.nextSibling && (e.target.nextSibling.style.display = 'flex'); }}
                      />
                      <div className="hidden w-full h-32 bg-muted rounded-lg border items-center justify-center">
                        <span className="text-xs text-muted-foreground">Image {idx + 1}</span>
                      </div>
                    </a>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Status History */}
          {replacement.status_history && replacement.status_history.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="font-[Manrope] flex items-center gap-2">
                  <Clock className="w-5 h-5" />Status History
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {[...replacement.status_history].reverse().map((entry, idx) => (
                    <div key={idx} className="flex items-start gap-3 text-sm border-l-2 border-primary/20 pl-4 py-2">
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <span className="font-medium">
                            {entry.from_status || 'Created'} \u2192 {entry.to_status}
                          </span>
                        </div>
                        <p className="text-xs text-muted-foreground mt-0.5">
                          {safeDate(entry.changed_at)} {entry.changed_by ? `by ${entry.changed_by}` : ''}
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
              {actions.map((action, idx) => (
                <Button
                  key={idx}
                  className="w-full"
                  variant={idx === 0 ? 'default' : 'outline'}
                  onClick={() => {
                    if (action.needsTracking || action.needsNotes) {
                      setSelectedAction(action);
                      setShowActionModal(true);
                    } else {
                      setSelectedAction(action);
                      // Direct update
                      const params = { new_status: action.status };
                      setUpdating(true);
                      api.patch(`/replacement-requests/${id}/status`, null, { params })
                        .then(() => {
                          toast.success(`Status updated to: ${action.status}`);
                          fetchReplacement();
                        })
                        .catch(err => toast.error(err.response?.data?.detail || 'Failed to update'))
                        .finally(() => setUpdating(false));
                    }
                  }}
                  disabled={updating}
                >
                  <ChevronRight className="w-4 h-4 mr-2" />{action.label}
                </Button>
              ))}

              <Button variant="outline" className="w-full" onClick={() => navigate(`/orders/${replacement.order_id}`)}>
                <Package className="w-4 h-4 mr-2" />View Order
              </Button>

              {isTerminal && (
                <div className={`p-3 rounded-lg border text-center ${
                  replacement.replacement_status === 'Issue Resolved'
                    ? 'bg-green-50 border-green-200'
                    : 'bg-red-50 border-red-200'
                }`}>
                  {replacement.replacement_status === 'Issue Resolved'
                    ? <CheckCircle2 className="w-6 h-6 text-green-600 mx-auto mb-1" />
                    : <X className="w-6 h-6 text-red-600 mx-auto mb-1" />
                  }
                  <p className={`text-sm font-medium ${
                    replacement.replacement_status === 'Issue Resolved' ? 'text-green-800' : 'text-red-800'
                  }`}>
                    {replacement.replacement_status}
                  </p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Timeline Quick View */}
          <Card>
            <CardHeader>
              <CardTitle className="font-[Manrope] text-sm">Timeline</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 text-sm">
              <TimelineItem label="Requested" date={replacement.requested_date} />
              <TimelineItem label="Priority Review" date={replacement.priority_review_date} />
              <TimelineItem label="Shipped" date={replacement.ship_date} />
              <TimelineItem label="Tracking Added" date={replacement.tracking_added_date} />
              <TimelineItem label="Delivered" date={replacement.delivered_date} />
              <TimelineItem label="Resolved" date={replacement.resolved_date} />
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Action Modal */}
      {showActionModal && selectedAction && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <Card className="w-full max-w-md">
            <CardHeader>
              <CardTitle className="font-[Manrope]">{selectedAction.label}</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {selectedAction.needsTracking && (
                <>
                  <div>
                    <label className="text-xs font-medium text-muted-foreground">Tracking Number *</label>
                    <Input
                      value={trackingNumber}
                      onChange={(e) => setTrackingNumber(e.target.value)}
                      placeholder="Enter tracking number"
                    />
                  </div>
                  <div>
                    <label className="text-xs font-medium text-muted-foreground">Courier Partner</label>
                    <Input
                      value={courierPartner}
                      onChange={(e) => setCourierPartner(e.target.value)}
                      placeholder="Delhivery, BlueDart, etc."
                    />
                  </div>
                </>
              )}
              {selectedAction.needsNotes && (
                <div>
                  <label className="text-xs font-medium text-muted-foreground">Resolution Notes</label>
                  <textarea
                    value={resolutionNotes}
                    onChange={(e) => setResolutionNotes(e.target.value)}
                    placeholder="Describe the resolution outcome..."
                    className="w-full p-2 border rounded-md min-h-[100px] text-sm"
                  />
                </div>
              )}
              <div className="flex gap-3 pt-2">
                <Button variant="outline" className="flex-1" onClick={() => {
                  setShowActionModal(false);
                  setSelectedAction(null);
                  setTrackingNumber('');
                  setCourierPartner('');
                  setResolutionNotes('');
                }}>
                  Cancel
                </Button>
                <Button
                  className="flex-1"
                  onClick={handleStatusUpdate}
                  disabled={updating || (selectedAction.needsTracking && !trackingNumber)}
                >
                  {updating ? 'Updating...' : 'Confirm'}
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

const TimelineItem = ({ label, date }) => (
  <div className="flex justify-between items-center">
    <span className="text-muted-foreground">{label}</span>
    <span className={`text-xs ${date ? 'font-medium' : 'text-muted-foreground'}`}>
      {date ? format(new Date(date), 'MMM dd, HH:mm') : '-'}
    </span>
  </div>
);
