import { apiClient } from './client';
import type {
  ReimbursementBatch,
  BatchDetail,
  BatchListResponse,
  AvailableInvoiceListResponse,
  LedgerRow,
  CreateBatchRequest,
  UpdateBatchRequest,
  UpdateBatchInvoiceRequest,
  AddInvoicesRequest,
  ManualRowCreateRequest,
  SubstituteInvoiceListResponse,
  SubstituteCreateRequest,
  SubstituteRelationListResponse,
  SubstituteCreatedResponse,
} from '@/types/batch';

export const batchesApi = {
  list: async (params?: { status?: string }): Promise<BatchListResponse> => {
    const r = await apiClient.get('/batches/', { params });
    return r.data;
  },

  create: async (data: CreateBatchRequest): Promise<ReimbursementBatch> => {
    const r = await apiClient.post('/batches/', data);
    return r.data;
  },

  complete: async (id: number): Promise<ReimbursementBatch> => {
    const r = await apiClient.put(`/batches/${id}/complete`);
    return r.data;
  },

  archive: async (id: number): Promise<{ archived: boolean; archived_invoice_count: number; batch_status: string }> => {
    const r = await apiClient.post(`/batches/${id}/archive`);
    return r.data;
  },

  unarchive: async (id: number): Promise<{ unarchived: boolean; batch_status: string; restored_invoice_count: number }> => {
    const r = await apiClient.post(`/batches/${id}/unarchive`);
    return r.data;
  },

  get: async (id: number): Promise<BatchDetail> => {
    const r = await apiClient.get(`/batches/${id}`);
    return r.data;
  },

  update: async (id: number, data: UpdateBatchRequest): Promise<ReimbursementBatch> => {
    const r = await apiClient.put(`/batches/${id}`, data);
    return r.data;
  },

  delete: async (id: number): Promise<{ deleted: boolean; released_invoice_count: number }> => {
    const r = await apiClient.delete(`/batches/${id}`);
    return r.data;
  },

  listAvailableInvoices: async (params?: {
    keyword?: string;
    page?: number;
    page_size?: number;
  }): Promise<AvailableInvoiceListResponse> => {
    const r = await apiClient.get('/batches/available-invoices', { params });
    return r.data;
  },

  addInvoices: async (batchId: number, data: AddInvoicesRequest): Promise<LedgerRow[]> => {
    const r = await apiClient.post(`/batches/${batchId}/invoices`, data);
    return r.data;
  },

  removeInvoice: async (batchId: number, invoiceId: number): Promise<{ removed: boolean }> => {
    const r = await apiClient.delete(`/batches/${batchId}/invoices/${invoiceId}`);
    return r.data;
  },

  updateInvoice: async (
    batchId: number,
    invoiceId: number,
    data: UpdateBatchInvoiceRequest,
  ): Promise<LedgerRow> => {
    const r = await apiClient.put(`/batches/${batchId}/invoices/${invoiceId}`, data);
    return r.data;
  },

  getExportExcelUrl: (batchId: number): string => {
    const token = localStorage.getItem('easybx_token');
    const params = token ? `?token=${encodeURIComponent(token)}` : '';
    return `/api/batches/${batchId}/export-excel${params}`;
  },

  addManualRow: async (batchId: number, data: ManualRowCreateRequest): Promise<LedgerRow> => {
    const r = await apiClient.post(`/batches/${batchId}/manual-rows`, data);
    return r.data;
  },

  updateManualRow: async (batchId: number, rowId: number, data: ManualRowCreateRequest): Promise<LedgerRow> => {
    const r = await apiClient.put(`/batches/${batchId}/manual-rows/${rowId}`, data);
    return r.data;
  },

  deleteManualRow: async (batchId: number, rowId: number): Promise<{ deleted: boolean; released_substitute_count: number }> => {
    const r = await apiClient.delete(`/batches/${batchId}/manual-rows/${rowId}`);
    return r.data;
  },

  listSubstituteInvoices: async (batchId: number, params?: {
    keyword?: string;
    page?: number;
    page_size?: number;
  }): Promise<SubstituteInvoiceListResponse> => {
    const r = await apiClient.get(`/batches/${batchId}/available-substitute-invoices`, { params });
    return r.data;
  },

  createSubstitution: async (batchId: number, data: SubstituteCreateRequest): Promise<SubstituteCreatedResponse> => {
    const r = await apiClient.post(`/batches/${batchId}/substitutions`, data);
    return r.data;
  },

  listSubstitutions: async (batchId: number): Promise<SubstituteRelationListResponse> => {
    const r = await apiClient.get(`/batches/${batchId}/substitutions`);
    return r.data;
  },

  removeSubstitution: async (batchId: number, subId: number): Promise<{ removed: boolean }> => {
    const r = await apiClient.delete(`/batches/${batchId}/substitutions/${subId}`);
    return r.data;
  },
};
