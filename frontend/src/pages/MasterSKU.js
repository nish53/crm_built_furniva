import React, { useEffect, useState } from 'react';
import api from '../lib/api';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { toast } from 'sonner';
import { Plus, Search, Edit, Trash2, Package } from 'lucide-react';

export const MasterSKU = () => {
  const [skuMappings, setSkuMappings] = useState([]);
  const [unmappedSkus, setUnmappedSkus] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [showAllUnmapped, setShowAllUnmapped] = useState(false);
  const [formData, setFormData] = useState({
    master_sku: '',
    product_name: '',
    description: '',
    category: '',
    amazon_sku: '',
    amazon_asin: '',
    flipkart_sku: '',
    flipkart_fsn: '',
    website_sku: '',
    dimensions: '',
    weight: '',
    cost_price: '',
    selling_price: ''
  });

  useEffect(() => {
    fetchMappings();
    fetchUnmappedSKUs();
  }, [searchTerm]);

  const fetchMappings = async () => {
    try {
      const params = searchTerm ? { search: searchTerm } : {};
      const response = await api.get('/master-sku/', { params });
      setSkuMappings(response.data);
    } catch (error) {
      toast.error('Failed to fetch SKU mappings');
    } finally {
      setLoading(false);
    }
  };

  const fetchUnmappedSKUs = async () => {
    try {
      const response = await api.get('/dashboard/priority/unmapped-skus');
      setUnmappedSkus(response.data.unmapped_skus || []);
    } catch (error) {
      console.error('Failed to fetch unmapped SKUs:', error);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    try {
      if (editingId) {
        await api.put(`/master-sku/${editingId}`, formData);
        toast.success('Master SKU updated successfully');
      } else {
        await api.post('/master-sku/', formData);
        toast.success('Master SKU created successfully');
      }
      
      resetForm();
      fetchMappings();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to save Master SKU');
    }
  };

  const handleEdit = (mapping) => {
    setFormData(mapping);
    setEditingId(mapping.master_sku);
    setShowForm(true);
  };

  const handleDelete = async (masterSku) => {
    if (!confirm('Are you sure you want to delete this Master SKU mapping?')) return;
    
    try {
      await api.delete(`/master-sku/${masterSku}`);
      toast.success('Master SKU deleted successfully');
      fetchMappings();
    } catch (error) {
      toast.error('Failed to delete Master SKU');
    }
  };

  const resetForm = () => {
    setFormData({
      master_sku: '',
      product_name: '',
      description: '',
      category: '',
      amazon_sku: '',
      amazon_asin: '',
      flipkart_sku: '',
      flipkart_fsn: '',
      website_sku: '',
      dimensions: '',
      weight: '',
      cost_price: '',
      selling_price: ''
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
          <h1 className="text-3xl font-bold font-[Manrope] text-foreground">Master SKU Management</h1>
          <p className="text-muted-foreground mt-1">Unified product SKU mapping across all platforms</p>
        </div>
        <Button onClick={() => setShowForm(true)}>
          <Plus className="w-4 h-4 mr-2" />
          Add Master SKU
        </Button>
      </div>

      {/* Unmapped SKUs Alert */}
      {unmappedSkus.length > 0 && (
        <Card className="border-yellow-500/50 bg-yellow-50/50 dark:bg-yellow-950/20">
          <CardHeader>
            <CardTitle className="font-[Manrope] flex items-center gap-2">
              <Package className="w-5 h-5 text-yellow-600" />
              {unmappedSkus.length} SKU(s) Need Mapping
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
              {(showAllUnmapped ? unmappedSkus : unmappedSkus.slice(0, 6)).map((item, idx) => (
                <div key={idx} className="flex items-center justify-between p-3 bg-white dark:bg-gray-800 rounded-lg border">
                  <div>
                    <p className="font-medium text-sm">{item.sku}</p>
                    <p className="text-xs text-muted-foreground">{item.channel} • {item.order_count} orders</p>
                  </div>
                  <Button
                    size="sm"
                    onClick={() => {
                      setFormData(prev => ({ ...prev, amazon_sku: item.sku, product_name: item.product_name }));
                      setShowForm(true);
                      setEditingId(null);
                    }}
                  >
                    Map Now
                  </Button>
                </div>
              ))}
            </div>
            {unmappedSkus.length > 6 && (
              <Button 
                variant="link" 
                className="mt-3" 
                onClick={() => setShowAllUnmapped(!showAllUnmapped)}
              >
                {showAllUnmapped ? 'Show Less' : `Show All ${unmappedSkus.length} SKUs`}
              </Button>
            )}
          </CardContent>
        </Card>
      )}

      {/* Search */}
      <div className="flex gap-4">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground w-4 h-4" />
          <Input
            placeholder="Search by Master SKU, Product Name, ASIN, FSN, etc..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10"
          />
        </div>
      </div>

      {/* Form Modal */}
      {showForm && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <Card className="w-full max-w-4xl max-h-[90vh] overflow-y-auto">
            <CardHeader>
              <CardTitle className="font-[Manrope]">
                {editingId ? 'Edit Master SKU' : 'Create Master SKU'}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSubmit} className="space-y-6">
                {/* Basic Info */}
                <div className="space-y-4">
                  <h3 className="text-sm font-semibold text-foreground">Basic Information</h3>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium mb-1">Master SKU *</label>
                      <Input
                        required
                        value={formData.master_sku}
                        onChange={(e) => setFormData({...formData, master_sku: e.target.value})}
                        placeholder="e.g., FURN-001"
                        disabled={editingId}
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-1">Product Name *</label>
                      <Input
                        required
                        value={formData.product_name}
                        onChange={(e) => setFormData({...formData, product_name: e.target.value})}
                        placeholder="Product name"
                      />
                    </div>
                    <div className="col-span-2">
                      <label className="block text-sm font-medium mb-1">Description</label>
                      <Input
                        value={formData.description}
                        onChange={(e) => setFormData({...formData, description: e.target.value})}
                        placeholder="Product description"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-1">Category</label>
                      <Input
                        value={formData.category}
                        onChange={(e) => setFormData({...formData, category: e.target.value})}
                        placeholder="e.g., Furniture, Decor"
                      />
                    </div>
                  </div>
                </div>

                {/* Amazon SKUs */}
                <div className="space-y-4">
                  <h3 className="text-sm font-semibold text-foreground">Amazon</h3>
                  <div className="grid grid-cols-3 gap-4">
                    <div>
                      <label className="block text-sm font-medium mb-1">Amazon SKU</label>
                      <Input
                        value={formData.amazon_sku}
                        onChange={(e) => setFormData({...formData, amazon_sku: e.target.value})}
                        placeholder="Seller SKU"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-1">ASIN</label>
                      <Input
                        value={formData.amazon_asin}
                        onChange={(e) => setFormData({...formData, amazon_asin: e.target.value})}
                        placeholder="B0XXXXXXXX"
                      />
                    </div>
                  </div>
                </div>

                {/* Flipkart SKUs */}
                <div className="space-y-4">
                  <h3 className="text-sm font-semibold text-foreground">Flipkart</h3>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium mb-1">Flipkart SKU</label>
                      <Input
                        value={formData.flipkart_sku}
                        onChange={(e) => setFormData({...formData, flipkart_sku: e.target.value})}
                        placeholder="Seller SKU"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-1">FSN ID</label>
                      <Input
                        value={formData.flipkart_fsn}
                        onChange={(e) => setFormData({...formData, flipkart_fsn: e.target.value})}
                        placeholder="FSN identifier"
                      />
                    </div>
                  </div>
                </div>

                {/* Website SKU */}
                <div className="space-y-4">
                  <h3 className="text-sm font-semibold text-foreground">Website</h3>
                  <div>
                    <label className="block text-sm font-medium mb-1">Website SKU</label>
                    <Input
                      value={formData.website_sku}
                      onChange={(e) => setFormData({...formData, website_sku: e.target.value})}
                      placeholder="Website SKU"
                    />
                  </div>
                </div>

                <div className="flex space-x-4">
                  <Button type="button" variant="outline" onClick={resetForm} className="flex-1">
                    Cancel
                  </Button>
                  <Button type="submit" className="flex-1">
                    {editingId ? 'Update' : 'Create'} Master SKU
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>
        </div>
      )}

      {/* SKU List */}
      <div className="grid gap-4">
        {skuMappings.length === 0 ? (
          <Card>
            <CardContent className="py-12 text-center">
              <Package className="w-12 h-12 mx-auto mb-4 text-muted-foreground" />
              <p className="text-muted-foreground">No Master SKU mappings yet</p>
              <Button onClick={() => setShowForm(true)} className="mt-4">
                <Plus className="w-4 h-4 mr-2" />
                Create First Master SKU
              </Button>
            </CardContent>
          </Card>
        ) : (
          skuMappings.map(mapping => (
            <Card key={mapping.id}>
              <CardContent className="p-6">
                <div className="flex justify-between items-start">
                  <div className="space-y-3 flex-1">
                    <div>
                      <div className="flex items-center gap-2">
                        <h3 className="text-lg font-bold font-[Manrope]">{mapping.master_sku}</h3>
                        {mapping.category && (
                          <span className="px-2 py-0.5 bg-primary/10 text-primary text-xs rounded-full">
                            {mapping.category}
                          </span>
                        )}
                      </div>
                      <p className="text-sm text-foreground mt-1">{mapping.product_name}</p>
                      {mapping.description && (
                        <p className="text-xs text-muted-foreground mt-1">{mapping.description}</p>
                      )}
                    </div>

                    <div className="grid grid-cols-3 gap-4 text-sm">
                      {/* Amazon */}
                      {(mapping.amazon_sku || mapping.amazon_asin) && (
                        <div>
                          <p className="text-xs font-medium text-muted-foreground mb-1">Amazon</p>
                          {mapping.amazon_sku && <p>SKU: {mapping.amazon_sku}</p>}
                          {mapping.amazon_asin && <p>ASIN: {mapping.amazon_asin}</p>}
                        </div>
                      )}

                      {/* Flipkart */}
                      {(mapping.flipkart_sku || mapping.flipkart_fsn) && (
                        <div>
                          <p className="text-xs font-medium text-muted-foreground mb-1">Flipkart</p>
                          {mapping.flipkart_sku && <p>SKU: {mapping.flipkart_sku}</p>}
                          {mapping.flipkart_fsn && <p>FSN: {mapping.flipkart_fsn}</p>}
                        </div>
                      )}

                      {/* Website */}
                      {mapping.website_sku && (
                        <div>
                          <p className="text-xs font-medium text-muted-foreground mb-1">Website</p>
                          <p>SKU: {mapping.website_sku}</p>
                        </div>
                      )}

                      {/* Details */}
                      <div>
                        <p className="text-xs font-medium text-muted-foreground mb-1">Details</p>
                        {mapping.dimensions && <p>Size: {mapping.dimensions}</p>}
                        {mapping.weight && <p>Weight: {mapping.weight} kg</p>}
                      </div>

                      {/* Pricing */}
                      {(mapping.cost_price || mapping.selling_price) && (
                        <div>
                          <p className="text-xs font-medium text-muted-foreground mb-1">Pricing</p>
                          {mapping.cost_price && <p>Cost: ₹{mapping.cost_price}</p>}
                          {mapping.selling_price && <p>Selling: ₹{mapping.selling_price}</p>}
                        </div>
                      )}
                    </div>
                  </div>

                  <div className="flex space-x-2">
                    <Button variant="outline" size="sm" onClick={() => handleEdit(mapping)}>
                      <Edit className="w-4 h-4" />
                    </Button>
                    <Button variant="outline" size="sm" onClick={() => handleDelete(mapping.master_sku)}>
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))
        )}
      </div>
    </div>
  );
};
