// Offline shell only. Ledger data (/api/*) is NEVER cached on the device, so a
// locked or shared phone does not leak balances through Cache Storage.
const CACHE = "bolo-khata-v3";
const SHELL = [
  "/", "/static/styles.css", "/static/app.js", "/static/icons/icon.svg", "/manifest.webmanifest",
  "/static/fonts/mukta-devanagari-400-normal.woff2", "/static/fonts/mukta-devanagari-600-normal.woff2",
  "/static/fonts/mukta-devanagari-800-normal.woff2", "/static/fonts/mukta-latin-400-normal.woff2",
  "/static/fonts/mukta-latin-600-normal.woff2", "/static/fonts/mukta-latin-800-normal.woff2",
];
self.addEventListener("install", (e) => e.waitUntil(caches.open(CACHE).then((c) => c.addAll(SHELL)).then(() => self.skipWaiting())));
self.addEventListener("activate", (e) => e.waitUntil(
  caches.keys().then((ks) => Promise.all(ks.filter((k) => k !== CACHE).map((k) => caches.delete(k)))).then(() => self.clients.claim())));
self.addEventListener("fetch", (e) => {
  const url = new URL(e.request.url);
  if (e.request.method !== "GET" || url.origin !== location.origin) return;
  if (url.pathname.startsWith("/api/")) return; // network only
  // stale-while-revalidate for the app shell
  e.respondWith(caches.open(CACHE).then(async (c) => {
    const hit = await c.match(e.request);
    const net = fetch(e.request).then((r) => { if (r.ok) c.put(e.request, r.clone()); return r; }).catch(() => hit);
    return hit || net;
  }));
});
