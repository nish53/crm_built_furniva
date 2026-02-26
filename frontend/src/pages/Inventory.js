import React, { useEffect, useState } from 'react';
import api from '../lib/api';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Badge } from '../components/ui/badge';
import { toast } from 'sonner';
import { Plus, Search, Trash2, List, ShoppingCart, X, DollarSign, Package } from 'lucide-react';
import { format } from 'date-fns';

export const Inventory = () => {
  const [masterSKUs, setMasterSKUs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [showMasterSKUForm, setShowMasterSKUForm] = useState(false);
  const [showListingsModal, setShowListingsModal] = useState(false);
  const [showProcurementModal, setShowProcurementModal] = useState(false);
  const [selectedMasterSKU, setSelectedMasterSKU] = useState(null);
  const [selectedMasterSKUData, setSelectedMasterSKUData] = useState(null);
  const [listings, setListings] = useState([]);
  const [batches, setBatches] = useState([]);
  const [averageCost, setAverageCost] = useState(null);

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
      
      const enrichedSKUs = await Promise.all(
        response.data.map(async (sku) => {
          try {
            const [listingsRes, batchesRes, costRes] = await Promise.all([
              api.get(`/platform-listings/by-master-sku/${sku.master_sku}`),
              api.get(`/procurement-batches/by-master-sku/${sku.master_sku}`),
              api.get(`/procurement-batches/average-cost/${sku.master_sku}?method=weighted`)
            ]);
            return {
              ...sku,
              listingsCount: listingsRes.data.length,
              batchesCount: batchesRes.data.length,
              averageCost: costRes.data.average_cost || 0
            };
          } catch (error) {
            return { ...sku, listingsCount: 0, batchesCount: 0, averageCost: 0 };
          }
        })
      );
      setMasterSKUs(enrichedSKUs);
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
      toast.success('Master SKU created');
      setShowMasterSKUForm(false);
      resetMasterSKUForm();
      fetchMasterSKUs();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create');
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

  const openListingsModal = async (masterSku, masterSKUData) => {
    setSelectedMasterSKU(masterSku);
    setSelectedMasterSKUData(masterSKUData);
    try {
      const response = await api.get(`/platform-listings/by-master-sku/${masterSku}`);
      setListings(response.data);
      setShowListingsModal(true);
    } catch (error) {
      setListings([]);
      setShowListingsModal(true);
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
      toast.success(`${promises.length} listing(s) added`);
      resetListingForm();
      openListingsModal(selectedMasterSKU, selectedMasterSKUData);
      fetchMasterSKUs();
    } catch (error) {
      toast.error('Failed to create listings');
    }
  };

  const handleDeleteListing = async (listingId) => {
    if (!confirm('Delete this listing?')) return;
    try {
      await api.delete(`/platform-listings/${listingId}`);
      toast.success('Listing deleted');
      openListingsModal(selectedMasterSKU, selectedMasterSKUData);
      fetchMasterSKUs();
    } catch (error) {
      toast.error('Failed to delete');
    }
  };

  const addListingPair = () => {
    if (listingForm.listings.length >= 10) {
      toast.error('Maximum 10 listings per batch');
      return;
    }
    setListingForm({
      ...listingForm,
      listings: [...listingForm.listings, { platform_sku: '', platform_product_id: '' }]
    });
  };

  const removeListingPair = (index) => {
    if (listingForm.listings.length === 1) return;
    const newListings = listingForm.listings.filter((_, i) => i !== index);
    setListingForm({ ...listingForm, listings: newListings });
  };

  const updateListingPair = (index, field, value) => {
    const newListings = [...listingForm.listings];
    newListings[index][field] = value;
    setListingForm({ ...listingForm, listings: newListings });
  };

  const openProcurementModal = async (masterSku, masterSKUData) => {
    setSelectedMasterSKU(masterSku);
    setSelectedMasterSKUData(masterSKUData);
    try {
      const [batchesRes, costRes] = await Promise.all([
        api.get(`/procurement-batches/by-master-sku/${masterSku}`),
        api.get(`/procurement-batches/average-cost/${masterSku}?method=weighted`)
      ]);
      setBatches(batchesRes.data);
      setAverageCost(costRes.data);
      setShowProcurementModal(true);
    } catch (error) {
      setBatches([]);
      setAverageCost(null);
      setShowProcurementModal(true);
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
          num_boxes: parseInt(procurementForm.num_boxes),
          box_dimensions: procurementForm.box_dimensions,
          reorder_level: procurementForm.reorder_level
        })
      });
      toast.success('Procurement added');
      resetProcurementForm();
      openProcurementModal(selectedMasterSKU, selectedMasterSKUData);
      fetchMasterSKUs();
    } catch (error) {
      toast.error('Failed to create');
    }
  };

  const handleDeleteBatch = async (batchId) => {
    if (!confirm('Delete this batch?')) return;
    try {
      await api.delete(`/procurement-batches/${batchId}`);
      toast.success('Batch deleted');
      openProcurementModal(selectedMasterSKU, selectedMasterSKUData);
      fetchMasterSKUs();
    } catch (error) {
      toast.error('Failed to delete');
    }
  };

  const addBoxDimension = () => {
    if (procurementForm.box_dimensions.length >= 10) {
      toast.error('Maximum 10 boxes');
      return;
    }
    const newDims = [...procurementForm.box_dimensions, { length: '', width: '', height: '' }];
    setProcurementForm({
      ...procurementForm,
      num_boxes: String(newDims.length),
      box_dimensions: newDims
    });
  };

  const removeBoxDimension = (index) => {
    if (procurementForm.box_dimensions.length === 1) return;
    const newDims = procurementForm.box_dimensions.filter((_, i) => i !== index);
    setProcurementForm({ 
      ...procurementForm, 
      num_boxes: String(newDims.length),
      box_dimensions: newDims 
    });
  };

  const updateBoxDimension = (index, field, value) => {
    const newDims = [...procurementForm.box_dimensions];
    newDims[index][field] = value;
    setProcurementForm({ ...procurementForm, box_dimensions: newDims });
  };

  const resetMasterSKUForm = () => {
    setMasterSKUForm({ master_sku: '', product_name: '', description: '', category: '' });
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
    return <div className="flex items-center justify-center h-screen"><div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div></div>;
  }

  const filteredSKUs = masterSKUs.filter(sku =>
    searchTerm === '' ||
    sku.master_sku.toLowerCase().includes(searchTerm.toLowerCase()) ||
    sku.product_name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold font-[Manrope]">Inventory & Master SKU</h1>
          <p className="text-muted-foreground mt-1">Manage Master SKUs, Platform Listings & Stock</p>
        </div>
        <Button onClick={() => setShowMasterSKUForm(true)}>
          <Plus className="w-4 h-4 mr-2" />Add Master SKU
        </Button>
      </div>

      <div className="relative">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4" />
        <Input placeholder="Search..." value={searchTerm} onChange={(e) => setSearchTerm(e.target.value)} className="pl-10" />
      </div>

      {/* Master SKU Cards */}
      {filteredSKUs.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <Package className="w-12 h-12 mx-auto mb-4 text-muted-foreground" />
            <p className="text-muted-foreground">No Master SKUs yet</p>
            <Button onClick={() => setShowMasterSKUForm(true)} className="mt-4">
              <Plus className="w-4 h-4 mr-2" />Create First Master SKU
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {filteredSKUs.map(sku => (
            <Card key={sku.id}>
              <CardContent className="p-6">
                <div className="space-y-4">
                  <div>
                    <h3 className="text-lg font-bold font-[Manrope]">{sku.master_sku}</h3>
                    <p className="text-sm text-foreground mt-1">{sku.product_name}</p>
                    {sku.description && <p className="text-xs text-muted-foreground mt-1">{sku.description}</p>}
                    {sku.category && <Badge className="mt-2">{sku.category}</Badge>}
                  </div>

                  <div className="flex flex-wrap gap-2">
                    <Badge variant="outline" className="text-xs"><List className="w-3 h-3 mr-1" />Listings: {sku.listingsCount}</Badge>
                    <Badge variant="outline" className="text-xs"><ShoppingCart className="w-3 h-3 mr-1" />Batches: {sku.batchesCount}</Badge>
                    <Badge variant="outline" className="text-xs"><DollarSign className="w-3 h-3 mr-1" />₹{sku.averageCost.toFixed(2)}</Badge>
                  </div>

                  <div className="flex flex-col gap-2">
                    <Button size="sm" variant="outline" onClick={() => openListingsModal(sku.master_sku, sku)} className="w-full">
                      <List className="w-4 h-4 mr-2" />Manage Listings
                    </Button>
                    <Button size="sm" variant="outline" onClick={() => openProcurementModal(sku.master_sku, sku)} className="w-full">
                      <ShoppingCart className="w-4 h-4 mr-2" />Manage Inventory
                    </Button>
                    <Button size="sm" variant="destructive" onClick={() => handleDeleteMasterSKU(sku.master_sku)} className="w-full">
                      <Trash2 className="w-4 h-4 mr-2" />Delete
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* MODALS CONTINUED IN NEXT FILE DUE TO LENGTH... */}
    </div>
  );
};