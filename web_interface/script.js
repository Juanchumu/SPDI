function navTo(viewName) {
    // Hide all views
    document.querySelectorAll('.content-view').forEach(v => v.classList.remove('active'));
    
    // Deactivate nav links
    document.querySelectorAll('.nav-item').forEach(v => {
        v.classList.remove('text-primary', 'font-bold', 'border-r-4', 'border-primary', 'bg-surface-container-high');
        v.classList.add('text-on-surface-variant', 'hover:bg-surface-container-high');
    });

    // Show target view
    const target = document.getElementById('content-' + viewName);
    if(target) target.classList.add('active');

    // Activate nav link
    const link = document.getElementById('nav-' + viewName);
    if(link) {
        link.classList.remove('text-on-surface-variant', 'hover:bg-surface-container-high');
        link.classList.add('text-primary', 'font-bold', 'border-r-4', 'border-primary', 'bg-surface-container-high');
    }

    // Workaround for Leaflet render bug when container is hidden
    if(viewName === 'map' && map) {
        setTimeout(() => map.invalidateSize(), 100);
    }
}

// ==========================================
// LOGIN
// ==========================================
const loginForm = document.getElementById('login-form');
if (loginForm) {
    loginForm.addEventListener('submit', (e) => {
        e.preventDefault();
        localStorage.setItem('isLoggedIn', 'true');
        performLogin();
    });
}

function performLogin() {
    document.getElementById('view-login').classList.remove('active');
    document.getElementById('view-app').classList.add('active');
    navTo('dashboard');
    fetchExistingOrders();
}

function logout() {
    localStorage.removeItem('isLoggedIn');
    document.getElementById('view-app').classList.remove('active');
    document.getElementById('view-login').classList.add('active');
}

// Auto-login if previously logged in
window.addEventListener('DOMContentLoaded', () => {
    if (localStorage.getItem('isLoggedIn') === 'true') {
        performLogin();
    }
});

function togglePassword() {
    const input = document.getElementById('password-input');
    const icon = document.getElementById('pw_icon');
    if (input.type === 'password') {
        input.type = 'text';
        icon.innerText = 'visibility_off';
    } else {
        input.type = 'password';
        icon.innerText = 'visibility';
    }
}

// Background effect for login
document.addEventListener('mousemove', (e) => {
    const img = document.getElementById('login-bg-img');
    if(img && document.getElementById('view-login').classList.contains('active')) {
        const x = (window.innerWidth / 2 - e.pageX) / 80;
        const y = (window.innerHeight / 2 - e.pageY) / 80;
        img.style.transform = `scale(1.05) translate(${x}px, ${y}px)`;
    }
});


// ==========================================
// MAP & API LOGIC
// ==========================================
let map;
let marker;
let drawnRectangles = [];
const API_URL = 'http://localhost:8000/api/v1';

// Init Map
document.addEventListener('DOMContentLoaded', () => {
    map = L.map('leaflet-map', {
        zoomControl: false,
        attributionControl: false
    }).setView([-34.6037, -58.3816], 5);

    L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
        maxZoom: 19
    }).addTo(map);

    L.control.zoom({ position: 'bottomright' }).addTo(map);

    // Click on map to set coordinates
    map.on('click', function(e) {
        const lat = parseFloat(e.latlng.lat).toFixed(4);
        const lon = parseFloat(e.latlng.lng).toFixed(4);
        
        document.getElementById('input-lat').value = lat;
        document.getElementById('input-lon').value = lon;
        
        if (marker) {
            marker.setLatLng(e.latlng);
        } else {
            marker = L.marker(e.latlng).addTo(map);
        }
    });
});

function drawRiskBox(lat, lon, riskPercent) {
    const kmDegrees = 0.09; // Approx 10km radius -> 20km square
    const bounds = [[lat - kmDegrees, lon - kmDegrees], [lat + kmDegrees, lon + kmDegrees]];
    
    let color = '#414844'; // Estable (Low)
    if (riskPercent > 50) color = '#b5270e'; // Extremo (High)
    else if (riskPercent > 20) color = '#d7e8cb'; // Moderado (Medium)

    const rect = L.rectangle(bounds, {
        color: color,
        weight: 2,
        fillColor: color,
        fillOpacity: 0.3
    }).addTo(map);
    
    drawnRectangles.push(rect);
    map.flyToBounds(bounds, { padding: [50, 50] });
}

function updateStatusBanner(text, isError=false, isSuccess=false) {
    const banner = document.getElementById('map-status-banner');
    const textEl = document.getElementById('map-status-text');
    banner.classList.remove('hidden');
    textEl.innerText = text;
    
    const dot = banner.querySelector('div');
    dot.className = 'w-3 h-3 rounded-full'; // reset
    if(isError) dot.classList.add('bg-error');
    else if(isSuccess) dot.classList.add('bg-primary-fixed');
    else dot.classList.add('bg-secondary', 'animate-pulse');
}

// Global store for orders to render in dashboard
let ordersDB = [];

function updateDashboardTable() {
    const tbody = document.getElementById('orders-table-body');
    if(!tbody) return;
    
    if(ordersDB.length === 0) {
        tbody.innerHTML = `<tr><td class="px-6 py-4 text-outline" colspan="6">Sin órdenes generadas.</td></tr>`;
        return;
    }

    tbody.innerHTML = '';
    ordersDB.forEach(order => {
        let statusBadge = `<span class="px-3 py-1 bg-surface-container text-on-surface-variant rounded-full text-[10px] font-bold uppercase">${order.status}</span>`;
        if(order.status === 'Predicha') statusBadge = `<span class="px-3 py-1 bg-primary-fixed text-primary rounded-full text-[10px] font-bold uppercase">Completado</span>`;
        if(order.status === 'error') statusBadge = `<span class="px-3 py-1 bg-error-container text-error rounded-full text-[10px] font-bold uppercase">Error</span>`;

        let resultBadge = '-';
        if(order.prediction !== null && order.prediction !== undefined) {
            let pct = 0;
            try {
                let predObj = typeof order.prediction === 'string' ? JSON.parse(order.prediction) : order.prediction;
                if (predObj && predObj.porcentaje_area_riesgo !== undefined) {
                    pct = parseFloat(predObj.porcentaje_area_riesgo);
                } else {
                    pct = parseFloat(order.prediction) * 100;
                }
            } catch(e) {
                pct = parseFloat(order.prediction) * 100;
            }
            
            if (!isNaN(pct)) {
                if(pct > 50) resultBadge = `<span class="risk-high px-3 py-1 rounded-full text-[10px] font-bold uppercase text-error bg-error-container">Alto (${pct.toFixed(1)}%)</span>`;
                else if(pct > 20) resultBadge = `<span class="risk-medium px-3 py-1 rounded-full text-[10px] font-bold uppercase text-on-tertiary-container bg-tertiary-container">Medio (${pct.toFixed(1)}%)</span>`;
                else resultBadge = `<span class="risk-low px-3 py-1 rounded-full text-[10px] font-bold uppercase text-primary bg-primary-container">Bajo (${pct.toFixed(1)}%)</span>`;
            } else {
                resultBadge = `<span class="px-3 py-1 rounded-full text-[10px] font-bold uppercase">Error de Parseo</span>`;
            }
        }

        let actionBtn = '-';
        if (order.status !== 'Predicha' && order.status !== 'Cancelada' && !order.status.toLowerCase().includes('error')) {
            actionBtn = `<button onclick="cancelOrder(${order.id})" class="text-error hover:text-on-error-container text-[12px] font-bold flex items-center gap-1 transition-colors"><span class="material-symbols-outlined text-[16px]">cancel</span> Cancelar</button>`;
        }

        const tr = document.createElement('tr');
        tr.className = 'hover:bg-surface-container-low transition-colors group';
        tr.innerHTML = `
            <td class="px-6 py-4 font-body-md font-bold text-primary">#${order.id}</td>
            <td class="px-6 py-4">${order.lat}</td>
            <td class="px-6 py-4">${order.lon}</td>
            <td class="px-6 py-4 text-on-surface-variant">${order.dia}</td>
            <td class="px-6 py-4">${statusBadge}</td>
            <td class="px-6 py-4">${resultBadge}</td>
            <td class="px-6 py-4 text-right flex justify-end">${actionBtn}</td>
        `;
        tbody.appendChild(tr);
    });
}

async function cancelOrder(id) {
    try {
        const resp = await fetch(`${API_URL}/orden/${id}`, { method: 'DELETE' });
        if (!resp.ok) throw new Error();
        
        // Update local DB
        const dbOrder = ordersDB.find(o => o.id === id);
        if(dbOrder) dbOrder.status = 'Cancelada';
        updateDashboardTable();
    } catch (e) {
        alert('No se pudo cancelar la orden. Puede que ya haya finalizado.');
    }
}

async function fetchExistingOrders() {
    try {
        const resp = await fetch(`${API_URL}/orden`);
        if (!resp.ok) return;
        const data = await resp.json();
        ordersDB = data;
        updateDashboardTable();
        
        // Resume polling for any order that is not finished
        ordersDB.forEach(o => {
            if (o.status !== 'Predicha' && o.status !== 'Cancelada' && !o.status.toLowerCase().includes('error')) {
                pollOrder(o.id, o.lat, o.lon);
            }
        });
    } catch (e) {
        console.error("Error fetching orders", e);
    }
}

// API interaction
async function triggerPrediction() {
    const lat = parseFloat(document.getElementById('input-lat').value);
    const lon = parseFloat(document.getElementById('input-lon').value);
    const dateVal = document.getElementById('input-date').value.replace(/-/g, '');

    if (isNaN(lat) || isNaN(lon) || !dateVal) {
        alert("Por favor completa latitud, longitud y fecha.");
        return;
    }

    updateStatusBanner('Solicitando análisis a la API...');
    const card = document.getElementById('prediction-card');
    card.classList.add('hidden');

    try {
        const resp = await fetch(`${API_URL}/orden`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ dia: parseInt(dateVal), lat, lon })
        });
        
        if (!resp.ok) throw new Error('Error al crear la orden.');
        const data = await resp.json();
        
        // Add to DB
        const newOrder = { id: data.id, lat, lon, dia: dateVal, status: 'Pendiente', prediction: null };
        ordersDB.unshift(newOrder);
        updateDashboardTable();

        pollOrder(data.id, lat, lon);
    } catch (err) {
        updateStatusBanner('Error de conexión con API', true);
        console.error(err);
    }
}

async function pollOrder(id, lat, lon) {
    updateStatusBanner(`Orden #${id}: Procesando satélite y AI...`);
    
    const interval = setInterval(async () => {
        try {
            const resp = await fetch(`${API_URL}/orden/${id}`);
            if (!resp.ok) return;
            const data = await resp.json();
            
            // Update local DB
            const dbOrder = ordersDB.find(o => o.id === id);
            if(dbOrder) {
                dbOrder.status = data.status || dbOrder.status;
                updateDashboardTable(); // Update UI with intermediate state
            }

            if (data.status === 'Predicha') {
                clearInterval(interval);
                updateStatusBanner(`Orden #${id}: Análisis finalizado.`, false, true);
                if(dbOrder) dbOrder.prediction = data.prediccion;
                updateDashboardTable();
                showResultCard(data.prediccion, lat, lon);
            } else if (data.status.toLowerCase().includes('error')) {
                clearInterval(interval);
                updateStatusBanner(`Orden #${id}: Falló el proceso.`, true);
            } else if (data.status === 'Cancelada') {
                clearInterval(interval);
                updateStatusBanner(`Orden #${id}: Cancelada.`, true);
            } else {
                updateStatusBanner(`Orden #${id}: ${data.status}`);
            }
        } catch (err) {
            console.error('Error polling', err);
        }
    }, 3000);
}

function showResultCard(predValue, lat, lon) {
    let val = 0;
    try {
        let obj = typeof predValue === 'string' ? JSON.parse(predValue) : predValue;
        if (obj && obj.porcentaje_area_riesgo !== undefined) {
            val = parseFloat(obj.porcentaje_area_riesgo);
        } else {
            val = parseFloat(predValue) * 100;
        }
    } catch(e) {
        val = parseFloat(predValue) * 100;
    }
    if (isNaN(val)) val = 0;
    const card = document.getElementById('prediction-card');
    const content = document.getElementById('prediction-content');
    
    let riskLabel = 'BAJO';
    let riskColorClass = 'text-primary';
    if(val > 50) { riskLabel = 'EXTREMO'; riskColorClass = 'text-error'; }
    else if(val > 20) { riskLabel = 'MEDIO'; riskColorClass = 'text-on-tertiary-container'; }

    content.innerHTML = `
        <div class="mb-4">
            <p class="text-[12px] opacity-80 mb-1">Riesgo calculado por modelo XGBoost:</p>
            <p class="text-3xl font-bold ${riskColorClass}">${val.toFixed(2)}%</p>
            <p class="text-sm font-bold ${riskColorClass} uppercase">${riskLabel}</p>
        </div>
        <div class="flex justify-between items-center text-[10px] text-on-surface-variant pt-2 border-t border-outline-variant">
            <span>Lat: ${lat.toFixed(4)}</span>
            <span>Lon: ${lon.toFixed(4)}</span>
        </div>
    `;
    
    card.classList.remove('hidden');
    drawRiskBox(lat, lon, val);
}

// ==========================================
// HEALTH POLLING
// ==========================================
let lastHealthData = null;

async function pollHealth() {
    try {
        const resp = await fetch(`${API_URL}/health`);
        if (!resp.ok) throw new Error();
        const data = await resp.json();
        lastHealthData = data;

        function updateBadge(id, statusObj) {
            const el = document.getElementById(id);
            if(!el) return;
            const isUp = typeof statusObj === 'string' ? statusObj === 'UP' : (statusObj && statusObj.status === 'UP');
            if(isUp) {
                el.innerText = 'OPERATIVO';
                el.className = 'px-2 py-1 bg-primary-container/10 text-primary font-label-bold text-[10px] rounded uppercase';
            } else {
                el.innerText = 'CAÍDO';
                el.className = 'px-2 py-1 bg-error-container text-error font-label-bold text-[10px] rounded uppercase';
            }
        }

        updateBadge('badge-api', data.services.api);
        updateBadge('badge-validador', data.services.validador);
        updateBadge('badge-worker', data.services.worker);
        updateBadge('badge-predictor', data.services.predictor);
        updateBadge('badge-entrenador', data.services.entrenador);
        updateBadge('badge-modelador', data.services.modelador);
        updateBadge('badge-db', data.dependencies.database);
        updateBadge('badge-minio', data.dependencies.minio);
        
        // If modal is open, update it
        const modal = document.getElementById('health-modal');
        if (modal && !modal.classList.contains('hidden')) {
            const currentService = document.getElementById('modal-title').innerText.toLowerCase();
            if (data.services[currentService]) {
                updateModalContent(currentService, data.services[currentService]);
            }
        }
    } catch (err) {
        // If API is down, mark everything as down
        ['badge-api', 'badge-validador', 'badge-worker', 'badge-predictor', 'badge-entrenador', 'badge-modelador', 'badge-db', 'badge-minio'].forEach(id => {
            const el = document.getElementById(id);
            if(el) {
                el.innerText = 'CAÍDO';
                el.className = 'px-2 py-1 bg-error-container text-error font-label-bold text-[10px] rounded uppercase';
            }
        });
    }
}

function updateModalContent(serviceName, data) {
    document.getElementById('modal-title').innerText = serviceName;
    
    const badge = document.getElementById('modal-badge');
    const isUp = typeof data === 'string' ? data === 'UP' : (data && data.status === 'UP');
    
    if(isUp) {
        badge.innerText = 'OPERATIVO';
        badge.className = 'px-2 py-1 bg-primary-container/10 text-primary font-label-bold text-[10px] rounded uppercase mt-1 inline-block';
    } else {
        badge.innerText = 'CAÍDO';
        badge.className = 'px-2 py-1 bg-error-container text-error font-label-bold text-[10px] rounded uppercase mt-1 inline-block';
    }
    
    document.getElementById('modal-desc').innerText = data.descripcion || 'Sin información detallada';
    document.getElementById('modal-queue').innerText = data.queue_size !== undefined ? data.queue_size : '-';
    
    if (data.seconds_since_last_heartbeat !== undefined) {
        document.getElementById('modal-ping').innerText = `${data.seconds_since_last_heartbeat}s`;
    } else {
        document.getElementById('modal-ping').innerText = '-';
    }
}

function showHealthDetails(serviceName) {
    if (!lastHealthData || !lastHealthData.services[serviceName]) return;
    
    const data = lastHealthData.services[serviceName];
    updateModalContent(serviceName, data);
    
    const modal = document.getElementById('health-modal');
    modal.classList.remove('hidden');
    setTimeout(() => {
        modal.classList.remove('opacity-0');
        modal.firstElementChild.classList.remove('scale-95');
    }, 10);
}

function closeHealthModal() {
    const modal = document.getElementById('health-modal');
    modal.classList.add('opacity-0');
    modal.firstElementChild.classList.add('scale-95');
    setTimeout(() => {
        modal.classList.add('hidden');
    }, 300);
}

// Start polling health every 5 seconds
setInterval(pollHealth, 5000);
pollHealth(); // Initial call

// ==========================================
// SEARCH LOCATION (NOMINATIM)
// ==========================================
async function executeSearch() {
    const input = document.getElementById('address-input');
    const query = input.value.trim();
    if(!query) return;

    // Switch to Map view if not already there
    navTo('map');
    // Check if query is directly coordinates (lat, lon)
    const coordMatch = query.match(/^\s*(-?\d+(\.\d+)?)\s*,\s*(-?\d+(\.\d+)?)\s*$/);
    
    let lat, lon;
    let displayName = query;
    
    if (coordMatch) {
        lat = parseFloat(coordMatch[1]);
        lon = parseFloat(coordMatch[3]);
        updateStatusBanner(`Coordenadas directas detectadas...`);
    } else {
        updateStatusBanner(`Buscando "${query}"...`);
        try {
            const url = `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(query)}`;
            const resp = await fetch(url, { headers: { 'Accept-Language': 'es' } });
            const results = await resp.json();

            if (results.length === 0) {
                updateStatusBanner('Ubicación no encontrada', true);
                alert('Ubicación no encontrada.');
                return;
            }

            lat = parseFloat(results[0].lat);
            lon = parseFloat(results[0].lon);
            displayName = results[0].display_name.split(',')[0];
        } catch (e) {
            console.error(e);
            updateStatusBanner('Error en la búsqueda', true);
            return;
        }
    }

    // Update inputs
        document.getElementById('input-lat').value = lat.toFixed(4);
        document.getElementById('input-lon').value = lon.toFixed(4);

        // Update Map Marker
        const latlng = [lat, lon];
        if (marker) {
            marker.setLatLng(latlng);
        } else {
            marker = L.marker(latlng).addTo(map);
        }
        
        map.flyTo(latlng, 12, { duration: 1.2 });
        updateStatusBanner(`Ubicación encontrada: ${displayName}`, false, true);
        
        setTimeout(() => {
            document.getElementById('map-status-banner').classList.add('hidden');
        }, 4000);
}

// ==========================================
// DARK MODE TOGGLE
// ==========================================
function toggleTheme() {
    const html = document.documentElement;
    const icon = document.getElementById('theme-icon');
    if (html.classList.contains('dark')) {
        html.classList.remove('dark');
        html.classList.add('light');
        localStorage.setItem('theme', 'light');
        if(icon) icon.innerText = 'dark_mode';
    } else {
        html.classList.remove('light');
        html.classList.add('dark');
        localStorage.setItem('theme', 'dark');
        if(icon) icon.innerText = 'light_mode';
    }
}

// Load theme preference on load
window.addEventListener('DOMContentLoaded', () => {
    const theme = localStorage.getItem('theme');
    const html = document.documentElement;
    const icon = document.getElementById('theme-icon');
    if (theme === 'dark') {
        html.classList.remove('light');
        html.classList.add('dark');
        if(icon) icon.innerText = 'light_mode';
    }
});
