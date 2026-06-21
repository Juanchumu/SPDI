import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { InformeService } from '../../../services/informe.service';
import { AuthService } from '../../../services/auth.service';
import { InformeRiesgo, InformeRiesgoRequest } from '../../../models/informe.model';

import { DatePipe } from '@angular/common';
@Component({
  selector: 'app-informe-riesgo',
  imports: [DatePipe],
  templateUrl: './informe-riesgo.component.html',
  styleUrls: ['./informe-riesgo.component.css']
})
export class InformeRiesgoComponent implements OnInit {
  informeForm: FormGroup;
  informes: InformeRiesgo[] = [];
  informeSeleccionado: InformeRiesgo | null = null;
  isLoading: boolean = false;
  isFormVisible: boolean = false;
  isAdmin: boolean = false;
  username: string = '';
  clientes: string[] = [];

  // Datos de ejemplo para clientes (se pueden cargar desde la API)
  clientesDisponibles: string[] = [
    'Agroindustria El Pinar',
    'Reserva Los Andes',
    'Maderas del Norte',
    'Viñedos del Sur',
    'Hacienda Los Olivos',
    'Reserva Forestal Norte'
  ];

  constructor(
    private fb: FormBuilder,
    private informeService: InformeService,
    private authService: AuthService
  ) {
    this.informeForm = this.fb.group({
      cliente: ['', Validators.required],
      descripcion: ['', [Validators.required, Validators.minLength(10)]]
    });
  }

  ngOnInit(): void {
    this.isAdmin = this.authService.isAdmin();
    this.username = this.authService.getUsername();
    this.cargarInformes();
  }

  cargarInformes(): void {
    this.isLoading = true;
    // Como no tenemos un endpoint para listar todos los informes de riesgo,
    // usamos el endpoint de órdenes para obtener los clientes
    // y simulamos algunos informes para demostración
    this.clientes = this.clientesDisponibles;

    // Simular carga de informes
    setTimeout(() => {
      this.informes = [
        {
          id: 1,
          responsable: 'admin',
          cliente: 'Agroindustria El Pinar',
          estado: 'listo',
          contenido: `## Informe de Riesgo de Asegurabilidad - Agroindustria El Pinar

**Factores Agravantes:** La presencia de zonas críticas de alto riesgo (predicciones "alto") en la proximidad del cliente, junto con la reiteración de estos riesgos, es un factor preocupante. La ubicación específica también presenta vegetación abundante, lo que incrementa el potencial de propagación de incendios.

**Evaluación General:** Alto

**Recomendación para la Aseguradora:** Conviene solicitar información adicional. Es crucial conocer las medidas de prevención implementadas por el cliente (equipamiento, personal, acceso a agua) y la disponibilidad de recursos en caso de un incendio. Se requiere una evaluación más profunda antes de considerar cualquier cobertura.`,
          descripcion: 'Cliente ubicado en zona con antecedentes de incendios forestales',
          created_at: '2024-05-12T10:30:00',
          updated_at: '2024-05-12T11:30:00'
        },
        {
          id: 2,
          responsable: 'admin',
          cliente: 'Reserva Los Andes',
          estado: 'listo',
          contenido: `## Informe de Riesgo de Asegurabilidad - Reserva Los Andes

**Factores Agravantes:** La zona presenta una pendiente crítica del 35% que facilita la propagación vertical del fuego. La acumulación de biomasa en el perímetro sur supera los 5kg/m².

**Evaluación General:** Medio

**Recomendación para la Aseguradora:** Se recomienda monitoreo constante y mantenimiento de cortafuegos. La implementación de sistemas de riego en zonas críticas podría reducir significativamente el riesgo.`,
          descripcion: 'Reserva natural en la cordillera oriental',
          created_at: '2024-05-10T14:20:00',
          updated_at: '2024-05-10T15:10:00'
        },
        {
          id: 3,
          responsable: 'operador_01',
          cliente: 'Viñedos del Sur',
          estado: 'requerido',
          descripcion: 'Viñedos en zona con riesgo de estrés hídrico',
          created_at: '2024-05-15T09:00:00',
          updated_at: '2024-05-15T09:00:00'
        }
      ];
      this.isLoading = false;
    }, 500);
  }

  toggleForm(): void {
    this.isFormVisible = !this.isFormVisible;
    if (!this.isFormVisible) {
      this.informeForm.reset();
    }
  }

  seleccionarInforme(informe: InformeRiesgo): void {
    this.informeSeleccionado = informe;
  }

  onSubmit(): void {
    if (this.informeForm.invalid) {
      this.informeForm.markAllAsTouched();
      return;
    }

    this.isLoading = true;
    const formData: InformeRiesgoRequest = {
      responsable: this.username,
      cliente: this.informeForm.value.cliente,
      descripcion: this.informeForm.value.descripcion
    };

    this.informeService.crearInformeRiesgo(formData).subscribe({
      next: (response) => {
        this.isLoading = false;
        this.isFormVisible = false;
        this.informeForm.reset();
        alert(`Informe de riesgo solicitado exitosamente. ID: ${response.id}`);
        this.cargarInformes();
      },
      error: (err) => {
        this.isLoading = false;
        console.error('Error al crear informe de riesgo:', err);
        alert('Error al solicitar el informe de riesgo');
      }
    });
  }

  getEstadoClass(estado: string): string {
    switch(estado) {
      case 'listo': return 'bg-primary text-white';
      case 'requerido': return 'bg-secondary-container text-on-secondary-container';
      default: return 'bg-surface-dim text-on-surface-variant';
    }
  }

  getEstadoLabel(estado: string): string {
    switch(estado) {
      case 'listo': return 'Listo';
      case 'requerido': return 'Pendiente';
      default: return estado;
    }
  }

  getNivelRiesgo(contenido: string | undefined): string {
    if (!contenido) return 'Pendiente';
    if (contenido.includes('**Evaluación General:** Alto')) return 'Crítico';
    if (contenido.includes('**Evaluación General:** Medio')) return 'Medio';
    if (contenido.includes('**Evaluación General:** Bajo')) return 'Bajo';
    return 'Pendiente';
  }

  getColorRiesgo(contenido: string | undefined): string {
    const nivel = this.getNivelRiesgo(contenido);
    switch(nivel) {
      case 'Crítico': return 'border-l-4 border-secondary';
      case 'Medio': return 'border-l-4 border-primary-container';
      case 'Bajo': return 'border-l-4 border-tertiary-container';
      default: return 'border-l-4 border-outline-variant';
    }
  }

  getRiesgoIcon(contenido: string | undefined): string {
    const nivel = this.getNivelRiesgo(contenido);
    switch(nivel) {
      case 'Crítico': return 'warning';
      case 'Medio': return 'visibility';
      case 'Bajo': return 'check_circle';
      default: return 'pending';
    }
  }

  getRiesgoColorIcon(contenido: string | undefined): string {
    const nivel = this.getNivelRiesgo(contenido);
    switch(nivel) {
      case 'Crítico': return 'text-secondary';
      case 'Medio': return 'text-primary-container';
      case 'Bajo': return 'text-tertiary-container';
      default: return 'text-outline';
    }
  }
}
