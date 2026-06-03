import { create } from 'zustand';
import type {
  ReimbursementBatch,
  BatchDetail,
  AvailableInvoice,
  CreateBatchRequest,
  UpdateBatchRequest,
  UpdateBatchInvoiceRequest,
  SubstituteInvoiceItem,
  SubstituteRelationResponse,
  SubstituteCreateRequest,
} from '@/types/batch';
import { batchesApi } from '@/api/batches';

interface BatchState {
  batches: ReimbursementBatch[];
  currentBatch: BatchDetail | null;
  availableInvoices: AvailableInvoice[];
  availableTotal: number;
  availablePage: number;
  substituteInvoices: SubstituteInvoiceItem[];
  substituteTotal: number;
  substitutePage: number;
  substitutions: SubstituteRelationResponse[];
  loading: boolean;
  error: string | null;
  statusFilter: string;

  fetchBatches: () => Promise<void>;
  setStatusFilter: (status: string) => void;
  fetchBatch: (id: number) => Promise<void>;
  createBatch: (data: CreateBatchRequest) => Promise<ReimbursementBatch>;
  updateBatch: (id: number, data: UpdateBatchRequest) => Promise<void>;
  completeBatch: (id: number) => Promise<void>;
  archiveBatch: (id: number) => Promise<void>;
  unarchiveBatch: (id: number) => Promise<void>;
  deleteBatch: (id: number) => Promise<void>;
  fetchAvailableInvoices: (params?: { keyword?: string; page?: number; page_size?: number }) => Promise<void>;
  addInvoices: (batchId: number, invoiceIds: number[]) => Promise<void>;
  removeInvoice: (batchId: number, invoiceId: number) => Promise<void>;
  updateInvoice: (batchId: number, invoiceId: number, data: UpdateBatchInvoiceRequest) => Promise<void>;
  addManualRow: (batchId: number, data: { row_date?: string; expense_item: string; row_amount: number; quantity?: number; advance_amount?: number; remark?: string }) => Promise<void>;
  deleteManualRow: (batchId: number, rowId: number) => Promise<void>;
  fetchSubstituteInvoices: (batchId: number, params?: { keyword?: string; page?: number; page_size?: number }) => Promise<void>;
  createSubstitution: (batchId: number, data: SubstituteCreateRequest) => Promise<void>;
  fetchSubstitutions: (batchId: number) => Promise<void>;
  removeSubstitution: (batchId: number, subId: number) => Promise<void>;
  clearError: () => void;
}

export const useBatchStore = create<BatchState>((set, get) => ({
  batches: [],
  currentBatch: null,
  availableInvoices: [],
  availableTotal: 0,
  availablePage: 1,
  substituteInvoices: [],
  substituteTotal: 0,
  substitutePage: 1,
  substitutions: [],
  loading: false,
  error: null,
  statusFilter: '',

  fetchBatches: async () => {
    const { statusFilter } = get();
    set({ loading: true, error: null });
    try {
      const data = await batchesApi.list({ status: statusFilter || undefined });
      set({ batches: data.items, loading: false });
    } catch {
      set({ error: '加载批次列表失败', loading: false });
    }
  },

  setStatusFilter: (status: string) => {
    set({ statusFilter: status });
    get().fetchBatches();
  },

  fetchBatch: async (id: number) => {
    set({ loading: true, error: null });
    try {
      const data = await batchesApi.get(id);
      set({ currentBatch: data, loading: false });
    } catch {
      set({ error: '加载批次详情失败', loading: false });
    }
  },

  createBatch: async (data) => {
    set({ loading: true, error: null });
    try {
      const result = await batchesApi.create(data);
      await get().fetchBatches();
      set({ loading: false });
      return result;
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || '创建批次失败';
      set({ error: msg, loading: false });
      throw err;
    }
  },

  updateBatch: async (id, data) => {
    set({ loading: true, error: null });
    try {
      await batchesApi.update(id, data);
      await get().fetchBatch(id);
      set({ loading: false });
    } catch {
      set({ error: '更新批次失败', loading: false });
    }
  },

  completeBatch: async (id) => {
    set({ error: null });
    try {
      await batchesApi.complete(id);
      await get().fetchBatch(id);
      await get().fetchBatches();
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || '完成批次失败';
      set({ error: msg });
      throw err;
    }
  },

  archiveBatch: async (id) => {
    set({ error: null });
    try {
      await batchesApi.archive(id);
      await get().fetchBatch(id);
      await get().fetchBatches();
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || '归档批次失败';
      set({ error: msg });
      throw err;
    }
  },

  unarchiveBatch: async (id) => {
    set({ error: null });
    try {
      await batchesApi.unarchive(id);
      await get().fetchBatch(id);
      await get().fetchBatches();
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || '撤销归档失败';
      set({ error: msg });
      throw err;
    }
  },

  deleteBatch: async (id) => {
    set({ loading: true, error: null });
    try {
      await batchesApi.delete(id);
      set({ currentBatch: null, loading: false });
    } catch {
      set({ error: '删除批次失败', loading: false });
    }
  },

  fetchAvailableInvoices: async (params) => {
    try {
      const data = await batchesApi.listAvailableInvoices(params);
      set({
        availableInvoices: data.items,
        availableTotal: data.total,
        availablePage: data.page,
      });
    } catch {
      set({ error: '加载可选发票失败' });
    }
  },

  addInvoices: async (batchId, invoiceIds) => {
    set({ error: null });
    try {
      await batchesApi.addInvoices(batchId, { invoice_ids: invoiceIds });
      await get().fetchBatch(batchId);
      await get().fetchAvailableInvoices();
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || '添加发票失败';
      set({ error: msg });
      throw err;
    }
  },

  removeInvoice: async (batchId, invoiceId) => {
    set({ error: null });
    try {
      await batchesApi.removeInvoice(batchId, invoiceId);
      await get().fetchBatch(batchId);
    } catch {
      set({ error: '移除发票失败' });
    }
  },

  updateInvoice: async (batchId, invoiceId, data) => {
    set({ error: null });
    try {
      await batchesApi.updateInvoice(batchId, invoiceId, data);
      await get().fetchBatch(batchId);
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || '更新台账行失败';
      set({ error: msg });
      throw err;
    }
  },

  addManualRow: async (batchId, data) => {
    set({ error: null });
    try {
      await batchesApi.addManualRow(batchId, data);
      await get().fetchBatch(batchId);
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || '添加台账行失败';
      set({ error: msg });
      throw err;
    }
  },

  deleteManualRow: async (batchId, rowId) => {
    set({ error: null });
    try {
      if (!window.confirm('确定删除该台账行吗？若有替票关联将自动解除。')) return;
      await batchesApi.deleteManualRow(batchId, rowId);
      await get().fetchBatch(batchId);
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || '删除台账行失败';
      set({ error: msg });
    }
  },

  fetchSubstituteInvoices: async (batchId, params) => {
    try {
      const data = await batchesApi.listSubstituteInvoices(batchId, params);
      set({
        substituteInvoices: data.items,
        substituteTotal: data.total,
        substitutePage: data.page,
      });
    } catch {
      set({ error: '加载替票发票列表失败' });
    }
  },

  createSubstitution: async (batchId, data) => {
    set({ error: null });
    try {
      await batchesApi.createSubstitution(batchId, data);
      await get().fetchBatch(batchId);
      await get().fetchSubstitutions(batchId);
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || '创建替票关联失败';
      set({ error: msg });
      throw err;
    }
  },

  fetchSubstitutions: async (batchId) => {
    try {
      const data = await batchesApi.listSubstitutions(batchId);
      set({ substitutions: data.relations });
    } catch {
      set({ error: '加载替票关联列表失败' });
    }
  },

  removeSubstitution: async (batchId, subId) => {
    set({ error: null });
    try {
      if (!window.confirm('确定解除该替票关联吗？解除后替票发票将回到可选池。')) return;
      await batchesApi.removeSubstitution(batchId, subId);
      await get().fetchBatch(batchId);
      await get().fetchSubstitutions(batchId);
      await get().fetchAvailableInvoices();
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || '解除替票关联失败';
      set({ error: msg });
    }
  },

  clearError: () => set({ error: null }),
}));
