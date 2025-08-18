/**
 * DesUr Mobile Offline Manager
 * Maneja funcionalidad offline para dispositivos móviles
 */

class DesUrMobileManager {
    constructor() {
        this.isOnline = navigator.onLine;
        this.offlineForms = [];
        this.syncInProgress = false;
        this.dbName = 'DesUrOfflineDB';
        this.dbVersion = 1;

        this.init();
    }

    async init() {
        // Registrar Service Worker
        await this.registerServiceWorker();

        // Configurar eventos de red
        this.setupNetworkEvents();

        // Configurar manejo de formularios offline
        this.setupOfflineFormHandling();

        // Inicializar UI offline
        this.updateUIStatus();

        // Intentar sincronizar datos pendientes
        if (this.isOnline) {
            this.syncOfflineData();
        }
    }

    async registerServiceWorker() {
        if ('serviceWorker' in navigator) {
            try {
                const registration = await navigator.serviceWorker.register('/desur/sw.js', {
                    scope: '/desur/'
                });

                console.log('DesUr: Service Worker registrado:', registration.scope);

                // Escuchar mensajes del SW
                navigator.serviceWorker.addEventListener('message', event => {
                    this.handleServiceWorkerMessage(event);
                });

                // Manejar actualizaciones del SW
                registration.addEventListener('updatefound', () => {
                    const newWorker = registration.installing;
                    newWorker.addEventListener('statechange', () => {
                        if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                            this.showUpdateAvailable();
                        }
                    });
                });

            } catch (error) {
                console.error('DesUr: Error registrando Service Worker:', error);
            }
        }
    }

    setupNetworkEvents() {
        window.addEventListener('online', () => {
            this.isOnline = true;
            this.updateUIStatus();
            this.syncOfflineData();
            this.showNotification('Conexión restaurada. Sincronizando datos...', 'success');
        });

        window.addEventListener('offline', () => {
            this.isOnline = false;
            this.updateUIStatus();
            this.showNotification('Modo offline activado. Los datos se guardarán localmente.', 'warning');
        });
    }

    setupOfflineFormHandling() {
        // Interceptar envío de formularios
        document.addEventListener('submit', (event) => {
            if (!this.isOnline) {
                event.preventDefault();
                this.handleOfflineFormSubmit(event.target);
            }
        });

        // Interceptar llamadas AJAX
        const originalFetch = window.fetch;
        window.fetch = async (...args) => {
            try {
                return await originalFetch(...args);
            } catch (error) {
                if (!this.isOnline && args[0].includes('/desur/')) {
                    return this.handleOfflineRequest(...args);
                }
                throw error;
            }
        };
    }

    async handleOfflineFormSubmit(form) {
        try {
            const formData = new FormData(form);
            const offlineForm = {
                url: form.action || window.location.pathname,
                method: form.method || 'POST',
                data: Object.fromEntries(formData.entries()),
                timestamp: Date.now(),
                type: 'form'
            };

            await this.saveOfflineData(offlineForm);

            this.showNotification('Formulario guardado offline. Se enviará automáticamente cuando recuperes la conexión.', 'info');

            // Simular respuesta exitosa para la UI
            if (form.dataset.successRedirect) {
                window.location.href = form.dataset.successRedirect;
            }

        } catch (error) {
            console.error('Error guardando formulario offline:', error);
            this.showNotification('Error guardando datos offline', 'error');
        }
    }

    async handleOfflineRequest(url, options = {}) {
        // Para requests GET, intentar cache primero
        if (!options.method || options.method === 'GET') {
            return new Response('{"error": "Sin conexión"}', {
                status: 503,
                headers: { 'Content-Type': 'application/json' }
            });
        }

        // Para POST/PUT, guardar para sincronización posterior
        if (options.body) {
            const offlineRequest = {
                url: url,
                method: options.method || 'POST',
                headers: options.headers || {},
                body: options.body,
                timestamp: Date.now(),
                type: 'ajax'
            };

            await this.saveOfflineData(offlineRequest);

            return new Response(JSON.stringify({
                success: true,
                message: 'Datos guardados offline',
                offline: true
            }), {
                status: 200,
                headers: { 'Content-Type': 'application/json' }
            });
        }
    }

    async saveOfflineData(data) {
        return new Promise((resolve, reject) => {
            const request = indexedDB.open(this.dbName, this.dbVersion);

            request.onerror = () => reject(request.error);

            request.onsuccess = () => {
                const db = request.result;
                const transaction = db.transaction(['offline_data'], 'readwrite');
                const store = transaction.objectStore('offline_data');

                store.add(data);
                transaction.oncomplete = () => resolve();
            };

            request.onupgradeneeded = () => {
                const db = request.result;
                if (!db.objectStoreNames.contains('offline_data')) {
                    const store = db.createObjectStore('offline_data', { keyPath: 'timestamp' });
                    store.createIndex('type', 'type', { unique: false });
                    store.createIndex('url', 'url', { unique: false });
                }
            };
        });
    }

    async getOfflineData() {
        return new Promise((resolve, reject) => {
            const request = indexedDB.open(this.dbName, this.dbVersion);

            request.onerror = () => reject(request.error);

            request.onsuccess = () => {
                const db = request.result;
                const transaction = db.transaction(['offline_data'], 'readonly');
                const store = transaction.objectStore('offline_data');
                const getAllRequest = store.getAll();

                getAllRequest.onsuccess = () => resolve(getAllRequest.result);
            };
        });
    }

    async removeOfflineData(timestamp) {
        return new Promise((resolve, reject) => {
            const request = indexedDB.open(this.dbName, this.dbVersion);

            request.onerror = () => reject(request.error);

            request.onsuccess = () => {
                const db = request.result;
                const transaction = db.transaction(['offline_data'], 'readwrite');
                const store = transaction.objectStore('offline_data');

                store.delete(timestamp);
                transaction.oncomplete = () => resolve();
            };
        });
    }

    async syncOfflineData() {
        if (this.syncInProgress || !this.isOnline) return;

        this.syncInProgress = true;

        try {
            const offlineData = await this.getOfflineData();

            if (offlineData.length === 0) {
                this.syncInProgress = false;
                return;
            }

            this.showNotification(`Sincronizando ${offlineData.length} elementos...`, 'info');

            let synced = 0;

            for (const item of offlineData) {
                try {
                    let response;

                    if (item.type === 'form') {
                        const formData = new FormData();
                        Object.entries(item.data).forEach(([key, value]) => {
                            formData.append(key, value);
                        });

                        response = await fetch(item.url, {
                            method: item.method,
                            body: formData,
                            headers: {
                                'X-Requested-With': 'XMLHttpRequest'
                            }
                        });
                    } else if (item.type === 'ajax') {
                        response = await fetch(item.url, {
                            method: item.method,
                            headers: item.headers,
                            body: item.body
                        });
                    }

                    if (response && response.ok) {
                        await this.removeOfflineData(item.timestamp);
                        synced++;
                    }

                } catch (error) {
                    console.error('Error sincronizando item:', error);
                }
            }

            if (synced > 0) {
                this.showNotification(`${synced} elementos sincronizados exitosamente`, 'success');
            }

        } catch (error) {
            console.error('Error en sincronización:', error);
        } finally {
            this.syncInProgress = false;
        }
    }

    updateUIStatus() {
        // Actualizar indicador de estado de conexión
        const statusElements = document.querySelectorAll('.connection-status');
        statusElements.forEach(element => {
            element.textContent = this.isOnline ? 'En línea' : 'Sin conexión';
            element.className = `connection-status ${this.isOnline ? 'online' : 'offline'}`;
        });

        // Actualizar botones y funcionalidad según estado
        const offlineButtons = document.querySelectorAll('.offline-disabled');
        offlineButtons.forEach(button => {
            button.disabled = !this.isOnline;
            if (!this.isOnline) {
                button.title = 'Esta función requiere conexión a internet';
            }
        });

        // Mostrar/ocultar elementos específicos para offline
        const onlineOnly = document.querySelectorAll('.online-only');
        const offlineOnly = document.querySelectorAll('.offline-only');

        onlineOnly.forEach(element => {
            element.style.display = this.isOnline ? 'block' : 'none';
        });

        offlineOnly.forEach(element => {
            element.style.display = this.isOnline ? 'none' : 'block';
        });
    }

    showNotification(message, type = 'info') {
        // Crear notificación visual
        const notification = document.createElement('div');
        notification.className = `alert alert-${type} mobile-notification`;
        notification.innerHTML = `
            <div class="d-flex align-items-center">
                <i class="fas fa-${this.getIconForType(type)} me-2"></i>
                <span>${message}</span>
                <button type="button" class="btn-close ms-auto" aria-label="Cerrar"></button>
            </div>
        `;

        // Posicionar en la parte superior
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            left: 50%;
            transform: translateX(-50%);
            z-index: 9999;
            min-width: 300px;
            max-width: 90vw;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        `;

        document.body.appendChild(notification);

        // Cerrar automáticamente después de 5 segundos
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 5000);

        // Cerrar al hacer click en el botón
        notification.querySelector('.btn-close').addEventListener('click', () => {
            notification.remove();
        });
    }

    getIconForType(type) {
        const icons = {
            'success': 'check-circle',
            'error': 'exclamation-triangle',
            'warning': 'exclamation-circle',
            'info': 'info-circle'
        };
        return icons[type] || 'info-circle';
    }

    showUpdateAvailable() {
        const notification = document.createElement('div');
        notification.className = 'alert alert-info mobile-notification';
        notification.innerHTML = `
            <div class="d-flex align-items-center">
                <i class="fas fa-download me-2"></i>
                <span>Nueva versión disponible</span>
                <button type="button" class="btn btn-sm btn-primary ms-2" id="update-app">Actualizar</button>
                <button type="button" class="btn-close ms-2" aria-label="Cerrar"></button>
            </div>
        `;

        notification.style.cssText = `
            position: fixed;
            top: 20px;
            left: 50%;
            transform: translateX(-50%);
            z-index: 9999;
            min-width: 300px;
            max-width: 90vw;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        `;

        document.body.appendChild(notification);

        notification.querySelector('#update-app').addEventListener('click', () => {
            if (navigator.serviceWorker && navigator.serviceWorker.controller) {
                navigator.serviceWorker.controller.postMessage({ type: 'SKIP_WAITING' });
                window.location.reload();
            }
        });

        notification.querySelector('.btn-close').addEventListener('click', () => {
            notification.remove();
        });
    }

    handleServiceWorkerMessage(event) {
        const { data } = event;

        if (data.type === 'FORM_SYNCED') {
            if (data.success) {
                this.showNotification('Formulario sincronizado exitosamente', 'success');
            } else {
                this.showNotification('Error sincronizando formulario', 'error');
            }
        }
    }

    // Métodos públicos para uso en la aplicación
    async getCacheStatus() {
        if (!navigator.serviceWorker || !navigator.serviceWorker.controller) {
            return null;
        }

        return new Promise((resolve) => {
            const messageChannel = new MessageChannel();
            messageChannel.port1.onmessage = (event) => {
                resolve(event.data);
            };

            navigator.serviceWorker.controller.postMessage(
                { type: 'GET_CACHE_STATUS' },
                [messageChannel.port2]
            );
        });
    }

    async clearOfflineData() {
        try {
            const offlineData = await this.getOfflineData();
            for (const item of offlineData) {
                await this.removeOfflineData(item.timestamp);
            }
            this.showNotification('Datos offline eliminados', 'info');
        } catch (error) {
            console.error('Error limpiando datos offline:', error);
        }
    }
}

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', () => {
    window.desurMobile = new DesUrMobileManager();
});

// Exportar para uso global
window.DesUrMobileManager = DesUrMobileManager;
