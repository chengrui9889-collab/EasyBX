import { useState, useMemo, useCallback, useEffect } from 'react';
import { Button } from '@/components/ui/Button';
import { Modal } from '@/components/ui/Modal';
import { cn } from '@/lib/utils';

type LayoutValue = 'portrait' | 'landscape';

interface PdfExportSettingsProps {
  open: boolean;
  onClose: () => void;
  invoices: { invoice_type: string | null }[];
  onExport: (layouts: Record<string, LayoutValue>) => Promise<void>;
}

const LAYOUT_OPTIONS: { value: LayoutValue; label: string }[] = [
  { value: 'portrait', label: '纵向（一页2张）' },
  { value: 'landscape', label: '横向（一页4张）' },
];

export function PdfExportSettings({ open, onClose, invoices, onExport }: PdfExportSettingsProps) {
  const [loading, setLoading] = useState(false);
  const [layouts, setLayouts] = useState<Record<string, LayoutValue>>({});

  const groups = useMemo(() => {
    const map = new Map<string, number>();
    for (const inv of invoices) {
      const t = inv.invoice_type || '其他';
      map.set(t, (map.get(t) || 0) + 1);
    }
    return Array.from(map.entries()).map(([type, count]) => ({ type, count }));
  }, [invoices]);

  useEffect(() => {
    if (open) {
      const defaults: Record<string, LayoutValue> = {};
      for (const g of groups) {
        defaults[g.type] = 'portrait';
      }
      setLayouts(defaults);
      setLoading(false);
    }
  }, [open, groups]);

  const handleClose = useCallback(() => {
    if (!loading) onClose();
  }, [loading, onClose]);

  const setAll = useCallback((value: LayoutValue) => {
    setLayouts((prev) => {
      const next = { ...prev };
      for (const key of Object.keys(next)) {
        next[key] = value;
      }
      return next;
    });
  }, []);

  const handleExport = useCallback(async () => {
    setLoading(true);
    try {
      await onExport(layouts);
      onClose();
    } catch {
      setLoading(false);
    }
  }, [layouts, onExport, onClose]);

  if (groups.length === 0) {
    return (
      <Modal open={open} onClose={handleClose} title="导出 PDF 设置" size="md">
        <p className="py-8 text-center text-gray-400">无发票可导出</p>
        <div className="flex justify-end gap-3 border-t border-gray-200 pt-4">
          <Button variant="secondary" onClick={handleClose}>关闭</Button>
        </div>
      </Modal>
    );
  }

  return (
    <Modal open={open} onClose={handleClose} title="导出 PDF 设置" size="md">
      {groups.length > 1 && (
        <div className="mb-4 flex gap-2">
          <Button variant="secondary" size="sm" onClick={() => setAll('portrait')}>
            统一设为纵向
          </Button>
          <Button variant="secondary" size="sm" onClick={() => setAll('landscape')}>
            统一设为横向
          </Button>
        </div>
      )}

      <div className="space-y-3">
        {groups.map(({ type, count }) => (
          <div
            key={type}
            className="flex items-center justify-between rounded-lg border border-gray-200 px-4 py-3"
          >
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium text-gray-900">{type}</span>
              <span className="rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-500">
                {count} 张
              </span>
            </div>
            <select
              value={layouts[type] || 'portrait'}
              onChange={(e) =>
                setLayouts((prev) => ({ ...prev, [type]: e.target.value as LayoutValue }))
              }
              className={cn(
                'rounded-md border border-gray-300 bg-white px-3 py-1.5 text-sm text-gray-700',
                'focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500',
              )}
            >
              {LAYOUT_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </div>
        ))}
      </div>

      <div className="mt-6 flex justify-end gap-3 border-t border-gray-200 pt-4">
        <Button variant="secondary" onClick={handleClose} disabled={loading}>
          取消
        </Button>
        <Button onClick={handleExport} disabled={loading}>
          {loading ? '导出中...' : '确认导出'}
        </Button>
      </div>
    </Modal>
  );
}