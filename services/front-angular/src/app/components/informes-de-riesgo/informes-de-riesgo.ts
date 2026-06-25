import { Component, OnInit, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';

import { MatCardModule } from '@angular/material/card';
import { MatExpansionModule } from '@angular/material/expansion';
import { MatChipsModule } from '@angular/material/chips';
import { MatIconModule } from '@angular/material/icon';
import { CommonModule, DatePipe } from '@angular/common';

export interface InformeRiesgo {
  id: number;
  responsable: string;
  cliente: string;
  estado: string;
  contenido: string | null;
  descripcion: string | null;
  created_at: string;
  updated_at: string | null;
}

@Component({
  selector: 'app-informe-riesgo-list',
  standalone: true,
  imports: [
    MatCardModule,
    MatExpansionModule,
    MatChipsModule,
    MatIconModule,
    DatePipe,
    CommonModule
  ],
  templateUrl: './informes-de-riesgo.html',
  styleUrls: ['./informes-de-riesgo.scss']
})
export class InformesDeRiesgo implements OnInit {

  private http = inject(HttpClient);

  informes: InformeRiesgo[] = [];

  readonly apiUrl = '/api/v1';

  ngOnInit(): void {
    this.cargarInformes();
  }

  cargarInformes(): void {

    const username =
      localStorage.getItem('username') ?? 'admin';

    this.http
      .get<InformeRiesgo[]>(
        `${this.apiUrl}/informes/riesgo?username=${username}`
      )
      .subscribe({
        next: (response) => {

          // ✔️ ahora es un array directo
          this.informes = response;
          console.log(this.informes);

        },
        error: (err) => {
          console.error('Error cargando informes', err);
        }
      });
  }

  estadoClass(estado: string): string {

    const e = estado.toLowerCase();

    if (e.includes('listo')) return 'estado-listo';
    if (e.includes('pendiente')) return 'estado-pendiente';
    if (e.includes('rechazado')) return 'estado-rechazado';

    return 'estado-default';
  }
}
