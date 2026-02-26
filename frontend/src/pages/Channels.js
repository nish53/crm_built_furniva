import React, { useEffect, useState } from 'react';
import api from '../lib/api';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { toast } from 'sonner';
import { Plus, Edit, Trash2, Package, DollarSign, CheckCircle, XCircle } from 'lucide-react';

export const Channels = () => {
  const [channels, setChannels] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    display_name: '',
    is_active: true,
    commission_rate: 0,
    supports_tracking: true,
    required_fields: [],
    optional_fields: []
  });

  useEffect(() => {
    fetchChannels();
  }, []);

  const fetchChannels = async () => {
    try {
      const response = await api.get('/channels/');
      setChannels(response.data);
    } catch (error) {
      toast.error('Failed to fetch channels');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    try {
      if (editingId) {
        await api.put(`/channels/${editingId}`, formData);
        toast.success('Channel updated successfully');
      } else {
        await api.post('/channels/', formData);
        toast.success('Channel created successfully');
      }
      
      resetForm();
      fetchChannels();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to save channel');
    }
  };

  const handleEdit = (channel) => {
    setFormData({
      name: channel.name,
      display_name: channel.display_name,
      is_active: channel.is_active,
      commission_rate: channel.commission_rate || 0,
      supports_tracking: channel.supports_tracking,
      required_fields: channel.required_fields || [],
      optional_fields: channel.optional_fields || []
    });
    setEditingId(channel.name);
    setShowForm(true);
  };

  const handleDelete = async (channelName) => {
    if (!confirm(`Are you sure you want to delete the ${channelName} channel?`)) return;
    
    try {
      await api.delete(`/channels/${channelName}`);
      toast.success('Channel deleted successfully');
      fetchChannels();
    } catch (error) {
      toast.error('Failed to delete channel');
    }
  };

  const resetForm = () => {
    setFormData({
      name: '',
      display_name: '',
      is_active: true,
      commission_rate: 0,
      supports_tracking: true,
      required_fields: [],
      optional_fields: []
    });
    setEditingId(null);
    setShowForm(false);
  };

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
          <h1 className="text-3xl font-bold font-[Manrope] text-foreground">Channel Management</h1>
          <p className="text-muted-foreground mt-1">Manage sales channels and marketplaces</p>
        </div>
        <Button onClick={() => setShowForm(true)}>
          <Plus className="w-4 h-4 mr-2" />
          Add Channel
        </Button>
      </div>

      {/* Form Modal */}
      {showForm && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <Card className="w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <CardHeader>
              <div className="flex justify-between items-center">
                <CardTitle className="font-[Manrope]">
                  {editingId ? 'Edit Channel' : 'Create New Channel'}
                </CardTitle>
                <Button variant="ghost" size="sm" onClick={resetForm}>×</Button>
              </div>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium mb-1">Channel ID *</label>
                    <Input
                      required
                      value={formData.name}
                      onChange={(e) => setFormData({...formData, name: e.target.value.toLowerCase().replace(/\s+/g, '_')})}
                      placeholder="e.g., instagram"
                      disabled={editingId}
                    />
                    <p className="text-xs text-muted-foreground mt-1">Lowercase, no spaces (auto-formatted)</p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Display Name *</label>
                    <Input
                      required
                      value={formData.display_name}
                      onChange={(e) => setFormData({...formData, display_name: e.target.value})}
                      placeholder="e.g., Instagram"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium mb-1">Commission Rate (%)</label>
                    <Input
                      type="number"
                      step="0.01"
                      value={formData.commission_rate}
                      onChange={(e) => setFormData({...formData, commission_rate: parseFloat(e.target.value) || 0})}
                      placeholder="0.00"
                    />
                  </div>
                  <div className="flex items-center space-x-6 pt-6">
                    <label className="flex items-center space-x-2">
                      <input
                        type="checkbox"
                        checked={formData.is_active}
                        onChange={(e) => setFormData({...formData, is_active: e.target.checked})}
                        className="rounded border-border"
                      />
                      <span className="text-sm font-medium">Active</span>
                    </label>
                    <label className="flex items-center space-x-2">
                      <input
                        type="checkbox"
                        checked={formData.supports_tracking}
                        onChange={(e) => setFormData({...formData, supports_tracking: e.target.checked})}
                        className="rounded border-border"
                      />
                      <span className="text-sm font-medium">Tracking</span>
                    </label>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-1">Required Fields (comma-separated)</label>
                  <Input
                    value={formData.required_fields.join(', ')}
                    onChange={(e) => setFormData({...formData, required_fields: e.target.value.split(',').map(f => f.trim()).filter(Boolean)})}
                    placeholder="e.g., order_number, sku"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-1">Optional Fields (comma-separated)</label>
                  <Input
                    value={formData.optional_fields.join(', ')}
                    onChange={(e) => setFormData({...formData, optional_fields: e.target.value.split(',').map(f => f.trim()).filter(Boolean)})}
                    placeholder="e.g., tracking_number, notes"
                  />
                </div>

                <div className="flex space-x-4">
                  <Button type="button" variant="outline" onClick={resetForm} className="flex-1">
                    Cancel
                  </Button>
                  <Button type="submit" className="flex-1">
                    {editingId ? 'Update' : 'Create'} Channel
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Channels List */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {channels.length === 0 ? (
          <Card className="col-span-full">
            <CardContent className="py-12 text-center">
              <Package className="w-12 h-12 mx-auto mb-4 text-muted-foreground" />
              <p className="text-muted-foreground">No channels configured yet</p>
              <Button onClick={() => setShowForm(true)} className="mt-4">
                <Plus className="w-4 h-4 mr-2" />
                Create First Channel
              </Button>
            </CardContent>
          </Card>
        ) : (
          channels.map(channel => (
            <Card key={channel.id} className="hover:border-primary/50 transition-colors">
              <CardContent className="p-6">
                <div className="space-y-4">
                  <div className="flex justify-between items-start">
                    <div>
                      <div className="flex items-center gap-2 mb-2">
                        <h3 className="text-lg font-bold font-[Manrope]">{channel.display_name}</h3>
                        {channel.is_active ? (
                          <Badge className="bg-green-100 text-green-800">
                            <CheckCircle className="w-3 h-3 mr-1" />
                            Active
                          </Badge>
                        ) : (
                          <Badge className="bg-gray-100 text-gray-800">
                            <XCircle className="w-3 h-3 mr-1" />
                            Inactive
                          </Badge>
                        )}
                      </div>
                      <p className="text-xs text-muted-foreground">ID: {channel.name}</p>
                    </div>
                    <div className="flex space-x-1">
                      <Button variant="ghost" size="sm" onClick={() => handleEdit(channel)}>
                        <Edit className="w-4 h-4" />
                      </Button>
                      <Button variant="ghost" size="sm" onClick={() => handleDelete(channel.name)}>
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>

                  <div className="space-y-2 text-sm">
                    <div className="flex items-center justify-between">
                      <span className="text-muted-foreground">Commission:</span>
                      <span className="font-medium flex items-center">
                        <DollarSign className="w-3 h-3" />
                        {channel.commission_rate}%
                      </span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-muted-foreground">Tracking:</span>
                      <span className="font-medium">
                        {channel.supports_tracking ? 'Supported' : 'Not Supported'}
                      </span>
                    </div>
                  </div>

                  {channel.required_fields && channel.required_fields.length > 0 && (
                    <div>
                      <p className="text-xs font-medium text-muted-foreground mb-1">Required Fields:</p>
                      <div className="flex flex-wrap gap-1">
                        {channel.required_fields.map(field => (
                          <Badge key={field} variant="outline" className="text-xs">
                            {field}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}

                  {channel.optional_fields && channel.optional_fields.length > 0 && (
                    <div>
                      <p className="text-xs font-medium text-muted-foreground mb-1">Optional Fields:</p>
                      <div className="flex flex-wrap gap-1">
                        {channel.optional_fields.slice(0, 3).map(field => (
                          <Badge key={field} variant="outline" className="text-xs bg-muted">
                            {field}
                          </Badge>
                        ))}
                        {channel.optional_fields.length > 3 && (
                          <Badge variant="outline" className="text-xs bg-muted">
                            +{channel.optional_fields.length - 3} more
                          </Badge>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          ))
        )}
      </div>
    </div>
  );
};
