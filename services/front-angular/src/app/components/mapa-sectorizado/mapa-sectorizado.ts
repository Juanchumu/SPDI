import { Component, AfterViewInit, Input, Output, EventEmitter, OnChanges, SimpleChanges } from '@angular/core';
import * as L from 'leaflet';

@Component({
  selector: 'app-mapa-sectorizado',
  standalone: true,
  imports: [],
  templateUrl: './mapa-sectorizado.html',
  styleUrl: './mapa-sectorizado.css',
})
export class MapaSectorizado implements AfterViewInit, OnChanges {
  @Input() geojson: any;
  @Input() modoCaptura = false;
  @Output() puntoSeleccionado = new EventEmitter<{lat:number;lon:number}>();

  private map!: L.Map;
  capaGeojson?: L.GeoJSON;

  private marcadoresCapturados: L.Marker[] = [];

  ngAfterViewInit(): void {
    this.initMap();
  }
  private initMap(): void {
    this.map = L.map('map').setView(
      [-34.6037, -58.3816], // Buenos Aires
      7 //zoom 7
    );
    L.tileLayer(
      'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
      {
        maxZoom: 11, //maximo zoom
        attribution: '&copy; OpenStreetMap contributors'
      }
    ).addTo(this.map);
    //captura de clicks
    this.map.on('click', (e: any) => {
      if (!this.modoCaptura) {return;}
      const lat = e.latlng.lat;
      const lon = e.latlng.lng;
      const marker = L.marker([lat, lon]).addTo(this.map);
      this.marcadoresCapturados.push(marker);
      //L.marker([lat, lon]).addTo(this.map);
      this.puntoSeleccionado.emit({lat: e.latlng.lat,lon: e.latlng.lng });
    });
  }

  limpiarPuntosCapturados(): void {

  for (const marker of this.marcadoresCapturados) {
    this.map.removeLayer(marker);
  }

  this.marcadoresCapturados = [];
  }
  ngOnChanges(changes: SimpleChanges){
    //para evitar un problema de inicio antes que recibir
    if (!this.map) {
      return;
    }
    //
    if (changes['geojson'] && this.geojson){
      if(this.capaGeojson){
        this.map.removeLayer(this.capaGeojson);
      }
      this.capaGeojson = L.geoJSON(this.geojson, {
        pointToLayer: (feature: any, latlng) => {
          const estado = feature.properties.estado;
          const color = estado === 'Predicha' ? 'green' : 'orange';
          return L.circleMarker(latlng, {
            radius: 8,
            color,
            fillColor: color,
            fillOpacity: 0.8
          });
        },
        onEachFeature: (feature: any, layer) => {
          const p = feature.properties;
          layer.bindPopup(`
                          <h3>Orden ${p.id}</h3>
                          <b>Día:</b> ${p.dia}<br>
                          <b>Estado:</b> ${p.estado}<br>
                          <b>Modelo:</b> ${p.modelo}<br>
                          <b>Enviado:</b> ${p.enviado}
                          `);
        }
      });

      this.capaGeojson.addTo(this.map);
      //ahora que se ajuste automaticamente a las ordenes
      const bounds = this.capaGeojson.getBounds();
      if (bounds.isValid()) {
        this.map.fitBounds(bounds);
      }
    }
  }
}
