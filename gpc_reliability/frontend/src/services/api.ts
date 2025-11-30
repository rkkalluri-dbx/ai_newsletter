/**
 * API client for GPC Reliability Tracker
 */
import axios, { AxiosInstance, AxiosResponse } from 'axios';

// API base URL - use environment variable or relative path for same-origin deployment
const API_BASE_URL = (import.meta as any).env?.VITE_API_URL || '/api/v1';

// Create axios instance with defaults
const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
});

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response: AxiosResponse) => response,
  (error) => {
    if (error.response) {
      // Server responded with error status
      console.error('API Error:', error.response.data);
    } else if (error.request) {
      // Request made but no response
      console.error('Network Error:', error.message);
    }
    return Promise.reject(error);
  }
);

// Generic API response type
export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}

export interface SingleResponse<T> {
  data: T;
}

// Query parameters for list endpoints
export interface ListParams {
  page?: number;
  per_page?: number;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
}

export interface ProjectListParams extends ListParams {
  status?: string;
  vendor_id?: string;
  region?: string;
  priority?: string;
  date_from?: string;
  date_to?: string;
  search?: string;
}

export interface AlertListParams extends ListParams {
  severity?: string;
  alert_type?: string;
  acknowledged?: boolean;
  project_id?: string;
}

// Dashboard API
export const dashboardApi = {
  getSummary: () => apiClient.get('/dashboard/summary'),
  getNextActions: (limit?: number) => apiClient.get('/dashboard/next-actions', { params: { limit } }),
  getStatusDistribution: () => apiClient.get('/dashboard/status-distribution'),
  getRegionDistribution: () => apiClient.get('/dashboard/region-distribution'),
  getVendorPerformance: (limit?: number) => apiClient.get('/dashboard/vendor-performance', { params: { limit } }),
  getRecentActivity: (limit?: number) => apiClient.get('/dashboard/recent-activity', { params: { limit } }),
};

// Projects API
export const projectsApi = {
  list: (params?: ProjectListParams) => apiClient.get('/projects', { params }),
  get: (id: string) => apiClient.get(`/projects/${id}`),
  create: (data: Record<string, unknown>) => apiClient.post('/projects', data),
  update: (id: string, data: Record<string, unknown>) => apiClient.patch(`/projects/${id}`, data),
  delete: (id: string) => apiClient.delete(`/projects/${id}`),
  getHistory: (id: string) => apiClient.get(`/projects/${id}/history`),
  export: (params?: ProjectListParams) => apiClient.get('/projects/export', { params, responseType: 'blob' }),
};

// Vendors API
export const vendorsApi = {
  list: (params?: { active_only?: boolean; search?: string }) => apiClient.get('/vendors', { params }),
  get: (id: string) => apiClient.get(`/vendors/${id}`),
  create: (data: Record<string, unknown>) => apiClient.post('/vendors', data),
  update: (id: string, data: Record<string, unknown>) => apiClient.patch(`/vendors/${id}`, data),
  delete: (id: string) => apiClient.delete(`/vendors/${id}`),
  getMetrics: (id: string) => apiClient.get(`/vendors/${id}/metrics`),
  getProjects: (id: string, params?: ListParams) => apiClient.get(`/vendors/${id}/projects`, { params }),
};

// Alerts API
export const alertsApi = {
  list: (params?: AlertListParams) => apiClient.get('/alerts', { params }),
  get: (id: string) => apiClient.get(`/alerts/${id}`),
  create: (data: Record<string, unknown>) => apiClient.post('/alerts', data),
  acknowledge: (id: string, user_email?: string) =>
    apiClient.post(`/alerts/${id}/acknowledge`, { user_email }),
  bulkAcknowledge: (alert_ids: string[], user_email?: string) =>
    apiClient.post('/alerts/acknowledge', { alert_ids, user_email }),
  delete: (id: string) => apiClient.delete(`/alerts/${id}`),
  getStats: () => apiClient.get('/alerts/stats'),
};

// Milestones API
export const milestonesApi = {
  list: (params?: { project_id?: string; stage?: string; is_overdue?: boolean; completed?: boolean }) =>
    apiClient.get('/milestones', { params }),
  get: (id: string) => apiClient.get(`/milestones/${id}`),
  complete: (id: string, actual_date?: string) =>
    apiClient.post(`/milestones/${id}/complete`, { actual_date }),
  update: (id: string, data: Record<string, unknown>) => apiClient.patch(`/milestones/${id}`, data),
  getOverdue: (limit?: number) => apiClient.get('/milestones/overdue', { params: { limit } }),
  getUpcoming: (days?: number, limit?: number) => apiClient.get('/milestones/upcoming', { params: { days, limit } }),
};

// Gantt API
export const ganttApi = {
  getData: (params?: { vendor_id?: string; region?: string; status?: string; priority?: string; limit?: number }) =>
    apiClient.get('/gantt', { params }),
  getTimeline: (params?: { start_date?: string; end_date?: string; view?: 'week' | 'month' | 'quarter' }) =>
    apiClient.get('/gantt/timeline', { params }),
};

export default apiClient;
