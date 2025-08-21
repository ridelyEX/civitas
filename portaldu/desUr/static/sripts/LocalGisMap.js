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

    async reverseGeocode(lat, lng) {
        try {
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;

            if (!csrfToken) {
                throw new Error('Token CSRF no encontrado');
            }

            console.log(`Enviando solicitud de geocodificación inversa: ${lat}, ${lng}`);

            const response = await fetch('/ageo/reverse-geocode/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken,
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify({ lat: lat, lng: lng })
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            console.log('Respuesta geocodificación inversa:', data);

            if (data.success && data.result) {
                return data.result;  // Retornar el resultado completo
            } else {
                console.log('No se encontró dirección:', data.error);
                return null;
            }
        } catch (error) {
            console.error('Error en geocodificación inversa:', error);
            throw error;  // Re-lanzar el error para que onMapClick lo maneje
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

        // Mostrar mensaje de "Buscando dirección..."
        this.currentMarker.bindPopup(`
            <div style="padding: 8px;">
                <strong>🔍 Buscando dirección...</strong><br>
                <small>Coordenadas: ${lat.toFixed(6)}, ${lng.toFixed(6)}</small><br>
                <div style="margin-top: 8px;">
                    <div class="spinner" style="
                        width: 16px; height: 16px; border: 2px solid #ccc;
                        border-top: 2px solid #2196F3; border-radius: 50%;
                        animation: spin 1s linear infinite; display: inline-block;
                    "></div>
                    <small style="margin-left: 8px;">Por favor espera...</small>
                </div>
            </div>
            <style>
                @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
            </style>
        `).openPopup();

        try {
            const addressData = await this.reverseGeocode(lat, lng);

            if (addressData && addressData.address) {
                console.log('✅ Geocodificación inversa exitosa:', addressData);
                const popupContent = this.createReverseGeocodePopup(addressData, lat, lng);
                this.currentMarker.bindPopup(popupContent).openPopup();

                if (addressData.components) {
                    this.updateAddressInputs(addressData.components);
                }
            } else {
                console.log('❌ No se encontró dirección para las coordenadas');
                const coordsText = `${lat.toFixed(6)}, ${lng.toFixed(6)}`;
                this.currentMarker.bindPopup(`
                    <div style="min-width: 250px; padding: 8px;">
                        <strong style="color: #ff9800;">📍 Ubicación sin dirección</strong><br>
                        <div style="margin: 8px 0; font-size: 12px;">
                            No se encontró una dirección específica para esta ubicación.
                        </div>
                        <div style="background: #f5f5f5; padding: 6px; border-radius: 4px; margin: 8px 0; font-family: monospace; font-size: 11px;">
                            <strong>Coordenadas:</strong><br>
                            Latitud: ${lat.toFixed(6)}<br>
                            Longitud: ${lng.toFixed(6)}
                        </div>
                        <button onclick="selectMapLocationFromPopup('Coordenadas: ${coordsText}', ${lat}, ${lng}, '{}')"
                                style="width: 100%; margin-top: 8px; padding: 8px; background: #ff9800; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 12px;">
                            📌 Usar coordenadas
                        </button>
                    </div>
                `).openPopup();
            }
        } catch (error) {
            console.error('Error en geocodificación inversa:', error);
            const coordsText = `${lat.toFixed(6)}, ${lng.toFixed(6)}`;

            this.currentMarker.bindPopup(`
                <div style="min-width: 250px; padding: 8px;">
                    <strong style="color: #f44336;">⚠️ Error en búsqueda</strong><br>
                    <div style="margin: 8px 0; font-size: 12px; color: #666;">
                        ${error.message || 'Error de conexión con el servidor'}
                    </div>
                    <div style="background: #f5f5f5; padding: 6px; border-radius: 4px; margin: 8px 0; font-family: monospace; font-size: 11px;">
                        <strong>Coordenadas:</strong> ${coordsText}
                    </div>
                    <button onclick="selectMapLocationFromPopup('${coordsText}', ${lat}, ${lng}, '{}')"
                            style="width: 100%; padding: 8px; margin-top: 8px; background: #f44336; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 12px;">
                        📌 Usar coordenadas
                    </button>
                </div>
            `).openPopup();
        }
    }

    async geocodeAddress(address) {
        const startTime = Date.now();

        try {
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;

            if (!csrfToken) {
                throw new Error('Token CSRF no encontrado');
            }

            this.showGeocodingProgress(address);
            console.log(`🔍 Iniciando geocodificación: ${address}`);

            const response = await fetch('/ageo/geocode/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken,
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify({ address: address })
            });

            const processingTime = Date.now() - startTime;

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            this.debugGeocodeResponse(data);
            this.hideGeocodingProgress();

            if (data.success && data.result && data.result.address) {
                console.log(`✅ Geocodificación exitosa en ${processingTime}ms:`, data.result);

                const lat = parseFloat(data.result.lat);
                const lng = parseFloat(data.result.lng);

                // Validar que las coordenadas son números válidos
                if (isNaN(lat) || isNaN(lng)) {
                    throw new Error('Coordenadas inválidas recibidas del servidor');
                }

                this.map.setView([lat, lng], 16);

                if (this.currentMarker) {
                    this.map.removeLayer(this.currentMarker);
                }

                this.currentMarker = L.marker([lat, lng]).addTo(this.map);

                // Crear popup con información detallada
                const popupContent = this.createResultPopup(data.result, processingTime);
                this.currentMarker.bindPopup(popupContent, {
                    maxWidth: 350,
                    className: 'geocode-result-popup'
                }).openPopup();

                // Actualizar inputs
                if (data.result.components) {
                    this.updateAddressInputs(data.result.components);
                }

                return { success: true, result: data.result };

            } else {
                console.log(`❌ No encontrado en ${processingTime}ms:`, data.error);
                this.showNotFoundMessage(address, data.suggestions, processingTime);
                return { success: false, error: data.error, suggestions: data.suggestions };
            }

        } catch (error) {
            const processingTime = Date.now() - startTime;
            console.error(`💥 Error en geocodificación después de ${processingTime}ms:`, error);
            this.hideGeocodingProgress();
            this.showErrorMessage(error.message, processingTime);
            return { success: false, error: error.message };
        }
    }

    showGeocodingProgress(address) {
        this.hideGeocodingProgress(); // Limpiar cualquier mensaje anterior

        const progressDiv = document.createElement('div');
        progressDiv.id = 'geocoding-progress';
        progressDiv.innerHTML = `
            <div style="
                position: fixed; top: 20px; right: 20px;
                background: #2196F3; color: white;
                padding: 12px 16px; border-radius: 6px;
                z-index: 10000; max-width: 300px;
                font-size: 13px; box-shadow: 0 4px 8px rgba(0,0,0,0.3);
                display: flex; align-items: center; gap: 10px;
            ">
                <div class="spinner" style="
                    width: 16px; height: 16px; border: 2px solid #fff3;
                    border-top: 2px solid #fff; border-radius: 50%;
                    animation: spin 1s linear infinite;
                "></div>
                <div>
                    <strong>🔍 Buscando dirección...</strong><br>
                    <small>${address}</small>
                </div>
            </div>
            <style>
                @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
            </style>
        `;
        document.body.appendChild(progressDiv);
    }

    hideGeocodingProgress() {
        const existing = document.getElementById('geocoding-progress');
        if (existing) {
            existing.remove();
        }
    }

    createResultPopup(result, processingTime) {
        console.log('Creando popup con resultado:', result);

        const components = result.components || {};

        let detailsHtml = '';
        if (components.calle || components.numero || components.colonia) {
            const details = [];
            if (components.calle) details.push(`📍 ${components.calle}`);
            if (components.numero) details.push(`🏠 #${components.numero}`);
            if (components.colonia) details.push(`🏘️ ${components.colonia}`);
            if (components.codigo_postal) details.push(`📮 CP ${components.codigo_postal}`);

            detailsHtml = `<div style="margin: 8px 0; font-size: 11px; opacity: 0.9;">
                ${details.join('<br>')}
            </div>`;
        }

        // Escapar caracteres especiales para JSON
        const escapedComponents = JSON.stringify(components).replace(/'/g, "&#39;").replace(/"/g, "&quot;");
        const escapedAddress = result.address.replace(/'/g, "&#39;").replace(/"/g, "&quot;");

        console.log('Dirección escapada:', escapedAddress);
        console.log('Componentes escapados:', escapedComponents);

        return `
            <div style="min-width: 200px; max-width: 300px;">
                <strong style="color: #2196F3;">📍 Dirección encontrada</strong><br>
                <div style="margin: 6px 0; font-weight: 500;">${result.address}</div>
                ${detailsHtml}
                <div style="margin-top: 8px; padding-top: 8px; border-top: 1px solid #eee; font-size: 10px; color: #666;">
                    📊 ${result.source || 'Unknown'} | ⚡ ${processingTime}ms | 🎯 ${result.score || 0}% precisión
                </div>
                <button onclick="selectMapLocationFromPopup('${escapedAddress}', ${result.lat}, ${result.lng}, '${escapedComponents}')"
                        style="
                            width: 100%; margin-top: 8px; padding: 6px;
                            background: #4CAF50; color: white; border: none;
                            border-radius: 4px; cursor: pointer; font-size: 12px;
                            transition: background-color 0.2s;
                        "
                        onmouseover="this.style.backgroundColor='#45a049'"
                        onmouseout="this.style.backgroundColor='#4CAF50'">
                    ✅ Seleccionar esta dirección
                </button>
            </div>
        `;
    }

   createReverseGeocodePopup(addressData, lat, lng) {
       console.log('Creando popup de geocodificación inversa:', addressData);

       const components = addressData.components || {};

       let detailsHtml = '';
       if (components.calle || components.numero || components.colonia) {
           const details = [];
           if (components.calle) details.push(`📍 ${components.calle}`);
           if (components.numero) details.push(`🏠 #${components.numero}`);
           if (components.colonia) details.push(`🏘️ ${components.colonia}`);
           if (components.codigo_postal) details.push(`📮 CP ${components.codigo_postal}`);

           detailsHtml = `<div style="margin: 8px 0; font-size: 11px; opacity: 0.9;">
               ${details.join('<br>')}
           </div>`;
       }

       const escapedComponents = JSON.stringify(components).replace(/'/g, "&#39;").replace(/"/g, "&quot;");
       const escapedAddress = addressData.address.replace(/'/g, "&#39;").replace(/"/g, "&quot;");

       return `
           <div style="min-width: 250px; padding: 4px;">
               <strong style="color: #2196F3;">📍 Ubicación encontrada</strong><br>
               <div style="margin: 6px 0; font-weight: 500;">${addressData.address}</div>
               ${detailsHtml}
               <div style="background: #f8f9fa; padding: 4px; border-radius: 3px; margin: 6px 0; font-size: 10px; color: #666;">
                   <strong>Coordenadas:</strong> ${lat.toFixed(6)}, ${lng.toFixed(6)}<br>
                   <strong>Fuente:</strong> ${addressData.source || 'Geocodificación inversa'}
               </div>
               <button onclick="selectMapLocationFromPopup('${escapedAddress}', ${lat}, ${lng}, '${escapedComponents}')"
                       style="
                           width: 100%; margin-top: 8px; padding: 6px;
                           background: #4CAF50; color: white; border: none;
                           border-radius: 4px; cursor: pointer; font-size: 12px;
                           transition: background-color 0.2s;
                       "
                       onmouseover="this.style.backgroundColor='#45a049'"
                       onmouseout="this.style.backgroundColor='#4CAF50'">
                   ✅ Seleccionar esta dirección
               </button>
           </div>
       `;
   }

    showNotFoundMessage(address, suggestions, processingTime) {
        const msgDiv = document.createElement('div');

        let suggestionsHtml = '';
        if (suggestions && suggestions.length > 0) {
            suggestionsHtml = `
                <div style="margin-top: 8px; padding-top: 8px; border-top: 1px solid #fff3;">
                    <strong>💡 Sugerencias:</strong><br>
                    ${suggestions.map(s => `• ${s}`).join('<br>')}
                </div>
            `;
        }

        msgDiv.innerHTML = `
            <div style="
                position: fixed; top: 20px; right: 20px;
                background: #ff9800; color: white;
                padding: 12px; border-radius: 6px;
                z-index: 10000; max-width: 350px;
                font-size: 12px; box-shadow: 0 4px 8px rgba(0,0,0,0.3);
            ">
                <strong>❌ No se encontró: "${address}"</strong><br>
                <small>Tiempo: ${processingTime}ms</small>
                ${suggestionsHtml}
            </div>
        `;

        document.body.appendChild(msgDiv);
        setTimeout(() => msgDiv.remove(), 8000);
    }

    showErrorMessage(error, processingTime) {
        const errorDiv = document.createElement('div');
        errorDiv.innerHTML = `
            <div style="
                position: fixed; top: 20px; right: 20px;
                background: #f44336; color: white;
                padding: 12px; border-radius: 6px;
                z-index: 10000; max-width: 300px;
                font-size: 12px; box-shadow: 0 4px 8px rgba(0,0,0,0.3);
            ">
                <strong>💥 Error de conexión</strong><br>
                <small>${error}</small><br>
                <small>Tiempo: ${processingTime}ms</small>
            </div>
        `;

        document.body.appendChild(errorDiv);
        setTimeout(() => errorDiv.remove(), 6000);
    }

    updateAddressInputs(components) {
        // Actualizar input principal del modal
        const inputModal = document.getElementById('dirr');
        if (inputModal && components && components.full_address) {
            inputModal.value = components.full_address;
            console.log('Input modal actualizado:', components.full_address);
        }

        // Actualizar inputs específicos si existen
        if (components) {
            const inputs = {
                'calle': components.calle || '',
                'numero': components.numero || '',
                'colonia': components.colonia || '',
                'codigo_postal': components.codigo_postal || '',
                'ciudad': components.ciudad || 'Chihuahua',
                'estado': components.estado || 'Chihuahua'
            };

            for (const [field, value] of Object.entries(inputs)) {
                const input = document.getElementById(field);
                if (input && value) {
                    input.value = value;
                    console.log(`Campo ${field} actualizado: ${value}`);
                }
            }
        }

        console.log('Inputs actualizados con componentes:', components);
    }

    debugGeocodeResponse(data) {
        console.group('🔍 Debug Geocodificación');
        console.log('Respuesta completa:', data);

        if (data.result) {
            console.log('Dirección:', data.result.address);
            console.log('Coordenadas:', data.result.lat, data.result.lng);
            console.log('Componentes:', data.result.components);
            console.log('Fuente:', data.result.source);
            console.log('Score:', data.result.score);
        }

        console.groupEnd();
    }
}

window.LocalGISMap = LocalGISMap;
if (typeof module !== 'undefined' && module.exports) {
    module.exports = LocalGISMap;
}