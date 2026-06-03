import { useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useBatchStore } from '@/stores/batchStore';
import { useAuthStore } from '@/stores/authStore';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Modal } from '@/components/ui/Modal';
import { Plus, Download, Trash2, Filter } from 'lucide-react';
import { formatDate, formatCurrency } from '@/lib/utils';
import { batchesApi } from '@/api/batches';

function todayStr(): string {
  const d = new Date();
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
}

const emptyForm = {
  department: '',
  reporter: '',
  period_start: '',
  period_end: '',
  report_date: '',
  reviewer: '',
  payee: '',
  bank_account: '',
  bank_name: '',
};

export function BatchesPage() {
  const navigate = useNavigate();
  const { batches, loading, error, statusFilter, fetchBatches, createBatch, deleteBatch, setStatusFilter, clearError } = useBatchStore();
  const { user, fetchUser } = useAuthStore();
  const [createOpen, setCreateOpen] = useState(false);
  const [form, setForm] = useState(emptyForm);

  useEffect(() => {
    fetchBatches();
    if (!user) fetchUser();
  }, [fetchBatches, user, fetchUser]);

  const openCreateModal = useCallback(() => {
    setForm({
      department: user?.default_department || '',
      reporter: user?.default_reporter || '',
      period_start: '',
      period_end: '',
      report_date: todayStr(),
      reviewer: '',
      payee: user?.default_payee || '',
      bank_account: user?.default_bank_account || '',
      bank_name: user?.default_bank_name || '',
    });
    setCreateOpen(true);
  }, [user]);

  const handleCreate = useCallback(async () => {
    try {
      await createBatch({
        department: form.department,
        reporter: form.reporter || undefined,
        period_start: form.period_start || null,
        period_end: form.period_end || null,
        report_date: form.report_date || null,
        reviewer: form.reviewer || null,
        payee: form.payee || null,
        bank_account: form.bank_account || null,
        bank_name: form.bank_name || null,
      });
      setCreateOpen(false);
      setForm(emptyForm);
    } catch {
      // error handled in store
    }
  }, [form, createBatch]);

  const handleDelete = useCallback(async (e: React.MouseEvent, id: number) => {
    e.stopPropagation();
    if (!window.confirm('确定删除该批次吗？批次中的发票将被释放。')) return;
    await deleteBatch(id);
    await fetchBatches();
  }, [deleteBatch, fetchBatches]);

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h2 className="text-xl font-semibold text-gray-900">报销批次</h2>
          <div className="flex items-center gap-1 rounded-lg border border-gray-300 px-2 py-1">
            <Filter className="h-4 w-4 text-gray-400" />
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="border-none bg-transparent text-sm text-gray-700 focus:outline-none"
            >
              <option value="">全部状态</option>
              <option value="draft">草稿</option>
              <option value="completed">已完成</option>
              <option value="archived">已归档</option>
            </select>
          </div>
        </div>
        <Button onClick={openCreateModal}>
          <Plus className="mr-1 h-4 w-4" />
          新建批次
        </Button>
      </div>

      {error && (
        <div className="mb-4 rounded-md bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
          <button onClick={clearError} className="ml-2 underline">关闭</button>
        </div>
      )}

      {loading ? (
        <div className="flex items-center justify-center py-20">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-gray-200 border-t-blue-600" />
        </div>
      ) : batches.length === 0 ? (
        <div className="flex flex-col items-center justify-center rounded-lg border-2 border-dashed border-gray-300 py-20">
          <p className="mb-2 text-gray-500">暂无报销批次</p>
          <p className="mb-4 text-sm text-gray-400">点击上方按钮创建第一个批次</p>
          <Button onClick={openCreateModal}>
            <Plus className="mr-1 h-4 w-4" />
            新建批次
          </Button>
        </div>
      ) : (
        <div className="overflow-x-auto rounded-lg border border-gray-200">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-gray-200 bg-gray-50">
                <th className="px-4 py-3 font-medium text-gray-600">部门</th>
                <th className="px-4 py-3 font-medium text-gray-600">报账期间</th>
                <th className="px-4 py-3 font-medium text-gray-600">报账人</th>
                <th className="px-4 py-3 font-medium text-gray-600">发票数</th>
                <th className="px-4 py-3 font-medium text-gray-600">合计金额</th>
                <th className="px-4 py-3 font-medium text-gray-600">状态</th>
                <th className="px-4 py-3 font-medium text-gray-600">创建时间</th>
                <th className="px-4 py-3 font-medium text-gray-600">操作</th>
              </tr>
            </thead>
            <tbody>
              {batches.map((batch, idx) => (
                <tr
                  key={batch.id}
                  onClick={() => navigate(`/batches/${batch.id}`)}
                  className={`cursor-pointer border-b border-gray-100 hover:bg-gray-50 ${
                    idx % 2 === 0 ? 'bg-white' : 'bg-gray-50/50'
                  }`}
                >
                  <td className="px-4 py-3 text-gray-700">{batch.department}</td>
                  <td className="px-4 py-3 text-gray-700">
                    {batch.period_start ? `${batch.period_start} ~ ${batch.period_end}` : '-'}
                  </td>
                  <td className="px-4 py-3 text-gray-700">{batch.reporter}</td>
                  <td className="px-4 py-3 text-gray-700">{batch.invoice_count}</td>
                  <td className="px-4 py-3 font-medium text-gray-900">
                    {formatCurrency(batch.total_amount)}
                  </td>
                  <td className="px-4 py-3">
                    {batch.status === 'draft' ? (
                      <span className="inline-flex rounded-full bg-blue-100 px-2 py-0.5 text-xs font-medium text-blue-700">草稿</span>
                    ) : batch.status === 'completed' ? (
                      <span className="inline-flex rounded-full bg-green-100 px-2 py-0.5 text-xs font-medium text-green-700">已完成</span>
                    ) : batch.status === 'archived' ? (
                      <span className="inline-flex rounded-full bg-gray-200 px-2 py-0.5 text-xs font-medium text-gray-700">已归档</span>
                    ) : (
                      <span className="inline-flex rounded-full bg-blue-100 px-2 py-0.5 text-xs font-medium text-blue-700">{batch.status}</span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-gray-500">{formatDate(batch.created_at)}</td>
                  <td className="px-4 py-3">
                    <div className="flex gap-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={(e) => {
                          e.stopPropagation();
                          window.open(batchesApi.getExportExcelUrl(batch.id), '_blank');
                        }}
                      >
                        <Download className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={(e) => handleDelete(e, batch.id)}
                        className="text-red-500 hover:text-red-700"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <Modal open={createOpen} onClose={() => setCreateOpen(false)} title="新建报销批次" size="lg">
        <div className="grid grid-cols-2 gap-4">
          <Input label="部门" value={form.department} onChange={(e) => setForm({ ...form, department: e.target.value })} placeholder="请输入部门" />
          <Input label="报账人" value={form.reporter} onChange={(e) => setForm({ ...form, reporter: e.target.value })} placeholder="请输入报账人" />
          <Input label="报销开始日期" type="date" value={form.period_start} onChange={(e) => setForm({ ...form, period_start: e.target.value })} />
          <Input label="报销结束日期" type="date" value={form.period_end} onChange={(e) => setForm({ ...form, period_end: e.target.value })} />
          <Input label="报账日期" type="date" value={form.report_date} onChange={(e) => setForm({ ...form, report_date: e.target.value })} />
          <Input label="审核人" value={form.reviewer} onChange={(e) => setForm({ ...form, reviewer: e.target.value })} placeholder="请输入审核人" />
          <Input label="收款人" value={form.payee} onChange={(e) => setForm({ ...form, payee: e.target.value })} placeholder="请输入收款人" />
          <Input label="银行卡号" value={form.bank_account} onChange={(e) => setForm({ ...form, bank_account: e.target.value })} placeholder="请输入银行卡号" />
          <Input label="开户行" value={form.bank_name} onChange={(e) => setForm({ ...form, bank_name: e.target.value })} placeholder="请输入开户行" className="col-span-2" />
        </div>
        <div className="mt-6 flex justify-end gap-3">
          <Button variant="secondary" onClick={() => setCreateOpen(false)}>取消</Button>
          <Button onClick={handleCreate} disabled={!form.department}>创建</Button>
        </div>
      </Modal>
    </div>
  );
}
