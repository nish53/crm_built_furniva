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
  BarChart3, AlertCircle, CheckCircle, Download, Layers, ShoppingCart, Truck
} from 'lucide-react';

export const InventoryIntelligence = () => {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [dashboard, setDashboard] = useState(null);
  const [stockSummary, setStockSummary] = useState(null);
  const [agingData, setAgingData] = useState(null);
  const [stockoutAlerts, setStockoutAlerts] = useState(null);
  const [demandForecast, setDemandForecast] = useState(null);
  const [purchaseSuggestions, setPurchaseSuggestions] = useState(null);
  const [returnAnalysis, setReturnAnalysis] = useState(null);
  const [liquidationSuggestions, setLiquidationSuggestions] = useState(null);
  const [smartAlerts, setSmartAlerts] = useState(null);
  const [purchaseOrders, setPurchaseOrders] = useState(null);
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

  const fetchDemandForecast = async () => {
    try {
      const res = await api.get('/inventory/demand-forecast?forecast_days=30');
      setDemandForecast(res.data);
    } catch (err) {
      toast.error('Failed to fetch demand forecast');
    }
  };

  const fetchPurchaseSuggestions = async () => {
    try {
      const res = await api.get('/inventory/purchase-suggestions?buffer_days=7');
      setPurchaseSuggestions(res.data);
    } catch (err) {
      toast.error('Failed to fetch purchase suggestions');
    }
  };

  const fetchReturnAnalysis = async () => {
    try {
      const res = await api.get('/inventory/return-analysis');
      setReturnAnalysis(res.data);
    } catch (err) {
      toast.error('Failed to fetch return analysis');
    }
  };

  const fetchLiquidationSuggestions = async () => {
    try {
      const res = await api.get('/inventory/liquidation-suggestions?min_age_days=90');
      setLiquidationSuggestions(res.data);
    } catch (err) {
      toast.error('Failed to fetch liquidation suggestions');
    }
  };

  const fetchSmartAlerts = async () => {
    try {
      const res = await api.get('/inventory/smart-alerts');
      setSmartAlerts(res.data);
    } catch (err) {
      toast.error('Failed to fetch smart alerts');
    }
  };

  const fetchPurchaseOrders = async () => {
    try {
      const res = await api.get('/inventory/purchase-orders');
      setPurchaseOrders(res.data);
    } catch (err) {
      toast.error('Failed to fetch purchase orders');
    }
  };

  const createPO = async (masterSku, quantity) => {
    try {
      const res = await api.post(`/inventory/auto-create-po?master_sku=${masterSku}&quantity=${quantity}`);
      toast.success(`PO ${res.data.po_number} created!`);
      fetchPurchaseOrders();
      fetchPurchaseSuggestions();
    } catch (err) {
      toast.error('Failed to create PO');
    }
  };

  const handleTabChange = (tab) => {
    setActiveTab(tab);
    if (tab === 'stock' && !stockSummary) fetchStockSummary();
    if (tab === 'aging' && !agingData) fetchAgingAnalysis();
    if (tab === 'alerts' && !stockoutAlerts) fetchStockoutAlerts();
    if (tab === 'forecast' && !demandForecast) fetchDemandForecast();
    if (tab === 'purchase' && !purchaseSuggestions) fetchPurchaseSuggestions();
    if (tab === 'returns' && !returnAnalysis) fetchReturnAnalysis();
    if (tab === 'liquidation' && !liquidationSuggestions) fetchLiquidationSuggestions();
    if (tab === 'smartalerts' && !smartAlerts) fetchSmartAlerts();
    if (tab === 'pos' && !purchaseOrders) fetchPurchaseOrders();
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
        <TabsList className="grid w-full grid-cols-5 lg:grid-cols-10">
          <TabsTrigger value="dashboard">Dashboard</TabsTrigger>
          <TabsTrigger value="stock">Stock</TabsTrigger>
          <TabsTrigger value="aging">Aging</TabsTrigger>
          <TabsTrigger value="alerts">Stockout</TabsTrigger>
          <TabsTrigger value="forecast">Forecast</TabsTrigger>
          <TabsTrigger value="purchase">Purchase</TabsTrigger>
          <TabsTrigger value="returns">Returns</TabsTrigger>
          <TabsTrigger value="liquidation">Liquidate</TabsTrigger>
          <TabsTrigger value="smartalerts">All Alerts</TabsTrigger>
          <TabsTrigger value="pos">POs</TabsTrigger>
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

        {/* Demand Forecast Tab */}
        <TabsContent value="forecast">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle className="flex items-center gap-2">
                <TrendingUp className="w-5 h-5" />
                Demand Forecast (30 Days)
              </CardTitle>
              <Button variant="outline" size="sm" onClick={fetchDemandForecast}>
                <RefreshCcw className="w-4 h-4 mr-2" />Refresh
              </Button>
            </CardHeader>
            <CardContent>
              {demandForecast ? (
                <div className="space-y-4">
                  {/* Season Info */}
                  <div className="grid grid-cols-3 gap-4 mb-6">
                    <div className="bg-purple-50 p-3 rounded-lg text-center border border-purple-200">
                      <p className="text-xs text-muted-foreground">Current Season</p>
                      <p className="text-lg font-bold text-purple-700">{demandForecast.season}</p>
                    </div>
                    <div className="bg-blue-50 p-3 rounded-lg text-center border border-blue-200">
                      <p className="text-xs text-muted-foreground">Seasonal Multiplier</p>
                      <p className="text-lg font-bold text-blue-700">{demandForecast.seasonal_multiplier}x</p>
                    </div>
                    <div className="bg-orange-50 p-3 rounded-lg text-center border border-orange-200">
                      <p className="text-xs text-muted-foreground">SKUs Needing Reorder</p>
                      <p className="text-lg font-bold text-orange-700">{demandForecast.skus_needing_reorder}</p>
                    </div>
                  </div>

                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead className="bg-secondary/30">
                        <tr>
                          <th className="text-left p-2">SKU</th>
                          <th className="text-left p-2">Product</th>
                          <th className="text-center p-2">30d Sales</th>
                          <th className="text-center p-2">Daily Avg</th>
                          <th className="text-center p-2">Forecast</th>
                          <th className="text-center p-2">Stock</th>
                          <th className="text-center p-2">Days Left</th>
                          <th className="text-center p-2">Reorder?</th>
                        </tr>
                      </thead>
                      <tbody>
                        {demandForecast.forecasts.map((item, idx) => (
                          <tr key={idx} className="border-b hover:bg-secondary/10">
                            <td className="p-2 font-mono text-xs">{item.master_sku}</td>
                            <td className="p-2">{item.product_name}</td>
                            <td className="p-2 text-center">{item.historical_sales.last_30_days}</td>
                            <td className="p-2 text-center">{item.daily_avg_adjusted}</td>
                            <td className="p-2 text-center font-bold">{item.forecast_qty}</td>
                            <td className="p-2 text-center">{item.current_stock}</td>
                            <td className="p-2 text-center">{item.days_to_stockout}</td>
                            <td className="p-2 text-center">
                              {item.reorder_needed ? (
                                <Badge className="bg-red-600">YES</Badge>
                              ) : (
                                <Badge className="bg-green-600">NO</Badge>
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              ) : (
                <div className="text-center py-8 text-muted-foreground">
                  Click Refresh to load demand forecast
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Purchase Suggestions Tab */}
        <TabsContent value="purchase">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle className="flex items-center gap-2">
                <ShoppingCart className="w-5 h-5" />
                Purchase Suggestions
              </CardTitle>
              <Button variant="outline" size="sm" onClick={fetchPurchaseSuggestions}>
                <RefreshCcw className="w-4 h-4 mr-2" />Refresh
              </Button>
            </CardHeader>
            <CardContent>
              {purchaseSuggestions ? (
                <div className="space-y-4">
                  {/* Summary */}
                  <div className="grid grid-cols-4 gap-4 mb-6">
                    <div className="bg-secondary/30 p-3 rounded-lg text-center">
                      <p className="text-xs text-muted-foreground">Total Suggestions</p>
                      <p className="text-xl font-bold">{purchaseSuggestions.total_suggestions}</p>
                    </div>
                    <div className="bg-red-50 p-3 rounded-lg text-center border border-red-200">
                      <p className="text-xs text-muted-foreground">Urgent</p>
                      <p className="text-xl font-bold text-red-700">{purchaseSuggestions.urgent_count}</p>
                    </div>
                    <div className="bg-green-50 p-3 rounded-lg text-center border border-green-200">
                      <p className="text-xs text-muted-foreground">Est. Total Cost</p>
                      <p className="text-xl font-bold text-green-700">₹{purchaseSuggestions.total_estimated_cost?.toLocaleString()}</p>
                    </div>
                    <div className="bg-blue-50 p-3 rounded-lg text-center border border-blue-200">
                      <p className="text-xs text-muted-foreground">Lead Time</p>
                      <p className="text-xl font-bold text-blue-700">{purchaseSuggestions.lead_time_assumed} days</p>
                    </div>
                  </div>

                  {purchaseSuggestions.suggestions.length > 0 ? (
                    <div className="space-y-3">
                      {purchaseSuggestions.suggestions.map((item, idx) => (
                        <div key={idx} className={`p-4 rounded-lg border ${
                          item.urgency.includes('URGENT') ? 'bg-red-50 border-red-200' :
                          item.urgency.includes('HIGH') ? 'bg-orange-50 border-orange-200' :
                          item.urgency.includes('MEDIUM') ? 'bg-yellow-50 border-yellow-200' :
                          'bg-blue-50 border-blue-200'
                        }`}>
                          <div className="flex items-start justify-between">
                            <div>
                              <div className="flex items-center gap-2 mb-1">
                                <span className="font-mono text-sm font-medium">{item.master_sku}</span>
                                <Badge className={
                                  item.urgency.includes('URGENT') ? 'bg-red-600' :
                                  item.urgency.includes('HIGH') ? 'bg-orange-600' :
                                  item.urgency.includes('MEDIUM') ? 'bg-yellow-600' :
                                  'bg-blue-600'
                                }>{item.urgency}</Badge>
                              </div>
                              <p className="text-sm">{item.product_name}</p>
                              <p className="text-xs text-muted-foreground mt-1">
                                Stock: {item.current_stock} | Daily Avg: {item.daily_avg_sales} | Stockout in: {item.days_to_stockout} days
                              </p>
                            </div>
                            <div className="text-right">
                              <p className="text-xs text-muted-foreground">Order Qty</p>
                              <p className="text-2xl font-bold text-green-600">{item.suggested_order_qty}</p>
                              <p className="text-sm text-muted-foreground">≈ ₹{item.estimated_cost?.toLocaleString()}</p>
                              <Button 
                                size="sm" 
                                className="mt-2"
                                onClick={() => createPO(item.master_sku, item.suggested_order_qty)}
                              >
                                Create PO
                              </Button>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-8">
                      <CheckCircle className="w-12 h-12 mx-auto mb-4 text-green-500" />
                      <p className="text-muted-foreground">No purchase suggestions needed. Stock levels are optimal!</p>
                    </div>
                  )}
                </div>
              ) : (
                <div className="text-center py-8 text-muted-foreground">
                  Click Refresh to load purchase suggestions
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Return Analysis Tab */}
        <TabsContent value="returns">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle className="flex items-center gap-2">
                <Truck className="w-5 h-5" />
                Return & Damage Analysis
              </CardTitle>
              <Button variant="outline" size="sm" onClick={fetchReturnAnalysis}>
                <RefreshCcw className="w-4 h-4 mr-2" />Refresh
              </Button>
            </CardHeader>
            <CardContent>
              {returnAnalysis ? (
                <div className="space-y-4">
                  {/* Summary */}
                  <div className="grid grid-cols-4 gap-4 mb-6">
                    <div className="bg-secondary/30 p-3 rounded-lg text-center">
                      <p className="text-xs text-muted-foreground">Total Orders</p>
                      <p className="text-xl font-bold">{returnAnalysis.total_orders}</p>
                    </div>
                    <div className="bg-orange-50 p-3 rounded-lg text-center border border-orange-200">
                      <p className="text-xs text-muted-foreground">Total Returns</p>
                      <p className="text-xl font-bold text-orange-700">{returnAnalysis.total_returns}</p>
                    </div>
                    <div className="bg-purple-50 p-3 rounded-lg text-center border border-purple-200">
                      <p className="text-xs text-muted-foreground">Return Rate</p>
                      <p className="text-xl font-bold text-purple-700">{returnAnalysis.overall_return_rate}%</p>
                    </div>
                    <div className="bg-red-50 p-3 rounded-lg text-center border border-red-200">
                      <p className="text-xs text-muted-foreground">Problem SKUs</p>
                      <p className="text-xl font-bold text-red-700">{returnAnalysis.problem_skus}</p>
                    </div>
                  </div>

                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead className="bg-secondary/30">
                        <tr>
                          <th className="text-left p-2">SKU</th>
                          <th className="text-left p-2">Product</th>
                          <th className="text-center p-2">Orders</th>
                          <th className="text-center p-2">Returns</th>
                          <th className="text-center p-2">Rate %</th>
                          <th className="text-left p-2">Top Reasons</th>
                          <th className="text-center p-2">Status</th>
                        </tr>
                      </thead>
                      <tbody>
                        {returnAnalysis.analysis.map((item, idx) => (
                          <tr key={idx} className="border-b hover:bg-secondary/10">
                            <td className="p-2 font-mono text-xs">{item.master_sku}</td>
                            <td className="p-2">{item.product_name}</td>
                            <td className="p-2 text-center">{item.total_orders}</td>
                            <td className="p-2 text-center text-orange-600">{item.total_returns}</td>
                            <td className="p-2 text-center font-bold">{item.return_rate_percent}%</td>
                            <td className="p-2 text-xs">
                              {item.top_return_reasons.map((r, i) => (
                                <span key={i} className="mr-2">{r.reason} ({r.count})</span>
                              ))}
                            </td>
                            <td className="p-2 text-center">
                              <Badge className={
                                item.status.includes('PROBLEM') ? 'bg-red-600' :
                                item.status.includes('WATCH') ? 'bg-yellow-600' :
                                'bg-green-600'
                              }>{item.status.replace(/[🔴🟡✅]/g, '').trim()}</Badge>
                            </td>
                          </tr>
                        ))}
                        {returnAnalysis.analysis.length === 0 && (
                          <tr><td colSpan="7" className="p-4 text-center text-muted-foreground">No return data</td></tr>
                        )}
                      </tbody>
                    </table>
                  </div>
                </div>
              ) : (
                <div className="text-center py-8 text-muted-foreground">
                  Click Refresh to load return analysis
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Liquidation Suggestions Tab */}
        <TabsContent value="liquidation">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle className="flex items-center gap-2">
                <AlertTriangle className="w-5 h-5 text-orange-500" />
                Liquidation Suggestions
              </CardTitle>
              <Button variant="outline" size="sm" onClick={fetchLiquidationSuggestions}>
                <RefreshCcw className="w-4 h-4 mr-2" />Refresh
              </Button>
            </CardHeader>
            <CardContent>
              {liquidationSuggestions ? (
                <div className="space-y-4">
                  <div className="grid grid-cols-4 gap-4 mb-6">
                    <div className="bg-secondary/30 p-3 rounded-lg text-center">
                      <p className="text-xs text-muted-foreground">Items to Liquidate</p>
                      <p className="text-xl font-bold">{liquidationSuggestions.total_items}</p>
                    </div>
                    <div className="bg-red-50 p-3 rounded-lg text-center border border-red-200">
                      <p className="text-xs text-muted-foreground">Critical</p>
                      <p className="text-xl font-bold text-red-700">{liquidationSuggestions.critical_count}</p>
                    </div>
                    <div className="bg-orange-50 p-3 rounded-lg text-center border border-orange-200">
                      <p className="text-xs text-muted-foreground">High Priority</p>
                      <p className="text-xl font-bold text-orange-700">{liquidationSuggestions.high_count}</p>
                    </div>
                    <div className="bg-purple-50 p-3 rounded-lg text-center border border-purple-200">
                      <p className="text-xs text-muted-foreground">Total Stock Value</p>
                      <p className="text-xl font-bold text-purple-700">₹{liquidationSuggestions.total_stock_value?.toLocaleString()}</p>
                    </div>
                  </div>

                  {liquidationSuggestions.suggestions.length > 0 ? (
                    <div className="space-y-3">
                      {liquidationSuggestions.suggestions.map((item, idx) => (
                        <div key={idx} className={`p-4 rounded-lg border ${
                          item.priority === 'CRITICAL' ? 'bg-red-50 border-red-200' :
                          item.priority === 'HIGH' ? 'bg-orange-50 border-orange-200' :
                          'bg-yellow-50 border-yellow-200'
                        }`}>
                          <div className="flex items-start justify-between">
                            <div>
                              <div className="flex items-center gap-2 mb-1">
                                <span className="font-mono text-sm font-medium">{item.master_sku}</span>
                                <Badge className={
                                  item.priority === 'CRITICAL' ? 'bg-red-600' :
                                  item.priority === 'HIGH' ? 'bg-orange-600' : 'bg-yellow-600'
                                }>{item.priority}</Badge>
                                <Badge variant="outline">{item.age_days} days old</Badge>
                              </div>
                              <p className="text-sm">{item.product_name}</p>
                              <p className="text-xs text-muted-foreground mt-1">{item.suggested_action}</p>
                            </div>
                            <div className="text-right">
                              <p className="text-xs text-muted-foreground">Stock: {item.current_stock}</p>
                              <p className="text-sm line-through text-muted-foreground">₹{item.current_price}</p>
                              <p className="text-lg font-bold text-green-600">₹{item.suggested_price}</p>
                              <p className="text-xs text-red-500">-{item.suggested_discount_percent}%</p>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-8">
                      <CheckCircle className="w-12 h-12 mx-auto mb-4 text-green-500" />
                      <p className="text-muted-foreground">No items need liquidation!</p>
                    </div>
                  )}
                </div>
              ) : (
                <div className="text-center py-8 text-muted-foreground">
                  Click Refresh to load liquidation suggestions
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Smart Alerts Tab */}
        <TabsContent value="smartalerts">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle className="flex items-center gap-2">
                <AlertCircle className="w-5 h-5 text-red-500" />
                All Smart Alerts
              </CardTitle>
              <Button variant="outline" size="sm" onClick={fetchSmartAlerts}>
                <RefreshCcw className="w-4 h-4 mr-2" />Refresh
              </Button>
            </CardHeader>
            <CardContent>
              {smartAlerts ? (
                <div className="space-y-4">
                  <div className="grid grid-cols-5 gap-4 mb-6">
                    <div className="bg-secondary/30 p-3 rounded-lg text-center">
                      <p className="text-xs text-muted-foreground">Total Alerts</p>
                      <p className="text-xl font-bold">{smartAlerts.total_alerts}</p>
                    </div>
                    <div className="bg-red-50 p-3 rounded-lg text-center border border-red-200">
                      <p className="text-xs text-muted-foreground">Critical</p>
                      <p className="text-xl font-bold text-red-700">{smartAlerts.critical}</p>
                    </div>
                    <div className="bg-orange-50 p-3 rounded-lg text-center border border-orange-200">
                      <p className="text-xs text-muted-foreground">High</p>
                      <p className="text-xl font-bold text-orange-700">{smartAlerts.high}</p>
                    </div>
                    <div className="bg-blue-50 p-3 rounded-lg text-center border border-blue-200">
                      <p className="text-xs text-muted-foreground">Stockout</p>
                      <p className="text-xl font-bold text-blue-700">{smartAlerts.by_type?.stockout || 0}</p>
                    </div>
                    <div className="bg-purple-50 p-3 rounded-lg text-center border border-purple-200">
                      <p className="text-xs text-muted-foreground">Dead Stock</p>
                      <p className="text-xl font-bold text-purple-700">{smartAlerts.by_type?.dead_stock || 0}</p>
                    </div>
                  </div>

                  {smartAlerts.alerts.length > 0 ? (
                    <div className="space-y-3">
                      {smartAlerts.alerts.map((alert, idx) => (
                        <div key={idx} className={`p-4 rounded-lg border ${
                          alert.priority.includes('CRITICAL') ? 'bg-red-50 border-red-200' :
                          alert.priority.includes('HIGH') ? 'bg-orange-50 border-orange-200' :
                          'bg-yellow-50 border-yellow-200'
                        }`}>
                          <div className="flex items-center justify-between">
                            <div>
                              <div className="flex items-center gap-2 mb-1">
                                <Badge className={
                                  alert.type === 'STOCKOUT' ? 'bg-blue-600' :
                                  alert.type === 'DEAD_STOCK' ? 'bg-purple-600' : 'bg-orange-600'
                                }>{alert.type.replace('_', ' ')}</Badge>
                                <span className="font-mono text-sm font-medium">{alert.master_sku}</span>
                                <Badge variant="outline">{alert.priority}</Badge>
                              </div>
                              <p className="text-sm">{alert.product_name}</p>
                              <p className="text-sm font-medium mt-1">{alert.message}</p>
                            </div>
                            <div className="text-right">
                              <p className="text-xs text-muted-foreground">{alert.action}</p>
                              {alert.current_stock !== undefined && (
                                <p className="text-sm">Stock: {alert.current_stock}</p>
                              )}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-8">
                      <CheckCircle className="w-12 h-12 mx-auto mb-4 text-green-500" />
                      <p className="text-muted-foreground">No alerts! Everything looks good.</p>
                    </div>
                  )}
                </div>
              ) : (
                <div className="text-center py-8 text-muted-foreground">
                  Click Refresh to load all alerts
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Purchase Orders Tab */}
        <TabsContent value="pos">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle className="flex items-center gap-2">
                <ShoppingCart className="w-5 h-5" />
                Purchase Orders
              </CardTitle>
              <Button variant="outline" size="sm" onClick={fetchPurchaseOrders}>
                <RefreshCcw className="w-4 h-4 mr-2" />Refresh
              </Button>
            </CardHeader>
            <CardContent>
              {purchaseOrders ? (
                <div className="space-y-4">
                  <p className="text-sm text-muted-foreground">Total POs: {purchaseOrders.total}</p>
                  
                  {purchaseOrders.items.length > 0 ? (
                    <div className="overflow-x-auto">
                      <table className="w-full text-sm">
                        <thead className="bg-secondary/30">
                          <tr>
                            <th className="text-left p-2">PO Number</th>
                            <th className="text-left p-2">SKU</th>
                            <th className="text-left p-2">Product</th>
                            <th className="text-center p-2">Qty</th>
                            <th className="text-center p-2">Total Cost</th>
                            <th className="text-center p-2">Status</th>
                            <th className="text-left p-2">Supplier</th>
                            <th className="text-left p-2">Created</th>
                          </tr>
                        </thead>
                        <tbody>
                          {purchaseOrders.items.map((po, idx) => (
                            <tr key={idx} className="border-b hover:bg-secondary/10">
                              <td className="p-2 font-mono text-xs">{po.po_number}</td>
                              <td className="p-2 font-mono text-xs">{po.master_sku}</td>
                              <td className="p-2">{po.product_name}</td>
                              <td className="p-2 text-center font-bold">{po.quantity}</td>
                              <td className="p-2 text-center">₹{po.total_cost?.toLocaleString()}</td>
                              <td className="p-2 text-center">
                                <Badge className={
                                  po.status === 'received' ? 'bg-green-600' :
                                  po.status === 'shipped' ? 'bg-blue-600' :
                                  po.status === 'confirmed' ? 'bg-purple-600' :
                                  po.status === 'cancelled' ? 'bg-red-600' :
                                  'bg-yellow-600'
                                }>{po.status}</Badge>
                              </td>
                              <td className="p-2">{po.supplier_name}</td>
                              <td className="p-2 text-xs">{po.created_at?.split('T')[0]}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  ) : (
                    <div className="text-center py-8 text-muted-foreground">
                      No purchase orders yet. Create one from the Purchase tab.
                    </div>
                  )}
                </div>
              ) : (
                <div className="text-center py-8 text-muted-foreground">
                  Click Refresh to load purchase orders
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
