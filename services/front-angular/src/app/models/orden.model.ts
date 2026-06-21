export interface Orden {
  id: number;
  lat: number;
  lon: number;
  dia: string;
  status: string;
  prediction?: string;
  username: string;
  cliente: string;
  created_at: string;
  updated_at?: string;
  modelo_utilizado?: string;
}

export interface OrdenRequest {
  dia: number;
  lat: number;
  lon: number;
  username: string;
  cliente: string;
}
