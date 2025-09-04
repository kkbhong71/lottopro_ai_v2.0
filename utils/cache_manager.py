"""
LottoPro-AI 고급 캐시 관리 시스템
Redis + 메모리 캐시 하이브리드 구조
"""

import time
import json
import hashlib
import threading
import logging
from typing import Any, Dict, List, Optional, Union, Set, Callable
from datetime import datetime, timedelta
from collections import defaultdict
from functools import wraps
import uuid
import pickle

# Redis 연결 시도 (옵션)
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

class CacheStats:
    """캐시 통계 클래스"""
    
    def __init__(self):
        self.hit_count = 0
        self.miss_count = 0
        self.set_count = 0
        self.delete_count = 0
        self.eviction_count = 0
        self.start_time = datetime.now()
        self.reset()

    def reset(self):
        """통계 리셋"""
        self.hit_count = 0
        self.miss_count = 0
        self.set_count = 0
        self.delete_count = 0
        self.eviction_count = 0

    @property
    def hit_rate(self) -> float:
        """히트율 계산"""
        total = self.hit_count + self.miss_count
        return (self.hit_count / total * 100) if total > 0 else 0

    @property
    def total_operations(self) -> int:
        """총 연산 수"""
        return self.hit_count + self.miss_count + self.set_count + self.delete_count

class MemoryCache:
    """메모리 기반 캐시 (Redis 백업용)"""
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.data = {}
        self.expiry_times = {}
        self.access_times = {}
        self.tags = defaultdict(set)
        self.lock = threading.RLock()
        
    def _cleanup_expired(self):
        """만료된 항목 정리"""
        current_time = time.time()
        expired_keys = []
        
        for key, expiry_time in self.expiry_times.items():
            if expiry_time <= current_time:
                expired_keys.append(key)
        
        for key in expired_keys:
            self._remove_key(key)
    
    def _remove_key(self, key: str):
        """키 제거 (내부 사용)"""
        if key in self.data:
            del self.data[key]
        if key in self.expiry_times:
            del self.expiry_times[key]
        if key in self.access_times:
            del self.access_times[key]
        
        # 태그에서도 제거
        for tag_keys in self.tags.values():
            tag_keys.discard(key)
    
    def _evict_if_needed(self):
        """LRU 방식으로 공간 확보"""
        if len(self.data) >= self.max_size:
            # 가장 오래된 항목 찾기
            oldest_key = min(self.access_times.keys(), 
                           key=lambda k: self.access_times[k])
            self._remove_key(oldest_key)
    
    def get(self, key: str) -> Optional[Any]:
        """값 조회"""
        with self.lock:
            self._cleanup_expired()
            
            if key not in self.data:
                return None
            
            # 액세스 시간 업데이트
            self.access_times[key] = time.time()
            return self.data[key]
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None, 
            tags: Optional[List[str]] = None):
        """값 저장"""
        with self.lock:
            self._cleanup_expired()
            self._evict_if_needed()
            
            # 데이터 저장
            self.data[key] = value
            self.access_times[key] = time.time()
            
            # TTL 설정
            if ttl is None:
                ttl = self.default_ttl
            self.expiry_times[key] = time.time() + ttl
            
            # 태그 설정
            if tags:
                for tag in tags:
                    self.tags[tag].add(key)
    
    def delete(self, key: str) -> bool:
        """키 삭제"""
        with self.lock:
            if key in self.data:
                self._remove_key(key)
                return True
            return False
    
    def clear(self, pattern: str = '*') -> int:
        """패턴 매칭으로 삭제"""
        with self.lock:
            if pattern == '*':
                count = len(self.data)
                self.data.clear()
                self.expiry_times.clear()
                self.access_times.clear()
                self.tags.clear()
                return count
            
            # 간단한 패턴 매칭 (와일드카드 지원)
            import fnmatch
            matching_keys = [key for key in self.data.keys() 
                           if fnmatch.fnmatch(key, pattern)]
            
            for key in matching_keys:
                self._remove_key(key)
            
            return len(matching_keys)
    
    def invalidate_by_tags(self, tags: List[str]) -> int:
        """태그별 무효화"""
        with self.lock:
            keys_to_remove = set()
            
            for tag in tags:
                if tag in self.tags:
                    keys_to_remove.update(self.tags[tag])
            
            for key in keys_to_remove:
                self._remove_key(key)
            
            return len(keys_to_remove)
    
    def get_stats(self) -> Dict:
        """캐시 상태 통계"""
        with self.lock:
            self._cleanup_expired()
            return {
                'total_keys': len(self.data),
                'max_size': self.max_size,
                'memory_usage_percent': (len(self.data) / self.max_size) * 100,
                'total_tags': len(self.tags)
            }

class CacheManager:
    """통합 캐시 관리자"""
    
    def __init__(self, redis_url: Optional[str] = None, 
                 default_ttl: int = 300,
                 memory_cache_size: int = 1000,
                 enable_compression: bool = True):
        
        self.default_ttl = default_ttl
        self.enable_compression = enable_compression
        self.stats = CacheStats()
        self.logger = logging.getLogger(__name__)
        
        # Redis 연결 시도
        self.redis_client = None
        if REDIS_AVAILABLE and redis_url:
            try:
                self.redis_client = redis.from_url(
                    redis_url, 
                    decode_responses=False,  # bytes로 받아서 pickle 처리
                    socket_timeout=5,
                    socket_connect_timeout=5,
                    retry_on_timeout=True
                )
                # 연결 테스트
                self.redis_client.ping()
                self.logger.info("Redis cache connected successfully")
            except Exception as e:
                self.logger.warning(f"Redis connection failed: {e}, using memory cache only")
                self.redis_client = None
        
        # 메모리 캐시 (백업 또는 메인)
        self.memory_cache = MemoryCache(memory_cache_size, default_ttl)
        
        # 캐시 레이어 결정
        self.use_redis = self.redis_client is not None
        self.logger.info(f"Cache layers: Redis={self.use_redis}, Memory=True")
    
    def _serialize_value(self, value: Any) -> bytes:
        """값 직렬화"""
        try:
            if self.enable_compression:
                import zlib
                data = pickle.dumps(value)
                return zlib.compress(data)
            else:
                return pickle.dumps(value)
        except Exception as e:
            self.logger.error(f"Serialization error: {e}")
            raise
    
    def _deserialize_value(self, data: bytes) -> Any:
        """값 역직렬화"""
        try:
            if self.enable_compression:
                import zlib
                decompressed = zlib.decompress(data)
                return pickle.loads(decompressed)
            else:
                return pickle.loads(data)
        except Exception as e:
            self.logger.error(f"Deserialization error: {e}")
            raise
    
    def get(self, key: str) -> Optional[Any]:
        """값 조회 (계층적 캐시)"""
        try:
            # Redis에서 먼저 조회
            if self.use_redis:
                try:
                    data = self.redis_client.get(key)
                    if data is not None:
                        self.stats.hit_count += 1
                        # 메모리 캐시에도 복사 (다음 조회 속도 향상)
                        value = self._deserialize_value(data)
                        self.memory_cache.set(key, value, ttl=self.default_ttl)
                        return value
                except Exception as e:
                    self.logger.warning(f"Redis get error for key {key}: {e}")
            
            # 메모리 캐시에서 조회
            value = self.memory_cache.get(key)
            if value is not None:
                self.stats.hit_count += 1
                return value
            
            # 캐시 미스
            self.stats.miss_count += 1
            return None
            
        except Exception as e:
            self.logger.error(f"Cache get error for key {key}: {e}")
            self.stats.miss_count += 1
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None, 
            tags: Optional[List[str]] = None) -> bool:
        """값 저장"""
        try:
            if ttl is None:
                ttl = self.default_ttl
            
            # Redis에 저장
            if self.use_redis:
                try:
                    serialized_value = self._serialize_value(value)
                    self.redis_client.setex(key, ttl, serialized_value)
                    
                    # 태그 저장 (Redis set으로)
                    if tags:
                        for tag in tags:
                            tag_key = f"tag:{tag}"
                            self.redis_client.sadd(tag_key, key)
                            self.redis_client.expire(tag_key, ttl + 3600)  # 태그는 더 오래 유지
                            
                except Exception as e:
                    self.logger.warning(f"Redis set error for key {key}: {e}")
            
            # 메모리 캐시에 저장
            self.memory_cache.set(key, value, ttl, tags)
            
            self.stats.set_count += 1
            return True
            
        except Exception as e:
            self.logger.error(f"Cache set error for key {key}: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """키 삭제"""
        success = True
        
        try:
            # Redis에서 삭제
            if self.use_redis:
                try:
                    self.redis_client.delete(key)
                except Exception as e:
                    self.logger.warning(f"Redis delete error for key {key}: {e}")
                    success = False
            
            # 메모리 캐시에서 삭제
            memory_result = self.memory_cache.delete(key)
            
            if success or memory_result:
                self.stats.delete_count += 1
            
            return success or memory_result
            
        except Exception as e:
            self.logger.error(f"Cache delete error for key {key}: {e}")
            return False
    
    def clear(self, pattern: str = '*') -> int:
        """패턴으로 캐시 클리어"""
        total_cleared = 0
        
        try:
            # Redis 클리어
            if self.use_redis:
                try:
                    if pattern == '*':
                        keys = self.redis_client.keys('*')
                        if keys:
                            total_cleared += self.redis_client.delete(*keys)
                    else:
                        keys = self.redis_client.keys(pattern)
                        if keys:
                            total_cleared += self.redis_client.delete(*keys)
                except Exception as e:
                    self.logger.warning(f"Redis clear error: {e}")
            
            # 메모리 캐시 클리어
            memory_cleared = self.memory_cache.clear(pattern)
            total_cleared += memory_cleared
            
            return total_cleared
            
        except Exception as e:
            self.logger.error(f"Cache clear error: {e}")
            return 0
    
    def invalidate_by_tags(self, tags: List[str]) -> int:
        """태그별 무효화"""
        total_invalidated = 0
        
        try:
            # Redis 태그 무효화
            if self.use_redis:
                try:
                    all_keys = set()
                    for tag in tags:
                        tag_key = f"tag:{tag}"
                        keys = self.redis_client.smembers(tag_key)
                        all_keys.update(keys)
                        self.redis_client.delete(tag_key)  # 태그 키도 삭제
                    
                    if all_keys:
                        # bytes를 문자열로 변환
                        str_keys = [k.decode('utf-8') if isinstance(k, bytes) else k for k in all_keys]
                        total_invalidated += self.redis_client.delete(*str_keys)
                        
                except Exception as e:
                    self.logger.warning(f"Redis tag invalidation error: {e}")
            
            # 메모리 캐시 태그 무효화
            memory_invalidated = self.memory_cache.invalidate_by_tags(tags)
            total_invalidated += memory_invalidated
            
            return total_invalidated
            
        except Exception as e:
            self.logger.error(f"Tag invalidation error: {e}")
            return 0
    
    def health_check(self) -> Dict:
        """캐시 시스템 건강 상태 확인"""
        health_status = {
            'overall_health': True,
            'redis_available': False,
            'memory_cache_available': True,
            'redis_connection_ok': False,
            'memory_cache_stats': {},
            'errors': []
        }
        
        try:
            # Redis 상태 확인
            if self.use_redis:
                try:
                    self.redis_client.ping()
                    health_status['redis_available'] = True
                    health_status['redis_connection_ok'] = True
                    
                    # Redis 정보 수집
                    redis_info = self.redis_client.info('memory')
                    health_status['redis_memory_usage'] = redis_info.get('used_memory', 0)
                    health_status['redis_memory_human'] = redis_info.get('used_memory_human', '0B')
                    
                except Exception as e:
                    health_status['errors'].append(f"Redis health check failed: {e}")
                    health_status['overall_health'] = False
            
            # 메모리 캐시 상태 확인
            try:
                memory_stats = self.memory_cache.get_stats()
                health_status['memory_cache_stats'] = memory_stats
                
                # 메모리 사용률이 95% 이상이면 경고
                if memory_stats['memory_usage_percent'] > 95:
                    health_status['errors'].append("Memory cache usage too high")
                    health_status['overall_health'] = False
                    
            except Exception as e:
                health_status['errors'].append(f"Memory cache health check failed: {e}")
                health_status['overall_health'] = False
            
            return health_status
            
        except Exception as e:
            health_status['errors'].append(f"General health check error: {e}")
            health_status['overall_health'] = False
            return health_status
    
    def get_cache_info(self) -> Dict:
        """캐시 시스템 정보"""
        info = {
            'redis_available': self.use_redis,
            'memory_cache_size': self.memory_cache.max_size,
            'default_ttl': self.default_ttl,
            'compression_enabled': self.enable_compression,
            'stats': {
                'hit_rate': self.stats.hit_rate,
                'hit_count': self.stats.hit_count,
                'miss_count': self.stats.miss_count,
                'set_count': self.stats.set_count,
                'delete_count': self.stats.delete_count,
                'total_operations': self.stats.total_operations
            }
        }
        
        # 메모리 캐시 정보 추가
        memory_stats = self.memory_cache.get_stats()
        info['memory_cache'] = memory_stats
        
        # Redis 정보 추가
        if self.use_redis:
            try:
                redis_info = self.redis_client.info()
                info['redis_info'] = {
                    'version': redis_info.get('redis_version'),
                    'connected_clients': redis_info.get('connected_clients'),
                    'used_memory': redis_info.get('used_memory_human'),
                    'keyspace_hits': redis_info.get('keyspace_hits', 0),
                    'keyspace_misses': redis_info.get('keyspace_misses', 0)
                }
            except Exception:
                info['redis_info'] = {'status': 'unavailable'}
        
        return info
    
    # 특화된 캐시 메소드들 (로또 앱 전용)
    def cache_prediction(self, user_numbers: List[int], model_type: str, 
                        result: List[int], ttl: int = 300):
        """예측 결과 캐시"""
        cache_key = self._generate_prediction_key(user_numbers, model_type)
        return self.set(cache_key, result, ttl, tags=['predictions', model_type])
    
    def get_cached_prediction(self, user_numbers: List[int], 
                             model_type: str) -> Optional[List[int]]:
        """캐시된 예측 결과 조회"""
        cache_key = self._generate_prediction_key(user_numbers, model_type)
        return self.get(cache_key)
    
    def cache_statistics(self, stat_type: str, data: Dict, ttl: int = 600):
        """통계 데이터 캐시"""
        cache_key = f"stats:{stat_type}"
        return self.set(cache_key, data, ttl, tags=['statistics'])
    
    def get_cached_statistics(self, stat_type: str) -> Optional[Dict]:
        """캐시된 통계 데이터 조회"""
        cache_key = f"stats:{stat_type}"
        return self.get(cache_key)
    
    def cache_user_numbers(self, user_id: str, numbers_data: List[Dict], ttl: int = 3600):
        """사용자 저장 번호 캐시"""
        cache_key = f"user_numbers:{user_id}"
        return self.set(cache_key, numbers_data, ttl, tags=['user_data'])
    
    def get_cached_user_numbers(self, user_id: str) -> Optional[List[Dict]]:
        """캐시된 사용자 번호 조회"""
        cache_key = f"user_numbers:{user_id}"
        return self.get(cache_key)
    
    def _generate_prediction_key(self, user_numbers: List[int], model_type: str) -> str:
        """예측 캐시 키 생성"""
        numbers_str = ','.join(map(str, sorted(user_numbers)))
        key_string = f"prediction:{model_type}:{numbers_str}"
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def warm_cache(self, warming_functions: List[Callable]) -> Dict:
        """캐시 워밍 (시작 시 자주 사용되는 데이터 미리 로드)"""
        results = {}
        
        for func in warming_functions:
            try:
                func_name = func.__name__ if hasattr(func, '__name__') else str(func)
                start_time = time.time()
                
                success = func()
                
                results[func_name] = {
                    'success': success,
                    'execution_time': time.time() - start_time,
                    'timestamp': datetime.now().isoformat()
                }
                
                self.logger.info(f"Cache warming for {func_name}: {'Success' if success else 'Failed'}")
                
            except Exception as e:
                results[func_name] = {
                    'success': False,
                    'error': str(e),
                    'execution_time': time.time() - start_time if 'start_time' in locals() else 0,
                    'timestamp': datetime.now().isoformat()
                }
                self.logger.error(f"Cache warming error for {func_name}: {e}")
        
        return results

# 캐시 데코레이터
def cached(ttl: int = 300, tags: Optional[List[str]] = None):
    """캐시 데코레이터"""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            try:
                # Flask 앱에서 캐시 매니저 가져오기
                from flask import current_app
                if not (hasattr(current_app, 'extensions') and 'cache_manager' in current_app.extensions):
                    # 캐시 매니저가 없으면 원본 함수 실행
                    return f(*args, **kwargs)
                
                cache_manager = current_app.extensions['cache_manager']
                
                # 캐시 키 생성 (함수명 + 인수들 해시)
                func_name = f.__name__
                args_str = json.dumps(args, sort_keys=True, default=str)
                kwargs_str = json.dumps(kwargs, sort_keys=True, default=str)
                cache_key = f"func:{func_name}:{hashlib.md5((args_str + kwargs_str).encode()).hexdigest()}"
                
                # 캐시에서 조회
                cached_result = cache_manager.get(cache_key)
                if cached_result is not None:
                    return cached_result
                
                # 캐시 미스 - 함수 실행
                result = f(*args, **kwargs)
                
                # 결과를 캐시에 저장
                cache_manager.set(cache_key, result, ttl, tags)
                
                return result
                
            except Exception:
                # 캐시 에러 시 원본 함수 실행
                return f(*args, **kwargs)
        
        return wrapper
    return decorator

def init_cache_system(app=None, redis_url: Optional[str] = None, 
                     default_ttl: int = 300, **kwargs) -> CacheManager:
    """캐시 시스템 초기화"""
    cache_manager = CacheManager(
        redis_url=redis_url,
        default_ttl=default_ttl,
        **kwargs
    )
    
    if app:
        # Flask 앱에 캐시 매니저 등록
        if not hasattr(app, 'extensions'):
            app.extensions = {}
        app.extensions['cache_manager'] = cache_manager
    
    return cache_manager
