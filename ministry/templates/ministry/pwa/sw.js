{% load static %}// 인투처치 서비스 워커
// - 한 번 열어본 화면은 저장해 두었다가 오프라인일 때 보여줍니다.
// - 리뷰 등록(POST), 관리자 페이지, "더 보기"(HTMX) 요청은 저장하지 않습니다.
// - 배포할 때마다 CACHE_VERSION이 바뀌어 예전 캐시는 자동으로 지워집니다.
const CACHE_VERSION = '{{ cache_version|escapejs }}';
const PRECACHE = `intochurch-precache-${CACHE_VERSION}`;
const PAGES = `intochurch-pages-${CACHE_VERSION}`;
const ASSETS = `intochurch-assets-${CACHE_VERSION}`;
const OFFLINE_URL = '{% url "offline" %}';
const STATIC_PREFIX = '{% get_static_prefix %}';

const PRECACHE_URLS = [
  OFFLINE_URL,
  '{% static "css/output.css" %}',
  '{% static "vendor/alpine.min.js" %}',
  '{% static "vendor/htmx.min.js" %}',
  '{% static "vendor/chart.umd.min.js" %}',
  '{% static "icons/favicon-32.png" %}',
  '{% static "icons/apple-touch-icon.png" %}',
  '{% static "icons/icon-192.png" %}',
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(PRECACHE)
      .then((cache) => cache.addAll(PRECACHE_URLS))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (event) => {
  const keep = [PRECACHE, PAGES, ASSETS];
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(
        keys.filter((key) => key.startsWith('intochurch-') && !keep.includes(key)).map((key) => caches.delete(key))
      ))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  const { request } = event;
  if (request.method !== 'GET') return;

  const url = new URL(request.url);

  if (url.origin === self.location.origin) {
    if (url.pathname.startsWith('/admin/')) return;
    if (request.headers.get('HX-Request')) return;

    if (request.mode === 'navigate') {
      event.respondWith(networkFirstPage(request));
    } else if (url.pathname.startsWith(STATIC_PREFIX)) {
      event.respondWith(staleWhileRevalidate(event));
    }
    return;
  }

  // Pretendard 폰트는 바뀌지 않으므로 한 번 받으면 저장해 둔 것을 씁니다.
  if (url.hostname === 'cdn.jsdelivr.net' && url.pathname.includes('/pretendard')) {
    event.respondWith(cacheFirst(request));
  }
});

// 화면(페이지): 인터넷 먼저 → 안 되면 저장해 둔 화면 → 그것도 없으면 오프라인 안내 화면
async function networkFirstPage(request) {
  const cache = await caches.open(PAGES);
  try {
    const response = await fetch(request);
    if (response.ok) cache.put(request, response.clone());
    return response;
  } catch (err) {
    const cached = await cache.match(request, { ignoreVary: true });
    return cached || (await caches.match(OFFLINE_URL)) || Response.error();
  }
}

// CSS/JS/이미지: 저장해 둔 것을 바로 보여주고, 뒤에서 새 버전을 받아 둡니다.
async function staleWhileRevalidate(event) {
  const { request } = event;
  const cache = await caches.open(ASSETS);
  const cached = await caches.match(request);
  const network = fetch(request)
    .then((response) => {
      if (response.ok) cache.put(request, response.clone());
      return response;
    })
    .catch(() => cached || Response.error());

  if (cached) {
    event.waitUntil(network);
    return cached;
  }
  return network;
}

async function cacheFirst(request) {
  const cached = await caches.match(request);
  if (cached) return cached;
  try {
    const response = await fetch(request);
    if (response.ok) {
      const cache = await caches.open(ASSETS);
      cache.put(request, response.clone());
    }
    return response;
  } catch (err) {
    return Response.error();
  }
}
