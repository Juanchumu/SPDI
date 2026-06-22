import { Component, OnInit } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { AuthService } from '../auth';

// Angular Material
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [
    FormsModule,
    MatFormFieldModule,
    MatInputModule,
    MatButtonModule,
    MatCardModule,
    MatProgressSpinnerModule
  ],
  templateUrl: './login.html',
  styleUrl: './login.css',
})
export class Login implements OnInit{
  username = '';
  password = '';
  loading = false;

  constructor(
    private http: HttpClient,
    private router: Router,
    private auth: AuthService
  ) {}

  login() {
    if (!this.username || !this.password || this.loading) return;

    this.loading = true;

    this.http.post<any>(
      'http://localhost:8000/api/v1/login',
      {
        username: this.username,
        password: this.password
      }
    ).subscribe({
      next: () => {
        localStorage.setItem('logged', 'true');
        localStorage.setItem('username', this.username);

        this.loading = false;
        this.router.navigate(['/dashboard-ordenes']);
      },
      error: () => {
        this.loading = false;
        alert('Usuario o contraseña incorrectos');
      }
    });
  }
  estaLogueado(): boolean {
    return this.auth.isLogged();
  }

  ngOnInit(): void {
    if (this.estaLogueado()) {
      this.router.navigate(['/mapa']);
    }
  }

}
