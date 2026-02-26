import React, { useEffect, useState } from 'react';
import api from '../lib/api';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Badge } from '../components/ui/badge';
import { toast } from 'sonner';
import { Plus, Search, Edit, Trash2, Package, List, ShoppingCart, X } from 'lucide-react';
import { format } from 'date-fns';

export const InventoryNew = () => {
  const [masterSKUs, setMasterSKUs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [showMasterSKUForm, setShowMasterSKUForm] = useState(false);
  const [showListingsModal, setShowListingsModal] = useState(false);
  const [showProcurementModal, setShowProcurementModal] = useState(false);
  const [selectedMasterSKU, setSelectedMasterSKU] = useState(null);
  const [listings, setListings] = useState([]);
  const [batches, setBatches] = useState([]);
  const [averageCost, setAverageCost] = useState(null);
  const [editingListing, setEditingListing] = useState(null);

  const [masterSKUForm, setMasterSKUForm] = useState({
    master_sku: '',
    product_name: '',
    description: '',
    category: ''
  });

  const [listingForm, setListingForm] = useState({
    platform: 'amazon',
    listings: [{ platform_sku: '', platform_product_id: '' }]
  });

  const [procurementForm, setProcurementForm] = useState({
    batch_number: '',
    procurement_date: new Date().toISOString().split('T')[0],
    quantity: '',
    unit_cost: '',
    supplier: '',
    weight: '',
    num_boxes: '1',
    box_dimensions: [{ length: '', width: '', height: '' }],
    reorder_level: ''
  });

  useEffect(() => {
    fetchMasterSKUs();
  }, [searchTerm]);

  const fetchMasterSKUs = async () => {
    try {
      const params = searchTerm ? { search: searchTerm } : {};
      const response = await api.get('/master-sku/', { params });
      setMasterSKUs(response.data);
    } catch (error) {
      toast.error('Failed to fetch Master SKUs');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateMasterSKU = async (e) => {
    e.preventDefault();
    try {
      await api.post('/master-sku/', masterSKUForm);
      toast.success('Master SKU created successfully');
      setShowMasterSKUForm(false);
      resetMasterSKUForm();
      fetchMasterSKUs();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create Master SKU');
    }
  };

  const handleDeleteMasterSKU = async (masterSku) => {
    if (!confirm(`Delete Master SKU ${masterSku}?`)) return;
    try {
      await api.delete(`/master-sku/${masterSku}`);
      toast.success('Master SKU deleted');
      fetchMasterSKUs();
    } catch (error) {
      toast.error('Failed to delete');
    }
  };

  const openListingsModal = async (masterSku) => {
    setSelectedMasterSKU(masterSku);
    try {
      const response = await api.get(`/platform-listings/by-master-sku/${masterSku}`);
      setListings(response.data);
      setShowListingsModal(true);
    } catch (error) {
      toast.error('Failed to fetch listings');
    }
  };

  const handleCreateListings = async (e) => {
    e.preventDefault();
    try {
      const promises = listingForm.listings
        .filter(l => l.platform_sku && l.platform_product_id)
        .map(listing => 
          api.post('/platform-listings/', {
            master_sku: selectedMasterSKU,
            platform: listingForm.platform,
            platform_sku: listing.platform_sku,
            platform_product_id: listing.platform_product_id,
            is_active: true
          })
        );
      
      await Promise.all(promises);
      toast.success(`${promises.length} listing(s) added successfully`);
      resetListingForm();
      openListingsModal(selectedMasterSKU);
    } catch (error) {
      toast.error('Failed to create listings');
    }
  };

  const handleDeleteListing = async (listingId) => {
    if (!confirm('Delete this listing?')) return;
    try {
      await api.delete(`/platform-listings/${listingId}`);
      toast.success('Listing deleted');
      openListingsModal(selectedMasterSKU);
    } catch (error) {
      toast.error('Failed to delete listing');
    }
  };

  const addListingPair = () => {
    setListingForm({
      ...listingForm,
      listings: [...listingForm.listings, { platform_sku: '', platform_product_id: '' }]
    });
  };

  const removeListingPair = (index) => {
    const newListings = listingForm.listings.filter((_, i) => i !== index);
    setListingForm({ ...listingForm, listings: newListings });
  };

  const updateListingPair = (index, field, value) => {
    const newListings = [...listingForm.listings];
    newListings[index][field] = value;
    setListingForm({ ...listingForm, listings: newListings });
  };

  const openProcurementModal = async (masterSku) => {
    setSelectedMasterSKU(masterSku);
    try {
      const [batchesRes, costRes] = await Promise.all([
        api.get(`/procurement-batches/by-master-sku/${masterSku}`),
        api.get(`/procurement-batches/average-cost/${masterSku}?method=weighted`)
      ]);
      setBatches(batchesRes.data);
      setAverageCost(costRes.data);
      setShowProcurementModal(true);
    } catch (error) {
      toast.error('Failed to fetch procurement data');
    }
  };

  const handleCreateProcurement = async (e) => {
    e.preventDefault();
    try {
      await api.post('/procurement-batches/', {
        master_sku: selectedMasterSKU,
        batch_number: procurementForm.batch_number,
        procurement_date: new Date(procurementForm.procurement_date).toISOString(),
        quantity: parseInt(procurementForm.quantity),
        unit_cost: parseFloat(procurementForm.unit_cost),
        supplier: procurementForm.supplier,
        notes: JSON.stringify({
          weight: procurementForm.weight,
          num_boxes: procurementForm.num_boxes,
          box_dimensions: procurementForm.box_dimensions,
          reorder_level: procurementForm.reorder_level
        })
      });
      toast.success('Procurement/Inventory added');
      resetProcurementForm();
      openProcurementModal(selectedMasterSKU);
    } catch (error) {
      toast.error('Failed to create procurement');
    }
  };

  const handleDeleteBatch = async (batchId) => {
    if (!confirm('Delete this procurement batch?')) return;
    try {
      await api.delete(`/procurement-batches/${batchId}`);
      toast.success('Batch deleted');
      openProcurementModal(selectedMasterSKU);
    } catch (error) {
      toast.error('Failed to delete');
    }
  };

  const addBoxDimension = () => {
    setProcurementForm({
      ...procurementForm,
      box_dimensions: [...procurementForm.box_dimensions, { length: '', width: '', height: '' }]
    });
  };

  const removeBoxDimension = (index) => {
    const newDims = procurementForm.box_dimensions.filter((_, i) => i !== index);
    setProcurementForm({ ...procurementForm, box_dimensions: newDims });
  };

  const updateBoxDimension = (index, field, value) => {
    const newDims = [...procurementForm.box_dimensions];
    newDims[index][field] = value;
    setProcurementForm({ ...procurementForm, box_dimensions: newDims });
  };

  const resetMasterSKUForm = () => {
    setMasterSKUForm({
      master_sku: '',
      product_name: '',
      description: '',
      category: ''
    });
  };

  const resetListingForm = () => {
    setListingForm({
      platform: 'amazon',
      listings: [{ platform_sku: '', platform_product_id: '' }]
    });
  };

  const resetProcurementForm = () => {
    setProcurementForm({
      batch_number: '',
      procurement_date: new Date().toISOString().split('T')[0],
      quantity: '',
      unit_cost: '',
      supplier: '',
      weight: '',
      num_boxes: '1',
      box_dimensions: [{ length: '', width: '', height: '' }],
      reorder_level: ''
    });
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
          <h1 className="text-3xl font-bold font-[Manrope] text-foreground">Inventory & Master SKU</h1>
          <p className="text-muted-foreground mt-1">Manage Master SKUs, Platform Listings & Stock</p>
        </div>
        <Button onClick={() => setShowMasterSKUForm(true)}>
          <Plus className="w-4 h-4 mr-2" />
          Add Master SKU
        </Button>
      </div>

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground w-4 h-4" />
        <Input
          placeholder="Search Master SKU or Product..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="pl-10"
        />
      </div>

      {/* Master SKU Form Modal */}
      {showMasterSKUForm && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <Card className="w-full max-w-2xl">
            <CardHeader>
              <div className="flex justify-between items-center">
                <CardTitle className="font-[Manrope]">Create Master SKU</CardTitle>
                <Button variant="ghost" size="sm" onClick={() => setShowMasterSKUForm(false)}>×</Button>
              </div>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleCreateMasterSKU} className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium mb-1">Master SKU *</label>
                    <Input
                      required
                      value={masterSKUForm.master_sku}
                      onChange={(e) => setMasterSKUForm({...masterSKUForm, master_sku: e.target.value})}
                      placeholder="e.g., CHAIR-PREM-001"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Product Name *</label>
                    <Input
                      required
                      value={masterSKUForm.product_name}
                      onChange={(e) => setMasterSKUForm({...masterSKUForm, product_name: e.target.value})}
                      placeholder="Premium Office Chair"
                    />
                  </div>
                  <div className="col-span-2">
                    <label className="block text-sm font-medium mb-1">Description</label>
                    <Input
                      value={masterSKUForm.description}
                      onChange={(e) => setMasterSKUForm({...masterSKUForm, description: e.target.value})}
                      placeholder="Product description"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Category</label>
                    <Input
                      value={masterSKUForm.category}
                      onChange={(e) => setMasterSKUForm({...masterSKUForm, category: e.target.value})}
                      placeholder="Furniture / Chairs"
                    />
                  </div>
                </div>
                <div className="flex space-x-4">
                  <Button type="button" variant="outline" onClick={() => setShowMasterSKUForm(false)} className="flex-1">
                    Cancel
                  </Button>
                  <Button type="submit" className="flex-1">Create Master SKU</Button>
                </div>
              </form>
            </CardContent>
          </Card>
        </div>
      )}

      {/* CONTINUED IN NEXT FILE DUE TO LENGTH... */}
    </div>
  );
};