export interface InformeRiesgo {
  id: number;
  responsable: string;
  cliente: string;
  estado: string;
  contenido?: string;
  descripcion?: string;
  created_at: string;
  updated_at: string;
}

export interface InformeRiesgoRequest {
  responsable: string;
  cliente: string;
  descripcion: string;
}

export interface InformeCliente {
  id: number;
  responsable: string;
  cliente: string;
  estado: string;
  contenido?: string;
  created_at: string;
  updated_at: string;
}

export interface InformeClienteRequest {
  responsable: string;
  cliente: string;
}
