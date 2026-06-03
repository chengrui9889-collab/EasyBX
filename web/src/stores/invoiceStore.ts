import { create } from 'zustand';
import type { Invoice, UploadResponse, DeleteResponse } from '@/types/invoice';
import { invoicesApi } from '@/api/invoices';

interface InvoiceState {
  invoices: Invoice[];
  total: number;
  totalPages: number;
  currentPage: number;
  pageSize: number;
  activeTab: string;
  dateFrom: string | null;
  dateTo: string | null;
  viewMode: 'table' | 'card';
  loading: boolean;
  uploading: boolean;
  error: string | null;
  trashInvoices: Invoice[];
  trashTotal: number;
  trashLoading: boolean;

  fetchInvoices: () => Promise<void>;
  setPage: (page: number) => void;
  setPageSize: (size: number) => void;
  setActiveTab: (tab: string) => void;
  setDateRange: (from: string | null, to: string | null) => void;
  setViewMode: (mode: 'table' | 'card') => void;
  uploadFiles: (files: File[]) => Promise<UploadResponse>;
  fetchTrash: () => Promise<void>;
  confirmInvoice: (id: number) => Promise<void>;
  deleteInvoice: (id: number) => Promise<DeleteResponse>;
  restoreInvoice: (id: number) => Promise<void>;
  restoreFromArchive: (id: number) => Promise<void>;
}

export const useInvoiceStore = create<InvoiceState>((set, get) => ({
  invoices: [],
  total: 0,
  totalPages: 0,
  currentPage: 1,
  pageSize: 20,
  activeTab: 'all',
  dateFrom: null,
  dateTo: null,
  viewMode: (localStorage.getItem('easybx_viewMode') as 'table' | 'card') || 'table',
  loading: false,
  uploading: false,
  error: null,
  trashInvoices: [],
  trashTotal: 0,
  trashLoading: false,

  fetchInvoices: async () => {
    const { activeTab, currentPage, pageSize, dateFrom, dateTo } = get();
    set({ loading: true, error: null });

    try {
      if (activeTab === 'pending_failed') {
        const [pendingRes, failedRes] = await Promise.all([
          invoicesApi.list({ state: 'pending', page: currentPage, page_size: pageSize, date_from: dateFrom ?? undefined, date_to: dateTo ?? undefined }),
          invoicesApi.list({ state: 'failed', page: currentPage, page_size: pageSize, date_from: dateFrom ?? undefined, date_to: dateTo ?? undefined }),
        ]);

        const merged = [...pendingRes.items, ...failedRes.items].sort(
          (a, b) => new Date(b.invoice_date ?? 0).getTime() - new Date(a.invoice_date ?? 0).getTime(),
        );

        set({
          invoices: merged,
          total: pendingRes.total + failedRes.total,
          totalPages: Math.max(pendingRes.total_pages, failedRes.total_pages),
          loading: false,
        });
      } else {
        const state = activeTab === 'all' ? undefined : activeTab;
        const res = await invoicesApi.list({
          state,
          page: currentPage,
          page_size: pageSize,
          date_from: dateFrom ?? undefined,
          date_to: dateTo ?? undefined,
        });

        set({
          invoices: res.items,
          total: res.total,
          totalPages: res.total_pages,
          loading: false,
        });
      }
    } catch {
      set({ error: '加载发票列表失败', loading: false });
    }
  },

  setPage: (page: number) => {
    set({ currentPage: page });
    get().fetchInvoices();
  },

  setPageSize: (size: number) => {
    set({ currentPage: 1, pageSize: size });
    get().fetchInvoices();
  },

  setActiveTab: (tab: string) => {
    set({ activeTab: tab, currentPage: 1 });
    get().fetchInvoices();
  },

  setDateRange: (from: string | null, to: string | null) => {
    set({ dateFrom: from, dateTo: to, currentPage: 1 });
    get().fetchInvoices();
  },

  setViewMode: (mode: 'table' | 'card') => {
    set({ viewMode: mode });
    localStorage.setItem('easybx_viewMode', mode);
  },

  uploadFiles: async (files: File[]) => {
    set({ uploading: true, error: null });
    try {
      const result = await invoicesApi.upload(files);
      set({ uploading: false });
      get().setActiveTab('processing');
      return result;
    } catch {
      set({ error: '上传失败', uploading: false });
      throw new Error('上传失败');
    }
  },

  fetchTrash: async () => {
    set({ trashLoading: true });
    try {
      const res = await invoicesApi.trashList();
      set({ trashInvoices: res.items, trashTotal: res.total, trashLoading: false });
    } catch {
      set({ trashLoading: false });
    }
  },

  confirmInvoice: async (id: number) => {
    await invoicesApi.confirm(id);
    get().fetchInvoices();
  },

  deleteInvoice: async (id: number) => {
    const result = await invoicesApi.remove(id);
    get().fetchInvoices();
    if (result.type === 'soft') {
      get().fetchTrash();
    }
    return result;
  },

  restoreInvoice: async (id: number) => {
    await invoicesApi.restore(id);
    get().fetchTrash();
    get().fetchInvoices();
  },

  restoreFromArchive: async (id: number) => {
    await invoicesApi.restoreFromArchive(id);
    get().fetchInvoices();
  },
}));