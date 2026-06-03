import { useEffect, useState, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useInvoiceStore } from '@/stores/invoiceStore';
import { InvoiceUploader } from '@/components/invoices/InvoiceUploader';
import { InvoiceTabs } from '@/components/invoices/InvoiceTabs';
import { InvoiceListView } from '@/components/invoices/InvoiceListView';
import { InvoiceCardView } from '@/components/invoices/InvoiceCardView';
import { Pagination } from '@/components/invoices/Pagination';
import { EmptyState } from '@/components/invoices/EmptyState';
import { InvoiceDetailModal } from '@/components/invoices/InvoiceDetailModal';
import { TrashModal } from '@/components/invoices/TrashModal';
import { PdfExportSettings } from '@/components/exports/PdfExportSettings';
import { exportsApi } from '@/api/exports';
import { Button } from '@/components/ui/Button';
import { Download } from 'lucide-react';
import type { UploadResponse } from '@/types/invoice';

export function InvoicesPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const activeTab = searchParams.get('tab') || 'all';

  const {
    invoices,
    total,
    totalPages,
    currentPage,
    pageSize,
    viewMode,
    loading,
    error,
    trashTotal,
    fetchInvoices,
    setPage,
    setPageSize,
    setActiveTab,
    setDateRange,
    setViewMode,
    deleteInvoice,
    restoreFromArchive,
  } = useInvoiceStore();

  const [detailModalId, setDetailModalId] = useState<number | null>(null);
  const [trashOpen, setTrashOpen] = useState(false);
  const [selectedInvoiceIds, setSelectedInvoiceIds] = useState<number[]>([]);
  const [pdfExportOpen, setPdfExportOpen] = useState(false);

  useEffect(() => {
    fetchInvoices();
  }, [activeTab, currentPage, pageSize, fetchInvoices]);

  useEffect(() => {
    const store = useInvoiceStore.getState();
    if (store.activeTab !== activeTab) {
      setActiveTab(activeTab);
    }
  }, []);

  const handleTabChange = useCallback(
    (tab: string) => {
      setSearchParams({ tab });
      setActiveTab(tab);
    },
    [setSearchParams, setActiveTab],
  );

  const handleUploadComplete = useCallback(
    (result: UploadResponse) => {
      setSearchParams({ tab: 'processing' });
      const successCount = result.results.filter((r) => r.success).length;
      const skipCount = result.skipped_count;
      // Toast feedback — using alert for now
      const msg =
        skipCount > 0
          ? `${successCount} 张上传成功，${skipCount} 张跳过`
          : `${successCount} 张上传成功`;
      console.log(msg);
    },
    [setSearchParams],
  );

  const handleDateChange = useCallback(
    (from: string | null, to: string | null) => {
      setDateRange(from, to);
    },
    [setDateRange],
  );

  const handleRefresh = useCallback(() => {
    fetchInvoices();
  }, [fetchInvoices]);

  const handleDelete = useCallback(
    async (id: number) => {
      const inv = invoices.find((i) => i.id === id);
      const isHardDelete = inv?.status !== 'confirmed';
      const confirmMsg = isHardDelete
        ? '确定删除这张发票吗？删除后不可恢复'
        : '发票将移至回收站，30天内可恢复';

      if (!window.confirm(confirmMsg)) return;

      try {
        await deleteInvoice(id);
      } catch {
        // error handled in store
      }
    },
    [invoices, deleteInvoice],
  );

  const handleRestoreFromArchive = useCallback(
    async (id: number) => {
      if (!window.confirm('确定将该发票从归档中恢复吗？恢复后将变为已入库状态。')) return;
      try {
        await restoreFromArchive(id);
      } catch {
        // error handled in store
      }
    },
    [restoreFromArchive],
  );

  const handleToggleSelect = useCallback((id: number) => {
    setSelectedInvoiceIds((prev) =>
      prev.includes(id) ? prev.filter((i) => i !== id) : [...prev, id],
    );
  }, []);

  const triggerPdfDownload = useCallback(
    async (layouts: Record<string, 'portrait' | 'landscape'>) => {
      const blob = await exportsApi.exportInvoicePdf({
        invoice_ids: selectedInvoiceIds,
        layouts,
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `发票合并_${Date.now()}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    },
    [selectedInvoiceIds],
  );

  return (
    <div>
      <h2 className="mb-6 text-xl font-semibold text-gray-900">发票管理</h2>

      <InvoiceUploader onUploadComplete={handleUploadComplete} />

      <InvoiceTabs
        activeTab={activeTab}
        onTabChange={handleTabChange}
        trashCount={trashTotal}
        onTrashOpen={() => setTrashOpen(true)}
        onDateChange={handleDateChange}
        onRefresh={handleRefresh}
        viewMode={viewMode}
        onViewModeChange={setViewMode}
      />

      {selectedInvoiceIds.length > 0 && (
        <div className="mb-4 flex items-center gap-2">
          <span className="text-sm text-gray-500">已选 {selectedInvoiceIds.length} 张</span>
          <Button
            size="sm"
            variant="secondary"
            onClick={() => setPdfExportOpen(true)}
          >
            <Download className="mr-1 h-4 w-4" />导出 PDF
          </Button>
          <Button
            size="sm"
            variant="ghost"
            onClick={() => setSelectedInvoiceIds([])}
          >
            取消选择
          </Button>
        </div>
      )}

      {error && (
        <div className="mb-4 rounded-md bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {loading ? (
        <div className="flex items-center justify-center py-20">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-gray-200 border-t-blue-600" />
        </div>
      ) : invoices.length === 0 ? (
        <EmptyState />
      ) : viewMode === 'table' ? (
        <InvoiceListView
          invoices={invoices}
          onView={setDetailModalId}
          onDelete={handleDelete}
          onRestore={handleRestoreFromArchive}
          selectedIds={selectedInvoiceIds}
          onToggleSelect={handleToggleSelect}
        />
      ) : (
        <InvoiceCardView
          invoices={invoices}
          onView={setDetailModalId}
          onDelete={handleDelete}
        />
      )}

      <Pagination
        currentPage={currentPage}
        totalPages={totalPages}
        total={total}
        pageSize={pageSize}
        onPageChange={setPage}
        onPageSizeChange={setPageSize}
      />

      {/* Stage 3: InvoiceDetailModal */}
      <InvoiceDetailModal
        invoiceId={detailModalId}
        onClose={() => setDetailModalId(null)}
      />

      {/* Stage 4: TrashModal */}
      <TrashModal open={trashOpen} onClose={() => setTrashOpen(false)} />

      <PdfExportSettings
        open={pdfExportOpen}
        onClose={() => setPdfExportOpen(false)}
        invoices={invoices
          .filter((inv) => selectedInvoiceIds.includes(inv.id))
          .map((inv) => ({ invoice_type: inv.invoice_type }))}
        onExport={triggerPdfDownload}
      />
    </div>
  );
}