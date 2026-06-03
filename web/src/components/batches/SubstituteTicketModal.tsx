import { useEffect, useState, useCallback } from 'react';
import { Modal } from '@/components/ui/Modal';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { useBatchStore } from '@/stores/batchStore';
import { formatDate, formatCurrency } from '@/lib/utils';
import { Search, Plus, Link2, Trash2 } from 'lucide-react';
import type { SubstituteInvoiceItem, SubstituteRelationResponse, LedgerRow } from '@/types/batch';

type TabKey = 'list' | 'create';

const MODE_LABELS: Record<string, string> = {
  one_to_one: '一对一替换',
  one_to_many: '一对多拆分',
  many_to_one: '多对一合并',
};

const MODE_HINTS: Record<string, string> = {
  one_to_one: '选择 1 个被替换行 + 1 张替票发票',
  one_to_many: '选择 1 张替票发票 → 拆给多笔费用',
  many_to_one: '选择多张替票发票 → 合并覆盖一笔费用',
};

interface Props {
  open: boolean;
  onClose: () => void;
  batchId: number;
  ledgerRows: LedgerRow[];
}

export function SubstituteTicketModal({ open, onClose, batchId, ledgerRows }: Props) {
  const {
    substituteInvoices,
    substituteTotal,
    substitutePage,
    substitutions,
    fetchSubstituteInvoices,
    fetchSubstitutions,
    createSubstitution,
    removeSubstitution,
  } = useBatchStore();

  const [tab, setTab] = useState<TabKey>('list');
  const [mode, setMode] = useState<string>('one_to_one');
  const [selectedInvoices, setSelectedInvoices] = useState<SubstituteInvoiceItem[]>([]);
  const [selectedRows, setSelectedRows] = useState<LedgerRow[]>([]);
  const [invKeyword, setInvKeyword] = useState('');
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    if (open) {
      fetchSubstitutions(batchId);
      fetchSubstituteInvoices(batchId, { page: 1, page_size: 50 });
    }
  }, [open, batchId, fetchSubstitutions, fetchSubstituteInvoices]);

  const resetCreate = useCallback(() => {
    setMode('one_to_one');
    setSelectedInvoices([]);
    setSelectedRows([]);
    setInvKeyword('');
  }, []);

  const handleInvSearch = useCallback(() => {
    fetchSubstituteInvoices(batchId, { keyword: invKeyword || undefined, page: 1, page_size: 50 });
  }, [batchId, invKeyword, fetchSubstituteInvoices]);

  const handleInvPageChange = useCallback((newPage: number) => {
    fetchSubstituteInvoices(batchId, { keyword: invKeyword || undefined, page: newPage, page_size: 50 });
  }, [batchId, invKeyword, fetchSubstituteInvoices]);

  const toggleInvoice = useCallback((inv: SubstituteInvoiceItem) => {
    setSelectedInvoices((prev) => {
      const exists = prev.find((i) => i.id === inv.id);
      if (exists) return prev.filter((i) => i.id !== inv.id);
      if (mode === 'one_to_one' || mode === 'one_to_many') return [inv];
      return [...prev, inv];
    });
  }, [mode]);

  const toggleRow = useCallback((row: LedgerRow) => {
    setSelectedRows((prev) => {
      const exists = prev.find((r) => r.id === row.id);
      if (exists) return prev.filter((r) => r.id !== row.id);
      if (mode === 'one_to_one' || mode === 'many_to_one') return [row];
      return [...prev, row];
    });
  }, [mode]);

  const handleCreate = useCallback(async () => {
    setCreating(true);
    try {
      await createSubstitution(batchId, {
        mode: mode as 'one_to_one' | 'one_to_many' | 'many_to_one',
        substitute_invoice_ids: selectedInvoices.map((i) => i.id),
        target_row_ids: selectedRows.map((r) => r.id),
      });
      resetCreate();
      setTab('list');
    } catch {
      // error handled in store
    } finally {
      setCreating(false);
    }
  }, [batchId, mode, selectedInvoices, selectedRows, createSubstitution, resetCreate]);

  const handleRemove = useCallback(async (subId: number) => {
    await removeSubstitution(batchId, subId);
  }, [batchId, removeSubstitution]);

  const substitutedInvoicesTotal = selectedInvoices.reduce((s, inv) => s + inv.remaining_amount, 0);
  const targetRowsTotal = selectedRows.reduce((s, r) => s + (r.amount ?? r.unit_price * r.quantity), 0);

  const canCreate = selectedInvoices.length > 0 && selectedRows.length > 0;

  const totalPages = Math.max(1, Math.ceil(substituteTotal / 50));

  return (
    <Modal open={open} onClose={() => { resetCreate(); onClose(); }} title="替票管理" size="xl">
      <div className="mb-4 flex gap-2 border-b border-gray-200">
        <button
          className={`px-4 py-2 text-sm font-medium ${tab === 'list' ? 'border-b-2 border-blue-600 text-blue-600' : 'text-gray-500 hover:text-gray-700'}`}
          onClick={() => setTab('list')}
        >
          <Link2 className="mr-1 inline h-4 w-4" />已有关联
          {substitutions.length > 0 && (
            <span className="ml-1 rounded-full bg-blue-100 px-1.5 py-0.5 text-xs text-blue-700">
              {substitutions.length}
            </span>
          )}
        </button>
        <button
          className={`px-4 py-2 text-sm font-medium ${tab === 'create' ? 'border-b-2 border-blue-600 text-blue-600' : 'text-gray-500 hover:text-gray-700'}`}
          onClick={() => setTab('create')}
        >
          <Plus className="mr-1 inline h-4 w-4" />新建替票
        </button>
      </div>

      {tab === 'list' ? (
        <div>
          {substitutions.length === 0 ? (
            <p className="py-12 text-center text-gray-400">
              <Link2 className="mx-auto mb-2 h-8 w-8 opacity-30" />
              暂无替票关联，点击"新建替票"开始
            </p>
          ) : (
            <div className="max-h-80 overflow-y-auto">
              <table className="w-full text-left text-sm">
                <thead className="sticky top-0 bg-white">
                  <tr className="border-b border-gray-200">
                    <th className="px-4 py-2 font-medium text-gray-600">被替换行</th>
                    <th className="px-4 py-2 font-medium text-gray-600">替票发票</th>
                    <th className="px-4 py-2 font-medium text-gray-600">模式</th>
                    <th className="px-4 py-2 font-medium text-gray-600">创建时间</th>
                    <th className="px-4 py-2 font-medium text-gray-600">操作</th>
                  </tr>
                </thead>
                <tbody>
                  {substitutions.map((rel: SubstituteRelationResponse) => (
                    <tr key={rel.id} className="border-b border-gray-100 hover:bg-gray-50">
                      <td className="px-4 py-2 text-gray-700">
                        <span>{rel.target_row.expense_item || '-'}</span>
                        <span className="ml-1 text-gray-400">
                          {rel.target_row.row_amount != null ? formatCurrency(rel.target_row.row_amount) : ''}
                        </span>
                      </td>
                      <td className="px-4 py-2 text-gray-700">
                        <span className="font-mono text-blue-600">{rel.substitute_invoice.invoice_no}</span>
                        <span className="ml-1 text-gray-400">
                          {formatCurrency(rel.substitute_invoice.amount)}
                        </span>
                      </td>
                      <td className="px-4 py-2">
                        <span className="rounded bg-gray-100 px-2 py-0.5 text-xs text-gray-600">
                          {MODE_LABELS[rel.mode] || rel.mode}
                        </span>
                      </td>
                      <td className="px-4 py-2 text-gray-500">{rel.created_at ? formatDate(rel.created_at) : '-'}</td>
                      <td className="px-4 py-2">
                        <Button
                          variant="ghost"
                          size="sm"
                          className="text-red-500 hover:text-red-700"
                          onClick={() => handleRemove(rel.id)}
                        >
                          <Trash2 className="h-4 w-4" /> 解除
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      ) : (
        <div>
          <div className="mb-4">
            <label className="mb-2 block text-sm font-medium text-gray-700">替票模式</label>
            <div className="flex gap-2">
              {Object.entries(MODE_LABELS).map(([key, label]) => (
                <button
                  key={key}
                  className={`rounded-lg border px-4 py-2 text-sm transition ${mode === key ? 'border-blue-500 bg-blue-50 text-blue-700' : 'border-gray-200 text-gray-600 hover:border-gray-300'}`}
                  onClick={() => { setMode(key); setSelectedInvoices([]); setSelectedRows([]); }}
                >
                  {label}
                </button>
              ))}
            </div>
            <p className="mt-1 text-xs text-gray-400">{MODE_HINTS[mode]}</p>
          </div>

          <div className="grid grid-cols-2 gap-6">
            <div>
              <h4 className="mb-2 text-sm font-medium text-gray-700">
                选择被替换行
                {selectedRows.length > 0 && (
                  <span className="ml-1 rounded bg-blue-100 px-1.5 py-0.5 text-xs text-blue-700">
                    {selectedRows.length} 行 / 合计 {formatCurrency(targetRowsTotal)}
                  </span>
                )}
              </h4>
              <div className="max-h-64 overflow-y-auto rounded-lg border border-gray-200">
                <table className="w-full text-left text-xs">
                  <thead className="sticky top-0 bg-gray-50">
                    <tr className="border-b border-gray-200">
                      <th className="w-8 px-2 py-1.5" />
                      <th className="px-2 py-1.5 font-medium text-gray-600">事由</th>
                      <th className="px-2 py-1.5 font-medium text-gray-600">金额</th>
                      <th className="px-2 py-1.5 font-medium text-gray-600">类型</th>
                    </tr>
                  </thead>
                  <tbody>
                    {ledgerRows.filter((r) => !r.invoice_id && !r.is_substitute).map((row) => (
                      <tr
                        key={row.id}
                        className={`cursor-pointer border-b border-gray-100 hover:bg-gray-50 ${selectedRows.find((r) => r.id === row.id) ? 'bg-blue-50' : ''}`}
                        onClick={() => toggleRow(row)}
                      >
                        <td className="px-2 py-1.5">
                          <input
                            type="checkbox"
                            checked={!!selectedRows.find((r) => r.id === row.id)}
                            onChange={() => toggleRow(row)}
                            className="h-3.5 w-3.5 rounded border-gray-300"
                          />
                        </td>
                        <td className="px-2 py-1.5 text-gray-700">
                          {row.expense_item || row.category || '-'}
                          {row.is_substitute && (
                            <span className="ml-1 text-orange-500">(已替)</span>
                          )}
                        </td>
                        <td className="px-2 py-1.5 text-gray-700">
                          {row.amount != null ? formatCurrency(row.amount) : '-'}
                        </td>
                        <td className="px-2 py-1.5">
                          <span className="rounded bg-yellow-100 px-1.5 py-0.5 text-xs text-yellow-700">手动</span>
                        </td>
                      </tr>
                    ))}
                    {ledgerRows.filter((r) => !r.invoice_id && !r.is_substitute).length === 0 && (
                      <tr>
                        <td colSpan={4} className="px-4 py-8 text-center text-gray-400">
                          暂无可选台账行
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>

            <div>
              <h4 className="mb-2 text-sm font-medium text-gray-700">
                选择替票发票
                {selectedInvoices.length > 0 && (
                  <span className="ml-1 rounded bg-green-100 px-1.5 py-0.5 text-xs text-green-700">
                    {selectedInvoices.length} 张 / 可用 {formatCurrency(substitutedInvoicesTotal)}
                  </span>
                )}
              </h4>
              <div className="mb-2 flex gap-1">
                <Input
                  placeholder="搜索发票号..."
                  value={invKeyword}
                  onChange={(e) => setInvKeyword(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleInvSearch()}
                  className="flex-1 text-xs"
                />
                <Button variant="secondary" size="sm" onClick={handleInvSearch}>
                  <Search className="h-3 w-3" />
                </Button>
              </div>
              <div className="max-h-56 overflow-y-auto rounded-lg border border-gray-200">
                <table className="w-full text-left text-xs">
                  <thead className="sticky top-0 bg-gray-50">
                    <tr className="border-b border-gray-200">
                      <th className="w-8 px-2 py-1.5" />
                      <th className="px-2 py-1.5 font-medium text-gray-600">发票号</th>
                      <th className="px-2 py-1.5 font-medium text-gray-600">金额</th>
                      <th className="px-2 py-1.5 font-medium text-gray-600">剩余</th>
                    </tr>
                  </thead>
                  <tbody>
                    {substituteInvoices.map((inv) => (
                      <tr
                        key={inv.id}
                        className={`cursor-pointer border-b border-gray-100 hover:bg-gray-50 ${selectedInvoices.find((i) => i.id === inv.id) ? 'bg-blue-50' : ''}`}
                        onClick={() => toggleInvoice(inv)}
                      >
                        <td className="px-2 py-1.5">
                          <input
                            type="checkbox"
                            checked={!!selectedInvoices.find((i) => i.id === inv.id)}
                            onChange={() => toggleInvoice(inv)}
                            className="h-3.5 w-3.5 rounded border-gray-300"
                          />
                        </td>
                        <td className="px-2 py-1.5 font-mono text-blue-600">{inv.invoice_no || '-'}</td>
                        <td className="px-2 py-1.5 text-gray-700">{formatCurrency(inv.amount)}</td>
                        <td className="px-2 py-1.5">
                          <span className={inv.remaining_amount <= 0 ? 'text-red-500' : 'text-green-600'}>
                            {formatCurrency(inv.remaining_amount)}
                          </span>
                        </td>
                      </tr>
                    ))}
                    {substituteInvoices.length === 0 && (
                      <tr>
                        <td colSpan={4} className="px-4 py-8 text-center text-gray-400">
                          暂无可选替票发票
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
              {totalPages > 1 && (
                <div className="mt-1 flex justify-center gap-1 text-xs text-gray-500">
                  <button
                    disabled={substitutePage <= 1}
                    onClick={() => handleInvPageChange(substitutePage - 1)}
                    className="disabled:opacity-30"
                  >
                    &lt;
                  </button>
                  <span>{substitutePage} / {totalPages}</span>
                  <button
                    disabled={substitutePage >= totalPages}
                    onClick={() => handleInvPageChange(substitutePage + 1)}
                    className="disabled:opacity-30"
                  >
                    &gt;
                  </button>
                </div>
              )}
            </div>
          </div>

          {substitutedInvoicesTotal > 0 && targetRowsTotal > 0 && substitutedInvoicesTotal < targetRowsTotal && (
            <div className="mt-3 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">
              替票可用金额（{formatCurrency(substitutedInvoicesTotal)}）不足以覆盖被替换行金额（{formatCurrency(targetRowsTotal)}）
            </div>
          )}

          <div className="mt-4 flex justify-end gap-3 border-t border-gray-200 pt-4">
            <Button variant="secondary" onClick={resetCreate}>重置</Button>
            <Button
              onClick={handleCreate}
              disabled={!canCreate || creating || substitutedInvoicesTotal < targetRowsTotal}
            >
              {creating ? '创建中...' : '确认替票关联'}
            </Button>
          </div>
        </div>
      )}
    </Modal>
  );
}