import { MapaSectorizado } from '../mapa-sectorizado/mapa-sectorizado'

import { Component, signal, ViewChild, OnInit } from '@angular/core';


import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { Router } from '@angular/router';

import { MensajeAlerta } from '../mensaje-alerta/mensaje-alerta';


import { FormsModule } from '@angular/forms';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatSelectModule } from '@angular/material/select';

import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatToolbarModule } from '@angular/material/toolbar';
import { HttpClient } from '@angular/common/http';
import { AuthService } from '../../auth';

@Component({
  selector: 'app-mapa',
  imports: [
    MatButtonModule, FormsModule, MatFormFieldModule, MatSelectModule,
    //MatDialog, MatDialogModule,
    MensajeAlerta,
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

  clientes: any[] = [];
  clienteSeleccionado = '';

  public nombreUsuario: string | null = null;

  constructor(private http: HttpClient,private auth: AuthService,private dialog: MatDialog,
  private router: Router) {
    this.nombreUsuario = this.auth.getUsername();
  }
  ngOnInit(): void {
    //this.nombreUsuario = localStorage.getItem('username');
    this.nombreUsuario = this.auth.getUsername();
    this.cargarClientes();
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
  }/*
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
  */

  enviarPuntos() {

  if (!this.clienteSeleccionado) {
    alert('Seleccione un cliente');
    return;
  }

  const hoy = new Date();

  const dia = Number(
    hoy.getFullYear().toString() +
    String(hoy.getMonth() + 1).padStart(2, '0') +
    String(hoy.getDate()).padStart(2, '0')
  );

  for (const p of this.puntos) {

    this.http.post(
      'http://localhost:8000/api/v1/orden',
      {
        dia,
        lat: p.lat,
        lon: p.lon,
        username: this.nombreUsuario,
        cliente: this.clienteSeleccionado
      }
    ).subscribe();

  }

  this.mapa.limpiarPuntosCapturados();
  this.puntos = [];
  this.capturando = false;
  this.capturaFinalizada = false;
}
/*
  cargarClientes() {
  this.http.get<any>(
    `http://localhost:8000/api/v1/clientes?username=${this.nombreUsuario}`
  )
  .subscribe({
    next: (data) => {
      this.clientes = data.features ?? [];

      if (this.clientes.length > 0) {
        this.clienteSeleccionado =
          this.clientes[0].properties.cliente;
      }
    },
    error: (err) => {
      console.error('Error cargando clientes', err);
    }
  });
}
*/
cargarClientes() {
  this.http.get<any[]>(
    `http://localhost:8000/api/v1/clientes?username=${this.nombreUsuario}`
  )
  .subscribe({
    next: (data) => {

      console.log(data);

      this.clientes = data;

      if (this.clientes.length > 0) {
        this.clienteSeleccionado = this.clientes[0].nombre;
      }
    },
    error: (err) => {
      console.error(err);
      this.mostrarAlerta();
    }
  });
}
mostrarAlerta(): void {

  const dialogRef = this.dialog.open(MensajeAlerta, {
    width: '400px',
    disableClose: true,
    data: {
      titulo: 'No Hay clientes',
      mensaje: 'Todavia no hay clientes dados de alta!!.'
    }
  });

  dialogRef.afterClosed().subscribe(resultado => {
    if (resultado) {
      this.router.navigate(['/alta-cliente']);
    }
  });
}

}
