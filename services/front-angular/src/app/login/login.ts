import { Component } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-login',
  imports: [FormsModule],
  templateUrl: './login.html',
  styleUrl: './login.css',
})
export class Login {
  username = '';
  password = '';

  constructor(
    private http: HttpClient,
    private router: Router
  ) {}

  login() {

    this.http.post<any>(
      'http://localhost:8000/api/v1/login',
      {
        username: this.username,
        password: this.password
      }
    ).subscribe({
      next: () => {

        localStorage.setItem('logged','true');
        localStorage.setItem('username', this.username );

        this.router.navigate(['/home']);
      },
      error: () => {
        alert('Usuario o contraseña incorrectos');
      }
    });

  }
}
