/* Field cache for mapa-purificadoras — app shell + vendor + geojson.
 * Network-first for HTML (cache fallback); stale-while-revalidate for vendor/data.
 * Bump CACHE on each deploy. Do not cache third-party map tiles. */
const CACHE = 'purif-field-20260924-places-anclas';

const PRECACHE = [
  './',
  './index.html',
  './vendor/leaflet.js',
  './vendor/leaflet-heat.js',
  './vendor/leaflet.css',
  './data/colonias.geojson',
  './data/compet.geojson',
  './data/anclas.geojson',
  './data/retail.geojson',
  './data/muni.geojson',
  './data/field_adds.geojson',
  './data/liked_zones.geojson',
  './data/places_anclas_zmm.geojson',
  './sw.js'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE)
      .then((cache) => cache.addAll(PRECACHE))
      .then(() => self.skipWaiting())
      .catch(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});

function isHTML(url) {
  const p = url.pathname;
  return p.endsWith('/') || p.endsWith('/index.html') || /\/mapa-purificadoras\/?$/.test(p);
}

function isFieldAsset(url) {
  const p = url.pathname;
  return /\/(vendor|data)\//.test(p) || /\.(geojson|js|css)$/.test(p);
}

self.addEventListener('fetch', (event) => {
  const req = event.request;
  if (req.method !== 'GET') return;
  let url;
  try { url = new URL(req.url); } catch (e) { return; }
  if (url.origin !== self.location.origin) return;

  if (isHTML(url)) {
    event.respondWith(
      fetch(req).then((res) => {
        const copy = res.clone();
        caches.open(CACHE).then((c) => c.put(req, copy)).catch(() => {});
        return res;
      }).catch(() =>
        caches.match(req).then((m) => m || caches.match('./index.html') || caches.match('./'))
      )
    );
    return;
  }

  if (isFieldAsset(url)) {
    event.respondWith((async () => {
      const cache = await caches.open(CACHE);
      const cached = await cache.match(req, { ignoreSearch: true });
      const network = fetch(req).then((res) => {
        if (res && res.ok) cache.put(req, res.clone()).catch(() => {});
        return res;
      }).catch(() => cached);
      return cached || network;
    })());
  }
});
