import { apiClient } from './client';
import type {
  Invoice,
  InvoiceListResponse,
  InvoiceListParams,
  UpdateInvoiceRequest,
  UploadResponse,
  DeleteResponse,
} from '@/types/invoice';

export const invoicesApi = {
  list: async (params?: InvoiceListParams): Promise<InvoiceListResponse> => {
    const r = await apiClient.get('/invoices/', { params });
    return r.data;
  },

  upload: async (files: File[]): Promise<UploadResponse> => {
    const form = new FormData();
    files.forEach((f) => form.append('files', f));
    const r = await apiClient.post('/invoices/', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return r.data;
  },

  get: async (id: number): Promise<Invoice> => {
    const r = await apiClient.get(`/invoices/${id}`);
    return r.data;
  },

  getFileUrl: (id: number): string => {
    const token = localStorage.getItem('easybx_token');
    const params = token ? `?token=${encodeURIComponent(token)}` : '';
    return `/api/invoices/${id}/file${params}`;
  },

  update: async (id: number, data: UpdateInvoiceRequest): Promise<Invoice> => {
    const r = await apiClient.put(`/invoices/${id}`, data);
    return r.data;
  },

  confirm: async (id: number): Promise<Invoice> => {
    const r = await apiClient.post(`/invoices/${id}/confirm`);
    return r.data;
  },

  remove: async (id: number): Promise<DeleteResponse> => {
    const r = await apiClient.delete(`/invoices/${id}`);
    return r.data;
  },

  trashList: async (
    params?: { page?: number; page_size?: number },
  ): Promise<InvoiceListResponse> => {
    const r = await apiClient.get('/invoices/trash', { params });
    return r.data;
  },

  restore: async (id: number): Promise<Invoice> => {
    const r = await apiClient.post(`/invoices/${id}/restore`);
    return r.data;
  },

  restoreFromArchive: async (id: number): Promise<Invoice> => {
    const r = await apiClient.post(`/invoices/${id}/restore-from-archive`);
    return r.data;
  },
};