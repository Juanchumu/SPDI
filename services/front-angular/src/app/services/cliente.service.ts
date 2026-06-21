import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';
import { Cliente, AreaAsegurada } from '../models/cliente.model';

@Injectable({
  providedIn: 'root'
})
export class ClienteService {
  private apiUrl = environment.apiUrl;

  constructor(private http: HttpClient) {}

  listarClientes(): Observable<Cliente[]> {
    return this.http.get<Cliente[]>(`${this.apiUrl}/clientes`);
  }

  crearCliente(cliente: Partial<Cliente>): Observable<Cliente> {
    return this.http.post<Cliente>(`${this.apiUrl}/clientes`, cliente);
  }

  listarAreasCliente(clienteId: number): Observable<AreaAsegurada[]> {
    return this.http.get<AreaAsegurada[]>(`${this.apiUrl}/clientes/${clienteId}/areas`);
  }

  crearAreaCliente(clienteId: number, area: Partial<AreaAsegurada>): Observable<AreaAsegurada> {
    return this.http.post<AreaAsegurada>(`${this.apiUrl}/clientes/${clienteId}/areas`, area);
  }
}
