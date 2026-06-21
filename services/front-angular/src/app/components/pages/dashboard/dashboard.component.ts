import { Component, OnInit } from '@angular/core';
import { AuthService } from '../../../services/auth.service';
import { OrdenService } from '../../../services/orden.service';
import { Orden } from '../../../models/orden.model';

@Component({
  selector: 'app-dashboard',
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.css']
})
export class DashboardComponent implements OnInit {
  ordenes: Orden[] = [];
  filteredOrdenes: Orden[] = [];
  clientesFiltro: string[] = [];
  clienteSeleccionado: string = 'all';
  isLoading: boolean = true;
  isAdmin: boolean = false;
  username: string = '';

  // Métricas
  totalClientesEnRiesgo: number = 0;
  totalZonasInteres: number = 0;
  totalAlertas: number = 0;

  constructor(
    private authService: AuthService,
    private ordenService: OrdenService
  ) {}

  ngOnInit(): void {
    this.isAdmin = this.authService.isAdmin();
    this.username = this.authService.getUsername();
    this.cargarOrdenes();
  }

  cargarOrdenes(): void {
    this.isLoading = true;
    this.ordenService.listarOrdenes().subscribe({
      next: (data) => {
        this.ordenes = data;
        this.filteredOrdenes = data;
        this.calcularMetricas();
        this.extraerClientes();
        this.isLoading = false;
      },
      error: (err) => {
        console.error('Error al cargar órdenes:', err);
        this.isLoading = false;
      }
    });
  }

  calcularMetricas(): void {
    // Simular métricas basadas en los datos reales
    this.totalClientesEnRiesgo = this.ordenes.length;
    this.totalZonasInteres = this.ordenes.length > 0 ? Math.min(this.ordenes.length * 2, 20) : 0;
    this.totalAlertas = this.ordenes.filter(o => o.status === 'Predicha' && o.prediction === 'Alto').length;
  }

  extraerClientes(): void {
    const clientesSet = new Set<string>();
    this.ordenes.forEach(o => {
      if (o.cliente) {
        clientesSet.add(o.cliente);
      }
    });
    this.clientesFiltro = Array.from(clientesSet);
  }

  filtrarPorCliente(): void {
    if (this.clienteSeleccionado === 'all') {
      this.filteredOrdenes = this.ordenes;
    } else {
      this.filteredOrdenes = this.ordenes.filter(o => o.cliente === this.clienteSeleccionado);
    }
  }

  getEstadoColor(estado: string): string {
    switch(estado) {
      case 'Predicha': return 'bg-secondary';
      case 'Pendiente..': return 'bg-tertiary-container';
      default: return 'bg-outline';
    }
  }

  getRiesgoColor(riesgo: string): string {
    switch(riesgo) {
      case 'Alto': return 'risk-high';
      case 'Medio': return 'risk-medium';
      case 'Bajo': return 'risk-low';
      default: return 'risk-low';
    }
  }

  getEstadoLabel(estado: string): string {
    switch(estado) {
      case 'Predicha': return 'Crítico';
      case 'Pendiente..': return 'Monitoreo';
      default: return 'Estable';
    }
  }
}
