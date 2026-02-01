// RC Plane Flight Tracker - Map & Real-time Updates

// Initialize map
const map = L.map('map').setView([0, 0], 2);

// Add OpenStreetMap tiles
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap contributors'
}).addTo(map);

// Plane marker
const planeIcon = L.divIcon({
    html: '✈️',
    className: 'plane-marker',
    iconSize: [30, 30],
    iconAnchor: [15, 15]
});

let planeMarker = null;
let flightPath = null;
let pathPoints = [];
let selectedFlightId = null;
let hasInitialPosition = false;

// Connect to SocketIO
const socket = io();

// Connection status
socket.on('connect', function() {
    updateConnectionStatus(true);
    loadFlightHistory();
});

socket.on('disconnect', function() {
    updateConnectionStatus(false);
});

// Receive flight data
socket.on('flight_data', function(data) {
    updateDisplay(data);

    // Update map position
    if (data.latitude !== 0 || data.longitude !== 0) {
        updatePlanePosition(data.latitude, data.longitude);

        // Add to path if in flight
        if (data.in_flight) {
            addPathPoint(data.latitude, data.longitude);
        }
    }

    // Update flight status
    updateFlightStatus(data.in_flight);
});

// Flight started
socket.on('flight_started', function(data) {
    console.log('Flight started:', data.flight_id);
    pathPoints = [];
    if (flightPath) {
        map.removeLayer(flightPath);
        flightPath = null;
    }
    updateFlightStatus(true);
});

// Flight ended
socket.on('flight_ended', function(data) {
    console.log('Flight ended:', data.flight_id);
    updateFlightStatus(false);
    loadFlightHistory();
});

// Signal lost
socket.on('signal_lost', function() {
    document.getElementById('statusText').textContent = 'Signal Lost!';
    document.querySelector('.status-dot').className = 'status-dot warning';
});

// Update functions
function updateConnectionStatus(connected) {
    const dot = document.querySelector('.status-dot');
    const text = document.getElementById('statusText');

    if (connected) {
        dot.className = 'status-dot connected';
        text.textContent = 'Connected';
    } else {
        dot.className = 'status-dot disconnected';
        text.textContent = 'Disconnected';
    }
}

function updateDisplay(data) {
    document.getElementById('latitude').textContent = data.latitude.toFixed(6);
    document.getElementById('longitude').textContent = data.longitude.toFixed(6);
    document.getElementById('satellites').textContent = data.satellites;

    document.getElementById('speed').textContent = data.speed.toFixed(1);
    document.getElementById('altitude').textContent = data.altitude.toFixed(1);

    document.getElementById('peakSpeed').textContent = data.peak_speed.toFixed(1);
    document.getElementById('peakAltitude').textContent = data.peak_altitude.toFixed(1);

    document.getElementById('rssi').textContent = data.rssi;
    document.getElementById('snr').textContent = data.snr.toFixed(1);

    // Update signal bar (RSSI typically -120 to -30 dBm)
    const signalPercent = Math.max(0, Math.min(100, (data.rssi + 120) * 1.1));
    const signalBar = document.getElementById('signalBar');
    signalBar.style.width = signalPercent + '%';

    // Color based on signal strength
    if (signalPercent > 70) {
        signalBar.style.background = '#22c55e';
    } else if (signalPercent > 40) {
        signalBar.style.background = '#eab308';
    } else {
        signalBar.style.background = '#ef4444';
    }

    // Update speed color
    const speedEl = document.getElementById('speed');
    if (data.speed < 30) {
        speedEl.style.color = '#22c55e';
    } else if (data.speed < 60) {
        speedEl.style.color = '#eab308';
    } else {
        speedEl.style.color = '#ef4444';
    }
}

function updatePlanePosition(lat, lng) {
    if (!planeMarker) {
        planeMarker = L.marker([lat, lng], { icon: planeIcon }).addTo(map);
    } else {
        planeMarker.setLatLng([lat, lng]);
    }

    // Center map on first valid position
    if (!hasInitialPosition && (lat !== 0 || lng !== 0)) {
        map.setView([lat, lng], 16);
        hasInitialPosition = true;
    }
}

function addPathPoint(lat, lng) {
    pathPoints.push([lat, lng]);

    // Update or create path
    if (flightPath) {
        flightPath.setLatLngs(pathPoints);
    } else {
        flightPath = L.polyline(pathPoints, {
            color: '#3b82f6',
            weight: 3,
            opacity: 0.8
        }).addTo(map);
    }
}

function updateFlightStatus(inFlight) {
    const badge = document.getElementById('flightBadge');

    if (inFlight) {
        badge.textContent = '🛫 IN FLIGHT';
        badge.className = 'flight-badge in-flight';
    } else {
        badge.textContent = 'STANDBY';
        badge.className = 'flight-badge';
    }
}

// Flight history
function loadFlightHistory() {
    fetch('/api/flights')
        .then(response => response.json())
        .then(flights => {
            const listEl = document.getElementById('flightList');

            if (flights.length === 0) {
                listEl.innerHTML = '<p class="no-flights">No flights recorded yet</p>';
                return;
            }

            listEl.innerHTML = flights.map(flight => {
                const date = new Date(flight.start_time);
                const dateStr = date.toLocaleDateString();
                const timeStr = date.toLocaleTimeString();
                const duration = formatDuration(flight.duration_seconds);

                return `
                    <div class="flight-item" onclick="showFlightDetails('${flight.id}')">
                        <div class="flight-info">
                            <span class="flight-date">${dateStr} ${timeStr}</span>
                            <span class="flight-duration">${duration}</span>
                        </div>
                        <div class="flight-stats">
                            <span>🚀 ${(flight.peak_speed || 0).toFixed(1)} mph</span>
                            <span>📏 ${(flight.peak_altitude || 0).toFixed(1)} m</span>
                        </div>
                    </div>
                `;
            }).join('');
        })
        .catch(err => console.error('Error loading flights:', err));
}

function formatDuration(seconds) {
    if (!seconds) return '0:00';
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
}

function showFlightDetails(flightId) {
    selectedFlightId = flightId;

    fetch(`/api/flight/${flightId}`)
        .then(response => response.json())
        .then(flight => {
            const date = new Date(flight.start_time);
            const details = document.getElementById('flightDetails');

            details.innerHTML = `
                <div class="detail-grid">
                    <div class="detail-item">
                        <span class="label">Flight ID</span>
                        <span class="value">${flight.id}</span>
                    </div>
                    <div class="detail-item">
                        <span class="label">Date</span>
                        <span class="value">${date.toLocaleDateString()}</span>
                    </div>
                    <div class="detail-item">
                        <span class="label">Start Time</span>
                        <span class="value">${date.toLocaleTimeString()}</span>
                    </div>
                    <div class="detail-item">
                        <span class="label">Duration</span>
                        <span class="value">${formatDuration(flight.duration_seconds)}</span>
                    </div>
                    <div class="detail-item">
                        <span class="label">Peak Speed</span>
                        <span class="value">${(flight.peak_speed || 0).toFixed(1)} mph</span>
                    </div>
                    <div class="detail-item">
                        <span class="label">Peak Altitude</span>
                        <span class="value">${(flight.peak_altitude || 0).toFixed(1)} m</span>
                    </div>
                    <div class="detail-item">
                        <span class="label">Data Points</span>
                        <span class="value">${flight.data_points ? flight.data_points.length : 0}</span>
                    </div>
                </div>
            `;

            // Show flight path on map
            if (flight.data_points && flight.data_points.length > 0) {
                const points = flight.data_points.map(p => [p.latitude, p.longitude]);

                // Remove existing path
                if (flightPath) {
                    map.removeLayer(flightPath);
                }

                // Draw historical path
                flightPath = L.polyline(points, {
                    color: '#f59e0b',
                    weight: 3,
                    opacity: 0.8
                }).addTo(map);

                // Fit map to path
                map.fitBounds(flightPath.getBounds(), { padding: [50, 50] });

                // Add start/end markers
                L.marker(points[0], {
                    icon: L.divIcon({
                        html: '🟢',
                        className: 'start-marker',
                        iconSize: [20, 20]
                    })
                }).addTo(map).bindPopup('Start');

                L.marker(points[points.length - 1], {
                    icon: L.divIcon({
                        html: '🔴',
                        className: 'end-marker',
                        iconSize: [20, 20]
                    })
                }).addTo(map).bindPopup('End');
            }

            document.getElementById('flightModal').style.display = 'flex';
        })
        .catch(err => console.error('Error loading flight details:', err));
}

function closeModal() {
    document.getElementById('flightModal').style.display = 'none';
}

function exportFlight() {
    if (selectedFlightId) {
        window.location.href = `/api/export/${selectedFlightId}`;
    }
}

// Close modal on outside click
document.getElementById('flightModal').addEventListener('click', function(e) {
    if (e.target === this) {
        closeModal();
    }
});

// Initial load
loadFlightHistory();
