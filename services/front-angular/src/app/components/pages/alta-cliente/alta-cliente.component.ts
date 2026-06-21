import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { ClienteService } from '../../../services/cliente.service';
import { AuthService } from '../../../services/auth.service';

@Component({
  selector: 'app-alta-cliente',
  imports : [RouterLink],
  templateUrl: './alta-cliente.component.html',
  styleUrls: ['./alta-cliente.component.css']
})
export class AltaClienteComponent implements OnInit {
  clienteForm: FormGroup;
  isNewClient: boolean = true;
  isSubmitting: boolean = false;
  latitud: number = -33.4489;
  longitud: number = -70.6693;

  constructor(
    private fb: FormBuilder,
    private clienteService: ClienteService,
    private authService: AuthService,
    private router: Router
  ) {
    this.clienteForm = this.fb.group({
      nombre_empresa: ['', Validators.required],
      nombre_propietario: ['', Validators.required],
      telefono: ['', Validators.required],
      email: ['', [Validators.required, Validators.email]],
      nombre_encargado: ['', Validators.required],
      email_alerta: ['', [Validators.required, Validators.email]],
      telefono_alerta: ['', Validators.required],
      nombre_predio: ['', Validators.required],
      descripcion: [''],
      latitud: [this.latitud],
      longitud: [this.longitud]
    });
  }

  ngOnInit(): void {
    if (!this.authService.isAdmin()) {
      this.router.navigate(['/dashboard']);
    }
  }

  toggleClientType(tipo: 'new' | 'existing'): void {
    this.isNewClient = tipo === 'new';
  }

  updateCoordinates(lat: number, lng: number): void {
    this.latitud = lat;
    this.longitud = lng;
    this.clienteForm.patchValue({
      latitud: lat,
      longitud: lng
    });
  }

  onSubmit(): void {
    if (this.clienteForm.invalid) {
      this.clienteForm.markAllAsTouched();
      return;
    }

    this.isSubmitting = true;
    const formData = this.clienteForm.value;

    // Crear cliente
    this.clienteService.crearCliente({
      nombre: formData.nombre_empresa,
      codigo_cliente: `CL-${Date.now().toString().slice(-8)}`,
      email: formData.email,
      telefono: formData.telefono
    }).subscribe({
      next: (cliente) => {
        // Crear área asegurada
        this.clienteService.crearAreaCliente(cliente.id!, {
          nombre_lote: formData.nombre_predio,
          latitud: formData.latitud,
          longitud: formData.longitud,
          descripcion_entorno: formData.descripcion
        }).subscribe({
          next: () => {
            this.isSubmitting = false;
            alert('Cliente y campo registrados exitosamente');
            this.router.navigate(['/dashboard']);
          },
          error: (err) => {
            this.isSubmitting = false;
            console.error('Error al crear área:', err);
            alert('Error al crear el área asegurada');
          }
        });
      },
      error: (err) => {
        this.isSubmitting = false;
        console.error('Error al crear cliente:', err);
        alert('Error al crear el cliente');
      }
    });
  }

  onMapClick(event: MouseEvent): void {
    const randomLat = (-33.4 - Math.random() * 0.1);
    const randomLng = (-70.6 - Math.random() * 0.1);
    this.updateCoordinates(
      parseFloat(randomLat.toFixed(4)),
      parseFloat(randomLng.toFixed(4))
    );
  }
}
