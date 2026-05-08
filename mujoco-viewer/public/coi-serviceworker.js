/* coi-serviceworker v0.1.7 — Guido Zuidhof & contributors, MIT License
 * Adds Cross-Origin-Opener-Policy / Cross-Origin-Embedder-Policy headers via
 * a service worker so SharedArrayBuffer is available on hosts (e.g. GitHub
 * Pages) that cannot set HTTP headers directly. */

if (typeof window === 'undefined') {
  // ── Running as service worker ───────────────────────────────────────────────
  self.addEventListener('install', () => self.skipWaiting())
  self.addEventListener('activate', (e) => e.waitUntil(self.clients.claim()))

  self.addEventListener('fetch', (e) => {
    if (e.request.cache === 'only-if-cached' && e.request.mode !== 'same-origin') return
    e.respondWith(
      fetch(e.request)
        .then((res) => {
          if (res.status === 0) return res
          const headers = new Headers(res.headers)
          headers.set('Cross-Origin-Opener-Policy', 'same-origin')
          headers.set('Cross-Origin-Embedder-Policy', 'require-corp')
          return new Response(res.body, { status: res.status, statusText: res.statusText, headers })
        })
        .catch(() => fetch(e.request))
    )
  })
} else {
  // ── Running in page context ─────────────────────────────────────────────────
  ;(() => {
    if (self.crossOriginIsolated) return   // headers already present, nothing to do
    if (!window.isSecureContext) {
      console.warn('[coi-sw] Not in a secure context — skipping service worker registration.')
      return
    }
    if (!('serviceWorker' in navigator)) {
      console.warn('[coi-sw] Service workers not supported.')
      return
    }

    const reloaded = sessionStorage.getItem('coi-sw-reloaded')

    navigator.serviceWorker
      .register(document.currentScript.src)
      .then((reg) => {
        if (reloaded) return  // already reloaded after install, stop loop

        const activate = () => {
          sessionStorage.setItem('coi-sw-reloaded', '1')
          window.location.reload()
        }

        if (reg.active && navigator.serviceWorker.controller) {
          activate()
        } else {
          const pending = reg.installing || reg.waiting
          if (pending) {
            pending.addEventListener('statechange', (ev) => {
              if (ev.target.state === 'activated') activate()
            })
          }
          // Also handle the case where a controller appears asynchronously
          navigator.serviceWorker.addEventListener('controllerchange', activate)
        }
      })
      .catch((err) => console.warn('[coi-sw] Registration failed:', err))
  })()
}
