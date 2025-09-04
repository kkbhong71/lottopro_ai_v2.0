"""
LottoPro-AI 성능 모니터링 시스템 테스트
"""

import unittest
import time
import threading
from unittest.mock import Mock, patch, MagicMock
import json
import os
import sys

# 프로젝트 루트를 패스에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    from monitoring.performance_monitor import (
        PerformanceMonitor, 
        PerformanceStats, 
        monitor_performance,
        init_monitoring
    )
    MONITORING_AVAILABLE = True
except ImportError as e:
    MONITORING_AVAILABLE = False
    print(f"Warning: Performance monitoring not available: {e}")


class TestPerformanceStats(unittest.TestCase):
    """성능 통계 클래스 테스트"""
    
    def setUp(self):
        if not MONITORING_AVAILABLE:
            self.skipTest("Performance monitoring not available")
        self.stats = PerformanceStats(window_size=100)
    
    def test_initial_state(self):
        """초기 상태 테스트"""
        self.assertEqual(self.stats.total_requests, 0)
        self.assertEqual(self.stats.total_errors, 0)
        self.assertEqual(self.stats.total_response_time, 0)
        self.assertEqual(self.stats.error_rate, 0)
        self.assertEqual(self.stats.average_response_time, 0)
    
    def test_add_request_success(self):
        """성공 요청 추가 테스트"""
        self.stats.add_request('/api/test', 0.5, error=False)
        
        self.assertEqual(self.stats.total_requests, 1)
        self.assertEqual(self.stats.total_errors, 0)
        self.assertEqual(self.stats.total_response_time, 0.5)
        self.assertEqual(self.stats.error_rate, 0)
        self.assertEqual(self.stats.average_response_time, 0.5)
    
    def test_add_request_error(self):
        """에러 요청 추가 테스트"""
        self.stats.add_request('/api/test', 1.0, error=True)
        
        self.assertEqual(self.stats.total_requests, 1)
        self.assertEqual(self.stats.total_errors, 1)
        self.assertEqual(self.stats.error_rate, 100.0)
    
    def test_endpoint_stats(self):
        """엔드포인트별 통계 테스트"""
        # 여러 요청 추가
        self.stats.add_request('/api/predict', 0.8, error=False)
        self.stats.add_request('/api/predict', 1.2, error=False)
        self.stats.add_request('/api/predict', 2.0, error=True)
        
        endpoint_stats = self.stats.endpoint_stats['/api/predict']
        
        self.assertEqual(endpoint_stats['count'], 3)
        self.assertEqual(endpoint_stats['errors'], 1)
        self.assertEqual(endpoint_stats['total_time'], 4.0)
        self.assertAlmostEqual(endpoint_stats['avg_time'], 4.0/3, places=2)
    
    def test_response_time_window(self):
        """응답시간 윈도우 테스트"""
        # window_size를 초과하는 요청 추가
        for i in range(150):
            self.stats.add_request('/api/test', 0.1)
        
        # 최대 window_size만큼만 저장되어야 함
        self.assertEqual(len(self.stats.response_times), 100)
    
    @patch('monitoring.performance_monitor.psutil')
    def test_add_system_stats(self, mock_psutil):
        """시스템 통계 추가 테스트"""
        # psutil mock 설정
        mock_psutil.cpu_percent.return_value = 75.5
        mock_psutil.virtual_memory.return_value = Mock(percent=82.3)
        mock_psutil.disk_usage.return_value = Mock(percent=45.8)
        
        self.stats.add_system_stats()
        
        self.assertEqual(len(self.stats.cpu_usage), 1)
        self.assertEqual(len(self.stats.memory_usage), 1)
        self.assertEqual(len(self.stats.disk_usage), 1)
        
        self.assertEqual(self.stats.cpu_usage[0], 75.5)
        self.assertEqual(self.stats.memory_usage[0], 82.3)
        self.assertEqual(self.stats.disk_usage[0], 45.8)


class TestPerformanceMonitor(unittest.TestCase):
    """성능 모니터 클래스 테스트"""
    
    def setUp(self):
        if not MONITORING_AVAILABLE:
            self.skipTest("Performance monitoring not available")
        self.monitor = PerformanceMonitor(auto_start=False)
    
    def tearDown(self):
        if hasattr(self, 'monitor'):
            self.monitor.stop_monitoring()
    
    def test_monitor_initialization(self):
        """모니터 초기화 테스트"""
        self.assertIsNotNone(self.monitor.stats)
        self.assertFalse(self.monitor.running)
        self.assertIsNone(self.monitor.collection_thread)
        
        # 기본 임계값 확인
        self.assertIn('response_time', self.monitor.thresholds)
        self.assertIn('error_rate', self.monitor.thresholds)
        self.assertIn('cpu_usage', self.monitor.thresholds)
    
    def test_custom_thresholds(self):
        """사용자 정의 임계값 테스트"""
        custom_thresholds = {
            'response_time': 15.0,
            'error_rate': 0.08
        }
        
        monitor = PerformanceMonitor(
            auto_start=False,
            custom_thresholds=custom_thresholds
        )
        
        self.assertEqual(monitor.thresholds['response_time'], 15.0)
        self.assertEqual(monitor.thresholds['error_rate'], 0.08)
        
        # 기본값이 유지되는지 확인
        self.assertIn('cpu_usage', monitor.thresholds)
    
    def test_start_stop_monitoring(self):
        """모니터링 시작/중지 테스트"""
        # 시작
        self.monitor.start_monitoring()
        self.assertTrue(self.monitor.running)
        self.assertIsNotNone(self.monitor.collection_thread)
        
        # 잠시 대기
        time.sleep(0.1)
        
        # 중지
        self.monitor.stop_monitoring()
        self.assertFalse(self.monitor.running)
    
    def test_alert_callbacks(self):
        """알림 콜백 테스트"""
        callback_called = []
        
        def test_callback(alert_info):
            callback_called.append(alert_info)
        
        self.monitor.add_alert_callback(test_callback)
        
        # 수동으로 알림 트리거
        alert_info = {
            'type': 'test_alert',
            'message': 'Test message',
            'value': 100,
            'threshold': 80
        }
        
        self.monitor._trigger_alert(alert_info)
        
        self.assertEqual(len(callback_called), 1)
        self.assertEqual(callback_called[0]['type'], 'test_alert')
    
    def test_get_current_stats(self):
        """현재 통계 조회 테스트"""
        # 테스트 데이터 추가
        self.monitor.stats.add_request('/api/test', 1.5, error=False)
        self.monitor.stats.add_request('/api/test', 2.0, error=True)
        
        stats = self.monitor.get_current_stats()
        
        # 기본 구조 확인
        self.assertIn('overview', stats)
        self.assertIn('system', stats)
        self.assertIn('endpoints', stats)
        self.assertIn('thresholds', stats)
        self.assertIn('health_status', stats)
        
        # 오버뷰 데이터 확인
        overview = stats['overview']
        self.assertEqual(overview['total_requests'], 2)
        self.assertEqual(overview['total_errors'], 1)
        self.assertEqual(overview['error_rate'], 50.0)
    
    def test_health_status_evaluation(self):
        """건강 상태 평가 테스트"""
        # 정상 상태 테스트
        with patch.object(self.monitor.stats, 'cpu_usage', [50.0]):
            with patch.object(self.monitor.stats, 'memory_usage', [60.0]):
                with patch.object(self.monitor.stats, 'error_rate', 2.0):
                    with patch.object(self.monitor.stats, 'average_response_time', 1.0):
                        health = self.monitor._get_health_status()
                        self.assertEqual(health, 'healthy')
        
        # 경고 상태 테스트 (CPU 높음)
        with patch.object(self.monitor.stats, 'cpu_usage', [90.0]):
            with patch.object(self.monitor.stats, 'memory_usage', [60.0]):
                with patch.object(self.monitor.stats, 'error_rate', 2.0):
                    with patch.object(self.monitor.stats, 'average_response_time', 1.0):
                        health = self.monitor._get_health_status()
                        self.assertEqual(health, 'warning')
        
        # 심각 상태 테스트 (에러율 매우 높음)
        with patch.object(self.monitor.stats, 'cpu_usage', [50.0]):
            with patch.object(self.monitor.stats, 'memory_usage', [60.0]):
                with patch.object(self.monitor.stats, 'error_rate', 60.0):
                    with patch.object(self.monitor.stats, 'average_response_time', 1.0):
                        health = self.monitor._get_health_status()
                        self.assertEqual(health, 'critical')
    
    def test_performance_trends(self):
        """성능 트렌드 분석 테스트"""
        # 시간별 통계에 테스트 데이터 추가
        from datetime import datetime, timedelta
        
        current_time = datetime.now()
        hour_key = current_time.strftime('%Y-%m-%d %H')
        
        self.monitor.stats.hourly_stats[hour_key] = {
            'requests': 100,
            'errors': 5,
            'avg_response_time': 1.2,
            'total_response_time': 120
        }
        
        trends = self.monitor.get_performance_trends(minutes=60)
        
        self.assertIn('time_range_minutes', trends)
        self.assertIn('hourly_trends', trends)
        self.assertIn('total_requests_in_period', trends)
        self.assertIn('trend_analysis', trends)
        
        self.assertEqual(trends['time_range_minutes'], 60)
    
    def test_export_metrics_json(self):
        """JSON 형태 메트릭 내보내기 테스트"""
        # 테스트 데이터 추가
        self.monitor.stats.add_request('/api/test', 1.0)
        
        json_data = self.monitor.export_metrics('json')
        
        # JSON 파싱 가능한지 확인
        parsed_data = json.loads(json_data)
        
        self.assertIn('overview', parsed_data)
        self.assertIn('system', parsed_data)
    
    def test_export_metrics_csv(self):
        """CSV 형태 메트릭 내보내기 테스트"""
        # 테스트 데이터 추가
        self.monitor.stats.add_request('/api/test', 1.5)
        
        csv_data = self.monitor.export_metrics('csv')
        
        # CSV 헤더 확인
        lines = csv_data.strip().split('\n')
        self.assertEqual(lines[0], 'metric,value,timestamp')
        self.assertGreater(len(lines), 1)


class TestPerformanceDecorator(unittest.TestCase):
    """성능 모니터링 데코레이터 테스트"""
    
    def setUp(self):
        if not MONITORING_AVAILABLE:
            self.skipTest("Performance monitoring not available")
    
    @patch('monitoring.performance_monitor.current_app')
    def test_monitor_performance_decorator(self, mock_current_app):
        """성능 모니터링 데코레이터 테스트"""
        # Mock Flask 앱과 모니터 설정
        mock_monitor = Mock()
        mock_current_app.extensions = {'performance_monitor': mock_monitor}
        
        @monitor_performance
        def test_function():
            time.sleep(0.01)  # 작은 지연
            return "success"
        
        result = test_function()
        
        # 함수가 정상적으로 실행되었는지 확인
        self.assertEqual(result, "success")
        
        # 모니터의 add_request가 호출되었는지 확인
        mock_monitor.stats.add_request.assert_called_once()
        
        # 호출 인자 확인
        args, kwargs = mock_monitor.stats.add_request.call_args
        endpoint, response_time, error = args
        
        self.assertEqual(endpoint, 'test_function')
        self.assertGreater(response_time, 0)
        self.assertFalse(error)
    
    @patch('monitoring.performance_monitor.current_app')
    def test_monitor_performance_decorator_error(self, mock_current_app):
        """성능 모니터링 데코레이터 에러 처리 테스트"""
        # Mock Flask 앱과 모니터 설정
        mock_monitor = Mock()
        mock_current_app.extensions = {'performance_monitor': mock_monitor}
        
        @monitor_performance
        def test_function_with_error():
            raise ValueError("Test error")
        
        with self.assertRaises(ValueError):
            test_function_with_error()
        
        # 에러가 발생해도 add_request가 호출되어야 함
        mock_monitor.stats.add_request.assert_called_once()
        
        # 에러 플래그 확인
        args, kwargs = mock_monitor.stats.add_request.call_args
        endpoint, response_time, error = args
        
        self.assertEqual(endpoint, 'test_function_with_error')
        self.assertTrue(error)
    
    @patch('monitoring.performance_monitor.current_app')
    def test_monitor_performance_no_monitor(self, mock_current_app):
        """모니터가 없을 때 데코레이터 동작 테스트"""
        # 모니터가 없는 상황 시뮬레이션
        mock_current_app.extensions = {}
        
        @monitor_performance
        def test_function():
            return "success"
        
        # 모니터가 없어도 함수는 정상적으로 실행되어야 함
        result = test_function()
        self.assertEqual(result, "success")


class TestInitMonitoring(unittest.TestCase):
    """모니터링 초기화 함수 테스트"""
    
    def setUp(self):
        if not MONITORING_AVAILABLE:
            self.skipTest("Performance monitoring not available")
    
    def test_init_monitoring_no_app(self):
        """앱 없이 모니터링 초기화 테스트"""
        monitor = init_monitoring(app=None, auto_start=False)
        
        self.assertIsInstance(monitor, PerformanceMonitor)
        self.assertFalse(monitor.running)
    
    def test_init_monitoring_with_app(self):
        """앱과 함께 모니터링 초기화 테스트"""
        # Mock Flask 앱
        mock_app = Mock()
        mock_app.extensions = {}
        
        monitor = init_monitoring(app=mock_app, auto_start=False)
        
        # 앱의 extensions에 등록되었는지 확인
        self.assertIn('performance_monitor', mock_app.extensions)
        self.assertEqual(mock_app.extensions['performance_monitor'], monitor)
    
    def test_init_monitoring_custom_config(self):
        """사용자 정의 설정으로 초기화 테스트"""
        custom_config = {
            'collection_interval': 60,
            'custom_thresholds': {
                'response_time': 20.0,
                'cpu_usage': 90.0
            }
        }
        
        monitor = init_monitoring(auto_start=False, **custom_config)
        
        self.assertEqual(monitor.collection_interval, 60)
        self.assertEqual(monitor.thresholds['response_time'], 20.0)
        self.assertEqual(monitor.thresholds['cpu_usage'], 90.0)


class PerformanceIntegrationTest(unittest.TestCase):
    """통합 테스트"""
    
    def setUp(self):
        if not MONITORING_AVAILABLE:
            self.skipTest("Performance monitoring not available")
        self.monitor = PerformanceMonitor(auto_start=False)
    
    def tearDown(self):
        if hasattr(self, 'monitor'):
            self.monitor.stop_monitoring()
    
    def test_full_monitoring_cycle(self):
        """전체 모니터링 사이클 테스트"""
        # 1. 모니터링 시작
        self.monitor.start_monitoring()
        
        # 2. 요청 데이터 추가
        self.monitor.stats.add_request('/api/predict', 1.2, error=False)
        self.monitor.stats.add_request('/api/predict', 2.1, error=False)
        self.monitor.stats.add_request('/api/stats', 0.8, error=False)
        self.monitor.stats.add_request('/api/predict', 5.0, error=True)
        
        # 3. 현재 통계 확인
        stats = self.monitor.get_current_stats()
        
        self.assertEqual(stats['overview']['total_requests'], 4)
        self.assertEqual(stats['overview']['total_errors'], 1)
        self.assertEqual(stats['overview']['error_rate'], 25.0)
        
        # 4. 엔드포인트별 통계 확인
        endpoints = stats['endpoints']
        self.assertIn('/api/predict', endpoints)
        self.assertEqual(endpoints['/api/predict']['count'], 3)
        self.assertEqual(endpoints['/api/predict']['errors'], 1)
        
        # 5. 내보내기 테스트
        json_export = self.monitor.export_metrics('json')
        self.assertIsInstance(json.loads(json_export), dict)
        
        csv_export = self.monitor.export_metrics('csv')
        self.assertIn('metric,value,timestamp', csv_export)
        
        # 6. 모니터링 중지
        self.monitor.stop_monitoring()
        self.assertFalse(self.monitor.running)


if __name__ == '__main__':
    # 테스트 실행 전 환경 확인
    print("성능 모니터링 시스템 테스트 실행")
    print(f"모니터링 모듈 사용 가능: {MONITORING_AVAILABLE}")
    
    if not MONITORING_AVAILABLE:
        print("Warning: 일부 테스트가 스킵됩니다.")
    
    # 테스트 실행
    unittest.main(verbosity=2)
