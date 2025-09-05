// 로또프로 AI v2.0 Service Worker - 최소 기능
const CACHE_NAME = 'lottopro-ai-v2-cache-v1';
const urlsToCache = [
  '/',
  '/static/css/style.css',
  '/static/js/main.js'
];

// 설치 이벤트
self.addEventListener('install', event => {
  console.log('🔧 Service Worker 설치 중...');
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('📦 캐시 열기 성공');
        return cache.addAll(urlsToCache);
      })
      .catch(error => {
        console.log('⚠️ 캐시 설정 실패:', error);
      })
  );
});

// 활성화 이벤트
self.addEventListener('activate', event => {
  console.log('✅ Service Worker 활성화');
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (cacheName !== CACHE_NAME) {
            console.log('🗑️ 이전 캐시 삭제:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
});

// 네트워크 요청 처리
self.addEventListener('fetch', event => {
  // API 요청은 캐시하지 않음
  if (event.request.url.includes('/api/')) {
    return;
  }
  
  event.respondWith(
    caches.match(event.request)
      .then(response => {
        // 캐시에서 찾으면 반환, 없으면 네트워크 요청
        return response || fetch(event.request);
      })
      .catch(error => {
        console.log('📡 네트워크 요청 실패:', error);
      })
  );
});
