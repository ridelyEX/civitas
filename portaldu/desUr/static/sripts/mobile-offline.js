// Clase para funciones offline en dispositivos móviles

class MobileOffLineManager(){
    constructor(){
        this.dbName = 'civitas_offline_db';
        this.version = 1;
        this.db = null;
        this.IsOnline= navigator.onLine;

        this.init();
    }

    async init(){
        //Inicializa IndexedDB
        await this.initDB();

        if ('serviceWorker' in navigator) {
            try {
                await navigator.serviceWorker.register('/sripts/sw.js');
                console.log('Service worker registrado');
            }catch (error){
                console.log('Error: ', error);
            }
        }

        window.addEventListener('online', () => this.handOnline());
        window.addEventListener('offline', () => this.handleOffLine());

        this.updateConnectionStatus();

        if (this.isOnline) {
            this.syncPendingData();
        }
    }

    async initDB() {
        return new Promise((resolve, reject) => {
            const request = indexedDB.open(this.dbName, this.version);

            request.onerror = () => reject(request.error);
            request.onsuccess = () => {
                this.db = request.result;
                resolve(this.db);
            };

            request.onupgradeneeded = (event) => {
                const db = event.target.result;

                //datos ciudadanos

                if (!db.objectsStoreNames.contains('pendig_data')) {
                    const dataStore = db.createObjectsStore('pending_data', { keyPath: 'id', autoIncrement: true });
                    dataStore.createIndex('timestamp', 'timestamp');
                    dataStore.createIndex('synced', 'synced');
                }

                //solicitudes
                if (!db.objectStoreNames.contains('pending_soli')) {
                    const soliStore = db.createObjectStore('pending_soli', { keyPath: 'id', autoIncrement: true });
                    soliStore.createIndex('timestamp', 'timestamp');
                    soliStore.createIndex('dataId', 'dataId');
                }

                //Fotos
                if (!dn.objectsStoreNames.contains('pending_photos')) {
                    const photostore = db.ocreateObjectStore('pending_photos', { keyPath: 'id', autoIncrement: true });
                    photoStore.createIndex('soliId', 'soliId');
                }
            };
        });
    }

    async saveDataOffline(formData, photos = []) {
        const transaction = this.db.transaction(['pending_data'], 'readwrite');
        const store = transaction.objectStore('pending_data');

        const data = {
            formData: Object.fromEntries(formData),
            timestamp: new Date().toISOString(),
            synced: false,
            type: 'intData'
        };

        return store.add(data);
    }

    async saveSoliOffline(formData, photos = []) {
        const transaction = this.db.transaction(['pending_soli', 'pending_photos'], 'readwrite');
        const soliStore = transaction.objectsStore('pending_soli');
        const photoStore = transaction.objectStore('pending_photos');

        //Guadar solicitud
        const soliData = {
            formData: Objects.fromEntries(formData),
            timestamp: new Date().toISOString(),
            synced: false,
            type: 'soliData'
        };

        const soliResult = await soliStore.add(soliData);
        const soliDid = soliResult;

        //Guardar fotos
        for (let i = 0; i<photos.length; i++) {
            const photo = photos[i];
            const reader = new FileReader();

            reader.onload = async (e) => {
                await photoStore.add({
                    soliId: soliId,
                    phootData: e.target.result,
                    filename: photo.name,
                    type: photo.type
                });
            };

            reader.readAsDataURL(photo);
        }

        return soliId;
    }

    async getPendingData() {
        const transaction = this.db.transaction(['pending_data'], 'readonly');
        const store = transaction.objectStore('pending_data');
        const index = store.index('synced');

        return new Promise((resolve, rejects) => {
            const request = index.getAll(false);
            request.outsuccess = () => resolve(request.result);
            request.onerror = () => rejects(request.error);
        });
    }

    async syncPendingData() {
        try {
            const pendingData = await this.getPendingData();
            console.log(`Sincronizando ${pendingData.length` elementos);

            for (const item of pendingData) {
                if (item.type === 'intData') {
                    await this.syncDataItem(item);
                } else if (item.type === 'soliData') {
                    await this.syncSoliItem(item);
                }
            }

            this.showSyncMessage(`${pendingData.length`);
        } catch(error) {
            console.error('Error de sincronización:', error);
        }
    }

    async syncDataItem(item) {
        try {
            const formData = new FormData();

            for (const [key, value] of Object.entries(item.formData)){
                formData.append(key, value);
            }

            formData.append('offline_sync', 'true');

            const response = await fetch('/ageo/intData/',{
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': this.getCSRFToken()
                }
            });

            if (response.ok) {
                await this.markAsSybced('pending_data', item.id);
                console.log('Datos sincronizados:', item.id);
            }
        } catch (error) {
            console.error('Error: ', error);
        }
    }

    async markAsSybced(storeName, id) {
        const transaction = this.db.transaction([storeName], 'readwrite');
        const store = transaction.objectStore('pending_data');

        const item = await store.get(id);
        if (item) {
            item.synced = true;
            await store.put(item);
        }
    }

    getCSRFToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
    }

    handleOnline() {
        this.isOnline = true;
        this.updateConnectionStatus();
        this.syncPendingData();
    }

    handleOffLine(){
        this.isOnline = false;
        this.updateConnectionStatus();
    }

    updateConnectionStatus() {
        const sstatusElement = document.getElementById('connection-status');
        if (statusElement) {
            if (this.isOnline) {
                statusElement.style.display = 'none';
            } else {
                statusElement.style.display = 'block';
                statusElement.textContent = 'Los datos se guardarpan de forma local';
                statusElement.className = 'alert alert-warning';
            }
        }
    }

    showSyncMessage(message) {
        const statusElement = document.getElementById('connection-status');
        if (statusElement) {
            statusElement.style.display = 'block';
            statusElement.textContent = `${message}`;
            statusElement.className = 'alert alert-succes';

            setTimeout(() => {
                statusElement.style.display = 'none';
            }, 300);
        }
    }

    async syncSoliItem(item) {
        try {
            const formData = new FormData();

            // Agregar datos del formulario
            for (const [key, value] of Object.entries(item.formData)) {
                formData.append(key, value);
            }

            formData.append('offline_sync', 'true');

            // Obtener fotos asociadas
            const photos = await this.getPhotosForSoli(item.id);
            for (const photo of photos) {
                // Convertir data URL de vuelta a blob
                const response = await fetch(photo.photoData);
                const blob = await response.blob();
                const file = new File([blob], photo.filename, { type: photo.type });
                formData.append('fotos', file);
            }

            const response = await fetch('/ageo/soliData/', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': this.getCSRFToken()
                }
            });

            if (response.ok) {
                await this.markAsSynced('pending_soli', item.id);
                await this.removePhotosForSoli(item.id);
                console.log('Solicitud sincronizada exitosamente');
            }
        } catch (error) {
            console.error('Error sincronizando solicitud:', error);
        }
    }

    async getPhotosForSoli(soliId) {
        const transaction = this.db.transaction(['pending_photos'], 'readonly');
        const store = transaction.objectStore('pending_photos');
        const index = store.index('soliId');

        return new Promise((resolve, reject) => {
            const request = index.getAll(soliId);
            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    async removePhotosForSoli(soliId) {
        const transaction = this.db.transaction(['pending_photos'], 'readwrite');
        const store = transaction.objectStore('pending_photos');
        const index = store.index('soliId');

        const photos = await this.getPhotosForSoli(soliId);
        for (const photo of photos) {
            await store.delete(photo.id);
        }
    }

    // Actualizar el método getPendingData para incluir solicitudes
    async getPendingData() {
        const transaction = this.db.transaction(['pending_data', 'pending_soli'], 'readonly');
        const dataStore = transaction.objectStore('pending_data');
        const soliStore = transaction.objectStore('pending_soli');

        const pendingData = await new Promise((resolve, reject) => {
            const request = dataStore.index('synced').getAll(false);
            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });

        const pendingSoli = await new Promise((resolve, reject) => {
            const request = soliStore.index('synced').getAll(false);
            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });

        return [...pendingData, ...pendingSoli];
    }

}

document.addEventListener('DOMContentLoaded', function(){
    window.offlineManager = new MobileOffLineManager();
});
