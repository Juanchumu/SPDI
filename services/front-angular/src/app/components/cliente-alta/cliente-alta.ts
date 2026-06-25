import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { HttpClient, HttpParams } from '@angular/common/http';

import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';

@Component({
  selector: 'app-cliente-alta',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    MatCardModule,
    MatFormFieldModule,
    MatInputModule,
    MatButtonModule,
    MatIconModule,
    MatProgressSpinnerModule
  ],
  templateUrl: './cliente-alta.html',
  styleUrl: './cliente-alta.scss'
})
export class ClienteAlta {

  private fb = inject(FormBuilder);
  private http = inject(HttpClient);

  private readonly apiUrl = '/api/v1/clientes';

  cargando = false;
  exito = false;
  error = '';

  form = this.fb.nonNullable.group({
    nombre: ['', Validators.required],
    codigo_cliente: ['', Validators.required],
    email: ['', Validators.email],
    telefono: [''],
    descripcion: ['', Validators.required]
  });

  guardar(): void {

    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }

    const username = localStorage.getItem('username');

    if (!username) {
      this.error = 'No hay usuario logueado';
      return;
    }

    this.cargando = true;
    this.error = '';
    this.exito = false;

    const params = new HttpParams().set('username', username);

    this.http.post(this.apiUrl, this.form.getRawValue(), { params })
      .subscribe({
        next: () => {
          this.cargando = false;
          this.exito = true;

          this.form.reset({
            nombre: '',
            codigo_cliente: '',
            email: '',
            telefono: '',
            descripcion: ''
          });
        },
        error: (err) => {
          this.cargando = false;
          this.error =
            err?.error?.detail ??
            'No fue posible crear el cliente';
        }
      });
  }
}
