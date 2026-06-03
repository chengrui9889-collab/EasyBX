import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { exportsApi } from '@/api/exports';
import { ReimbursementForm } from '@/components/exports/ReimbursementForm';
import { Button } from '@/components/ui/Button';
import { ArrowLeft } from 'lucide-react';
import type { ReimbursementPreview } from '@/types/export';

const ROWS_PER_PAGE = 6;

export function ReimbursementPreviewPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const batchId = Number(id);

  const [data, setData] = useState<ReimbursementPreview | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!batchId) return;

    let cancelled = false;
    setLoading(true);
    setError(null);

    exportsApi
      .getReimbursementPreview(batchId)
      .then((result) => {
        if (!cancelled) {
          setData(result);
          setLoading(false);
        }
      })
      .catch((err) => {
        if (!cancelled) {
          const message =
            err?.response?.data?.detail?.message ||
            err?.response?.data?.detail ||
            '加载报销单预览失败，请稍后重试';
          setError(typeof message === 'string' ? message : '加载报销单预览失败');
          setLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [batchId]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-gray-200 border-t-blue-600" />
      </div>
    );
  }

  if (error) {
    return (
      <div>
        <Button variant="ghost" onClick={() => navigate(`/batches/${batchId}`)} className="mb-4">
          <ArrowLeft className="mr-1 h-4 w-4" />返回批次详情
        </Button>
        <div className="rounded-lg border border-red-200 bg-red-50 px-6 py-8 text-center text-red-600">
          <p className="text-lg font-medium">{error}</p>
        </div>
      </div>
    );
  }

  if (!data) return null;

  const pages = Math.ceil(data.items.length / ROWS_PER_PAGE) || 1;

  return (
    <div>
      <div className="mb-6 flex items-center gap-4">
        <Button variant="ghost" onClick={() => navigate(`/batches/${batchId}`)}>
          <ArrowLeft className="mr-1 h-4 w-4" />返回批次详情
        </Button>
        <h2 className="text-xl font-semibold text-gray-900">费用报销单预览</h2>
        <span className="ml-auto text-sm text-gray-500">
          共 {pages} 页，{data.items.length} 项
        </span>
      </div>

      <div className="space-y-6">
        {Array.from({ length: pages }).map((_, pageIdx) => {
          const pageItems = data.items.slice(
            pageIdx * ROWS_PER_PAGE,
            (pageIdx + 1) * ROWS_PER_PAGE,
          );
          return (
            <ReimbursementForm
              key={pageIdx}
              department={data.department}
              reportDate={data.report_date}
              reporter={data.reporter}
              items={pageItems}
              pageIndex={pageIdx + 1}
              totalPages={pages}
            />
          );
        })}
      </div>
    </div>
  );
}