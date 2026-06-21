import { Component, OnInit, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';

import { MatCardModule } from '@angular/material/card';
import { MatExpansionModule } from '@angular/material/expansion';
import { MatChipsModule } from '@angular/material/chips';
import { MatIconModule } from '@angular/material/icon';
import { DatePipe } from '@angular/common';

export interface InformeRiesgo {
  id: number;
  responsable: string;
  cliente: string;
  estado: string;
  contenido: string;
  descripcion: string;
  created_at: string;
  updated_at: string;
}

@Component({
  selector: 'app-informe-riesgo-list',
  standalone: true,
  imports: [
    MatCardModule,
    MatExpansionModule,
    MatChipsModule,
    MatIconModule,
    DatePipe
  ],
  templateUrl: './informes-de-riesgo.html',
  styleUrls: ['./informes-de-riesgo.scss']
})
export class InformesDeRiesgo implements OnInit {

  private http = inject(HttpClient);

  informes: InformeRiesgo[] = [];

  readonly apiUrl = 'http://localhost:8000/api/v1';

  ngOnInit(): void {
    this.cargarInformes();
  }

  cargarInformes(): void {

    const username =
      localStorage.getItem('username') ?? 'admin';

    this.http.get<any>(
      `${this.apiUrl}/informes/riesgo?username=${username}`
    )
    .subscribe({
      next: (response) => {

        this.informes = response.features.map(
          (f: any) => ({
            id: f.properties.id,
            responsable: f.properties.responsable,
            cliente: f.properties.cliente,
            estado: f.properties.estado,
            contenido: f.properties.contenido,
            descripcion: f.properties.descripcion,
            created_at: f.properties.created_at,
            updated_at: f.properties.updated_at
          })
        );

      },
      error: console.error
    });
  }

  estadoClass(estado: string): string {

    const e = estado.toLowerCase();

    if (e.includes('listo')) {
      return 'estado-listo';
    }

    if (e.includes('pendiente')) {
      return 'estado-pendiente';
    }

    if (e.includes('rechazado')) {
      return 'estado-rechazado';
    }

    return 'estado-default';
  }
}
