import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../lib/api';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { toast } from 'sonner';
import { ArrowLeft } from 'lucide-react';

export const NewOrder = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    channel: 'whatsapp',
    order_number: '',
    order_date: new Date().toISOString().split('T')[0],
    dispatch_by: '',
    customer_name: '',
    phone: '',
    shipping_address: '',
    city: '',
    state: '',
    pincode: '',
    sku: '',
    master_sku: '',
    fnsku: '',
    asin: '',
    product_name: '',
    quantity: 1,
    price: 0,
    instructions: '',
  });

  const handleChange = (field, value) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const payload = {
        ...formData,
        customer_id: crypto.randomUUID(),
        order_date: new Date(formData.order_date).toISOString(),
        dispatch_by: new Date(formData.dispatch_by).toISOString(),
        quantity: parseInt(formData.quantity),
        price: parseFloat(formData.price),
      };

      await api.post('/orders/', payload);
      toast.success('Order created successfully');
      navigate('/orders');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create order');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6" data-testid="new-order-page">
      <div className="flex items-center gap-4">
        <Button variant="ghost" onClick={() => navigate('/orders')} data-testid="back-button">
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back
        </Button>
        <div>
          <h1 className="text-3xl font-bold font-[Manrope] text-foreground tracking-tight">
            Create New Order
          </h1>
          <p className="text-muted-foreground mt-1">Manually add a new order to the system</p>
        </div>
      </div>

      <form onSubmit={handleSubmit}>
        <Card className="border-border/60">
          <CardHeader>
            <CardTitle className="font-[Manrope]">Order Information</CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="channel">Channel *</Label>
                <Select value={formData.channel} onValueChange={(val) => handleChange('channel', val)}>
                  <SelectTrigger data-testid="channel-select">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="whatsapp">WhatsApp</SelectItem>
                    <SelectItem value="phone">Phone</SelectItem>
                    <SelectItem value="website">Website</SelectItem>
                    <SelectItem value="amazon">Amazon</SelectItem>
                    <SelectItem value="flipkart">Flipkart</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="order_number">Order Number *</Label>
                <Input
                  data-testid="order-number-input"
                  id="order_number"
                  value={formData.order_number}
                  onChange={(e) => handleChange('order_number', e.target.value)}
                  required
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="order_date">Order Date *</Label>
                <Input
                  data-testid="order-date-input"
                  id="order_date"
                  type="date"
                  value={formData.order_date}
                  onChange={(e) => handleChange('order_date', e.target.value)}
                  required
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="dispatch_by">Dispatch By *</Label>
                <Input
                  data-testid="dispatch-by-input"
                  id="dispatch_by"
                  type="date"
                  value={formData.dispatch_by}
                  onChange={(e) => handleChange('dispatch_by', e.target.value)}
                  required
                />
              </div>
            </div>

            <div className="border-t border-border pt-6">
              <h3 className="text-lg font-semibold font-[Manrope] mb-4">Customer Details</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="customer_name">Customer Name *</Label>
                  <Input
                    data-testid="customer-name-input"
                    id="customer_name"
                    value={formData.customer_name}
                    onChange={(e) => handleChange('customer_name', e.target.value)}
                    required
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="phone">Phone *</Label>
                  <Input
                    data-testid="phone-input"
                    id="phone"
                    value={formData.phone}
                    onChange={(e) => handleChange('phone', e.target.value)}
                    required
                  />
                </div>

                <div className="space-y-2 md:col-span-2">
                  <Label htmlFor="shipping_address">Shipping Address</Label>
                  <Input
                    data-testid="address-input"
                    id="shipping_address"
                    value={formData.shipping_address}
                    onChange={(e) => handleChange('shipping_address', e.target.value)}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="city">City</Label>
                  <Input
                    data-testid="city-input"
                    id="city"
                    value={formData.city}
                    onChange={(e) => handleChange('city', e.target.value)}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="state">State</Label>
                  <Input
                    data-testid="state-input"
                    id="state"
                    value={formData.state}
                    onChange={(e) => handleChange('state', e.target.value)}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="pincode">Pincode *</Label>
                  <Input
                    data-testid="pincode-input"
                    id="pincode"
                    value={formData.pincode}
                    onChange={(e) => handleChange('pincode', e.target.value)}
                    required
                  />
                </div>
              </div>
            </div>

            <div className="border-t border-border pt-6">
              <h3 className="text-lg font-semibold font-[Manrope] mb-4">Product Details</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="sku">SKU *</Label>
                  <Input
                    data-testid="sku-input"
                    id="sku"
                    value={formData.sku}
                    onChange={(e) => handleChange('sku', e.target.value)}
                    required
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="product_name">Product Name *</Label>
                  <Input
                    data-testid="product-name-input"
                    id="product_name"
                    value={formData.product_name}
                    onChange={(e) => handleChange('product_name', e.target.value)}
                    required
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="quantity">Quantity *</Label>
                  <Input
                    data-testid="quantity-input"
                    id="quantity"
                    type="number"
                    min="1"
                    value={formData.quantity}
                    onChange={(e) => handleChange('quantity', e.target.value)}
                    required
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="price">Price (₹) *</Label>
                  <Input
                    data-testid="price-input"
                    id="price"
                    type="number"
                    min="0"
                    step="0.01"
                    value={formData.price}
                    onChange={(e) => handleChange('price', e.target.value)}
                    required
                  />
                </div>

                <div className="space-y-2 md:col-span-2">
                  <Label htmlFor="instructions">Instructions</Label>
                  <Input
                    data-testid="instructions-input"
                    id="instructions"
                    value={formData.instructions}
                    onChange={(e) => handleChange('instructions', e.target.value)}
                  />
                </div>
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-4">
              <Button
                type="button"
                variant="outline"
                onClick={() => navigate('/orders')}
                data-testid="cancel-button"
              >
                Cancel
              </Button>
              <Button type="submit" disabled={loading} data-testid="submit-order-button">
                {loading ? 'Creating...' : 'Create Order'}
              </Button>
            </div>
          </CardContent>
        </Card>
      </form>
    </div>
  );
};
