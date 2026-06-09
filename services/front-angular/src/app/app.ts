import { Component, signal } from '@angular/core';
import { RouterOutlet } from '@angular/router';

import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatToolbarModule } from '@angular/material/toolbar';
import { MapaSectorizado } from './components/mapa-sectorizado/mapa-sectorizado'
import { HttpClient } from '@angular/common/http';

@Component({
  selector: 'app-root',
  imports: [
    RouterOutlet,
    MatButtonModule,
    MatToolbarModule,
    MatIconModule,
    MapaSectorizado
  ],
  templateUrl: './app.html',
  styleUrl: './app.css'
})
export class App {
  protected readonly title = signal('front-angular-spdi');
  geojsonData: any;
  constructor(private http: HttpClient){}
  recuperar_ordenes(){
    console.log("click");
    this.http.get('http://localhost:8000/api/v1/recuperar_ordenes').subscribe((geojson) => {
      console.log(geojson);
      this.geojsonData = geojson;
    });
  }
  // captura de puntos
  capturando = false;
  puntos: {lat:number, lon:number}[] = [];
  iniciarCaptura() {
    this.capturando = true;
  }
  agregarPunto(punto: {lat:number, lon:number}) {
    this.puntos.push(punto);
  }
  enviarPuntos() {
    const dia = 20211125;
    for (const p of this.puntos) {
      this.http.post(
        'http://localhost:8000/api/v1/orden',
        {
          dia,
          lat: p.lat,
          lon: p.lon
        }
      ).subscribe();
    }
  }
}
