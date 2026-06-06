// script.js – Interactive SPDI Risk Command Logic with Light Mode support

// Initialize Leaflet map with CartoDB Dark Matter tile layer
const map = L.map('map', {
  zoomControl: false,
  attributionControl: false
}).setView([-34.6037, -58.3816], 5); // default to Buenos Aires

// Store tileLayer reference to switch URLs on theme toggle
const tileLayer = L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
  maxZoom: 19
}).addTo(map);

// Add zoom control at bottom-right for clean HUD look
L.control.zoom({
  position: 'bottomright'
}).addTo(map);

let marker = null;
let selectedCoords = null;
let riskRectangles = [];

// DOM Elements
const dateInput = document.getElementById('dateInput');
const addressInput = document.getElementById('addressInput');
const searchBtn = document.getElementById('searchBtn');
const latInput = document.getElementById('latInput');
const lngInput = document.getElementById('lngInput');
const predictBtn = document.getElementById('predictBtn');
const statusDot = document.getElementById('statusDot');
const statusText = document.getElementById('statusText');
const statusDetails = document.getElementById('statusDetails');
const displayLat = document.getElementById('displayLat');
const displayLng = document.getElementById('displayLng');

// Results Panel Elements
const resultsPanel = document.getElementById('results-panel');
const orderIdText = document.getElementById('orderIdText');
const riskBadge = document.getElementById('riskBadge');
const riskCircle = document.getElementById('riskCircle');
const riskPercentText = document.getElementById('riskPercentText');
const modelLabel = document.getElementById('modelLabel');
const resultsDate = document.getElementById('resultsDate');
const zonesList = document.getElementById('zonesList');
const closeReportBtn = document.getElementById('closeReportBtn');

// Theme Switcher Elements
const themeToggleBtn = document.getElementById('themeToggleBtn');
const htmlEl = document.documentElement;

// Initialize theme state from DOM
let isDarkMode = htmlEl.classList.contains('dark');
updateThemeUI(isDarkMode);

themeToggleBtn.addEventListener('click', () => {
  isDarkMode = !isDarkMode;
  if (isDarkMode) {
    htmlEl.classList.add('dark');
  } else {
    htmlEl.classList.remove('dark');
  }
  updateThemeUI(isDarkMode);
});

function updateThemeUI(isDark) {
  if (isDark) {
    themeToggleBtn.textContent = 'light_mode'; // icon to switch to light mode
    tileLayer.setUrl('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png');
  } else {
    themeToggleBtn.textContent = 'dark_mode'; // icon to switch to dark mode
    tileLayer.setUrl('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png');
  }
}

// Helper: Sync coordinates from map marker to inputs
function updateCoordFields(lat, lng) {
  selectedCoords = { lat, lng };
  latInput.value = lat.toFixed(6);
  lngInput.value = lng.toFixed(6);
  displayLat.textContent = lat.toFixed(4);
  displayLng.textContent = lng.toFixed(4);
  togglePredictButton();
}

// Map click event
map.on('click', function(e) {
  const { lat, lng } = e.latlng;
  placeMarker(lat, lng);
});

// Coordinate input changes (manual entry)
function handleCoordinateInputChange() {
  const lat = parseFloat(latInput.value);
  const lng = parseFloat(lngInput.value);
  if (!isNaN(lat) && !isNaN(lng)) {
    placeMarker(lat, lng, false); // place marker without reflying map
  }
}
latInput.addEventListener('input', handleCoordinateInputChange);
lngInput.addEventListener('input', handleCoordinateInputChange);

// Place marker on coordinates
function placeMarker(lat, lng, fly = true) {
  selectedCoords = { lat, lng };
  if (marker) {
    marker.setLatLng([lat, lng]);
  } else {
    marker = L.marker([lat, lng], { draggable: true }).addTo(map);
    marker.on('dragend', function(ev) {
      const pos = ev.target.getLatLng();
      updateCoordFields(pos.lat, pos.lng);
    });
  }
  updateCoordFields(lat, lng);
  if (fly) {
    map.flyTo([lat, lng], 12, { duration: 1.2 });
  }
}

// Enable/Disable predict button
function togglePredictButton() {
  const dateVal = dateInput.value;
  predictBtn.disabled = !(selectedCoords && dateVal);
}
dateInput.addEventListener('change', togglePredictButton);

// Nominatim Search Address
async function searchAddress(query) {
  const url = `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(query)}`;
  const resp = await fetch(url, { headers: { 'Accept-Language': 'es' } });
  return await resp.json();
}

searchBtn.addEventListener('click', async () => {
  const query = addressInput.value.trim();
  if (!query) return;
  
  updateStatusUI('Sistema: Buscando', 'bg-primary-fixed', `Buscando ubicación: "${query}"...`);
  try {
    const results = await searchAddress(query);
    if (results.length === 0) {
      alert('Ubicación no encontrada.');
      updateStatusUI('Sistema: En espera', 'bg-on-surface-variant', 'Ubicación no encontrada. Listo para reintentar.');
      return;
    }
    const { lat, lon } = results[0];
    const latF = parseFloat(lat);
    const lonF = parseFloat(lon);
    placeMarker(latF, lonF);
    updateStatusUI('Sistema: En espera', 'bg-on-surface-variant', 'Ubicación encontrada. Listo para predecir.');
  } catch (err) {
    alert('Error al buscar dirección: ' + err.message);
    updateStatusUI('Sistema: En espera', 'bg-on-surface-variant', 'Error en la búsqueda.');
  }
});

// UI State Helpers
function updateStatusUI(text, dotClass, detailsText) {
  statusText.textContent = text;
  statusDot.className = `w-2.5 h-2.5 rounded-full transition-colors ${dotClass}`;
  statusDetails.textContent = detailsText;
}

// API Calls
async function createOrder(dia, lat, lon) {
  const payload = { dia, lat, lon };
  const resp = await fetch('/api/v1/orden', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  if (!resp.ok) throw new Error('Fallo al crear la orden de predicción');
  return await resp.json(); // {id, status}
}

async function getOrder(id) {
  const resp = await fetch(`/api/v1/orden/${id}`);
  if (!resp.ok) throw new Error('Fallo al recuperar los detalles de la orden');
  return await resp.json();
}

async function pollOrder(id) {
  const maxAttempts = 60; // 5 mins
  const interval = 5000;  // 5 secs
  
  for (let i = 0; i < maxAttempts; i++) {
    const data = await getOrder(id);
    
    if (typeof data === 'string') {
      const displayStatus = data.replace("Estado: ", "");
      updateStatusUI('Sistema: Procesando', 'bg-primary-fixed-dim animate-pulse', `Fase: ${displayStatus}`);
      if (data.includes("Error") || data.includes("error")) {
        throw new Error(data);
      }
    }
    
    if (typeof data === 'object' && data.prediccion) {
      updateStatusUI('Sistema: Finalizado', 'bg-risk-low', 'Análisis completado. Reporte generado.');
      return data;
    }
    await new Promise(r => setTimeout(r, interval));
  }
  throw new Error('Tiempo de espera de predicción agotado');
}

// Clean map overlays
function clearMapOverlays() {
  riskRectangles.forEach(rect => map.removeLayer(rect));
  riskRectangles = [];
}

// Show results panel and draw critical zones on Leaflet
function renderPredictionResult(result, dateStr) {
  const predData = JSON.parse(result.prediccion);
  
  // Set up details
  orderIdText.textContent = `ID: #ORD-${result.id}-XGB`;
  modelLabel.textContent = result.modelo_utilizado;
  resultsDate.textContent = dateStr;
  
  // Risk evaluation
  const risk = predData.riesgo || 'bajo';
  const percentage = predData.porcentaje_area_riesgo || 0;
  
  if (risk === 'alto') {
    riskBadge.textContent = 'RIESGO ALTO';
    riskBadge.className = 'px-3 py-1 rounded-full font-label-caps text-label-caps border border-risk-high text-risk-high bg-risk-high/10 shadow-[0_0_8px_rgba(255,59,59,0.2)]';
    riskCircle.style.color = '#ff3b3b';
  } else {
    riskBadge.textContent = 'RIESGO BAJO';
    riskBadge.className = 'px-3 py-1 rounded-full font-label-caps text-label-caps border border-risk-low text-risk-low bg-risk-low/10';
    riskCircle.style.color = '#00ff88';
  }
  
  // Update circle animation (SVG circumference is 364.4)
  const offset = 364.4 - (364.4 * percentage / 100);
  riskCircle.style.strokeDashoffset = offset;
  riskPercentText.textContent = `${percentage.toFixed(1)}%`;
  
  // Inject critical zones
  zonesList.innerHTML = '';
  clearMapOverlays();
  
  const lat = selectedCoords.lat;
  const lng = selectedCoords.lng;
  const zones = predData.zonas_criticas || [];
  
  if (zones.length === 0) {
    zonesList.innerHTML = '<div class="text-[11px] text-on-surface-variant/40 italic">Ninguna zona crítica detectada.</div>';
  } else {
    // 0.009 and 0.011 bounding box constants
    const latBuffer = 0.009;
    const lonBuffer = 0.011;
    const left = lng - lonBuffer;
    const right = lng + lonBuffer;
    const bottom = lat - latBuffer;
    const topLat = lat + latBuffer;
    
    zones.forEach((zona, index) => {
      // Scale pixel coordinates to WGS84 coordinates
      const boxLeft = left + (zona.x1 / 200) * (right - left);
      const boxRight = left + (zona.x2 / 200) * (right - left);
      const boxTop = topLat - (zona.y1 / 200) * (topLat - bottom);
      const boxBottom = topLat - (zona.y2 / 200) * (topLat - bottom);
      
      const bounds = [[boxBottom, boxLeft], [boxTop, boxRight]];
      
      // Color coded by risk level
      const color = risk === 'alto' ? '#ff3b3b' : '#ffaa00';
      const rect = L.rectangle(bounds, {
        color: color,
        weight: 2,
        fillOpacity: 0.35,
        dashArray: '3, 5'
      }).addTo(map)
        .bindPopup(`<b>Zona Crítica #${index+1}</b><br>Pixeles: ${zona.pixels}`);
      
      riskRectangles.push(rect);
      
      // Add HTML list item (fully responsive theme-ready color styling)
      const item = document.createElement('div');
      item.className = 'bg-white/5 p-2 rounded border border-white/5 flex justify-between items-center';
      item.innerHTML = `
        <div class="flex flex-col">
          <span class="text-[9px] text-on-surface-variant/60 font-label-caps">LÍMITES: ${zona.x1},${zona.y1} a ${zona.x2},${zona.y2}</span>
          <span class="font-data-sm text-[11px] text-on-surface">Cluster #${index+1} (${zona.pixels} px)</span>
        </div>
        <span class="w-1.5 h-1.5 rounded-full" style="background-color: ${color}; box-shadow: 0 0 6px ${color}"></span>
      `;
      zonesList.appendChild(item);
    });
  }
  
  // Slide in results panel
  resultsPanel.classList.remove('hidden-state');
  map.flyTo([lat, lng], 13, { duration: 1.5 });
}

// Predict button action
predictBtn.addEventListener('click', async () => {
  const dateStr = dateInput.value; // YYYY-MM-DD
  const diaInt = parseInt(dateStr.replace(/-/g, ''), 10);
  const { lat, lng } = selectedCoords;
  
  // Reset previous result panel
  resultsPanel.classList.add('hidden-state');
  clearMapOverlays();
  
  predictBtn.disabled = true;
  updateStatusUI('Sistema: Iniciando', 'bg-primary-fixed-dim animate-pulse', 'Creando orden de análisis satelital...');
  
  try {
    const order = await createOrder(diaInt, lat, lng);
    updateStatusUI('Sistema: En cola', 'bg-primary-fixed-dim', `Orden #${order.id} enviada. Esperando procesamiento...`);
    
    const result = await pollOrder(order.id);
    renderPredictionResult(result, dateStr);
  } catch (err) {
    alert(err.message);
    updateStatusUI('Sistema: En espera', 'bg-error', `Fallo: ${err.message}`);
  } finally {
    togglePredictButton();
  }
});

// Close panel action
closeReportBtn.addEventListener('click', () => {
  resultsPanel.classList.add('hidden-state');
  clearMapOverlays();
});
