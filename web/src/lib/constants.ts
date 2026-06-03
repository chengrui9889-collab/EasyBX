export const INVOICE_STATUS = {
  PROCESSING: 'processing',
  PENDING: 'pending',
  FAILED: 'failed',
  CONFIRMED: 'confirmed',
} as const;

export const BATCH_STATUS = {
  DRAFT: 'draft',
  COMPLETED: 'completed',
  ARCHIVED: 'archived',
} as const;

export const INVOICE_CATEGORIES = [
  '交通费',
  '打车费',
  '住宿费',
  '餐饮费',
  '办公用品',
  '通讯费',
  '奖金',
  '其他',
] as const;

export const PDF_LAYOUTS = {
  PORTRAIT: 'portrait',
  LANDSCAPE: 'landscape',
} as const;

export const SUBSTITUTE_MODES = {
  ONE_TO_ONE: 'one_to_one',
  ONE_TO_MANY: 'one_to_many',
  MANY_TO_ONE: 'many_to_one',
} as const;

export const STATUS_LABELS: Record<string, string> = {
  processing: '识别中',
  pending: '待确认',
  failed: '识别失败',
  confirmed: '已入库',
  archived: '已归档',
};

export const STATUS_COLORS: Record<string, string> = {
  processing: 'blue',
  pending: 'yellow',
  failed: 'red',
  confirmed: 'green',
  archived: 'gray',
};

export const INVOICE_TABS = [
  { key: 'all', label: '全部' },
  { key: 'processing', label: '识别中', state: 'processing' as const },
  { key: 'pending_failed', label: '待确认', state: 'pending_failed' as const },
  { key: 'confirmed', label: '已入库', state: 'confirmed' as const },
  { key: 'archived', label: '已归档' as const },
] as const;