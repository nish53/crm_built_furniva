import React, { useEffect, useState } from 'react';
import api from '../lib/api';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { toast } from 'sonner';
import { Settings as SettingsIcon, Save, RotateCcw, DollarSign } from 'lucide-react';

export const Settings = () => {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [config, setConfig] = useState({});
  const [isDefault, setIsDefault] = useState(true);

  useEffect(() => {
    fetchConfig();
  }, []);

  const fetchConfig = async () => {
    try {
      const res = await api.get('/financials/loss/config');
      setConfig(res.data.config);
      setIsDefault(res.data.is_default);
    } catch (error) {
      toast.error('Failed to fetch configuration');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      const params = new URLSearchParams();
      Object.keys(config).forEach(key => {
        if (config[key] !== undefined && config[key] !== null) {
          params.append(key, config[key]);
        }
      });
      
      const res = await api.patch(`/financials/loss/config?${params.toString()}`);
      setConfig(res.data.config);
      setIsDefault(false);
      toast.success('Configuration saved successfully');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to save configuration');
    } finally {
      setSaving(false);
    }
  };

  const handleReset = () => {
    if (confirm('Reset to default values?')) {
      setConfig({
        resolved_cost_percentage: 15.0,
        default_outbound_logistics: 150.0,
        default_return_logistics: 120.0,
        refund_processing_fee: 50.0,
        qc_inspection_cost: 30.0,
        restocking_fee_percentage: 10.0,
        fraud_investigation_cost: 500.0,
      });
      toast.info('Values reset to defaults (not saved yet)');
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
    <div className="space-y-6 max-w-4xl">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold font-[Manrope] flex items-center gap-3">
            <SettingsIcon className="w-8 h-8" />
            Settings
          </h1>
          <p className="text-muted-foreground mt-1">Configure system variables and calculations</p>
        </div>
        {isDefault && (
          <div className="bg-yellow-50 text-yellow-800 px-3 py-1.5 rounded-md text-sm border border-yellow-200">
            Using default values
          </div>
        )}
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="font-[Manrope] flex items-center gap-2">
            <DollarSign className="w-5 h-5" />
            Loss Calculation Configuration
          </CardTitle>
          <CardDescription>
            Configure variables used for calculating losses on returns, cancellations, and refunds
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSave} className="space-y-6">
            <div className="grid grid-cols-2 gap-6">
              {/* Resolved Cost Percentage */}
              <div>
                <label className="text-sm font-medium">Resolved Cost Percentage (%)</label>
                <p className="text-xs text-muted-foreground mb-2">
                  % of product cost for replacement parts on resolved returns
                </p>
                <div className="flex items-center gap-2">
                  <Input
                    type="number"
                    step="0.01"
                    value={config.resolved_cost_percentage || ''}
                    onChange={e => setConfig({ ...config, resolved_cost_percentage: parseFloat(e.target.value) })}
                    placeholder="15.0"
                  />
                  <span className="text-sm text-muted-foreground">%</span>
                </div>
              </div>

              {/* Default Outbound Logistics */}
              <div>
                <label className="text-sm font-medium">Default Outbound Logistics (₹)</label>
                <p className="text-xs text-muted-foreground mb-2">
                  Default shipping cost to customer
                </p>
                <div className="flex items-center gap-2">
                  <span className="text-sm">₹</span>
                  <Input
                    type="number"
                    step="0.01"
                    value={config.default_outbound_logistics || ''}
                    onChange={e => setConfig({ ...config, default_outbound_logistics: parseFloat(e.target.value) })}
                    placeholder="150.0"
                  />
                </div>
              </div>

              {/* Default Return Logistics */}
              <div>
                <label className="text-sm font-medium">Default Return Logistics (₹)</label>
                <p className="text-xs text-muted-foreground mb-2">
                  Default return shipping cost from customer
                </p>
                <div className="flex items-center gap-2">
                  <span className="text-sm">₹</span>
                  <Input
                    type="number"
                    step="0.01"
                    value={config.default_return_logistics || ''}
                    onChange={e => setConfig({ ...config, default_return_logistics: parseFloat(e.target.value) })}
                    placeholder="120.0"
                  />
                </div>
              </div>

              {/* Refund Processing Fee */}
              <div>
                <label className="text-sm font-medium">Refund Processing Fee (₹)</label>
                <p className="text-xs text-muted-foreground mb-2">
                  Processing fee per refund transaction
                </p>
                <div className="flex items-center gap-2">
                  <span className="text-sm">₹</span>
                  <Input
                    type="number"
                    step="0.01"
                    value={config.refund_processing_fee || ''}
                    onChange={e => setConfig({ ...config, refund_processing_fee: parseFloat(e.target.value) })}
                    placeholder="50.0"
                  />
                </div>
              </div>

              {/* QC Inspection Cost */}
              <div>
                <label className="text-sm font-medium">QC Inspection Cost (₹)</label>
                <p className="text-xs text-muted-foreground mb-2">
                  Quality control inspection cost per return
                </p>
                <div className="flex items-center gap-2">
                  <span className="text-sm">₹</span>
                  <Input
                    type="number"
                    step="0.01"
                    value={config.qc_inspection_cost || ''}
                    onChange={e => setConfig({ ...config, qc_inspection_cost: parseFloat(e.target.value) })}
                    placeholder="30.0"
                  />
                </div>
              </div>

              {/* Restocking Fee Percentage */}
              <div>
                <label className="text-sm font-medium">Restocking Fee Percentage (%)</label>
                <p className="text-xs text-muted-foreground mb-2">
                  % fee for restocking refurbished items
                </p>
                <div className="flex items-center gap-2">
                  <Input
                    type="number"
                    step="0.01"
                    value={config.restocking_fee_percentage || ''}
                    onChange={e => setConfig({ ...config, restocking_fee_percentage: parseFloat(e.target.value) })}
                    placeholder="10.0"
                  />
                  <span className="text-sm text-muted-foreground">%</span>
                </div>
              </div>

              {/* Fraud Investigation Cost */}
              <div className="col-span-2">
                <label className="text-sm font-medium">Fraud Investigation Cost (₹)</label>
                <p className="text-xs text-muted-foreground mb-2">
                  Cost to investigate and handle fraud cases
                </p>
                <div className="flex items-center gap-2">
                  <span className="text-sm">₹</span>
                  <Input
                    type="number"
                    step="0.01"
                    value={config.fraud_investigation_cost || ''}
                    onChange={e => setConfig({ ...config, fraud_investigation_cost: parseFloat(e.target.value) })}
                    placeholder="500.0"
                  />
                </div>
              </div>
            </div>

            <div className="flex gap-3 pt-4 border-t">
              <Button type="button" variant="outline" onClick={handleReset} disabled={saving}>
                <RotateCcw className="w-4 h-4 mr-2" />
                Reset to Defaults
              </Button>
              <Button type="submit" disabled={saving} className="ml-auto">
                <Save className="w-4 h-4 mr-2" />
                {saving ? 'Saving...' : 'Save Configuration'}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      {/* Usage Information */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">How Loss Calculation Works</CardTitle>
        </CardHeader>
        <CardContent className="text-sm space-y-3">
          <div>
            <p className="font-medium">Automatic Calculation:</p>
            <p className="text-muted-foreground">
              When a return/cancellation occurs, the system automatically calculates total loss using these configured values.
            </p>
          </div>
          <div>
            <p className="font-medium">Loss Components:</p>
            <ul className="list-disc list-inside text-muted-foreground space-y-1 ml-2">
              <li>Outbound + Return Logistics</li>
              <li>Product Cost (if non-recoverable)</li>
              <li>Replacement Parts Cost (for resolved returns)</li>
              <li>QC Inspection + Processing Fees</li>
              <li>Additional costs based on category (fraud investigation, etc.)</li>
            </ul>
          </div>
          <div>
            <p className="font-medium">Manual Override:</p>
            <p className="text-muted-foreground">
              You can manually override calculated values in the Order Detail page's Loss Calculation card.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
