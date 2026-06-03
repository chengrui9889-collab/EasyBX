import { Inbox } from 'lucide-react';

export function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center py-20">
      <Inbox className="mb-4 h-16 w-16 text-gray-300" />
      <p className="text-lg font-medium text-gray-500">暂无发票</p>
      <p className="mt-1 text-sm text-gray-400">
        拖拽文件到上方区域开始上传
      </p>
    </div>
  );
}