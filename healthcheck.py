#!/usr/bin/env python3
"""
LottoPro AI v2.0 - 헬스체크 스크립트
Docker 컨테이너 및 시스템 상태 모니터링
"""

import sys
import time
import requests
import sqlite3
import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

class HealthChecker:
    """시스템 헬스체크 클래스"""
    
    def __init__(self):
        self.app_url = os.getenv('APP_URL', 'http://localhost:5000')
        self.timeout = int(os.getenv('HEALTH_TIMEOUT', '10'))
        self.checks = {
            'web_server': self.check_web_server,
            'database': self.check_database,
            'transparency_api': self.check_transparency_api,
            'prediction_api': self.check_prediction_api,
            'disk_space': self.check_disk_space,
            'memory_usage': self.check_memory_usage
        }
        
    def run_all_checks(self) -> Tuple[bool, Dict]:
        """모든 헬스체크 실행"""
        results = {
            'timestamp': datetime.now().isoformat(),
            'overall_status': 'healthy',
            'checks': {},
            'warnings': [],
            'errors': []
        }
        
        all_healthy = True
        
        for check_name, check_func in self.checks.items():
            try:
                start_time = time.time()
                is_healthy, details = check_func()
                execution_time = (time.time() - start_time) * 1000  # ms
                
                results['checks'][check_name] = {
                    'status': 'healthy' if is_healthy else 'unhealthy',
                    'execution_time_ms': round(execution_time, 2),
                    'details': details
                }
                
                if not is_healthy:
                    all_healthy = False
                    results['errors'].append(f"{check_name}: {details.get('error', 'Unknown error')}")
                    
                # 경고 조건 체크
                if execution_time > 5000:  # 5초 이상 소요
                    results['warnings'].append(f"{check_name} response time is slow: {execution_time:.0f}ms")
                    
            except Exception as e:
                all_healthy = False
                results['checks'][check_name] = {
                    'status': 'error',
                    'execution_time_ms': 0,
                    'details': {'error': str(e)}
                }
                results['errors'].append(f"{check_name}: {str(e)}")
        
        results['overall_status'] = 'healthy' if all_healthy else 'unhealthy'
        return all_healthy, results
    
    def check_web_server(self) -> Tuple[bool, Dict]:
        """웹 서버 상태 확인"""
        try:
            response = requests.get(self.app_url, timeout=self.timeout)
            return response.status_code == 200, {
                'status_code': response.status_code,
                'response_time_ms': response.elapsed.total_seconds() * 1000,
                'content_length': len(response.content)
            }
        except requests.exceptions.RequestException as e:
            return False, {'error': str(e)}
    
    def check_database(self) -> Tuple[bool, Dict]:
        """데이터베이스 연결 확인"""
        try:
            db_path = os.getenv('DATABASE_PATH', 'data/lottopro.db')
            
            # 데이터베이스 파일 존재 확인
            if not os.path.exists(db_path):
                return False, {'error': f'Database file not found: {db_path}'}
            
            # 연결 테스트
            conn = sqlite3.connect(db_path, timeout=5)
            cursor = conn.cursor()
            cursor.execute('SELECT 1')
            result = cursor.fetchone()
            conn.close()
            
            return result is not None, {
                'database_file': db_path,
                'file_size_mb': round(os.path.getsize(db_path) / 1024 / 1024, 2),
                'connection_test': 'passed'
            }
        except Exception as e:
            return False, {'error': str(e)}
    
    def check_transparency_api(self) -> Tuple[bool, Dict]:
        """투명성 API 확인"""
        try:
            endpoints = [
                '/api/transparency_report',
                '/api/statistical_analysis',
                '/api/model_performance/combined'
            ]
            
            results = {}
            all_ok = True
            
            for endpoint in endpoints:
                try:
                    response = requests.get(f"{self.app_url}{endpoint}", timeout=self.timeout)
                    results[endpoint] = {
                        'status_code': response.status_code,
                        'response_time_ms': response.elapsed.total_seconds() * 1000
                    }
                    
                    if response.status_code != 200:
                        all_ok = False
                        
                except Exception as e:
                    results[endpoint] = {'error': str(e)}
                    all_ok = False
            
            return all_ok, results
        except Exception as e:
            return False, {'error': str(e)}
    
    def check_prediction_api(self) -> Tuple[bool, Dict]:
        """예측 API 확인"""
        try:
            # 기본 정보 API 테스트
            endpoints = [
                '/api/lottery_info/hotNumbers',
                '/api/lottery_info/coldNumbers',
                '/api/lottery_info/carryover'
            ]
            
            results = {}
            all_ok = True
            
            for endpoint in endpoints:
                try:
                    response = requests.get(f"{self.app_url}{endpoint}", timeout=self.timeout)
                    results[endpoint] = {
                        'status_code': response.status_code,
                        'has_data': len(response.content) > 50  # 최소한의 데이터 있는지 확인
                    }
                    
                    if response.status_code != 200:
                        all_ok = False
                        
                except Exception as e:
                    results[endpoint] = {'error': str(e)}
                    all_ok = False
            
            return all_ok, results
        except Exception as e:
            return False, {'error': str(e)}
    
    def check_disk_space(self) -> Tuple[bool, Dict]:
        """디스크 공간 확인"""
        try:
            import shutil
            
            # 현재 디렉토리의 디스크 사용량 확인
            total, used, free = shutil.disk_usage('.')
            
            total_gb = total / (1024**3)
            used_gb = used / (1024**3)
            free_gb = free / (1024**3)
            usage_percent = (used / total) * 100
            
            # 90% 이상 사용 시 경고
            is_healthy = usage_percent < 90
            
            return is_healthy, {
                'total_gb': round(total_gb, 2),
                'used_gb': round(used_gb, 2),
                'free_gb': round(free_gb, 2),
                'usage_percent': round(usage_percent, 2),
                'threshold_exceeded': usage_percent >= 90
            }
        except Exception as e:
            return False, {'error': str(e)}
    
    def check_memory_usage(self) -> Tuple[bool, Dict]:
        """메모리 사용량 확인"""
        try:
            import psutil
            
            memory = psutil.virtual_memory()
            
            # 95% 이상 사용 시 경고
            is_healthy = memory.percent < 95
            
            return is_healthy, {
                'total_mb': round(memory.total / (1024**2), 2),
                'available_mb': round(memory.available / (1024**2), 2),
                'used_percent': memory.percent,
                'threshold_exceeded': memory.percent >= 95
            }
        except ImportError:
            # psutil이 없는 경우 기본적인 메모리 체크
            try:
                with open('/proc/meminfo', 'r') as f:
                    meminfo = f.read()
                
                # 기본적인 파싱
                lines = meminfo.split('\n')
                memtotal = int([line for line in lines if 'MemTotal' in line][0].split()[1])
                memfree = int([line for line in lines if 'MemFree' in line][0].split()[1])
                
                usage_percent = ((memtotal - memfree) / memtotal) * 100
                is_healthy = usage_percent < 95
                
                return is_healthy, {
                    'total_mb': round(memtotal / 1024, 2),
                    'free_mb': round(memfree / 1024, 2),
                    'used_percent': round(usage_percent, 2),
                    'method': 'proc_meminfo'
                }
            except:
                return True, {'error': 'Unable to check memory usage', 'method': 'unavailable'}
        except Exception as e:
            return False, {'error': str(e)}

def main():
    """메인 헬스체크 실행"""
    checker = HealthChecker()
    is_healthy, results = checker.run_all_checks()
    
    # 결과 출력
    print(json.dumps(results, indent=2))
    
    # Docker 헬스체크용 exit code
    if not is_healthy:
        print("Health check failed!", file=sys.stderr)
        sys.exit(1)
    else:
        print("All health checks passed!")
        sys.exit(0)

if __name__ == "__main__":
    main()
