import { useState, useEffect, useCallback } from 'react';
import { useAuthStore } from '@/stores/authStore';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Save } from 'lucide-react';

export function UserSettingsPage() {
  const { user, fetchUser, updateDefaults } = useAuthStore();
  const [form, setForm] = useState({
    default_department: '',
    default_reporter: '',
    default_payee: '',
    default_bank_account: '',
    default_bank_name: '',
  });
  const [saved, setSaved] = useState(false);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!user) {
      fetchUser();
    } else {
      setForm({
        default_department: user.default_department || '',
        default_reporter: user.default_reporter || '',
        default_payee: user.default_payee || '',
        default_bank_account: user.default_bank_account || '',
        default_bank_name: user.default_bank_name || '',
      });
    }
  }, [user, fetchUser]);

  const handleSave = useCallback(async () => {
    setSaving(true);
    setSaved(false);
    try {
      await updateDefaults({
        default_department: form.default_department || null,
        default_reporter: form.default_reporter || null,
        default_payee: form.default_payee || null,
        default_bank_account: form.default_bank_account || null,
        default_bank_name: form.default_bank_name || null,
      });
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } catch {
      // error handled by store
    } finally {
      setSaving(false);
    }
  }, [form, updateDefaults]);

  return (
    <div>
      <h2 className="mb-6 text-xl font-semibold text-gray-900">账号设置</h2>

      <div className="max-w-lg rounded-lg border border-gray-200 bg-white p-6">
        <h3 className="mb-4 text-base font-medium text-gray-800">报销默认值</h3>
        <p className="mb-6 text-sm text-gray-500">
          设置后，新建报销批次时将自动填充以下信息。
        </p>

        <div className="flex flex-col gap-4">
          <Input
            label="默认报账部门"
            value={form.default_department}
            onChange={(e) => setForm({ ...form, default_department: e.target.value })}
            placeholder="请输入报账部门"
          />
          <Input
            label="默认报账人"
            value={form.default_reporter}
            onChange={(e) => setForm({ ...form, default_reporter: e.target.value })}
            placeholder="请输入报账人姓名"
          />
          <Input
            label="默认收款人"
            value={form.default_payee}
            onChange={(e) => setForm({ ...form, default_payee: e.target.value })}
            placeholder="请输入收款人姓名"
          />
          <Input
            label="默认银行卡号"
            value={form.default_bank_account}
            onChange={(e) => setForm({ ...form, default_bank_account: e.target.value })}
            placeholder="请输入银行卡号"
          />
          <Input
            label="默认开户行"
            value={form.default_bank_name}
            onChange={(e) => setForm({ ...form, default_bank_name: e.target.value })}
            placeholder="请输入开户行名称"
          />
        </div>

        <div className="mt-6 flex items-center gap-3">
          <Button onClick={handleSave} disabled={saving}>
            <Save className="mr-1 h-4 w-4" />
            {saving ? '保存中...' : '保存'}
          </Button>
          {saved && (
            <span className="text-sm text-green-600">保存成功</span>
          )}
        </div>
      </div>
    </div>
  );
}
