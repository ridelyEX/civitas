const CACHE_NAME = 'ageo-mobile-v1';
const OFFLINE_URL '/ageo/offline/';

const CRITICAL_RESOURCES = [
    '/ageo/',
    '/ageo/intData/',
    '/ageo/soliData/',
    '/static/css/bootstrap.min.css',
    '/static/js/jquery.min.js',
    '/static/sripts/mobile-app.js'
];

self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME)
        .then(cache => cache.addAll(CRITICAL_RESOURCES))
        .then(() => self.skipWaiting)
    );
});

self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then(cacheNames => {
            return Promise.all(
                cacheNames.map(cacheNames => {
                    return cache.delete(cacheNames);
                });
            );
        });
    );
});

self.addEventListener('fetch', (event) => {
    const { request} = event;

    if (request.url.includes('/ageo/intData') || request.url.includes('/ageo/soliData')) {
        event.respondWith(
            fetch(request)
            .catch(() => cache.match(OFFLINE_URL))
        );
    }

    else if (request.url.includes('/static/')) {
        event.respondWith(
            caches.match(request)
                .then(response => response || fetch(request))
        );
    }
    else {
        event.respondWith(
            fetch(request)
                .catch(() => caches.match(OFFLINE_URL))
        );
    }

});