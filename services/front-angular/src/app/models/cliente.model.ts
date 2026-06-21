export interface Cliente {
  id: number;
  nombre: string;
  codigo_cliente: string;
  email?: string;
  telefono?: string;
  created_at?: string;
}

export interface AreaAsegurada {
  id: number;
  cliente_id: number;
  nombre_lote: string;
  latitud: number;
  longitud: number;
  riesgo_promedio?: number;
  descripcion_entorno?: string;
  created_at?: string;
}
