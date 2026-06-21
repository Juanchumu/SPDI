import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { ClienteService } from '../../../services/cliente.service';
import { AuthService } from '../../../services/auth.service';
import { Cliente, AreaAsegurada } from '../../../models/cliente.model';

@Component({
  selector: 'app-registro-cliente',
  templateUrl: './registro-cliente.component.html',
  styleUrls: ['./registro-cliente.component.css']
})
export class RegistroClienteComponent implements OnInit {
  cliente: Cliente | null = null;
  areas: AreaAsegurada[] = [];
  isLoading: boolean = true;
  clienteId: number = 0;
  riesgoPromedio: number = 0;

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
    // Como no tenemos un endpoint para obtener un cliente específico,
    // obtenemos la lista y filtramos
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

  getColorRiesgo(riesgo: number | undefined): string {
    if (riesgo === undefined || riesgo === null) return 'bg-primary';
    if (riesgo > 0.5) return 'bg-error';
    if (riesgo > 0.2) return 'bg-secondary';
    return 'bg-primary';
  }

  generarInforme(): void {
    alert(`Generando informe para ${this.cliente?.nombre}`);
  }

  enviarAlerta(): void {
    alert(`Enviando alerta a ${this.cliente?.nombre}`);
  }
}
