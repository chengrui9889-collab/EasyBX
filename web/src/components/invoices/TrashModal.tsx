import { useEffect, useCallback } from 'react';
import { Modal } from '@/components/ui/Modal';
import { Table, type Column } from '@/components/ui/Table';
import { useInvoiceStore } from '@/stores/invoiceStore';
import { getDaysLeft } from '@/lib/utils';
import type { Invoice } from '@/types/invoice';

interface TrashModalProps {
  open: boolean;
  onClose: () => void;
}

export function TrashModal({ open, onClose }: TrashModalProps) {
  const trashInvoices = useInvoiceStore((s) => s.trashInvoices);
  const trashTotal = useInvoiceStore((s) => s.trashTotal);
  const trashLoading = useInvoiceStore((s) => s.trashLoading);
  const fetchTrash = useInvoiceStore((s) => s.fetchTrash);
  const restoreInvoice = useInvoiceStore((s) => s.restoreInvoice);

  useEffect(() => {
    if (open) {
      fetchTrash();
    }
  }, [open, fetchTrash]);

  const handleRestore = useCallback(
    async (id: number) => {
      if (!window.confirm('确定恢复这张发票吗？')) return;
      try {
        await restoreInvoice(id);
      } catch (err) {
        alert('请检查后端是否正确运行: ' + (err instanceof Error ? err.message : ''));
      }
    },
    [restoreInvoice],
  );

  const columns: Column<Invoice>[] = [
    {
      key: 'invoice_no',
      header: '发票号码',
      render: (inv) => <span className="text-sm text-gray-700">{inv.invoice_no || '-'}</span>,
    },
    {
      key: 'amount',
      header: '金额',
      render: (inv) => (
        <span className="text-sm font-medium text-gray-900">
          {inv.amount != null ? `¥${inv.amount.toFixed(2)}` : '-'}
        </span>
      ),
    },
    {
      key: 'date',
      header: '开票日期',
      render: (inv) => <span className="text-sm text-gray-500">{inv.invoice_date || '-'}</span>,
    },
    {
      key: 'deleted_at',
      header: '删除时间',
      render: (inv) => (
        <span className="text-sm text-gray-500">
          {new Date(inv.updated_at).toLocaleDateString('zh-CN')}
        </span>
      ),
    },
    {
      key: 'days_left',
      header: '剩余天数',
      width: 'w-20',
      render: (inv) => {
        const days = getDaysLeft(inv.updated_at);
        return (
          <span className={`text-sm font-medium ${days <= 3 ? 'text-red-600' : 'text-gray-600'}`}>
            {days > 0 ? `${days} 天` : '已过期'}
          </span>
        );
      },
    },
    {
      key: 'actions',
      header: '操作',
      width: 'w-20',
      render: (inv) => (
        <button
          onClick={() => handleRestore(inv.id)}
          className="rounded px-2 py-1 text-xs text-blue-600 hover:bg-blue-50"
        >
          恢复
        </button>
      ),
    },
  ];

  return (
    <Modal open={open} onClose={onClose} title={`回收站 (${trashTotal})`} size="lg">
      {trashLoading ? (
        <div className="flex items-center justify-center py-12">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-gray-200 border-t-blue-600" />
        </div>
      ) : trashInvoices.length === 0 ? (
        <div className="py-12 text-center text-gray-400">回收站为空</div>
      ) : (
        <Table columns={columns} data={trashInvoices} />
      )}
    </Modal>
  );
}