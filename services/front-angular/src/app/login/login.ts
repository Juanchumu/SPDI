import { Component } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import { FormsModule } from '@angular/forms';

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
export class Login {
  username = '';
  password = '';
  loading = false;

  constructor(
    private http: HttpClient,
    private router: Router
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
        this.router.navigate(['/home']);
      },
      error: () => {
        this.loading = false;
        alert('Usuario o contraseña incorrectos');
      }
    });
  }
}
