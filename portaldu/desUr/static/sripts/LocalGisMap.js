class LocalGISMap {
    constructor(containerId, options = {}) {
        this.containerId = containerId;
        this.map = null;
        this.currentMarker = null;
        this.options = {
            center: [28.6353, -106.0889],
            zoom: 12,
            ...options
        };
        this.initMap();
    }

    async initMap() {
        try {
            if (typeof L === 'undefined') {
                console.error('Leaflet no está cargado');
                return;
            }

            const container = document.getElementById(this.containerId);
            if (!container) {
                console.error(`Contenedor ${this.containerId} no encontrado`);
                return;
            }

            this.map = L.map(this.containerId).setView(this.options.center, this.options.zoom);

            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '© OpenStreetMap contributors',
                maxZoom: 19
            }).addTo(this.map);

            this.map.on('click', (e) => {
                this.onMapClick(e.latlng);
            });

            console.log('Mapa inicializado correctamente');
        } catch (error) {
            console.error('Error inicializando mapa:', error);
        }
    }

    async onMapClick(latlng) {
        const lat = latlng.lat;
        const lng = latlng.lng;

        console.log(`Click en mapa: ${lat}, ${lng}`);

        if (this.currentMarker) {
            this.map.removeLayer(this.currentMarker);
        }

        this.currentMarker = L.marker([lat, lng]).addTo(this.map);

        const address = await this.reverseGeocode(lat, lng);
        const displayText = address || `${lat.toFixed(6)}, ${lng.toFixed(6)}`;

        this.currentMarker.bindPopup(`
            <div>
                <strong>Ubicación seleccionada</strong><br>
                ${displayText}<br>
                <button onclick="window.selectMapLocation('${displayText}', ${lat}, ${lng})" style="background: #014277; color: white; border: none; padding: 5px 10px; border-radius: 3px; cursor: pointer; margin-top: 5px;">
                    Usar esta dirección
                </button>
            </div>
        `).openPopup();

        const inputModal = document.getElementById('dirr');
        if (inputModal) {
            inputModal.value = displayText;
        }
    }

    async reverseGeocode(lat, lng) {
        try {
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;

            if (!csrfToken) {
                console.warn('CSRF token no encontrado');
                return null;
            }

            const response = await fetch('/ageo/reverse-geocode/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({
                    lat: lat,
                    lng: lng
                })
            });

            if (!response.ok) {
                console.warn(`Error HTTP en geocodificación inversa: ${response.status}`);
                return null;
            }

            const data = await response.json();

            if (data.success && data.address) {
                return data.address;
            } else {
                console.warn('Geocodificación inversa fallida');
                return null;
            }
        } catch (error) {
            console.error('Error en geocodificación inversa:', error);
            return null;
        }
    }

    async geocodeAddress(address) {
        try {
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;

            if (!csrfToken) {
                console.error('CSRF token no encontrado');
                return { success: false, error: 'CSRF token no encontrado' };
            }

            console.log('Enviando dirección para geocodificar:', address);

            const response = await fetch('/ageo/geocode/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({
                    address: address
                })
            });

            if (!response.ok) {
                console.error(`Error HTTP: ${response.status}`);
                return { success: false, error: `Error HTTP: ${response.status}` };
            }

            const data = await response.json();
            console.log('Respuesta del servidor:', data);

            if (data.success && data.result) {
                const { lat, lng } = data.result;

                if (this.currentMarker) {
                    this.map.removeLayer(this.currentMarker);
                }

                this.currentMarker = L.marker([lat, lng]).addTo(this.map);
                this.map.setView([lat, lng], 16);

                this.currentMarker.bindPopup(`
                    <div>
                        <strong>Dirección encontrada</strong><br>
                        ${data.result.address}<br>
                        <button onclick="window.selectMapLocation('${data.result.address}', ${lat}, ${lng})" style="background: #014277; color: white; border: none; padding: 5px 10px; border-radius: 3px; cursor: pointer; margin-top: 5px;">
                            Seleccionar
                        </button>
                    </div>
                `).openPopup();

                return data;
            } else {
                return { success: false, error: data.error || 'Dirección no encontrada' };
            }
        } catch (error) {
            console.error('Error en geocodificación:', error);
            return { success: false, error: error.message };
        }
    }
}

// Hacer la clase disponible globalmente
window.LocalGISMap = LocalGISMap;