// script.js – Interactive UI for SPDI fire prediction

// Initialize Leaflet map
const map = L.map('map').setView([-34.6037, -58.3816], 5); // default to Buenos Aires

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
  attribution: '&copy; OpenStreetMap contributors',
  maxZoom: 19,
}).addTo(map);

let marker = null;
let selectedCoords = null;

function updateCoordInfo(lat, lng) {
  const info = document.getElementById('coordInfo');
  info.textContent = `Coordenadas: ${lat.toFixed(5)}, ${lng.toFixed(5)}`;
}

// Click on map to select point
map.on('click', function(e) {
  const { lat, lng } = e.latlng;
  selectedCoords = { lat, lng };
  if (marker) {
    marker.setLatLng(e.latlng);
  } else {
    marker = L.marker(e.latlng, { draggable: true }).addTo(map);
    marker.on('dragend', function(ev) {
      const pos = ev.target.getLatLng();
      selectedCoords = { lat: pos.lat, lng: pos.lng };
      updateCoordInfo(pos.lat, pos.lng);
    });
  }
  updateCoordInfo(lat, lng);
  toggleRunButton();
});

// Address search using Nominatim
async function searchAddress(query) {
  const url = `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(query)}`;
  const resp = await fetch(url, { headers: { 'Accept-Language': 'es' } });
  const data = await resp.json();
  return data;
}

document.getElementById('searchBtn').addEventListener('click', async () => {
  const query = document.getElementById('addressInput').value.trim();
  if (!query) return;
  const results = await searchAddress(query);
  if (results.length === 0) {
    alert('No se encontraron resultados');
    return;
  }
  const { lat, lon, display_name } = results[0];
  const latF = parseFloat(lat);
  const lonF = parseFloat(lon);
  map.setView([latF, lonF], 12);
  selectedCoords = { lat: latF, lng: lonF };
  if (marker) {
    marker.setLatLng([latF, lonF]);
  } else {
    marker = L.marker([latF, lonF], { draggable: true }).addTo(map);
    marker.on('dragend', function(ev) {
      const pos = ev.target.getLatLng();
      selectedCoords = { lat: pos.lat, lng: pos.lng };
      updateCoordInfo(pos.lat, pos.lng);
    });
  }
  updateCoordInfo(latF, lonF);
  toggleRunButton();
});

function toggleRunButton() {
  const btn = document.getElementById('runBtn');
  const date = document.getElementById('datePicker').value;
  btn.disabled = !(selectedCoords && date);
}

// Enable button when date changes
document.getElementById('datePicker').addEventListener('change', toggleRunButton);

// Main prediction flow
async function createOrder(dia, lat, lon) {
  const payload = { dia, lat, lon };
  const resp = await fetch('/api/v1/orden', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  if (!resp.ok) throw new Error('Error al crear la orden');
  return await resp.json(); // {id, status}
}

async function getOrder(id) {
  const resp = await fetch(`/api/v1/orden/${id}`);
  if (!resp.ok) throw new Error('Error al obtener la orden');
  return await resp.json();
}

async function pollOrder(id) {
  const maxAttempts = 60; // ~5 minutes
  const interval = 5000; // 5 sec
  for (let i = 0; i < maxAttempts; i++) {
    const data = await getOrder(id);
    
    // Mostrar estado en pantalla
    const info = document.getElementById('coordInfo');
    if (typeof data === 'string') {
        info.textContent = data; // Ej: "Estado: Validando.."
        if (data.includes("Error")) {
            throw new Error(data);
        }
    }

    if (typeof data === 'object' && data.prediccion) {
      info.textContent = "Estado: ¡Predicción Completada!";
      return data;
    }
    await new Promise(r => setTimeout(r, interval));
  }
  throw new Error('Tiempo de espera agotado');
}

document.getElementById('runBtn').addEventListener('click', async () => {
  const btn = document.getElementById('runBtn');
  btn.disabled = true;

  // Limpiar el resultado anterior de la pantalla y el mapa
  const box = document.getElementById('resultBox');
  const pre = document.getElementById('resultJson');
  box.hidden = true;
  pre.textContent = "";
  if (window.zonesLayer) {
    window.zonesLayer.clearLayers();
  }

  const dateStr = document.getElementById('datePicker').value; // YYYY-MM-DD
  const diaInt = parseInt(dateStr.replace(/-/g, ''), 10);
  const { lat, lng } = selectedCoords;
  try {
    const order = await createOrder(diaInt, lat, lng);
    const result = await pollOrder(order.id);
    const predData = JSON.parse(result.prediccion);
    const pre = document.getElementById('resultJson');
    pre.textContent = JSON.stringify(predData, null, 2);
    box.hidden = false;

    // Dibujar zonas críticas en el mapa
    if (!window.zonesLayer) {
      window.zonesLayer = L.layerGroup().addTo(map);
    }
    
    if (predData.zonas_criticas && predData.zonas_criticas.length > 0) {
      const latBuffer = 0.009;
      const lonBuffer = 0.011;
      const left = lng - lonBuffer;
      const right = lng + lonBuffer;
      const bottom = lat - latBuffer;
      const topLat = lat + latBuffer;

      predData.zonas_criticas.forEach(zona => {
        // zona tiene x1, y1, x2, y2 en coordenadas de pixel (0 a 200)
        const boxLeft = left + (zona.x1 / 200) * (right - left);
        const boxRight = left + (zona.x2 / 200) * (right - left);
        const boxTop = topLat - (zona.y1 / 200) * (topLat - bottom);
        const boxBottom = topLat - (zona.y2 / 200) * (topLat - bottom);

        const bounds = [[boxBottom, boxLeft], [boxTop, boxRight]];
        L.rectangle(bounds, {color: "#ff0000", weight: 3, fillOpacity: 0.3}).addTo(window.zonesLayer)
          .bindPopup(`<b>ZONA CRÍTICA</b><br>Píxeles afectados: ${zona.pixels}`);
      });
      // Hacer zoom a la zona
      map.setView([lat, lng], 13);
    }

  } catch (e) {
    alert(e.message);
  } finally {
    btn.disabled = false;
  }
});
