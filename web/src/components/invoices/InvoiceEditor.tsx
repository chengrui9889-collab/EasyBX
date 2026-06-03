import { useForm } from 'react-hook-form';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';
import type { Invoice, UpdateInvoiceRequest } from '@/types/invoice';

interface InvoiceEditorProps {
  invoice: Invoice;
  onSave: (data: UpdateInvoiceRequest) => Promise<void>;
  onConfirm: () => Promise<void>;
  onDelete: () => void;
  saving?: boolean;
}

const TYPE_FIELDS: Record<
  string,
  Array<{ key: keyof Invoice; label: string }>
> = {
  '增值税': [],
  '高铁': [
    { key: 'train_no', label: '车次' },
    { key: 'departure_station', label: '出发站' },
    { key: 'arrival_station', label: '到达站' },
  ],
  '滴滴': [
    { key: 'departure_location', label: '出发地' },
    { key: 'arrival_location', label: '目的地' },
  ],
  '飞机': [
    { key: 'flight_no', label: '航班号' },
    { key: 'departure_city', label: '出发城市' },
    { key: 'arrival_city', label: '到达城市' },
  ],
};

const statusEditable = (status: string) =>
  status === 'pending' || status === 'failed' || status === 'confirmed';

const canConfirmFn = (date: string | null, amount: number | null) =>
  !!date && (amount ?? 0) > 0;

type FormData = {
  invoice_no: string;
  amount: string;
  invoice_date: string;
  category: string;
  vendor: string;
  buyer_name: string;
  invoice_type: string;
  project_name: string;
  train_no: string;
  departure_station: string;
  arrival_station: string;
  departure_location: string;
  arrival_location: string;
  flight_no: string;
  departure_city: string;
  arrival_city: string;
  remark: string;
};

export function InvoiceEditor({
  invoice,
  onSave,
  onConfirm,
  onDelete,
  saving = false,
}: InvoiceEditorProps) {
  const { register, handleSubmit, watch, formState } = useForm<FormData>({
    defaultValues: {
      invoice_no: invoice.invoice_no || '',
      amount: invoice.amount != null ? String(invoice.amount) : '',
      invoice_date: invoice.invoice_date || '',
      category: invoice.category || '',
      vendor: invoice.vendor || '',
      buyer_name: invoice.buyer_name || '',
      invoice_type: invoice.invoice_type || '',
      project_name: invoice.project_name || '',
      train_no: invoice.train_no || '',
      departure_station: invoice.departure_station || '',
      arrival_station: invoice.arrival_station || '',
      departure_location: invoice.departure_location || '',
      arrival_location: invoice.arrival_location || '',
      flight_no: invoice.flight_no || '',
      departure_city: invoice.departure_city || '',
      arrival_city: invoice.arrival_city || '',
      remark: invoice.remark || '',
    },
  });

  const watchedDate = watch('invoice_date');
  const watchedAmount = watch('amount');
  const watchedType = watch('invoice_type');

  const isProcessing = invoice.status === 'processing';
  const isConfirmed = invoice.status === 'confirmed';
  const readonly = !statusEditable(invoice.status);
  const canConfirm = !isConfirmed && canConfirmFn(watchedDate, Number(watchedAmount));
  const extraFields = TYPE_FIELDS[watchedType] || [];

  const onSubmit = async (data: FormData) => {
    await onSave({
      invoice_no: data.invoice_no || null,
      amount: data.amount ? Number(data.amount) : null,
      invoice_date: data.invoice_date || null,
      category: data.category || null,
      vendor: data.vendor || null,
      buyer_name: data.buyer_name || null,
      invoice_type: data.invoice_type || null,
      project_name: data.project_name || null,
      train_no: data.train_no || null,
      departure_station: data.departure_station || null,
      arrival_station: data.arrival_station || null,
      departure_location: data.departure_location || null,
      arrival_location: data.arrival_location || null,
      flight_no: data.flight_no || null,
      departure_city: data.departure_city || null,
      arrival_city: data.arrival_city || null,
      remark: data.remark || null,
    });
  };

  return (
    <div>
      {isProcessing && (
        <div className="mb-4 rounded-md bg-blue-50 px-4 py-3 text-sm text-blue-700">
          发票正在识别中，请稍候...
        </div>
      )}

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <Input
            label="发票号码"
            readOnly={readonly}
            {...register('invoice_no')}
          />
          <Input
            label="开票日期"
            type="date"
            readOnly={readonly}
            {...register('invoice_date')}
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <Input
            label="金额"
            type="number"
            step="0.01"
            readOnly={readonly}
            {...register('amount')}
          />
          <Input
            label="发票类型"
            readOnly={readonly}
            {...register('invoice_type')}
          />
        </div>

        <div className="space-y-1">
          <label className="block text-sm font-medium text-gray-700">报销类型</label>
          <select
            className="block w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 disabled:cursor-not-allowed disabled:bg-gray-50 disabled:text-gray-500"
            disabled={readonly}
            {...register('category')}
          >
            <option value="">-- 请选择 --</option>
            <option value="交通费">交通费</option>
            <option value="住宿费">住宿费</option>
            <option value="打车费">打车费</option>
            <option value="打印费">打印费</option>
            <option value="餐饮费">餐饮费</option>
            <option value="办公费">办公费</option>
            <option value="快递费">快递费</option>
          </select>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <Input
            label="销售方名称"
            readOnly={readonly}
            {...register('vendor')}
          />
          <Input
            label="购买方名称"
            readOnly={readonly}
            {...register('buyer_name')}
          />
        </div>

        <Input
          label="项目名称"
          readOnly={readonly}
          {...register('project_name')}
        />

        {extraFields.length > 0 && (
          <div className="rounded-md border border-gray-200 bg-gray-50 p-3">
            <p className="mb-2 text-xs font-medium text-gray-500">
              {watchedType} 特有字段
            </p>
            <div className="grid grid-cols-2 gap-4">
              {extraFields.map((field) => (
                <Input
                  key={field.key}
                  label={field.label}
                  readOnly={readonly}
                  {...register(field.key as keyof FormData)}
                />
              ))}
            </div>
          </div>
        )}

        <Input
          label="报销说明"
          readOnly={readonly}
          {...register('remark')}
        />

        <div className="flex items-center gap-3 border-t border-gray-200 pt-4">
          {isConfirmed && (
            <Button type="button" variant="secondary" disabled>
              已入库
            </Button>
          )}

          {!isProcessing && (
            <Button type="submit" variant="primary" disabled={saving || formState.isSubmitting}>
              {saving || formState.isSubmitting ? '保存中...' : '保存'}
            </Button>
          )}

          {!isConfirmed && !isProcessing && (
            <Button
              type="button"
              variant="primary"
              disabled={!canConfirm}
              onClick={onConfirm}
              title={
                !canConfirm
                  ? !watchedDate
                    ? '请填写发票日期'
                    : '金额必须大于 0'
                  : undefined
              }
            >
              确认入库
            </Button>
          )}

          <div className="flex-1" />

          <Button type="button" variant="danger" onClick={onDelete}>
            删除
          </Button>
        </div>
      </form>
    </div>
  );
}