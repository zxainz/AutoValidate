import axios from 'axios';
import { Finding, DashboardMetrics, ReportSummary, SettingsConfig } from '../types';

const client = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

export const api = {
  // Metrics
  getMetrics: async (): Promise<DashboardMetrics> => {
    const res = await client.get('/metrics');
    return res.data;
  },

  // Findings
  getFindings: async (params?: {
    status?: string;
    severity?: string;
    scan_source?: string;
    search?: string;
    limit?: number;
    offset?: number;
  }): Promise<Finding[]> => {
    const res = await client.get('/findings', { params });
    return res.data;
  },

  getFinding: async (id: number): Promise<Finding> => {
    const res = await client.get(`/findings/${id}`);
    return res.data;
  },

  uploadScannerFile: async (file: File, scannerType: string = 'auto') => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('scanner_type', scannerType);
    const res = await client.post('/findings/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return res.data;
  },

  clearAllFindings: async () => {
    const res = await client.delete('/findings');
    return res.data;
  },

  deleteFinding: async (id: number) => {
    const res = await client.delete(`/findings/${id}`);
    return res.data;
  },

  // Validation
  startValidation: async (findingIds: number[] = [], options?: any) => {
    const res = await client.post('/validation/start', {
      finding_ids: findingIds,
      options: options || {},
    });
    return res.data;
  },

  validateSingleFinding: async (findingId: number, envType: string = 'Production Web/API') => {
    const res = await client.post(`/validation/single/${findingId}`, null, {
      params: { environment_type: envType },
    });
    return res.data;
  },

  getJobStatus: async (jobId: number) => {
    const res = await client.get(`/validation/jobs/${jobId}`);
    return res.data;
  },

  // Reports
  generateReport: async (title: string = 'Pentest Validation Report'): Promise<ReportSummary> => {
    const res = await client.post('/reports/generate', null, { params: { title } });
    return res.data;
  },

  listReports: async (): Promise<ReportSummary[]> => {
    const res = await client.get('/reports');
    return res.data;
  },

  getExportUrl: (reportId: number, format: 'html' | 'pdf' | 'csv' | 'json') => {
    return `/api/reports/${reportId}/export?format=${format}`;
  },

  // Settings & AI Health
  getSettings: async (): Promise<SettingsConfig> => {
    const res = await client.get('/settings');
    return res.data;
  },

  getAIStatus: async (): Promise<{ connected: boolean; status: string; message: string; model?: string }> => {
    const res = await client.get('/ai/status');
    return res.data;
  },

  testAiConnection: async (payload: { api_key?: string; base_url?: string; model_name?: string }): Promise<{ connected: boolean; status: string; message: string; model?: string }> => {
    const res = await client.post('/ai/test', payload);
    return res.data;
  },

  updateSettings: async (settings: Partial<SettingsConfig> & { zai_api_key?: string; zai_base_url?: string }) => {
    const res = await client.post('/settings', settings);
    return res.data;
  },
};
