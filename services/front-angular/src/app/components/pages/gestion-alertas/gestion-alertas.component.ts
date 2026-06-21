import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { ClienteService } from '../../../services/cliente.service';
import { AuthService } from '../../../services/auth.service';
import { Cliente, AreaAsegurada } from '../../../models/cliente.model';

@Component({
  selector: 'app-gestion-alertas',
  templateUrl: './gestion-alertas.component.html',
  styleUrls: ['./gestion-alertas.component.css']
})
export class GestionAlertasComponent implements OnInit {
  cliente: Cliente | null = null;
  areas: AreaAsegurada[] = [];
  isLoading: boolean = true;
  clienteId: number = 0;
  riesgoPromedio: number = 0;
  isEnviandoAlerta: boolean = false;

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private clienteService: ClienteService,
    public authService: AuthService
  ) {}

  ngOnInit(): void {
    this.route.params.subscribe(params => {
      this.clienteId = +params['id'];
      if (this.clienteId) {
        this.cargarCliente();
      }
    });
  }

  cargarCliente(): void {
    this.isLoading = true;
    this.clienteService.listarClientes().subscribe({
      next: (clientes) => {
        this.cliente = clientes.find(c => c.id === this.clienteId) || null;
        if (this.cliente) {
          this.cargarAreas();
        } else {
          this.isLoading = false;
        }
      },
      error: (err) => {
        console.error('Error al cargar cliente:', err);
        this.isLoading = false;
      }
    });
  }

  cargarAreas(): void {
    this.clienteService.listarAreasCliente(this.clienteId).subscribe({
      next: (areas) => {
        this.areas = areas;
        this.calcularRiesgoPromedio();
        this.isLoading = false;
      },
      error: (err) => {
        console.error('Error al cargar áreas:', err);
        this.isLoading = false;
      }
    });
  }

  calcularRiesgoPromedio(): void {
    const riesgos = this.areas
      .map(a => a.riesgo_promedio)
      .filter(r => r !== undefined && r !== null) as number[];

    if (riesgos.length > 0) {
      this.riesgoPromedio = riesgos.reduce((a, b) => a + b, 0) / riesgos.length;
    }
  }

  getNivelRiesgo(riesgo: number | undefined): string {
    if (riesgo === undefined || riesgo === null) return 'Bajo';
    if (riesgo > 0.5) return 'Alto';
    if (riesgo > 0.2) return 'Medio';
    return 'Bajo';
  }

  enviarAlerta(): void {
    this.isEnviandoAlerta = true;
    // Simular envío de alerta
    setTimeout(() => {
      this.isEnviandoAlerta = false;
      alert(`Alerta enviada a ${this.cliente?.nombre}`);
    }, 1500);
  }
}
