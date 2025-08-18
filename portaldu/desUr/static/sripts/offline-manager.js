/**
 * DesUr Offline Manager
 * Gestiona funcionalidad offline, detección móvil y sincronización
 */

class DesUrOfflineManager {
    constructor() {
        this.isOnline = navigator.onLine;
        this.isMobile = this.detectMobile();
        this.offlineQueue = [];
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.setupOfflineSync();
        this.initializeUI();
        this.checkMobileRedirect();
    }

    detectMobile() {
        const userAgent = navigator.userAgent || navigator.vendor || window.opera;

        // Detectar dispositivos móviles específicos
        const mobileRegex = /android|webos|iphone|ipad|ipod|blackberry|iemobile|opera mini/i;
        const isAndroid = /android/i.test(userAgent);
        const isIOS = /iPad|iPhone|iPod/.test(userAgent) && !window.MSStream;
        const isTablet = /tablet|ipad|playbook|silk/i.test(userAgent);

        // Verificar tamaño de pantalla como respaldo
        const screenWidth = window.screen.width;
        const isMobileScreen = screenWidth <= 768;

        return mobileRegex.test(userAgent) || isAndroid || isIOS || (isMobileScreen && !isTablet);
    }

    checkMobileRedirect() {
        if (this.isMobile && !window.location.pathname.includes('/mobile/')) {
            const mobilePages = [
                '/ageo/auth/menu/',
                '/ageo/auth/historial/',
                '/ageo/main/',
                '/ageo/docs/',
                '/ageo/fotos/',
                '/ageo/mapa/'
            ];

            const currentPath = window.location.pathname;

            if (mobilePages.some(page => currentPath.includes(page.replace('/mobile/', '')))) {
                const mobilePath = currentPath.replace('/ageo/', '/ageo/mobile/');
                console.log('Redirigiendo a versión móvil:', mobilePath);
                window.location.href = mobilePath;
            }
        }
    }

    setupEventListeners() {
        // Eventos de conexión
        window.addEventListener('online', () => this.handleOnline());
        window.addEventListener('offline', () => this.handleOffline());

        // Eventos de Service Worker
        if ('serviceWorker' in navigator) {
            navigator.serviceWorker.addEventListener('message', (event) => {
                this.handleSWMessage(event);
            });
        }

        // Interceptar formularios para funcionamiento offline
        document.addEventListener('submit', (event) => {
            this.handleFormSubmit(event);
        });

        // Eventos de visibilidad de página
        document.addEventListener('visibilitychange', () => {
            if (!document.hidden && this.isOnline) {
                this.syncOfflineData();
            }
        });
    }

    handleOnline() {
        this.isOnline = true;
        this.updateConnectionIndicator();
        this.syncOfflineData();
        this.showNotification('Conexión restaurada', 'success');
    }

    handleOffline() {
        this.isOnline = false;
        this.updateConnectionIndicator();
        this.showNotification('Sin conexión - Modo offline activado', 'warning');
    }

    updateConnectionIndicator() {
        const indicator = document.getElementById('connectionIndicator');
        if (!indicator) return;

        if (this.isOnline) {
            indicator.className = 'connection-indicator status-online';
            indicator.innerHTML = '🌐 Conectado';
        } else {
            indicator.className = 'connection-indicator status-offline';
            indicator.innerHTML = '📶 Sin conexión';

            // Agregar contador de elementos offline si hay
            const offlineCount = this.getOfflineQueueCount();
            if (offlineCount > 0) {
                indicator.innerHTML += `<span class="offline-counter">${offlineCount}</span>`;
            }
        }
    }

    handleFormSubmit(event) {
        if (!this.isOnline) {
            event.preventDefault();
            this.saveFormOffline(event.target);
            return false;
        }
    }

    saveFormOffline(form) {
        const formData = new FormData(form);
        const offlineItem = {
            id: Date.now(),
            url: form.action || window.location.href,
            method: form.method || 'POST',
            data: Object.fromEntries(formData.entries()),
            timestamp: new Date().toISOString(),
            type: 'form'
        };

        this.addToOfflineQueue(offlineItem);
        this.showNotification('Formulario guardado offline. Se enviará cuando recuperes la conexión.', 'info');
    }

    addToOfflineQueue(item) {
        // Guardar en localStorage para persistencia
        let offlineQueue = JSON.parse(localStorage.getItem('ageo_offline_queue') || '[]');
        offlineQueue.push(item);
        localStorage.setItem('ageo_offline_queue', JSON.stringify(offlineQueue));

        this.updateConnectionIndicator();
    }

    getOfflineQueueCount() {
        const offlineQueue = JSON.parse(localStorage.getItem('ageo_offline_queue') || '[]');
        return offlineQueue.length;
    }

    async syncOfflineData() {
        if (!this.isOnline) return;

        const offlineQueue = JSON.parse(localStorage.getItem('ageo_offline_queue') || '[]');
        if (offlineQueue.length === 0) return;

        console.log('Sincronizando datos offline...', offlineQueue);

        const syncedItems = [];

        for (const item of offlineQueue) {
            try {
                await this.syncItem(item);
                syncedItems.push(item);
            } catch (error) {
                console.error('Error sincronizando item:', error);
            }
        }

        // Remover items sincronizados
        if (syncedItems.length > 0) {
            const remainingQueue = offlineQueue.filter(item =>
                !syncedItems.some(synced => synced.id === item.id)
            );

            localStorage.setItem('ageo_offline_queue', JSON.stringify(remainingQueue));
            this.showNotification(`${syncedItems.length} elementos sincronizados`, 'success');
            this.updateConnectionIndicator();
        }
    }

    async syncItem(item) {
        const formData = new FormData();

        // Agregar datos del formulario
        Object.entries(item.data).forEach(([key, value]) => {
            formData.append(key, value);
        });

        // Agregar token CSRF si está disponible
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
        if (csrfToken) {
            formData.append('csrfmiddlewaretoken', csrfToken.value);
        }

        const response = await fetch(item.url, {
            method: item.method,
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        return response;
    }

    handleSWMessage(event) {
        const message = event.data;

        switch (message.type) {
            case 'FORM_SYNCED':
                this.showNotification('Formulario sincronizado exitosamente', 'success');
                break;
            case 'CACHE_UPDATED':
                this.showNotification('Aplicación actualizada', 'info');
                break;
        }
    }

    showNotification(message, type = 'info') {
        // Crear elemento de notificación
        const notification = document.createElement('div');
        notification.className = `alert alert-${this.getBootstrapClass(type)} alert-dismissible fade show`;
        notification.style.cssText = `
            position: fixed;
            top: 70px;
            right: 20px;
            z-index: 1100;
            max-width: 300px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        `;

        notification.innerHTML = `
            <strong>${this.getTypeIcon(type)}</strong> ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        document.body.appendChild(notification);

        // Auto-remove después de 5 segundos
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 5000);
    }

    getBootstrapClass(type) {
        const classMap = {
            'success': 'success',
            'error': 'danger',
            'warning': 'warning',
            'info': 'info'
        };
        return classMap[type] || 'info';
    }

    getTypeIcon(type) {
        const iconMap = {
            'success': '✅',
            'error': '❌',
            'warning': '⚠️',
            'info': 'ℹ️'
        };
        return iconMap[type] || 'ℹ️';
    }

    setupOfflineSync() {
        // Intentar sincronizar cada 30 segundos si está online
        setInterval(() => {
            if (this.isOnline) {
                this.syncOfflineData();
            }
        }, 30000);

        // Sincronizar cuando la página se vuelve visible
        document.addEventListener('visibilitychange', () => {
            if (!document.hidden && this.isOnline) {
                setTimeout(() => this.syncOfflineData(), 1000);
            }
        });
    }

    initializeUI() {
        // Aplicar estilos móviles si es necesario
        if (this.isMobile) {
            document.body.classList.add('mobile-device');

            // Mejorar experiencia táctil
            const style = document.createElement('style');
            style.textContent = `
                .mobile-device {
                    -webkit-touch-callout: none;
                    -webkit-user-select: none;
                    -webkit-tap-highlight-color: transparent;
                }

                .mobile-device button,
                .mobile-device .btn {
                    min-height: 44px;
                    touch-action: manipulation;
                }

                .mobile-device input,
                .mobile-device select,
                .mobile-device textarea {
                    font-size: 16px; /* Prevenir zoom en iOS */
                }
            `;
            document.head.appendChild(style);
        }

        // Inicializar indicador de conexión
        this.updateConnectionIndicator();
    }

    // Método público para obtener estado
    getStatus() {
        return {
            isOnline: this.isOnline,
            isMobile: this.isMobile,
            offlineQueueCount: this.getOfflineQueueCount(),
            userAgent: navigator.userAgent
        };
    }
}

// Inicializar el manager cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', () => {
    window.desUrOfflineManager = new DesUrOfflineManager();

    // Exponer globalmente para debugging
    window.getDesUrStatus = () => window.desUrOfflineManager.getStatus();
});

// Exportar para uso en módulos
if (typeof module !== 'undefined' && module.exports) {
    module.exports = DesUrOfflineManager;
}
