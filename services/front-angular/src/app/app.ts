import { Component, signal, ViewChild } from '@angular/core';
import { RouterOutlet, RouterLink } from '@angular/router';
import { MatButtonModule } from '@angular/material/button';
import { MatToolbarModule } from '@angular/material/toolbar';
import { MatIconModule } from '@angular/material/icon';
import { AuthService } from './auth';


@Component({
  selector: 'app-root',
  imports: [
    RouterOutlet,
    RouterLink,
    MatButtonModule,
    MatToolbarModule,
    MatIconModule
  ],
  templateUrl: './app.html',
  styleUrl: './app.css'
})
export class App {
  //public estaLogueado : boolean =
  constructor(private auth: AuthService) {}
  estaLogueado(): boolean {return this.auth.isLogged();}
  cerrarSesion() {this.auth.logout();}
  nombreDeSesion(): string {return this.auth.getUsername();}
  esAdmin() : boolean {return (this.nombreDeSesion() === "admin");}
}
