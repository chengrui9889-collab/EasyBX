import type { ReimbursementItem } from '@/types/export';
import { splitAmountToDigits, amountToChinese } from '@/lib/utils';

interface ReimbursementFormProps {
  department: string;
  reportDate: string | null;
  reporter: string;
  items: ReimbursementItem[];
  pageIndex: number;
  totalPages: number;
}

const ROWS_PER_PAGE = 6;

const AMOUNT_LABELS = ['百万', '十万', '万', '千', '百', '十', '元', '角', '分'];

export function ReimbursementForm({
  department,
  reportDate,
  reporter,
  items,
  pageIndex,
  totalPages,
}: ReimbursementFormProps) {
  const totalAmount = items.reduce((sum, item) => sum + item.amount, 0);
  const emptyRows = Math.max(0, ROWS_PER_PAGE - items.length);

  const formatReportDate = (dateStr: string | null): string => {
    if (!dateStr) return '＿年＿月＿日';
    const d = new Date(dateStr);
    return `${d.getFullYear()}年${d.getMonth() + 1}月${d.getDate()}日`;
  };

  return (
    <div className="mx-auto mb-8 bg-white p-8 shadow-lg print:shadow-none print:mb-0 print:p-0"
      style={{
        width: '210mm',
        minHeight: '297mm',
      }}
    >
      <div className="mb-4 text-center">
        <h1 className="inline-block border-b-2 border-double border-gray-800 pb-1 text-2xl font-bold tracking-widest text-gray-900"
          style={{ borderBottomWidth: '3px', borderBottomStyle: 'double' }}
        >
          费用报销单
        </h1>
      </div>

      <div className="mb-3 flex items-end justify-between text-sm">
        <span className="text-gray-700">
          报销部门：<span className="underline decoration-gray-400 underline-offset-2">{department}</span>
        </span>
        <div className="flex gap-4">
          <span className="text-gray-700">{formatReportDate(reportDate)}</span>
          <span className="text-gray-700">单据及附件共<span className="mx-1 underline decoration-gray-400">{'＿'}</span>页</span>
        </div>
      </div>

      <table className="w-full border-collapse border border-gray-400 text-xs">
        <thead>
          <tr className="border-b border-gray-400">
            <th className="w-10 border-r border-gray-400 py-2 text-center font-medium text-gray-700">序号</th>
            <th className="border-r border-gray-400 px-2 py-2 text-center font-medium text-gray-700">报销项目</th>
            <th className="w-24 border-r border-gray-400 py-2 text-center font-medium text-gray-700">摘要</th>
            {AMOUNT_LABELS.map((label, idx) => (
              <th
                key={idx}
                className={`w-7 py-2 text-center font-medium text-gray-700 ${
                  idx < AMOUNT_LABELS.length - 1 ? 'border-r border-gray-300' : ''
                }`}
              >
                {label}
              </th>
            ))}
            <th className="border-l border-gray-400 px-2 py-2 text-center font-medium text-gray-700" colSpan={5}>
              备注
            </th>
          </tr>
        </thead>
        <tbody>
          {items.map((item, idx) => {
            const digits = splitAmountToDigits(item.amount);
            return (
              <tr key={idx} className="border-b border-gray-300">
                <td className="border-r border-gray-400 py-1.5 text-center text-gray-700">{idx + 1}</td>
                <td className="border-r border-gray-400 px-2 py-1.5 text-gray-800">{item.expense_item}</td>
                <td className="border-r border-gray-400 py-1.5" />
                {digits.map((digit, dIdx) => (
                  <td
                    key={dIdx}
                    className={`py-1.5 text-center text-gray-800 ${
                      dIdx < digits.length - 1 ? 'border-r border-gray-300' : ''
                    }`}
                  >
                    {digit ?? ''}
                  </td>
                ))}
                <td className="border-l border-gray-400 py-1.5" colSpan={5} />
              </tr>
            );
          })}

          {Array.from({ length: emptyRows }).map((_, idx) => (
            <tr key={`empty-${idx}`} className="border-b border-gray-300">
              <td className="border-r border-gray-400 py-4 text-center text-gray-400">
                {items.length + idx + 1}
              </td>
              <td className="border-r border-gray-400 py-4" />
              <td className="border-r border-gray-400 py-4" />
              {AMOUNT_LABELS.map((_, dIdx) => (
                <td
                  key={dIdx}
                  className={`py-4 ${
                    dIdx < AMOUNT_LABELS.length - 1 ? 'border-r border-gray-300' : ''
                  }`}
                />
              ))}
              <td className="border-l border-gray-400 py-4" colSpan={5} />
            </tr>
          ))}

          <tr className="border-t-2 border-gray-500">
            <td className="border-r border-gray-400 py-2 text-center text-gray-700" />
            <td colSpan={2} className="border-r border-gray-400 py-2 text-center font-medium text-gray-800">
              合&nbsp;&nbsp;&nbsp;&nbsp;计
            </td>
            {splitAmountToDigits(totalAmount).map((digit, dIdx) => (
              <td
                key={dIdx}
                className={`py-2 text-center font-medium text-gray-900 ${
                  dIdx < AMOUNT_LABELS.length - 1 ? 'border-r border-gray-300' : ''
                }`}
              >
                {digit ?? ''}
              </td>
            ))}
            <td className="border-l border-gray-400 py-2" colSpan={5} />
          </tr>
        </tbody>
      </table>

      <div className="mt-3 flex border-t-2 border-gray-500 pt-2 text-xs">
        <div className="flex-1">
          <div className="mb-1 flex items-center gap-1">
            <span className="text-gray-700">
              金额（大写）：<span className="font-medium text-gray-900">{amountToChinese(totalAmount)}</span>
            </span>
          </div>

          <div className="mt-3 grid grid-cols-2 gap-x-8 gap-y-1.5">
            <div className="flex items-center gap-1">
              <span className="text-gray-600">原借款：</span>
              <span className="flex-1 border-b border-gray-400" />
            </div>
            <div className="flex items-center gap-1">
              <span className="text-gray-600">应退（补）款：</span>
              <span className="flex-1 border-b border-gray-400" />
            </div>
          </div>
        </div>

        <div className="flex w-32 flex-col items-center border-l border-gray-400 pl-4">
          <div className="flex items-center gap-1 text-sm font-medium">
            <span className="text-gray-700">报销人：</span>
            <span className="text-gray-900">{reporter}</span>
          </div>
        </div>
      </div>

      <div className="mt-6 grid grid-cols-4 gap-4 border-t border-gray-400 pt-3 text-xs">
        <div className="flex flex-col items-center">
          <span className="mb-2 font-medium text-gray-700">领导审批</span>
          <div className="h-12 w-full border-b border-gray-400" />
        </div>
        <div className="flex flex-col items-center">
          <span className="mb-2 font-medium text-gray-700">会计主管</span>
          <div className="h-12 w-full border-b border-gray-400" />
        </div>
        <div className="flex flex-col items-center">
          <span className="mb-2 font-medium text-gray-700">复核</span>
          <div className="h-12 w-full border-b border-gray-400" />
        </div>
        <div className="flex flex-col items-center">
          <span className="mb-2 font-medium text-gray-700">出纳</span>
          <div className="h-12 w-full border-b border-gray-400" />
        </div>
      </div>

      <div className="mt-2 text-right text-xs text-gray-400">
        第 {pageIndex} 页 / 共 {totalPages} 页
      </div>
    </div>
  );
}