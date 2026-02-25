import React, { useEffect, useState } from 'react';
import api from '../lib/api';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { toast } from 'sonner';
import { Archive, Plus, AlertTriangle, Package, TrendingDown } from 'lucide-react';

export const Inventory = () => {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({
    sku: '',
    name: '',
    description: '',
    category: '',
    weight: 0,
    dimensions: { length: 0, width: 0, height: 0 },
    num_boxes: 1,
    stock_quantity: 0,
    reorder_level: 10,
    price: 0,
    cost: 0,
  });

  useEffect(() => {
    fetchProducts();
  }, []);

  const fetchProducts = async () => {
    try {
      const response = await api.get('/products/');
      setProducts(response.data);
    } catch (error) {
      toast.error('Failed to fetch products');
    } finally {
      setLoading(false);
    }
  };

  const createProduct = async (e) => {
    e.preventDefault();
    try {
      await api.post('/products', formData);
      toast.success('Product created');
      setShowForm(false);
      setFormData({
        sku: '', name: '', description: '', category: '', weight: 0,
        dimensions: { length: 0, width: 0, height: 0 }, num_boxes: 1,
        stock_quantity: 0, reorder_level: 10, price: 0, cost: 0
      });
      fetchProducts();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create product');
    }
  };

  const lowStockProducts = products.filter(p => p.stock_quantity <= p.reorder_level);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="inventory-page">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold font-[Manrope] text-foreground tracking-tight">
            Inventory Management
          </h1>
          <p className="text-muted-foreground mt-1">
            Track stock levels and product details
          </p>
        </div>
        <Button onClick={() => setShowForm(!showForm)} data-testid="add-product-button">
          <Plus className="w-4 h-4 mr-2" />
          Add Product
        </Button>
      </div>

      {lowStockProducts.length > 0 && (
        <Card className="border-destructive/50 bg-destructive/5">
          <CardHeader>
            <CardTitle className="font-[Manrope] flex items-center gap-2 text-destructive">
              <AlertTriangle className="w-5 h-5" />
              Low Stock Alert
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {lowStockProducts.map((product) => (
                <div key={product.id} className="flex items-center justify-between p-2 bg-background rounded">
                  <span className="text-sm font-medium">{product.name} ({product.sku})</span>
                  <Badge variant="destructive">{product.stock_quantity} units</Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {showForm && (
        <Card className="border-border/60">
          <CardHeader>
            <CardTitle className="font-[Manrope]">Add New Product</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={createProduct} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="sku">SKU *</Label>
                  <Input
                    id="sku"
                    value={formData.sku}
                    onChange={(e) => setFormData({ ...formData, sku: e.target.value })}
                    required
                  />
                </div>
                <div className="space-y-2 md:col-span-2">
                  <Label htmlFor="name">Product Name *</Label>
                  <Input
                    id="name"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="category">Category</Label>
                  <Input
                    id="category"
                    value={formData.category}
                    onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="weight">Weight (kg)</Label>
                  <Input
                    id="weight"
                    type="number"
                    step="0.1"
                    value={formData.weight}
                    onChange={(e) => setFormData({ ...formData, weight: parseFloat(e.target.value) })}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="num_boxes">Number of Boxes</Label>
                  <Input
                    id="num_boxes"
                    type="number"
                    value={formData.num_boxes}
                    onChange={(e) => setFormData({ ...formData, num_boxes: parseInt(e.target.value) })}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="stock">Stock Quantity *</Label>
                  <Input
                    id="stock"
                    type="number"
                    value={formData.stock_quantity}
                    onChange={(e) => setFormData({ ...formData, stock_quantity: parseInt(e.target.value) })}
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="reorder">Reorder Level</Label>
                  <Input
                    id="reorder"
                    type="number"
                    value={formData.reorder_level}
                    onChange={(e) => setFormData({ ...formData, reorder_level: parseInt(e.target.value) })}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="price">Price (₹) *</Label>
                  <Input
                    id="price"
                    type="number"
                    step="0.01"
                    value={formData.price}
                    onChange={(e) => setFormData({ ...formData, price: parseFloat(e.target.value) })}
                    required
                  />
                </div>
              </div>
              <div className="flex justify-end gap-2">
                <Button type="button" variant="outline" onClick={() => setShowForm(false)}>
                  Cancel
                </Button>
                <Button type="submit">Create Product</Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      <Card className="border-border/60">
        <CardHeader>
          <CardTitle className="font-[Manrope]">Products ({products.length})</CardTitle>
        </CardHeader>
        <CardContent>
          {products.length === 0 ? (
            <div className="text-center py-12">
              <Package className="w-12 h-12 text-muted-foreground mx-auto mb-4 opacity-50" />
              <p className="text-muted-foreground">No products yet</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-border">
                    <th className="text-left py-3 px-4 text-xs font-bold text-muted-foreground uppercase">SKU</th>
                    <th className="text-left py-3 px-4 text-xs font-bold text-muted-foreground uppercase">Product</th>
                    <th className="text-left py-3 px-4 text-xs font-bold text-muted-foreground uppercase">Category</th>
                    <th className="text-right py-3 px-4 text-xs font-bold text-muted-foreground uppercase">Stock</th>
                    <th className="text-right py-3 px-4 text-xs font-bold text-muted-foreground uppercase">Weight</th>
                    <th className="text-right py-3 px-4 text-xs font-bold text-muted-foreground uppercase">Price</th>
                    <th className="text-right py-3 px-4 text-xs font-bold text-muted-foreground uppercase">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {products.map((product) => (
                    <tr key={product.id} className="border-b border-border/40 hover:bg-secondary/30">
                      <td className="py-4 px-4">
                        <span className="font-[JetBrains_Mono] text-sm">{product.sku}</span>
                      </td>
                      <td className="py-4 px-4">
                        <div>
                          <p className="font-medium text-sm">{product.name}</p>
                          {product.description && (
                            <p className="text-xs text-muted-foreground line-clamp-1">{product.description}</p>
                          )}
                        </div>
                      </td>
                      <td className="py-4 px-4 text-sm">{product.category || '-'}</td>
                      <td className="py-4 px-4 text-right">
                        <span className={`font-medium ${
                          product.stock_quantity <= product.reorder_level ? 'text-destructive' : ''
                        }`}>
                          {product.stock_quantity}
                        </span>
                      </td>
                      <td className="py-4 px-4 text-right text-sm">{product.weight} kg</td>
                      <td className="py-4 px-4 text-right font-medium">₹{product.price.toLocaleString()}</td>
                      <td className="py-4 px-4 text-right">
                        {product.stock_quantity <= product.reorder_level ? (
                          <Badge variant="destructive" className="flex items-center gap-1 w-fit ml-auto">
                            <TrendingDown className="w-3 h-3" />
                            Low Stock
                          </Badge>
                        ) : (
                          <Badge className="bg-primary/20 text-primary">In Stock</Badge>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};
