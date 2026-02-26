import React, { useEffect, useState } from 'react';
import api from '../lib/api';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { toast } from 'sonner';
import { DollarSign, TrendingUp, TrendingDown, AlertTriangle, BarChart3 } from 'lucide-react';

export const Costing = () => {
  const [profitAnalysis, setProfitAnalysis] = useState(null);
  const [leakages, setLeakages] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => { fetchData(); }, []);

  const fetchData = async () => {
    try {
      const [profitRes, leakageRes] = await Promise.all([
        api.get('/financials/profit-analysis').catch(() => ({ data: null })),
        api.get('/financials/leakage-report').catch(() => ({ data: [] }))
      ]);
      setProfitAnalysis(profitRes.data);
      setLeakages(Array.isArray(leakageRes.data) ? leakageRes.data : []);
    } catch {
      toast.error('Failed to fetch financial data');
    } finally {
      setLoading(false);
    }
  };

  if (loading) return (
    <div className="flex items-center justify-center h-[60vh]">
      <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-primary" />
    </div>
  );

  const pa = profitAnalysis || {};

  return (
    <div className="space-y-6" data-testid="costing-page">
      <div>
        <h1 className="text-3xl font-bold font-[Manrope]">Financial Control</h1>
        <p className="text-muted-foreground mt-1">Profit analysis, cost tracking & leakage detection</p>
      </div>

      {/* Summary KPIs */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <KPICard
          icon={DollarSign}
          label="Total Revenue"
          value={pa.total_revenue ? `₹${pa.total_revenue.toLocaleString()}` : '₹0'}
          sub={`${pa.total_orders || 0} orders`}
        />
        <KPICard
          icon={TrendingUp}
          label="Net Revenue"
          value={pa.total_net_revenue ? `₹${pa.total_net_revenue.toLocaleString()}` : '₹0'}
          sub="After deductions"
        />
        <KPICard
          icon={TrendingDown}
          label="Total Costs"
          value={pa.total_cost ? `₹${pa.total_cost.toLocaleString()}` : '₹0'}
          sub="All costs combined"
          warn
        />
        <KPICard
          icon={BarChart3}
          label="Gross Profit"
          value={pa.total_profit ? `₹${pa.total_profit.toLocaleString()}` : '₹0'}
          sub={pa.avg_margin ? `${pa.avg_margin.toFixed(1)}% avg margin` : '-'}
          highlight={pa.total_profit > 0}
          warn={pa.total_profit < 0}
        />
      </div>

      {/* Help Text */}
      {!pa.total_orders && (
        <Card>
          <CardContent className="py-8 text-center">
            <DollarSign className="w-12 h-12 mx-auto mb-4 text-muted-foreground" />
            <h3 className="text-lg font-semibold font-[Manrope] mb-2">No Financial Data Yet</h3>
            <p className="text-muted-foreground text-sm max-w-md mx-auto">
              Go to any order's detail page and click "Calculate Financials" to start tracking per-order profitability.
              The aggregated data will appear here.
            </p>
          </CardContent>
        </Card>
      )}

      {/* Leakage Report */}
      {leakages.length > 0 && (
        <Card data-testid="leakage-card">
          <CardHeader>
            <CardTitle className="font-[Manrope] flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-orange-500" />
              Leakage Report
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {leakages.map((l, i) => (
                <div key={i} className="flex items-center justify-between p-3 bg-orange-50 rounded-lg border border-orange-100">
                  <div>
                    <p className="text-sm font-medium font-[JetBrains_Mono]">{l.order_number || 'Unknown'}</p>
                    <div className="flex gap-4 mt-1">
                      {l.settlement_variance && (
                        <span className="text-xs text-muted-foreground">
                          Settlement gap: <span className="font-medium text-red-600">₹{Math.abs(l.settlement_variance)}</span>
                        </span>
                      )}
                      {l.refund_leakage > 0 && (
                        <span className="text-xs text-muted-foreground">
                          Refund leak: <span className="font-medium text-red-600">₹{l.refund_leakage}</span>
                        </span>
                      )}
                      {l.claim_leakage > 0 && (
                        <span className="text-xs text-muted-foreground">
                          Claim leak: <span className="font-medium text-red-600">₹{l.claim_leakage}</span>
                        </span>
                      )}
                    </div>
                  </div>
                  <Badge className="bg-red-100 text-red-800">Leakage</Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* How It Works */}
      <Card>
        <CardHeader>
          <CardTitle className="font-[Manrope]">How Costing Works</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid md:grid-cols-3 gap-6 text-sm">
            <div>
              <h4 className="font-semibold mb-2">1. Per-Order Calculation</h4>
              <p className="text-muted-foreground">
                Open any order detail page and click "Calculate Financials". Enter product cost, shipping, packaging, and installation costs.
              </p>
            </div>
            <div>
              <h4 className="font-semibold mb-2">2. Auto Deductions</h4>
              <p className="text-muted-foreground">
                The system automatically calculates marketplace commission, TCS/TDS (1%), and payment gateway fees (2%) from the selling price.
              </p>
            </div>
            <div>
              <h4 className="font-semibold mb-2">3. Profit & Leakage</h4>
              <p className="text-muted-foreground">
                View gross profit, contribution margin, and identify settlement variances or refund/claim leakages across all orders.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

const KPICard = ({ icon: Icon, label, value, sub, highlight, warn }) => (
  <Card data-testid={`kpi-${label.toLowerCase().replace(/\s/g, '-')}`}>
    <CardContent className="p-5">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs text-muted-foreground uppercase tracking-wide">{label}</p>
          <p className={`text-xl font-bold font-[JetBrains_Mono] mt-1 ${highlight ? 'text-green-700' : ''} ${warn ? 'text-red-600' : ''}`}>
            {value}
          </p>
          {sub && <p className="text-xs text-muted-foreground mt-1">{sub}</p>}
        </div>
        <div className={`p-2 rounded-lg ${highlight ? 'bg-green-100' : warn ? 'bg-red-100' : 'bg-secondary'}`}>
          <Icon className={`w-4 h-4 ${highlight ? 'text-green-700' : warn ? 'text-red-600' : 'text-muted-foreground'}`} />
        </div>
      </div>
    </CardContent>
  </Card>
);
