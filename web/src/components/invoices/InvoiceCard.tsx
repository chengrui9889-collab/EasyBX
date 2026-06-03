import { Receipt, Train, Car, Plane, FileText, Eye } from 'lucide-react';
import { cn } from '@/lib/utils';
import { STATUS_LABELS, STATUS_COLORS } from '@/lib/constants';
import type { Invoice } from '@/types/invoice';

const iconMap: Record<string, React.ComponentType<{ className?: string }>> = {
  Receipt,
  Train,
  Car,
  Plane,
  FileText,
};

function getIcon(type: string | null): React.ComponentType<{ className?: string }> {
  const nameMap: Record<string, string> = {
    '增值税': 'Receipt',
    '高铁': 'Train',
    '滴滴': 'Car',
    '飞机': 'Plane',
  };
  return iconMap[nameMap[type || '']] || iconMap.FileText;
}

const colorMap: Record<string, string> = {
  '增值税': 'text-red-500',
  '高铁': 'text-blue-500',
  '滴滴': 'text-green-500',
  '飞机': 'text-purple-500',
};

const statusBadgeStyles: Record<string, string> = {
  blue: 'bg-blue-100 text-blue-700',
  yellow: 'bg-yellow-100 text-yellow-700',
  red: 'bg-red-100 text-red-700',
  green: 'bg-green-100 text-green-700',
};

interface InvoiceCardProps {
  invoice: Invoice;
  onView: (id: number) => void;
  onDelete: (id: number) => void;
  variant?: 'card' | 'row';
}

export function InvoiceCard({
  invoice,
  onView,
  onDelete,
  variant = 'card',
}: InvoiceCardProps) {
  const iconColor = colorMap[invoice.invoice_type || ''] || 'text-gray-400';
  const IconComp = getIcon(invoice.invoice_type);
  const badgeColor = STATUS_COLORS[invoice.status] || 'gray';
  const badgeLabel = STATUS_LABELS[invoice.status] || invoice.status;

  const amountDisplay =
    invoice.amount != null ? `¥${invoice.amount.toFixed(2)}` : '待识别';

  if (variant === 'row') {
    return (
      <div className="flex items-center gap-3 py-2">
        <IconComp className={cn('h-5 w-5 flex-shrink-0', iconColor)} />
        <span className="w-32 truncate text-sm text-gray-700">
          {invoice.invoice_no || '-'}
        </span>
        <span className="w-24 text-right text-sm font-medium text-gray-900">
          {amountDisplay}
        </span>
        <span className="w-28 text-sm text-gray-500">
          {invoice.invoice_date || '-'}
        </span>
        <span className="min-w-0 flex-1 truncate text-sm text-gray-600">
          {invoice.vendor || '-'}
        </span>
        <span className="w-28 truncate text-sm text-gray-500">
          {invoice.project_name || '-'}
        </span>
        <span className="w-16 text-sm text-gray-500">
          {invoice.category || '-'}
        </span>
        <span
          className={cn(
            'inline-flex rounded-full px-2 py-0.5 text-xs font-medium',
            statusBadgeStyles[badgeColor],
          )}
        >
          {invoice.status === 'processing' && (
            <svg className="mr-1 h-3 w-3 animate-spin" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
          )}
          {badgeLabel}
        </span>
        <div className="flex items-center gap-1">
          <button
            onClick={(e) => { e.stopPropagation(); onView(invoice.id); }}
            className="rounded p-1 text-blue-600 hover:bg-blue-50"
            title="查看"
          >
            <Eye className="h-4 w-4" />
          </button>
        </div>
      </div>
    );
  }

  return (
    <div
      onClick={() => onView(invoice.id)}
      className="cursor-pointer rounded-lg border border-gray-200 bg-white p-4 shadow-sm transition-shadow hover:shadow-md"
    >
      <div className="mb-2 flex items-center justify-between">
        <IconComp className={cn('h-6 w-6', iconColor)} />
        <span
          className={cn(
            'rounded-full px-2 py-0.5 text-xs font-medium',
            statusBadgeStyles[badgeColor],
          )}
        >
          {invoice.status === 'processing' && (
            <svg className="mr-1 inline h-3 w-3 animate-spin" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
          )}
          {badgeLabel}
        </span>
      </div>

      <p className="mb-1 text-lg font-semibold text-gray-900">{amountDisplay}</p>
      <p className="text-sm text-gray-500">{invoice.invoice_date || '日期待识别'}</p>
      <p className="mt-1 truncate text-sm text-gray-600">{invoice.vendor || '-'}</p>
      {invoice.project_name && (
        <p className="mt-0.5 truncate text-xs text-gray-400">{invoice.project_name}</p>
      )}
      {invoice.category && (
        <p className="mt-0.5 truncate text-xs text-gray-400">报销类型：{invoice.category}</p>
      )}

      <div className="mt-3 flex items-center gap-2 border-t border-gray-100 pt-2">
        <button
          onClick={(e) => { e.stopPropagation(); onView(invoice.id); }}
          className="rounded px-2 py-1 text-xs text-blue-600 hover:bg-blue-50"
        >
          查看
        </button>
        <button
          onClick={(e) => { e.stopPropagation(); onDelete(invoice.id); }}
          className="rounded px-2 py-1 text-xs text-red-500 hover:bg-red-50"
        >
          删除
        </button>
      </div>
    </div>
  );
}