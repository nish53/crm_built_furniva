import React, { useEffect, useState } from 'react';
import api from '../lib/api';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Badge } from '../components/ui/badge';
import { toast } from 'sonner';
import { RefreshCcw, Search, Package, CheckCircle, XCircle, Truck, Eye } from 'lucide-react';
import { format } from 'date-fns';

export const Returns = () => {
  const [returns, setReturns] = useState([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedReturn, setSelectedReturn] = useState(null);
  const [showDetailModal, setShowDetailModal] = useState(false);
  const [updatingStatus, setUpdatingStatus] = useState(false);

  useEffect(() => {
    fetchReturns();
  }, [statusFilter]);

  const fetchReturns = async () => {
    try {
      const params = {};
      if (statusFilter !== 'all') params.status = statusFilter;
      
      const response = await api.get('/returns/', { params });
      setReturns(response.data);
    } catch (error) {
      toast.error('Failed to fetch returns');
    } finally {
      setLoading(false);
    }
  };

  const handleStatusUpdate = async (returnId, newStatus, notes = '', refundAmount = null) => {
    setUpdatingStatus(true);
    try {
      const params = new URLSearchParams();
      params.append('status', newStatus);
      if (notes) params.append('notes', notes);
      if (refundAmount) params.append('refund_amount', refundAmount);

      await api.patch(`/returns/${returnId}/status?${params.toString()}`);
      toast.success('Return status updated');
      fetchReturns();
      setShowDetailModal(false);
    } catch (error) {
      toast.error('Failed to update status');
    } finally {
      setUpdatingStatus(false);
    }
  };

  const getStatusBadge = (status) => {
    const statusConfig = {
      requested: { color: 'bg-yellow-100 text-yellow-800', label: 'Requested' },
      approved: { color: 'bg-blue-100 text-blue-800', label: 'Approved' },
      rejected: { color: 'bg-red-100 text-red-800', label: 'Rejected' },
      pickup_scheduled: { color: 'bg-purple-100 text-purple-800', label: 'Pickup Scheduled' },
      in_transit: { color: 'bg-indigo-100 text-indigo-800', label: 'In Transit' },
      received: { color: 'bg-teal-100 text-teal-800', label: 'Received' },
      inspected: { color: 'bg-cyan-100 text-cyan-800', label: 'Inspected' },
      refunded: { color: 'bg-green-100 text-green-800', label: 'Refunded' },
      replaced: { color: 'bg-emerald-100 text-emerald-800', label: 'Replaced' }
    };

    const config = statusConfig[status] || { color: 'bg-gray-100 text-gray-800', label: status };
    return <Badge className={config.color}>{config.label}</Badge>;
  };

  const getReasonLabel = (reason) => {
    const labels = {
      defective: 'Defective Product',
      damaged: 'Damaged in Transit',
      wrong_item: 'Wrong Item Delivered',
      not_as_described: 'Not as Described',
      size_issue: 'Size Issue',
      quality_issue: 'Quality Issue',
      customer_changed_mind: 'Customer Changed Mind',
      delivery_delay: 'Delivery Delay',
      other: 'Other'
    };
    return labels[reason] || reason;
  };

  const filteredReturns = returns.filter(ret =>
    searchTerm === '' ||
    ret.order_number.toLowerCase().includes(searchTerm.toLowerCase()) ||
    ret.customer_name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold font-[Manrope] text-foreground">Returns Management</h1>
          <p className="text-muted-foreground mt-1">Track and manage product returns</p>
        </div>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground w-4 h-4" />
              <Input
                placeholder="Search by order number or customer..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-[200px]">
                <SelectValue placeholder="Filter by status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Returns</SelectItem>
                <SelectItem value="requested">Requested</SelectItem>
                <SelectItem value="approved">Approved</SelectItem>
                <SelectItem value="rejected">Rejected</SelectItem>
                <SelectItem value="pickup_scheduled">Pickup Scheduled</SelectItem>
                <SelectItem value="in_transit">In Transit</SelectItem>
                <SelectItem value="received">Received</SelectItem>
                <SelectItem value="inspected">Inspected</SelectItem>
                <SelectItem value="refunded">Refunded</SelectItem>
                <SelectItem value="replaced">Replaced</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Returns List */}
      {filteredReturns.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <RefreshCcw className="w-12 h-12 mx-auto mb-4 text-muted-foreground" />
            <p className="text-muted-foreground">No returns found</p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4">
          {filteredReturns.map(returnReq => (
            <Card key={returnReq.id} className="hover:border-primary/50 transition-colors">
              <CardContent className="p-6">
                <div className="flex justify-between items-start">
                  <div className="space-y-3 flex-1">
                    <div className="flex items-center gap-3">
                      <h3 className="text-lg font-bold font-[Manrope]">
                        Order #{returnReq.order_number}
                      </h3>
                      {getStatusBadge(returnReq.return_status)}
                      {returnReq.is_installation_related && (
                        <Badge className="bg-orange-100 text-orange-800">Installation Related</Badge>
                      )}
                    </div>

                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                      <div>
                        <p className="text-muted-foreground text-xs">Customer</p>
                        <p className="font-medium">{returnReq.customer_name}</p>
                        <p className="text-xs text-muted-foreground">{returnReq.phone}</p>
                      </div>
                      <div>
                        <p className="text-muted-foreground text-xs">Return Reason</p>
                        <p className="font-medium">{getReasonLabel(returnReq.return_reason)}</p>
                      </div>
                      <div>
                        <p className="text-muted-foreground text-xs">Requested Date</p>
                        <p className="font-medium">
                          {returnReq.requested_date ? format(new Date(returnReq.requested_date), 'MMM dd, yyyy') : 'N/A'}
                        </p>
                      </div>
                      {returnReq.damage_category && (
                        <div>
                          <p className="text-muted-foreground text-xs">Damage Type</p>
                          <p className="font-medium capitalize">{returnReq.damage_category.replace('_', ' ')}</p>
                        </div>
                      )}
                    </div>

                    {returnReq.return_reason_details && (
                      <div className="p-3 bg-muted rounded-lg">
                        <p className="text-xs text-muted-foreground mb-1">Details:</p>
                        <p className="text-sm">{returnReq.return_reason_details}</p>
                      </div>
                    )}
                  </div>

                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      setSelectedReturn(returnReq);
                      setShowDetailModal(true);
                    }}
                  >
                    <Eye className="w-4 h-4 mr-2" />
                    Manage
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Return Detail Modal */}
      {showDetailModal && selectedReturn && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <Card className="w-full max-w-3xl max-h-[90vh] overflow-y-auto">
            <CardHeader>
              <div className="flex justify-between items-center">
                <CardTitle className="font-[Manrope]">Return Details</CardTitle>
                <Button variant="ghost" size="sm" onClick={() => setShowDetailModal(false)}>×</Button>
              </div>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Current Status */}
              <div>
                <h3 className="text-sm font-semibold mb-3">Current Status</h3>
                <div className="flex items-center gap-4">
                  {getStatusBadge(selectedReturn.return_status)}
                  <p className="text-sm text-muted-foreground">
                    Requested on {format(new Date(selectedReturn.requested_date), 'MMM dd, yyyy')}
                  </p>
                </div>
              </div>

              {/* Order & Customer Info */}
              <div>
                <h3 className="text-sm font-semibold mb-3">Order Information</h3>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-muted-foreground">Order Number:</span>
                    <p className="font-medium">{selectedReturn.order_number}</p>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Customer:</span>
                    <p className="font-medium">{selectedReturn.customer_name}</p>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Phone:</span>
                    <p className="font-medium">{selectedReturn.phone}</p>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Return Reason:</span>
                    <p className="font-medium">{getReasonLabel(selectedReturn.return_reason)}</p>
                  </div>
                </div>
              </div>

              {/* Return Details */}
              {selectedReturn.return_reason_details && (
                <div>
                  <h3 className="text-sm font-semibold mb-2">Return Details</h3>
                  <p className="text-sm p-3 bg-muted rounded-lg">{selectedReturn.return_reason_details}</p>
                </div>
              )}

              {/* Tracking Info */}
              {selectedReturn.return_tracking_number && (
                <div>
                  <h3 className="text-sm font-semibold mb-2">Tracking Information</h3>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-muted-foreground">Tracking Number:</span>
                      <p className="font-medium">{selectedReturn.return_tracking_number}</p>
                    </div>
                    {selectedReturn.courier_partner && (
                      <div>
                        <span className="text-muted-foreground">Courier:</span>
                        <p className="font-medium">{selectedReturn.courier_partner}</p>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* QC Notes */}
              {selectedReturn.qc_notes && (
                <div>
                  <h3 className="text-sm font-semibold mb-2">QC Notes</h3>
                  <p className="text-sm p-3 bg-muted rounded-lg">{selectedReturn.qc_notes}</p>
                </div>
              )}

              {/* Update Status Actions */}
              <div>
                <h3 className="text-sm font-semibold mb-3">Update Status</h3>
                <div className="grid grid-cols-2 gap-2">
                  {selectedReturn.return_status === 'requested' && (
                    <>
                      <Button
                        onClick={() => handleStatusUpdate(selectedReturn.id, 'approved')}
                        disabled={updatingStatus}
                        className="w-full"
                      >
                        <CheckCircle className="w-4 h-4 mr-2" />
                        Approve Return
                      </Button>
                      <Button
                        variant="destructive"
                        onClick={() => handleStatusUpdate(selectedReturn.id, 'rejected')}
                        disabled={updatingStatus}
                        className="w-full"
                      >
                        <XCircle className="w-4 h-4 mr-2" />
                        Reject Return
                      </Button>
                    </>
                  )}
                  {selectedReturn.return_status === 'approved' && (
                    <Button
                      onClick={() => handleStatusUpdate(selectedReturn.id, 'pickup_scheduled')}
                      disabled={updatingStatus}
                      className="w-full"
                    >
                      <Package className="w-4 h-4 mr-2" />
                      Schedule Pickup
                    </Button>
                  )}
                  {selectedReturn.return_status === 'pickup_scheduled' && (
                    <Button
                      onClick={() => handleStatusUpdate(selectedReturn.id, 'in_transit')}
                      disabled={updatingStatus}
                      className="w-full"
                    >
                      <Truck className="w-4 h-4 mr-2" />
                      Mark In Transit
                    </Button>
                  )}
                  {selectedReturn.return_status === 'in_transit' && (
                    <Button
                      onClick={() => handleStatusUpdate(selectedReturn.id, 'received')}
                      disabled={updatingStatus}
                      className="w-full"
                    >
                      <Package className="w-4 h-4 mr-2" />
                      Mark Received
                    </Button>
                  )}
                  {selectedReturn.return_status === 'received' && (
                    <Button
                      onClick={() => handleStatusUpdate(selectedReturn.id, 'inspected')}
                      disabled={updatingStatus}
                      className="w-full"
                    >
                      <Eye className="w-4 h-4 mr-2" />
                      Mark Inspected
                    </Button>
                  )}
                  {selectedReturn.return_status === 'inspected' && (
                    <>
                      <Button
                        onClick={() => {
                          const amount = prompt('Enter refund amount:');
                          if (amount) handleStatusUpdate(selectedReturn.id, 'refunded', '', parseFloat(amount));
                        }}
                        disabled={updatingStatus}
                        className="w-full"
                      >
                        <CheckCircle className="w-4 h-4 mr-2" />
                        Process Refund
                      </Button>
                      <Button
                        variant="outline"
                        onClick={() => handleStatusUpdate(selectedReturn.id, 'replaced')}
                        disabled={updatingStatus}
                        className="w-full"
                      >
                        <RefreshCcw className="w-4 h-4 mr-2" />
                        Mark Replaced
                      </Button>
                    </>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
};
