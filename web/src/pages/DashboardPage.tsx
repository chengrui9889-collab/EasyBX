import { useEffect } from 'react';
import { Link } from 'react-router-dom';
import { FileText, Receipt, Upload } from 'lucide-react';
import { useDashboardStore } from '@/stores/dashboardStore';
import type { DashboardStats } from '@/types/dashboard';

function formatAmount(amount: number): string {
  return `¥${amount.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

function StatCard({ label, value, href }: { label: string; value: string | number; href?: string }) {
  const content = (
    <div className="flex flex-col rounded-lg border border-gray-200 bg-white p-6 shadow-sm hover:shadow-md transition-shadow">
      <span className="text-sm font-medium text-gray-500">{label}</span>
      <span className="mt-2 text-3xl font-bold text-gray-900">{value}</span>
    </div>
  );

  if (href) {
    return <Link to={href} className="block">{content}</Link>;
  }
  return content;
}

function EmptyStateGuide({ stats }: { stats: DashboardStats }) {
  if (stats.pending_invoice_count !== 0 || stats.active_batch_count !== 0) {
    return null;
  }

  return (
    <div className="flex flex-col items-center justify-center rounded-lg border-2 border-dashed border-gray-200 bg-white px-6 py-12">
      <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-blue-50">
        <Receipt className="h-8 w-8 text-blue-500" />
      </div>
      <p className="text-lg font-medium text-gray-700">欢迎使用 EasyBX</p>
      <p className="mt-1 text-sm text-gray-500">
        上传你的第一张发票，开始报销之旅
      </p>
      <Link
        to="/invoices"
        className="mt-4 inline-flex items-center gap-2 rounded-lg bg-blue-600 px-5 py-2.5 text-sm font-medium text-white hover:bg-blue-700 transition-colors"
      >
        <Upload className="h-4 w-4" />
        开始使用
      </Link>
    </div>
  );
}

function QuickActions() {
  return (
    <div>
      <h3 className="mb-3 text-sm font-medium text-gray-500">快捷操作</h3>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <Link
          to="/invoices"
          className="flex items-center gap-3 rounded-lg border border-gray-200 bg-white px-5 py-4 shadow-sm hover:shadow-md hover:bg-gray-50 transition-all"
        >
          <Upload className="h-5 w-5 text-blue-600" />
          <span className="text-sm font-medium text-gray-700">上传发票</span>
        </Link>
        <Link
          to="/batches"
          className="flex items-center gap-3 rounded-lg border border-gray-200 bg-white px-5 py-4 shadow-sm hover:shadow-md hover:bg-gray-50 transition-all"
        >
          <FileText className="h-5 w-5 text-blue-600" />
          <span className="text-sm font-medium text-gray-700">创建批次</span>
        </Link>
        <Link
          to="/batches"
          className="flex items-center gap-3 rounded-lg border border-gray-200 bg-white px-5 py-4 shadow-sm hover:shadow-md hover:bg-gray-50 transition-all"
        >
          <Receipt className="h-5 w-5 text-blue-600" />
          <span className="text-sm font-medium text-gray-700">导出台账</span>
        </Link>
      </div>
    </div>
  );
}

function RecentBatches({ stats }: { stats: DashboardStats }) {
  if (stats.recent_batches.length === 0) {
    return null;
  }

  return (
    <div>
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-sm font-medium text-gray-500">最近批次</h3>
        <Link to="/batches" className="text-xs text-blue-600 hover:text-blue-700">
          查看更多 →
        </Link>
      </div>
      <div className="rounded-lg border border-gray-200 bg-white shadow-sm">
        {stats.recent_batches.map((batch, idx) => (
          <Link
            key={batch.id}
            to={`/batches/${batch.id}`}
            className={`flex items-center justify-between px-5 py-3.5 transition-colors hover:bg-gray-50 ${
              idx < stats.recent_batches.length - 1 ? 'border-b border-gray-100' : ''
            }`}
          >
            <div className="flex flex-col">
              <span className="text-sm font-medium text-gray-900">{batch.department}</span>
              <span className="text-xs text-gray-400">{batch.reporter} · {batch.report_date || '-'}</span>
            </div>
            <div className="flex items-center gap-3">
              <span className="text-sm font-semibold text-gray-900">{formatAmount(batch.total_amount)}</span>
              <span className="text-xs text-gray-400">&rarr;</span>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}

export function DashboardPage() {
  const { stats, loading, error, fetchStats } = useDashboardStore();

  useEffect(() => {
    fetchStats();
  }, [fetchStats]);

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-semibold text-gray-900">概览</h2>

      {loading && !stats && (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="animate-pulse rounded-lg border border-gray-200 bg-white p-6">
              <div className="mb-2 h-4 w-16 rounded bg-gray-200" />
              <div className="h-9 w-20 rounded bg-gray-200" />
            </div>
          ))}
        </div>
      )}

      {!loading && (
        <>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            <StatCard
              label="待处理发票数"
              value={error ? '——' : (stats?.pending_invoice_count ?? '——')}
              href={!error && stats && stats.pending_invoice_count > 0 ? '/invoices?tab=pending' : undefined}
            />
            <StatCard
              label="本月报销总额"
              value={error ? '——' : (stats ? formatAmount(stats.monthly_total_amount) : '——')}
            />
            <StatCard
              label="进行中批次数"
              value={error ? '——' : (stats?.active_batch_count ?? '——')}
              href={!error && stats && stats.active_batch_count > 0 ? '/batches' : undefined}
            />
          </div>

          {stats && <EmptyStateGuide stats={stats} />}

          {stats && stats.recent_batches.length > 0 && <RecentBatches stats={stats} />}

          <QuickActions />
        </>
      )}
    </div>
  );
}