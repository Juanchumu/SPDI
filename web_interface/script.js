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

    // Click on map is disabled for manager view to avoid confusion, or can be kept.
    // Cargar clientes en el select
    loadClients();
});

let currentClientAreas = [];
let clientMarkers = [];

async function loadClients() {
    try {
        const resp = await fetch(`${API_URL}/clientes`);
        if (!resp.ok) return;
        const clientes = await resp.json();
        
        // Update main select
        const selectMain = document.getElementById('client-select');
        if(selectMain) {
            selectMain.innerHTML = '<option value="">Seleccionar Cliente...</option>';
            clientes.forEach(c => {
                const opt = document.createElement('option');
                opt.value = c.id;
                opt.dataset.codigo = c.codigo_cliente || '';
                opt.dataset.email = c.email || '';
                opt.dataset.telefono = c.telefono || '';
                opt.dataset.nombre = c.nombre || '';
                opt.innerText = c.nombre;
                selectMain.appendChild(opt);
            });
        }

        // Update alta-area select
        const selectAlta = document.getElementById('alta-area-cliente');
        if(selectAlta) {
            selectAlta.innerHTML = '<option value="">Seleccionar Cliente...</option>';
            clientes.forEach(c => {
                const opt = document.createElement('option');
                opt.value = c.id;
                opt.innerText = c.nombre;
                selectAlta.appendChild(opt);
            });
        }
    } catch(e) {
        console.error("Error cargando clientes:", e);
    }
}

async function loadClientAreas() {
    const select = document.getElementById('client-select');
    if(!select) return;
    const clientId = select.value;
    
    // Update UI headers
    if(clientId) {
        const opt = select.selectedOptions[0];
        document.getElementById('client-name-display').innerText = opt.dataset.nombre;
        document.getElementById('client-code-display').innerText = opt.dataset.codigo;
        document.getElementById('client-id-display').innerText = `ID: ${opt.dataset.codigo}`;
        document.getElementById('client-email-display').innerText = opt.dataset.email || '---';
        document.getElementById('client-phone-display').innerText = opt.dataset.telefono || '---';
    } else {
        document.getElementById('client-name-display').innerText = 'Seleccione un Cliente';
        document.getElementById('client-code-display').innerText = 'EXP-2024-0000';
        document.getElementById('client-id-display').innerText = 'ID: -';
        document.getElementById('client-email-display').innerText = '---';
        document.getElementById('client-phone-display').innerText = '---';
        document.getElementById('areas-table-body').innerHTML = '<tr><td class="p-3 border-b border-outline-variant" colspan="2">Seleccione un cliente...</td></tr>';
        document.getElementById('points-count').innerText = '0 PUNTOS';
        clearMapMarkers();
        return;
    }

    try {
        const resp = await fetch(`${API_URL}/clientes/${clientId}/areas`);
        if(!resp.ok) return;
        currentClientAreas = await resp.json();
        
        const tbody = document.getElementById('areas-table-body');
        tbody.innerHTML = '';
        document.getElementById('points-count').innerText = `${currentClientAreas.length} PUNTOS`;
        
        clearMapMarkers();
        let bounds = [];

        currentClientAreas.forEach(area => {
            const tr = document.createElement('tr');
            tr.className = 'hover:bg-surface-container-low transition-colors group';
            tr.innerHTML = `
                <td class="p-3 border-b border-outline-variant">
                    <p class="font-bold text-primary text-sm">${area.nombre_lote}</p>
                </td>
                <td class="p-3 border-b border-outline-variant">
                    <p class="text-on-surface-variant text-[10px]">${area.latitud.toFixed(4)}°, ${area.longitud.toFixed(4)}°</p>
                </td>
                <td class="p-3 border-b border-outline-variant text-right">
                    <button onclick="triggerIndividualPrediction(${area.id}, ${area.latitud}, ${area.longitud})" class="text-secondary hover:text-secondary-container transition-colors" title="Actualizar Predicción">
                        <span class="material-symbols-outlined text-[18px]">refresh</span>
                    </button>
                </td>
            `;
            tbody.appendChild(tr);

            const marker = L.marker([area.latitud, area.longitud]).addTo(map);
            marker.bindPopup(`<b>${area.nombre_lote}</b>`);
            clientMarkers.push(marker);
            bounds.push([area.latitud, area.longitud]);
        });

        if(bounds.length > 0) {
            map.fitBounds(bounds, { padding: [50, 50] });
        }
    } catch(e) {
        console.error("Error loading areas:", e);
    }
}

function clearMapMarkers() {
    clientMarkers.forEach(m => map.removeLayer(m));
    clientMarkers = [];
    drawnRectangles.forEach(r => map.removeLayer(r));
    drawnRectangles = [];
}

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

async function triggerPrediction() {
    const clientId = document.getElementById('client-select') ? document.getElementById('client-select').value : null;
    if(!clientId || currentClientAreas.length === 0) {
        alert("Selecciona un cliente con áreas definidas.");
        return;
    }

    updateStatusBanner('Solicitando análisis batch a la API...');
    const card = document.getElementById('prediction-card');
    if(card) card.classList.add('hidden');

    const dateVal = "20211125"; // Por defecto usamos una fecha conocida con datos

    for(const area of currentClientAreas) {
        try {
            const resp = await fetch(`${API_URL}/orden`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ dia: parseInt(dateVal), lat: area.latitud, lon: area.longitud })
            });
            if(resp.ok) {
                const data = await resp.json();
                const newOrder = { id: data.id, lat: area.latitud, lon: area.longitud, dia: dateVal, status: 'Pendiente', prediction: null };
                ordersDB.unshift(newOrder);
                pollOrder(data.id, area.latitud, area.longitud);
            }
        } catch(e) {
            console.error("Error creating order for area", area, e);
            updateStatusBanner('Error de conexión con API', true);
        }
    }
    updateDashboardTable();
}

async function triggerIndividualPrediction(areaId, lat, lon) {
    const dateVal = "20211125";
    updateStatusBanner('Solicitando actualización individual...');
    
    try {
        const resp = await fetch(`${API_URL}/orden`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ dia: parseInt(dateVal), lat, lon })
        });
        if(resp.ok) {
            const data = await resp.json();
            const newOrder = { id: data.id, lat, lon, dia: dateVal, status: 'Pendiente', prediction: null };
            ordersDB.unshift(newOrder);
            pollOrder(data.id, lat, lon);
            updateDashboardTable();
            navTo('dashboard'); // opcional, para ver cómo procesa
        }
    } catch(e) {
        console.error("Error individual", e);
        updateStatusBanner('Error en API', true);
    }
}

// ==========================================
// ALTA DE CLIENTES Y CAMPOS
// ==========================================
let isNewClientMode = true;
let altaMap = null;
let altaMarker = null;

// Initialize Alta Logic
document.addEventListener('DOMContentLoaded', () => {
    const toggleNew = document.getElementById('toggle-new');
    const toggleExisting = document.getElementById('toggle-existing');
    const secNew = document.getElementById('section-cliente-nuevo');
    const secExist = document.getElementById('section-cliente-existente');
    
    if(toggleNew && toggleExisting) {
        toggleNew.addEventListener('click', () => {
            isNewClientMode = true;
            toggleNew.classList.add('bg-primary', 'text-white', 'shadow-sm');
            toggleNew.classList.remove('text-on-surface-variant');
            toggleExisting.classList.remove('bg-primary', 'text-white', 'shadow-sm');
            toggleExisting.classList.add('text-on-surface-variant');
            secNew.classList.remove('hidden');
            secNew.classList.add('grid');
            secExist.classList.add('hidden');
            
            // Requisitos de form
            document.getElementById('alta-cli-nombre').required = true;
            document.getElementById('alta-cli-codigo').required = true;
            document.getElementById('alta-area-cliente').required = false;
        });

        toggleExisting.addEventListener('click', () => {
            isNewClientMode = false;
            toggleExisting.classList.add('bg-primary', 'text-white', 'shadow-sm');
            toggleExisting.classList.remove('text-on-surface-variant');
            toggleNew.classList.remove('bg-primary', 'text-white', 'shadow-sm');
            toggleNew.classList.add('text-on-surface-variant');
            secExist.classList.remove('hidden');
            secNew.classList.add('hidden');
            secNew.classList.remove('grid');
            
            // Requisitos de form
            document.getElementById('alta-cli-nombre').required = false;
            document.getElementById('alta-cli-codigo').required = false;
            document.getElementById('alta-area-cliente').required = true;
        });
    }

    // Initialize the second map when navigating to 'alta' view
    document.getElementById('nav-alta')?.addEventListener('click', () => {
        if(!altaMap && document.getElementById('alta-leaflet-map')) {
            altaMap = L.map('alta-leaflet-map', {
                zoomControl: true,
                attributionControl: false
            }).setView([-34.6037, -58.3816], 5);
            L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', { maxZoom: 19 }).addTo(altaMap);
            
            altaMarker = L.marker([-34.6037, -58.3816], { draggable: true }).addTo(altaMap);
            
            altaMarker.on('dragend', function (e) {
                document.getElementById('alta-area-lat').value = altaMarker.getLatLng().lat.toFixed(4);
                document.getElementById('alta-area-lon').value = altaMarker.getLatLng().lng.toFixed(4);
            });
            altaMap.on('click', function(e) {
                altaMarker.setLatLng(e.latlng);
                document.getElementById('alta-area-lat').value = e.latlng.lat.toFixed(4);
                document.getElementById('alta-area-lon').value = e.latlng.lng.toFixed(4);
            });
        }
        
        // Fix Leaflet rendering inside hidden div bug
        if(altaMap) {
            setTimeout(() => altaMap.invalidateSize(), 100);
        }
    });
});

async function guardarRegistroAlta(e) {
    e.preventDefault();
    
    // Obtener campos de Área
    const nombreLote = document.getElementById('alta-area-lote').value;
    const lat = parseFloat(document.getElementById('alta-area-lat').value);
    const lon = parseFloat(document.getElementById('alta-area-lon').value);
    const desc = document.getElementById('alta-area-desc').value;
    
    let clientId = null;

    try {
        if(isNewClientMode) {
            const nombre = document.getElementById('alta-cli-nombre').value;
            const codigo = document.getElementById('alta-cli-codigo').value;
            const email = document.getElementById('alta-cli-email').value;
            const telefono = document.getElementById('alta-cli-telefono').value;
            
            const respCli = await fetch(`${API_URL}/clientes`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ nombre, codigo_cliente: codigo, email, telefono })
            });
            if(!respCli.ok) throw new Error("Error al crear cliente. Puede que el código de cliente ya exista.");
            const dataCli = await respCli.json();
            clientId = dataCli.id;
        } else {
            clientId = document.getElementById('alta-area-cliente').value;
            if(!clientId) { alert("Seleccione un cliente registrado primero."); return; }
        }
        
        // Crear Área
        const respArea = await fetch(`${API_URL}/clientes/${clientId}/areas`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ nombre_lote: nombreLote, latitud: lat, longitud: lon, descripcion_entorno: desc })
        });
        if(!respArea.ok) throw new Error("Error al crear campo en el servidor.");
        
        alert("Registro de cliente y/o campo guardado exitosamente");
        document.getElementById('form-alta-registro').reset();
        
        // Si creamos un cliente nuevo, recargar selects globales
        if(isNewClientMode) {
            loadClients();
        }
        
    } catch(err) {
        console.error(err);
        alert(err.message || "Error al guardar el registro");
    }
}

// ==========================================
// GEMINI ALERTAS
// ==========================================
async function enviarAlerta() {
    const clientId = document.getElementById('client-select') ? document.getElementById('client-select').value : null;
    if(!clientId || currentClientAreas.length === 0) {
        alert("Selecciona un cliente con áreas definidas.");
        return;
    }
    
    updateStatusBanner('Redactando alerta con Gemini AI...', false, false);
    document.getElementById('map-status-banner').classList.remove('hidden');
    
    try {
        const resp = await fetch(`${API_URL}/clientes/${clientId}/alerta/preview`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({})
        });
        
        if(!resp.ok) throw new Error("Fallo la generación");
        const data = await resp.json();
        
        document.getElementById('gemini-asunto').value = data.asunto || '';
        document.getElementById('gemini-cuerpo').value = data.cuerpo_mail || '';
        
        document.getElementById('map-status-banner').classList.add('hidden');
        
        // Show modal
        const modal = document.getElementById('gemini-modal');
        modal.classList.remove('hidden');
    } catch(e) {
        console.error(e);
        updateStatusBanner('Error conectando con Gemini', true);
        setTimeout(() => document.getElementById('map-status-banner').classList.add('hidden'), 3000);
    }
}

function closeGeminiModal() {
    document.getElementById('gemini-modal').classList.add('hidden');
}

async function confirmarEnvioAlerta() {
    const clientId = document.getElementById('client-select').value;
    const asunto = document.getElementById('gemini-asunto').value;
    const cuerpo = document.getElementById('gemini-cuerpo').value;
    
    try {
        const resp = await fetch(`${API_URL}/clientes/${clientId}/alerta/send`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ asunto: asunto, cuerpo_mail: cuerpo })
        });
        if(resp.ok) {
            closeGeminiModal();
            updateStatusBanner('Alerta enviada exitosamente (Simulada).', false, true);
            setTimeout(() => document.getElementById('map-status-banner').classList.add('hidden'), 4000);
        }
    } catch(e) {
        console.error(e);
        alert("Error al enviar");
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
                updateStatusBanner(`Orden #${id}: ${dbOrder.status}`);
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

    const isAltaActive = document.getElementById('content-alta').classList.contains('active');
    
    // Switch to Map view if not in Alta or Map
    if(!isAltaActive && !document.getElementById('content-map').classList.contains('active')) {
        navTo('map');
    }

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

    if(isAltaActive) {
        // Update Alta inputs
        document.getElementById('alta-area-lat').value = lat.toFixed(4);
        document.getElementById('alta-area-lon').value = lon.toFixed(4);

        if(typeof altaMarker !== 'undefined') {
            altaMarker.setLatLng([lat, lon]);
        } else if(typeof altaMap !== 'undefined') {
            altaMarker = L.marker([lat, lon], {draggable: true}).addTo(altaMap);
        }
        if(typeof altaMap !== 'undefined') {
            altaMap.setView([lat, lon], 12);
        }
    } else {
        // Update main Map inputs
        const inputLat = document.getElementById('input-lat');
        const inputLon = document.getElementById('input-lon');
        if(inputLat) inputLat.value = lat.toFixed(4);
        if(inputLon) inputLon.value = lon.toFixed(4);

        if (typeof marker !== 'undefined') {
            marker.setLatLng([lat, lon]);
        } else if (typeof map !== 'undefined') {
            marker = L.marker([lat, lon]).addTo(map);
        }
        if (typeof map !== 'undefined') {
            map.setView([lat, lon], 12);
        }
    }
    
    updateStatusBanner(''); // clear banner
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
