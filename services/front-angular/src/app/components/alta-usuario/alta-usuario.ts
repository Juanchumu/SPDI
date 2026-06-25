import { Component, signal, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';

import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';

@Component({
  selector: 'app-usuario-alta',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    MatCardModule,
    MatFormFieldModule,
    MatInputModule,
    MatButtonModule,
    MatSnackBarModule
  ],
  templateUrl: './alta-usuario.html'
})
export class AltaUsuario {

  private fb = inject(FormBuilder);
  private http = inject(HttpClient);
  private snack = inject(MatSnackBar);

  loading = signal(false);
  errorMsg = signal('');
  successMsg = signal('');

  form = this.fb.group({
    username: ['', [Validators.required, Validators.minLength(3)]],
    password: ['', [Validators.required, Validators.minLength(4)]]
  });

  crearUsuario() {
    if (this.form.invalid) {
      this.errorMsg.set('Formulario inválido');
      return;
    }

    this.loading.set(true);
    this.errorMsg.set('');
    this.successMsg.set('');

    const payload = this.form.value;

    this.http.post<any>('/api/v1/usuarios', payload)
      .subscribe({
        next: (res) => {
          this.loading.set(false);
          this.successMsg.set(`Usuario creado: ${res.username}`);

          this.snack.open('Usuario creado correctamente', 'OK', {
            duration: 2500
          });

          this.form.reset();
        },
        error: (err) => {
          this.loading.set(false);

          const msg = err?.error?.detail || 'Error al crear usuario';
          this.errorMsg.set(msg);

          this.snack.open(msg, 'Cerrar', {
            duration: 3500
          });
        }
      });
  }
}
