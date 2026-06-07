import { Component, AfterViewInit } from '@angular/core';
import * as L from 'leaflet';

@Component({
  selector: 'app-mapa-sectorizado',
  standalone: true,
  imports: [],
  templateUrl: './mapa-sectorizado.html',
  styleUrl: './mapa-sectorizado.css',
})
export class MapaSectorizado implements AfterViewInit {
  private map!: L.Map;

  ngAfterViewInit(): void {
    this.initMap();
  }
  private initMap(): void {
    this.map = L.map('map').setView(
      [-34.6037, -58.3816], // Buenos Aires
      11
    );
    L.tileLayer(
      'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
      {
        maxZoom: 19,
        attribution: '&copy; OpenStreetMap contributors'
      }
    ).addTo(this.map);
  }
}
