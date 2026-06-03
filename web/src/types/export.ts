export interface ReimbursementItem {
  expense_item: string;
  amount: number;
}

export interface ReimbursementPreview {
  department: string;
  report_date: string | null;
  reporter: string;
  items: ReimbursementItem[];
  total_amount: number;
  total_amount_cn: string;
}

export interface PdfExportRequest {
  invoice_ids: number[];
  layouts: Record<string, 'portrait' | 'landscape'>;
}

export interface BatchPdfExportRequest {
  layouts: Record<string, 'portrait' | 'landscape'>;
}