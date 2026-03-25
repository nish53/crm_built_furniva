import React, { useState, useEffect } from 'react';
import api from '../lib/api';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { toast } from 'sonner';
import { Settings as SettingsIcon, Save, RotateCcw, AlertCircle } from 'lucide-react';

export const Settings = () => {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [config, setConfig] = useState({
    pfc_loss_percentage: 0,
    resolved_cost_percentage: 15,
    default_outbound_logistics: 100,
    default_return_logistics: 100,
    refunded_includes_product_cost_if_damage: true,
    fraud_includes_product_and_logistics: true
  });
  const [isDefault, setIsDefault] = useState(true);

  const defaultConfig = {
    pfc_loss_percentage: 0,
    resolved_cost_percentage: 15,
    default_outbound_logistics: 100,
    default_return_logistics: 100,
    refunded_includes_product_cost_if_damage: true,
    fraud_includes_product_and_logistics: true
  };

  useEffect(() => {
    fetchConfig();
  }, []);

  const fetchConfig = async () => {
    try {
      const res = await api.get('/loss/config');
      setConfig(res.data);
      checkIfDefault(res.data);
    } catch (err) {
      toast.error('Failed to load configuration');
    } finally {
      setLoading(false);
    }
  };

  const checkIfDefault = (cfg) => {
    const isDefaultVal = 
      cfg.pfc_loss_percentage === defaultConfig.pfc_loss_percentage &&
      cfg.resolved_cost_percentage === defaultConfig.resolved_cost_percentage &&
      cfg.default_outbound_logistics === defaultConfig.default_outbound_logistics &&
      cfg.default_return_logistics === defaultConfig.default_return_logistics;
    setIsDefault(isDefaultVal);
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await api.patch('/loss/config', {
        pfc_loss_percentage: parseFloat(config.pfc_loss_percentage) || 0,
        resolved_cost_percentage: parseFloat(config.resolved_cost_percentage) || 15,
        default_outbound_logistics: parseFloat(config.default_outbound_logistics) || 100,
        default_return_logistics: parseFloat(config.default_return_logistics) || 100,
        refunded_includes_product_cost_if_damage: config.refunded_includes_product_cost_if_damage,
        fraud_includes_product_and_logistics: config.fraud_includes_product_and_logistics
      });
      toast.success('Configuration saved successfully');
      checkIfDefault(config);
    } catch (err) {
      toast.error('Failed to save configuration');
    } finally {
      setSaving(false);
    }
  };

  const handleReset = async () => {
    setSaving(true);
    try {
      await api.patch('/loss/config', defaultConfig);
      setConfig({ ...defaultConfig });
      setIsDefault(true);
      toast.success('Configuration reset to defaults');
    } catch (err) {
      toast.error('Failed to reset configuration');
    } finally {
      setSaving(false);
    }
  };

  const handleChange = (field, value) => {
    const newConfig = { ...config, [field]: value };
    setConfig(newConfig);
    checkIfDefault(newConfig);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-[60vh]">
        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-primary" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold font-[Manrope] tracking-tight">Settings</h1>
          <p className="text-muted-foreground mt-1">Configure system parameters</p>
        </div>
        {isDefault && (
          <div className="flex items-center gap-2 text-sm text-muted-foreground bg-muted px-3 py-1.5 rounded-full">
            <AlertCircle className="w-4 h-4" />
            Using default values
          </div>
        )}
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="font-[Manrope] flex items-center gap-2">
            <SettingsIcon className="w-5 h-5" />
            Loss Calculation Configuration
          </CardTitle>
          <CardDescription>
            Configure how loss amounts are calculated for different return categories
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Percentage Settings */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="text-sm font-medium text-foreground">PFC Loss Percentage (%)</label>
              <p className="text-xs text-muted-foreground mb-2">Loss percentage for Pre-Fulfillment Cancellations</p>
              <Input
                type="number"
                step="0.1"
                min="0"
                max="100"
                value={config.pfc_loss_percentage}
                onChange={(e) => handleChange('pfc_loss_percentage', e.target.value)}
                className="font-[JetBrains_Mono]"
              />
            </div>
            <div>
              <label className="text-sm font-medium text-foreground">Resolved Cost Percentage (%)</label>
              <p className="text-xs text-muted-foreground mb-2">Cost percentage for resolved issues (replacements, repairs)</p>
              <Input
                type="number"
                step="0.1"
                min="0"
                max="100"
                value={config.resolved_cost_percentage}
                onChange={(e) => handleChange('resolved_cost_percentage', e.target.value)}
                className="font-[JetBrains_Mono]"
              />
            </div>
          </div>

          {/* Logistics Costs */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="text-sm font-medium text-foreground">Default Outbound Logistics (₹)</label>
              <p className="text-xs text-muted-foreground mb-2">Default shipping cost to customer</p>
              <Input
                type="number"
                step="1"
                min="0"
                value={config.default_outbound_logistics}
                onChange={(e) => handleChange('default_outbound_logistics', e.target.value)}
                className="font-[JetBrains_Mono]"
              />
            </div>
            <div>
              <label className="text-sm font-medium text-foreground">Default Return Logistics (₹)</label>
              <p className="text-xs text-muted-foreground mb-2">Default return shipping cost</p>
              <Input
                type="number"
                step="1"
                min="0"
                value={config.default_return_logistics}
                onChange={(e) => handleChange('default_return_logistics', e.target.value)}
                className="font-[JetBrains_Mono]"
              />
            </div>
          </div>

          {/* Boolean Settings */}
          <div className="space-y-4 border-t pt-4">
            <h4 className="text-sm font-medium text-foreground">Calculation Rules</h4>
            <label className="flex items-center gap-3 cursor-pointer">
              <input
                type="checkbox"
                checked={config.refunded_includes_product_cost_if_damage}
                onChange={(e) => handleChange('refunded_includes_product_cost_if_damage', e.target.checked)}
                className="rounded border-input w-4 h-4"
              />
              <div>
                <p className="text-sm font-medium">Include product cost in refunds for damage-related returns</p>
                <p className="text-xs text-muted-foreground">Adds product cost to loss calculation when damage is involved</p>
              </div>
            </label>
            <label className="flex items-center gap-3 cursor-pointer">
              <input
                type="checkbox"
                checked={config.fraud_includes_product_and_logistics}
                onChange={(e) => handleChange('fraud_includes_product_and_logistics', e.target.checked)}
                className="rounded border-input w-4 h-4"
              />
              <div>
                <p className="text-sm font-medium">Fraud includes product cost and both logistics</p>
                <p className="text-xs text-muted-foreground">Full loss calculation for fraud cases</p>
              </div>
            </label>
          </div>

          {/* Category Explanations */}
          <div className="bg-muted/50 p-4 rounded-lg border">
            <h4 className="text-sm font-medium mb-3">Loss Category Formulas</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
              <div className="bg-background p-3 rounded border">
                <span className="font-medium text-yellow-700">PFC:</span>
                <p className="text-muted-foreground text-xs mt-1">Price × PFC Loss %</p>
              </div>
              <div className="bg-background p-3 rounded border">
                <span className="font-medium text-blue-700">Resolved:</span>
                <p className="text-muted-foreground text-xs mt-1">Price × Resolved Cost % + Replacement Parts</p>
              </div>
              <div className="bg-background p-3 rounded border">
                <span className="font-medium text-orange-700">Refunded:</span>
                <p className="text-muted-foreground text-xs mt-1">Outbound + Return Logistics (+ Product if damage)</p>
              </div>
              <div className="bg-background p-3 rounded border">
                <span className="font-medium text-red-700">Fraud:</span>
                <p className="text-muted-foreground text-xs mt-1">Product Cost + Outbound + Return Logistics</p>
              </div>
            </div>
          </div>

          {/* Actions */}
          <div className="flex gap-3 pt-4 border-t">
            <Button onClick={handleSave} disabled={saving} className="flex-1">
              <Save className="w-4 h-4 mr-2" />
              {saving ? 'Saving...' : 'Save Configuration'}
            </Button>
            <Button variant="outline" onClick={handleReset} disabled={saving}>
              <RotateCcw className="w-4 h-4 mr-2" />
              Reset to Defaults
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
