import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import {
  FormBuilder,
  ReactiveFormsModule,
  Validators
} from '@angular/forms';

import { Observable, map, startWith } from 'rxjs';

import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatAutocompleteModule } from '@angular/material/autocomplete';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';

interface Cliente {
  id: number;
  nombre: string;
  codigo_cliente: string;
  email: string | null;
  telefono: string | null;
  descripcion: string;
}

@Component({
  selector: 'app-informe-riesgo',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    MatCardModule,
    MatFormFieldModule,
    MatInputModule,
    MatAutocompleteModule,
    MatButtonModule,
    MatIconModule
  ],
  templateUrl: './informe-riesgo.html',
  styleUrl: './informe-riesgo.scss'
})
export class InformeRiesgo implements OnInit {

  private http = inject(HttpClient);
  private fb = inject(FormBuilder);

  readonly apiClientes =
    'http://localhost:8000/api/v1/clientes';

  readonly apiInformes =
    'http://localhost:8000/api/v1/informes/riesgo';

  responsable =
    localStorage.getItem('username') ?? '';

  clientes: Cliente[] = [];

  clienteSeleccionado: Cliente | null = null;

  cargando = false;
  exito = false;
  error = '';

  form = this.fb.group({
    cliente: [null as Cliente | null, Validators.required]
  });

  clientesFiltrados$!: Observable<Cliente[]>;

  ngOnInit(): void {

    this.http
      .get<Cliente[]>(this.apiClientes)
      .subscribe({
        next: (clientes) => {

          this.clientes = clientes;

          this.clientesFiltrados$ =
            this.form.controls.cliente.valueChanges.pipe(
              startWith(''),
              map(valor => {

                const texto =
                  typeof valor === 'string'
                    ? valor
                    : valor?.nombre ?? '';

                return this.filtrarClientes(texto);
              })
            );
        }
      });
  }

  private filtrarClientes(texto: string): Cliente[] {

    const filtro = texto.toLowerCase();

    return this.clientes.filter(cliente =>
      cliente.nombre.toLowerCase().includes(filtro)
    );
  }

  displayCliente(cliente: Cliente | null): string {
    return cliente?.nombre ?? '';
  }

  seleccionarCliente(cliente: Cliente): void {
    this.clienteSeleccionado = cliente;
  }

  generarInforme(): void {

    if (!this.clienteSeleccionado) {
      return;
    }

    this.cargando = true;
    this.error = '';
    this.exito = false;

    const payload = {
      responsable: this.responsable,
      cliente: this.clienteSeleccionado.nombre,
      descripcion: this.clienteSeleccionado.descripcion
    };

    this.http
      .post(this.apiInformes, payload)
      .subscribe({
        next: () => {

          this.cargando = false;
          this.exito = true;

        },
        error: (err) => {

          this.cargando = false;

          this.error =
            err?.error?.detail ??
            'No fue posible generar el informe';
        }
      });
  }
}
