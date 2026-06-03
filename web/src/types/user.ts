export interface User {
  id: number;
  username: string;
  display_name: string | null;
  default_department: string | null;
  default_reporter: string | null;
  default_payee: string | null;
  default_bank_account: string | null;
  default_bank_name: string | null;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface RegisterRequest {
  username: string;
  password: string;
  display_name?: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface UpdateUserDefaultsRequest {
  default_department?: string | null;
  default_reporter?: string | null;
  default_payee?: string | null;
  default_bank_account?: string | null;
  default_bank_name?: string | null;
}
