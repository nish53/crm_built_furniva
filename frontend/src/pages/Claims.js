import React, { useState, useEffect, useCallback } from 'react';
import { useLocation } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Input } from '../components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import api from '../lib/api';
import { toast } from 'sonner';
import {
  FileText, Plus, Search, Filter, DollarSign, Clock,
  CheckCircle, XCircle, AlertTriangle, Eye, ChevronDown,
  ChevronUp, MessageSquare, Paperclip, BarChart3, X
} from 'lucide-react';
import { format } from 'date-fns';

const STATUS_OPTIONS = [
  { value: 'draft', label: 'Draft' },
  { value: 'filed', label: 'Filed' },
  { value: 'under_review', label: 'Under Review' },
  { value: 'approved', label: 'Approved' },
  { value: 'partially_approved', label: 'Partially Approved' },
  { value: 'rejected', label: 'Rejected' },
  { value: 'appealed', label: 'Appealed' },
  { value: 'closed', label: 'Closed' },
];

const TYPE_OPTIONS = [
  { value: 'courier_damage', label: 'Courier Damage' },
  { value: 'marketplace_a_to_z', label: 'Amazon A-to-Z' },
  { value: 'marketplace_safe_t', label: 'Amazon SAFE-T' },
  { value: 'insurance', label: 'Insurance' },
  { value: 'warranty', label: 'Warranty' },
  { value: 'other', label: 'Other' },
];

const statusColors = {
  draft: 'bg-gray-100 text-gray-800',
  filed: 'bg-blue-100 text-blue-800',
  under_review: 'bg-purple-100 text-purple-800',
  approved: 'bg-green-100 text-green-800',
  partially_approved: 'bg-amber-100 text-amber-800',
  rejected: 'bg-red-100 text-red-800',
  appealed: 'bg-orange-100 text-orange-800',
  closed: 'bg-gray-100 text-gray-800',
};

const statusIcons = {
  draft: Clock,
  filed: FileText,
  under_review: Search,
  approved: CheckCircle,
  partially_approved: AlertTriangle,
  rejected: XCircle,
  appealed: AlertTriangle,
  closed: CheckCircle,
};

export const Claims = () => {
  const location = useLocation();
  const [claims, setClaims] = useState([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('all');
  const [typeFilter, setTypeFilter] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [expandedClaim, setExpandedClaim] = useState(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showStatusModal, setShowStatusModal] = useState(false);
  const [showCorrespondenceModal, setShowCorrespondenceModal] = useState(false);
  const [selectedClaim, setSelectedClaim] = useState(null);
  const [analytics, setAnalytics] = useState({ byType: [], byStatus: [] });
  const [showAnalytics, setShowAnalytics] = useState(false);
  
  // Apply filter from navigation state
  useEffect(() => {
    if (location.state?.filterStatus) {
      setStatusFilter(location.state.filterStatus);
    }
  }, [location.state]);
  
  // Create form
  const [createForm, setCreateForm] = useState({
    order_id: '', type: 'courier_damage', amount: '', description: '',
    platform: '', reference_number: ''
  });
  
  // Status update form
  const [statusForm, setStatusForm] = useState({
    status: '', approved_amount: '', rejection_reason: '', resolution_notes: ''
  });
  
  // Correspondence form
  const [corrForm, setCorrForm] = useState({
    message: '', to_party: '', comm_type: 'note'
  });

  const fetchClaims = useCallback(async () => {
    try {
      const params = {};
      if (statusFilter !== 'all') params.status = statusFilter;
      if (typeFilter !== 'all') params.claim_type = typeFilter;
      if (searchQuery) params.search = searchQuery;
      const res = await api.get('/claims/', { params });
      setClaims(res.data || []);
    } catch (err) {
      toast.error('Failed to fetch claims');
    } finally {
      setLoading(false);
    }
  }, [statusFilter, typeFilter, searchQuery]);

  const fetchAnalytics = async () => {
    try {
      const [byType, byStatus] = await Promise.all([
        api.get('/claims/analytics/by-type'),
        api.get('/claims/analytics/by-status'),
      ]);
      setAnalytics({
        byType: byType.data?.analytics || [],
        byStatus: byStatus.data?.analytics || []
      });
    } catch (err) {
      // Analytics may fail silently
    }
  };

  useEffect(() => {
    fetchClaims();
    fetchAnalytics();
  }, [fetchClaims]);

  const handleCreateClaim = async () => {
    if (!createForm.order_id || !createForm.amount || !createForm.description) {
      toast.error('Order ID, amount, and description are required');
      return;
    }
    try {
      await api.post('/claims/', {
        ...createForm,
        amount: parseFloat(createForm.amount),
        status: 'filed'
      });
      toast.success('Claim created successfully');
      setShowCreateModal(false);
      setCreateForm({ order_id: '', type: 'courier_damage', amount: '', description: '', platform: '', reference_number: '' });
      fetchClaims();
      fetchAnalytics();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to create claim');
    }
  };

  const handleUpdateStatus = async () => {
    if (!selectedClaim || !statusForm.status) return;
    try {
      const params = { status: statusForm.status };
      if (statusForm.approved_amount) params.approved_amount = parseFloat(statusForm.approved_amount);
      if (statusForm.rejection_reason) params.rejection_reason = statusForm.rejection_reason;
      if (statusForm.resolution_notes) params.resolution_notes = statusForm.resolution_notes;
      
      await api.patch(`/claims/${selectedClaim.id}/status`, null, { params });
      toast.success('Claim status updated');
      setShowStatusModal(false);
      setStatusForm({ status: '', approved_amount: '', rejection_reason: '', resolution_notes: '' });
      fetchClaims();
      fetchAnalytics();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to update status');
    }
  };

  const handleAddCorrespondence = async () => {
    if (!selectedClaim || !corrForm.message) return;
    try {
      const params = { message: corrForm.message };
      if (corrForm.to_party) params.to_party = corrForm.to_party;
      if (corrForm.comm_type) params.comm_type = corrForm.comm_type;
      
      await api.post(`/claims/${selectedClaim.id}/correspondence`, null, { params });
      toast.success('Correspondence added');
      setShowCorrespondenceModal(false);
      setCorrForm({ message: '', to_party: '', comm_type: 'note' });
      fetchClaims();
    } catch (err) {
      toast.error('Failed to add correspondence');
    }
  };

  const safeDate = (d) => {
    if (!d) return '-';
    try { return format(new Date(d), 'MMM dd, yyyy HH:mm'); }
    catch { return '-'; }
  };

  const totalAmount = claims.reduce((acc, c) => acc + (c.amount || 0), 0);
  const approvedAmount = claims.reduce((acc, c) => acc + (c.approved_amount || 0), 0);

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold font-[Manrope]">Claims Management</h1>
          <p className="text-muted-foreground mt-1">Track and manage all claims across platforms</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => setShowAnalytics(!showAnalytics)}>
            <BarChart3 className="w-4 h-4 mr-2" />{showAnalytics ? 'Hide' : 'Show'} Analytics
          </Button>
          <Button onClick={() => setShowCreateModal(true)}>
            <Plus className="w-4 h-4 mr-2" />New Claim
          </Button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <p className="text-sm text-muted-foreground">Total Claims</p>
            <p className="text-2xl font-bold">{claims.length}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <p className="text-sm text-muted-foreground">Total Filed</p>
            <p className="text-2xl font-bold font-[JetBrains_Mono]">₹{totalAmount.toLocaleString()}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <p className="text-sm text-muted-foreground">Approved</p>
            <p className="text-2xl font-bold text-green-600 font-[JetBrains_Mono]">₹{approvedAmount.toLocaleString()}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <p className="text-sm text-muted-foreground">Pending Review</p>
            <p className="text-2xl font-bold text-orange-600">
              {claims.filter(c => ['filed', 'under_review', 'appealed'].includes(c.status)).length}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Analytics Section */}
      {showAnalytics && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Card>
            <CardHeader><CardTitle className="text-sm font-[Manrope]">By Type</CardTitle></CardHeader>
            <CardContent>
              {analytics.byType.length === 0 ? (
                <p className="text-sm text-muted-foreground">No data</p>
              ) : (
                <div className="space-y-2">
                  {analytics.byType.map((item, idx) => (
                    <div key={idx} className="flex items-center justify-between text-sm">
                      <span className="capitalize">{(item._id || 'Unknown').replace(/_/g, ' ')}</span>
                      <div className="flex items-center gap-3">
                        <Badge variant="outline">{item.count}</Badge>
                        <span className="font-[JetBrains_Mono] text-xs">₹{(item.total_amount || 0).toLocaleString()}</span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
          <Card>
            <CardHeader><CardTitle className="text-sm font-[Manrope]">By Status</CardTitle></CardHeader>
            <CardContent>
              {analytics.byStatus.length === 0 ? (
                <p className="text-sm text-muted-foreground">No data</p>
              ) : (
                <div className="space-y-2">
                  {analytics.byStatus.map((item, idx) => (
                    <div key={idx} className="flex items-center justify-between text-sm">
                      <Badge className={statusColors[item._id] || 'bg-gray-100 text-gray-800'}>
                        {(item._id || 'Unknown').replace(/_/g, ' ')}
                      </Badge>
                      <div className="flex items-center gap-3">
                        <span className="font-medium">{item.count}</span>
                        <span className="font-[JetBrains_Mono] text-xs">₹{(item.total_amount || 0).toLocaleString()}</span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <Input
            className="pl-10"
            placeholder="Search by order ID, description, reference..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-[160px]">
            <SelectValue placeholder="Status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Statuses</SelectItem>
            {STATUS_OPTIONS.map(s => (
              <SelectItem key={s.value} value={s.value}>{s.label}</SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Select value={typeFilter} onValueChange={setTypeFilter}>
          <SelectTrigger className="w-[160px]">
            <SelectValue placeholder="Type" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Types</SelectItem>
            {TYPE_OPTIONS.map(t => (
              <SelectItem key={t.value} value={t.value}>{t.label}</SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Button variant="outline" size="sm" onClick={() => { setStatusFilter('all'); setTypeFilter('all'); setSearchQuery(''); }}>
          Clear
        </Button>
      </div>

      {/* Claims List */}
      <Card>
        <CardHeader>
          <CardTitle className="font-[Manrope]">Claims ({claims.length})</CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="text-center py-12">
              <p className="text-muted-foreground">Loading claims...</p>
            </div>
          ) : claims.length === 0 ? (
            <div className="text-center py-12">
              <FileText className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
              <p className="text-muted-foreground">No claims found</p>
            </div>
          ) : (
            <div className="space-y-3">
              {claims.map((claim) => {
                const isExpanded = expandedClaim === claim.id;
                const StatusIcon = statusIcons[claim.status] || FileText;
                
                return (
                  <div key={claim.id} className="border rounded-lg overflow-hidden">
                    {/* Claim Row */}
                    <div
                      className="p-4 flex items-center gap-4 cursor-pointer hover:bg-secondary/20 transition-colors"
                      onClick={() => setExpandedClaim(isExpanded ? null : claim.id)}
                    >
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="font-[JetBrains_Mono] text-sm font-medium">{claim.order_id}</span>
                          <Badge className={statusColors[claim.status] || 'bg-gray-100'}>
                            <StatusIcon className="w-3 h-3 mr-1" />
                            {claim.status?.replace(/_/g, ' ')}
                          </Badge>
                          <Badge variant="outline" className="capitalize text-xs">
                            {(claim.type || '').replace(/_/g, ' ')}
                          </Badge>
                        </div>
                        <p className="text-sm text-muted-foreground truncate">{claim.description}</p>
                      </div>
                      <div className="text-right flex-shrink-0">
                        <p className="font-[JetBrains_Mono] font-medium">₹{(claim.amount || 0).toLocaleString()}</p>
                        {claim.approved_amount > 0 && (
                          <p className="text-xs text-green-600">Approved: ₹{claim.approved_amount.toLocaleString()}</p>
                        )}
                      </div>
                      <div className="text-xs text-muted-foreground flex-shrink-0 w-24 text-right">
                        {safeDate(claim.created_at)}
                      </div>
                      {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                    </div>

                    {/* Expanded Detail */}
                    {isExpanded && (
                      <div className="border-t bg-muted/30 p-4 space-y-4">
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                          <div>
                            <p className="text-xs text-muted-foreground">Filed By</p>
                            <p className="font-medium">{claim.filed_by}</p>
                          </div>
                          <div>
                            <p className="text-xs text-muted-foreground">Platform</p>
                            <p className="font-medium">{claim.platform || '-'}</p>
                          </div>
                          <div>
                            <p className="text-xs text-muted-foreground">Reference #</p>
                            <p className="font-[JetBrains_Mono] text-sm">{claim.reference_number || '-'}</p>
                          </div>
                          <div>
                            <p className="text-xs text-muted-foreground">Reviewed By</p>
                            <p className="font-medium">{claim.reviewed_by || '-'}</p>
                          </div>
                        </div>

                        {claim.rejection_reason && (
                          <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
                            <p className="text-xs text-red-700 mb-1">Rejection Reason</p>
                            <p className="text-sm text-red-900">{claim.rejection_reason}</p>
                          </div>
                        )}

                        {claim.resolution_notes && (
                          <div className="p-3 bg-green-50 border border-green-200 rounded-lg">
                            <p className="text-xs text-green-700 mb-1">Resolution</p>
                            <p className="text-sm text-green-900">{claim.resolution_notes}</p>
                          </div>
                        )}

                        {/* Status History */}
                        {claim.status_history && claim.status_history.length > 0 && (
                          <div>
                            <p className="text-xs font-medium text-muted-foreground mb-2">Status History</p>
                            <div className="space-y-1">
                              {[...claim.status_history].reverse().map((h, idx) => (
                                <div key={idx} className="flex items-center gap-2 text-xs">
                                  <Badge className={`${statusColors[h.status] || 'bg-gray-100'} text-[10px]`}>
                                    {h.status?.replace(/_/g, ' ')}
                                  </Badge>
                                  <span className="text-muted-foreground">{safeDate(h.changed_at)}</span>
                                  <span className="text-muted-foreground">by {h.changed_by}</span>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* Correspondence */}
                        {claim.correspondence && claim.correspondence.length > 0 && (
                          <div>
                            <p className="text-xs font-medium text-muted-foreground mb-2">Correspondence ({claim.correspondence.length})</p>
                            <div className="space-y-2 max-h-40 overflow-y-auto">
                              {[...claim.correspondence].reverse().map((c, idx) => (
                                <div key={idx} className="p-2 bg-background border rounded text-xs">
                                  <div className="flex items-center gap-2 mb-1">
                                    <Badge variant="outline" className="text-[10px]">{c.type}</Badge>
                                    <span className="text-muted-foreground">{safeDate(c.date)}</span>
                                    <span>{c.from}</span>
                                    {c.to && <span className="text-muted-foreground">\u2192 {c.to}</span>}
                                  </div>
                                  <p>{c.message}</p>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* Documents */}
                        {claim.documents && claim.documents.length > 0 && (
                          <div>
                            <p className="text-xs font-medium text-muted-foreground mb-2">Documents ({claim.documents.length})</p>
                            <div className="flex flex-wrap gap-2">
                              {claim.documents.map((doc, idx) => (
                                <Badge key={idx} variant="outline" className="text-xs">
                                  <Paperclip className="w-3 h-3 mr-1" />
                                  {doc.filename || `Document ${idx + 1}`}
                                </Badge>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* Actions */}
                        <div className="flex flex-wrap gap-2 pt-2 border-t">
                          <Button size="sm" variant="outline" onClick={(e) => {
                            e.stopPropagation();
                            setSelectedClaim(claim);
                            setStatusForm({ ...statusForm, status: '' });
                            setShowStatusModal(true);
                          }}>
                            Update Status
                          </Button>
                          <Button size="sm" variant="outline" onClick={(e) => {
                            e.stopPropagation();
                            setSelectedClaim(claim);
                            setShowCorrespondenceModal(true);
                          }}>
                            <MessageSquare className="w-3 h-3 mr-1" />Add Note
                          </Button>
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Create Claim Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <Card className="w-full max-w-lg max-h-[80vh] overflow-y-auto">
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle className="font-[Manrope]">New Claim</CardTitle>
              <Button variant="ghost" size="sm" onClick={() => setShowCreateModal(false)}><X className="w-4 h-4" /></Button>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="text-xs font-medium text-muted-foreground">Order ID *</label>
                <Input value={createForm.order_id} onChange={e => setCreateForm({...createForm, order_id: e.target.value})} placeholder="Enter order ID" />
              </div>
              <div>
                <label className="text-xs font-medium text-muted-foreground">Claim Type *</label>
                <Select value={createForm.type} onValueChange={v => setCreateForm({...createForm, type: v})}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    {TYPE_OPTIONS.map(t => <SelectItem key={t.value} value={t.value}>{t.label}</SelectItem>)}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <label className="text-xs font-medium text-muted-foreground">Amount (₹) *</label>
                <Input type="number" step="0.01" value={createForm.amount} onChange={e => setCreateForm({...createForm, amount: e.target.value})} placeholder="Claim amount" />
              </div>
              <div>
                <label className="text-xs font-medium text-muted-foreground">Description *</label>
                <textarea
                  value={createForm.description}
                  onChange={e => setCreateForm({...createForm, description: e.target.value})}
                  placeholder="Describe the claim..."
                  className="w-full p-2 border rounded-md min-h-[80px] text-sm"
                />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-medium text-muted-foreground">Platform</label>
                  <Input value={createForm.platform} onChange={e => setCreateForm({...createForm, platform: e.target.value})} placeholder="Amazon, Flipkart..." />
                </div>
                <div>
                  <label className="text-xs font-medium text-muted-foreground">Reference #</label>
                  <Input value={createForm.reference_number} onChange={e => setCreateForm({...createForm, reference_number: e.target.value})} placeholder="Claim reference" />
                </div>
              </div>
              <div className="flex gap-3 pt-2">
                <Button variant="outline" className="flex-1" onClick={() => setShowCreateModal(false)}>Cancel</Button>
                <Button className="flex-1" onClick={handleCreateClaim}>Create Claim</Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Update Status Modal */}
      {showStatusModal && selectedClaim && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <Card className="w-full max-w-md">
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle className="font-[Manrope]">Update Claim Status</CardTitle>
              <Button variant="ghost" size="sm" onClick={() => setShowStatusModal(false)}><X className="w-4 h-4" /></Button>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="text-xs font-medium text-muted-foreground">Current Status</label>
                <Badge className={statusColors[selectedClaim.status] || 'bg-gray-100'}>
                  {selectedClaim.status?.replace(/_/g, ' ')}
                </Badge>
              </div>
              <div>
                <label className="text-xs font-medium text-muted-foreground">New Status *</label>
                <Select value={statusForm.status} onValueChange={v => setStatusForm({...statusForm, status: v})}>
                  <SelectTrigger><SelectValue placeholder="Select status" /></SelectTrigger>
                  <SelectContent>
                    {STATUS_OPTIONS.map(s => <SelectItem key={s.value} value={s.value}>{s.label}</SelectItem>)}
                  </SelectContent>
                </Select>
              </div>
              {['approved', 'partially_approved'].includes(statusForm.status) && (
                <div>
                  <label className="text-xs font-medium text-muted-foreground">Approved Amount</label>
                  <Input type="number" step="0.01" value={statusForm.approved_amount} onChange={e => setStatusForm({...statusForm, approved_amount: e.target.value})} placeholder="Amount approved" />
                </div>
              )}
              {statusForm.status === 'rejected' && (
                <div>
                  <label className="text-xs font-medium text-muted-foreground">Rejection Reason</label>
                  <Input value={statusForm.rejection_reason} onChange={e => setStatusForm({...statusForm, rejection_reason: e.target.value})} placeholder="Why was it rejected?" />
                </div>
              )}
              <div>
                <label className="text-xs font-medium text-muted-foreground">Notes</label>
                <Input value={statusForm.resolution_notes} onChange={e => setStatusForm({...statusForm, resolution_notes: e.target.value})} placeholder="Optional notes" />
              </div>
              <div className="flex gap-3 pt-2">
                <Button variant="outline" className="flex-1" onClick={() => setShowStatusModal(false)}>Cancel</Button>
                <Button className="flex-1" onClick={handleUpdateStatus} disabled={!statusForm.status}>Update</Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Correspondence Modal */}
      {showCorrespondenceModal && selectedClaim && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <Card className="w-full max-w-md">
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle className="font-[Manrope]">Add Correspondence</CardTitle>
              <Button variant="ghost" size="sm" onClick={() => setShowCorrespondenceModal(false)}><X className="w-4 h-4" /></Button>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="text-xs font-medium text-muted-foreground">Type</label>
                <Select value={corrForm.comm_type} onValueChange={v => setCorrForm({...corrForm, comm_type: v})}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="note">Note</SelectItem>
                    <SelectItem value="email">Email</SelectItem>
                    <SelectItem value="call">Call</SelectItem>
                    <SelectItem value="platform_message">Platform Message</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <label className="text-xs font-medium text-muted-foreground">To (optional)</label>
                <Input value={corrForm.to_party} onChange={e => setCorrForm({...corrForm, to_party: e.target.value})} placeholder="Recipient" />
              </div>
              <div>
                <label className="text-xs font-medium text-muted-foreground">Message *</label>
                <textarea
                  value={corrForm.message}
                  onChange={e => setCorrForm({...corrForm, message: e.target.value})}
                  placeholder="Enter message or note..."
                  className="w-full p-2 border rounded-md min-h-[100px] text-sm"
                />
              </div>
              <div className="flex gap-3 pt-2">
                <Button variant="outline" className="flex-1" onClick={() => setShowCorrespondenceModal(false)}>Cancel</Button>
                <Button className="flex-1" onClick={handleAddCorrespondence} disabled={!corrForm.message}>Add</Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
};
