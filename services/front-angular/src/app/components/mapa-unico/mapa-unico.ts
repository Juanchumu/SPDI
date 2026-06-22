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

    // -------------------------
    // BASE LAYERS
    // -------------------------
    const osm = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© OpenStreetMap',
    });

    const esriStreets = L.tileLayer(
      'https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}',
      {
        attribution: 'Tiles © Esri',
      }
    );

    const esriSat = L.tileLayer(
      'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
      {
        attribution: 'Tiles © Esri',
      }
    );

    // default
    osm.addTo(this.map);

    const baseMaps = {
      'OpenStreetMap': osm,
      'ESRI Streets': esriStreets,
      'ESRI Satélite': esriSat,
    };

    L.control.layers(baseMaps, {}).addTo(this.map);

    // -------------------------
    // MARKER
    // -------------------------
    L.marker([coords[1], coords[0]])
      .addTo(this.map)
      .bindPopup(
        `ID: ${this.feature.properties.id}<br>
         Estado: ${this.feature.properties.estado}`
      )
      .openPopup();
  }
}
