import React, { useState, useEffect } from 'react';
import api from '../lib/api';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { toast } from 'sonner';
import { Upload, FileText, ArrowRight, Save, Download } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export const ImportWizard = () => {
  const [step, setStep] = useState(1);
  const [file, setFile] = useState(null);
  const [channel, setChannel] = useState('');
  const [channels, setChannels] = useState([]);
  const [delimiter, setDelimiter] = useState(',');
  const [hasHeader, setHasHeader] = useState(true);
  const [previewData, setPreviewData] = useState(null);
  const [columnMappings, setColumnMappings] = useState({});
  const [availableFields, setAvailableFields] = useState({ required_fields: [], optional_fields: [] });
  const [templates, setTemplates] = useState([]);
  const [selectedTemplate, setSelectedTemplate] = useState('');
  const [importing, setImporting] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    fetchChannels();
    fetchAvailableFields();
    fetchTemplates();
  }, []);

  const fetchChannels = async () => {
    try {
      const response = await api.get('/channels/');
      setChannels(response.data);
    } catch (error) {
      console.error('Failed to fetch channels:', error);
    }
  };

  const fetchAvailableFields = async () => {
    try {
      const response = await api.get('/import/available-fields');
      setAvailableFields(response.data);
    } catch (error) {
      toast.error('Failed to load field options');
    }
  };

  const fetchTemplates = async () => {
    try {
      const response = await api.get('/import/templates');
      setTemplates(response.data);
    } catch (error) {
      console.error('Failed to fetch templates:', error);
    }
  };

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      setFile(selectedFile);
      // Auto-detect delimiter from filename
      if (selectedFile.name.endsWith('.txt')) {
        setDelimiter('\t');
      }
    }
  };

  const handlePreviewFile = async () => {
    if (!file || !channel) {
      toast.error('Please select a file and channel');
      return;
    }

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await api.post(
        `/import/preview-file?delimiter=${encodeURIComponent(delimiter)}&has_header=${hasHeader}`,
        formData,
        { headers: { 'Content-Type': 'multipart/form-data' } }
      );
      setPreviewData(response.data);
      
      // Initialize mappings with empty values
      const initialMappings = {};
      response.data.columns.forEach(col => {
        initialMappings[col] = '';
      });
      setColumnMappings(initialMappings);
      
      setStep(2);
      toast.success('File preview loaded successfully');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to preview file');
    }
  };

  const handleMappingChange = (csvColumn, systemField) => {
    setColumnMappings(prev => ({
      ...prev,
      [csvColumn]: systemField
    }));
  };

  const applyTemplate = (template) => {
    if (template) {
      setColumnMappings(template.column_mappings);
      setDelimiter(template.delimiter || ',');
      setHasHeader(template.has_header);
      toast.success('Template applied');
    }
  };

  const handleSaveTemplate = async () => {
    const templateName = prompt('Enter template name:');
    if (!templateName) return;

    try {
      await api.post('/import/templates', {
        name: templateName,
        channel: channel,
        description: `Template for ${channel} imports`,
        column_mappings: columnMappings,
        delimiter: delimiter,
        has_header: hasHeader,
        is_default: false
      });
      toast.success('Template saved successfully');
      fetchTemplates();
    } catch (error) {
      toast.error('Failed to save template');
    }
  };

  const handleContinueToImport = () => {
    // Check if at least required fields are mapped
    const mappedFields = Object.values(columnMappings).filter(v => v);
    if (mappedFields.length === 0) {
      toast.error('Please map at least one column');
      return;
    }
    setStep(3);
  };

  const handleImport = async () => {
    setImporting(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      // Ensure delimiter is properly encoded as single character
      const delimiterChar = delimiter === '\t' ? '%09' : encodeURIComponent(delimiter);
      
      const response = await api.post(
        `/import/with-mapping?channel=${channel}&column_mappings=${encodeURIComponent(JSON.stringify(columnMappings))}&delimiter=${delimiterChar}&has_header=${hasHeader}&auto_lookup_master_sku=true`,
        formData,
        { headers: { 'Content-Type': 'multipart/form-data' } }
      );
      
      toast.success(
        <div>
          <div className="font-bold">Import Completed!</div>
          <div>Imported: {response.data.imported}</div>
          <div>Skipped: {response.data.skipped}</div>
          {response.data.errors > 0 && <div>Errors: {response.data.errors}</div>}
        </div>
      );
      
      // Reset and go back to orders
      setTimeout(() => navigate('/orders'), 2000);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Import failed');
    } finally {
      setImporting(false);
    }
  };

  const allFields = [
    ...availableFields.required_fields,
    ...availableFields.optional_fields
  ];

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold font-[Manrope] text-foreground">Import Orders</h1>
          <p className="text-muted-foreground mt-1">Import orders from CSV or TXT files with custom column mapping</p>
        </div>
        <Button variant="outline" onClick={() => navigate('/orders')}>
          Back to Orders
        </Button>
      </div>

      {/* Progress Steps */}
      <div className="flex items-center justify-center space-x-4">
        <div className={`flex items-center space-x-2 ${step >= 1 ? 'text-primary' : 'text-muted-foreground'}`}>
          <div className={`w-8 h-8 rounded-full flex items-center justify-center ${step >= 1 ? 'bg-primary text-primary-foreground' : 'bg-muted'}`}>
            1
          </div>
          <span className="font-medium">Upload File</span>
        </div>
        <ArrowRight className="w-5 h-5 text-muted-foreground" />
        <div className={`flex items-center space-x-2 ${step >= 2 ? 'text-primary' : 'text-muted-foreground'}`}>
          <div className={`w-8 h-8 rounded-full flex items-center justify-center ${step >= 2 ? 'bg-primary text-primary-foreground' : 'bg-muted'}`}>
            2
          </div>
          <span className="font-medium">Map Columns</span>
        </div>
        <ArrowRight className="w-5 h-5 text-muted-foreground" />
        <div className={`flex items-center space-x-2 ${step >= 3 ? 'text-primary' : 'text-muted-foreground'}`}>
          <div className={`w-8 h-8 rounded-full flex items-center justify-center ${step >= 3 ? 'bg-primary text-primary-foreground' : 'bg-muted'}`}>
            3
          </div>
          <span className="font-medium">Import</span>
        </div>
      </div>

      {step === 1 && (
        <Card>
          <CardHeader>
            <CardTitle className="font-[Manrope]">Step 1: Upload File & Select Channel</CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <div>
              <label className="block text-sm font-medium mb-2">Select Channel</label>
              <Select value={channel} onValueChange={setChannel}>
                <SelectTrigger>
                  <SelectValue placeholder="Choose import channel" />
                </SelectTrigger>
                <SelectContent>
                  {channels.map(ch => (
                    <SelectItem key={ch.id} value={ch.name}>{ch.display_name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Upload File</label>
              <div className="border-2 border-dashed border-border rounded-lg p-8 text-center hover:border-primary transition-colors">
                <input
                  type="file"
                  accept=".csv,.txt"
                  onChange={handleFileChange}
                  className="hidden"
                  id="file-upload"
                />
                <label htmlFor="file-upload" className="cursor-pointer">
                  <Upload className="w-12 h-12 mx-auto mb-4 text-muted-foreground" />
                  {file ? (
                    <div>
                      <p className="text-sm font-medium">{file.name}</p>
                      <p className="text-xs text-muted-foreground mt-1">Click to change file</p>
                    </div>
                  ) : (
                    <div>
                      <p className="text-sm font-medium">Click to upload or drag and drop</p>
                      <p className="text-xs text-muted-foreground mt-1">CSV or TXT files supported</p>
                    </div>
                  )}
                </label>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-2">Delimiter</label>
                <Select value={delimiter} onValueChange={setDelimiter}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value=",">,  (Comma)</SelectItem>
                    <SelectItem value="\t">Tab</SelectItem>
                    <SelectItem value="|">|  (Pipe)</SelectItem>
                    <SelectItem value=";">; (Semicolon)</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="flex items-center space-x-2 pt-8">
                <input
                  type="checkbox"
                  id="has-header"
                  checked={hasHeader}
                  onChange={(e) => setHasHeader(e.target.checked)}
                  className="rounded border-border"
                />
                <label htmlFor="has-header" className="text-sm font-medium">
                  File has header row
                </label>
              </div>
            </div>

            <Button onClick={handlePreviewFile} className="w-full" disabled={!file || !channel}>
              <FileText className="w-4 h-4 mr-2" />
              Preview & Continue
            </Button>
          </CardContent>
        </Card>
      )}

      {step === 2 && previewData && (
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <div className="flex justify-between items-center">
                <CardTitle className="font-[Manrope]">Step 2: Map Columns to System Fields</CardTitle>
                <div className="space-x-2">
                  {templates.length > 0 && (
                    <Select value={selectedTemplate} onValueChange={(val) => {
                      setSelectedTemplate(val);
                      const template = templates.find(t => t.id === val);
                      if (template) applyTemplate(template);
                    }}>
                      <SelectTrigger className="w-[200px]">
                        <SelectValue placeholder="Load Template" />
                      </SelectTrigger>
                      <SelectContent>
                        {templates.filter(t => t.channel === channel).map(template => (
                          <SelectItem key={template.id} value={template.id}>{template.name}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  )}
                  <Button variant="outline" size="sm" onClick={handleSaveTemplate}>
                    <Save className="w-4 h-4 mr-2" />
                    Save as Template
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="text-sm text-muted-foreground">
                  <p>Total Rows: {previewData.total_rows}</p>
                  <p className="mt-1">Map each column from your file to a system field (or leave empty to ignore)</p>
                </div>

                <div className="space-y-3 max-h-[500px] overflow-y-auto">
                  {previewData.columns.map((column, idx) => (
                    <div key={idx} className="grid grid-cols-3 gap-4 items-start p-4 border border-border rounded-lg">
                      <div>
                        <p className="text-sm font-medium mb-1">{column}</p>
                        <p className="text-xs text-muted-foreground">
                          Sample: {previewData.preview_data[0]?.[idx] || 'N/A'}
                        </p>
                      </div>
                      <div className="col-span-2">
                        <Select
                          value={columnMappings[column] || '__skip__'}
                          onValueChange={(value) => handleMappingChange(column, value === '__skip__' ? '' : value)}
                        >
                          <SelectTrigger>
                            <SelectValue placeholder="Select system field" />
                          </SelectTrigger>
                          <SelectContent className="max-h-[400px]">
                            <SelectItem value="__skip__">-- Ignore Column --</SelectItem>
                            {availableFields.required_fields.map(field => (
                              <SelectItem key={field.field} value={field.field}>
                                ⭐ {field.field} - {field.description}
                              </SelectItem>
                            ))}
                            {availableFields.optional_fields.map(field => (
                              <SelectItem key={field.field} value={field.field}>
                                {field.field} - {field.description}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                    </div>
                  ))}
                </div>

                <div className="flex space-x-4">
                  <Button variant="outline" onClick={() => setStep(1)}>
                    Back
                  </Button>
                  <Button onClick={handleContinueToImport} className="flex-1">
                    Continue to Import
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {step === 3 && (
        <Card>
          <CardHeader>
            <CardTitle className="font-[Manrope]">Step 3: Review & Import</CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-muted-foreground">File:</span>
                  <p className="font-medium">{file?.name}</p>
                </div>
                <div>
                  <span className="text-muted-foreground">Channel:</span>
                  <p className="font-medium">{channel}</p>
                </div>
                <div>
                  <span className="text-muted-foreground">Total Rows:</span>
                  <p className="font-medium">{previewData?.total_rows}</p>
                </div>
                <div>
                  <span className="text-muted-foreground">Mapped Columns:</span>
                  <p className="font-medium">
                    {Object.values(columnMappings).filter(v => v).length} / {previewData?.columns.length}
                  </p>
                </div>
              </div>

              <div className="p-4 bg-muted rounded-lg">
                <p className="text-sm font-medium mb-2">Column Mappings:</p>
                <div className="space-y-1 text-xs">
                  {Object.entries(columnMappings).filter(([_, v]) => v).map(([csvCol, sysField]) => (
                    <div key={csvCol}>
                      <span className="text-muted-foreground">{csvCol}</span> → <span className="font-medium">{sysField}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="flex space-x-4">
                <Button variant="outline" onClick={() => setStep(2)}>
                  Back
                </Button>
                <Button onClick={handleImport} className="flex-1" disabled={importing}>
                  {importing ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary-foreground mr-2" />
                      Importing...
                    </>
                  ) : (
                    <>
                      <Download className="w-4 h-4 mr-2" />
                      Start Import
                    </>
                  )}
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};
