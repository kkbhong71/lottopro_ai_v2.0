#!/usr/bin/env python3
"""
LottoPro-AI 헬스체크 스크립트
Docker 컨테이너 및 시스템 상태 확인
"""

import os
import sys
import time
import json
import requests
import subprocess
from datetime import datetime
from typing import Dict, List, Tuple, Optional

class HealthChecker:
    """종합 헬스체크 클래스"""
    
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url
        self.timeout = 10
        self.critical_checks = []
        self.warning_checks = []
        self.info_checks = []
        
    def check_web_service(self) -> Tuple[bool, str]:
        """웹 서비스 상태 확인"""
        try:
            response = requests.get(
                f"{self.base_url}/api/health",
                timeout=self.timeout,
                headers={'User-Agent': 'HealthCheck/1.0'}
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'healthy':
                    return True, f"Web service healthy - Version: {data.get('version', 'unknown')}"
                else:
                    return False, f"Web service unhealthy: {data.get('error', 'unknown error')}"
            else:
                return False, f"Web service returned status {response.status_code}"
                
        except requests.exceptions.ConnectinError:
            return False, "Cannot connect to web service"
        except requests.exceptions.Timeout:
            return False, "Web service health check timed out"
        except Exception as e:
            return False, f"Web service health check failed: {str(e)}"
    
    def check_redis_connection(self) -> Tuple[bool, str]:
        """Redis 연결 상태 확인"""
        try:
            import redis
            
            redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
            client = redis.from_url(redis_url, socket_timeout=5)
            
            # 연결 테스트
            client.ping()
            
            # 기본 명령 테스트
            test_key = 'healthcheck:test'
            client.set(test_key, 'test_value', ex=10)
            value = client.get(test_key)
            client.delete(test_key)
            
            if value == b'test_value':
                # Redis 정보 수집
                info = client.info()
                version = info.get('redis_version', 'unknown')
                memory_usage = info.get('used_memory_human', 'unknown')
                connected_clients = info.get('connected_clients', 0)
                
                return True, f"Redis healthy - Version: {version}, Memory: {memory_usage}, Clients: {connected_clients}"
            else:
                return False, "Redis read/write test failed"
                
        except ImportError:
            return False, "Redis client not available (redis package not installed)"
        except redis.exceptions.ConnectionError:
            return False, "Cannot connect to Redis server"
        except redis.exceptions.TimeoutError:
            return False, "Redis connection timed out"
        except Exception as e:
            return False, f"Redis health check failed: {str(e)}"
    
    def check_system_resources(self) -> Tuple[bool, str]:
        """시스템 리소스 상태 확인"""
        try:
            import psutil
            
            # CPU 사용률
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # 메모리 사용률
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # 디스크 사용률
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            
            # 프로세스 수
            process_count = len(psutil.pids())
            
            # 임계값 확인
            warnings = []
            if cpu_percent > 90:
                warnings.append(f"High CPU usage: {cpu_percent:.1f}%")
            if memory_percent > 90:
                warnings.append(f"High memory usage: {memory_percent:.1f}%")
            if disk_percent > 95:
                warnings.append(f"High disk usage: {disk_percent:.1f}%")
            
            status_msg = f"CPU: {cpu_percent:.1f}%, Memory: {memory_percent:.1f}%, Disk: {disk_percent:.1f}%, Processes: {process_count}"
            
            if warnings:
                return False, f"System resources warning - {status_msg} | Issues: {'; '.join(warnings)}"
            else:
                return True, f"System resources healthy - {status_msg}"
                
        except ImportError:
            return False, "System resource monitoring not available (psutil package not installed)"
        except Exception as e:
            return False, f"System resource check failed: {str(e)}"
    
    def check_disk_space(self, min_free_gb: float = 1.0) -> Tuple[bool, str]:
        """디스크 여유 공간 확인"""
        try:
            import shutil
            
            # 현재 디렉토리 디스크 사용량 확인
            total, used, free = shutil.disk_usage('.')
            
            free_gb = free / (1024**3)  # GB로 변환
            total_gb = total / (1024**3)
            used_percent = (used / total) * 100
            
            if free_gb < min_free_gb:
                return False, f"Low disk space: {free_gb:.2f}GB free ({used_percent:.1f}% used)"
            else:
                return True, f"Disk space healthy: {free_gb:.2f}GB free of {total_gb:.2f}GB ({used_percent:.1f}% used)"
                
        except Exception as e:
            return False, f"Disk space check failed: {str(e)}"
    
    def check_required_directories(self) -> Tuple[bool, str]:
        """필수 디렉토리 존재 확인"""
        required_dirs = ['logs', 'data', 'static', 'templates']
        missing_dirs = []
        
        for dir_name in required_dirs:
            if not os.path.exists(dir_name):
                missing_dirs.append(dir_name)
        
        if missing_dirs:
            return False, f"Missing required directories: {', '.join(missing_dirs)}"
        else:
            return True, f"All required directories present: {', '.join(required_dirs)}"
    
    def check_python_dependencies(self) -> Tuple[bool, str]:
        """Python 패키지 의존성 확인"""
        required_packages = {
            'flask': 'Flask web framework',
            'numpy': 'Numerical computing',
            'redis': 'Redis cache client',
            'psutil': 'System monitoring',
            'requests': 'HTTP client'
        }
        
        missing_packages = []
        available_packages = []
        
        for package, description in required_packages.items():
            try:
                __import__(package)
                available_packages.append(package)
            except ImportError:
                missing_packages.append(f"{package} ({description})")
        
        if missing_packages:
            return False, f"Missing packages: {', '.join(missing_packages)}"
        else:
            return True, f"All required packages available: {', '.join(available_packages)}"
    
    def check_environment_variables(self) -> Tuple[bool, str]:
        """중요 환경 변수 확인"""
        required_vars = ['SECRET_KEY', 'FLASK_ENV']
        recommended_vars = ['REDIS_URL', 'LOG_LEVEL']
        
        missing_required = []
        missing_recommended = []
        
        for var in required_vars:
            if not os.environ.get(var):
                missing_required.append(var)
        
        for var in recommended_vars:
            if not os.environ.get(var):
                missing_recommended.append(var)
        
        if missing_required:
            return False, f"Missing required environment variables: {', '.join(missing_required)}"
        
        messages = []
        if missing_recommended:
            messages.append(f"Missing recommended vars: {', '.join(missing_recommended)}")
        
        env_info = f"Environment: {os.environ.get('FLASK_ENV', 'unknown')}"
        if messages:
            return True, f"Environment variables OK - {env_info} | {'; '.join(messages)}"
        else:
            return True, f"Environment variables OK - {env_info}"
    
    def check_network_connectivity(self) -> Tuple[bool, str]:
        """네트워크 연결성 확인"""
        try:
            # 로컬 서비스 포트 확인
            import socket
            
            def check_port(host: str, port: int, timeout: int = 3) -> bool:
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(timeout)
                    result = sock.connect_ex((host, port))
                    sock.close()
                    return result == 0
                except Exception:
                    return False
            
            checks = []
            
            # 웹 서비스 포트 (5000)
            if check_port('localhost', 5000):
                checks.append("Web:5000✓")
            else:
                checks.append("Web:5000✗")
            
            # Redis 포트 (6379)
            redis_host = os.environ.get('REDIS_URL', 'redis://localhost:6379').split('//')[1].split(':')[0]
            if check_port(redis_host, 6379):
                checks.append("Redis:6379✓")
            else:
                checks.append("Redis:6379✗")
            
            # 외부 인터넷 연결 확인
            try:
                response = requests.get('https://httpbin.org/ip', timeout=5)
                if response.status_code == 200:
                    checks.append("Internet✓")
                else:
                    checks.append("Internet✗")
            except:
                checks.append("Internet✗")
            
            failed_checks = [check for check in checks if '✗' in check]
            
            if failed_checks:
                return False, f"Network connectivity issues: {', '.join(checks)}"
            else:
                return True, f"Network connectivity healthy: {', '.join(checks)}"
                
        except Exception as e:
            return False, f"Network connectivity check failed: {str(e)}"
    
    def check_log_files(self) -> Tuple[bool, str]:
        """로그 파일 상태 확인"""
        try:
            log_dir = 'logs'
            if not os.path.exists(log_dir):
                return False, "Log directory does not exist"
            
            log_files = []
            total_size = 0
            
            for filename in os.listdir(log_dir):
                if filename.endswith('.log'):
                    filepath = os.path.join(log_dir, filename)
                    file_size = os.path.getsize(filepath)
                    total_size += file_size
                    
                    # 파일이 최근에 수정되었는지 확인
                    mtime = os.path.getmtime(filepath)
                    age_hours = (time.time() - mtime) / 3600
                    
                    log_files.append({
                        'name': filename,
                        'size_mb': file_size / (1024*1024),
                        'age_hours': age_hours
                    })
            
            if not log_files:
                return True, "No log files present (normal for new installation)"
            
            # 로그 파일 크기 경고
            large_files = [f for f in log_files if f['size_mb'] > 100]
            old_files = [f for f in log_files if f['age_hours'] > 24]
            
            warnings = []
            if large_files:
                warnings.append(f"{len(large_files)} large files (>100MB)")
            if old_files:
                warnings.append(f"{len(old_files)} old files (>24h)")
            
            total_size_mb = total_size / (1024*1024)
            status_msg = f"{len(log_files)} log files, {total_size_mb:.1f}MB total"
            
            if warnings:
                return True, f"Log files OK - {status_msg} | Warnings: {'; '.join(warnings)}"
            else:
                return True, f"Log files healthy - {status_msg}"
                
        except Exception as e:
            return False, f"Log file check failed: {str(e)}"
    
    def run_all_checks(self) -> Dict:
        """모든 헬스체크 실행"""
        checks = [
            ("Web Service", self.check_web_service, "critical"),
            ("Redis Connection", self.check_redis_connection, "critical"),
            ("System Resources", self.check_system_resources, "warning"),
            ("Disk Space", self.check_disk_space, "warning"),
            ("Required Directories", self.check_required_directories, "critical"),
            ("Python Dependencies", self.check_python_dependencies, "critical"),
            ("Environment Variables", self.check_environment_variables, "warning"),
            ("Network Connectivity", self.check_network_connectivity, "info"),
            ("Log Files", self.check_log_files, "info")
        ]
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'overall_status': 'healthy',
            'critical_failures': 0,
            'warnings': 0,
            'checks': []
        }
        
        for name, check_func, severity in checks:
            try:
                success, message = check_func()
                
                check_result = {
                    'name': name,
                    'status': 'pass' if success else 'fail',
                    'message': message,
                    'severity': severity
                }
                
                results['checks'].append(check_result)
                
                if not success:
                    if severity == 'critical':
                        results['critical_failures'] += 1
                    elif severity == 'warning':
                        results['warnings'] += 1
                        
            except Exception as e:
                results['checks'].append({
                    'name': name,
                    'status': 'error',
                    'message': f"Check failed: {str(e)}",
                    'severity': severity
                })
                
                if severity == 'critical':
                    results['critical_failures'] += 1
                elif severity == 'warning':
                    results['warnings'] += 1
        
        # 전체 상태 결정
        if results['critical_failures'] > 0:
            results['overall_status'] = 'unhealthy'
        elif results['warnings'] > 0:
            results['overall_status'] = 'degraded'
        
        return results

def main():
    """메인 헬스체크 실행"""
    print("🔍 LottoPro-AI Health Check Starting...")
    print("=" * 50)
    
    # 헬스체커 초기화
    base_url = os.environ.get('HEALTH_CHECK_URL', 'http://localhost:5000')
    checker = HealthChecker(base_url)
    
    # 모든 체크 실행
    results = checker.run_all_checks()
    
    # 결과 출력
    print(f"Timestamp: {results['timestamp']}")
    print(f"Overall Status: {results['overall_status'].upper()}")
    print("-" * 50)
    
    for check in results['checks']:
        status_icon = "✅" if check['status'] == 'pass' else "❌" if check['status'] == 'fail' else "⚠️"
        severity_label = f"[{check['severity'].upper()}]"
        print(f"{status_icon} {check['name']} {severity_label}")
        print(f"   {check['message']}")
    
    print("-" * 50)
    print(f"Summary: {results['critical_failures']} critical failures, {results['warnings']} warnings")
    
    # JSON 출력 (로그 파일용)
    if os.environ.get('HEALTH_CHECK_JSON_OUTPUT'):
        print("\nJSON Output:")
        print(json.dumps(results, indent=2))
    
    # Docker 헬스체크를 위한 종료 코드
    if results['overall_status'] == 'unhealthy':
        print("❌ Health check FAILED")
        sys.exit(1)
    elif results['overall_status'] == 'degraded':
        print("⚠️ Health check DEGRADED")
        if os.environ.get('STRICT_HEALTH_CHECK', 'false').lower() == 'true':
            sys.exit(1)
        else:
            sys.exit(0)  # 경고는 성공으로 처리
    else:
        print("✅ Health check PASSED")
        sys.exit(0)

if __name__ == '__main__':
    main()
