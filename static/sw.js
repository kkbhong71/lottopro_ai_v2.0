// LottoPro AI v2.0 Service Worker
// 오프라인 지원, 캐싱, 백그라운드 업데이트 등을 제공

const CACHE_NAME = 'lottopro-ai-v2.0.0';
const STATIC_CACHE = `${CACHE_NAME}-static`;
const DYNAMIC_CACHE = `${CACHE_NAME}-dynamic`;
const API_CACHE = `${CACHE_NAME}-api`;

// 캐시할 정적 파일들
const STATIC_FILES = [
    '/',
    '/static/css/style.css',
    '/static/js/app.js',
    '/static/manifest.json',
    '/static/images/icon-192x192.png',
    '/static/images/icon-512x512.png',
    'https://cdnjs.cloudflare.com/ajax/libs/bootstrap/5.3.0/css/bootstrap.min.css',
    'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css',
    'https://cdnjs.cloudflare.com/ajax/libs/bootstrap/5.3.0/js/bootstrap.bundle.min.js',
    'https://cdnjs.cloudflare.com/ajax/libs/animate.css/4.1.1/animate.min.css'
];

// API 엔드포인트들
const API_ENDPOINTS = [
    '/api/stats',
    '/api/example-numbers',
    '/api/health',
    '/api/saved-numbers'
];

// 캐시 전략 설정
const CACHE_STRATEGIES = {
    // 정적 파일: 캐시 우선 (Cache First)
    static: 'cache-first',
    // API 호출: 네트워크 우선 (Network First)  
    api: 'network-first',
    // 동적 콘텐츠: 스테일 상태로 재검증 (Stale While Revalidate)
    dynamic: 'stale-while-revalidate'
};

// 서비스 워커 설치
self.addEventListener('install', event => {
    console.log('[SW] 서비스 워커 설치 중...');
    
    event.waitUntil(
        Promise.all([
            // 정적 파일 캐시
            caches.open(STATIC_CACHE).then(cache => {
                console.log('[SW] 정적 파일 캐싱 중...');
                return cache.addAll(STATIC_FILES);
            }),
            // API 캐시 초기화
            caches.open(API_CACHE).then(cache => {
                console.log('[SW] API 캐시 초기화 완료');
                return Promise.resolve();
            })
        ]).then(() => {
            console.log('[SW] 모든 파일 캐싱 완료');
            return self.skipWaiting(); // 즉시 활성화
        }).catch(error => {
            console.error('[SW] 캐싱 실패:', error);
        })
    );
});

// 서비스 워커 활성화
self.addEventListener('activate', event => {
    console.log('[SW] 서비스 워커 활성화 중...');
    
    event.waitUntil(
        Promise.all([
            // 이전 캐시 정리
            cleanupOldCaches(),
            // 클라이언트 제어 시작
            self.clients.claim()
        ]).then(() => {
            console.log('[SW] 서비스 워커 활성화 완료');
        })
    );
});

// 네트워크 요청 가로채기
self.addEventListener('fetch', event => {
    const { request } = event;
    const url = new URL(request.url);
    
    // Chrome extension, devtools 등 제외
    if (!url.protocol.startsWith('http')) {
        return;
    }
    
    // POST 요청은 캐시하지 않음
    if (request.method !== 'GET') {
        return;
    }
    
    event.respondWith(handleRequest(request));
});

// 백그라운드 동기화
self.addEventListener('sync', event => {
    console.log('[SW] 백그라운드 동기화:', event.tag);
    
    if (event.tag === 'update-lottery-data') {
        event.waitUntil(updateLotteryData());
    } else if (event.tag === 'sync-saved-numbers') {
        event.waitUntil(syncSavedNumbers());
    }
});

// 푸시 알림 처리
self.addEventListener('push', event => {
    console.log('[SW] 푸시 메시지 수신:', event);
    
    if (event.data) {
        const data = event.data.json();
        const options = {
            body: data.body || '새로운 로또 정보가 업데이트되었습니다.',
            icon: '/static/images/icon-192x192.png',
            badge: '/static/images/badge-72x72.png',
            tag: data.tag || 'lottopro-notification',
            data: data.data || {},
            actions: [
                {
                    action: 'view',
                    title: '확인하기',
                    icon: '/static/images/action-view.png'
                },
                {
                    action: 'dismiss',
                    title: '닫기',
                    icon: '/static/images/action-close.png'
                }
            ],
            requireInteraction: false,
            silent: false
        };
        
        event.waitUntil(
            self.registration.showNotification(data.title || 'LottoPro AI', options)
        );
    }
});

// 알림 클릭 처리
self.addEventListener('notificationclick', event => {
    console.log('[SW] 알림 클릭:', event);
    
    event.notification.close();
    
    if (event.action === 'view') {
        // 앱 열기
        event.waitUntil(
            clients.openWindow('/')
        );
    } else if (event.action === 'dismiss') {
        // 알림만 닫기
        return;
    } else {
        // 기본 클릭 - 앱 열기
        event.waitUntil(
            clients.openWindow('/')
        );
    }
});

// 메시지 처리 (클라이언트와 통신)
self.addEventListener('message', event => {
    console.log('[SW] 메시지 수신:', event.data);
    
    const { type, payload } = event.data;
    
    switch (type) {
        case 'SKIP_WAITING':
            self.skipWaiting();
            break;
            
        case 'GET_VERSION':
            event.ports[0].postMessage({
                type: 'VERSION_INFO',
                version: CACHE_NAME
            });
            break;
            
        case 'CLEAR_CACHE':
            clearAllCaches().then(() => {
                event.ports[0].postMessage({
                    type: 'CACHE_CLEARED',
                    success: true
                });
            });
            break;
            
        case 'SYNC_DATA':
            event.waitUntil(syncData(payload));
            break;
            
        default:
            console.log('[SW] 알 수 없는 메시지 타입:', type);
    }
});

// === 유틸리티 함수들 ===

// 요청 처리 메인 함수
async function handleRequest(request) {
    const url = new URL(request.url);
    
    try {
        // API 요청 처리
        if (url.pathname.startsWith('/api/')) {
            return await handleApiRequest(request);
        }
        
        // 정적 파일 처리
        if (isStaticFile(url.pathname)) {
            return await handleStaticRequest(request);
        }
        
        // 동적 콘텐츠 처리
        return await handleDynamicRequest(request);
        
    } catch (error) {
        console.error('[SW] 요청 처리 실패:', error);
        return await getOfflineFallback(request);
    }
}

// API 요청 처리 (Network First)
async function handleApiRequest(request) {
    const cache = await caches.open(API_CACHE);
    
    try {
        // 네트워크 우선 시도
        const networkResponse = await fetch(request);
        
        if (networkResponse.ok) {
            // 성공 시 캐시 업데이트
            cache.put(request, networkResponse.clone());
            return networkResponse;
        }
        
        throw new Error(`API 응답 오류: ${networkResponse.status}`);
        
    } catch (error) {
        console.log('[SW] 네트워크 실패, 캐시에서 응답:', error.message);
        
        // 네트워크 실패 시 캐시에서 응답
        const cachedResponse = await cache.match(request);
        if (cachedResponse) {
            return cachedResponse;
        }
        
        // 캐시도 없으면 오프라인 응답
        return getOfflineApiResponse(request);
    }
}

// 정적 파일 처리 (Cache First)
async function handleStaticRequest(request) {
    const cache = await caches.open(STATIC_CACHE);
    
    // 캐시 우선 확인
    const cachedResponse = await cache.match(request);
    if (cachedResponse) {
        return cachedResponse;
    }
    
    try {
        // 캐시에 없으면 네트워크에서 가져와서 캐시
        const networkResponse = await fetch(request);
        
        if (networkResponse.ok) {
            cache.put(request, networkResponse.clone());
        }
        
        return networkResponse;
        
    } catch (error) {
        console.error('[SW] 정적 파일 로드 실패:', error);
        return getOfflineFallback(request);
    }
}

// 동적 콘텐츠 처리 (Stale While Revalidate)
async function handleDynamicRequest(request) {
    const cache = await caches.open(DYNAMIC_CACHE);
    
    // 캐시된 응답 즉시 반환
    const cachedResponse = await cache.match(request);
    
    // 백그라운드에서 업데이트
    const networkUpdate = fetch(request).then(response => {
        if (response.ok) {
            cache.put(request, response.clone());
        }
        return response;
    }).catch(error => {
        console.log('[SW] 동적 콘텐츠 업데이트 실패:', error);
    });
    
    // 캐시가 있으면 즉시 반환, 없으면 네트워크 기다림
    return cachedResponse || networkUpdate || getOfflineFallback(request);
}

// 파일이 정적 파일인지 확인
function isStaticFile(pathname) {
    const staticExtensions = ['.css', '.js', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.woff', '.woff2'];
    return staticExtensions.some(ext => pathname.endsWith(ext)) || 
           pathname.startsWith('/static/');
}

// 이전 캐시 정리
async function cleanupOldCaches() {
    const cacheNames = await caches.keys();
    const oldCaches = cacheNames.filter(name => 
        name.startsWith('lottopro-ai-') && !name.includes('v2.0.0')
    );
    
    return Promise.all(
        oldCaches.map(name => {
            console.log('[SW] 이전 캐시 삭제:', name);
            return caches.delete(name);
        })
    );
}

// 모든 캐시 정리
async function clearAllCaches() {
    const cacheNames = await caches.keys();
    return Promise.all(
        cacheNames.map(name => caches.delete(name))
    );
}

// 오프라인 폴백 응답
async function getOfflineFallback(request) {
    const url = new URL(request.url);
    
    // HTML 페이지 요청 시 오프라인 페이지
    if (request.headers.get('accept').includes('text/html')) {
        return new Response(`
            <!DOCTYPE html>
            <html lang="ko">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>오프라인 - LottoPro AI</title>
                <style>
                    body {
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                        background: linear-gradient(135deg, #667eea, #764ba2);
                        color: white;
                        text-align: center;
                        padding: 2rem;
                        margin: 0;
                        min-height: 100vh;
                        display: flex;
                        flex-direction: column;
                        justify-content: center;
                        align-items: center;
                    }
                    .offline-container {
                        max-width: 500px;
                        padding: 2rem;
                        background: rgba(255,255,255,0.1);
                        border-radius: 20px;
                        backdrop-filter: blur(10px);
                    }
                    .offline-icon {
                        font-size: 4rem;
                        margin-bottom: 1rem;
                    }
                    .offline-title {
                        font-size: 2rem;
                        margin-bottom: 1rem;
                    }
                    .offline-message {
                        font-size: 1.1rem;
                        margin-bottom: 2rem;
                        opacity: 0.9;
                    }
                    .retry-btn {
                        background: #28a745;
                        color: white;
                        border: none;
                        padding: 1rem 2rem;
                        font-size: 1.1rem;
                        border-radius: 10px;
                        cursor: pointer;
                        transition: all 0.3s ease;
                    }
                    .retry-btn:hover {
                        background: #218838;
                        transform: translateY(-2px);
                    }
                    .cached-features {
                        margin-top: 2rem;
                        text-align: left;
                        background: rgba(255,255,255,0.1);
                        padding: 1rem;
                        border-radius: 10px;
                    }
                    .cached-features h4 {
                        margin-bottom: 1rem;
                        text-align: center;
                    }
                    .cached-features ul {
                        list-style: none;
                        padding: 0;
                    }
                    .cached-features li {
                        padding: 0.5rem 0;
                        border-bottom: 1px solid rgba(255,255,255,0.2);
                    }
                    .cached-features li:last-child {
                        border-bottom: none;
                    }
                    .cached-features li::before {
                        content: '✓ ';
                        color: #28a745;
                        font-weight: bold;
                    }
                </style>
            </head>
            <body>
                <div class="offline-container">
                    <div class="offline-icon">📱</div>
                    <h1 class="offline-title">오프라인 모드</h1>
                    <p class="offline-message">
                        인터넷 연결을 확인할 수 없습니다.<br>
                        일부 기능은 오프라인에서도 사용 가능합니다.
                    </p>
                    <button class="retry-btn" onclick="location.reload()">
                        다시 시도
                    </button>
                    
                    <div class="cached-features">
                        <h4>📋 오프라인 사용 가능한 기능</h4>
                        <ul>
                            <li>저장된 번호 확인</li>
                            <li>기본 통계 정보</li>
                            <li>세금 계산기</li>
                            <li>앱 기본 기능</li>
                        </ul>
                    </div>
                </div>
                
                <script>
                    // 온라인 상태 복구 감지
                    window.addEventListener('online', function() {
                        location.reload();
                    });
                    
                    // 서비스 워커 메시지 수신
                    if ('serviceWorker' in navigator) {
                        navigator.serviceWorker.addEventListener('message', function(event) {
                            if (event.data.type === 'CACHE_UPDATED') {
                                location.reload();
                            }
                        });
                    }
                </script>
            </body>
            </html>
        `, {
            status: 200,
            headers: {
                'Content-Type': 'text/html; charset=utf-8',
                'Cache-Control': 'no-cache'
            }
        });
    }
    
    // 기타 요청에 대한 기본 오프라인 응답
    return new Response('오프라인 상태입니다.', {
        status: 503,
        statusText: 'Service Unavailable',
        headers: {
            'Content-Type': 'text/plain; charset=utf-8'
        }
    });
}

// 오프라인 API 응답
function getOfflineApiResponse(request) {
    const url = new URL(request.url);
    
    // 기본 응답 생성
    const offlineData = {
        success: false,
        error: '오프라인 상태입니다. 인터넷 연결을 확인해주세요.',
        offline: true,
        cached_data: null
    };
    
    // 특정 API에 대한 오프라인 응답
    if (url.pathname === '/api/health') {
        offlineData.status = 'offline';
        offlineData.timestamp = new Date().toISOString();
        offlineData.version = 'v2.0.0';
    } else if (url.pathname === '/api/stats') {
        offlineData.cached_data = {
            hot_numbers: [[7, 15], [13, 14], [22, 13], [31, 12], [42, 11]],
            cold_numbers: [[45, 8], [44, 9], [43, 10], [2, 11], [3, 12]],
            total_draws: 200,
            data_source: '오프라인 캐시'
        };
    }
    
    return new Response(JSON.stringify(offlineData), {
        status: 503,
        headers: {
            'Content-Type': 'application/json; charset=utf-8',
            'Cache-Control': 'no-cache'
        }
    });
}

// 백그라운드 데이터 업데이트
async function updateLotteryData() {
    console.log('[SW] 백그라운드 로또 데이터 업데이트 시작');
    
    try {
        // 최신 통계 정보 가져오기
        const statsResponse = await fetch('/api/stats');
        if (statsResponse.ok) {
            const cache = await caches.open(API_CACHE);
            cache.put('/api/stats', statsResponse.clone());
            console.log('[SW] 통계 데이터 업데이트 완료');
        }
        
        // 클라이언트에게 업데이트 알림
        const clients = await self.clients.matchAll();
        clients.forEach(client => {
            client.postMessage({
                type: 'DATA_UPDATED',
                endpoint: '/api/stats'
            });
        });
        
    } catch (error) {
        console.error('[SW] 백그라운드 업데이트 실패:', error);
    }
}

// 저장된 번호 동기화
async function syncSavedNumbers() {
    console.log('[SW] 저장된 번호 동기화 시작');
    
    try {
        // IndexedDB에서 오프라인 저장된 번호들 가져오기
        // (실제 구현 시 IndexedDB 사용)
        
        // 서버와 동기화
        const response = await fetch('/api/sync-saved-numbers', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                // 동기화할 데이터
            })
        });
        
        if (response.ok) {
            console.log('[SW] 번호 동기화 완료');
        }
        
    } catch (error) {
        console.error('[SW] 번호 동기화 실패:', error);
    }
}

// 데이터 동기화
async function syncData(payload) {
    console.log('[SW] 데이터 동기화:', payload);
    
    try {
        const response = await fetch('/api/sync', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });
        
        if (response.ok) {
            // 관련 캐시 무효화
            const cache = await caches.open(API_CACHE);
            await cache.delete('/api/saved-numbers');
            
            console.log('[SW] 데이터 동기화 완료');
        }
        
    } catch (error) {
        console.error('[SW] 데이터 동기화 실패:', error);
    }
}

// 정기적인 캐시 정리 (24시간마다)
setInterval(() => {
    cleanupOldCaches();
}, 24 * 60 * 60 * 1000);

console.log('[SW] LottoPro AI v2.0 서비스 워커 로드 완료');
