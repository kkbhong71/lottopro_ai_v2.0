"""
LottoPro AI v2.0 - 애플리케이션 설정
환경별 설정 클래스와 투명성 관련 설정
"""

import os
from datetime import timedelta
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

class Config:
    """기본 설정 클래스"""
    
    # === 기본 Flask 설정 ===
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # === 데이터베이스 설정 ===
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///data/lottopro.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_POOL_SIZE = int(os.environ.get('DATABASE_POOL_SIZE', 10))
    SQLALCHEMY_POOL_TIMEOUT = int(os.environ.get('DATABASE_POOL_TIMEOUT', 30))
    
    # === 투명성 및 컴플라이언스 설정 ===
    TRANSPARENCY_MODE = os.environ.get('TRANSPARENCY_MODE', 'enabled').lower() == 'enabled'
    DATA_RETENTION_DAYS = int(os.environ.get('DATA_RETENTION_DAYS', 365))
    AUDIT_LOG_ENABLED = os.environ.get('AUDIT_LOG_ENABLED', 'true').lower() == 'true'
    STATISTICAL_VALIDATION = os.environ.get('STATISTICAL_VALIDATION', 'strict')
    
    # === 보안 설정 ===
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'true').lower() == 'true'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_PERMANENT = False
    PERMANENT_SESSION_LIFETIME = timedelta(hours=1)
    WTF_CSRF_ENABLED = os.environ.get('WTF_CSRF_ENABLED', 'true').lower() == 'true'
    
    # === Rate Limiting 설정 ===
    RATELIMIT_STORAGE_URL = os.environ.get('RATELIMIT_STORAGE_URL', 'memory://')
    RATELIMIT_DEFAULT = os.environ.get('RATELIMIT_DEFAULT', '100 per hour')
    RATELIMIT_API = os.environ.get('RATELIMIT_API', '50 per hour')
    
    # === 캐시 설정 ===
    CACHE_TYPE = os.environ.get('CACHE_TYPE', 'simple')
    CACHE_REDIS_URL = os.environ.get('CACHE_REDIS_URL', 'redis://localhost:6379/1')
    CACHE_DEFAULT_TIMEOUT = int(os.environ.get('CACHE_DEFAULT_TIMEOUT', 300))
    
    # === 로깅 설정 ===
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = os.environ.get('LOG_FILE', 'logs/lottopro.log')
    LOG_MAX_BYTES = int(os.environ.get('LOG_MAX_BYTES', 10485760))  # 10MB
    LOG_BACKUP_COUNT = int(os.environ.get('LOG_BACKUP_COUNT', 5))
    
    # === 모니터링 설정 ===
    MONITORING_ENABLED = os.environ.get('MONITORING_ENABLED', 'true').lower() == 'true'
    MONITORING_PORT = int(os.environ.get('MONITORING_PORT', 5001))
    PROMETHEUS_METRICS = os.environ.get('PROMETHEUS_METRICS', 'true').lower() == 'true'
    HEALTH_CHECK_INTERVAL = int(os.environ.get('HEALTH_CHECK_INTERVAL', 30))
    
    # === AI 모델 설정 ===
    MODEL_UPDATE_INTERVAL = os.environ.get('MODEL_UPDATE_INTERVAL', 'weekly')
    PREDICTION_HISTORY_LIMIT = int(os.environ.get('PREDICTION_HISTORY_LIMIT', 1000))
    STATISTICAL_SIGNIFICANCE_LEVEL = float(os.environ.get('STATISTICAL_SIGNIFICANCE_LEVEL', 0.05))
    
    # === 외부 서비스 설정 ===
    LOTTERY_DATA_SOURCE = os.environ.get('LOTTERY_DATA_SOURCE', 'manual')
    DATA_UPDATE_SCHEDULE = os.environ.get('DATA_UPDATE_SCHEDULE', '0 2 * * 6')
    
    # === 법적 준수 설정 ===
    AGE_VERIFICATION_REQUIRED = os.environ.get('AGE_VERIFICATION_REQUIRED', 'true').lower() == 'true'
    GAMBLING_WARNING_ENABLED = os.environ.get('GAMBLING_WARNING_ENABLED', 'true').lower() == 'true'
    JURISDICTION = os.environ.get('JURISDICTION', 'KR')
    COMPLIANCE_MODE = os.environ.get('COMPLIANCE_MODE', 'strict')
    
    # === 알림 설정 ===
    ALERT_EMAIL_ENABLED = os.environ.get('ALERT_EMAIL_ENABLED', 'false').lower() == 'true'
    ALERT_EMAIL_SMTP_SERVER = os.environ.get('ALERT_EMAIL_SMTP_SERVER', 'smtp.gmail.com')
    ALERT_EMAIL_PORT = int(os.environ.get('ALERT_EMAIL_PORT', 587))
    ALERT_EMAIL_USERNAME = os.environ.get('ALERT_EMAIL_USERNAME', '')
    ALERT_EMAIL_PASSWORD = os.environ.get('ALERT_EMAIL_PASSWORD', '')
    ALERT_EMAIL_RECIPIENTS = os.environ.get('ALERT_EMAIL_RECIPIENTS', '').split(',')
    
    # === 백업 설정 ===
    BACKUP_ENABLED = os.environ.get('BACKUP_ENABLED', 'true').lower() == 'true'
    BACKUP_SCHEDULE = os.environ.get('BACKUP_SCHEDULE', '0 3 * * *')
    BACKUP_RETENTION_DAYS = int(os.environ.get('BACKUP_RETENTION_DAYS', 30))
    BACKUP_LOCATION = os.environ.get('BACKUP_LOCATION', '/app/backups')
    
    # === 투명성 관련 상수 ===
    TRANSPARENCY_FEATURES = {
        'algorithm_disclosure': True,
        'performance_metrics': True,
        'statistical_validation': True,
        'prediction_history': True,
        'model_comparison': True,
        'real_time_monitoring': True,
        'audit_trail': True,
        'data_integrity_checks': True
    }
    
    ETHICAL_GUIDELINES = {
        'no_guarantee_disclaimer': True,
        'gambling_addiction_warning': True,
        'age_restriction_enforcement': True,
        'responsible_gaming_promotion': True,
        'financial_risk_warning': True
    }
    
    # === 성능 설정 ===
    JSON_SORT_KEYS = False
    JSONIFY_PRETTYPRINT_REGULAR = False
    
    @staticmethod
    def init_app(app):
        """애플리케이션 초기화"""
        pass

class DevelopmentConfig(Config):
    """개발 환경 설정"""
    
    DEBUG = True
    TESTING = False
    
    # 개발 환경에서는 보안 설정 완화
    SESSION_COOKIE_SECURE = False
    WTF_CSRF_ENABLED = False
    
    # 더 자세한 로깅
    LOG_LEVEL = 'DEBUG'
    
    # 캐시 비활성화 (개발 중 즉시 반영을 위해)
    CACHE_TYPE = 'null'
    
    # Rate limiting 완화
    RATELIMIT_DEFAULT = '1000 per hour'
    RATELIMIT_API = '500 per hour'
    
    # 투명성 기능 모두 활성화 (테스트용)
    TRANSPARENCY_MODE = True
    STATISTICAL_VALIDATION = 'permissive'
    
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        
        # 개발 환경 전용 설정
        app.logger.setLevel('DEBUG')

class TestingConfig(Config):
    """테스트 환경 설정"""
    
    TESTING = True
    DEBUG = False
    
    # 테스트용 인메모리 데이터베이스
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    
    # CSRF 비활성화 (테스트 편의성)
    WTF_CSRF_ENABLED = False
    
    # 캐시 비활성화
    CACHE_TYPE = 'null'
    
    # Rate limiting 비활성화
    RATELIMIT_STORAGE_URL = 'memory://'
    RATELIMIT_DEFAULT = '10000 per hour'
    
    # 빠른 테스트를 위한 설정
    SESSION_PERMANENT = False
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=5)
    
    # 테스트 데이터 제한
    PREDICTION_HISTORY_LIMIT = 100
    DATA_RETENTION_DAYS = 7
    
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        
        # 테스트 환경 설정
        app.logger.disabled = True

class ProductionConfig(Config):
    """프로덕션 환경 설정"""
    
    DEBUG = False
    TESTING = False
    
    # 프로덕션 보안 강화
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Strict'
    
    # 엄격한 투명성 및 컴플라이언스
    TRANSPARENCY_MODE = True
    STATISTICAL_VALIDATION = 'strict'
    COMPLIANCE_MODE = 'strict'
    
    # 프로덕션 로깅 설정
    LOG_LEVEL = 'WARNING'
    AUDIT_LOG_ENABLED = True
    
    # 성능 최적화
    SQLALCHEMY_POOL_SIZE = 20
    SQLALCHEMY_POOL_TIMEOUT = 30
    CACHE_DEFAULT_TIMEOUT = 600  # 10분
    
    # 모니터링 강화
    MONITORING_ENABLED = True
    PROMETHEUS_METRICS = True
    
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        
        # 프로덕션 환경 전용 설정
        import logging
        from logging.handlers import RotatingFileHandler
        
        if not os.path.exists('logs'):
            os.mkdir('logs')
        
        file_handler = RotatingFileHandler(
            cls.LOG_FILE,
            maxBytes=cls.LOG_MAX_BYTES,
            backupCount=cls.LOG_BACKUP_COUNT
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        
        app.logger.setLevel(logging.INFO)
        app.logger.info('LottoPro AI startup')

class DockerConfig(ProductionConfig):
    """Docker 컨테이너 환경 설정"""
    
    # Docker 환경에 맞는 경로 설정
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:////app/data/lottopro.db'
    LOG_FILE = '/app/logs/lottopro.log'
    BACKUP_LOCATION = '/app/data/backups'
    
    # 컨테이너 환경에서의 헬스체크
    HEALTH_CHECK_INTERVAL = 30
    
    @classmethod
    def init_app(cls, app):
        ProductionConfig.init_app(app)
        
        # Docker 환경 전용 설정
        import logging
        
        # 컨테이너 로그는 stdout으로 출력
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(logging.INFO)
        stream_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s'
        ))
        app.logger.addHandler(stream_handler)

# 환경별 설정 매핑
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'docker': DockerConfig,
    'default': DevelopmentConfig
}

def get_config(config_name=None):
    """설정 클래스 반환"""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'default')
    
    return config.get(config_name, config['default'])
