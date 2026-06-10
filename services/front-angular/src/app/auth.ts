import { Service } from '@angular/core';
import { Injectable } from '@angular/core';
import { Router } from '@angular/router';

@Injectable({
  providedIn: 'root'
})

//@Service()
export class AuthService {
  constructor(private router: Router) {}
  login() {
    localStorage.setItem('logged','true');
  }

  logout() {
    localStorage.removeItem('logged');
    this.router.navigate(['/login']);
  }

  isLogged(): boolean {
    return localStorage.getItem('logged') === 'true';
  }
  getUsername(): string {
    return localStorage.getItem('username') || '';
  }
}
