import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';
import { Orden, OrdenRequest } from '../models/orden.model';

@Injectable({
  providedIn: 'root'
})
export class OrdenService {
  private apiUrl = environment.apiUrl;

  constructor(private http: HttpClient) {}

  crearOrden(orden: OrdenRequest): Observable<{ id: number; status: string }> {
    return this.http.post<{ id: number; status: string }>(`${this.apiUrl}/orden`, orden);
  }

  listarOrdenes(): Observable<Orden[]> {
    return this.http.get<Orden[]>(`${this.apiUrl}/orden`);
  }

  obtenerOrden(id: number): Observable<Orden> {
    return this.http.get<Orden>(`${this.apiUrl}/orden/${id}`);
  }

  recuperarOrdenesPorUsuario(username: string): Observable<any> {
    const params = new HttpParams().set('username', username);
    return this.http.get(`${this.apiUrl}/recuperar_ordenes`, { params });
  }
}
