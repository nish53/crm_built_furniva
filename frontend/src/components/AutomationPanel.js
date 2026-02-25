import React, { useState, useEffect } from 'react';
import api from '../lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { toast } from 'sonner';
import { Zap, MessageSquare, CheckCircle, Clock, AlertCircle } from 'lucide-react';
import { format } from 'date-fns';

export const AutomationPanel = ({ orderId }) => {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [triggering, setTriggering] = useState(false);

  useEffect(() => {
    fetchLogs();
  }, [orderId]);

  const fetchLogs = async () => {
    try {
      const response = await api.get(`/automation/logs/${orderId}`);
      setLogs(response.data);
    } catch (error) {
      console.error('Failed to fetch automation logs');
    } finally {
      setLoading(false);
    }
  };

  const triggerAutomation = async (type) => {
    setTriggering(true);
    try {
      await api.post(`/automation/trigger/${orderId}`, null, {
        params: { automation_type: type },
      });
      toast.success(`${type} automation triggered`);
      setTimeout(fetchLogs, 2000);
    } catch (error) {
      toast.error('Failed to trigger automation');
    } finally {
      setTriggering(false);
    }
  };

  const automationTypes = [
    { value: 'order_confirmation', label: 'Order Confirmation', icon: CheckCircle },
    { value: 'dispatch_call', label: 'Dispatch Call Reminder', icon: MessageSquare },
    { value: 'dispatch_notification', label: 'Dispatch Notification', icon: Zap },
    { value: 'installation_inquiry', label: 'Installation Inquiry', icon: MessageSquare },
    { value: 'delivery_confirmation', label: 'Delivery Confirmation', icon: CheckCircle },
    { value: 'review_request', label: 'Review Request', icon: MessageSquare },
  ];

  return (
    <div className="space-y-4" data-testid="automation-panel">
      <Card className="border-border/60">
        <CardHeader>
          <CardTitle className="font-[Manrope] flex items-center gap-2">
            <Zap className="w-5 h-5 text-primary" />
            Quick Automations
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {automationTypes.map((auto) => {
              const Icon = auto.icon;
              return (
                <Button
                  key={auto.value}
                  variant="outline"
                  size="sm"
                  onClick={() => triggerAutomation(auto.value)}
                  disabled={triggering}
                  className="justify-start"
                  data-testid={`trigger-${auto.value}`}
                >
                  <Icon className="w-4 h-4 mr-2" />
                  {auto.label}
                </Button>
              );
            })}
          </div>
        </CardContent>
      </Card>

      <Card className="border-border/60">
        <CardHeader>
          <CardTitle className="font-[Manrope]">Automation History</CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="text-center py-4 text-muted-foreground">Loading...</div>
          ) : logs.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              <Clock className="w-8 h-8 mx-auto mb-2 opacity-50" />
              <p>No automations triggered yet</p>
            </div>
          ) : (
            <div className="space-y-3">
              {logs.map((log, idx) => (
                <div
                  key={log.id || idx}
                  className="flex items-start gap-3 p-3 border border-border/40 rounded-lg"
                  data-testid={`automation-log-${idx}`}
                >
                  <div className={`mt-1 ${
                    log.status === 'sent' ? 'text-primary' : 'text-destructive'
                  }`}>
                    {log.status === 'sent' ? (
                      <CheckCircle className="w-5 h-5" />
                    ) : (
                      <AlertCircle className="w-5 h-5" />
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between mb-1">
                      <p className="text-sm font-medium">
                        {log.automation_type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                      </p>
                      <Badge variant={log.status === 'sent' ? 'default' : 'destructive'} className="text-xs">
                        {log.status}
                      </Badge>
                    </div>
                    {log.message && (
                      <p className="text-xs text-muted-foreground line-clamp-2">{log.message}</p>
                    )}
                    <p className="text-xs text-muted-foreground mt-1">
                      {format(new Date(log.created_at), 'MMM dd, yyyy HH:mm')}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};
