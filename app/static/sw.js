const CACHE_NAME = 'homeserver-dashboard-v1';

const STATIC_ASSETS = [
    '/',
    '/static/manifest.json',
    '/static/icons/icon-192.svg',
    '/static/icons/icon-512.svg',
    '/static/dashboard.css',
    '/static/dashboard.js'
];

self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then((cache) => cache.addAll(STATIC_ASSETS))
            .then(() => self.skipWaiting())
    );
});

self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys()
            .then((cacheNames) => {
                return Promise.all(
                    cacheNames
                        .filter((name) => name !== CACHE_NAME)
                        .map((name) => caches.delete(name))
                );
            })
            .then(() => self.clients.claim())
    );
});

self.addEventListener('fetch', (event) => {
    const { request } = event;
    const url = new URL(request.url);

    if (url.pathname.startsWith('/api/')) {
        event.respondWith(
            fetch(request)
                .catch(() => {
                    return new Response(
                        JSON.stringify({
                            error: 'Offline',
                            message: 'Unable to fetch data while offline'
                        }),
                        {
                            status: 503,
                            headers: { 'Content-Type': 'application/json' }
                        }
                    );
                })
        );
        return;
    }

    event.respondWith(
        caches.match(request)
            .then((cachedResponse) => {
                if (cachedResponse) {
                    event.waitUntil(
                        fetch(request)
                            .then((networkResponse) => {
                                if (networkResponse.ok) {
                                    caches.open(CACHE_NAME)
                                        .then((cache) => cache.put(request, networkResponse));
                                }
                            })
                            .catch(() => {})
                    );
                    return cachedResponse;
                }

                return fetch(request)
                    .then((networkResponse) => {
                        if (networkResponse.ok) {
                            const responseToCache = networkResponse.clone();
                            caches.open(CACHE_NAME)
                                .then((cache) => cache.put(request, responseToCache));
                        }
                        return networkResponse;
                    });
            })
    );
});
