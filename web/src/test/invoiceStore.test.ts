import { describe, it, expect, vi, beforeEach } from 'vitest';
import { act } from '@testing-library/react';

vi.mock('@/api/invoices', () => ({
  invoicesApi: {
    list: vi.fn(),
    upload: vi.fn(),
    get: vi.fn(),
    getFileUrl: vi.fn((id: number) => `/api/invoices/${id}/file`),
    update: vi.fn(),
    confirm: vi.fn(),
    remove: vi.fn(),
    trashList: vi.fn(),
    restore: vi.fn(),
  },
}));

import { invoicesApi } from '@/api/invoices';
import { useInvoiceStore } from '@/stores/invoiceStore';

function makeInvoice(id: number) {
  return {
    id,
    user_id: 1,
    invoice_no: `NO-${id}`,
    amount: 100 + id,
    invoice_date: '2025-06-15',
    category: null,
    vendor: '测试公司',
    buyer_name: null,
    invoice_type: '增值税',
    project_name: null,
    train_no: null,
    departure_station: null,
    arrival_station: null,
    departure_location: null,
    arrival_location: null,
    flight_no: null,
    departure_city: null,
    arrival_city: null,
    file_path: `/uploads/${id}.jpg`,
    file_original_name: `invoice-${id}.jpg`,
    status: 'pending',
    remark: null,
    ocr_raw_data: null,
    created_at: '2025-06-15T10:00:00',
    updated_at: '2025-06-15T10:00:00',
  } as const;
}

describe('invoiceStore', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    act(() => {
      useInvoiceStore.setState({
        invoices: [],
        total: 0,
        totalPages: 0,
        currentPage: 1,
        pageSize: 20,
        activeTab: 'all',
        dateFrom: null,
        dateTo: null,
        viewMode: 'table',
        loading: false,
        uploading: false,
        error: null,
        trashInvoices: [],
        trashTotal: 0,
        trashLoading: false,
      });
    });
  });

  it('fetchInvoices sets invoices and pagination from API response', async () => {
    const invoices = [makeInvoice(1), makeInvoice(2)];
    vi.mocked(invoicesApi.list).mockResolvedValue({
      items: invoices,
      total: 2,
      page: 1,
      page_size: 20,
      total_pages: 1,
    });

    await act(async () => {
      await useInvoiceStore.getState().fetchInvoices();
    });

    const state = useInvoiceStore.getState();
    expect(state.invoices).toHaveLength(2);
    expect(state.total).toBe(2);
    expect(state.totalPages).toBe(1);
    expect(state.loading).toBe(false);
  });

  it('fetchInvoices on pending_failed tab sends two parallel requests and merges by date desc', async () => {
    const pendingInvs = [{ ...makeInvoice(1), status: 'pending' as const, invoice_date: '2025-06-15' }];
    const failedInvs = [{ ...makeInvoice(2), status: 'failed' as const, invoice_date: '2025-06-10' }];

    vi.mocked(invoicesApi.list)
      .mockResolvedValueOnce({
        items: pendingInvs,
        total: 1,
        page: 1,
        page_size: 20,
        total_pages: 1,
      })
      .mockResolvedValueOnce({
        items: failedInvs,
        total: 1,
        page: 1,
        page_size: 20,
        total_pages: 1,
      });

    act(() => {
      useInvoiceStore.getState().setActiveTab('pending_failed');
    });

    await act(async () => {
      await useInvoiceStore.getState().fetchInvoices();
    });

    const state = useInvoiceStore.getState();
    expect(state.invoices).toHaveLength(2);
    expect(state.total).toBe(2);
    expect(state.invoices[0].invoice_date).toBe('2025-06-15');
    expect(state.invoices[1].invoice_date).toBe('2025-06-10');
  });

  it('setPage triggers fetch with updated page', async () => {
    vi.mocked(invoicesApi.list).mockResolvedValue({
      items: [],
      total: 0,
      page: 3,
      page_size: 20,
      total_pages: 0,
    });

    await act(async () => {
      useInvoiceStore.getState().setPage(3);
    });

    expect(useInvoiceStore.getState().currentPage).toBe(3);
  });

  it('setActiveTab resets page to 1', async () => {
    act(() => {
      useInvoiceStore.setState({ currentPage: 5 });
    });

    act(() => {
      useInvoiceStore.getState().setActiveTab('confirmed');
    });

    expect(useInvoiceStore.getState().currentPage).toBe(1);
    expect(useInvoiceStore.getState().activeTab).toBe('confirmed');
  });

  it('setDateRange updates dateFrom/dateTo and fetches', async () => {
    vi.mocked(invoicesApi.list).mockResolvedValue({
      items: [],
      total: 0,
      page: 1,
      page_size: 20,
      total_pages: 0,
    });

    await act(async () => {
      useInvoiceStore.getState().setDateRange('2025-01-01', '2025-01-31');
    });

    expect(useInvoiceStore.getState().dateFrom).toBe('2025-01-01');
    expect(useInvoiceStore.getState().dateTo).toBe('2025-01-31');
  });

  it('uploadFiles sets uploading to true then false', async () => {
    vi.mocked(invoicesApi.upload).mockResolvedValue({
      results: [],
      skipped_count: 0,
    });

    let uploadingDuringCall = false;
    const uploadPromise = act(async () => {
      const p = useInvoiceStore.getState().uploadFiles([new File([''], 'a.jpg', { type: 'image/jpeg' })]);
      uploadingDuringCall = useInvoiceStore.getState().uploading;
      await p;
    });

    await uploadPromise;
    expect(uploadingDuringCall).toBe(true);
    expect(useInvoiceStore.getState().uploading).toBe(false);
  });

  it('setViewMode writes to localStorage', () => {
    localStorage.clear();
    act(() => {
      useInvoiceStore.getState().setViewMode('card');
    });

    expect(useInvoiceStore.getState().viewMode).toBe('card');
    expect(localStorage.getItem('easybx_viewMode')).toBe('card');
  });

  it('deleteInvoice calls remove and refreshes list', async () => {
    vi.mocked(invoicesApi.remove).mockResolvedValue({
      deleted: true,
      type: 'hard',
      restorable_until: null,
    });
    vi.mocked(invoicesApi.list).mockResolvedValue({
      items: [],
      total: 0,
      page: 1,
      page_size: 20,
      total_pages: 0,
    });

    await act(async () => {
      await useInvoiceStore.getState().deleteInvoice(5);
    });

    expect(invoicesApi.remove).toHaveBeenCalledWith(5);
    expect(invoicesApi.list).toHaveBeenCalled();
  });

  it('trashList and restore work correctly', async () => {
    vi.mocked(invoicesApi.trashList).mockResolvedValue({
      items: [makeInvoice(1)],
      total: 1,
      page: 1,
      page_size: 20,
      total_pages: 1,
    });

    await act(async () => {
      await useInvoiceStore.getState().fetchTrash();
    });

    expect(useInvoiceStore.getState().trashInvoices).toHaveLength(1);
    expect(useInvoiceStore.getState().trashTotal).toBe(1);

    vi.mocked(invoicesApi.restore).mockResolvedValue(makeInvoice(1));
    vi.mocked(invoicesApi.trashList).mockResolvedValue({
      items: [],
      total: 0,
      page: 1,
      page_size: 20,
      total_pages: 0,
    });

    await act(async () => {
      await useInvoiceStore.getState().restoreInvoice(1);
    });

    expect(invoicesApi.restore).toHaveBeenCalledWith(1);
  });
});