import React, { useState, useEffect } from 'react';
import api from '../lib/api';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from './ui/dialog';
import { toast } from 'sonner';

export const MasterSKUDialog = ({ isOpen, onClose, prefilledSKU = '', onSuccess }) => {
  const [formData, setFormData] = useState({
    master_sku: '',
    amazon_sku: '',
    flipkart_sku: '',
    website_sku: '',
    product_name: '',
    category: '',
  });

  useEffect(() => {
    if (prefilledSKU) {
      // Try to detect channel from the SKU or set it to amazon_sku by default
      setFormData(prev => ({
        ...prev,
        amazon_sku: prefilledSKU
      }));
    }
  }, [prefilledSKU]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.master_sku) {
      toast.error('Master SKU is required');
      return;
    }

    try {
      await api.post('/master-sku/', formData);
      toast.success('Master SKU mapping created successfully');
      if (onSuccess) onSuccess();
      onClose();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create mapping');
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle className="font-[Manrope]">Map SKU to Master SKU</DialogTitle>
        </DialogHeader>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="col-span-2">
              <Label htmlFor="master_sku">Master SKU *</Label>
              <Input
                id="master_sku"
                placeholder="e.g., SKYLINE-2DOOR"
                value={formData.master_sku}
                onChange={(e) => setFormData({ ...formData, master_sku: e.target.value })}
                required
              />
            </div>

            <div>
              <Label htmlFor="amazon_sku">Amazon SKU</Label>
              <Input
                id="amazon_sku"
                placeholder="Amazon SKU code"
                value={formData.amazon_sku}
                onChange={(e) => setFormData({ ...formData, amazon_sku: e.target.value })}
              />
            </div>

            <div>
              <Label htmlFor="flipkart_sku">Flipkart SKU</Label>
              <Input
                id="flipkart_sku"
                placeholder="Flipkart SKU code"
                value={formData.flipkart_sku}
                onChange={(e) => setFormData({ ...formData, flipkart_sku: e.target.value })}
              />
            </div>

            <div>
              <Label htmlFor="website_sku">Website SKU</Label>
              <Input
                id="website_sku"
                placeholder="Website SKU code"
                value={formData.website_sku}
                onChange={(e) => setFormData({ ...formData, website_sku: e.target.value })}
              />
            </div>

            <div>
              <Label htmlFor="product_name">Product Name</Label>
              <Input
                id="product_name"
                placeholder="Product name"
                value={formData.product_name}
                onChange={(e) => setFormData({ ...formData, product_name: e.target.value })}
              />
            </div>

            <div className="col-span-2">
              <Label htmlFor="category">Category</Label>
              <Input
                id="category"
                placeholder="Product category"
                value={formData.category}
                onChange={(e) => setFormData({ ...formData, category: e.target.value })}
              />
            </div>
          </div>

          <DialogFooter>
            <Button type="button" variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button type="submit">
              Save Mapping
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
};
