import React, { useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../lib/api';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { toast } from 'sonner';
import {
  RefreshCcw, Search, X, Undo2, ChevronRight, Clock, AlertTriangle
} from 'lucide-react';
import { format } from 'date-fns';

const STATUS_FLOW = [
  'requested', 'approved', 'pickup_scheduled', 'in_transit',
  'received', 'inspected', 'refunded', 'replaced', 'rejected', 'cancelled'
];

const STATUS_LABELS = {
  requested: 'Requested', approved: 'Approved', pickup_scheduled: 'Pickup Scheduled',
  in_transit: 'In Transit', received: 'Received', inspected: 'Inspected',
  refunded: 'Refunded', replaced: 'Replaced', rejected: 'Rejected', cancelled: 'Cancelled'
};

const STATUS_COLORS = {
  requested: 'bg-yellow-100 text-yellow-800', approved: 'bg-blue-100 text-blue-800',
  pickup_scheduled: 'bg-indigo-100 text-indigo-800', in_transit: 'bg-purple-100 text-purple-800',
  received: 'bg-teal-100 text-teal-800', inspected: 'bg-cyan-100 text-cyan-800',
  refunded: 'bg-green-100 text-green-800', replaced: 'bg-green-100 text-green-800',
  rejected: 'bg-red-100 text-red-800', cancelled: 'bg-gray-100 text-gray-800'
};

export const Returns = () => {
  const navigate = useNavigate();
  const [returns, setReturns] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [selectedReturn, setSelectedReturn] = useState(null);

  // Status update form (for mandatory fields)
  const [pendingStatus, setPendingStatus] = useState(null);
  const [statusFields, setStatusFields] = useState({ pickup_date: '', tracking_number: '', courier_partner: '', notes: '', refund_amount: '' });

  const fetchReturns = useCallback(async () => {
    try {
      const params = {};
      if (statusFilter !== 'all') params.status = statusFilter;
      const res = await api.get('/returns/', { params });
      setReturns(res.data);
    } catch { toast.error('Failed to fetch returns'); }
    finally { setLoading(false); }
  }, [statusFilter]);

  useEffect(() => { fetchReturns(); }, [fetchReturns]);

  const getNextStatuses = (current) => {
    const idx = STATUS_FLOW.indexOf(current);
    if (idx === -1) return [];
    const next = [];
    // Allow forward transitions
    if (current === 'requested') next.push('approved', 'rejected');
    else if (current === 'approved') next.push('pickup_scheduled', 'cancelled');
    else if (current === 'pickup_scheduled') next.push('in_transit', 'cancelled');
    else if (current === 'in_transit') next.push('received');
    else if (current === 'received') next.push('inspected');
    else if (current === 'inspected') next.push('refunded', 'replaced', 'rejected');
    return next;
  };

  const initiateStatusChange = (ret, newStatus) => {
    // Check if mandatory fields needed
    if (newStatus === 'pickup_scheduled' || newStatus === 'in_transit') {
      setPendingStatus({ returnId: ret.id, status: newStatus });
      setStatusFields({ pickup_date: '', tracking_number: '', courier_partner: '', notes: '', refund_amount: '' });
    } else if (newStatus === 'refunded') {
      setPendingStatus({ returnId: ret.id, status: newStatus });
      setStatusFields({ pickup_date: '', tracking_number: '', courier_partner: '', notes: '', refund_amount: '' });
    } else {
      executeStatusChange(ret.id, newStatus, {});
    }
  };

  const executeStatusChange = async (returnId, status, fields) => {
    try {
      const params = new URLSearchParams({ status });
      if (fields.pickup_date) params.append('pickup_date', new Date(fields.pickup_date).toISOString());
      if (fields.tracking_number) params.append('tracking_number', fields.tracking_number);
      if (fields.courier_partner) params.append('courier_partner', fields.courier_partner);
      if (fields.notes) params.append('notes', fields.notes);
      if (fields.refund_amount) params.append('refund_amount', fields.refund_amount);

      const res = await api.patch(`/returns/${returnId}/status?${params.toString()}`);
      toast.success(`Status updated to ${STATUS_LABELS[status]}`);
      setSelectedReturn(res.data);
      setPendingStatus(null);
      fetchReturns();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to update status');
    }
  };

  const handleMandatorySubmit = (e) => {
    e.preventDefault();
    if (!pendingStatus) return;

    if (pendingStatus.status === 'pickup_scheduled' && !statusFields.pickup_date) {
      toast.error('Pickup date is required'); return;
    }
    if (pendingStatus.status === 'in_transit' && !statusFields.tracking_number) {
      toast.error('Tracking number is required'); return;
    }

    executeStatusChange(pendingStatus.returnId, pendingStatus.status, statusFields);
  };

  const handleUndo = async (ret) => {
    if (!ret.previous_status) {
      toast.error('No previous status to revert to');
      return;
    }
    if (!confirm(`Undo status change? Will revert from "${STATUS_LABELS[ret.return_status]}" to "${STATUS_LABELS[ret.previous_status]}"`)) return;
    try {
      const res = await api.patch(`/returns/${ret.id}/undo`);
      toast.success(`Reverted to ${STATUS_LABELS[res.data.return_status]}`);
      setSelectedReturn(res.data);
      fetchReturns();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to undo');
    }
  };

  const safeDateShort = (d) => { if (!d) return '-'; try { return format(new Date(d), 'MMM dd, yyyy'); } catch { return '-'; } };

  const filtered = returns.filter(r =>
    !searchTerm ||
    r.order_number?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    r.customer_name?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  if (loading) return (
    <div className="flex items-center justify-center h-[60vh]">
      <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-primary" />
    </div>
  );

  return (
    <div className="space-y-6" data-testid="returns-page">
      <div>
        <h1 className="text-3xl font-bold font-[Manrope]">Returns Management</h1>
        <p className="text-muted-foreground mt-1">Track and manage return requests</p>
      </div>

      {/* Filters */}
      <div className="flex gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <Input placeholder="Search by order or customer..." value={searchTerm}
            onChange={e => setSearchTerm(e.target.value)} className="pl-10" data-testid="returns-search" />
        </div>
        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-48" data-testid="returns-status-filter"><SelectValue placeholder="Filter by status" /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Statuses</SelectItem>
            {STATUS_FLOW.map(s => <SelectItem key={s} value={s}>{STATUS_LABELS[s]}</SelectItem>)}
          </SelectContent>
        </Select>
      </div>

      {filtered.length === 0 ? (
        <Card><CardContent className="py-12 text-center">
          <RefreshCcw className="w-12 h-12 mx-auto mb-4 text-muted-foreground" />
          <p className="text-muted-foreground">No return requests found</p>
          <p className="text-sm text-muted-foreground mt-1">Create returns from the Order Detail page</p>
        </CardContent></Card>
      ) : (
        <div className="space-y-3">
          {filtered.map(ret => (
            <Card key={ret.id} className="hover:border-primary/40 transition-colors cursor-pointer"
              onClick={() => navigate(`/returns/${ret.id}`)} data-testid={`return-card-${ret.id}`}>
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4 min-w-0">
                    <div className="min-w-0">
                      <div className="flex items-center gap-2">
                        <p className="font-semibold font-[JetBrains_Mono] text-sm">{ret.order_number}</p>
                        <Badge className={STATUS_COLORS[ret.return_status]}>{STATUS_LABELS[ret.return_status]}</Badge>
                      </div>
                      <p className="text-sm text-muted-foreground mt-0.5">{ret.customer_name} - {ret.phone}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3 text-sm text-muted-foreground">
                    <span>{safeDateShort(ret.requested_date)}</span>
                    <Badge variant="outline" className="text-xs capitalize">{ret.return_reason?.replace(/_/g, ' ')}</Badge>
                    <ChevronRight className="w-4 h-4" />
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* ===== RETURN DETAIL MODAL ===== */}
      {selectedReturn && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4" data-testid="return-detail-modal">
          <Card className="w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle className="font-[Manrope]">Return: {selectedReturn.order_number}</CardTitle>
                <div className="flex items-center gap-2 mt-1">
                  <Badge className={STATUS_COLORS[selectedReturn.return_status]}>{STATUS_LABELS[selectedReturn.return_status]}</Badge>
                  {selectedReturn.previous_status && (
                    <span className="text-xs text-muted-foreground">
                      (prev: {STATUS_LABELS[selectedReturn.previous_status]})
                    </span>
                  )}
                </div>
              </div>
              <Button variant="ghost" size="sm" onClick={() => { setSelectedReturn(null); setPendingStatus(null); }}><X className="w-4 h-4" /></Button>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Return Info */}
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div><p className="text-xs text-muted-foreground">Customer</p><p className="font-medium">{selectedReturn.customer_name}</p></div>
                <div><p className="text-xs text-muted-foreground">Phone</p><p className="font-medium font-[JetBrains_Mono]">{selectedReturn.phone}</p></div>
                <div><p className="text-xs text-muted-foreground">Reason</p><p className="font-medium capitalize">{selectedReturn.return_reason?.replace(/_/g, ' ')}</p></div>
                <div><p className="text-xs text-muted-foreground">Damage Category</p><p className="font-medium capitalize">{selectedReturn.damage_category?.replace(/_/g, ' ') || '-'}</p></div>
                {selectedReturn.return_reason_details && (
                  <div className="col-span-2"><p className="text-xs text-muted-foreground">Details</p><p className="text-sm">{selectedReturn.return_reason_details}</p></div>
                )}
                {selectedReturn.is_installation_related && <Badge variant="outline" className="text-xs col-span-2 w-fit">Installation Related</Badge>}
              </div>

              {/* Timeline dates */}
              <div className="grid grid-cols-2 gap-3">
                <TimelineDate label="Requested" date={selectedReturn.requested_date} />
                <TimelineDate label="Approved" date={selectedReturn.approved_date} />
                <TimelineDate label="Pickup" date={selectedReturn.pickup_date} />
                <TimelineDate label="Received" date={selectedReturn.received_date} />
                <TimelineDate label="Inspected" date={selectedReturn.inspection_date} />
                <TimelineDate label="Refund" date={selectedReturn.refund_date} />
              </div>

              {/* Tracking Info */}
              {(selectedReturn.return_tracking_number || selectedReturn.courier_partner) && (
                <div className="p-3 bg-primary/5 rounded-lg">
                  <p className="text-xs text-muted-foreground mb-1">Return Tracking</p>
                  <p className="font-[JetBrains_Mono] font-medium">{selectedReturn.return_tracking_number || '-'}</p>
                  {selectedReturn.courier_partner && <p className="text-xs text-muted-foreground mt-1">via {selectedReturn.courier_partner}</p>}
                </div>
              )}

              {selectedReturn.refund_amount && (
                <div className="p-3 bg-green-50 rounded-lg border border-green-200">
                  <p className="text-xs text-muted-foreground">Refund Amount</p>
                  <p className="text-lg font-bold font-[JetBrains_Mono] text-green-700">₹{selectedReturn.refund_amount}</p>
                </div>
              )}

              {/* Status History */}
              {selectedReturn.status_history?.length > 0 && (
                <div>
                  <h4 className="text-sm font-semibold mb-2">Status History</h4>
                  <div className="space-y-1.5">
                    {selectedReturn.status_history.map((h, i) => (
                      <div key={i} className={`flex items-center justify-between text-xs p-2 rounded ${h.is_undo ? 'bg-orange-50' : 'bg-secondary/30'}`}>
                        <div className="flex items-center gap-2">
                          {h.is_undo && <Undo2 className="w-3 h-3 text-orange-500" />}
                          <span>{STATUS_LABELS[h.from_status]}</span>
                          <ChevronRight className="w-3 h-3" />
                          <span className="font-medium">{STATUS_LABELS[h.to_status]}</span>
                        </div>
                        <span className="text-muted-foreground">{safeDateShort(h.changed_at)}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Status Actions */}
              {!['refunded', 'replaced', 'rejected', 'cancelled'].includes(selectedReturn.return_status) && (
                <div className="border-t pt-4">
                  <h4 className="text-sm font-semibold mb-3">Update Status</h4>
                  <div className="flex flex-wrap gap-2">
                    {getNextStatuses(selectedReturn.return_status).map(s => (
                      <Button key={s} size="sm" variant={['rejected', 'cancelled'].includes(s) ? 'destructive' : 'outline'}
                        onClick={() => initiateStatusChange(selectedReturn, s)} data-testid={`status-btn-${s}`}>
                        {STATUS_LABELS[s]}
                      </Button>
                    ))}
                  </div>
                </div>
              )}

              {/* Undo Button */}
              {selectedReturn.previous_status && (
                <div className="border-t pt-4">
                  <Button variant="outline" className="border-orange-300 text-orange-700 hover:bg-orange-50"
                    onClick={() => handleUndo(selectedReturn)} data-testid="undo-status-btn">
                    <Undo2 className="w-4 h-4 mr-2" />Undo (Revert to {STATUS_LABELS[selectedReturn.previous_status]})
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}

      {/* ===== MANDATORY FIELDS MODAL ===== */}
      {pendingStatus && (
        <div className="fixed inset-0 bg-black/60 z-[60] flex items-center justify-center p-4" data-testid="mandatory-fields-modal">
          <Card className="w-full max-w-md">
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle className="font-[Manrope] text-base">
                  {STATUS_LABELS[pendingStatus.status]} - Required Info
                </CardTitle>
                <p className="text-xs text-muted-foreground mt-1">
                  <AlertTriangle className="w-3 h-3 inline mr-1" />
                  Mandatory fields must be filled
                </p>
              </div>
              <Button variant="ghost" size="sm" onClick={() => setPendingStatus(null)}><X className="w-4 h-4" /></Button>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleMandatorySubmit} className="space-y-4">
                {pendingStatus.status === 'pickup_scheduled' && (
                  <div>
                    <label className="text-xs font-medium text-muted-foreground">Pickup Date *</label>
                    <Input type="date" required value={statusFields.pickup_date}
                      onChange={e => setStatusFields({ ...statusFields, pickup_date: e.target.value })} data-testid="input-pickup-date" />
                  </div>
                )}
                {pendingStatus.status === 'in_transit' && (
                  <>
                    <div>
                      <label className="text-xs font-medium text-muted-foreground">Tracking Number *</label>
                      <Input required value={statusFields.tracking_number}
                        onChange={e => setStatusFields({ ...statusFields, tracking_number: e.target.value })}
                        placeholder="Enter tracking number" data-testid="input-return-tracking" />
                    </div>
                    <div>
                      <label className="text-xs font-medium text-muted-foreground">Courier Partner</label>
                      <Input value={statusFields.courier_partner}
                        onChange={e => setStatusFields({ ...statusFields, courier_partner: e.target.value })}
                        placeholder="Courier name" />
                    </div>
                  </>
                )}
                {pendingStatus.status === 'refunded' && (
                  <div>
                    <label className="text-xs font-medium text-muted-foreground">Refund Amount</label>
                    <Input type="number" step="0.01" value={statusFields.refund_amount}
                      onChange={e => setStatusFields({ ...statusFields, refund_amount: e.target.value })}
                      placeholder="0.00" />
                  </div>
                )}
                <div>
                  <label className="text-xs font-medium text-muted-foreground">Notes</label>
                  <Input value={statusFields.notes}
                    onChange={e => setStatusFields({ ...statusFields, notes: e.target.value })}
                    placeholder="Optional notes" />
                </div>
                <div className="flex gap-3">
                  <Button type="button" variant="outline" onClick={() => setPendingStatus(null)} className="flex-1">Cancel</Button>
                  <Button type="submit" className="flex-1" data-testid="submit-mandatory-btn">Confirm</Button>
                </div>
              </form>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
};

const TimelineDate = ({ label, date }) => {
  const d = date ? format(new Date(date), 'MMM dd, yyyy') : null;
  return (
    <div className={`p-2 rounded-lg border text-center ${d ? 'border-primary/20 bg-primary/5' : 'border-border/40 bg-muted/30 opacity-50'}`}>
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className="text-sm font-medium">{d || '-'}</p>
    </div>
  );
};
