import React, { useEffect, useState, useRef } from 'react';
import api from '../lib/api';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { toast } from 'sonner';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import {
  Package, AlertTriangle, Clock, TrendingUp, Upload, RefreshCcw,
  BarChart3, AlertCircle, CheckCircle, Download, Layers
} from 'lucide-react';

export const InventoryIntelligence = () => {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [dashboard, setDashboard] = useState(null);
  const [stockSummary, setStockSummary] = useState(null);
  const [agingData, setAgingData] = useState(null);
  const [stockoutAlerts, setStockoutAlerts] = useState(null);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef(null);

  useEffect(() => {
    fetchDashboard();
  }, []);

  const fetchDashboard = async () => {
    try {
      const res = await api.get('/inventory/dashboard');
      setDashboard(res.data);
    } catch (err) {
      toast.error('Failed to fetch dashboard');
    } finally {
      setLoading(false);
    }
  };

  const fetchStockSummary = async () => {
    try {
      const res = await api.get('/inventory/stock-summary');
      setStockSummary(res.data);
    } catch (err) {
      toast.error('Failed to fetch stock summary');
    }
  };

  const fetchAgingAnalysis = async () => {
    try {
      const res = await api.get('/inventory/aging-analysis');
      setAgingData(res.data);
    } catch (err) {
      toast.error('Failed to fetch aging analysis');
    }
  };

  const fetchStockoutAlerts = async () => {
    try {
      const res = await api.get('/inventory/stockout-alerts?threshold_days=7');
      setStockoutAlerts(res.data);
    } catch (err) {
      toast.error('Failed to fetch stockout alerts');
    }
  };

  const handleTabChange = (tab) => {
    setActiveTab(tab);
    if (tab === 'stock' && !stockSummary) fetchStockSummary();
    if (tab === 'aging' && !agingData) fetchAgingAnalysis();
    if (tab === 'alerts' && !stockoutAlerts) fetchStockoutAlerts();
  };

  const handleFileUpload = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setUploading(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await api.post('/inventory/bulk-import-csv?mode=merge', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      toast.success(`Imported ${res.data.imported} SKUs, Updated ${res.data.updated}, Skipped ${res.data.skipped}`);
      fetchDashboard();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Import failed');
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const downloadTemplate = async () => {
    try {
      const res = await api.get('/inventory/csv-template');
      const csv = res.data.columns.join(',') + '\n' + Object.values(res.data.example_row).join(',');
      const blob = new Blob([csv], { type: 'text/csv' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'sku_import_template.csv';
      a.click();
    } catch {
      toast.error('Failed to download template');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-[60vh]">
        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-primary" />
      </div>
    );
  }

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold font-[Manrope]">Inventory Intelligence</h1>
          <p className="text-muted-foreground mt-1">Stock analysis, aging, alerts & bulk import</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={downloadTemplate}>
            <Download className="w-4 h-4 mr-2" />
            CSV Template
          </Button>
          <input
            ref={fileInputRef}
            type="file"
            accept=".csv"
            className="hidden"
            onChange={handleFileUpload}
          />
          <Button onClick={() => fileInputRef.current?.click()} disabled={uploading}>
            <Upload className="w-4 h-4 mr-2" />
            {uploading ? 'Uploading...' : 'Import CSV'}
          </Button>
        </div>
      </div>

      {/* Dashboard Summary Cards */}
      {dashboard && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Total SKUs</p>
                  <p className="text-2xl font-bold">{dashboard.total_skus}</p>
                </div>
                <Package className="w-8 h-8 text-blue-500" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Categories</p>
                  <p className="text-2xl font-bold">{dashboard.category_count}</p>
                </div>
                <Layers className="w-8 h-8 text-purple-500" />
              </div>
            </CardContent>
          </Card>

          <Card className="border-yellow-200">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Stale Stock</p>
                  <p className="text-2xl font-bold text-yellow-600">{dashboard.aging?.stale_stock || 0}</p>
                </div>
                <Clock className="w-8 h-8 text-yellow-500" />
              </div>
            </CardContent>
          </Card>

          <Card className="border-red-200">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Dead Stock</p>
                  <p className="text-2xl font-bold text-red-600">{dashboard.aging?.dead_stock || 0}</p>
                </div>
                <AlertTriangle className="w-8 h-8 text-red-500" />
              </div>
            </CardContent>
          </Card>

          <Card className="border-orange-200">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Stockout Alerts</p>
                  <p className="text-2xl font-bold text-orange-600">{dashboard.stockout_alerts}</p>
                </div>
                <AlertCircle className="w-8 h-8 text-orange-500" />
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={handleTabChange}>
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="dashboard">Dashboard</TabsTrigger>
          <TabsTrigger value="stock">Stock Buckets</TabsTrigger>
          <TabsTrigger value="aging">Aging Analysis</TabsTrigger>
          <TabsTrigger value="alerts">Stockout Alerts</TabsTrigger>
        </TabsList>

        {/* Dashboard Tab */}
        <TabsContent value="dashboard">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BarChart3 className="w-5 h-5" />
                Inventory Overview
              </CardTitle>
            </CardHeader>
            <CardContent>
              {dashboard && (
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="bg-secondary/30 p-4 rounded-lg">
                      <p className="text-sm text-muted-foreground">Total Procurement Value</p>
                      <p className="text-2xl font-bold">₹{dashboard.total_procurement_value?.toLocaleString() || 0}</p>
                    </div>
                    <div className="bg-secondary/30 p-4 rounded-lg">
                      <p className="text-sm text-muted-foreground">Items Needing Attention</p>
                      <p className="text-2xl font-bold text-amber-600">{dashboard.aging?.attention_needed || 0}</p>
                    </div>
                  </div>
                  
                  <div>
                    <p className="text-sm font-medium mb-2">Categories</p>
                    <div className="flex flex-wrap gap-2">
                      {dashboard.categories?.map((cat, idx) => (
                        <Badge key={idx} variant="outline">{cat}</Badge>
                      ))}
                      {(!dashboard.categories || dashboard.categories.length === 0) && (
                        <span className="text-muted-foreground text-sm">No categories defined</span>
                      )}
                    </div>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Stock Buckets Tab */}
        <TabsContent value="stock">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle className="flex items-center gap-2">
                <Package className="w-5 h-5" />
                Real-Time Stock Buckets
              </CardTitle>
              <Button variant="outline" size="sm" onClick={fetchStockSummary}>
                <RefreshCcw className="w-4 h-4 mr-2" />Refresh
              </Button>
            </CardHeader>
            <CardContent>
              {stockSummary ? (
                <div className="space-y-4">
                  {/* Summary */}
                  <div className="grid grid-cols-4 gap-4 mb-6">
                    <div className="bg-blue-50 p-3 rounded-lg text-center">
                      <p className="text-xs text-muted-foreground">Total SKUs</p>
                      <p className="text-xl font-bold text-blue-700">{stockSummary.summary.total_skus}</p>
                    </div>
                    <div className="bg-green-50 p-3 rounded-lg text-center">
                      <p className="text-xs text-muted-foreground">Total Available</p>
                      <p className="text-xl font-bold text-green-700">{stockSummary.summary.total_available}</p>
                    </div>
                    <div className="bg-yellow-50 p-3 rounded-lg text-center">
                      <p className="text-xs text-muted-foreground">Total Reserved</p>
                      <p className="text-xl font-bold text-yellow-700">{stockSummary.summary.total_reserved}</p>
                    </div>
                    <div className="bg-red-50 p-3 rounded-lg text-center">
                      <p className="text-xs text-muted-foreground">Total Damaged</p>
                      <p className="text-xl font-bold text-red-700">{stockSummary.summary.total_damaged}</p>
                    </div>
                  </div>

                  {/* Per-SKU breakdown */}
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead className="bg-secondary/30">
                        <tr>
                          <th className="text-left p-2">SKU</th>
                          <th className="text-left p-2">Product</th>
                          <th className="text-center p-2">Procured</th>
                          <th className="text-center p-2">Reserved</th>
                          <th className="text-center p-2">In Transit</th>
                          <th className="text-center p-2">Sold</th>
                          <th className="text-center p-2">Available</th>
                          <th className="text-center p-2">Damaged</th>
                        </tr>
                      </thead>
                      <tbody>
                        {stockSummary.stock_by_sku.map((item, idx) => (
                          <tr key={idx} className="border-b hover:bg-secondary/10">
                            <td className="p-2 font-mono text-xs">{item.master_sku}</td>
                            <td className="p-2">{item.product_name}</td>
                            <td className="p-2 text-center">{item.buckets.total_procured}</td>
                            <td className="p-2 text-center text-yellow-600">{item.buckets.reserved}</td>
                            <td className="p-2 text-center text-blue-600">{item.buckets.in_transit}</td>
                            <td className="p-2 text-center text-purple-600">{item.buckets.sold}</td>
                            <td className="p-2 text-center font-bold text-green-600">{item.sellable}</td>
                            <td className="p-2 text-center text-red-600">{item.buckets.damaged_blocked}</td>
                          </tr>
                        ))}
                        {stockSummary.stock_by_sku.length === 0 && (
                          <tr><td colSpan="8" className="p-4 text-center text-muted-foreground">No inventory data</td></tr>
                        )}
                      </tbody>
                    </table>
                  </div>
                </div>
              ) : (
                <div className="text-center py-8 text-muted-foreground">
                  Click Refresh to load stock data
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Aging Analysis Tab */}
        <TabsContent value="aging">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle className="flex items-center gap-2">
                <Clock className="w-5 h-5" />
                Inventory Aging Analysis
              </CardTitle>
              <Button variant="outline" size="sm" onClick={fetchAgingAnalysis}>
                <RefreshCcw className="w-4 h-4 mr-2" />Refresh
              </Button>
            </CardHeader>
            <CardContent>
              {agingData ? (
                <div className="space-y-4">
                  {/* Aging Buckets Summary */}
                  <div className="grid grid-cols-5 gap-3 mb-6">
                    <div className="bg-green-50 p-3 rounded-lg text-center border border-green-200">
                      <p className="text-xs text-muted-foreground">0-30 Days</p>
                      <p className="text-xl font-bold text-green-700">{agingData.summary.fast_moving}</p>
                      <p className="text-xs text-green-600">Fast Moving</p>
                    </div>
                    <div className="bg-blue-50 p-3 rounded-lg text-center border border-blue-200">
                      <p className="text-xs text-muted-foreground">31-60 Days</p>
                      <p className="text-xl font-bold text-blue-700">{agingData.summary.normal}</p>
                      <p className="text-xs text-blue-600">Normal</p>
                    </div>
                    <div className="bg-yellow-50 p-3 rounded-lg text-center border border-yellow-200">
                      <p className="text-xs text-muted-foreground">61-90 Days</p>
                      <p className="text-xl font-bold text-yellow-700">{agingData.summary.slow}</p>
                      <p className="text-xs text-yellow-600">Slow Moving</p>
                    </div>
                    <div className="bg-orange-50 p-3 rounded-lg text-center border border-orange-200">
                      <p className="text-xs text-muted-foreground">91-180 Days</p>
                      <p className="text-xl font-bold text-orange-700">{agingData.summary.stale}</p>
                      <p className="text-xs text-orange-600">Stale</p>
                    </div>
                    <div className="bg-red-50 p-3 rounded-lg text-center border border-red-200">
                      <p className="text-xs text-muted-foreground">180+ Days</p>
                      <p className="text-xl font-bold text-red-700">{agingData.summary.dead_stock}</p>
                      <p className="text-xs text-red-600">Dead Stock</p>
                    </div>
                  </div>

                  {/* Per-SKU aging */}
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead className="bg-secondary/30">
                        <tr>
                          <th className="text-left p-2">SKU</th>
                          <th className="text-left p-2">Product</th>
                          <th className="text-center p-2">Days Since Sale</th>
                          <th className="text-center p-2">Sales (30d)</th>
                          <th className="text-left p-2">Status</th>
                          <th className="text-left p-2">Suggested Action</th>
                        </tr>
                      </thead>
                      <tbody>
                        {agingData.aging_by_sku.map((item, idx) => (
                          <tr key={idx} className="border-b hover:bg-secondary/10">
                            <td className="p-2 font-mono text-xs">{item.master_sku}</td>
                            <td className="p-2">{item.product_name}</td>
                            <td className="p-2 text-center font-bold">{item.days_since_last_sale}</td>
                            <td className="p-2 text-center">{item.sales_last_30_days}</td>
                            <td className="p-2">
                              <Badge className={
                                item.bucket === 'fast_0_30' ? 'bg-green-100 text-green-800' :
                                item.bucket === 'normal_31_60' ? 'bg-blue-100 text-blue-800' :
                                item.bucket === 'slow_61_90' ? 'bg-yellow-100 text-yellow-800' :
                                item.bucket === 'stale_91_180' ? 'bg-orange-100 text-orange-800' :
                                'bg-red-100 text-red-800'
                              }>
                                {item.bucket.replace(/_/g, ' ').replace(/\d+/g, '').trim()}
                              </Badge>
                            </td>
                            <td className="p-2 text-xs">{item.suggested_action}</td>
                          </tr>
                        ))}
                        {agingData.aging_by_sku.length === 0 && (
                          <tr><td colSpan="6" className="p-4 text-center text-muted-foreground">No aging data</td></tr>
                        )}
                      </tbody>
                    </table>
                  </div>
                </div>
              ) : (
                <div className="text-center py-8 text-muted-foreground">
                  Click Refresh to load aging analysis
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Stockout Alerts Tab */}
        <TabsContent value="alerts">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle className="flex items-center gap-2">
                <AlertCircle className="w-5 h-5 text-red-500" />
                Stockout Alerts (7-Day Threshold)
              </CardTitle>
              <Button variant="outline" size="sm" onClick={fetchStockoutAlerts}>
                <RefreshCcw className="w-4 h-4 mr-2" />Refresh
              </Button>
            </CardHeader>
            <CardContent>
              {stockoutAlerts ? (
                <div className="space-y-4">
                  {/* Alert Summary */}
                  <div className="grid grid-cols-4 gap-4 mb-6">
                    <div className="bg-secondary/30 p-3 rounded-lg text-center">
                      <p className="text-xs text-muted-foreground">Total Alerts</p>
                      <p className="text-xl font-bold">{stockoutAlerts.total_alerts}</p>
                    </div>
                    <div className="bg-red-50 p-3 rounded-lg text-center border border-red-200">
                      <p className="text-xs text-muted-foreground">Critical</p>
                      <p className="text-xl font-bold text-red-700">{stockoutAlerts.critical}</p>
                    </div>
                    <div className="bg-orange-50 p-3 rounded-lg text-center border border-orange-200">
                      <p className="text-xs text-muted-foreground">High</p>
                      <p className="text-xl font-bold text-orange-700">{stockoutAlerts.high}</p>
                    </div>
                    <div className="bg-yellow-50 p-3 rounded-lg text-center border border-yellow-200">
                      <p className="text-xs text-muted-foreground">Medium</p>
                      <p className="text-xl font-bold text-yellow-700">{stockoutAlerts.medium}</p>
                    </div>
                  </div>

                  {/* Alerts List */}
                  {stockoutAlerts.alerts.length > 0 ? (
                    <div className="space-y-3">
                      {stockoutAlerts.alerts.map((alert, idx) => (
                        <div key={idx} className={`p-4 rounded-lg border ${
                          alert.priority.includes('CRITICAL') ? 'bg-red-50 border-red-200' :
                          alert.priority.includes('HIGH') ? 'bg-orange-50 border-orange-200' :
                          'bg-yellow-50 border-yellow-200'
                        }`}>
                          <div className="flex items-start justify-between">
                            <div>
                              <div className="flex items-center gap-2 mb-1">
                                <span className="font-mono text-sm font-medium">{alert.master_sku}</span>
                                <Badge className={
                                  alert.priority.includes('CRITICAL') ? 'bg-red-600' :
                                  alert.priority.includes('HIGH') ? 'bg-orange-600' :
                                  'bg-yellow-600'
                                }>{alert.priority}</Badge>
                              </div>
                              <p className="text-sm">{alert.product_name}</p>
                              <p className="text-sm mt-2 font-medium">{alert.message}</p>
                            </div>
                            <div className="text-right">
                              <p className="text-xs text-muted-foreground">Current Stock</p>
                              <p className="text-lg font-bold">{alert.current_stock}</p>
                              <p className="text-xs text-muted-foreground mt-2">Suggested Reorder</p>
                              <p className="text-lg font-bold text-green-600">+{alert.suggested_reorder_qty}</p>
                            </div>
                          </div>
                          <div className="mt-2 text-xs text-muted-foreground">
                            Avg Daily Sales: {alert.avg_daily_sales} | Days to Stockout: {alert.days_to_stockout}
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-8">
                      <CheckCircle className="w-12 h-12 mx-auto mb-4 text-green-500" />
                      <p className="text-muted-foreground">No stockout alerts! All inventory levels are healthy.</p>
                    </div>
                  )}
                </div>
              ) : (
                <div className="text-center py-8 text-muted-foreground">
                  Click Refresh to check stockout alerts
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default InventoryIntelligence;
