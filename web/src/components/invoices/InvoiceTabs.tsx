import { RefreshCw, LayoutList, LayoutGrid, Trash2 } from 'lucide-react';
import { cn } from '@/lib/utils';
import { INVOICE_TABS } from '@/lib/constants';

interface InvoiceTabsProps {
  activeTab: string;
  onTabChange: (tab: string) => void;
  trashCount: number;
  onTrashOpen: () => void;
  onDateChange: (from: string | null, to: string | null) => void;
  onRefresh: () => void;
  viewMode: 'table' | 'card';
  onViewModeChange: (mode: 'table' | 'card') => void;
}

export function InvoiceTabs({
  activeTab,
  onTabChange,
  trashCount,
  onTrashOpen,
  onDateChange,
  onRefresh,
  viewMode,
  onViewModeChange,
}: InvoiceTabsProps) {
  return (
    <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
      <div className="flex gap-1 rounded-lg bg-gray-100 p-1">
        {INVOICE_TABS.map((tab) => (
          <button
            key={tab.key}
            onClick={() => onTabChange(tab.key)}
            className={cn(
              'rounded-md px-3 py-1.5 text-sm font-medium transition-colors',
              activeTab === tab.key
                ? 'bg-white text-blue-700 shadow-sm'
                : 'text-gray-600 hover:text-gray-900',
            )}
          >
            {tab.label}
          </button>
        ))}
      </div>

      <div className="flex items-center gap-2">
        <input
          type="date"
          onChange={(e) => {
            const from = e.target.value || null;
            onDateChange(from, (document.getElementById('invoice-date-to') as HTMLInputElement)?.value || null);
          }}
          className="rounded-md border border-gray-300 px-2 py-1.5 text-sm text-gray-700 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          placeholder="开始日期"
        />
        <span className="text-xs text-gray-400">-</span>
        <input
          id="invoice-date-to"
          type="date"
          onChange={(e) => {
            const to = e.target.value || null;
            onDateChange((document.querySelector('input[type="date"]') as HTMLInputElement)?.value || null, to);
          }}
          className="rounded-md border border-gray-300 px-2 py-1.5 text-sm text-gray-700 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          placeholder="结束日期"
        />

        <button
          onClick={onRefresh}
          className="rounded-md p-1.5 text-gray-500 hover:bg-gray-100 hover:text-gray-700"
          title="刷新"
        >
          <RefreshCw className="h-4 w-4" />
        </button>

        <div className="flex rounded-md border border-gray-300">
          <button
            onClick={() => onViewModeChange('table')}
            className={cn(
              'rounded-l-md p-1.5',
              viewMode === 'table'
                ? 'bg-blue-50 text-blue-600'
                : 'text-gray-500 hover:bg-gray-50',
            )}
            title="表格视图"
          >
            <LayoutList className="h-4 w-4" />
          </button>
          <button
            onClick={() => onViewModeChange('card')}
            className={cn(
              'rounded-r-md p-1.5',
              viewMode === 'card'
                ? 'bg-blue-50 text-blue-600'
                : 'text-gray-500 hover:bg-gray-50',
            )}
            title="卡片视图"
          >
            <LayoutGrid className="h-4 w-4" />
          </button>
        </div>

        <button
          onClick={onTrashOpen}
          className="relative rounded-md p-1.5 text-gray-500 hover:bg-gray-100 hover:text-gray-700"
          title="回收站"
        >
          <Trash2 className="h-4 w-4" />
          {trashCount > 0 && (
            <span className="absolute -right-1 -top-1 flex h-4 min-w-[16px] items-center justify-center rounded-full bg-red-500 px-1 text-[10px] font-medium text-white">
              {trashCount > 99 ? '99+' : trashCount}
            </span>
          )}
        </button>
      </div>
    </div>
  );
}