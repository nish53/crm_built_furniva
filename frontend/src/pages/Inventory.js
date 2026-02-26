import React, { useEffect, useState, useCallback } from 'react';
import api from '../lib/api';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Badge } from '../components/ui/badge';
import { toast } from 'sonner';
import {
  Plus, Search, Trash2, ShoppingCart, X,
  Package, Edit, Layers, Tag
} from 'lucide-react';
import { format } from 'date-fns';

export const Inventory = () => {
  const [masterSKUs, setMasterSKUs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');

  const [showCreateForm, setShowCreateForm] = useState(false);
  const [editingSKU, setEditingSKU] = useState(null);
  const [showListingsModal, setShowListingsModal] = useState(false);
  const [showProcurementModal, setShowProcurementModal] = useState(false);
  const [selectedSKU, setSelectedSKU] = useState(null);

  const [listings, setListings] = useState([]);
  const [batches, setBatches] = useState([]);
  const [avgCost, setAvgCost] = useState(null);

  // Master SKU Form (simplified - no fnsku, dims, weight, costs)
  const [skuForm, setSkuForm] = useState({
    master_sku: '', product_name: '', description: '', category: '',
    amazon_sku: '', amazon_asin: '',
    flipkart_sku: '', flipkart_fsn: '', website_sku: ''
  });

  // Platform Listing Form
  const [listingForm, setListingForm] = useState({
    platform: 'amazon',
    rows: [{ platform_sku: '', platform_product_id: '' }]
  });

  // Procurement Form with box details
  const [procForm, setProcForm] = useState({
    batch_number: '', procurement_date: new Date().toISOString().split('T')[0],
    quantity: '', unit_cost: '', supplier: '', notes: '',
    num_boxes: 1, box_weights: [0], box_dimensions: [{ length: 0, width: 0, height: 0 }]
  });

  const fetchMasterSKUs = useCallback(async () => {
    try {
      const params = searchTerm ? { search: searchTerm } : {};
      const res = await api.get('/master-sku/', { params });
      const skus = res.data;
      const enriched = await Promise.all(
        skus.map(async (sku) => {
          try {
            const [lRes, bRes, cRes] = await Promise.all([
              api.get(`/platform-listings/by-master-sku/${sku.master_sku}`),
              api.get(`/procurement-batches/by-master-sku/${sku.master_sku}`),
              api.get(`/procurement-batches/average-cost/${sku.master_sku}?method=weighted`)
            ]);
            const totalStock = bRes.data.reduce((sum, b) => sum + (b.quantity || 0), 0);
            const totalWeight = bRes.data.reduce((sum, b) => sum + (b.total_weight || 0), 0);
            return { ...sku, listingsCount: lRes.data.length, batchesCount: bRes.data.length, totalStock, totalWeight, averageCost: cRes.data.average_cost || 0 };
          } catch {
            return { ...sku, listingsCount: 0, batchesCount: 0, totalStock: 0, totalWeight: 0, averageCost: 0 };
          }
        })
      );
      setMasterSKUs(enriched);
    } catch { toast.error('Failed to fetch inventory'); }
    finally { setLoading(false); }
  }, [searchTerm]);

  useEffect(() => { fetchMasterSKUs(); }, [fetchMasterSKUs]);

  // === MASTER SKU CRUD ===
  const handleSaveSKU = async (e) => {
    e.preventDefault();
    try {
      if (editingSKU) {
        await api.put(`/master-sku/${editingSKU}`, skuForm);
        toast.success('Master SKU updated');
      } else {
        await api.post('/master-sku/', skuForm);
        toast.success('Master SKU created');
      }
      closeCreateForm();
      fetchMasterSKUs();
    } catch (err) { toast.error(err.response?.data?.detail || 'Failed to save'); }
  };

  const handleDeleteSKU = async (masterSku) => {
    if (!confirm(`Delete "${masterSku}" and all its listings/batches?`)) return;
    try { await api.delete(`/master-sku/${masterSku}`); toast.success('Deleted'); fetchMasterSKUs(); }
    catch { toast.error('Failed to delete'); }
  };

  const openEditForm = (sku) => {
    setSkuForm({
      master_sku: sku.master_sku || '', product_name: sku.product_name || '',
      description: sku.description || '', category: sku.category || '',
      amazon_sku: sku.amazon_sku || '', amazon_asin: sku.amazon_asin || '',
      flipkart_sku: sku.flipkart_sku || '', flipkart_fsn: sku.flipkart_fsn || '',
      website_sku: sku.website_sku || ''
    });
    setEditingSKU(sku.master_sku);
    setShowCreateForm(true);
  };

  const closeCreateForm = () => {
    setShowCreateForm(false); setEditingSKU(null);
    setSkuForm({ master_sku: '', product_name: '', description: '', category: '', amazon_sku: '', amazon_asin: '', flipkart_sku: '', flipkart_fsn: '', website_sku: '' });
  };

  // === PLATFORM LISTINGS ===
  const openListings = async (sku) => {
    setSelectedSKU(sku);
    try { const res = await api.get(`/platform-listings/by-master-sku/${sku.master_sku}`); setListings(res.data); }
    catch { setListings([]); }
    setListingForm({ platform: 'amazon', rows: [{ platform_sku: '', platform_product_id: '' }] });
    setShowListingsModal(true);
  };

  const addListingRow = () => {
    if (listingForm.rows.length >= 10) return;
    setListingForm({ ...listingForm, rows: [...listingForm.rows, { platform_sku: '', platform_product_id: '' }] });
  };
  const updateListingRow = (idx, field, value) => {
    const rows = [...listingForm.rows]; rows[idx][field] = value;
    setListingForm({ ...listingForm, rows });
  };
  const removeListingRow = (idx) => {
    if (listingForm.rows.length <= 1) return;
    setListingForm({ ...listingForm, rows: listingForm.rows.filter((_, i) => i !== idx) });
  };

  const handleAddListings = async (e) => {
    e.preventDefault();
    const valid = listingForm.rows.filter(r => r.platform_sku);
    if (!valid.length) { toast.error('Add at least one SKU'); return; }
    try {
      await Promise.all(valid.map(r => api.post('/platform-listings/', {
        master_sku: selectedSKU.master_sku, platform: listingForm.platform,
        platform_sku: r.platform_sku, platform_product_id: r.platform_product_id,
        is_active: true
      })));
      toast.success(`${valid.length} listing(s) added`);
      const res = await api.get(`/platform-listings/by-master-sku/${selectedSKU.master_sku}`);
      setListings(res.data);
      setListingForm({ platform: 'amazon', rows: [{ platform_sku: '', platform_product_id: '' }] });
      fetchMasterSKUs();
    } catch { toast.error('Failed to create listings'); }
  };

  const handleDeleteListing = async (id) => {
    if (!confirm('Delete this listing?')) return;
    try {
      await api.delete(`/platform-listings/${id}`); toast.success('Deleted');
      const res = await api.get(`/platform-listings/by-master-sku/${selectedSKU.master_sku}`);
      setListings(res.data); fetchMasterSKUs();
    } catch { toast.error('Failed to delete'); }
  };

  // === PROCUREMENT ===
  const openProcurement = async (sku) => {
    setSelectedSKU(sku);
    try {
      const [bRes, cRes] = await Promise.all([
        api.get(`/procurement-batches/by-master-sku/${sku.master_sku}`),
        api.get(`/procurement-batches/average-cost/${sku.master_sku}?method=weighted`)
      ]);
      setBatches(bRes.data); setAvgCost(cRes.data);
    } catch { setBatches([]); setAvgCost(null); }
    resetProcForm();
    setShowProcurementModal(true);
  };

  const resetProcForm = () => setProcForm({
    batch_number: '', procurement_date: new Date().toISOString().split('T')[0],
    quantity: '', unit_cost: '', supplier: '', notes: '',
    num_boxes: 1, box_weights: [0], box_dimensions: [{ length: 0, width: 0, height: 0 }]
  });

  const handleNumBoxesChange = (val) => {
    const n = Math.max(1, Math.min(20, parseInt(val) || 1));
    const weights = Array.from({ length: n }, (_, i) => procForm.box_weights[i] || 0);
    const dims = Array.from({ length: n }, (_, i) => procForm.box_dimensions[i] || { length: 0, width: 0, height: 0 });
    setProcForm({ ...procForm, num_boxes: n, box_weights: weights, box_dimensions: dims });
  };

  const updateBoxWeight = (idx, val) => {
    const w = [...procForm.box_weights]; w[idx] = parseFloat(val) || 0;
    setProcForm({ ...procForm, box_weights: w });
  };

  const updateBoxDim = (idx, field, val) => {
    const d = [...procForm.box_dimensions];
    d[idx] = { ...d[idx], [field]: parseFloat(val) || 0 };
    setProcForm({ ...procForm, box_dimensions: d });
  };

  const totalWeight = procForm.box_weights.reduce((s, w) => s + w, 0);

  const handleAddBatch = async (e) => {
    e.preventDefault();
    try {
      await api.post('/procurement-batches/', {
        master_sku: selectedSKU.master_sku,
        batch_number: procForm.batch_number,
        procurement_date: new Date(procForm.procurement_date).toISOString(),
        quantity: parseInt(procForm.quantity),
        unit_cost: parseFloat(procForm.unit_cost),
        num_boxes: procForm.num_boxes,
        box_weights: procForm.box_weights,
        box_dimensions: procForm.box_dimensions,
        supplier: procForm.supplier || null,
        notes: procForm.notes || null
      });
      toast.success('Batch added');
      const [bRes, cRes] = await Promise.all([
        api.get(`/procurement-batches/by-master-sku/${selectedSKU.master_sku}`),
        api.get(`/procurement-batches/average-cost/${selectedSKU.master_sku}?method=weighted`)
      ]);
      setBatches(bRes.data); setAvgCost(cRes.data);
      resetProcForm(); fetchMasterSKUs();
    } catch { toast.error('Failed to create batch'); }
  };

  const handleDeleteBatch = async (id) => {
    if (!confirm('Delete this batch?')) return;
    try {
      await api.delete(`/procurement-batches/${id}`); toast.success('Deleted');
      const [bRes, cRes] = await Promise.all([
        api.get(`/procurement-batches/by-master-sku/${selectedSKU.master_sku}`),
        api.get(`/procurement-batches/average-cost/${selectedSKU.master_sku}?method=weighted`)
      ]);
      setBatches(bRes.data); setAvgCost(cRes.data); fetchMasterSKUs();
    } catch { toast.error('Failed to delete'); }
  };

  const platformLabel = (p) => ({ amazon: 'Amazon', flipkart: 'Flipkart', website: 'Website' }[p] || p);
  const platformIdLabel = (p) => ({ amazon: 'ASIN', flipkart: 'FSN ID', website: 'Product ID' }[p] || 'ID');

  const filtered = masterSKUs.filter(s =>
    !searchTerm || s.master_sku?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    s.product_name?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  if (loading) return (
    <div className="flex items-center justify-center h-[60vh]">
      <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-primary" />
    </div>
  );

  return (
    <div className="space-y-6" data-testid="inventory-page">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold font-[Manrope]">Inventory</h1>
          <p className="text-muted-foreground mt-1">Master SKUs, Platform Listings & Procurement</p>
        </div>
        <Button onClick={() => setShowCreateForm(true)} data-testid="add-master-sku-btn">
          <Plus className="w-4 h-4 mr-2" />Add Master SKU
        </Button>
      </div>

      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
        <Input placeholder="Search by SKU or product name..." value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)} className="pl-10" data-testid="inventory-search" />
      </div>

      {filtered.length === 0 ? (
        <Card><CardContent className="py-12 text-center">
          <Package className="w-12 h-12 mx-auto mb-4 text-muted-foreground" />
          <p className="text-muted-foreground mb-4">No Master SKUs found</p>
          <Button onClick={() => setShowCreateForm(true)}><Plus className="w-4 h-4 mr-2" />Create First Master SKU</Button>
        </CardContent></Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {filtered.map(sku => (
            <Card key={sku.id} className="hover:border-primary/40 transition-colors" data-testid={`sku-card-${sku.master_sku}`}>
              <CardContent className="p-5 space-y-4">
                <div className="flex justify-between items-start">
                  <div className="min-w-0 flex-1">
                    <h3 className="font-bold font-[Manrope] text-base truncate">{sku.master_sku}</h3>
                    <p className="text-sm text-foreground mt-0.5 truncate">{sku.product_name}</p>
                    {sku.category && <Badge variant="outline" className="mt-1.5 text-xs">{sku.category}</Badge>}
                  </div>
                  <div className="flex gap-1 ml-2">
                    <Button variant="ghost" size="sm" onClick={() => openEditForm(sku)} data-testid={`edit-sku-${sku.master_sku}`}><Edit className="w-3.5 h-3.5" /></Button>
                    <Button variant="ghost" size="sm" onClick={() => handleDeleteSKU(sku.master_sku)}><Trash2 className="w-3.5 h-3.5 text-destructive" /></Button>
                  </div>
                </div>
                <div className="grid grid-cols-3 gap-2">
                  <div className="bg-secondary/50 rounded-lg p-2 text-center">
                    <p className="text-xs text-muted-foreground">Listings</p>
                    <p className="font-bold text-sm">{sku.listingsCount}</p>
                  </div>
                  <div className="bg-secondary/50 rounded-lg p-2 text-center">
                    <p className="text-xs text-muted-foreground">Stock</p>
                    <p className="font-bold text-sm">{sku.totalStock}</p>
                  </div>
                  <div className="bg-secondary/50 rounded-lg p-2 text-center">
                    <p className="text-xs text-muted-foreground">Avg Cost</p>
                    <p className="font-bold text-sm font-[JetBrains_Mono]">{sku.averageCost > 0 ? `₹${sku.averageCost.toFixed(0)}` : '-'}</p>
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-2">
                  <Button size="sm" variant="outline" onClick={() => openListings(sku)} data-testid={`manage-listings-${sku.master_sku}`}>
                    <Layers className="w-3.5 h-3.5 mr-1.5" />Listings
                  </Button>
                  <Button size="sm" variant="outline" onClick={() => openProcurement(sku)} data-testid={`manage-procurement-${sku.master_sku}`}>
                    <ShoppingCart className="w-3.5 h-3.5 mr-1.5" />Procurement
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* ===== CREATE/EDIT MASTER SKU MODAL ===== */}
      {showCreateForm && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4" data-testid="master-sku-modal">
          <Card className="w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle className="font-[Manrope]">{editingSKU ? 'Edit' : 'Create'} Master SKU</CardTitle>
              <Button variant="ghost" size="sm" onClick={closeCreateForm}><X className="w-4 h-4" /></Button>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSaveSKU} className="space-y-5">
                <div>
                  <h4 className="text-sm font-semibold mb-3 flex items-center gap-2"><Tag className="w-4 h-4" />Basic Information</h4>
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="text-xs font-medium text-muted-foreground">Master SKU *</label>
                      <Input required value={skuForm.master_sku} disabled={!!editingSKU}
                        onChange={e => setSkuForm({ ...skuForm, master_sku: e.target.value })}
                        placeholder="e.g., FURN-001" data-testid="input-master-sku" />
                    </div>
                    <div>
                      <label className="text-xs font-medium text-muted-foreground">Product Name *</label>
                      <Input required value={skuForm.product_name}
                        onChange={e => setSkuForm({ ...skuForm, product_name: e.target.value })}
                        placeholder="Product name" data-testid="input-product-name" />
                    </div>
                    <div className="col-span-2">
                      <label className="text-xs font-medium text-muted-foreground">Description</label>
                      <Input value={skuForm.description} onChange={e => setSkuForm({ ...skuForm, description: e.target.value })} placeholder="Brief description" />
                    </div>
                    <div>
                      <label className="text-xs font-medium text-muted-foreground">Category</label>
                      <Input value={skuForm.category} onChange={e => setSkuForm({ ...skuForm, category: e.target.value })} placeholder="e.g., Furniture, Decor" />
                    </div>
                  </div>
                </div>
                <div>
                  <h4 className="text-sm font-semibold mb-3">Amazon</h4>
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="text-xs font-medium text-muted-foreground">Seller SKU</label>
                      <Input value={skuForm.amazon_sku} onChange={e => setSkuForm({ ...skuForm, amazon_sku: e.target.value })} placeholder="Seller SKU" />
                    </div>
                    <div>
                      <label className="text-xs font-medium text-muted-foreground">ASIN</label>
                      <Input value={skuForm.amazon_asin} onChange={e => setSkuForm({ ...skuForm, amazon_asin: e.target.value })} placeholder="B0XXXXXXXX" />
                    </div>
                  </div>
                </div>
                <div>
                  <h4 className="text-sm font-semibold mb-3">Flipkart</h4>
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="text-xs font-medium text-muted-foreground">Seller SKU</label>
                      <Input value={skuForm.flipkart_sku} onChange={e => setSkuForm({ ...skuForm, flipkart_sku: e.target.value })} placeholder="Seller SKU" />
                    </div>
                    <div>
                      <label className="text-xs font-medium text-muted-foreground">FSN ID</label>
                      <Input value={skuForm.flipkart_fsn} onChange={e => setSkuForm({ ...skuForm, flipkart_fsn: e.target.value })} placeholder="FSN identifier" />
                    </div>
                  </div>
                </div>
                <div>
                  <h4 className="text-sm font-semibold mb-3">Website</h4>
                  <div>
                    <label className="text-xs font-medium text-muted-foreground">Website SKU</label>
                    <Input value={skuForm.website_sku} onChange={e => setSkuForm({ ...skuForm, website_sku: e.target.value })} placeholder="Website SKU" />
                  </div>
                </div>
                <div className="flex gap-3 pt-2">
                  <Button type="button" variant="outline" onClick={closeCreateForm} className="flex-1">Cancel</Button>
                  <Button type="submit" className="flex-1" data-testid="save-master-sku-btn">{editingSKU ? 'Update' : 'Create'} Master SKU</Button>
                </div>
              </form>
            </CardContent>
          </Card>
        </div>
      )}

      {/* ===== PLATFORM LISTINGS MODAL ===== */}
      {showListingsModal && selectedSKU && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4" data-testid="listings-modal">
          <Card className="w-full max-w-3xl max-h-[90vh] overflow-y-auto">
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle className="font-[Manrope]">Platform Listings</CardTitle>
                <p className="text-sm text-muted-foreground mt-1"><span className="font-[JetBrains_Mono]">{selectedSKU.master_sku}</span> - {selectedSKU.product_name}</p>
              </div>
              <Button variant="ghost" size="sm" onClick={() => setShowListingsModal(false)}><X className="w-4 h-4" /></Button>
            </CardHeader>
            <CardContent className="space-y-6">
              {listings.length > 0 && (
                <div>
                  <h4 className="text-sm font-semibold mb-3">Current Listings ({listings.length})</h4>
                  <div className="space-y-2">
                    {listings.map(l => (
                      <div key={l.id} className="flex items-center justify-between p-3 bg-secondary/30 rounded-lg">
                        <div className="flex items-center gap-3 min-w-0">
                          <Badge variant="outline" className="shrink-0 uppercase text-xs">{l.platform}</Badge>
                          <div className="min-w-0">
                            <p className="text-sm font-medium font-[JetBrains_Mono] truncate">SKU: {l.platform_sku || '-'}</p>
                            <p className="text-xs text-muted-foreground truncate">
                              {l.platform === 'amazon' ? 'ASIN' : l.platform === 'flipkart' ? 'FSN' : 'ID'}: {l.platform_product_id || '-'}
                              {l.platform_fnsku && ` | FNSKU: ${l.platform_fnsku}`}
                            </p>
                          </div>
                        </div>
                        <Button variant="ghost" size="sm" onClick={() => handleDeleteListing(l.id)}><Trash2 className="w-3.5 h-3.5 text-destructive" /></Button>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              <div>
                <h4 className="text-sm font-semibold mb-3">Add New Listings</h4>
                <form onSubmit={handleAddListings} className="space-y-4">
                  <div>
                    <label className="text-xs font-medium text-muted-foreground">Platform</label>
                    <Select value={listingForm.platform} onValueChange={v => setListingForm({ ...listingForm, platform: v })}>
                      <SelectTrigger data-testid="listing-platform-select"><SelectValue /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="amazon">Amazon</SelectItem>
                        <SelectItem value="flipkart">Flipkart</SelectItem>
                        <SelectItem value="website">Website</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  {listingForm.rows.map((row, idx) => (
                    <div key={idx} className="flex gap-2 items-end">
                      <div className="flex-1">
                        <label className="text-xs font-medium text-muted-foreground">Seller SKU</label>
                        <Input value={row.platform_sku} onChange={e => updateListingRow(idx, 'platform_sku', e.target.value)} placeholder="Seller SKU" data-testid={`listing-sku-${idx}`} />
                      </div>
                      <div className="flex-1">
                        <label className="text-xs font-medium text-muted-foreground">{platformIdLabel(listingForm.platform)}</label>
                        <Input value={row.platform_product_id} onChange={e => updateListingRow(idx, 'platform_product_id', e.target.value)} placeholder={platformIdLabel(listingForm.platform)} />
                      </div>
                      <Button type="button" variant="ghost" size="sm" onClick={() => removeListingRow(idx)} disabled={listingForm.rows.length <= 1}><X className="w-3.5 h-3.5" /></Button>
                    </div>
                  ))}
                  <div className="flex gap-3">
                    <Button type="button" variant="outline" size="sm" onClick={addListingRow}><Plus className="w-3.5 h-3.5 mr-1" />Add Row</Button>
                    <Button type="submit" size="sm" data-testid="save-listings-btn">Save Listings</Button>
                  </div>
                </form>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* ===== PROCUREMENT BATCHES MODAL ===== */}
      {showProcurementModal && selectedSKU && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4" data-testid="procurement-modal">
          <Card className="w-full max-w-4xl max-h-[90vh] overflow-y-auto">
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle className="font-[Manrope]">Procurement & Stock</CardTitle>
                <p className="text-sm text-muted-foreground mt-1"><span className="font-[JetBrains_Mono]">{selectedSKU.master_sku}</span> - {selectedSKU.product_name}</p>
              </div>
              <Button variant="ghost" size="sm" onClick={() => setShowProcurementModal(false)}><X className="w-4 h-4" /></Button>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Cost Summary */}
              {avgCost && (
                <div className="grid grid-cols-3 gap-3">
                  <div className="bg-primary/5 border border-primary/10 rounded-lg p-3 text-center">
                    <p className="text-xs text-muted-foreground">Weighted Avg Cost</p>
                    <p className="text-lg font-bold font-[JetBrains_Mono] text-primary">₹{avgCost.average_cost?.toFixed(2) || '0.00'}</p>
                  </div>
                  <div className="bg-secondary/50 rounded-lg p-3 text-center">
                    <p className="text-xs text-muted-foreground">Total Batches</p>
                    <p className="text-lg font-bold">{batches.length}</p>
                  </div>
                  <div className="bg-secondary/50 rounded-lg p-3 text-center">
                    <p className="text-xs text-muted-foreground">Total Stock</p>
                    <p className="text-lg font-bold">{batches.reduce((s, b) => s + (b.quantity || 0), 0)}</p>
                  </div>
                </div>
              )}

              {/* Existing Batches */}
              {batches.length > 0 && (
                <div>
                  <h4 className="text-sm font-semibold mb-3">Procurement History</h4>
                  <div className="space-y-2">
                    {batches.map(b => (
                      <div key={b.id} className="flex items-center justify-between p-3 bg-secondary/30 rounded-lg">
                        <div className="grid grid-cols-5 gap-3 flex-1 min-w-0 text-sm">
                          <div>
                            <p className="text-xs text-muted-foreground">Batch</p>
                            <p className="font-medium font-[JetBrains_Mono]">{b.batch_number}</p>
                          </div>
                          <div>
                            <p className="text-xs text-muted-foreground">Qty</p>
                            <p className="font-medium">{b.quantity}</p>
                          </div>
                          <div>
                            <p className="text-xs text-muted-foreground">Unit Cost</p>
                            <p className="font-medium font-[JetBrains_Mono]">₹{b.unit_cost}</p>
                          </div>
                          <div>
                            <p className="text-xs text-muted-foreground">Boxes / Weight</p>
                            <p className="font-medium">{b.num_boxes || '-'} boxes / {(b.total_weight || 0).toFixed(1)} kg</p>
                          </div>
                          <div>
                            <p className="text-xs text-muted-foreground">Date</p>
                            <p className="font-medium">{b.procurement_date ? format(new Date(b.procurement_date), 'MMM dd, yyyy') : '-'}</p>
                          </div>
                        </div>
                        <Button variant="ghost" size="sm" onClick={() => handleDeleteBatch(b.id)}><Trash2 className="w-3.5 h-3.5 text-destructive" /></Button>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Add New Batch */}
              <div>
                <h4 className="text-sm font-semibold mb-3">Add Procurement Batch</h4>
                <form onSubmit={handleAddBatch} className="space-y-4">
                  <div className="grid grid-cols-3 gap-3">
                    <div>
                      <label className="text-xs font-medium text-muted-foreground">Batch Number *</label>
                      <Input required value={procForm.batch_number} onChange={e => setProcForm({ ...procForm, batch_number: e.target.value })} placeholder="e.g., BATCH-001" data-testid="input-batch-number" />
                    </div>
                    <div>
                      <label className="text-xs font-medium text-muted-foreground">Date *</label>
                      <Input type="date" required value={procForm.procurement_date} onChange={e => setProcForm({ ...procForm, procurement_date: e.target.value })} />
                    </div>
                    <div>
                      <label className="text-xs font-medium text-muted-foreground">Supplier</label>
                      <Input value={procForm.supplier} onChange={e => setProcForm({ ...procForm, supplier: e.target.value })} placeholder="Supplier name" />
                    </div>
                    <div>
                      <label className="text-xs font-medium text-muted-foreground">Quantity *</label>
                      <Input type="number" required min="1" value={procForm.quantity} onChange={e => setProcForm({ ...procForm, quantity: e.target.value })} placeholder="0" data-testid="input-batch-quantity" />
                    </div>
                    <div>
                      <label className="text-xs font-medium text-muted-foreground">Unit Cost (INR) *</label>
                      <Input type="number" required step="0.01" min="0" value={procForm.unit_cost} onChange={e => setProcForm({ ...procForm, unit_cost: e.target.value })} placeholder="0.00" data-testid="input-unit-cost" />
                    </div>
                    <div>
                      <label className="text-xs font-medium text-muted-foreground">Number of Boxes *</label>
                      <Input type="number" required min="1" max="20" value={procForm.num_boxes} onChange={e => handleNumBoxesChange(e.target.value)} data-testid="input-num-boxes" />
                    </div>
                  </div>

                  {/* Per-box weight and dimensions */}
                  <div className="border rounded-lg p-4 space-y-3 bg-secondary/20">
                    <div className="flex justify-between items-center">
                      <h5 className="text-sm font-semibold">Box Details ({procForm.num_boxes} {procForm.num_boxes === 1 ? 'box' : 'boxes'})</h5>
                      <div className="text-sm font-[JetBrains_Mono]">
                        Total Weight: <span className="font-bold text-primary">{totalWeight.toFixed(2)} kg</span>
                      </div>
                    </div>
                    <div className="space-y-2">
                      {Array.from({ length: procForm.num_boxes }).map((_, idx) => (
                        <div key={idx} className="grid grid-cols-5 gap-2 items-end">
                          <div className="text-xs font-medium text-muted-foreground self-center">Box {idx + 1}</div>
                          <div>
                            {idx === 0 && <label className="text-xs font-medium text-muted-foreground">Weight (kg)</label>}
                            <Input type="number" step="0.01" min="0" value={procForm.box_weights[idx] || ''} onChange={e => updateBoxWeight(idx, e.target.value)} placeholder="kg" />
                          </div>
                          <div>
                            {idx === 0 && <label className="text-xs font-medium text-muted-foreground">Length (cm)</label>}
                            <Input type="number" step="0.1" min="0" value={procForm.box_dimensions[idx]?.length || ''} onChange={e => updateBoxDim(idx, 'length', e.target.value)} placeholder="L" />
                          </div>
                          <div>
                            {idx === 0 && <label className="text-xs font-medium text-muted-foreground">Width (cm)</label>}
                            <Input type="number" step="0.1" min="0" value={procForm.box_dimensions[idx]?.width || ''} onChange={e => updateBoxDim(idx, 'width', e.target.value)} placeholder="W" />
                          </div>
                          <div>
                            {idx === 0 && <label className="text-xs font-medium text-muted-foreground">Height (cm)</label>}
                            <Input type="number" step="0.1" min="0" value={procForm.box_dimensions[idx]?.height || ''} onChange={e => updateBoxDim(idx, 'height', e.target.value)} placeholder="H" />
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div>
                    <label className="text-xs font-medium text-muted-foreground">Notes</label>
                    <Input value={procForm.notes} onChange={e => setProcForm({ ...procForm, notes: e.target.value })} placeholder="Additional notes" />
                  </div>
                  <Button type="submit" data-testid="save-batch-btn">Add Batch</Button>
                </form>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
};
