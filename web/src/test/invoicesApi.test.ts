import { describe, it, expect, vi, beforeEach } from 'vitest';
import MockAdapter from 'axios-mock-adapter';
import { apiClient } from '@/api/client';
import { invoicesApi } from '@/api/invoices';

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
  };
}

describe('invoicesApi', () => {
  let mock: MockAdapter;

  beforeEach(() => {
    mock = new MockAdapter(apiClient);
  });

  afterEach(() => {
    mock.restore();
  });

  describe('list', () => {
    it('calls GET /invoices/ and returns InvoiceListResponse', async () => {
      const inv = makeInvoice(1);
      mock.onGet('/invoices/').reply(200, {
        items: [inv],
        total: 1,
        page: 1,
        page_size: 20,
        total_pages: 1,
      });

      const result = await invoicesApi.list();

      expect(result.items).toHaveLength(1);
      expect(result.items[0].id).toBe(1);
      expect(result.total).toBe(1);
      expect(result.page).toBe(1);
      expect(result.page_size).toBe(20);
    });

    it('passes query params (state, page, page_size, date_from, date_to)', async () => {
      mock.onGet('/invoices/').reply(200, {
        items: [], total: 0, page: 1, page_size: 50, total_pages: 0,
      });

      await invoicesApi.list({
        state: 'pending',
        page: 2,
        page_size: 50,
        date_from: '2025-01-01',
        date_to: '2025-01-31',
      });

      const params = mock.history.get[0].params;
      expect(params.state).toBe('pending');
      expect(params.page).toBe(2);
      expect(params.page_size).toBe(50);
      expect(params.date_from).toBe('2025-01-01');
      expect(params.date_to).toBe('2025-01-31');
    });
  });

  describe('upload', () => {
    it('calls POST /invoices/ with FormData containing files', async () => {
      mock.onPost('/invoices/').reply(200, {
        results: [
          { filename: 'a.jpg', success: true, invoice_id: 1, error: null },
        ],
        skipped_count: 0,
      });

      const file = new File([''], 'a.jpg', { type: 'image/jpeg' });
      const result = await invoicesApi.upload([file]);

      expect(result.results).toHaveLength(1);
      expect(result.results[0].success).toBe(true);
      expect(result.results[0].invoice_id).toBe(1);

      const reqData = mock.history.post[0].data;
      expect(reqData instanceof FormData).toBe(true);
    });
  });

  describe('get', () => {
    it('calls GET /invoices/{id} and returns Invoice', async () => {
      const inv = makeInvoice(5);
      mock.onGet('/invoices/5').reply(200, inv);

      const result = await invoicesApi.get(5);

      expect(result.id).toBe(5);
      expect(result.invoice_no).toBe('NO-5');
    });
  });

  describe('getFileUrl', () => {
    it('returns /api/invoices/{id}/file', () => {
      expect(invoicesApi.getFileUrl(3)).toBe('/api/invoices/3/file');
    });
  });

  describe('update', () => {
    it('calls PUT /invoices/{id} and returns updated Invoice', async () => {
      const inv = makeInvoice(10);
      mock.onPut('/invoices/10').reply(200, { ...inv, amount: 999 });

      const result = await invoicesApi.update(10, { amount: 999 });

      expect(result.amount).toBe(999);
    });
  });

  describe('confirm', () => {
    it('calls POST /invoices/{id}/confirm and returns Invoice', async () => {
      const inv = { ...makeInvoice(7), status: 'confirmed' as const };
      mock.onPost('/invoices/7/confirm').reply(200, inv);

      const result = await invoicesApi.confirm(7);

      expect(result.status).toBe('confirmed');
    });
  });

  describe('remove', () => {
    it('calls DELETE /invoices/{id} and returns DeleteResponse', async () => {
      mock.onDelete('/invoices/2').reply(200, {
        deleted: true,
        type: 'hard',
        restorable_until: null,
      });

      const result = await invoicesApi.remove(2);

      expect(result.deleted).toBe(true);
      expect(result.type).toBe('hard');
    });
  });

  describe('trashList', () => {
    it('calls GET /invoices/trash with optional page params', async () => {
      const inv = makeInvoice(1);
      mock.onGet('/invoices/trash').reply(200, {
        items: [inv], total: 1, page: 1, page_size: 20, total_pages: 1,
      });

      await invoicesApi.trashList({ page: 1, page_size: 20 });

      expect(mock.history.get[0].url).toBe('/invoices/trash');
    });
  });

  describe('restore', () => {
    it('calls POST /invoices/{id}/restore and returns Invoice', async () => {
      const inv = { ...makeInvoice(8), status: 'confirmed' as const };
      mock.onPost('/invoices/8/restore').reply(200, inv);

      const result = await invoicesApi.restore(8);

      expect(result.id).toBe(8);
      expect(result.status).toBe('confirmed');
    });
  });
});