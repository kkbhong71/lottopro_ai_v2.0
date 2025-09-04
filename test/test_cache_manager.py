"""
LottoPro-AI 캐시 관리 시스템 테스트
"""

import unittest
import time
import json
import threading
from unittest.mock import Mock, patch, MagicMock
import os
import sys

# 프로젝트 루트를 패스에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    from utils.cache_manager import (
        CacheManager, 
        MemoryCache, 
        CacheStats,
        cached,
        init_cache_system
    )
    CACHE_AVAILABLE = True
except ImportError as e:
    CACHE_AVAILABLE = False
    print(f"Warning: Cache manager not available: {e}")


class TestCacheStats(unittest.TestCase):
    """캐시 통계 클래스 테스트"""
    
    def setUp(self):
        if not CACHE_AVAILABLE:
            self.skipTest("Cache manager not available")
        self.stats = CacheStats()
    
    def test_initial_state(self):
        """초기 상태 테스트"""
        self.assertEqual(self.stats.hit_count, 0)
        self.assertEqual(self.stats.miss_count, 0)
        self.assertEqual(self.stats.set_count, 0)
        self.assertEqual(self.stats.delete_count, 0)
        self.assertEqual(self.stats.hit_rate, 0)
        self.assertEqual(self.stats.total_operations, 0)
    
    def test_hit_rate_calculation(self):
        """히트율 계산 테스트"""
        # 초기 상태 (분모가 0인 경우)
        self.assertEqual(self.stats.hit_rate, 0)
        
        # 히트와 미스 추가
        self.stats.hit_count = 8
        self.stats.miss_count = 2
        
        expected_hit_rate = (8 / (8 + 2)) * 100
        self.assertEqual(self.stats.hit_rate, expected_hit_rate)
    
    def test_total_operations(self):
        """총 연산 수 테스트"""
        self.stats.hit_count = 10
        self.stats.miss_count = 5
        self.stats.set_count = 15
        self.stats.delete_count = 3
        
        expected_total = 10 + 5 + 15 + 3
        self.assertEqual(self.stats.total_operations, expected_total)
    
    def test_reset(self):
        """통계 리셋 테스트"""
        # 일부 값 설정
        self.stats.hit_count = 10
        self.stats.miss_count = 5
        self.stats.set_count = 20
        
        # 리셋
        self.stats.reset()
        
        self.assertEqual(self.stats.hit_count, 0)
        self.assertEqual(self.stats.miss_count, 0)
        self.assertEqual(self.stats.set_count, 0)
        self.assertEqual(self.stats.delete_count, 0)


class TestMemoryCache(unittest.TestCase):
    """메모리 캐시 클래스 테스트"""
    
    def setUp(self):
        if not CACHE_AVAILABLE:
            self.skipTest("Cache manager not available")
        self.cache = MemoryCache(max_size=5, default_ttl=1)
    
    def test_basic_operations(self):
        """기본 캐시 동작 테스트"""
        # 설정
        self.cache.set('key1', 'value1')
        
        # 조회
        result = self.cache.get('key1')
        self.assertEqual(result, 'value1')
        
        # 없는 키 조회
        result = self.cache.get('nonexistent')
        self.assertIsNone(result)
    
    def test_ttl_expiration(self):
        """TTL 만료 테스트"""
        # 짧은 TTL로 설정
        self.cache.set('key1', 'value1', ttl=0.1)
        
        # 즉시 조회 (존재해야 함)
        result = self.cache.get('key1')
        self.assertEqual(result, 'value1')
        
        # TTL 대기
        time.sleep(0.2)
        
        # 만료된 키 조회 (None이어야 함)
        result = self.cache.get('key1')
        self.assertIsNone(result)
    
    def test_lru_eviction(self):
        """LRU 제거 정책 테스트"""
        # max_size(5)를 초과하는 데이터 추가
        for i in range(7):
            self.cache.set(f'key{i}', f'value{i}')
        
        # 처음 두 개 키는 제거되었어야 함
        self.assertIsNone(self.cache.get('key0'))
        self.assertIsNone(self.cache.get('key1'))
        
        # 나머지는 존재해야 함
        self.assertEqual(self.cache.get('key6'), 'value6')
        self.assertEqual(self.cache.get('key5'), 'value5')
    
    def test_access_time_update(self):
        """액세스 시간 업데이트 테스트"""
        # 여러 키 설정
        for i in range(5):
            self.cache.set(f'key{i}', f'value{i}')
        
        # key0 액세스 (최근 사용으로 표시)
        self.cache.get('key0')
        
        # 새로운 키 추가로 제거 유발
        self.cache.set('key5', 'value5')
        
        # key0는 최근에 액세스했으므로 유지되어야 함
        self.assertEqual(self.cache.get('key0'), 'value0')
        
        # 다른 키는 제거되었을 수 있음
        # (정확한 제거 대상은 구현에 따라 달라질 수 있음)
    
    def test_tags_functionality(self):
        """태그 기능 테스트"""
        # 태그와 함께 데이터 설정
        self.cache.set('user:1', 'data1', tags=['user', 'profile'])
        self.cache.set('user:2', 'data2', tags=['user', 'profile'])
        self.cache.set('post:1', 'post1', tags=['post'])
        
        # 태그별 무효화
        invalidated = self.cache.invalidate_by_tags(['user'])
        
        self.assertEqual(invalidated, 2)
        
        # user 태그 데이터는 제거됨
        self.assertIsNone(self.cache.get('user:1'))
        self.assertIsNone(self.cache.get('user:2'))
        
        # post 태그 데이터는 유지됨
        self.assertEqual(self.cache.get('post:1'), 'post1')
    
    def test_clear_operations(self):
        """삭제 및 클리어 테스트"""
        # 데이터 설정
        self.cache.set('key1', 'value1')
        self.cache.set('key2', 'value2')
        self.cache.set('test_key', 'test_value')
        
        # 개별 삭제
        result = self.cache.delete('key1')
        self.assertTrue(result)
        self.assertIsNone(self.cache.get('key1'))
        
        # 없는 키 삭제
        result = self.cache.delete('nonexistent')
        self.assertFalse(result)
        
        # 패턴 삭제
        deleted_count = self.cache.clear('test_*')
        self.assertEqual(deleted_count, 1)
        self.assertIsNone(self.cache.get('test_key'))
        
        # 전체 클리어
        deleted_count = self.cache.clear('*')
        self.assertEqual(deleted_count, 1)  # key2만 남아있음
        self.assertIsNone(self.cache.get('key2'))
    
    def test_get_stats(self):
        """통계 조회 테스트"""
        # 데이터 추가
        for i in range(3):
            self.cache.set(f'key{i}', f'value{i}')
        
        stats = self.cache.get_stats()
        
        self.assertEqual(stats['total_keys'], 3)
        self.assertEqual(stats['max_size'], 5)
        self.assertEqual(stats['memory_usage_percent'], 60.0)  # 3/5 * 100
    
    def test_concurrent_access(self):
        """동시 접근 테스트"""
        def worker(worker_id):
            for i in range(10):
                key = f'worker{worker_id}_key{i}'
                value = f'worker{worker_id}_value{i}'
                self.cache.set(key, value)
                result = self.cache.get(key)
                self.assertIsNotNone(result)
        
        # 여러 스레드로 동시 접근
        threads = []
        for i in range(3):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        # 모든 스레드 완료 대기
        for thread in threads:
            thread.join()
        
        # 캐시가 정상적으로 작동했는지 확인
        stats = self.cache.get_stats()
        self.assertGreater(stats['total_keys'], 0)


class TestCacheManager(unittest.TestCase):
    """통합 캐시 매니저 테스트"""
    
    def setUp(self):
        if not CACHE_AVAILABLE:
            self.skipTest("Cache manager not available")
        # Redis 없이 메모리 캐시만 사용
        self.cache_manager = CacheManager(
            redis_url=None,
            memory_cache_size=10,
            enable_compression=False
        )
    
    def test_basic_cache_operations(self):
        """기본 캐시 동작 테스트"""
        # 설정
        success = self.cache_manager.set('test_key', 'test_value', ttl=60)
        self.assertTrue(success)
        
        # 조회
        result = self.cache_manager.get('test_key')
        self.assertEqual(result, 'test_value')
        
        # 삭제
        success = self.cache_manager.delete('test_key')
        self.assertTrue(success)
        
        # 삭제 확인
        result = self.cache_manager.get('test_key')
        self.assertIsNone(result)
    
    def test_complex_data_types(self):
        """복잡한 데이터 타입 테스트"""
        test_data = {
            'string': 'test_string',
            'number': 42,
            'list': [1, 2, 3, 'four'],
            'dict': {'nested': True, 'value': 123},
            'boolean': True,
            'null': None
        }
        
        # 설정 및 조회
        success = self.cache_manager.set('complex_data', test_data)
        self.assertTrue(success)
        
        result = self.cache_manager.get('complex_data')
        self.assertEqual(result, test_data)
    
    def test_tags_invalidation(self):
        """태그 무효화 테스트"""
        # 태그와 함께 여러 데이터 설정
        self.cache_manager.set('item1', 'data1', tags=['tag1', 'common'])
        self.cache_manager.set('item2', 'data2', tags=['tag2', 'common'])
        self.cache_manager.set('item3', 'data3', tags=['tag1'])
        
        # 특정 태그로 무효화
        invalidated = self.cache_manager.invalidate_by_tags(['tag1'])
        
        # tag1을 가진 item들은 제거됨
        self.assertIsNone(self.cache_manager.get('item1'))
        self.assertIsNone(self.cache_manager.get('item3'))
        
        # tag2만 가진 item2는 유지됨
        self.assertEqual(self.cache_manager.get('item2'), 'data2')
    
    def test_specialized_cache_methods(self):
        """특화된 캐시 메소드 테스트"""
        # 예측 캐시
        user_numbers = [1, 2, 3, 4, 5, 6]
        model_type = 'frequency'
        prediction_result = [7, 14, 21, 28, 35, 42]
        
        success = self.cache_manager.cache_prediction(
            user_numbers, model_type, prediction_result, ttl=300
        )
        self.assertTrue(success)
        
        cached_result = self.cache_manager.get_cached_prediction(
            user_numbers, model_type
        )
        self.assertEqual(cached_result, prediction_result)
        
        # 통계 캐시
        stats_data = {'total_draws': 1000, 'hot_numbers': [1, 2, 3]}
        success = self.cache_manager.cache_statistics('main', stats_data)
        self.assertTrue(success)
        
        cached_stats = self.cache_manager.get_cached_statistics('main')
        self.assertEqual(cached_stats, stats_data)
        
        # 사용자 번호 캐시
        user_id = 'user123'
        numbers_data = [{'numbers': [1, 2, 3, 4, 5, 6], 'label': 'Test'}]
        
        success = self.cache_manager.cache_user_numbers(user_id, numbers_data)
        self.assertTrue(success)
        
        cached_numbers = self.cache_manager.get_cached_user_numbers(user_id)
        self.assertEqual(cached_numbers, numbers_data)
    
    def test_health_check(self):
        """캐시 건강 상태 확인 테스트"""
        health = self.cache_manager.health_check()
        
        self.assertIn('overall_health', health)
        self.assertIn('memory_cache_available', health)
        self.assertIn('errors', health)
        
        self.assertTrue(health['memory_cache_available'])
        self.assertIsInstance(health['errors'], list)
    
    def test_cache_info(self):
        """캐시 정보 조회 테스트"""
        info = self.cache_manager.get_cache_info()
        
        self.assertIn('redis_available', info)
        self.assertIn('memory_cache_size', info)
        self.assertIn('stats', info)
        
        self.assertFalse(info['redis_available'])  # Redis 없이 테스트
        self.assertEqual(info['memory_cache_size'], 10)
    
    def test_cache_warming(self):
        """캐시 워밍 테스트"""
        warming_functions = []
        
        def warm_function1():
            self.cache_manager.set('warmed_key1', 'warmed_value1')
            return True
        
        def warm_function2():
            # 실패하는 함수
            raise Exception("Warming failed")
        
        def warm_function3():
            self.cache_manager.set('warmed_key3', 'warmed_value3')
            return True
        
        warming_functions = [warm_function1, warm_function2, warm_function3]
        
        results = self.cache_manager.warm_cache(warming_functions)
        
        # 결과 확인
        self.assertEqual(len(results), 3)
        
        # 성공한 함수들
        self.assertTrue(results['warm_function1']['success'])
        self.assertTrue(results['warm_function3']['success'])
        
        # 실패한 함수
        self.assertFalse(results['warm_function2']['success'])
        self.assertIn('error', results['warm_function2'])
        
        # 실제로 캐시된 데이터 확인
        self.assertEqual(self.cache_manager.get('warmed_key1'), 'warmed_value1')
        self.assertEqual(self.cache_manager.get('warmed_key3'), 'warmed_value3')


@unittest.skipUnless(CACHE_AVAILABLE, "Cache manager not available")
class TestCacheDecorator(unittest.TestCase):
    """캐시 데코레이터 테스트"""
    
    def setUp(self):
        # Mock Flask current_app
        self.mock_cache_manager = Mock()
        
        # 패치할 current_app 설정
        self.current_app_patcher = patch('utils.cache_manager.current_app')
        self.mock_current_app = self.current_app_patcher.start()
        self.mock_current_app.extensions = {
            'cache_manager': self.mock_cache_manager
        }
    
    def tearDown(self):
        self.current_app_patcher.stop()
    
    def test_cached_decorator_hit(self):
        """캐시 히트 테스트"""
        # 캐시에서 값을 반환하도록 설정
        self.mock_cache_manager.get.return_value = "cached_result"
        
        @cached(ttl=300, tags=['test'])
        def test_function(param1, param2='default'):
            return f"function_result_{param1}_{param2}"
        
        result = test_function('arg1', param2='arg2')
        
        # 캐시된 결과가 반환되어야 함
        self.assertEqual(result, "cached_result")
        
        # 캐시 조회가 호출되었는지 확인
        self.mock_cache_manager.get.assert_called_once()
        
        # 실제 함수는 실행되지 않았으므로 set이 호출되지 않아야 함
        self.mock_cache_manager.set.assert_not_called()
    
    def test_cached_decorator_miss(self):
        """캐시 미스 테스트"""
        # 캐시에 값이 없음을 시뮬레이션
        self.mock_cache_manager.get.return_value = None
        self.mock_cache_manager.set.return_value = True
        
        @cached(ttl=300, tags=['test'])
        def test_function(param1):
            return f"function_result_{param1}"
        
        result = test_function('arg1')
        
        # 함수 실행 결과가 반환되어야 함
        self.assertEqual(result, "function_result_arg1")
        
        # 캐시 조회와 저장이 모두 호출되었는지 확인
        self.mock_cache_manager.get.assert_called_once()
        self.mock_cache_manager.set.assert_called_once()
        
        # set 호출 인자 확인
        args, kwargs = self.mock_cache_manager.set.call_args
        cache_key, cached_value, ttl, tags = args
        
        self.assertEqual(cached_value, "function_result_arg1")
        self.assertEqual(ttl, 300)
        self.assertEqual(tags, ['test'])
    
    def test_cached_decorator_no_cache_manager(self):
        """캐시 매니저가 없을 때 데코레이터 동작 테스트"""
        # 캐시 매니저가 없는 상황 시뮬레이션
        self.mock_current_app.extensions = {}
        
        @cached(ttl=300)
        def test_function(param1):
            return f"function_result_{param1}"
        
        result = test_function('arg1')
        
        # 캐시 매니저가 없어도 함수는 정상적으로 실행되어야 함
        self.assertEqual(result, "function_result_arg1")
    
    def test_cached_decorator_cache_error(self):
        """캐시 에러 시 데코레이터 동작 테스트"""
        # 캐시에서 에러 발생 시뮬레이션
        self.mock_cache_manager.get.side_effect = Exception("Cache error")
        
        @cached(ttl=300)
        def test_function(param1):
            return f"function_result_{param1}"
        
        result = test_function('arg1')
        
        # 캐시 에러가 발생해도 함수는 정상적으로 실행되어야 함
        self.assertEqual(result, "function_result_arg1")


class TestInitCacheSystem(unittest.TestCase):
    """캐시 시스템 초기화 테스트"""
    
    def setUp(self):
        if not CACHE_AVAILABLE:
            self.skipTest("Cache manager not available")
    
    def test_init_cache_system_no_app(self):
        """앱 없이 캐시 시스템 초기화 테스트"""
        cache_manager = init_cache_system(
            app=None,
            redis_url=None,
            default_ttl=600
        )
        
        self.assertIsInstance(cache_manager, CacheManager)
        self.assertEqual(cache_manager.default_ttl, 600)
    
    def test_init_cache_system_with_app(self):
        """앱과 함께 캐시 시스템 초기화 테스트"""
        # Mock Flask 앱
        mock_app = Mock()
        mock_app.extensions = {}
        
        cache_manager = init_cache_system(
            app=mock_app,
            redis_url=None,
            default_ttl=300
        )
        
        # 앱의 extensions에 등록되었는지 확인
        self.assertIn('cache_manager', mock_app.extensions)
        self.assertEqual(mock_app.extensions['cache_manager'], cache_manager)


class CacheIntegrationTest(unittest.TestCase):
    """캐시 시스템 통합 테스트"""
    
    def setUp(self):
        if not CACHE_AVAILABLE:
            self.skipTest("Cache manager not available")
        self.cache_manager = CacheManager(
            redis_url=None,
            memory_cache_size=20,
            enable_compression=False
        )
    
    def test_full_cache_lifecycle(self):
        """전체 캐시 라이프사이클 테스트"""
        # 1. 초기 상태 확인
        info = self.cache_manager.get_cache_info()
        initial_stats = info['stats']
        
        # 2. 다양한 데이터 타입으로 캐시 설정
        test_cases = [
            ('string_key', 'string_value', ['strings']),
            ('int_key', 12345, ['numbers']),
            ('list_key', [1, 2, 3, 'four'], ['lists']),
            ('dict_key', {'nested': {'deep': True}}, ['dicts']),
            ('bool_key', True, ['booleans']),
        ]
        
        for key, value, tags in test_cases:
            success = self.cache_manager.set(key, value, ttl=60, tags=tags)
            self.assertTrue(success)
        
        # 3. 모든 값 조회 및 확인
        for key, expected_value, _ in test_cases:
            cached_value = self.cache_manager.get(key)
            self.assertEqual(cached_value, expected_value)
        
        # 4. 특화된 캐시 메소드 테스트
        # 예측 캐시
        prediction_result = self.cache_manager.get_cached_prediction([1, 2, 3], 'test_model')
        self.assertIsNone(prediction_result)  # 캐시 미스
        
        self.cache_manager.cache_prediction([1, 2, 3], 'test_model', [10, 20, 30])
        prediction_result = self.cache_manager.get_cached_prediction([1, 2, 3], 'test_model')
        self.assertEqual(prediction_result, [10, 20, 30])  # 캐시 히트
        
        # 5. 태그별 무효화
        invalidated = self.cache_manager.invalidate_by_tags(['strings', 'numbers'])
        self.assertGreaterEqual(invalidated, 2)
        
        # 무효화된 키들은 조회되지 않아야 함
        self.assertIsNone(self.cache_manager.get('string_key'))
        self.assertIsNone(self.cache_manager.get('int_key'))
        
        # 다른 키들은 유지되어야 함
        self.assertEqual(self.cache_manager.get('list_key'), [1, 2, 3, 'four'])
        
        # 6. 건강 상태 확인
        health = self.cache_manager.health_check()
        self.assertTrue(health['overall_health'])
        
        # 7. 최종 통계 확인
        final_info = self.cache_manager.get_cache_info()
        final_stats = final_info['stats']
        
        # 히트와 미스가 발생했는지 확인
        self.assertGreater(final_stats['total_operations'], initial_stats['total_operations'])
    
    def test_performance_under_load(self):
        """부하 상황에서의 성능 테스트"""
        import threading
        
        def worker(worker_id, iterations=100):
            for i in range(iterations):
                key = f'worker_{worker_id}_item_{i}'
                value = f'data_{worker_id}_{i}'
                
                # 설정
                self.cache_manager.set(key, value, ttl=30)
                
                # 조회
                result = self.cache_manager.get(key)
                self.assertEqual(result, value)
                
                # 가끔 삭제
                if i % 10 == 0:
                    self.cache_manager.delete(key)
        
        # 여러 스레드로 동시 부하 생성
        threads = []
        start_time = time.time()
        
        for worker_id in range(5):
            thread = threading.Thread(target=worker, args=(worker_id, 50))
            threads.append(thread)
            thread.start()
        
        # 모든 스레드 완료 대기
        for thread in threads:
            thread.join()
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        print(f"Performance test completed in {execution_time:.2f} seconds")
        
        # 최종 상태 확인
        info = self.cache_manager.get_cache_info()
        print(f"Final cache stats: {info['stats']}")
        
        # 건강 상태 확인
        health = self.cache_manager.health_check()
        self.assertTrue(health['overall_health'])
    
    def test_memory_usage_limits(self):
        """메모리 사용량 제한 테스트"""
        # 최대 크기를 초과하는 데이터 추가
        for i in range(25):  # max_size(20)를 초과
            key = f'memory_test_key_{i}'
            value = f'memory_test_value_{i}' * 100  # 큰 값
            self.cache_manager.set(key, value)
        
        # 메모리 캐시 상태 확인
        memory_stats = self.cache_manager.memory_cache.get_stats()
        
        # 최대 크기를 초과하지 않았는지 확인
        self.assertLessEqual(memory_stats['total_keys'], 20)
        
        # 메모리 사용률 확인
        self.assertLessEqual(memory_stats['memory_usage_percent'], 100)


if __name__ == '__main__':
    # 테스트 실행 전 환경 확인
    print("캐시 관리 시스템 테스트 실행")
    print(f"캐시 모듈 사용 가능: {CACHE_AVAILABLE}")
    
    if not CACHE_AVAILABLE:
        print("Warning: 일부 테스트가 스킵됩니다.")
    
    # 테스트 실행
    unittest.main(verbosity=2)
