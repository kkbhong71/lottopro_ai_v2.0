"""
LottoPro-AI 환경 설정 관리
개발/스테이징/프로덕션 환경별 설정 분리
"""

import os
from datetime import timedelta
from typing import Dict, Any

class Config:
    """기본 설정 클래스"""
    
    # Flask 기본 설정
    SECRET_KEY = os.environ.get('SECRET_KEY', 'lottopro-ai-v2-enhanced-2024-default-key')
    PERMANENT_SESSION_LIFETIME = timedelta(days=30)
    
    # 데이터베이스 설정 (미래 확장용)
    DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///lottopro.db')
    
    # Redis 캐시 설정
    REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    CACHE_TYPE = os.environ.get('CACHE_TYPE', 'redis')  # redis, memory
    CACHE_DEFAULT_TIMEOUT = int(os.environ.get('CACHE_DEFAULT_TIMEOUT', 300))
    CACHE_KEY_PREFIX = os.environ.get('CACHE_KEY_PREFIX', 'lottopro:')
    
    # 성능 모니터링 설정
    MONITORING_ENABLED = os.environ.get('MONITORING_ENABLED', 'true').lower() == 'true'
    MONITORING_COLLECTION_INTERVAL = int(os.environ.get('MONITORING_COLLECTION_INTERVAL', 30))
    
    # 성능 임계값 설정
    PERFORMANCE_THRESHOLDS = {
        'response_time': float(os.environ.get('THRESHOLD_RESPONSE_TIME', 10.0)),
        'error_rate': float(os.environ.get('THRESHOLD_ERROR_RATE', 0.05)),
        'cpu_usage': float(os.environ.get('THRESHOLD_CPU_USAGE', 80.0)),
        'memory_usage': float(os.environ.get('THRESHOLD_MEMORY_USAGE', 85.0)),
        'disk_usage': float(os.environ.get('THRESHOLD_DISK_USAGE', 95.0))
    }
    
    # Rate Limiting 설정
    RATE_LIMIT_ENABLED = os.environ.get('RATE_LIMIT_ENABLED', 'true').lower() == 'true'
    RATE_LIMIT_DEFAULT = os.environ.get('RATE_LIMIT_DEFAULT', '100/hour')
    RATE_LIMIT_PREDICT = os.environ.get('RATE_LIMIT_PREDICT', '30/hour')
    RATE_LIMIT_SAVE_NUMBERS = os.environ.get('RATE_LIMIT_SAVE_NUMBERS', '50/hour')
    
    # 로그 설정
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FORMAT = os.environ.get('LOG_FORMAT', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    LOG_TO_FILE = os.environ.get('LOG_TO_FILE', 'false').lower() == 'true'
    LOG_FILE_PATH = os.environ.get('LOG_FILE_PATH', 'logs/lottopro.log')
    LOG_MAX_BYTES = int(os.environ.get('LOG_MAX_BYTES', 10485760))  # 10MB
    LOG_BACKUP_COUNT = int(os.environ.get('LOG_BACKUP_COUNT', 5))
    
    # 보안 설정
    CORS_ENABLED = os.environ.get('CORS_ENABLED', 'true').lower() == 'true'
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '*').split(',')
    SECURE_HEADERS_ENABLED = os.environ.get('SECURE_HEADERS_ENABLED', 'true').lower() == 'true'
    
    # API 설정
    API_VERSION = os.environ.get('API_VERSION', 'v2.1')
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))  # 16MB
    
    # 외부 서비스 설정
    EXTERNAL_API_TIMEOUT = int(os.environ.get('EXTERNAL_API_TIMEOUT', 30))
    USER_AGENT = f"LottoPro-AI/{API_VERSION} (https://lottopro-ai-v2-0.onrender.com)"
    
    # 데이터 설정
    SAMPLE_DATA_SIZE = int(os.environ.get('SAMPLE_DATA_SIZE', 200))
    MAX_SAVED_NUMBERS_PER_USER = int(os.environ.get('MAX_SAVED_NUMBERS_PER_USER', 50))
    
    # AI 예측 설정
    AI_PREDICTION_CACHE_TTL = int(os.environ.get('AI_PREDICTION_CACHE_TTL', 300))  # 5분
    AI_STATS_CACHE_TTL = int(os.environ.get('AI_STATS_CACHE_TTL', 600))  # 10분
    AI_MODEL_WEIGHTS_UPDATE_INTERVAL = int(os.environ.get('AI_MODEL_WEIGHTS_UPDATE_INTERVAL', 3600))  # 1시간
    
    # 시뮬레이션 설정
    MAX_SIMULATION_ROUNDS = int(os.environ.get('MAX_SIMULATION_ROUNDS', 50000))
    SIMULATION_TIMEOUT = int(os.environ.get('SIMULATION_TIMEOUT', 20))
    
    # 관리자 API 설정
    ADMIN_API_ENABLED = os.environ.get('ADMIN_API_ENABLED', 'true').lower() == 'true'
    ADMIN_API_KEY = os.environ.get('ADMIN_API_KEY')  # 설정 시에만 활성화
    
    @classmethod
    def get_redis_config(cls) -> Dict[str, Any]:
        """Redis 설정 반환"""
        return {
            'url': cls.REDIS_URL,
            'default_ttl': cls.CACHE_DEFAULT_TIMEOUT,
            'key_prefix': cls.CACHE_KEY_PREFIX,
            'max_connections': int(os.environ.get('REDIS_MAX_CONNECTIONS', 20)),
            'socket_timeout': int(os.environ.get('REDIS_SOCKET_TIMEOUT', 5)),
            'socket_connect_timeout': int(os.environ.get('REDIS_SOCKET_CONNECT_TIMEOUT', 5)),
            'retry_on_timeout': os.environ.get('REDIS_RETRY_ON_TIMEOUT', 'true').lower() == 'true'
        }
    
    @classmethod
    def get_monitoring_config(cls) -> Dict[str, Any]:
        """모니터링 설정 반환"""
        return {
            'enabled': cls.MONITORING_ENABLED,
            'collection_interval': cls.MONITORING_COLLECTION_INTERVAL,
            'thresholds': cls.PERFORMANCE_THRESHOLDS,
            'auto_start': os.environ.get('MONITORING_AUTO_START', 'true').lower() == 'true',
            'alert_enabled': os.environ.get('MONITORING_ALERT_ENABLED', 'true').lower() == 'true'
        }
    
    @classmethod
    def get_cache_config(cls) -> Dict[str, Any]:
        """캐시 설정 반환"""
        return {
            'type': cls.CACHE_TYPE,
            'default_ttl': cls.CACHE_DEFAULT_TIMEOUT,
            'memory_cache_size': int(os.environ.get('MEMORY_CACHE_SIZE', 1000)),
            'enable_compression': os.environ.get('CACHE_COMPRESSION', 'true').lower() == 'true',
            'enable_warming': os.environ.get('CACHE_WARMING', 'true').lower() == 'true'
        }

class DevelopmentConfig(Config):
    """개발 환경 설정"""
    
    DEBUG = True
    TESTING = False
    
    # 개발용 낮은 임계값
    PERFORMANCE_THRESHOLDS = {
        'response_time': 15.0,
        'error_rate': 0.1,
        'cpu_usage': 90.0,
        'memory_usage': 90.0,
        'disk_usage': 98.0
    }
    
    # 개발용 관대한 Rate Limit
    RATE_LIMIT_DEFAULT = '1000/hour'
    RATE_LIMIT_PREDICT = '100/hour'
    RATE_LIMIT_SAVE_NUMBERS = '200/hour'
    
    # 로그 레벨
    LOG_LEVEL = 'DEBUG'
    LOG_TO_FILE = True
    
    # 개발용 Redis (로컬)
    REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/1')
    
    # CORS 설정 (개발용)
    CORS_ORIGINS = ['http://localhost:3000', 'http://localhost:5000', 'http://127.0.0.1:5000']

class TestingConfig(Config):
    """테스트 환경 설정"""
    
    DEBUG = True
    TESTING = True
    
    # 테스트용 메모리 캐시
    CACHE_TYPE = 'memory'
    REDIS_URL = 'redis://localhost:6379/2'
    
    # 테스트용 빠른 설정
    CACHE_DEFAULT_TIMEOUT = 10
    AI_PREDICTION_CACHE_TTL = 10
    AI_STATS_CACHE_TTL = 10
    
    # 모니터링 비활성화
    MONITORING_ENABLED = False
    
    # Rate Limit 비활성화
    RATE_LIMIT_ENABLED = False
    
    # 로그 최소화
    LOG_LEVEL = 'WARNING'
    LOG_TO_FILE = False
    
    # 테스트용 작은 데이터 크기
    SAMPLE_DATA_SIZE = 50
    MAX_SIMULATION_ROUNDS = 1000

class StagingConfig(Config):
    """스테이징 환경 설정"""
    
    DEBUG = False
    TESTING = False
    
    # 프로덕션과 유사하지만 약간 관대한 설정
    PERFORMANCE_THRESHOLDS = {
        'response_time': 12.0,
        'error_rate': 0.08,
        'cpu_usage': 85.0,
        'memory_usage': 88.0,
        'disk_usage': 95.0
    }
    
    # 스테이징용 Redis
    REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/3')
    
    # 로그 설정
    LOG_LEVEL = 'INFO'
    LOG_TO_FILE = True
    
    # CORS 설정
    CORS_ORIGINS = ['https://lottopro-staging.example.com']

class ProductionConfig(Config):
    """프로덕션 환경 설정"""
    
    DEBUG = False
    TESTING = False
    
    # 보안 강화
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SECURE_HEADERS_ENABLED = True
    
    # 엄격한 성능 임계값
    PERFORMANCE_THRESHOLDS = {
        'response_time': 8.0,
        'error_rate': 0.03,
        'cpu_usage': 75.0,
        'memory_usage': 80.0,
        'disk_usage': 90.0
    }
    
    # 엄격한 Rate Limit
    RATE_LIMIT_DEFAULT = '50/hour'
    RATE_LIMIT_PREDICT = '20/hour'
    RATE_LIMIT_SAVE_NUMBERS = '30/hour'
    
    # 로그 설정
    LOG_LEVEL = 'WARNING'
    LOG_TO_FILE = True
    
    # 압축 및 최적화
    CACHE_COMPRESSION = True
    
    # CORS 설정 (실제 도메인)
    CORS_ORIGINS = ['https://lottopro-ai-v2-0.onrender.com']
    
    # 관리자 API 보안
    ADMIN_API_ENABLED = bool(os.environ.get('ADMIN_API_KEY'))

# 환경별 설정 매핑
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'staging': StagingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

def get_config(config_name: str = None) -> Config:
    """환경 설정 반환"""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    return config.get(config_name, config['default'])

def validate_config(config_obj: Config) -> list:
    """설정 유효성 검사"""
    errors = []
    
    # 필수 환경 변수 확인
    required_vars = ['SECRET_KEY']
    for var in required_vars:
        if not getattr(config_obj, var) or getattr(config_obj, var) == f'lottopro-ai-v2-enhanced-2024-default-key':
            errors.append(f"Missing or default {var}")
    
    # Redis URL 형식 확인
    redis_url = config_obj.REDIS_URL
    if redis_url and not (redis_url.startswith('redis://') or redis_url.startswith('rediss://')):
        errors.append("Invalid Redis URL format")
    
    # 성능 임계값 유효성 확인
    thresholds = config_obj.PERFORMANCE_THRESHOLDS
    if thresholds['response_time'] <= 0:
        errors.append("Response time threshold must be positive")
    
    if not 0 <= thresholds['error_rate'] <= 1:
        errors.append("Error rate threshold must be between 0 and 1")
    
    for usage_key in ['cpu_usage', 'memory_usage', 'disk_usage']:
        if not 0 <= thresholds[usage_key] <= 100:
            errors.append(f"{usage_key} threshold must be between 0 and 100")
    
    return errors

def print_config_summary(config_obj: Config):
    """설정 요약 출력"""
    print("=== LottoPro-AI Configuration Summary ===")
    print(f"Environment: {os.environ.get('FLASK_ENV', 'development')}")
    print(f"Debug Mode: {config_obj.DEBUG}")
    print(f"Redis URL: {config_obj.REDIS_URL}")
    print(f"Cache Type: {config_obj.CACHE_TYPE}")
    print(f"Monitoring Enabled: {config_obj.MONITORING_ENABLED}")
    print(f"Rate Limiting Enabled: {config_obj.RATE_LIMIT_ENABLED}")
    print(f"Admin API Enabled: {config_obj.ADMIN_API_ENABLED}")
    print(f"Log Level: {config_obj.LOG_LEVEL}")
    print("==========================================")

if __name__ == '__main__':
    # 설정 테스트
    config_name = os.environ.get('FLASK_ENV', 'development')
    config_obj = get_config(config_name)
    
    print_config_summary(config_obj)
    
    errors = validate_config(config_obj)
    if errors:
        print("Configuration Errors:")
        for error in errors:
            print(f"- {error}")
    else:
        print("Configuration validation passed!")
