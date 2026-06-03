import { apiClient } from './client';
import type { ReimbursementPreview, PdfExportRequest, BatchPdfExportRequest } from '@/types/export';

export const exportsApi = {
  getReimbursementPreview: async (batchId: number): Promise<ReimbursementPreview> => {
    const r = await apiClient.get(`/exports/reimbursement-preview/${batchId}`);
    return r.data;
  },
  exportInvoicePdf: async (data: PdfExportRequest): Promise<Blob> => {
    const r = await apiClient.post('/exports/invoice-pdf', data, {
      responseType: 'blob',
    });
    return r.data;
  },
  exportBatchInvoicePdf: async (batchId: number, data: BatchPdfExportRequest): Promise<Blob> => {
    const r = await apiClient.post(`/batches/${batchId}/export-invoice-pdf`, data, {
      responseType: 'blob',
    });
    return r.data;
  },
  exportReimbursementPdf: (batchId: number): string => {
    return `/api/exports/reimbursement-pdf/${batchId}`;
  },
};
