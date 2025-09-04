"""
LottoPro AI v2.0 - 고급 캐싱 시스템

이 모듈은 애플리케이션의 성능을 향상시키기 위한 
고급 캐싱 기능을 제공합니다.

주요 기능:
- Redis 기반 분산 캐싱 (fallback to 메모리 캐시)
- AI 예측 결과 지능형 캐싱
- 통계 데이터 캐싱
- TTL 기반 자동 만료
- 캐시 히트/미스 통계
- 압축 및 직렬화
- 캐시 워밍 (예열)
- 패턴 기반 무효화
"""

import redis
import json
import hashlib
import time
import threading
import pickle
import zlib
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Union, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict, OrderedDict
import os
from functools import wraps
import asyncio
from concurrent.futures import ThreadPoolExecutor
import weakref

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class CacheStats:
    """캐시 통계 정보"""
    hits: int = 0
    misses: int = 0
    sets: int = 0
    deletes: int = 0
    errors: int = 0
    total_size_bytes: int = 0
    avg_response_time_ms: float = 0.0
    
    @property
    def hit_rate(self) -> float:
        """캐시 히트율 계산"""
        total = self.hits + self.misses
        return (self.hits / total * 100) if total > 0 else 0.0
    
    @property
    def total_operations(self) -> int:
        """총 연산 수"""
        return self.hits + self.misses + self.sets + self.deletes

@dataclass 
class CacheEntry:
    """캐시 엔트리 정보"""
    key: str
    value: Any
    created_at: float
    expires_at: float
    access_count: int = 0
    last_accessed: float = 0.0
    size_bytes: int = 0
    tags: List[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.last_accessed == 0.0:
            self.last_accessed = self.created_at

class MemoryCache:
    """
    메모리 기반 캐시 구현 (Redis fallback용)
    LRU 방식으로 동작하며 TTL 지원
    """
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 3600):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cache = OrderedDict()
        self.lock = threading.RLock()
        self.stats = CacheStats()
        
        # 백그라운드 정리 스레드
        self.cleanup_thread = threading.Thread(target=self._cleanup_expired, daemon=True)
        self.cleanup_thread.start()
    
    def get(self, key: str) -> Optional[Any]:
        """캐시에서 값 조회"""
        with self.lock:
            if key not in self.cache:
                self.stats.misses += 1
                return None
            
            entry = self.cache[key]
            
            # 만료 확인
            if time.time() > entry.expires_at:
                del self.cache[key]
                self.stats.misses += 1
                return None
            
            # LRU 업데이트
            self.cache.move_to_end(key)
            entry.access_count += 1
            entry.last_accessed = time.time()
            
            self.stats.hits += 1
            return entry.value
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """캐시에 값 저장"""
        try:
            with self.lock:
                ttl = ttl or self.default_ttl
                expires_at = time.time() + ttl
                
                # 값 크기 계산
                size_bytes = len(pickle.dumps(value))
                
                entry = CacheEntry(
                    key=key,
                    value=value,
                    created_at=time.time(),
                    expires_at=expires_at,
                    size_bytes=size_bytes
                )
                
                # 기존 엔트리가 있으면 크기 차감
                if key in self.cache:
                    old_entry = self.cache[key]
                    self.stats.total_size_bytes -= old_entry.size_bytes
                
                self.cache[key] = entry
                self.cache.move_to_end(key)
                
                # 크기 추가
                self.stats.total_size_bytes += size_bytes
                self.stats.sets += 1
                
                # 최대 크기 초과시 LRU 제거
                while len(self.cache) > self.max_size:
                    oldest_key, oldest_entry = self.cache.popitem(last=False)
                    self.stats.total_size_bytes -= oldest_entry.size_bytes
                
                return True
                
        except Exception as e:
            logger.error(f"메모리 캐시 설정 실패 [{key}]: {str(e)}")
            self.stats.errors += 1
            return False
    
    def delete(self, key: str) -> bool:
        """캐시에서 값 삭제"""
        with self.lock:
            if key in self.cache:
                entry = self.cache[key]
                del self.cache[key]
                self.stats.total_size_bytes -= entry.size_bytes
                self.stats.deletes += 1
                return True
            return False
    
    def clear(self):
        """모든 캐시 삭제"""
        with self.lock:
            self.cache.clear()
            self.stats.total_size_bytes = 0
    
    def keys(self, pattern: str = "*") -> List[str]:
        """패턴에 맞는 키 목록 반환"""
        import fnmatch
        with self.lock:
            if pattern == "*":
                return list(self.cache.keys())
            return [key for key in self.cache.keys() if fnmatch.fnmatch(key, pattern)]
    
    def _cleanup_expired(self):
        """만료된 캐시 정리 (백그라운드)"""
        while True:
            try:
                time.sleep(60)  # 1분마다 정리
                current_time = time.time()
                expired_keys = []
                
                with self.lock:
                    for key, entry in self.cache.items():
                        if current_time > entry.expires_at:
                            expired_keys.append(key)
                    
                    for key in expired_keys:
                        if key in self.cache:
                            entry = self.cache[key]
                            del self.cache[key]
                            self.stats.total_size_bytes -= entry.size_bytes
                
                if expired_keys:
                    logger.debug(f"만료된 캐시 {len(expired_keys)}개 정리 완료")
                    
            except Exception as e:
                logger.error(f"캐시 정리 중 오류: {str(e)}")

class CacheManager:
    """
    고급 캐시 관리자
    Redis를 우선 사용하고 사용 불가시 메모리 캐시로 fallback
    """
    
    def __init__(self, 
                 redis_url: Optional[str] = None,
                 default_ttl: int = 3600,
                 key_prefix: str = 'lottopro:',
                 compression_threshold: int = 1024,
                 enable_stats: bool = True):
        """
        캐시 매니저 초기화
        
        Args:
            redis_url: Redis 연결 URL
            default_ttl: 기본 TTL (초)
            key_prefix: 캐시 키 접두사
            compression_threshold: 압축 임계값 (바이트)
            enable_stats: 통계 수집 활성화 여부
        """
        self.default_ttl = default_ttl
        self.key_prefix = key_prefix
        self.compression_threshold = compression_threshold
        self.enable_stats = enable_stats
        
        # Redis 연결 시도
        redis_url = redis_url or os.getenv('REDIS_URL', 'redis://localhost:6379')
        self.redis_client = None
        self.redis_available = False
        
        try:
            self.redis_client = redis.from_url(redis_url, decode_responses=False, 
                                             socket_timeout=5, socket_connect_timeout=5)
            # 연결 테스트
            self.redis_client.ping()
            self.redis_available = True
            logger.info(f"Redis 캐시 연결 성공: {redis_url}")
        except Exception as e:
            logger.warning(f"Redis 연결 실패, 메모리 캐시 사용: {str(e)}")
            
        # 메모리 캐시 (fallback)
        self.memory_cache = MemoryCache(max_size=1000, default_ttl=default_ttl)
        
        # 통계 및 상태
        self.stats = CacheStats()
        self.cache_warming_tasks = set()
        self.invalidation_patterns = defaultdict(set)
        
        # 스레드 풀 (비동기 작업용)
        self.executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="cache")
        
        logger.info(f"캐시 시스템 초기화 완료 (Redis: {self.redis_available})")
    
    def _generate_key(self, key: str) -> str:
        """접두사가 포함된 최종 키 생성"""
        return f"{self.key_prefix}{key}"
    
    def _serialize_value(self, value: Any) -> Tuple[bytes, bool]:
        """값 직렬화 및 압축"""
        try:
            # JSON 직렬화 시도 (더 효율적)
            try:
                serialized = json.dumps(value, ensure_ascii=False, default=str).encode('utf-8')
                is_json = True
            except (TypeError, ValueError):
                # Pickle 직렬화 (복잡한 객체)
                serialized = pickle.dumps(value)
                is_json = False
            
            # 압축 적용 (임계값 이상)
            compressed = False
            if len(serialized) > self.compression_threshold:
                try:
                    compressed_data = zlib.compress(serialized)
                    if len(compressed_data) < len(serialized):  # 압축이 효과적인 경우만
                        serialized = compressed_data
                        compressed = True
                except:
                    pass  # 압축 실패시 원본 사용
            
            # 메타데이터 추가
            metadata = {
                'is_json': is_json,
                'compressed': compressed,
                'timestamp': time.time(),
                'size': len(serialized)
            }
            
            final_data = {
                'metadata': metadata,
                'data': serialized
            }
            
            return pickle.dumps(final_data), compressed
            
        except Exception as e:
            logger.error(f"값 직렬화 실패: {str(e)}")
            raise
    
    def _deserialize_value(self, data: bytes) -> Any:
        """값 역직렬화 및 압축 해제"""
        try:
            # 데이터 구조 복원
            final_data = pickle.loads(data)
            metadata = final_data['metadata']
            serialized = final_data['data']
            
            # 압축 해제
            if metadata.get('compressed', False):
                serialized = zlib.decompress(serialized)
            
            # 역직렬화
            if metadata.get('is_json', False):
                return json.loads(serialized.decode('utf-8'))
            else:
                return pickle.loads(serialized)
                
        except Exception as e:
            logger.error(f"값 역직렬화 실패: {str(e)}")
            raise
    
    def get(self, key: str, default: Any = None) -> Any:
        """캐시에서 값 조회"""
        start_time = time.time()
        final_key = self._generate_key(key)
        
        try:
            if self.redis_available:
                # Redis에서 조회
                data = self.redis_client.get(final_key)
                if data is not None:
                    value = self._deserialize_value(data)
                    self._update_stats('hit', time.time() - start_time)
                    return value
                else:
                    self._update_stats('miss', time.time() - start_time)
                    return default
            else:
                # 메모리 캐시에서 조회
                value = self.memory_cache.get(final_key)
                if value is not None:
                    self._update_stats('hit', time.time() - start_time)
                    return value
                else:
                    self._update_stats('miss', time.time() - start_time)
                    return default
                    
        except Exception as e:
            logger.error(f"캐시 조회 실패 [{key}]: {str(e)}")
            self._update_stats('error', time.time() - start_time)
            return default
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None, 
            tags: Optional[List[str]] = None) -> bool:
        """캐시에 값 저장"""
        start_time = time.time()
        final_key = self._generate_key(key)
        ttl = ttl or self.default_ttl
        
        try:
            if self.redis_available:
                # Redis에 저장
                serialized_data, _ = self._serialize_value(value)
                result = self.redis_client.setex(final_key, ttl, serialized_data)
                
                # 태그 정보 저장
                if tags:
                    self._store_tags(key, tags)
                
                self._update_stats('set', time.time() - start_time)
                return bool(result)
            else:
                # 메모리 캐시에 저장
                result = self.memory_cache.set(final_key, value, ttl)
                
                # 태그 정보 저장 (메모리)
                if tags:
                    for tag in tags:
                        self.invalidation_patterns[tag].add(key)
                
                self._update_stats('set', time.time() - start_time)
                return result
                
        except Exception as e:
            logger.error(f"캐시 저장 실패 [{key}]: {str(e)}")
            self._update_stats('error', time.time() - start_time)
            return False
    
    def delete(self, key: str) -> bool:
        """캐시에서 값 삭제"""
        start_time = time.time()
        final_key = self._generate_key(key)
        
        try:
            if self.redis_available:
                result = self.redis_client.delete(final_key) > 0
            else:
                result = self.memory_cache.delete(final_key)
            
            self._update_stats('delete', time.time() - start_time)
            return result
            
        except Exception as e:
            logger.error(f"캐시 삭제 실패 [{key}]: {str(e)}")
            self._update_stats('error', time.time() - start_time)
            return False
    
    def exists(self, key: str) -> bool:
        """키 존재 여부 확인"""
        final_key = self._generate_key(key)
        
        try:
            if self.redis_available:
                return bool(self.redis_client.exists(final_key))
            else:
                return final_key in self.memory_cache.cache
        except Exception as e:
            logger.error(f"키 존재 확인 실패 [{key}]: {str(e)}")
            return False
    
    def clear(self, pattern: str = "*"):
        """패턴에 맞는 모든 키 삭제"""
        try:
            if pattern == "*":
                # 전체 삭제
                if self.redis_available:
                    pattern_key = self._generate_key("*")
                    keys = self.redis_client.keys(pattern_key)
                    if keys:
                        self.redis_client.delete(*keys)
                else:
                    self.memory_cache.clear()
            else:
                # 패턴 매칭 삭제
                keys = self.keys(pattern)
                for key in keys:
                    self.delete(key)
                    
            logger.info(f"캐시 정리 완료: {pattern}")
            
        except Exception as e:
            logger.error(f"캐시 정리 실패 [{pattern}]: {str(e)}")
    
    def keys(self, pattern: str = "*") -> List[str]:
        """패턴에 맞는 키 목록 반환"""
        try:
            if self.redis_available:
                pattern_key = self._generate_key(pattern)
                redis_keys = self.redis_client.keys(pattern_key)
                # 접두사 제거하여 반환
                return [key.decode('utf-8').replace(self.key_prefix, '', 1) 
                       for key in redis_keys]
            else:
                pattern_key = self._generate_key(pattern)
                memory_keys = self.memory_cache.keys(pattern_key)
                return [key.replace(self.key_prefix, '', 1) for key in memory_keys]
                
        except Exception as e:
            logger.error(f"키 목록 조회 실패 [{pattern}]: {str(e)}")
            return []
    
    def _store_tags(self, key: str, tags: List[str]):
        """태그 정보 저장 (Redis)"""
        try:
            for tag in tags:
                tag_key = self._generate_key(f"tag:{tag}")
                self.redis_client.sadd(tag_key, key)
                self.redis_client.expire(tag_key, self.default_ttl)
        except Exception as e:
            logger.error(f"태그 저장 실패 [{key}]: {str(e)}")
    
    def invalidate_by_tags(self, tags: List[str]) -> int:
        """태그로 캐시 무효화"""
        invalidated_count = 0
        
        try:
            if self.redis_available:
                for tag in tags:
                    tag_key = self._generate_key(f"tag:{tag}")
                    keys_to_invalidate = self.redis_client.smembers(tag_key)
                    
                    for key in keys_to_invalidate:
                        key_str = key.decode('utf-8') if isinstance(key, bytes) else str(key)
                        if self.delete(key_str):
                            invalidated_count += 1
                    
                    # 태그 키도 삭제
                    self.redis_client.delete(tag_key)
            else:
                # 메모리 캐시 태그 처리
                for tag in tags:
                    if tag in self.invalidation_patterns:
                        keys_to_invalidate = list(self.invalidation_patterns[tag])
                        for key in keys_to_invalidate:
                            if self.delete(key):
                                invalidated_count += 1
                        del self.invalidation_patterns[tag]
            
            logger.info(f"태그 기반 캐시 무효화 완료: {tags} ({invalidated_count}개)")
            return invalidated_count
            
        except Exception as e:
            logger.error(f"태그 기반 무효화 실패 {tags}: {str(e)}")
            return 0
    
    def _update_stats(self, operation: str, response_time: float):
        """통계 업데이트"""
        if not self.enable_stats:
            return
        
        response_time_ms = response_time * 1000
        
        if operation == 'hit':
            self.stats.hits += 1
        elif operation == 'miss':
            self.stats.misses += 1
        elif operation == 'set':
            self.stats.sets += 1
        elif operation == 'delete':
            self.stats.deletes += 1
        elif operation == 'error':
            self.stats.errors += 1
        
        # 평균 응답시간 업데이트
        total_ops = self.stats.total_operations
        if total_ops > 0:
            current_avg = self.stats.avg_response_time_ms
            self.stats.avg_response_time_ms = (
                (current_avg * (total_ops - 1) + response_time_ms) / total_ops
            )
    
    # 특화된 캐싱 메서드들
    
    def cache_prediction(self, user_numbers: List[int], model_type: str, 
                        prediction_data: Dict, ttl: int = 300) -> bool:
        """AI 예측 결과 캐싱"""
        try:
            # 예측 키 생성 (사용자 번호와 모델 타입 기반)
            user_hash = hashlib.md5(json.dumps(sorted(user_numbers)).encode()).hexdigest()[:8]
            key = f"prediction:{model_type}:{user_hash}"
            
            # 메타데이터 추가
            cache_data = {
                'user_numbers': user_numbers,
                'model_type': model_type,
                'prediction': prediction_data,
                'cached_at': time.time(),
                'version': '2.0'
            }
            
            tags = ['predictions', f'model:{model_type}']
            return self.set(key, cache_data, ttl=ttl, tags=tags)
            
        except Exception as e:
            logger.error(f"예측 캐싱 실패: {str(e)}")
            return False
    
    def get_cached_prediction(self, user_numbers: List[int], 
                            model_type: str) -> Optional[Dict]:
        """캐시된 AI 예측 조회"""
        try:
            user_hash = hashlib.md5(json.dumps(sorted(user_numbers)).encode()).hexdigest()[:8]
            key = f"prediction:{model_type}:{user_hash}"
            
            cached_data = self.get(key)
            if cached_data and isinstance(cached_data, dict):
                # 캐시된 데이터의 유효성 검사
                if (cached_data.get('user_numbers') == sorted(user_numbers) and
                    cached_data.get('model_type') == model_type):
                    return cached_data.get('prediction')
            
            return None
            
        except Exception as e:
            logger.error(f"예측 캐시 조회 실패: {str(e)}")
            return None
    
    def cache_statistics(self, stats_type: str, stats_data: Dict, ttl: int = 600) -> bool:
        """통계 데이터 캐싱"""
        try:
            key = f"stats:{stats_type}"
            
            cache_data = {
                'type': stats_type,
                'data': stats_data,
                'cached_at': time.time(),
                'version': '2.0'
            }
            
            tags = ['statistics', f'stats:{stats_type}']
            return self.set(key, cache_data, ttl=ttl, tags=tags)
            
        except Exception as e:
            logger.error(f"통계 캐싱 실패: {str(e)}")
            return False
    
    def get_cached_statistics(self, stats_type: str) -> Optional[Dict]:
        """캐시된 통계 데이터 조회"""
        try:
            key = f"stats:{stats_type}"
            cached_data = self.get(key)
            
            if cached_data and isinstance(cached_data, dict):
                return cached_data.get('data')
            
            return None
            
        except Exception as e:
            logger.error(f"통계 캐시 조회 실패: {str(e)}")
            return None
    
    def cache_user_numbers(self, user_id: str, numbers_data: List[Dict], 
                          ttl: int = 86400) -> bool:
        """사용자 저장 번호 캐싱"""
        try:
            key = f"user:numbers:{user_id}"
            
            cache_data = {
                'user_id': user_id,
                'numbers': numbers_data,
                'cached_at': time.time(),
                'count': len(numbers_data)
            }
            
            tags = ['user_data', f'user:{user_id}']
            return self.set(key, cache_data, ttl=ttl, tags=tags)
            
        except Exception as e:
            logger.error(f"사용자 번호 캐싱 실패: {str(e)}")
            return False
    
    def get_cached_user_numbers(self, user_id: str) -> Optional[List[Dict]]:
        """캐시된 사용자 번호 조회"""
        try:
            key = f"user:numbers:{user_id}"
            cached_data = self.get(key)
            
            if cached_data and isinstance(cached_data, dict):
                return cached_data.get('numbers', [])
            
            return None
            
        except Exception as e:
            logger.error(f"사용자 번호 캐시 조회 실패: {str(e)}")
            return None
    
    def warm_cache(self, warming_functions: List[callable], 
                   concurrent: bool = True) -> Dict[str, bool]:
        """캐시 워밍 (예열)"""
        results = {}
        
        try:
            if concurrent and len(warming_functions) > 1:
                # 병렬 처리
                future_to_func = {}
                for func in warming_functions:
                    future = self.executor.submit(self._execute_warming_function, func)
                    future_to_func[future] = func.__name__
                
                for future in future_to_func:
                    func_name = future_to_func[future]
                    try:
                        result = future.result(timeout=30)  # 30초 타임아웃
                        results[func_name] = result
                    except Exception as e:
                        logger.error(f"캐시 워밍 실패 [{func_name}]: {str(e)}")
                        results[func_name] = False
            else:
                # 순차 처리
                for func in warming_functions:
                    func_name = func.__name__
                    try:
                        result = self._execute_warming_function(func)
                        results[func_name] = result
                    except Exception as e:
                        logger.error(f"캐시 워밍 실패 [{func_name}]: {str(e)}")
                        results[func_name] = False
            
            success_count = sum(1 for v in results.values() if v)
            logger.info(f"캐시 워밍 완료: {success_count}/{len(results)} 성공")
            
            return results
            
        except Exception as e:
            logger.error(f"캐시 워밍 중 오류: {str(e)}")
            return {func.__name__: False for func in warming_functions}
    
    def _execute_warming_function(self, func: callable) -> bool:
        """워밍 함수 실행"""
        try:
            result = func()
            return result is not False
        except Exception as e:
            logger.error(f"워밍 함수 실행 실패 [{func.__name__}]: {str(e)}")
            return False
    
    def get_cache_info(self) -> Dict:
        """캐시 시스템 정보 반환"""
        try:
            info = {
                'redis_available': self.redis_available,
                'default_ttl': self.default_ttl,
                'key_prefix': self.key_prefix,
                'compression_threshold': self.compression_threshold,
                'stats': asdict(self.stats) if self.enable_stats else None,
                'memory_cache_size': len(self.memory_cache.cache),
                'memory_cache_stats': asdict(self.memory_cache.stats)
            }
            
            if self.redis_available:
                try:
                    redis_info = self.redis_client.info()
                    info['redis_info'] = {
                        'used_memory_human': redis_info.get('used_memory_human'),
                        'connected_clients': redis_info.get('connected_clients'),
                        'total_commands_processed': redis_info.get('total_commands_processed'),
                        'keyspace_hits': redis_info.get('keyspace_hits'),
                        'keyspace_misses': redis_info.get('keyspace_misses')
                    }
                    
                    # Redis에서 우리 키들의 수
                    our_keys = len(self.redis_client.keys(self._generate_key("*")))
                    info['redis_key_count'] = our_keys
                    
                except Exception as e:
                    logger.warning(f"Redis 정보 조회 실패: {str(e)}")
            
            return info
            
        except Exception as e:
            logger.error(f"캐시 정보 조회 실패: {str(e)}")
            return {'error': str(e)}
    
    def health_check(self) -> Dict[str, bool]:
        """캐시 시스템 건강 상태 체크"""
        results = {}
        
        # Redis 연결 테스트
        if self.redis_available:
            try:
                self.redis_client.ping()
                results['redis_connection'] = True
            except:
                results['redis_connection'] = False
                self.redis_available = False  # 연결 실패시 플래그 업데이트
        else:
            results['redis_connection'] = False
        
        # 메모리 캐시 테스트
        try:
            test_key = f"health_check_{int(time.time())}"
            test_value = {"test": True, "timestamp": time.time()}
            
            # 저장 테스트
            set_result = self.memory_cache.set(test_key, test_value, 60)
            results['memory_cache_write'] = set_result
            
            # 조회 테스트
            get_result = self.memory_cache.get(test_key)
            results['memory_cache_read'] = (get_result == test_value)
            
            # 정리
            self.memory_cache.delete(test_key)
            
        except Exception as e:
            logger.error(f"메모리 캐시 건강 체크 실패: {str(e)}")
            results['memory_cache_write'] = False
            results['memory_cache_read'] = False
        
        # 전체 캐시 시스템 테스트
        try:
            test_key = f"system_health_check_{int(time.time())}"
            test_value = {"system_test": True, "timestamp": time.time()}
            
            set_result = self.set(test_key, test_value, 60)
            get_result = self.get(test_key)
            delete_result = self.delete(test_key)
            
            results['system_write'] = set_result
            results['system_read'] = (get_result is not None and 
                                    get_result.get('system_test') == True)
            results['system_delete'] = delete_result
            
        except Exception as e:
            logger.error(f"시스템 건강 체크 실패: {str(e)}")
            results['system_write'] = False
            results['system_read'] = False
            results['system_delete'] = False
        
        # 전체 건강 상태
        all_healthy = all(results.values())
        results['overall_health'] = all_healthy
        
        return results

# 캐시 데코레이터
def cached(ttl: int = 3600, key_prefix: str = "", tags: Optional[List[str]] = None):
    """
    함수 결과를 캐시하는 데코레이터
    
    Args:
        ttl: 캐시 TTL (초)
        key_prefix: 캐시 키 접두사
        tags: 캐시 태그 목록
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 캐시 키 생성
            key_parts = [key_prefix or func.__name__]
            
            # 인자들을 키에 포함
            if args:
                args_hash = hashlib.md5(str(args).encode()).hexdigest()[:8]
                key_parts.append(f"args:{args_hash}")
            
            if kwargs:
                kwargs_hash = hashlib.md5(str(sorted(kwargs.items())).encode()).hexdigest()[:8]
                key_parts.append(f"kwargs:{kwargs_hash}")
            
            cache_key = ":".join(key_parts)
            
            # 캐시에서 조회
            cached_result = cache_manager.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # 함수 실행 및 결과 캐싱
            result = func(*args, **kwargs)
            cache_manager.set(cache_key, result, ttl=ttl, tags=tags)
            
            return result
            
        return wrapper
    return decorator

# 전역 캐시 매니저 인스턴스
cache_manager = CacheManager()

def init_cache_system(app=None, 
                     redis_url: Optional[str] = None,
                     default_ttl: int = 3600,
                     enable_warming: bool = True) -> CacheManager:
    """
    캐시 시스템 초기화
    
    Args:
        app: Flask 앱 인스턴스
        redis_url: Redis 연결 URL
        default_ttl: 기본 TTL
        enable_warming: 캐시 워밍 활성화
    """
    global cache_manager
    
    # 새로운 캐시 매니저 인스턴스 생성 (설정 적용)
    cache_manager = CacheManager(
        redis_url=redis_url,
        default_ttl=default_ttl,
        key_prefix='lottopro:v2:',
        compression_threshold=1024,
        enable_stats=True
    )
    
    if app:
        # Flask 앱에 캐시 매니저 연결
        app.cache = cache_manager
        
        # 캐시 관련 라우트 등록
        @app.route('/admin/cache/info')
        def cache_info():
            """캐시 정보 API"""
            from flask import jsonify
            return jsonify(cache_manager.get_cache_info())
        
        @app.route('/admin/cache/health')
        def cache_health():
            """캐시 건강 상태 API"""
            from flask import jsonify
            health_results = cache_manager.health_check()
            status_code = 200 if health_results.get('overall_health') else 503
            return jsonify(health_results), status_code
        
        @app.route('/admin/cache/clear', methods=['POST'])
        def clear_cache():
            """캐시 클리어 API"""
            from flask import jsonify, request
            
            data = request.get_json() or {}
            pattern = data.get('pattern', '*')
            
            try:
                cache_manager.clear(pattern)
                return jsonify({
                    'success': True,
                    'message': f'캐시 정리 완료: {pattern}'
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        # 캐시 워밍
        if enable_warming:
            def warm_basic_caches():
                """기본 캐시들 워밍"""
                try:
                    # 기본 통계 데이터 생성 및 캐싱
                    basic_stats = {
                        'hot_numbers': list(range(1, 11)),
                        'cold_numbers': list(range(35, 46)),
                        'generated_at': time.time()
                    }
                    return cache_manager.cache_statistics('basic', basic_stats)
                except Exception as e:
                    logger.error(f"기본 캐시 워밍 실패: {str(e)}")
                    return False
            
            # 앱 시작 시 캐시 워밍 (백그라운드)
            def background_warming():
                time.sleep(2)  # 앱 시작 후 잠시 대기
                cache_manager.warm_cache([warm_basic_caches])
            
            import threading
            warming_thread = threading.Thread(target=background_warming, daemon=True)
            warming_thread.start()
    
    logger.info("캐시 시스템 초기화 완료")
    return cache_manager

# 사용 예시 및 테스트
if __name__ == "__main__":
    # 테스트 실행
    print("캐시 시스템 테스트를 시작합니다...")
    
    # 캐시 매니저 생성
    test_cache = CacheManager(default_ttl=60)
    
    # 기본 캐시 테스트
    print("1. 기본 캐시 테스트")
    test_cache.set("test_key", {"message": "Hello Cache!", "number": 42})
    result = test_cache.get("test_key")
    print(f"   캐시 조회 결과: {result}")
    
    # 예측 캐시 테스트  
    print("2. 예측 캐시 테스트")
    user_nums = [7, 14, 21, 28, 35, 42]
    prediction_data = {
        "numbers": [1, 2, 3, 4, 5, 6],
        "confidence": 85,
        "model": "frequency"
    }
    
    test_cache.cache_prediction(user_nums, "frequency", prediction_data)
    cached_prediction = test_cache.get_cached_prediction(user_nums, "frequency")
    print(f"   예측 캐시 결과: {cached_prediction}")
    
    # 통계 캐시 테스트
    print("3. 통계 캐시 테스트")
    stats_data = {
        "total_users": 1000,
        "total_predictions": 5000,
        "accuracy_rate": 18.5
    }
    
    test_cache.cache_statistics("daily", stats_data)
    cached_stats = test_cache.get_cached_statistics("daily")
    print(f"   통계 캐시 결과: {cached_stats}")
    
    # 성능 테스트
    print("4. 성능 테스트")
    import time
    
    start_time = time.time()
    for i in range(1000):
        test_cache.set(f"perf_test_{i}", {"data": i, "timestamp": time.time()})
    set_time = time.time() - start_time
    
    start_time = time.time()
    for i in range(1000):
        test_cache.get(f"perf_test_{i}")
    get_time = time.time() - start_time
    
    print(f"   1000회 SET 시간: {set_time:.3f}초")
    print(f"   1000회 GET 시간: {get_time:.3f}초")
    
    # 캐시 정보 출력
    print("5. 캐시 시스템 정보")
    info = test_cache.get_cache_info()
    print(f"   히트율: {info['stats']['hit_rate']:.1f}%")
    print(f"   총 연산: {info['stats']['total_operations']}")
    print(f"   평균 응답시간: {info['stats']['avg_response_time_ms']:.1f}ms")
    
    # 건강 상태 체크
    print("6. 건강 상태 체크")
    health = test_cache.health_check()
    print(f"   전체 건강 상태: {'정상' if health['overall_health'] else '이상'}")
    for check, status in health.items():
        if check != 'overall_health':
            print(f"   {check}: {'OK' if status else 'FAIL'}")
    
    print("캐시 시스템 테스트 완료!")
