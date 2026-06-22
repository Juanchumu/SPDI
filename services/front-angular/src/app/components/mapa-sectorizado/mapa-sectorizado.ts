import { Component, AfterViewInit, Input, Output, EventEmitter, OnChanges, SimpleChanges } from '@angular/core';
import * as L from 'leaflet';
import 'leaflet.heat';

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
  @Output() puntoSeleccionado = new EventEmitter<{ lat: number; lon: number }>();

  private map!: L.Map;
  capaGeojson?: L.GeoJSON;

  private marcadoresCapturados: L.Marker[] = [];

  private heatLayer?: any;

  private clientColorMap = new Map<string, string>();
  private palette = [
    '#1e88e5', '#8e24aa', '#f4511e', '#3949ab',
    '#00acc1', '#7cb342', '#fb8c00', '#6d4c41'
  ];

  ngAfterViewInit(): void {
    this.initMap();
  }

  private initMap(): void {
    this.map = L.map('map').setView([-34.6037, -58.3816], 7);

    L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 11,
      attribution: '&copy; OpenStreetMap contributors'
    }).addTo(this.map);

    this.map.on('click', (e: any) => {
      if (!this.modoCaptura) return;

      const lat = e.latlng.lat;
      const lon = e.latlng.lng;

      const marker = L.marker([lat, lon]).addTo(this.map);
      this.marcadoresCapturados.push(marker);

      this.puntoSeleccionado.emit({ lat, lon });
    });
  }

  ngOnChanges(changes: SimpleChanges) {
    if (!this.map) return;

    if (changes['geojson'] && this.geojson) {
      this.renderGeojson();
      this.renderHeatmap(this.geojson.features);
    }
  }

  private renderGeojson(): void {
    if (this.capaGeojson) {
      this.map.removeLayer(this.capaGeojson);
    }

    this.capaGeojson = L.geoJSON(this.geojson, {
      pointToLayer: (feature: any, latlng) => {
        const p = feature.properties;

        const risk = p.riesgo ?? '-';
        const client = p.cliente ?? null;

        const fillColor = this.getRiskColor(risk);
        const borderColor = this.getClientColor(client);

        return L.circle(latlng, {
          radius: 1414, // ≈ 2000m cuadrado equivalente
          color: borderColor,
          weight: 2,
          fillColor,
          fillOpacity: 0.35
        });
      },

      onEachFeature: (feature: any, layer) => {
        const p = feature.properties;

        const pred = p.prediccion ? JSON.parse(p.prediccion) : null;

        layer.bindPopup(`
          <h3>Orden ${p.id}</h3>
          <b>Cliente:</b> ${p.cliente ?? 'Sin cliente'}<br>
          <b>Día:</b> ${p.dia}<br>
          <b>Estado:</b> ${p.estado}<br>
          <b>Riesgo:</b> ${p.riesgo ?? '-'}<br>
          <b>Porcentaje:</b> ${pred?.porcentaje_area_riesgo ?? 'Sin Calcular'}<br>
          <b>Modelo:</b> ${p.modelo}<br>
          <b>Enviado:</b> ${p.enviado}
        `);
      }
    });

    this.capaGeojson.addTo(this.map);

    const bounds = this.capaGeojson.getBounds();
    if (bounds.isValid()) {
      this.map.fitBounds(bounds);
    }
  }

  private renderHeatmap(points: any[]): void {
    if (!points) return;

    if (this.heatLayer) {
      this.map.removeLayer(this.heatLayer);
    }

    const heatData = points.map((p: any) => {
      const coords = p.geometry.coordinates;

      const risk = p.properties?.riesgo;

      const intensity =
        risk === 'alto' ? 1 :
        risk === 'bajo' ? 0.5 : 0.2;

      return [coords[1], coords[0], intensity];
    });

    this.heatLayer = (L as any).heatLayer(heatData, {
      radius: 25,
      blur: 15,
      maxZoom: 10
    }).addTo(this.map);
  }

  limpiarPuntosCapturados(): void {
    for (const marker of this.marcadoresCapturados) {
      this.map.removeLayer(marker);
    }
    this.marcadoresCapturados = [];
  }

  private getRiskColor(risk: string | null): string {
    switch (risk) {
      case 'alto': return '#e53935';
      case 'bajo': return '#43a047';
      default: return '#9e9e9e';
    }
  }

  private getClientColor(client: string | null): string {
    if (!client) return '#bdbdbd';

    if (this.clientColorMap.has(client)) {
      return this.clientColorMap.get(client)!;
    }

    const color = this.palette[this.clientColorMap.size % this.palette.length];
    this.clientColorMap.set(client, color);
    return color;
  }
}
