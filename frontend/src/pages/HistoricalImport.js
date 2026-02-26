import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../lib/api';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { toast } from 'sonner';
import { Upload, ArrowLeft, FileText } from 'lucide-react';

export const HistoricalImport = () => {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [importResult, setImportResult] = useState(null);
  const [showErrorModal, setShowErrorModal] = useState(false);
  const navigate = useNavigate();

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile && !selectedFile.name.endsWith('.csv')) {
      toast.error('Please select a CSV file');
      return;
    }
    setFile(selectedFile);
  };

  const handleImport = async () => {
    if (!file) {
      toast.error('Please select a file');
      return;
    }

    setUploading(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await api.post('/orders/import-historical', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      setImportResult(response.data);
      
      if (response.data.errors > 0) {
        setShowErrorModal(true);
      }

      toast.success(
        <div>
          <div className="font-bold">Import Completed!</div>
          <div>Imported: {response.data.imported}</div>
          <div>Skipped: {response.data.skipped}</div>
          {response.data.errors > 0 && <div>Errors: {response.data.errors}</div>}
        </div>
      );

      if (response.data.errors === 0) {
        setTimeout(() => navigate('/orders'), 2000);
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Import failed');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="ghost" onClick={() => navigate('/orders')}>
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back
        </Button>
        <div>
          <h1 className="text-3xl font-bold font-[Manrope] text-foreground tracking-tight">
            Import Historical Orders
          </h1>
          <p className="text-muted-foreground mt-1">
            Import old orders with complete historical data
          </p>
        </div>
      </div>

      <Card className="border-border/60">
        <CardHeader>
          <CardTitle className="font-[Manrope]">Upload Historical Data</CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="bg-muted/50 p-4 rounded-lg">
            <h3 className="font-medium mb-2">Required CSV Headers:</h3>
            <div className="text-sm text-muted-foreground space-y-1">
              <p>Order ID, Order Date, Dispatch By, Delivery By, Actual Dispatch Date</p>
              <p>Order Conf Calling, Assembly Type, Dispatch Confirmation Sent</p>
              <p>Did Not Pick Day 1-3, Confirmed on Day 1-3, Deliver Conf, Review Conf</p>
              <p>Delivery Date, Customer Name, Billing No., Shipping No.</p>
              <p>Place, State, Pincode, SKU, Qty, Tracking, Actual Shipping Company</p>
              <p>Instructions, Live Status, Price, Pickup Status</p>
              <p>Reason for Cancellation/Replacement</p>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">Upload CSV File</label>
            <div className="border-2 border-dashed border-border rounded-lg p-8 text-center hover:border-primary transition-colors">
              <input
                type="file"
                accept=".csv"
                onChange={handleFileChange}
                className="hidden"
                id="historical-file-upload"
              />
              <label htmlFor="historical-file-upload" className="cursor-pointer">
                <Upload className="w-12 h-12 mx-auto mb-4 text-muted-foreground" />
                {file ? (
                  <div>
                    <p className="text-sm font-medium">{file.name}</p>
                    <p className="text-xs text-muted-foreground mt-1">Click to change file</p>
                  </div>
                ) : (
                  <div>
                    <p className="text-sm font-medium">Click to upload CSV file</p>
                    <p className="text-xs text-muted-foreground mt-1">CSV file with historical order data</p>
                  </div>
                )}
              </label>
            </div>
          </div>

          <div className="flex gap-2">
            <Button
              variant="outline"
              onClick={() => navigate('/orders')}
              className="flex-1"
            >
              Cancel
            </Button>
            <Button
              onClick={handleImport}
              disabled={!file || uploading}
              className="flex-1"
            >
              {uploading ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary-foreground mr-2" />
                  Importing...
                </>
              ) : (
                <>
                  <FileText className="w-4 h-4 mr-2" />
                  Import Historical Orders
                </>
              )}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
