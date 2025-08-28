"""
LottoPro AI v2.0 - 실시간 모니터링 시스템
투명성과 성능을 실시간으로 모니터링하고 리포팅하는 시스템
"""

import time
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from collections import deque
import threading
from flask import Flask, jsonify, request
import requests
import sqlite3
import os

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class MetricPoint:
    """메트릭 데이터 포인트"""
    timestamp: str
    metric_name: str
    value: float
    metadata: Dict[str, Any] = None

@dataclass
class AlertCondition:
    """알람 조건"""
    metric_name: str
    threshold: float
    operator: str  # 'gt', 'lt', 'eq'
    severity: str  # 'low', 'medium', 'high', 'critical'
    message: str

class MetricsCollector:
    """메트릭 수집기"""
    
    def __init__(self, app_url: str = "http://localhost:5000"):
        self.app_url = app_url
        self.metrics_buffer = deque(maxlen=1000)  # 최근 1000개 메트릭 보관
        self.collection_interval = 30  # 30초마다 수집
        self.is_running = False
        self.collection_thread = None
        
    def start_collection(self):
        """메트릭 수집 시작"""
        if self.is_running:
            return
            
        self.is_running = True
        self.collection_thread = threading.Thread(target=self._collection_loop)
        self.collection_thread.daemon = True
        self.collection_thread.start()
        logger.info("메트릭 수집 시작됨")
        
    def stop_collection(self):
        """메트릭 수집 중지"""
        self.is_running = False
        if self.collection_thread:
            self.collection_thread.join()
        logger.info("메트릭 수집 중지됨")
        
    def _collection_loop(self):
        """메트릭 수집 루프"""
        while self.is_running:
            try:
                self._collect_performance_metrics()
                self._collect_transparency_metrics()
                self._collect_system_metrics()
                time.sleep(self.collection_interval)
            except Exception as e:
                logger.error(f"메트릭 수집 중 오류: {e}")
                time.sleep(5)  # 오류 시 잠시 대기
                
    def _collect_performance_metrics(self):
        """성능 메트릭 수집"""
        try:
            # AI 모델 성능 메트릭
            response = requests.get(f"{self.app_url}/api/model_performance/combined", timeout=10)
            if response.status_code == 200:
                data = response.json()
                
                metrics = [
                    MetricPoint(
                        timestamp=datetime.now().isoformat(),
                        metric_name="accuracy_rate",
                        value=data.get('accuracy_rate', 0),
                        metadata={'model': 'combined'}
                    ),
                    MetricPoint(
                        timestamp=datetime.now().isoformat(),
                        metric_name="performance_vs_random",
                        value=data.get('performance_vs_random', 0),
                        metadata={'model': 'combined'}
                    )
                ]
                
                for metric in metrics:
                    self.metrics_buffer.append(metric)
                    
        except Exception as e:
            logger.error(f"성능 메트릭 수집 실패: {e}")
            
    def _collect_transparency_metrics(self):
        """투명성 메트릭 수집"""
        try:
            response = requests.get(f"{self.app_url}/api/transparency_report", timeout=10)
            if response.status_code == 200:
                data = response.json()
                
                metric = MetricPoint(
                    timestamp=datetime.now().isoformat(),
                    metric_name="transparency_score",
                    value=data.get('data_completeness', 0),
                    metadata={'report_type': 'transparency'}
                )
                
                self.metrics_buffer.append(metric)
                
        except Exception as e:
            logger.error(f"투명성 메트릭 수집 실패: {e}")
            
    def _collect_system_metrics(self):
        """시스템 메트릭 수집"""
        try:
            # 응답 시간 측정
            start_time = time.time()
            response = requests.get(f"{self.app_url}/", timeout=10)
            response_time = (time.time() - start_time) * 1000  # ms
            
            metrics = [
                MetricPoint(
                    timestamp=datetime.now().isoformat(),
                    metric_name="response_time_ms",
                    value=response_time,
                    metadata={'endpoint': '/'}
                ),
                MetricPoint(
                    timestamp=datetime.now().isoformat(),
                    metric_name="http_status",
                    value=response.status_code,
                    metadata={'endpoint': '/'}
                )
            ]
            
            for metric in metrics:
                self.metrics_buffer.append(metric)
                
        except Exception as e:
            logger.error(f"시스템 메트릭 수집 실패: {e}")
            
    def get_recent_metrics(self, metric_name: str = None, limit: int = 100) -> List[MetricPoint]:
        """최근 메트릭 조회"""
        metrics = list(self.metrics_buffer)
        
        if metric_name:
            metrics = [m for m in metrics if m.metric_name == metric_name]
            
        return metrics[-limit:]

class AlertManager:
    """알람 관리자"""
    
    def __init__(self):
        self.alert_conditions = []
        self.alert_history = deque(maxlen=100)
        self.notification_channels = []
        self._setup_default_alerts()
        
    def _setup_default_alerts(self):
        """기본 알람 조건 설정"""
        default_alerts = [
            AlertCondition(
                metric_name="accuracy_rate",
                threshold=5.0,
                operator="lt",
                severity="medium",
                message="AI 예측 정확도가 5% 미만으로 떨어졌습니다"
            ),
            AlertCondition(
                metric_name="response_time_ms",
                threshold=5000.0,
                operator="gt",
                severity="high",
                message="응답 시간이 5초를 초과했습니다"
            ),
            AlertCondition(
                metric_name="transparency_score",
                threshold=70.0,
                operator="lt",
                severity="medium",
                message="투명성 점수가 70점 미만입니다"
            ),
            AlertCondition(
                metric_name="http_status",
                threshold=400.0,
                operator="gt",
                severity="high",
                message="HTTP 오류가 발생했습니다"
            )
        ]
        
        self.alert_conditions.extend(default_alerts)
        
    def check_alerts(self, metrics: List[MetricPoint]) -> List[Dict[str, Any]]:
        """알람 조건 확인"""
        triggered_alerts = []
        
        for metric in metrics:
            for condition in self.alert_conditions:
                if metric.metric_name == condition.metric_name:
                    if self._evaluate_condition(metric.value, condition):
                        alert = {
                            'id': f"alert_{int(time.time())}",
                            'timestamp': metric.timestamp,
                            'metric_name': condition.metric_name,
                            'metric_value': metric.value,
                            'condition': asdict(condition),
                            'severity': condition.severity,
                            'message': condition.message
                        }
                        
                        triggered_alerts.append(alert)
                        self.alert_history.append(alert)
                        
        return triggered_alerts
        
    def _evaluate_condition(self, value: float, condition: AlertCondition) -> bool:
        """조건 평가"""
        if condition.operator == "gt":
            return value > condition.threshold
        elif condition.operator == "lt":
            return value < condition.threshold
        elif condition.operator == "eq":
            return abs(value - condition.threshold) < 0.001
        else:
            return False
            
    def get_alert_summary(self) -> Dict[str, Any]:
        """알람 요약 정보"""
        recent_alerts = [a for a in self.alert_history 
                        if datetime.fromisoformat(a['timestamp']) > datetime.now() - timedelta(hours=24)]
        
        severity_counts = {}
        for alert in recent_alerts:
            severity = alert['severity']
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
            
        return {
            'total_alerts_24h': len(recent_alerts),
            'severity_breakdown': severity_counts,
            'latest_alert': self.alert_history[-1] if self.alert_history else None,
            'active_conditions': len(self.alert_conditions)
        }

class DatabaseManager:
    """데이터베이스 관리자"""
    
    def __init__(self, db_path: str = "monitoring.db"):
        self.db_path = db_path
        self._init_database()
        
    def _init_database(self):
        """데이터베이스 초기화"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 메트릭 테이블
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                metric_name TEXT NOT NULL,
                value REAL NOT NULL,
                metadata TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 알람 테이블
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alert_id TEXT UNIQUE NOT NULL,
                timestamp TEXT NOT NULL,
                metric_name TEXT NOT NULL,
                metric_value REAL NOT NULL,
                severity TEXT NOT NULL,
                message TEXT NOT NULL,
                acknowledged BOOLEAN DEFAULT FALSE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 인덱스 생성
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON metrics(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_metrics_name ON metrics(metric_name)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_alerts_timestamp ON alerts(timestamp)')
        
        conn.commit()
        conn.close()
        
    def store_metrics(self, metrics: List[MetricPoint]):
        """메트릭 저장"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for metric in metrics:
            cursor.execute('''
                INSERT INTO metrics (timestamp, metric_name, value, metadata)
                VALUES (?, ?, ?, ?)
            ''', (
                metric.timestamp,
                metric.metric_name,
                metric.value,
                json.dumps(metric.metadata) if metric.metadata else None
            ))
            
        conn.commit()
        conn.close()
        
    def store_alerts(self, alerts: List[Dict[str, Any]]):
        """알람 저장"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for alert in alerts:
            cursor.execute('''
                INSERT OR IGNORE INTO alerts 
                (alert_id, timestamp, metric_name, metric_value, severity, message)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                alert['id'],
                alert['timestamp'],
                alert['metric_name'],
                alert['metric_value'],
                alert['severity'],
                alert['message']
            ))
            
        conn.commit()
        conn.close()
        
    def get_metrics_history(self, metric_name: str = None, 
                           hours: int = 24, limit: int = 1000) -> List[Dict[str, Any]]:
        """메트릭 히스토리 조회"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        since_time = (datetime.now() - timedelta(hours=hours)).isoformat()
        
        if metric_name:
            cursor.execute('''
                SELECT timestamp, metric_name, value, metadata 
                FROM metrics 
                WHERE metric_name = ? AND timestamp >= ?
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (metric_name, since_time, limit))
        else:
            cursor.execute('''
                SELECT timestamp, metric_name, value, metadata 
                FROM metrics 
                WHERE timestamp >= ?
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (since_time, limit))
            
        results = []
        for row in cursor.fetchall():
            results.append({
                'timestamp': row[0],
                'metric_name': row[1],
                'value': row[2],
                'metadata': json.loads(row[3]) if row[3] else None
            })
            
        conn.close()
        return results

class MonitoringAPI:
    """모니터링 API 서버"""
    
    def __init__(self, app_url: str = "http://localhost:5000"):
        self.app = Flask(__name__)
        self.metrics_collector = MetricsCollector(app_url)
        self.alert_manager = AlertManager()
        self.db_manager = DatabaseManager()
        self._setup_routes()
        
    def _setup_routes(self):
        """API 라우트 설정"""
        
        @self.app.route('/monitoring/health')
        def health_check():
            """헬스 체크"""
            return jsonify({
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'collector_running': self.metrics_collector.is_running
            })
            
        @self.app.route('/monitoring/metrics')
        def get_metrics():
            """메트릭 조회"""
            metric_name = request.args.get('metric_name')
            limit = int(request.args.get('limit', 100))
            hours = int(request.args.get('hours', 1))
            
            # 메모리에서 최근 데이터 조회
            recent_metrics = self.metrics_collector.get_recent_metrics(metric_name, limit)
            
            # 데이터베이스에서 히스토리 조회
            historical_metrics = self.db_manager.get_metrics_history(metric_name, hours, limit)
            
            return jsonify({
                'recent_metrics': [asdict(m) for m in recent_metrics],
                'historical_metrics': historical_metrics,
                'total_count': len(recent_metrics) + len(historical_metrics)
            })
            
        @self.app.route('/monitoring/alerts')
        def get_alerts():
            """알람 조회"""
            summary = self.alert_manager.get_alert_summary()
            return jsonify(summary)
            
        @self.app.route('/monitoring/dashboard')
        def get_dashboard():
            """대시보드 데이터"""
            # 핵심 메트릭 수집
            accuracy_metrics = self.metrics_collector.get_recent_metrics('accuracy_rate', 10)
            response_time_metrics = self.metrics_collector.get_recent_metrics('response_time_ms', 10)
            
            # 평균 계산
            avg_accuracy = sum(m.value for m in accuracy_metrics) / len(accuracy_metrics) if accuracy_metrics else 0
            avg_response_time = sum(m.value for m in response_time_metrics) / len(response_time_metrics) if response_time_metrics else 0
            
            # 알람 요약
            alert_summary = self.alert_manager.get_alert_summary()
            
            return jsonify({
                'summary': {
                    'avg_accuracy_rate': round(avg_accuracy, 2),
                    'avg_response_time_ms': round(avg_response_time, 1),
                    'total_alerts_24h': alert_summary['total_alerts_24h'],
                    'system_status': 'healthy' if avg_response_time < 2000 else 'degraded'
                },
                'metrics': {
                    'accuracy_trend': [asdict(m) for m in accuracy_metrics],
                    'response_time_trend': [asdict(m) for m in response_time_metrics]
                },
                'alerts': alert_summary
            })
            
        @self.app.route('/monitoring/transparency')
        def get_transparency_status():
            """투명성 상태"""
            transparency_metrics = self.metrics_collector.get_recent_metrics('transparency_score', 1)
            
            current_score = transparency_metrics[-1].value if transparency_metrics else 0
            
            return jsonify({
                'current_transparency_score': current_score,
                'transparency_level': self._get_transparency_level(current_score),
                'last_updated': transparency_metrics[-1].timestamp if transparency_metrics else None,
                'compliance_status': self._get_compliance_status(current_score)
            })
            
        @self.app.route('/monitoring/start', methods=['POST'])
        def start_monitoring():
            """모니터링 시작"""
            self.metrics_collector.start_collection()
            return jsonify({'message': '모니터링이 시작되었습니다'})
            
        @self.app.route('/monitoring/stop', methods=['POST'])
        def stop_monitoring():
            """모니터링 중지"""
            self.metrics_collector.stop_collection()
            return jsonify({'message': '모니터링이 중지되었습니다'})
            
    def _get_transparency_level(self, score: float) -> str:
        """투명성 레벨 결정"""
        if score >= 90:
            return 'Excellent'
        elif score >= 80:
            return 'Good'
        elif score >= 70:
            return 'Acceptable'
        elif score >= 60:
            return 'Needs Improvement'
        else:
            return 'Poor'
            
    def _get_compliance_status(self, score: float) -> str:
        """컴플라이언스 상태"""
        if score >= 80:
            return 'Compliant'
        elif score >= 60:
            return 'Partially Compliant'
        else:
            return 'Non-Compliant'
            
    def start_background_tasks(self):
        """백그라운드 작업 시작"""
        # 메트릭 수집 시작
        self.metrics_collector.start_collection()
        
        # 주기적 데이터베이스 저장 (5분마다)
        def periodic_save():
            while True:
                try:
                    # 메트릭 저장
                    recent_metrics = self.metrics_collector.get_recent_metrics(limit=100)
                    if recent_metrics:
                        self.db_manager.store_metrics(recent_metrics)
                    
                    # 알람 체크
                    alerts = self.alert_manager.check_alerts(recent_metrics)
                    if alerts:
                        self.db_manager.store_alerts(alerts)
                        logger.info(f"{len(alerts)}개의 알람이 트리거되었습니다")
                    
                    time.sleep(300)  # 5분 대기
                except Exception as e:
                    logger.error(f"주기적 저장 중 오류: {e}")
                    time.sleep(60)  # 오류 시 1분 대기
        
        save_thread = threading.Thread(target=periodic_save)
        save_thread.daemon = True
        save_thread.start()
        
    def run(self, host='0.0.0.0', port=5001, debug=False):
        """모니터링 서버 실행"""
        self.start_background_tasks()
        logger.info(f"모니터링 서버가 {host}:{port}에서 시작됩니다")
        self.app.run(host=host, port=port, debug=debug)

# 실행 예제
if __name__ == "__main__":
    # 모니터링 API 서버 시작
    monitor = MonitoringAPI()
    monitor.run(debug=True)
