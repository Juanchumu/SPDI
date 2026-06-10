import { MapaSectorizado } from '../mapa-sectorizado/mapa-sectorizado'

import { Component, signal, ViewChild, OnInit } from '@angular/core';

import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatToolbarModule } from '@angular/material/toolbar';
import { HttpClient } from '@angular/common/http';
import { AuthService } from '../../auth';

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
export class Mapa implements OnInit {
  @ViewChild(MapaSectorizado)
  mapa!: MapaSectorizado;
  protected readonly title = signal('front-angular-spdi');
  geojsonData: any;

  public nombreUsuario: string | null = null;

  constructor(private http: HttpClient,private auth: AuthService) {
    this.nombreUsuario = this.auth.getUsername();
  }
  ngOnInit(): void {
    //this.nombreUsuario = localStorage.getItem('username');
    this.nombreUsuario = this.auth.getUsername();
  }
  cerrarSesion() {this.auth.logout();}
  recuperar_ordenes(){
    console.log("click");
    this.http.get(`http://localhost:8000/api/v1/recuperar_ordenes?username=${this.nombreUsuario}`).subscribe((geojson) => {
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
    //const dia = 20211125;
    const hoy = new Date();
    const dia = Number(
      hoy.getFullYear().toString() +
        String(hoy.getMonth() + 1).padStart(2, '0') +
        String(hoy.getDate()).padStart(2, '0')
    );
    console.log(dia); // 20260609
    for (const p of this.puntos) {
      this.http.post(
        'http://localhost:8000/api/v1/orden',
        {
          dia,
          lat: p.lat,
          lon: p.lon,
          username: this.nombreUsuario
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
