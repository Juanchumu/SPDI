import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatToolbarModule } from '@angular/material/toolbar';
import { HttpClient } from '@angular/common/http';


@Component({
  selector: 'app-healt',
  imports: [MatIconModule, MatToolbarModule, MatButtonModule, CommonModule],
  templateUrl: './healt.html',
  styleUrl: './healt.css',
})
export class Healt implements OnInit {
  health: any;
  constructor(private http: HttpClient) {}
  ngOnInit(): void {
    this.cargarHealth();
  }
  cargarHealth() {
    this.http.get('http://localhost:8000/api/v1/health')
      .subscribe({
        next: (data) => {
          this.health = data;
        },
        error: (err) => {
          console.error(err);
        }
      });
  }

}
