const CACHE_NAME = "dashboard-v1";
const STATIC_ASSETS = [
    "/",
    "/static/manifest.json",
    "/static/icons/icon-192.svg",
    "/static/icons/icon-512.svg"
];

self.addEventListener("install", (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            return cache.addAll(STATIC_ASSETS);
        })
    );
    self.skipWaiting();
});

self.addEventListener("activate", (event) => {
    event.waitUntil(
        caches.keys().then((keys) => {
            return Promise.all(
                keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key))
            );
        })
    );
    self.clients.claim();
});

self.addEventListener("fetch", (event) => {
    const { request } = event;

    if (request.url.includes("/api/")) {
        event.respondWith(
            fetch(request).catch(() => {
                return new Response(JSON.stringify({ error: "Offline" }), {
                    headers: { "Content-Type": "application/json" }
                });
            })
        );
        return;
    }

    event.respondWith(
        caches.match(request).then((cached) => {
            const fetched = fetch(request).then((response) => {
                if (response && response.status === 200) {
                    const clone = response.clone();
                    caches.open(CACHE_NAME).then((cache) => {
                        cache.put(request, clone);
                    });
                }
                return response;
            }).catch(() => cached);

            return cached || fetched;
        })
    );
});
