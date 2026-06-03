export type InvoiceStatus = 'processing' | 'pending' | 'failed' | 'confirmed' | 'archived';

export type InvoiceType = '增值税' | '高铁' | '滴滴' | '飞机' | '其他';

export interface Invoice {
  id: number;
  user_id: number;
  invoice_no: string | null;
  amount: number | null;
  invoice_date: string | null;
  category: string | null;
  vendor: string | null;
  buyer_name: string | null;
  invoice_type: string | null;
  project_name: string | null;
  train_no: string | null;
  departure_station: string | null;
  arrival_station: string | null;
  departure_location: string | null;
  arrival_location: string | null;
  flight_no: string | null;
  departure_city: string | null;
  arrival_city: string | null;
  file_path: string;
  file_original_name: string | null;
  status: InvoiceStatus;
  remark: string | null;
  ocr_raw_data: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
}

export interface UpdateInvoiceRequest {
  invoice_no?: string | null;
  amount?: number | null;
  invoice_date?: string | null;
  category?: string | null;
  vendor?: string | null;
  buyer_name?: string | null;
  invoice_type?: string | null;
  project_name?: string | null;
  train_no?: string | null;
  departure_station?: string | null;
  arrival_station?: string | null;
  departure_location?: string | null;
  arrival_location?: string | null;
  flight_no?: string | null;
  departure_city?: string | null;
  arrival_city?: string | null;
  remark?: string | null;
}

export interface UploadFileResult {
  filename: string;
  success: boolean;
  invoice_id: number | null;
  error: string | null;
}

export interface UploadResponse {
  results: UploadFileResult[];
  skipped_count: number;
}

export interface InvoiceListResponse {
  items: Invoice[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface DeleteResponse {
  deleted: boolean;
  type: 'hard' | 'soft';
  restorable_until: string | null;
}

export interface InvoiceListParams {
  state?: string;
  page?: number;
  page_size?: number;
  date_from?: string;
  date_to?: string;
}