"""
LottoPro-AI 성능 모니터링 시스템
실시간 성능 메트릭 수집, 분석 및 알림
"""

import time
import threading
import psutil
import os
from collections import defaultdict, deque
from datetime import datetime, timedelta
from functools import wraps
import json
import uuid
from typing import Dict, List, Optional, Callable, Any
import logging

class PerformanceStats:
    """성능 통계 클래스"""
    
    def __init__(self, window_size: int = 1000):
        self.window_size = window_size
        self.response_times = deque(maxlen=window_size)
        self.error_counts = defaultdict(int)
        self.request_counts = defaultdict(int)
        self.endpoint_stats = defaultdict(lambda: {
            'count': 0,
            'total_time': 0,
            'errors': 0,
            'avg_time': 0
        })
        self.hourly_stats = defaultdict(lambda: {
            'requests': 0,
            'errors': 0,
            'avg_response_time': 0,
            'total_response_time': 0
        })
        
        # 시스템 리소스 기록
        self.cpu_usage = deque(maxlen=100)
        self.memory_usage = deque(maxlen=100)
        self.disk_usage = deque(maxlen=100)
        
        # 시작 시간
        self.start_time = datetime.now()
        self.total_requests = 0
        self.total_errors = 0
        self.total_response_time = 0

    @property
    def hit_rate(self) -> float:
        """캐시 히트율 (캐시 시스템과 연동 시 사용)"""
        if hasattr(self, '_hit_count') and hasattr(self, '_miss_count'):
            total = self._hit_count + self._miss_count
            return (self._hit_count / total * 100) if total > 0 else 0
        return 0

    @property
    def error_rate(self) -> float:
        """에러율 계산"""
        return (self.total_errors / max(self.total_requests, 1)) * 100

    @property
    def average_response_time(self) -> float:
        """평균 응답 시간"""
        return self.total_response_time / max(self.total_requests, 1)

    def add_request(self, endpoint: str, response_time: float, error: bool = False):
        """요청 통계 추가"""
        self.total_requests += 1
        self.total_response_time += response_time
        self.response_times.append(response_time)
        
        if error:
            self.total_errors += 1
            self.error_counts[endpoint] += 1
            self.endpoint_stats[endpoint]['errors'] += 1
        
        self.request_counts[endpoint] += 1
        self.endpoint_stats[endpoint]['count'] += 1
        self.endpoint_stats[endpoint]['total_time'] += response_time
        self.endpoint_stats[endpoint]['avg_time'] = (
            self.endpoint_stats[endpoint]['total_time'] / 
            self.endpoint_stats[endpoint]['count']
        )
        
        # 시간별 통계
        current_hour = datetime.now().strftime('%Y-%m-%d %H')
        self.hourly_stats[current_hour]['requests'] += 1
        self.hourly_stats[current_hour]['total_response_time'] += response_time
        self.hourly_stats[current_hour]['avg_response_time'] = (
            self.hourly_stats[current_hour]['total_response_time'] /
            self.hourly_stats[current_hour]['requests']
        )
        
        if error:
            self.hourly_stats[current_hour]['errors'] += 1

    def add_system_stats(self):
        """시스템 리소스 통계 추가"""
        try:
            self.cpu_usage.append(psutil.cpu_percent())
            self.memory_usage.append(psutil.virtual_memory().percent)
            self.disk_usage.append(psutil.disk_usage('/').percent)
        except Exception:
            # psutil이 없거나 에러 시 기본값
            self.cpu_usage.append(0)
            self.memory_usage.append(0)
            self.disk_usage.append(0)

class PerformanceMonitor:
    """성능 모니터링 메인 클래스"""
    
    def __init__(self, app=None, auto_start: bool = True, 
                 collection_interval: int = 30,
                 custom_thresholds: Dict[str, float] = None):
        self.app = app
        self.stats = PerformanceStats()
        self.collection_interval = collection_interval
        self.running = False
        self.collection_thread = None
        self.alert_callbacks = []
        
        # 임계값 설정
        self.thresholds = {
            'response_time': 5.0,      # 5초
            'error_rate': 0.1,         # 10%
            'cpu_usage': 85.0,         # 85%
            'memory_usage': 90.0,      # 90%
            'disk_usage': 95.0         # 95%
        }
        
        if custom_thresholds:
            self.thresholds.update(custom_thresholds)
        
        # 로거 설정
        self.logger = logging.getLogger(__name__)
        
        if app and auto_start:
            self.init_app(app)
            self.start_monitoring()

    def init_app(self, app):
        """Flask 앱 초기화"""
        self.app = app
        
        # Flask 앱에 모니터 인스턴스 등록
        if not hasattr(app, 'extensions'):
            app.extensions = {}
        app.extensions['performance_monitor'] = self

    def start_monitoring(self):
        """모니터링 시작"""
        if self.running:
            return
        
        self.running = True
        self.collection_thread = threading.Thread(
            target=self._collect_system_stats, 
            daemon=True
        )
        self.collection_thread.start()
        self.logger.info("Performance monitoring started")

    def stop_monitoring(self):
        """모니터링 중지"""
        self.running = False
        if self.collection_thread:
            self.collection_thread.join(timeout=5)
        self.logger.info("Performance monitoring stopped")

    def _collect_system_stats(self):
        """시스템 통계 수집 스레드"""
        while self.running:
            try:
                self.stats.add_system_stats()
                self._check_thresholds()
                time.sleep(self.collection_interval)
            except Exception as e:
                self.logger.error(f"System stats collection error: {e}")
                time.sleep(self.collection_interval)

    def _check_thresholds(self):
        """임계값 확인 및 알림"""
        alerts = []
        
        # CPU 사용률 확인
        if self.stats.cpu_usage:
            current_cpu = self.stats.cpu_usage[-1]
            if current_cpu > self.thresholds['cpu_usage']:
                alerts.append({
                    'type': 'cpu_high',
                    'message': f'CPU 사용률 높음: {current_cpu:.1f}%',
                    'value': current_cpu,
                    'threshold': self.thresholds['cpu_usage'],
                    'timestamp': datetime.now().isoformat()
                })
        
        # 메모리 사용률 확인
        if self.stats.memory_usage:
            current_memory = self.stats.memory_usage[-1]
            if current_memory > self.thresholds['memory_usage']:
                alerts.append({
                    'type': 'memory_high',
                    'message': f'메모리 사용률 높음: {current_memory:.1f}%',
                    'value': current_memory,
                    'threshold': self.thresholds['memory_usage'],
                    'timestamp': datetime.now().isoformat()
                })
        
        # 에러율 확인
        if self.stats.error_rate > self.thresholds['error_rate'] * 100:
            alerts.append({
                'type': 'error_rate_high',
                'message': f'에러율 높음: {self.stats.error_rate:.2f}%',
                'value': self.stats.error_rate,
                'threshold': self.thresholds['error_rate'] * 100,
                'timestamp': datetime.now().isoformat()
            })
        
        # 응답 시간 확인
        if self.stats.average_response_time > self.thresholds['response_time']:
            alerts.append({
                'type': 'response_time_high',
                'message': f'평균 응답 시간 높음: {self.stats.average_response_time:.2f}s',
                'value': self.stats.average_response_time,
                'threshold': self.thresholds['response_time'],
                'timestamp': datetime.now().isoformat()
            })
        
        # 알림 콜백 실행
        for alert in alerts:
            self._trigger_alert(alert)

    def _trigger_alert(self, alert_info: Dict):
        """알림 트리거"""
        for callback in self.alert_callbacks:
            try:
                callback(alert_info)
            except Exception as e:
                self.logger.error(f"Alert callback error: {e}")

    def add_alert_callback(self, callback: Callable):
        """알림 콜백 추가"""
        self.alert_callbacks.append(callback)

    def get_current_stats(self) -> Dict:
        """현재 통계 반환"""
        uptime = datetime.now() - self.stats.start_time
        
        return {
            'overview': {
                'total_requests': self.stats.total_requests,
                'total_errors': self.stats.total_errors,
                'error_rate': round(self.stats.error_rate, 2),
                'average_response_time': round(self.stats.average_response_time, 3),
                'uptime_seconds': int(uptime.total_seconds()),
                'uptime_human': str(uptime).split('.')[0]
            },
            'system': {
                'cpu_usage': list(self.stats.cpu_usage)[-10:] if self.stats.cpu_usage else [],
                'memory_usage': list(self.stats.memory_usage)[-10:] if self.stats.memory_usage else [],
                'disk_usage': list(self.stats.disk_usage)[-10:] if self.stats.disk_usage else [],
                'current_cpu': self.stats.cpu_usage[-1] if self.stats.cpu_usage else 0,
                'current_memory': self.stats.memory_usage[-1] if self.stats.memory_usage else 0,
                'current_disk': self.stats.disk_usage[-1] if self.stats.disk_usage else 0
            },
            'endpoints': dict(self.stats.endpoint_stats),
            'recent_response_times': list(self.stats.response_times)[-20:],
            'thresholds': self.thresholds,
            'health_status': self._get_health_status(),
            'collection_interval': self.collection_interval,
            'monitoring_active': self.running
        }

    def _get_health_status(self) -> str:
        """건강 상태 평가"""
        if not self.stats.cpu_usage or not self.stats.memory_usage:
            return 'unknown'
        
        current_cpu = self.stats.cpu_usage[-1]
        current_memory = self.stats.memory_usage[-1]
        error_rate = self.stats.error_rate
        avg_response_time = self.stats.average_response_time
        
        # 심각한 문제
        if (current_cpu > 95 or current_memory > 95 or 
            error_rate > 50 or avg_response_time > 30):
            return 'critical'
        
        # 경고 수준
        if (current_cpu > self.thresholds['cpu_usage'] or 
            current_memory > self.thresholds['memory_usage'] or
            error_rate > self.thresholds['error_rate'] * 100 or
            avg_response_time > self.thresholds['response_time']):
            return 'warning'
        
        # 정상
        return 'healthy'

    def get_performance_trends(self, minutes: int = 60) -> Dict:
        """성능 트렌드 분석"""
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        cutoff_hour = cutoff_time.strftime('%Y-%m-%d %H')
        
        relevant_hours = []
        for hour_key, stats in self.stats.hourly_stats.items():
            if hour_key >= cutoff_hour:
                relevant_hours.append({
                    'hour': hour_key,
                    'requests': stats['requests'],
                    'errors': stats['errors'],
                    'error_rate': (stats['errors'] / max(stats['requests'], 1)) * 100,
                    'avg_response_time': stats['avg_response_time']
                })
        
        relevant_hours.sort(key=lambda x: x['hour'])
        
        return {
            'time_range_minutes': minutes,
            'hourly_trends': relevant_hours,
            'total_requests_in_period': sum(h['requests'] for h in relevant_hours),
            'total_errors_in_period': sum(h['errors'] for h in relevant_hours),
            'trend_analysis': self._analyze_trends(relevant_hours)
        }

    def _analyze_trends(self, hourly_data: List[Dict]) -> Dict:
        """트렌드 분석"""
        if len(hourly_data) < 2:
            return {'status': 'insufficient_data'}
        
        recent_requests = [h['requests'] for h in hourly_data[-3:]]
        recent_response_times = [h['avg_response_time'] for h in hourly_data[-3:]]
        recent_error_rates = [h['error_rate'] for h in hourly_data[-3:]]
        
        # 단순 트렌드 분석
        request_trend = 'increasing' if recent_requests[-1] > recent_requests[0] else 'decreasing'
        response_time_trend = 'increasing' if recent_response_times[-1] > recent_response_times[0] else 'decreasing'
        error_rate_trend = 'increasing' if recent_error_rates[-1] > recent_error_rates[0] else 'decreasing'
        
        return {
            'status': 'analyzed',
            'request_trend': request_trend,
            'response_time_trend': response_time_trend,
            'error_rate_trend': error_rate_trend,
            'recommendations': self._get_recommendations(recent_response_times, recent_error_rates)
        }

    def _get_recommendations(self, response_times: List[float], error_rates: List[float]) -> List[str]:
        """성능 개선 권장사항"""
        recommendations = []
        
        avg_response_time = sum(response_times) / len(response_times)
        avg_error_rate = sum(error_rates) / len(error_rates)
        
        if avg_response_time > 3.0:
            recommendations.append("응답 시간이 느립니다. 캐시 시스템 활용을 고려하세요.")
        
        if avg_error_rate > 5.0:
            recommendations.append("에러율이 높습니다. 로그를 확인하고 버그를 수정하세요.")
        
        if self.stats.cpu_usage and max(self.stats.cpu_usage[-10:]) > 80:
            recommendations.append("CPU 사용률이 높습니다. 코드 최적화를 고려하세요.")
        
        if self.stats.memory_usage and max(self.stats.memory_usage[-10:]) > 85:
            recommendations.append("메모리 사용률이 높습니다. 메모리 누수를 확인하세요.")
        
        if not recommendations:
            recommendations.append("현재 시스템 성능이 양호합니다.")
        
        return recommendations

    def export_metrics(self, format_type: str = 'json') -> str:
        """메트릭 내보내기"""
        data = self.get_current_stats()
        
        if format_type == 'json':
            return json.dumps(data, indent=2, ensure_ascii=False)
        elif format_type == 'csv':
            # 간단한 CSV 형태로 변환
            lines = ['metric,value,timestamp']
            timestamp = datetime.now().isoformat()
            
            lines.append(f"total_requests,{data['overview']['total_requests']},{timestamp}")
            lines.append(f"error_rate,{data['overview']['error_rate']},{timestamp}")
            lines.append(f"avg_response_time,{data['overview']['average_response_time']},{timestamp}")
            lines.append(f"current_cpu,{data['system']['current_cpu']},{timestamp}")
            lines.append(f"current_memory,{data['system']['current_memory']},{timestamp}")
            
            return '\n'.join(lines)
        else:
            return str(data)

def monitor_performance(f):
    """성능 모니터링 데코레이터"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        start_time = time.time()
        endpoint = getattr(f, '__name__', 'unknown')
        error_occurred = False
        
        try:
            result = f(*args, **kwargs)
            return result
        except Exception as e:
            error_occurred = True
            raise
        finally:
            response_time = time.time() - start_time
            
            # Flask 앱에서 모니터 인스턴스 가져오기
            try:
                from flask import current_app
                if hasattr(current_app, 'extensions') and 'performance_monitor' in current_app.extensions:
                    monitor = current_app.extensions['performance_monitor']
                    monitor.stats.add_request(endpoint, response_time, error_occurred)
            except Exception:
                pass  # Flask context가 없거나 모니터가 없는 경우 무시
    
    return decorated_function

def init_monitoring(app=None, auto_start: bool = True, **kwargs) -> PerformanceMonitor:
    """모니터링 시스템 초기화"""
    monitor = PerformanceMonitor(app=app, auto_start=auto_start, **kwargs)
    return monitor
