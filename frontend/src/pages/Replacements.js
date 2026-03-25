import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Input } from '../components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import api from '../lib/api';
import { toast } from 'sonner';
import { Package, Clock, CheckCircle2, Truck, AlertTriangle, X, Trash2, Eye } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export const Replacements = () => {
  const [replacements, setReplacements] = useState([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('all');
  const [selectedReplacement, setSelectedReplacement] = useState(null);
  const [showStatusModal, setShowStatusModal] = useState(false);
  const [trackingNumber, setTrackingNumber] = useState('');
  const [resolutionNotes, setResolutionNotes] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    fetchReplacements();
  }, [statusFilter]);

  const fetchReplacements = async () => {
    try {
      const params = {};
      // ONLY fetch open replacements (exclude resolved status)
      params.exclude_status = 'resolved';
      
      if (statusFilter !== 'all') params.status = statusFilter;
      
      const response = await api.get('/replacement-requests/', { params });
      setReplacements(response.data || []);
    } catch (error) {
      toast.error('Failed to fetch replacements');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (replacementId) => {
    if (!window.confirm('Are you sure you want to delete this replacement request? This action cannot be undone.')) {
      return;
    }

    try {
      await api.delete(`/replacement-requests/${replacementId}`);
      toast.success('Replacement request deleted successfully');
      fetchReplacements();
    } catch (error) {
      toast.error('Failed to delete replacement request');
    }
  };

  const updateStatus = async (replacementId, newStatus) => {
    try {
      const params = { new_status: newStatus };
      if (trackingNumber) params.tracking_number = trackingNumber;
      if (resolutionNotes) params.resolution_notes = resolutionNotes;
      
      await api.patch(`/replacement-requests/${replacementId}/status`, null, { params });
      toast.success(`Status updated to: ${newStatus}`);
      setShowStatusModal(false);
      setTrackingNumber('');
      setResolutionNotes('');
      fetchReplacements();
    } catch (error) {
      toast.error('Failed to update status');
    }
  };

  const getStatusBadge = (status) => {
    const statusMap = {
      'Replacement Pending': { color: 'bg-orange-100 text-orange-800', icon: Clock },
      'Priority Review': { color: 'bg-red-100 text-red-800', icon: AlertTriangle },
      'Ship Replacement': { color: 'bg-blue-100 text-blue-800', icon: Package },
      'Tracking Added': { color: 'bg-blue-100 text-blue-800', icon: Truck },
      'Delivered': { color: 'bg-green-100 text-green-800', icon: CheckCircle2 },
      'Issue Resolved': { color: 'bg-green-100 text-green-800', icon: CheckCircle2 },
      'Issue Not Resolved': { color: 'bg-red-100 text-red-800', icon: X }
    };
    
    const config = statusMap[status] || { color: 'bg-gray-100 text-gray-800', icon: Package };
    const Icon = config.icon;
    
    return (
      <Badge className={config.color}>
        <Icon className="w-3 h-3 mr-1" />
        {status}
      </Badge>
    );
  };

  const getNextActions = (replacement) => {
    const status = replacement.replacement_status;
    
    if (status === 'Replacement Pending') {
      return [
        { label: 'Mark Priority', status: 'Priority Review', needsInput: false },
        { label: 'Ship Replacement', status: 'Ship Replacement', needsInput: false }
      ];
    }
    if (status === 'Priority Review') {
      return [{ label: 'Ship Replacement', status: 'Ship Replacement', needsInput: false }];
    }
    if (status === 'Ship Replacement') {
      return [{ label: 'Add Tracking', status: 'Tracking Added', needsInput: 'tracking' }];
    }
    if (status === 'Tracking Added') {
      return [{ label: 'Mark Delivered', status: 'Delivered', needsInput: false }];
    }
    if (status === 'Delivered') {
      return [
        { label: 'Issue Resolved', status: 'Issue Resolved', needsInput: 'resolution' },
        { label: 'Not Resolved', status: 'Issue Not Resolved', needsInput: 'resolution' }
      ];
    }
    
    return [];
  };

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold font-[Manrope]">Open Replacements</h1>
          <p className="text-muted-foreground mt-1">Manage in-progress replacement requests (resolved replacements moved to Resolved Orders)</p>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="cursor-pointer hover:bg-secondary/20" onClick={() => setStatusFilter('Replacement Pending')}>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Pending</p>
                <p className="text-2xl font-bold">{replacements.filter(r => r.replacement_status === 'Replacement Pending').length}</p>
              </div>
              <Clock className="w-8 h-8 text-orange-500" />
            </div>
          </CardContent>
        </Card>

        <Card className="cursor-pointer hover:bg-secondary/20" onClick={() => setStatusFilter('Priority Review')}>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Priority</p>
                <p className="text-2xl font-bold">{replacements.filter(r => r.replacement_status === 'Priority Review').length}</p>
              </div>
              <AlertTriangle className="w-8 h-8 text-red-500" />
            </div>
          </CardContent>
        </Card>

        <Card className="cursor-pointer hover:bg-secondary/20" onClick={() => setStatusFilter('Ship Replacement')}>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">To Ship</p>
                <p className="text-2xl font-bold">{replacements.filter(r => r.replacement_status === 'Ship Replacement').length}</p>
              </div>
              <Package className="w-8 h-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>

        <Card className="cursor-pointer hover:bg-secondary/20" onClick={() => setStatusFilter('Delivered')}>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Delivered</p>
                <p className="text-2xl font-bold">{replacements.filter(r => r.replacement_status === 'Delivered').length}</p>
              </div>
              <CheckCircle2 className="w-8 h-8 text-green-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Status Filter */}
      <div className="flex items-center gap-4">
        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-[200px]">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Statuses</SelectItem>
            <SelectItem value="Replacement Pending">Pending</SelectItem>
            <SelectItem value="Priority Review">Priority Review</SelectItem>
            <SelectItem value="Ship Replacement">To Ship</SelectItem>
            <SelectItem value="Tracking Added">In Transit</SelectItem>
            <SelectItem value="Delivered">Delivered</SelectItem>
            <SelectItem value="Issue Resolved">Resolved</SelectItem>
          </SelectContent>
        </Select>
        <Button variant="outline" onClick={() => { setStatusFilter('all'); fetchReplacements(); }}>
          Clear Filter
        </Button>
      </div>

      {/* Replacements List */}
      <Card>
        <CardHeader>
          <CardTitle className="font-[Manrope]">Replacement Requests</CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="text-center py-12">
              <p className="text-muted-foreground">Loading replacements...</p>
            </div>
          ) : replacements.length === 0 ? (
            <div className="text-center py-12">
              <Package className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
              <p className="text-muted-foreground">No replacement requests found</p>
            </div>
          ) : (
            <div className="space-y-4">
              {replacements.map((replacement) => (
                <div key={replacement.id} className="border rounded-lg p-4 hover:bg-secondary/20 cursor-pointer"
                  onClick={() => navigate(`/replacements/${replacement.id}`)}>
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <span className="font-[JetBrains_Mono] font-medium">{replacement.order_number}</span>
                        {getStatusBadge(replacement.replacement_status)}
                        <Badge variant="outline">{replacement.replacement_reason}</Badge>
                      </div>
                      
                      <div className="grid grid-cols-2 gap-4 text-sm mb-3">
                        <div>
                          <p className="text-muted-foreground">Customer</p>
                          <p className="font-medium">{replacement.customer_name}</p>
                          <p className="text-xs text-muted-foreground">{replacement.phone}</p>
                        </div>
                        <div>
                          <p className="text-muted-foreground">Requested</p>
                          <p>{new Date(replacement.requested_date).toLocaleDateString()}</p>
                        </div>
                      </div>
                      
                      <div className="bg-secondary/30 p-3 rounded-md mb-3">
                        <p className="text-xs font-medium text-muted-foreground mb-1">Damage Description:</p>
                        <p className="text-sm">{replacement.damage_description}</p>
                      </div>
                      
                      {replacement.tracking_number && (
                        <div className="flex items-center gap-2 text-sm">
                          <Truck className="w-4 h-4" />
                          <span>Tracking: {replacement.tracking_number}</span>
                        </div>
                      )}
                      
                      {replacement.damage_images && replacement.damage_images.length > 0 && (
                        <div className="mt-3">
                          <p className="text-xs font-medium text-muted-foreground mb-2">Damage Images:</p>
                          <div className="flex flex-wrap gap-2">
                            {replacement.damage_images.map((img, idx) => (
                              <div key={idx} className="relative group">
                                <Badge variant="outline" className="text-xs cursor-pointer hover:bg-secondary">
                                  📷 Image {idx + 1}: {img}
                                </Badge>
                                <span className="text-xs text-muted-foreground block mt-1">
                                  (Click to view - images stored as: {img})
                                </span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                    
                    <div className="flex flex-col gap-2 ml-4">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => navigate(`/replacements/${replacement.id}`)}
                        className="flex items-center gap-2"
                      >
                        <Eye className="w-4 h-4" />
                        View Details
                      </Button>
                      
                      {getNextActions(replacement).map((action, idx) => (
                        <Button
                          key={idx}
                          size="sm"
                          onClick={() => {
                            setSelectedReplacement(replacement);
                            if (action.needsInput) {
                              setShowStatusModal(true);
                            } else {
                              updateStatus(replacement.id, action.status);
                            }
                          }}
                        >
                          {action.label}
                        </Button>
                      ))}
                      
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleDelete(replacement.id)}
                        className="text-red-600 hover:text-red-700 hover:bg-red-50 flex items-center gap-2"
                      >
                        <Trash2 className="w-4 h-4" />
                        Delete
                      </Button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Status Update Modal */}
      {showStatusModal && selectedReplacement && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <Card className="w-full max-w-md">
            <CardHeader>
              <CardTitle>Update Replacement Status</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {selectedReplacement.replacement_status === 'Ship Replacement' && (
                <div>
                  <label className="text-sm font-medium">Tracking Number *</label>
                  <Input
                    value={trackingNumber}
                    onChange={(e) => setTrackingNumber(e.target.value)}
                    placeholder="Enter tracking number"
                  />
                </div>
              )}
              
              {selectedReplacement.replacement_status === 'Delivered' && (
                <div>
                  <label className="text-sm font-medium">Resolution Notes</label>
                  <textarea
                    value={resolutionNotes}
                    onChange={(e) => setResolutionNotes(e.target.value)}
                    placeholder="Was the issue resolved? Any notes..."
                    className="w-full p-2 border rounded-md min-h-[100px]"
                  />
                </div>
              )}
              
              <div className="flex gap-3">
                <Button variant="outline" onClick={() => setShowStatusModal(false)} className="flex-1">
                  Cancel
                </Button>
                <Button
                  onClick={() => updateStatus(selectedReplacement.id, 'Tracking Added')}
                  className="flex-1"
                  disabled={selectedReplacement.replacement_status === 'Ship Replacement' && !trackingNumber}
                >
                  Update
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
};
