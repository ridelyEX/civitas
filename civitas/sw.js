const CACHE_NAME = 'ageo-mobile-v2.0.0';
const OFFLINE_URL = '/ageo/offline/';
const API_CACHE = 'ageo-api-cache-v1';
const FORMS_CACHE = 'ageo-forms-cache-v1';

// Recursos estáticos críticos para funcionamiento offline
const STATIC_CACHE_URLS = [
  '/ageo/',
  '/ageo/auth/menu/',
  '/ageo/main/',
  '/ageo/offline/',
  '/ageo/manifest.json',
  '/static/styles/bootstrap.min.css',
  '/static/styles/style.css',
  '/static/sripts/jquery.min.js',
  '/static/sripts/bootstrap.min.js',
  '/static/sripts/mobile-offline.js',
  '/static/sripts/offline-manager.js',
  '/static/images/icon-192x192.png',
  '/static/images/icon-512x512.png'
];

// URLs de formularios que deben funcionar offline
const FORM_URLS = [
  '/ageo/auth/menu/',
  '/ageo/main/',
  '/ageo/documet/',
  '/ageo/fotos/',
  '/ageo/mapa/',
  '/ageo/docs/',
  '/ageo/pp/',
  '/ageo/pago/'
];

// Instalación del Service Worker
self.addEventListener('install', event => {
  console.log('Ageo SW: Instalando Service Worker...');
  event.waitUntil(
    Promise.all([
      caches.open(CACHE_NAME).then(cache => {
        console.log('Ageo SW: Precacheando recursos estáticos...');
        return cache.addAll(STATIC_CACHE_URLS.map(url => new Request(url, { credentials: 'same-origin' })));
      }),
      caches.open(API_CACHE),
      caches.open(FORMS_CACHE)
    ]).then(() => {
      console.log('Ageo SW: Instalación completada');
      return self.skipWaiting();
    }).catch(error => {
      console.error('Ageo SW: Error en instalación:', error);
    })
  );
});

// Activación del Service Worker
self.addEventListener('activate', event => {
  console.log('Ageo SW: Activando Service Worker...');
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (cacheName !== CACHE_NAME && cacheName !== API_CACHE && cacheName !== FORMS_CACHE) {
            console.log('Ageo SW: Eliminando cache antiguo:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    }).then(() => {
      console.log('Ageo SW: Activación completada');
      return self.clients.claim();
    })
  );
});

// Interceptar requests para estrategia offline-first
self.addEventListener('fetch', event => {
  const request = event.request;
  const url = new URL(request.url);

  // Ignorar requests que no son GET o que son cross-origin
  if (request.method !== 'GET' || url.origin !== location.origin) {
    return;
  }

  // Estrategia para páginas HTML - Cache First con Network Update
  if (request.headers.get('accept')?.includes('text/html')) {
    event.respondWith(handlePageRequest(request));
    return;
  }

  // Estrategia para recursos estáticos - Cache First
  if (url.pathname.startsWith('/static/') || url.pathname.startsWith('/media/')) {
    event.respondWith(handleStaticRequest(request));
    return;
  }

  // Estrategia para API calls - Network First con Cache Fallback
  if (url.pathname.startsWith('/ageo/api/') || url.pathname.includes('/api/')) {
    event.respondWith(handleApiRequest(request));
    return;
  }

  // Estrategia para formularios POST offline
  if (request.method === 'POST' && url.pathname.startsWith('/ageo/')) {
    event.respondWith(handleFormSubmission(request));
    return;
  }
});

// Manejar requests de páginas HTML
async function handlePageRequest(request) {
  try {
    // Intentar cache primero para respuesta instantánea
    const cachedResponse = await caches.match(request);

    if (cachedResponse) {
      // Actualizar cache en background si hay conexión
      updateCacheInBackground(request);
      return cachedResponse;
    }

    // Si no está en cache, intentar red
    const networkResponse = await fetch(request);

    if (networkResponse.ok) {
      // Guardar en cache
      const cache = await caches.open(CACHE_NAME);
      cache.put(request, networkResponse.clone());
      return networkResponse;
    }

    // Si hay error de red, mostrar página offline
    return await caches.match(OFFLINE_URL) || new Response('Offline', { status: 503 });

  } catch (error) {
    console.log('Ageo SW: Error en page request:', error);
    return await caches.match(OFFLINE_URL) || new Response('Offline', { status: 503 });
  }
}

// Manejar recursos estáticos
async function handleStaticRequest(request) {
  try {
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      return cachedResponse;
    }

    const networkResponse = await fetch(request);
    if (networkResponse.ok) {
      const cache = await caches.open(CACHE_NAME);
      cache.put(request, networkResponse.clone());
    }
    return networkResponse;

  } catch (error) {
    console.log('Ageo SW: Error en static request:', error);
    return new Response('Resource not available offline', { status: 503 });
  }
}

// Manejar calls de API
async function handleApiRequest(request) {
  try {
    // Network first para datos actualizados
    const networkResponse = await fetch(request);

    if (networkResponse.ok) {
      const cache = await caches.open(API_CACHE);
      cache.put(request, networkResponse.clone());
      return networkResponse;
    }

    // Fallback a cache si hay error
    const cachedResponse = await caches.match(request);
    return cachedResponse || new Response('{"error": "Sin conexión"}', {
      status: 503,
      headers: { 'Content-Type': 'application/json' }
    });

  } catch (error) {
    console.log('Ageo SW: Error en API request:', error);
    const cachedResponse = await caches.match(request);
    return cachedResponse || new Response('{"error": "Sin conexión"}', {
      status: 503,
      headers: { 'Content-Type': 'application/json' }
    });
  }
}

// Actualizar cache en background
async function updateCacheInBackground(request) {
  try {
    const networkResponse = await fetch(request);
    if (networkResponse.ok) {
      const cache = await caches.open(CACHE_NAME);
      cache.put(request, networkResponse);
    }
  } catch (error) {
    // Silencioso - es solo para actualización en background
  }
}

// Manejar envío de formularios offline
async function handleFormSubmission(request) {
  try {
    // Intentar envío inmediato
    const response = await fetch(request.clone());
    return response;

  } catch (error) {
    // Si falla, guardar para sincronización posterior
    const formData = await request.clone().formData();
    const offlineForm = {
      url: request.url,
      method: request.method,
      headers: Object.fromEntries(request.headers.entries()),
      body: Object.fromEntries(formData.entries()),
      timestamp: Date.now()
    };

    // Guardar en IndexedDB para sincronización posterior
    await saveOfflineForm(offlineForm);

    // Registrar background sync si está disponible
    if ('serviceWorker' in navigator && 'sync' in window.ServiceWorkerRegistration.prototype) {
      await self.registration.sync.register('ageo-form-sync');
    }

    return new Response(JSON.stringify({
      success: true,
      message: 'Formulario guardado offline. Se enviará cuando recuperes la conexión.',
      offline: true
    }), {
      status: 200,
      headers: { 'Content-Type': 'application/json' }
    });
  }
}

// Background Sync para formularios offline
self.addEventListener('sync', event => {
  console.log('Ageo SW: Background sync event:', event.tag);

  if (event.tag === 'ageo-form-sync') {
    event.waitUntil(syncOfflineForms());
  }
});

// Sincronizar formularios offline
async function syncOfflineForms() {
  try {
    const offlineForms = await getOfflineForms();

    for (const form of offlineForms) {
      try {
        const formData = new FormData();
        Object.entries(form.body).forEach(([key, value]) => {
          formData.append(key, value);
        });

        const response = await fetch(form.url, {
          method: form.method,
          body: formData,
          headers: {
            'X-Requested-With': 'XMLHttpRequest'
          }
        });

        if (response.ok) {
          await removeOfflineForm(form.timestamp);
          console.log('Ageo SW: Formulario sincronizado exitosamente');

          // Notificar al cliente
          const clients = await self.clients.matchAll();
          clients.forEach(client => {
            client.postMessage({
              type: 'FORM_SYNCED',
              success: true,
              form: form
            });
          });
        }

      } catch (error) {
        console.log('Ageo SW: Error sincronizando formulario:', error);
      }
    }

  } catch (error) {
    console.log('Ageo SW: Error en sync de formularios:', error);
  }
}

// Funciones para manejo de IndexedDB (formularios offline)
async function saveOfflineForm(form) {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open('ageoOfflineDB', 1);

    request.onerror = () => reject(request.error);
    request.onsuccess = () => {
      const db = request.result;
      const transaction = db.transaction(['forms'], 'readwrite');
      const store = transaction.objectStore('forms');
      store.add(form);
      transaction.oncomplete = () => resolve();
    };

    request.onupgradeneeded = () => {
      const db = request.result;
      if (!db.objectStoreNames.contains('forms')) {
        const store = db.createObjectStore('forms', { keyPath: 'timestamp' });
        store.createIndex('url', 'url', { unique: false });
      }
    };
  });
}

async function getOfflineForms() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open('ageoOfflineDB', 1);

    request.onerror = () => reject(request.error);
    request.onsuccess = () => {
      const db = request.result;
      const transaction = db.transaction(['forms'], 'readonly');
      const store = transaction.objectStore('forms');
      const getAllRequest = store.getAll();

      getAllRequest.onsuccess = () => resolve(getAllRequest.result);
    };
  });
}

async function removeOfflineForm(timestamp) {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open('ageoOfflineDB', 1);

    request.onerror = () => reject(request.error);
    request.onsuccess = () => {
      const db = request.result;
      const transaction = db.transaction(['forms'], 'readwrite');
      const store = transaction.objectStore('forms');
      store.delete(timestamp);
      transaction.oncomplete = () => resolve();
    };
  });
}

// Manejar mensajes del cliente
self.addEventListener('message', event => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }

  if (event.data && event.data.type === 'GET_CACHE_STATUS') {
    getCacheStatus().then(status => {
      event.ports[0].postMessage(status);
    });
  }
});

// Obtener estado del cache
async function getCacheStatus() {
  const cacheNames = await caches.keys();
  const totalSize = await Promise.all(
    cacheNames.map(async name => {
      const cache = await caches.open(name);
      const keys = await cache.keys();
      return keys.length;
    })
  );

  return {
    caches: cacheNames.length,
    resources: totalSize.reduce((a, b) => a + b, 0),
    version: CACHE_NAME
  };
}

console.log('Ageo SW: Service Worker cargado correctamente');
