import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';

import { MatToolbarModule } from '@angular/material/toolbar';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatCardModule } from '@angular/material/card';
import { MatChipsModule } from '@angular/material/chips';

@Component({
  selector: 'app-healt',
  standalone: true,
  imports: [
    CommonModule,
    MatToolbarModule,
    MatButtonModule,
    MatIconModule,
    MatCardModule,
    MatChipsModule
  ],
  templateUrl: './healt.html',
  styleUrls: ['./healt.css'],
})
export class Healt implements OnInit {

  health: any = null;

  constructor(private http: HttpClient) {}

  ngOnInit(): void {
    this.cargarHealth();
  }

  cargarHealth() {
    this.http.get('http://localhost:8000/api/v1/health')
      .subscribe({
        next: (data) => this.health = data,
        error: (err) => console.error(err)
      });
  }
}
