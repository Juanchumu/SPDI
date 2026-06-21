import { Component, AfterViewInit } from '@angular/core';
import * as L from 'leaflet';
import { ActivatedRoute } from '@angular/router';

@Component({
  selector: 'app-orden-detail-map',
  standalone: true,
  templateUrl: './mapa-unico.html',
})
export class MapaUnico implements AfterViewInit {
  private map!: L.Map;

  feature: any;

  constructor(private route: ActivatedRoute) {
    this.feature = history.state.feature;
  }

  ngAfterViewInit(): void {
    const coords = this.feature.geometry.coordinates;

    this.map = L.map('map').setView([coords[1], coords[0]], 10);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: 'OSM',
    }).addTo(this.map);

    L.marker([coords[1], coords[0]])
      .addTo(this.map)
      .bindPopup(
        `ID: ${this.feature.properties.id}<br>
         Estado: ${this.feature.properties.estado}`
      )
      .openPopup();
  }
}
