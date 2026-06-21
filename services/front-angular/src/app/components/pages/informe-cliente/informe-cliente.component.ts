import { Component, OnInit } from '@angular/core';
import { DatePipe } from '@angular/common';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { InformeService } from '../../../services/informe.service';
import { AuthService } from '../../../services/auth.service';
import { InformeCliente, InformeClienteRequest } from '../../../models/informe.model';

@Component({
  selector: 'app-informe-cliente',
  imports: [DatePipe],
  templateUrl: './informe-cliente.component.html',
  styleUrls: ['./informe-cliente.component.css']
})
export class InformeClienteComponent implements OnInit {
  informeForm: FormGroup;
  informes: InformeCliente[] = [];
  informeSeleccionado: InformeCliente | null = null;
  isLoading: boolean = false;
  isFormVisible: boolean = false;
  isSendingEmail: boolean = false;
  username: string = '';
  clientesDisponibles: string[] = [
    'Juan Pérez - Hacienda Los Pinos',
    'María García - Reserva El Roble',
    'Agrícola Norte - Valle Seco',
    'Alejandro Villalobos',
    'Viñedos del Sur'
  ];

  constructor(
    private fb: FormBuilder,
    private informeService: InformeService,
    private authService: AuthService
  ) {
    this.informeForm = this.fb.group({
      cliente: ['', Validators.required]
    });
  }

  ngOnInit(): void {
    this.username = this.authService.getUsername();
    this.cargarInformes();
  }

  cargarInformes(): void {
    this.isLoading = true;

    // Simular carga de informes desde la API
    setTimeout(() => {
      this.informes = [
        {
          id: 1,
          responsable: 'admin',
          cliente: 'Juan Pérez - Hacienda Los Pinos',
          estado: 'listo',
          contenido: `**Asunto: Anuncio de Evaluación de Riesgo de Incendio - Propiedad de Juan Pérez**

Estimado Juan Pérez,

Le escribimos para informarle que hemos completado la evaluación de riesgo de incendio para su propiedad en Hacienda Los Pinos.

**Resultados de la Evaluación:**
- Nivel de Riesgo: BAJO
- Probabilidad de incendio: 0.04%
- Humedad de biomasa: 24.2%

**Recomendaciones:**
1. Mantener los cortafuegos perimetrales libres de residuos secos.
2. Monitorear el aumento de temperatura previsto para el fin de semana.
3. Verificar operatividad de las tomas de agua en el sector Noroeste.

Atentamente,
Ignis Guard Risk Management Platform`,
          created_at: '2024-05-14T10:30:00',
          updated_at: '2024-05-14T11:30:00'
        },
        {
          id: 2,
          responsable: 'admin',
          cliente: 'María García - Reserva El Roble',
          estado: 'listo',
          contenido: `**Asunto: Evaluación de Riesgo - Reserva El Roble**

Estimada María García,

La evaluación de riesgo para su reserva ha sido completada.

**Resultados de la Evaluación:**
- Nivel de Riesgo: MEDIO
- Zonas críticas identificadas: Sector Norte y Este

**Recomendaciones:**
1. Implementar sistema de riego en zonas críticas.
2. Realizar limpieza de sotobosque en el perímetro.
3. Establecer puntos de vigilancia en el sector Norte.

Atentamente,
Ignis Guard Risk Management Platform`,
          created_at: '2024-05-12T14:20:00',
          updated_at: '2024-05-12T15:10:00'
        },
        {
          id: 3,
          responsable: 'operador_01',
          cliente: 'Agrícola Norte - Valle Seco',
          estado: 'requerido',
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

  seleccionarInforme(informe: InformeCliente): void {
    this.informeSeleccionado = informe;
  }

  onSubmit(): void {
    if (this.informeForm.invalid) {
      this.informeForm.markAllAsTouched();
      return;
    }

    this.isLoading = true;
    const formData: InformeClienteRequest = {
      responsable: this.username,
      cliente: this.informeForm.value.cliente
    };

    this.informeService.crearInformeCliente(formData).subscribe({
      next: (response) => {
        this.isLoading = false;
        this.isFormVisible = false;
        this.informeForm.reset();
        alert(`Informe para cliente solicitado exitosamente. ID: ${response.id}`);
        this.cargarInformes();
      },
      error: (err) => {
        this.isLoading = false;
        console.error('Error al crear informe para cliente:', err);
        alert('Error al solicitar el informe para cliente');
      }
    });
  }

  sendEmail(): void {
    if (!this.informeSeleccionado) return;

    this.isSendingEmail = true;
    const cliente = this.informeSeleccionado.cliente;
    const reportId = this.informeSeleccionado.id;

    // Extraer email del cliente (simulado)
    const email = cliente.split(' - ')[0].toLowerCase().replace(/ /g, '.') + '@email.com';
    const subject = encodeURIComponent(`[Ignis Guard] Informe de Riesgo ${reportId} - ${cliente}`);
    const body = encodeURIComponent(
      `Estimado ${cliente},\n\n` +
      `Adjunto encontrará el informe técnico de gestión de riesgos forestales correspondiente al periodo actual para su propiedad.\n\n` +
      `Resumen: ${this.informeSeleccionado.contenido?.substring(0, 200) || 'Informe disponible en la plataforma'}\n\n` +
      `Por favor, revise las recomendaciones técnicas en el documento completo.\n\n` +
      `Atentamente,\n` +
      `Equipo de Riesgos - Ignis Guard`
    );

    // Simular envío de email
    setTimeout(() => {
      this.isSendingEmail = false;
      alert(`Email enviado a ${email}\n\nAsunto: ${decodeURIComponent(subject)}\n\nEl mensaje ha sido enviado correctamente.`);

      // Opción para abrir el cliente de email
      // window.location.href = `mailto:${email}?subject=${subject}&body=${body}`;
    }, 1500);
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

  getStatusBadgeClass(estado: string): string {
    switch(estado) {
      case 'listo': return 'bg-primary text-on-primary';
      case 'requerido': return 'bg-secondary-container text-on-secondary-container';
      default: return 'bg-surface-dim text-on-surface-variant';
    }
  }

  getStatusLabel(estado: string): string {
    switch(estado) {
      case 'listo': return 'Completado';
      case 'requerido': return 'En Proceso';
      default: return estado;
    }
  }

  getStatusIcon(estado: string): string {
    switch(estado) {
      case 'listo': return 'check_circle';
      case 'requerido': return 'pending';
      default: return 'help';
    }
  }
}
