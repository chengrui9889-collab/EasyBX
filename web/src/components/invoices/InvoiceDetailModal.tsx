import { useEffect, useState, useCallback } from 'react';
import { Modal } from '@/components/ui/Modal';
import { InvoiceEditor } from './InvoiceEditor';
import { invoicesApi } from '@/api/invoices';
import { useInvoiceStore } from '@/stores/invoiceStore';
import type { Invoice, UpdateInvoiceRequest } from '@/types/invoice';

interface InvoiceDetailModalProps {
  invoiceId: number | null;
  onClose: () => void;
}

export function InvoiceDetailModal({ invoiceId, onClose }: InvoiceDetailModalProps) {
  const [invoice, setInvoice] = useState<Invoice | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const deleteInvoice = useInvoiceStore((s) => s.deleteInvoice);
  const confirmInvoice = useInvoiceStore((s) => s.confirmInvoice);
  const fetchInvoices = useInvoiceStore((s) => s.fetchInvoices);

  useEffect(() => {
    if (invoiceId === null) {
      setInvoice(null);
      setError(null);
      return;
    }

    setLoading(true);
    setError(null);
    invoicesApi
      .get(invoiceId)
      .then((data) => setInvoice(data))
      .catch((err) => {
        setInvoice(null);
        if (err?.response?.status === 404) {
          setError('发票不存在或已被删除');
        } else {
          setError('加载发票信息失败，请稍后重试');
        }
      })
      .finally(() => setLoading(false));
  }, [invoiceId]);

  const handleSave = useCallback(
    async (data: UpdateInvoiceRequest) => {
      if (!invoice) return;
      setSaving(true);
      try {
        await invoicesApi.update(invoice.id, data);
        setInvoice((prev) => prev ? { ...prev, ...data } : prev);
        fetchInvoices();
        onClose();
      } catch (err: any) {
        const msg = err?.response?.data?.detail || '保存失败，请稍后重试';
        alert(msg);
      } finally {
        setSaving(false);
      }
    },
    [invoice, onClose, fetchInvoices],
  );

  const handleConfirm = useCallback(async () => {
    if (!invoice) return;
    setSaving(true);
    try {
      await confirmInvoice(invoice.id);
      onClose();
    } catch (err: any) {
      const msg = err?.response?.data?.detail || '确认入库失败';
      alert(msg);
    } finally {
      setSaving(false);
    }
  }, [invoice, confirmInvoice, onClose]);

  const handleDelete = useCallback(async () => {
    if (!invoice) return;
    const isConfirmed = invoice.status === 'confirmed';
    const msg = isConfirmed
      ? '发票将移至回收站，30天内可恢复'
      : '确定删除这张发票吗？删除后不可恢复';
    if (!window.confirm(msg)) return;
    await deleteInvoice(invoice.id);
    onClose();
  }, [invoice, deleteInvoice, onClose]);

  const isOpen = invoiceId !== null;

  return (
    <Modal open={isOpen} onClose={onClose} title="发票详情" size="xl">
      {loading ? (
        <div className="flex items-center justify-center py-12">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-gray-200 border-t-blue-600" />
        </div>
      ) : error ? (
        <div className="py-8 text-center">
          <p className="text-red-500">{error}</p>
          <button
            onClick={() => { setError(null); setLoading(true); invoicesApi.get(invoiceId!).then(setInvoice).catch(() => setInvoice(null)).finally(() => setLoading(false)); }}
            className="mt-2 text-sm text-blue-600 hover:underline"
          >
            重新加载
          </button>
        </div>
      ) : invoice ? (
        <div className="flex flex-col gap-6 lg:flex-row">
          <div className="flex-shrink-0 lg:w-1/2">
            <div className="overflow-hidden rounded-lg border border-gray-200 bg-gray-50">
              {invoice.file_path.match(/\.(jpg|jpeg|png)$/i) ? (
                <img
                  src={invoicesApi.getFileUrl(invoice.id)}
                  alt={invoice.file_original_name || '发票文件'}
                  className="max-h-[500px] w-full object-contain"
                />
              ) : (
                <iframe
                  src={invoicesApi.getFileUrl(invoice.id)}
                  className="h-[500px] w-full"
                  title="发票预览"
                />
              )}
            </div>
          </div>

          <div className="flex-1 overflow-y-auto">
            <InvoiceEditor
              invoice={invoice}
              onSave={handleSave}
              onConfirm={handleConfirm}
              onDelete={handleDelete}
              saving={saving}
            />
          </div>
        </div>
      ) : (
        <div className="py-8 text-center text-gray-500">未找到发票信息</div>
      )}
    </Modal>
  );
}