export interface Usuario {
  id?: number;
  username: string;
  password?: string;
  password_hash?: string;
  rol?: string;
  created_at?: string;
}

export interface LoginResponse {
  success: boolean;
  username: string;
}
