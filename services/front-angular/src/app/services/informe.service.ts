import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';
import { 
  InformeRiesgo, 
  InformeRiesgoRequest, 
  InformeCliente, 
  InformeClienteRequest 
} from '../models/informe.model';

@Injectable({
  providedIn: 'root'
})
export class InformeService {
  private apiUrl = environment.apiUrl;

  constructor(private http: HttpClient) {}

  // Informes de Riesgo
  crearInformeRiesgo(data: InformeRiesgoRequest): Observable<{ id: number; estado: string }> {
    return this.http.post<{ id: number; estado: string }>(`${this.apiUrl}/informes/riesgo`, data);
  }

  obtenerInformeRiesgo(id: number): Observable<InformeRiesgo> {
    return this.http.get<InformeRiesgo>(`${this.apiUrl}/informes/riesgo/${id}`);
  }

  // Informes para Clientes
  crearInformeCliente(data: InformeClienteRequest): Observable<{ id: number; estado: string }> {
    return this.http.post<{ id: number; estado: string }>(`${this.apiUrl}/informes/clientes`, data);
  }

  obtenerInformeCliente(id: number): Observable<InformeCliente> {
    return this.http.get<InformeCliente>(`${this.apiUrl}/informes/clientes/${id}`);
  }

  // Listar informes de riesgo (usando el endpoint de ordenes para obtener los clientes)
  // Nota: Para listar todos los informes, podríamos necesitar un endpoint adicional
  // Por ahora usaremos el endpoint de ordenes para obtener los clientes
}
