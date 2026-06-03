export interface RecentBatchItem {
  id: number;
  department: string;
  period_start: string | null;
  period_end: string | null;
  report_date: string | null;
  reporter: string;
  total_amount: number;
  status: string;
  invoice_count: number;
  created_at: string;
}

export interface DashboardStats {
  pending_invoice_count: number;
  monthly_total_amount: number;
  active_batch_count: number;
  recent_batches: RecentBatchItem[];
}