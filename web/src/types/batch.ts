export interface ReimbursementBatch {
  id: number;
  department: string;
  period_start: string | null;
  period_end: string | null;
  report_date: string | null;
  reporter: string;
  reviewer: string | null;
  payee: string | null;
  bank_account: string | null;
  bank_name: string | null;
  total_amount: number;
  status: string;
  invoice_count: number;
  created_at: string;
  updated_at: string;
}

export interface LedgerRow {
  id: number;
  invoice_id: number;
  invoice_date: string | null;
  category: string | null;
  invoice_type: string | null;
  amount: number | null;
  quantity: number;
  unit_price: number;
  advance_amount: number;
  remark: string | null;
  expense_item: string | null;
  invoice_no: string | null;
  vendor: string | null;
  is_substitute: boolean;
  substitute_for: string | null;
}

export interface BatchDetail extends ReimbursementBatch {
  ledger_rows: LedgerRow[];
}

export interface AvailableInvoice {
  id: number;
  invoice_no: string | null;
  amount: number | null;
  invoice_date: string | null;
  category: string | null;
  vendor: string | null;
  file_path: string;
  file_original_name: string | null;
}

export interface AvailableInvoiceListResponse {
  items: AvailableInvoice[];
  total: number;
  page: number;
  page_size: number;
}

export interface BatchListResponse {
  items: ReimbursementBatch[];
  total: number;
}

export interface CreateBatchRequest {
  department: string;
  period_start?: string | null;
  period_end?: string | null;
  report_date?: string | null;
  reporter?: string | null;
  reviewer?: string | null;
  payee?: string | null;
  bank_account?: string | null;
  bank_name?: string | null;
}

export interface UpdateBatchRequest {
  department?: string | null;
  period_start?: string | null;
  period_end?: string | null;
  report_date?: string | null;
  reporter?: string | null;
  reviewer?: string | null;
  payee?: string | null;
  bank_account?: string | null;
  bank_name?: string | null;
}

export interface UpdateBatchInvoiceRequest {
  quantity?: number | null;
  advance_amount?: number | null;
  remark?: string | null;
}

export interface AddInvoicesRequest {
  invoice_ids: number[];
}

export interface ManualRowCreateRequest {
  row_date?: string | null;
  expense_item: string;
  row_amount: number;
  quantity?: number;
  advance_amount?: number;
  remark?: string | null;
}

export interface ManualRowUpdateRequest {
  row_date?: string | null;
  expense_item?: string;
  row_amount?: number;
  quantity?: number;
  advance_amount?: number;
  remark?: string | null;
}

export interface SubstituteInvoiceItem {
  id: number;
  invoice_no: string | null;
  amount: number;
  invoice_date: string | null;
  category: string | null;
  vendor: string | null;
  file_path: string;
  file_original_name: string | null;
  used_as_substitute: number;
  remaining_amount: number;
}

export interface SubstituteInvoiceListResponse {
  items: SubstituteInvoiceItem[];
  total: number;
  page: number;
  page_size: number;
}

export interface SubstituteCreateRequest {
  mode: 'one_to_one' | 'one_to_many' | 'many_to_one';
  substitute_invoice_ids: number[];
  target_row_ids: number[];
}

export interface SubstituteInvoiceInfo {
  id: number;
  invoice_no: string;
  amount: number;
  category: string | null;
}

export interface SubstituteTargetRowInfo {
  id: number;
  expense_item: string | null;
  row_amount: number | null;
  source_type: string;
}

export interface SubstituteRelationResponse {
  id: number;
  mode: string;
  substitute_invoice: SubstituteInvoiceInfo;
  target_row: SubstituteTargetRowInfo;
  created_at: string;
}

export interface SubstituteRelationListResponse {
  relations: SubstituteRelationResponse[];
}

export interface SubstituteCreatedResponse {
  relations: Array<{
    id: number;
    batch_id: number;
    substitute_invoice_id: number;
    target_row_id: number;
    mode: string;
    created_at: string;
  }>;
  updated_target_rows: Array<{
    id: number;
    expense_item: string | null;
    row_amount: number | null;
    remark: string | null;
    is_substitute: boolean;
    substitute_for: string | null;
  }>;
}
