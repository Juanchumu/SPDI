import { MapaSectorizado } from '../mapa-sectorizado/mapa-sectorizado'

import { Component, signal, ViewChild } from '@angular/core';

import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatToolbarModule } from '@angular/material/toolbar';
import { HttpClient } from '@angular/common/http';

@Component({
  selector: 'app-mapa',
  imports: [
    MatButtonModule,
    MatToolbarModule,
    MatIconModule,
    MapaSectorizado,
    ],
  templateUrl: './mapa.html',
  styleUrl: './mapa.css',
})
export class Mapa {
  @ViewChild(MapaSectorizado)
  mapa!: MapaSectorizado;
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
  capturaFinalizada = false;
  puntos: {lat:number, lon:number}[] = [];
  iniciarCaptura() {
    this.capturando = true;
  }
  agregarPunto(punto: {lat:number; lon:number}) {
    this.puntos.push(punto);
  }
  toggleCaptura(){
    if(this.capturando){
      this.capturaFinalizada = true;
    }
    this.capturando = !this.capturando;
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
    //Reiniciar flujo de envio
    this.mapa.limpiarPuntosCapturados();
    this.puntos = [];
    this.capturando = false;
    this.capturaFinalizada = false;
  }

}
