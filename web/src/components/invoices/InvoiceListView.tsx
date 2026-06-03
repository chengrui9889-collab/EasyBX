import { Receipt, Train, Car, Plane, FileText, Eye, RotateCcw } from 'lucide-react';
import { Table, type Column } from '@/components/ui/Table';
import type { Invoice } from '@/types/invoice';
import { STATUS_LABELS, STATUS_COLORS } from '@/lib/constants';
import { cn } from '@/lib/utils';

interface InvoiceListViewProps {
  invoices: Invoice[];
  onView: (id: number) => void;
  onDelete: (id: number) => void;
  onRestore?: (id: number) => void;
  selectedIds?: number[];
  onToggleSelect?: (id: number) => void;
}

const iconMap: Record<string, React.ComponentType<{ className?: string }>> = {
  Receipt, Train, Car, Plane, FileText,
};

function getIcon(type: string | null): React.ComponentType<{ className?: string }> {
  const nameMap: Record<string, string> = {
    '增值税': 'Receipt', '高铁': 'Train', '滴滴': 'Car', '飞机': 'Plane',
  };
  return iconMap[nameMap[type || '']] || iconMap.FileText;
}

function getIconColor(type: string | null): string {
  const colors: Record<string, string> = {
    '增值税': 'text-red-500', '高铁': 'text-blue-500', '滴滴': 'text-green-500', '飞机': 'text-purple-500',
  };
  return colors[type || ''] || 'text-gray-400';
}

const badgeStyles: Record<string, string> = {
  blue: 'bg-blue-100 text-blue-700',
  yellow: 'bg-yellow-100 text-yellow-700',
  red: 'bg-red-100 text-red-700',
  green: 'bg-green-100 text-green-700',
};

export function InvoiceListView({ invoices, onView, onDelete, onRestore, selectedIds, onToggleSelect }: InvoiceListViewProps) {
  const columns: Column<Invoice>[] = [
    ...(onToggleSelect
      ? [
          {
            key: 'select' as const,
            header: '',
            width: 'w-10',
            render: (inv: Invoice) => (
              <input
                type="checkbox"
                checked={selectedIds?.includes(inv.id) ?? false}
                onChange={(e) => {
                  e.stopPropagation();
                  onToggleSelect(inv.id);
                }}
                className="h-4 w-4 rounded border-gray-300"
              />
            ),
          } satisfies Column<Invoice>,
        ]
      : []),
    {
      key: 'type',
      header: '类型',
      width: 'w-12',
      render: (inv) => {
        const Icon = getIcon(inv.invoice_type);
        return <Icon className={cn('h-5 w-5', getIconColor(inv.invoice_type))} />;
      },
    },
    {
      key: 'invoice_no',
      header: '发票号码',
      render: (inv) => <span className="text-sm text-gray-700">{inv.invoice_no || '-'}</span>,
    },
    {
      key: 'amount',
      header: '金额',
      width: 'w-28',
      render: (inv) => (
        <span className="text-sm font-medium text-gray-900">
          {inv.amount != null ? `¥${inv.amount.toFixed(2)}` : '待识别'}
        </span>
      ),
    },
    {
      key: 'date',
      header: '开票日期',
      width: 'w-28',
      render: (inv) => <span className="text-sm text-gray-500">{inv.invoice_date || '-'}</span>,
    },
    {
      key: 'vendor',
      header: '销售方',
      render: (inv) => (
        <span className="block max-w-[200px] truncate text-sm text-gray-600">{inv.vendor || '-'}</span>
      ),
    },
    {
      key: 'project_name',
      header: '项目名称',
      render: (inv) => (
        <span className="block max-w-[180px] truncate text-sm text-gray-600">{inv.project_name || '-'}</span>
      ),
    },
    {
      key: 'category',
      header: '报销类型',
      width: 'w-20',
      render: (inv) => (
        <span className="text-sm text-gray-600">{inv.category || '-'}</span>
      ),
    },
    {
      key: 'status',
      header: '状态',
      width: 'w-24',
      render: (inv) => {
        const badgeColor = STATUS_COLORS[inv.status] || 'gray';
        return (
          <span className={cn('inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium', badgeStyles[badgeColor])}>
            {inv.status === 'processing' && (
              <svg className="mr-1 h-3 w-3 animate-spin" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
            )}
            {STATUS_LABELS[inv.status] || inv.status}
          </span>
        );
      },
    },
    {
      key: 'actions',
      header: '操作',
      width: 'w-20',
      render: (inv) => (
        <div className="flex items-center gap-1">
          <button
            onClick={(e) => { e.stopPropagation(); onView(inv.id); }}
            className="rounded p-1 text-blue-600 hover:bg-blue-50"
            title="查看"
          >
            <Eye className="h-4 w-4" />
          </button>
          {inv.status === 'archived' ? (
            <button
              onClick={(e) => { e.stopPropagation(); onRestore?.(inv.id); }}
              className="rounded p-1 text-green-600 hover:bg-green-50"
              title="恢复到已入库"
            >
              <RotateCcw className="h-4 w-4" />
            </button>
          ) : (
            <button
              onClick={(e) => { e.stopPropagation(); onDelete(inv.id); }}
              className="rounded p-1 text-red-500 hover:bg-red-50"
              title="删除"
            >
              <TrashIcon className="h-4 w-4" />
            </button>
          )}
        </div>
      ),
    },
  ];

  return <Table columns={columns} data={invoices} onRowClick={(inv) => onView(inv.id)} />;
}

function TrashIcon({ className }: { className?: string }) {
  return (
    <svg className={className} xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M3 6h18" />
      <path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6" />
      <path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2" />
    </svg>
  );
}