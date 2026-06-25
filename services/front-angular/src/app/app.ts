import { Component, signal, ViewChild } from '@angular/core';
import { RouterOutlet, RouterLink } from '@angular/router';
import { MatButtonModule } from '@angular/material/button';
import { MatToolbarModule } from '@angular/material/toolbar';
import { MatIconModule } from '@angular/material/icon';
import { AuthService } from './auth';
import { ThemeService } from './services/theme';

import { MatSlideToggleModule } from '@angular/material/slide-toggle';

import { MatTooltipModule } from '@angular/material/tooltip';


@Component({
  selector: 'app-root',
  imports: [
    RouterOutlet,
    RouterLink,
    MatButtonModule,
    MatToolbarModule,
    MatIconModule,
    MatSlideToggleModule, MatTooltipModule
  ],
  templateUrl: './app.html',
  styleUrl: './app.css'
})
export class App {
  //public estaLogueado : boolean =
  //public themeService = inject(ThemeService);
  constructor(private auth: AuthService, public themeService: ThemeService) {
  this.themeService.init();}
  estaLogueado(): boolean {return this.auth.isLogged();}
  cerrarSesion() {this.auth.logout();}
  nombreDeSesion(): string {return this.auth.getUsername();}
  esAdmin() : boolean {return (this.nombreDeSesion() === "admin");}
}
