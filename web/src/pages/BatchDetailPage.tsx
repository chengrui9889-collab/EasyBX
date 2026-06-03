import { useEffect, useState, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useBatchStore } from '@/stores/batchStore';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Modal } from '@/components/ui/Modal';
import { SubstituteTicketModal } from '@/components/batches/SubstituteTicketModal';
import { formatDate, formatCurrency } from '@/lib/utils';
import { batchesApi } from '@/api/batches';
import { exportsApi } from '@/api/exports';
import { invoicesApi } from '@/api/invoices';
import type { LedgerRow } from '@/types/batch';
import { PdfExportSettings } from '@/components/exports/PdfExportSettings';
import {
  ArrowLeft,
  Download,
  Plus,
  Trash2,
  Edit3,
  Search,
  ChevronLeft,
  ChevronRight,
  Eye,
  Link2,
  Archive,
  RotateCcw,
} from 'lucide-react';

export function BatchDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const batchId = Number(id);

  const {
    currentBatch,
    loading,
    error,
    availableInvoices,
    availableTotal,
    fetchBatch,
    updateBatch,
    completeBatch,
    archiveBatch,
    unarchiveBatch,
    deleteBatch,
    fetchAvailableInvoices,
    addInvoices,
    removeInvoice,
    updateInvoice,
    addManualRow,
    deleteManualRow,
  } = useBatchStore();

  const [editRowId, setEditRowId] = useState<number | null>(null);
  const [editForm, setEditForm] = useState({ quantity: 1, advance_amount: 0, remark: '' });
  const [addInvoiceOpen, setAddInvoiceOpen] = useState(false);
  const [editBatchOpen, setEditBatchOpen] = useState(false);
  const [selectedIds, setSelectedIds] = useState<number[]>([]);
  const [searchKeyword, setSearchKeyword] = useState('');
  const [availPage, setAvailPage] = useState(1);
  const [previewInvoiceId, setPreviewInvoiceId] = useState<number | null>(null);
  const [batchForm, setBatchForm] = useState({
    department: '', reporter: '', period_start: '', period_end: '',
    report_date: '', reviewer: '', payee: '', bank_account: '', bank_name: '',
  });

  const [substituteModalOpen, setSubstituteModalOpen] = useState(false);
  const [manualRowModalOpen, setManualRowModalOpen] = useState(false);
  const [editManualRowId, setEditManualRowId] = useState<number | null>(null);
  const [manualRowForm, setManualRowForm] = useState({
    row_date: new Date().toISOString().slice(0, 10),
    expense_item: '',
    row_amount: 0,
    quantity: 1,
    advance_amount: 0,
    remark: '',
  });
  const [editManualRowForm, setEditManualRowForm] = useState({
    row_date: '',
    expense_item: '',
    row_amount: 0,
    quantity: 1,
    advance_amount: 0,
    remark: '',
  });

  const [pdfExportOpen, setPdfExportOpen] = useState(false);

  const triggerPdfDownload = useCallback(async (layouts: Record<string, 'portrait' | 'landscape'>) => {
    const blob = await exportsApi.exportBatchInvoicePdf(batchId, { layouts });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `发票合并_${Date.now()}.pdf`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }, [batchId]);

  useEffect(() => {
    if (batchId) fetchBatch(batchId);
  }, [batchId, fetchBatch]);

  useEffect(() => {
    if (currentBatch) {
      setBatchForm({
        department: currentBatch.department,
        reporter: currentBatch.reporter,
        period_start: currentBatch.period_start || '',
        period_end: currentBatch.period_end || '',
        report_date: currentBatch.report_date || '',
        reviewer: currentBatch.reviewer || '',
        payee: currentBatch.payee || '',
        bank_account: currentBatch.bank_account || '',
        bank_name: currentBatch.bank_name || '',
      });
    }
  }, [currentBatch]);

  const handleEditRow = useCallback((row: LedgerRow) => {
    setEditRowId(row.invoice_id);
    setEditForm({
      quantity: row.quantity,
      advance_amount: row.advance_amount,
      remark: row.remark || '',
    });
  }, []);

  const handleSaveRow = useCallback(async () => {
    if (editRowId === null) return;
    try {
      await updateInvoice(batchId, editRowId, {
        quantity: editForm.quantity,
        advance_amount: editForm.advance_amount,
        remark: editForm.remark || null,
      });
      setEditRowId(null);
    } catch {
      // handled in store
    }
  }, [batchId, editRowId, editForm, updateInvoice]);

  const handleRemoveInvoice = useCallback(async (invoiceId: number) => {
    if (!window.confirm('确定从批次中移除该发票吗？')) return;
    await removeInvoice(batchId, invoiceId);
  }, [batchId, removeInvoice]);

  const handleDeleteBatch = useCallback(async () => {
    if (!window.confirm('确定删除该批次吗？批次中的发票将被释放。')) return;
    await deleteBatch(batchId);
    navigate('/batches');
  }, [batchId, deleteBatch, navigate]);

  const handleCompleteBatch = useCallback(async () => {
    if (!window.confirm('完成批次后无法再修改台账和发票，确定完成吗？')) return;
    try {
      await completeBatch(batchId);
    } catch {
      // handled in store
    }
  }, [batchId, completeBatch]);

  const handleArchiveBatch = useCallback(async () => {
    if (!window.confirm('归档后该批次下的所有发票将被标记为已归档，确定归档吗？')) return;
    try {
      await archiveBatch(batchId);
    } catch {
      // handled in store
    }
  }, [batchId, archiveBatch]);

  const handleUnarchiveBatch = useCallback(async () => {
    if (!window.confirm('撤销归档将把该批次恢复为已完成状态，所有发票也将恢复为已入库，确定撤销吗？')) return;
    try {
      await unarchiveBatch(batchId);
    } catch {
      // handled in store
    }
  }, [batchId, unarchiveBatch]);

  const isLocked = currentBatch?.status !== 'draft';

  const openAddInvoices = useCallback(() => {
    setSelectedIds([]);
    setSearchKeyword('');
    setAvailPage(1);
    setAddInvoiceOpen(true);
    fetchAvailableInvoices({ page: 1, page_size: 10 });
  }, [fetchAvailableInvoices]);

  const handleSearch = useCallback(() => {
    setAvailPage(1);
    fetchAvailableInvoices({ keyword: searchKeyword || undefined, page: 1, page_size: 10 });
  }, [searchKeyword, fetchAvailableInvoices]);

  const handleAvailPageChange = useCallback((newPage: number) => {
    setAvailPage(newPage);
    fetchAvailableInvoices({ keyword: searchKeyword || undefined, page: newPage, page_size: 10 });
  }, [searchKeyword, fetchAvailableInvoices]);

  const toggleSelectInvoice = useCallback((invoiceId: number) => {
    setSelectedIds((prev) =>
      prev.includes(invoiceId) ? prev.filter((id) => id !== invoiceId) : [...prev, invoiceId],
    );
  }, []);

  const handleAddInvoices = useCallback(async () => {
    if (selectedIds.length === 0) return;
    try {
      await addInvoices(batchId, selectedIds);
      setAddInvoiceOpen(false);
      setSelectedIds([]);
    } catch {
      // handled in store
    }
  }, [batchId, selectedIds, addInvoices]);

  const handleSaveBatch = useCallback(async () => {
    try {
      await updateBatch(batchId, {
        department: batchForm.department,
        reporter: batchForm.reporter || undefined,
        period_start: batchForm.period_start || null,
        period_end: batchForm.period_end || null,
        report_date: batchForm.report_date || null,
        reviewer: batchForm.reviewer || null,
        payee: batchForm.payee || null,
        bank_account: batchForm.bank_account || null,
        bank_name: batchForm.bank_name || null,
      });
      setEditBatchOpen(false);
    } catch {
      // handled in store
    }
  }, [batchId, batchForm, updateBatch]);

  const handleAddManualRow = useCallback(async () => {
    if (!manualRowForm.expense_item.trim()) return;
    if (manualRowForm.row_amount <= 0) return;
    try {
      await addManualRow(batchId, {
        row_date: manualRowForm.row_date || undefined,
        expense_item: manualRowForm.expense_item.trim(),
        row_amount: manualRowForm.row_amount,
        quantity: manualRowForm.quantity || 1,
        advance_amount: manualRowForm.advance_amount || manualRowForm.row_amount,
        remark: manualRowForm.remark || undefined,
      });
      setManualRowModalOpen(false);
      setManualRowForm({
        row_date: new Date().toISOString().slice(0, 10),
        expense_item: '',
        row_amount: 0,
        quantity: 1,
        advance_amount: 0,
        remark: '',
      });
    } catch {
      // handled in store
    }
  }, [batchId, manualRowForm, addManualRow]);

  const handleEditManualRow = useCallback((row: LedgerRow) => {
    setEditManualRowId(row.id);
    setEditManualRowForm({
      row_date: row.invoice_date || '',
      expense_item: row.expense_item || '',
      row_amount: row.amount || 0,
      quantity: row.quantity,
      advance_amount: row.advance_amount,
      remark: row.remark || '',
    });
  }, []);

  const handleSaveManualRow = useCallback(async () => {
    if (editManualRowId === null) return;
    try {
      await batchesApi.updateManualRow(batchId, editManualRowId, {
        row_date: editManualRowForm.row_date || undefined,
        expense_item: editManualRowForm.expense_item,
        row_amount: editManualRowForm.row_amount,
        quantity: editManualRowForm.quantity,
        advance_amount: editManualRowForm.advance_amount,
        remark: editManualRowForm.remark || undefined,
      });
      await fetchBatch(batchId);
      setEditManualRowId(null);
    } catch {
      // handled in store
    }
  }, [batchId, editManualRowId, editManualRowForm, fetchBatch]);

  const handleRemoveManualRow = useCallback(async (rowId: number) => {
    await deleteManualRow(batchId, rowId);
  }, [batchId, deleteManualRow]);

  if (loading && !currentBatch) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-gray-200 border-t-blue-600" />
      </div>
    );
  }

  if (!currentBatch) {
    return (
      <div>
        <Button variant="ghost" onClick={() => navigate('/batches')} className="mb-4">
          <ArrowLeft className="mr-1 h-4 w-4" />返回批次列表
        </Button>
        <p className="text-gray-500">批次不存在</p>
      </div>
    );
  }

  const rows = currentBatch.ledger_rows || [];
  const totalPages = Math.max(1, Math.ceil(availableTotal / 10));

  return (
    <div>
      <Button variant="ghost" onClick={() => navigate('/batches')} className="mb-4">
        <ArrowLeft className="mr-1 h-4 w-4" />返回批次列表
      </Button>

      {error && (
        <div className="mb-4 rounded-md bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div>
      )}

      <div className="mb-6 rounded-lg border border-gray-200 bg-white p-6">
        <div className="flex items-start justify-between">
          <div>
            <h2 className="mb-2 text-xl font-semibold text-gray-900">
              {currentBatch.department} - {currentBatch.reporter}
            </h2>
            <div className="flex flex-wrap gap-x-6 gap-y-1 text-sm text-gray-500">
              <span>报账期间：{currentBatch.period_start ? `${currentBatch.period_start} ~ ${currentBatch.period_end}` : '未设置'}</span>
              <span>报账日期：{currentBatch.report_date ? formatDate(currentBatch.report_date) : '未设置'}</span>
              <span>审核人：{currentBatch.reviewer || '未设置'}</span>
              <span>收款人：{currentBatch.payee || '未设置'}</span>
              <span>银行卡号：{currentBatch.bank_account || '未设置'}</span>
              <span>开户行：{currentBatch.bank_name || '未设置'}</span>
              <span className="font-medium text-gray-900">合计：{formatCurrency(currentBatch.total_amount)}</span>
            </div>
          </div>
          <div className="flex gap-2">
            {!isLocked && (
              <>
                <Button variant="secondary" size="sm" onClick={() => setSubstituteModalOpen(true)}>
                  <Link2 className="mr-1 h-4 w-4" />替票管理
                </Button>
                <Button variant="secondary" size="sm" onClick={() => setEditBatchOpen(true)}>
                  <Edit3 className="mr-1 h-4 w-4" />编辑
                </Button>
              </>
            )}
            <Button variant="secondary" size="sm" onClick={() => setPdfExportOpen(true)}>
              <Download className="mr-1 h-4 w-4" />导出 PDF
            </Button>
            <Button variant="secondary" size="sm" onClick={() => navigate(`/batches/${batchId}/preview`)}>
              <Eye className="mr-1 h-4 w-4" />预览报销单
            </Button>
            <Button variant="secondary" size="sm" onClick={() => window.open(batchesApi.getExportExcelUrl(batchId), '_blank')}>
              <Download className="mr-1 h-4 w-4" />导出
            </Button>
            {!isLocked && (
              <Button variant="ghost" size="sm" className="text-red-500 hover:text-red-700" onClick={handleDeleteBatch}>
                <Trash2 className="mr-1 h-4 w-4" />删除
              </Button>
            )}
            {currentBatch.status === 'draft' && (
              <Button size="sm" onClick={handleCompleteBatch} className="bg-green-600 text-white hover:bg-green-700">
                完成批次
              </Button>
            )}
            {currentBatch.status === 'completed' && (
              <Button size="sm" onClick={handleArchiveBatch} className="bg-orange-600 text-white hover:bg-orange-700">
                <Archive className="mr-1 h-4 w-4" />归档这批发票
              </Button>
            )}
            {currentBatch.status === 'archived' && (
              <Button size="sm" onClick={handleUnarchiveBatch} className="bg-blue-600 text-white hover:bg-blue-700">
                <RotateCcw className="mr-1 h-4 w-4" />撤销归档
              </Button>
            )}
          </div>
        </div>
      </div>

      <div className="mb-4 flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900">台账明细（{rows.length} 条）</h3>
        {!isLocked && (
          <div className="flex gap-2">
            <Button size="sm" variant="secondary" onClick={() => setManualRowModalOpen(true)}>
              <Plus className="mr-1 h-4 w-4" />新增台账行
            </Button>
            <Button size="sm" onClick={openAddInvoices}>
              <Plus className="mr-1 h-4 w-4" />添加发票
            </Button>
          </div>
        )}
      </div>

      <div className="overflow-x-auto rounded-lg border border-gray-200">
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="border-b border-gray-200 bg-gray-50">
              <th className="px-4 py-3 font-medium text-gray-600">日期</th>
              <th className="px-4 py-3 font-medium text-gray-600">类别/事由</th>
              <th className="px-4 py-3 font-medium text-gray-600">发票号</th>
              <th className="px-4 py-3 font-medium text-gray-600">供应商</th>
              <th className="px-4 py-3 font-medium text-gray-600">金额</th>
              <th className="px-4 py-3 font-medium text-gray-600">数量</th>
              <th className="px-4 py-3 font-medium text-gray-600">单价</th>
              <th className="px-4 py-3 font-medium text-gray-600">垫款金额</th>
              <th className="px-4 py-3 font-medium text-gray-600">备注</th>
              <th className="px-4 py-3 font-medium text-gray-600">操作</th>
            </tr>
          </thead>
          <tbody>
            {rows.length === 0 ? (
              <tr>
                <td colSpan={10} className="px-4 py-12 text-center text-gray-400">
                  暂无台账数据，请点击"新增台账行"或"添加发票"加入数据
                </td>
              </tr>
            ) : (
              rows.map((row, idx) => (
                <tr key={row.id} className={`border-b border-gray-100 ${row.is_substitute ? 'bg-blue-50/70' : idx % 2 === 0 ? 'bg-white' : 'bg-gray-50/50'}`}>
                  <td className="px-4 py-3 text-gray-700">{row.invoice_date ? formatDate(row.invoice_date) : '-'}</td>
                  <td className="px-4 py-3 text-gray-700">
                    {row.expense_item || row.category || '-'}
                    {row.is_substitute && (
                      <span className="ml-1 rounded bg-blue-100 px-1.5 py-0.5 text-xs text-blue-700" title={row.substitute_for || undefined}>
                        替票
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-gray-700">{row.invoice_no || '-'}</td>
                  <td className="px-4 py-3 text-gray-700">{row.vendor || '-'}</td>
                  <td className="px-4 py-3 text-gray-900">{row.amount != null ? formatCurrency(row.amount) : '-'}</td>
                  <td className="px-4 py-3 text-gray-700">{row.quantity}</td>
                  <td className="px-4 py-3 text-gray-700">{formatCurrency(row.unit_price)}</td>
                  <td className="px-4 py-3 text-gray-700">{formatCurrency(row.advance_amount)}</td>
                  <td className="max-w-[200px] truncate px-4 py-3 text-gray-500">{row.remark || '-'}</td>
                  <td className="px-4 py-3">
                    {!isLocked && (
                      <div className="flex gap-1">
                        {row.invoice_id ? (
                          <>
                            <Button variant="ghost" size="sm" onClick={() => handleEditRow(row)}>
                              <Edit3 className="h-4 w-4" />
                            </Button>
                            <Button variant="ghost" size="sm" className="text-red-500 hover:text-red-700" onClick={() => handleRemoveInvoice(row.invoice_id)}>
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </>
                        ) : (
                          <>
                            <Button variant="ghost" size="sm" onClick={() => handleEditManualRow(row)}>
                              <Edit3 className="h-4 w-4" />
                            </Button>
                            <Button variant="ghost" size="sm" className="text-red-500 hover:text-red-700" onClick={() => handleRemoveManualRow(row.id)}>
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </>
                        )}
                      </div>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Edit Ledger Row Modal */}
      <Modal open={editRowId !== null} onClose={() => setEditRowId(null)} title="编辑台账行" size="sm">
        <div className="flex flex-col gap-4">
          <Input
            label="数量"
            type="number"
            min={1}
            step={1}
            value={editForm.quantity}
            onChange={(e) => setEditForm({ ...editForm, quantity: Number(e.target.value) })}
          />
          <Input
            label="垫款金额"
            type="number"
            min={0}
            step={0.01}
            value={editForm.advance_amount}
            onChange={(e) => setEditForm({ ...editForm, advance_amount: Number(e.target.value) })}
          />
          <Input
            label="备注"
            value={editForm.remark}
            onChange={(e) => setEditForm({ ...editForm, remark: e.target.value })}
          />
        </div>
        <div className="mt-6 flex justify-end gap-3">
          <Button variant="secondary" onClick={() => setEditRowId(null)}>取消</Button>
          <Button onClick={handleSaveRow}>保存</Button>
        </div>
      </Modal>

      {/* Add Invoices Modal */}
      <Modal open={addInvoiceOpen} onClose={() => setAddInvoiceOpen(false)} title="添加发票" size="xl">
        <div className="mb-4 flex gap-2">
          <Input
            placeholder="搜索发票号、供应商、类别"
            value={searchKeyword}
            onChange={(e) => setSearchKeyword(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
            className="flex-1"
          />
          <Button variant="secondary" onClick={handleSearch}>
            <Search className="h-4 w-4" />
          </Button>
        </div>

        {availableInvoices.length === 0 ? (
          <p className="py-8 text-center text-gray-400">无可选发票（已确认且未加入其他批次）</p>
        ) : (
          <>
            <div className="max-h-80 overflow-y-auto">
              <table className="w-full text-left text-sm">
                <thead className="sticky top-0 bg-white">
                  <tr className="border-b border-gray-200">
                    <th className="w-10 px-4 py-2" />
                    <th className="px-4 py-2 font-medium text-gray-600">发票号</th>
                    <th className="px-4 py-2 font-medium text-gray-600">日期</th>
                    <th className="px-4 py-2 font-medium text-gray-600">类别</th>
                    <th className="px-4 py-2 font-medium text-gray-600">供应商</th>
                    <th className="px-4 py-2 font-medium text-gray-600">金额</th>
                    <th className="w-16 px-4 py-2 font-medium text-gray-600">操作</th>
                  </tr>
                </thead>
                <tbody>
                  {availableInvoices.map((inv) => (
                    <tr
                      key={inv.id}
                      className={`cursor-pointer border-b border-gray-100 hover:bg-gray-50 ${
                        selectedIds.includes(inv.id) ? 'bg-blue-50' : ''
                      }`}
                      onClick={() => toggleSelectInvoice(inv.id)}
                    >
                      <td className="px-4 py-2">
                        <input
                          type="checkbox"
                          checked={selectedIds.includes(inv.id)}
                          onChange={() => toggleSelectInvoice(inv.id)}
                          className="h-4 w-4 rounded border-gray-300"
                        />
                      </td>
                      <td className="px-4 py-2 text-gray-700">{inv.invoice_no || '-'}</td>
                      <td className="px-4 py-2 text-gray-500">{inv.invoice_date ? formatDate(inv.invoice_date) : '-'}</td>
                      <td className="px-4 py-2 text-gray-700">{inv.category || '-'}</td>
                      <td className="px-4 py-2 text-gray-700">{inv.vendor || '-'}</td>
                      <td className="px-4 py-2 text-gray-900">{inv.amount != null ? formatCurrency(inv.amount) : '-'}</td>
                      <td className="px-4 py-2">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={(e) => {
                            e.stopPropagation();
                            setPreviewInvoiceId(inv.id);
                          }}
                          title="预览发票"
                        >
                          <Eye className="h-4 w-4 text-gray-500 hover:text-blue-600" />
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="mt-3 flex items-center justify-between">
              <span className="text-sm text-gray-500">
                已选 {selectedIds.length} 张，共 {availableTotal} 张可选
              </span>
              <div className="flex items-center gap-2">
                <Button
                  variant="ghost"
                  size="sm"
                  disabled={availPage <= 1}
                  onClick={() => handleAvailPageChange(availPage - 1)}
                >
                  <ChevronLeft className="h-4 w-4" />
                </Button>
                <span className="text-sm text-gray-500">
                  {availPage} / {totalPages}
                </span>
                <Button
                  variant="ghost"
                  size="sm"
                  disabled={availPage >= totalPages}
                  onClick={() => handleAvailPageChange(availPage + 1)}
                >
                  <ChevronRight className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </>
        )}

        <div className="mt-4 flex justify-end gap-3 border-t border-gray-200 pt-4">
          <Button variant="secondary" onClick={() => setAddInvoiceOpen(false)}>取消</Button>
          <Button onClick={handleAddInvoices} disabled={selectedIds.length === 0}>
            添加 {selectedIds.length > 0 ? `(${selectedIds.length} 张)` : ''}
          </Button>
        </div>
      </Modal>

      {/* Invoice Preview Modal */}
      <Modal open={previewInvoiceId !== null} onClose={() => setPreviewInvoiceId(null)} title="发票预览" size="sm">
        {previewInvoiceId !== null && (() => {
          const inv = availableInvoices.find((i) => i.id === previewInvoiceId);
          if (!inv) return <p className="py-8 text-center text-gray-400">未找到发票信息</p>;
          const isImage = inv.file_path?.match(/\.(jpg|jpeg|png)$/i);
          return (
            <div className="overflow-hidden rounded-lg border border-gray-200 bg-gray-50">
              {isImage ? (
                <img
                  src={invoicesApi.getFileUrl(inv.id)}
                  alt={inv.file_original_name || '发票文件'}
                  className="max-h-[500px] w-full object-contain"
                />
              ) : (
                <iframe
                  src={invoicesApi.getFileUrl(inv.id)}
                  className="h-[500px] w-full"
                  title="发票预览"
                />
              )}
            </div>
          );
        })()}
      </Modal>

      {/* Edit Batch Modal */}
      <Modal open={editBatchOpen} onClose={() => setEditBatchOpen(false)} title="编辑批次信息" size="lg">
        <div className="grid grid-cols-2 gap-4">
          <Input label="部门" value={batchForm.department} onChange={(e) => setBatchForm({ ...batchForm, department: e.target.value })} />
          <Input label="报账人" value={batchForm.reporter} onChange={(e) => setBatchForm({ ...batchForm, reporter: e.target.value })} />
          <Input label="报销开始日期" type="date" value={batchForm.period_start} onChange={(e) => setBatchForm({ ...batchForm, period_start: e.target.value })} />
          <Input label="报销结束日期" type="date" value={batchForm.period_end} onChange={(e) => setBatchForm({ ...batchForm, period_end: e.target.value })} />
          <Input label="报账日期" type="date" value={batchForm.report_date} onChange={(e) => setBatchForm({ ...batchForm, report_date: e.target.value })} />
          <Input label="审核人" value={batchForm.reviewer} onChange={(e) => setBatchForm({ ...batchForm, reviewer: e.target.value })} />
          <Input label="收款人" value={batchForm.payee} onChange={(e) => setBatchForm({ ...batchForm, payee: e.target.value })} />
          <Input label="银行卡号" value={batchForm.bank_account} onChange={(e) => setBatchForm({ ...batchForm, bank_account: e.target.value })} />
          <Input label="开户行" value={batchForm.bank_name} onChange={(e) => setBatchForm({ ...batchForm, bank_name: e.target.value })} className="col-span-2" />
        </div>
        <div className="mt-6 flex justify-end gap-3">
          <Button variant="secondary" onClick={() => setEditBatchOpen(false)}>取消</Button>
          <Button onClick={handleSaveBatch}>保存</Button>
        </div>
      </Modal>

      {/* Add Manual Row Modal */}
      <Modal open={manualRowModalOpen} onClose={() => setManualRowModalOpen(false)} title="新增台账行" size="md">
        <div className="grid grid-cols-2 gap-4">
          <Input
            label="日期"
            type="date"
            value={manualRowForm.row_date}
            onChange={(e) => setManualRowForm({ ...manualRowForm, row_date: e.target.value })}
          />
          <Input
            label="事由"
            value={manualRowForm.expense_item}
            onChange={(e) => setManualRowForm({ ...manualRowForm, expense_item: e.target.value })}
            placeholder="如：奖金、劳务费"
            required
          />
          <Input
            label="金额"
            type="number"
            min={0.01}
            step={0.01}
            value={manualRowForm.row_amount || ''}
            onChange={(e) => {
              const v = Number(e.target.value);
              setManualRowForm({ ...manualRowForm, row_amount: v, advance_amount: v });
            }}
            placeholder="必填，> 0"
            required
          />
          <Input
            label="数量"
            type="number"
            min={1}
            step={1}
            value={manualRowForm.quantity}
            onChange={(e) => setManualRowForm({ ...manualRowForm, quantity: Number(e.target.value) })}
          />
          <Input
            label="垫款金额"
            type="number"
            min={0}
            step={0.01}
            value={manualRowForm.advance_amount}
            onChange={(e) => setManualRowForm({ ...manualRowForm, advance_amount: Number(e.target.value) })}
          />
          <Input
            label="备注"
            value={manualRowForm.remark}
            onChange={(e) => setManualRowForm({ ...manualRowForm, remark: e.target.value })}
          />
        </div>
        <div className="mt-1 text-xs text-gray-400">
          单价 = 金额 ÷ 数量，自动计算
        </div>
        <div className="mt-4 flex justify-end gap-3 border-t border-gray-200 pt-4">
          <Button variant="secondary" onClick={() => setManualRowModalOpen(false)}>取消</Button>
          <Button
            onClick={handleAddManualRow}
            disabled={!manualRowForm.expense_item.trim() || manualRowForm.row_amount <= 0}
          >
            添加
          </Button>
        </div>
      </Modal>

      {/* Edit Manual Row Modal */}
      <Modal open={editManualRowId !== null} onClose={() => setEditManualRowId(null)} title="编辑手动台账行" size="md">
        <div className="grid grid-cols-2 gap-4">
          <Input
            label="日期"
            type="date"
            value={editManualRowForm.row_date}
            onChange={(e) => setEditManualRowForm({ ...editManualRowForm, row_date: e.target.value })}
          />
          <Input
            label="事由"
            value={editManualRowForm.expense_item}
            onChange={(e) => setEditManualRowForm({ ...editManualRowForm, expense_item: e.target.value })}
          />
          <Input
            label="金额"
            type="number"
            min={0.01}
            step={0.01}
            value={editManualRowForm.row_amount || ''}
            onChange={(e) => setEditManualRowForm({ ...editManualRowForm, row_amount: Number(e.target.value) })}
          />
          <Input
            label="数量"
            type="number"
            min={1}
            step={1}
            value={editManualRowForm.quantity}
            onChange={(e) => setEditManualRowForm({ ...editManualRowForm, quantity: Number(e.target.value) })}
          />
          <Input
            label="垫款金额"
            type="number"
            min={0}
            step={0.01}
            value={editManualRowForm.advance_amount}
            onChange={(e) => setEditManualRowForm({ ...editManualRowForm, advance_amount: Number(e.target.value) })}
          />
          <Input
            label="备注"
            value={editManualRowForm.remark}
            onChange={(e) => setEditManualRowForm({ ...editManualRowForm, remark: e.target.value })}
          />
        </div>
        <div className="mt-4 flex justify-end gap-3 border-t border-gray-200 pt-4">
          <Button variant="secondary" onClick={() => setEditManualRowId(null)}>取消</Button>
          <Button onClick={handleSaveManualRow}>保存</Button>
        </div>
      </Modal>

      {/* Substitute Ticket Modal */}
      <SubstituteTicketModal
        open={substituteModalOpen}
        onClose={() => setSubstituteModalOpen(false)}
        batchId={batchId}
        ledgerRows={rows}
      />

      <PdfExportSettings
        open={pdfExportOpen}
        onClose={() => setPdfExportOpen(false)}
        invoices={rows.filter(r => r.invoice_id).map(r => ({ invoice_type: r.invoice_type }))}
        onExport={triggerPdfDownload}
      />
    </div>
  );
}
