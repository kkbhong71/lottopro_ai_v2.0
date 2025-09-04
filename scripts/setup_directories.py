#!/usr/bin/env python3
"""
LottoPro-AI 프로젝트 디렉토리 구조 설정 스크립트
성능 모니터링 및 캐싱 시스템을 위한 디렉토리 생성
"""

import os
import sys
from pathlib import Path
import json
from datetime import datetime

class DirectorySetup:
    """디렉토리 설정 클래스"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.created_dirs = []
        self.created_files = []
        
    def create_directory_structure(self):
        """전체 디렉토리 구조 생성"""
        
        # 디렉토리 구조 정의
        directories = [
            # 기본 앱 디렉토리
            "static/css",
            "static/js",
            "static/images",
            "templates",
            
            # 성능 모니터링 관련
            "monitoring",
            "monitoring/dashboards",
            "monitoring/alerts",
            "monitoring/reports",
            
            # 캐시 및 유틸리티
            "utils",
            "utils/cache",
            "utils/helpers",
            
            # 로그 디렉토리
            "logs",
            "logs/access",
            "logs/error",
            "logs/performance",
            "logs/cache",
            
            # 데이터 디렉토리
            "data",
            "data/backup",
            "data/exports",
            "data/imports",
            "data/temp",
            
            # 설정 및 스크립트
            "config",
            "scripts",
            "scripts/deployment",
            "scripts/maintenance",
            "scripts/monitoring",
            
            # 테스트 디렉토리
            "tests",
            "tests/unit",
            "tests/integration",
            "tests/performance",
            
            # Docker 및 배포
            "docker",
            "docker/nginx",
            "docker/redis",
            "docker/monitoring",
            
            # 문서
            "docs",
            "docs/api",
            "docs/deployment",
            "docs/monitoring",
            
            # SSL 인증서 (프로덕션용)
            "ssl",
            
            # 백업 및 아카이브
            "backups",
            "archives"
        ]
        
        print("🚀 LottoPro-AI 디렉토리 구조 설정 시작...")
        print(f"📁 프로젝트 루트: {self.project_root}")
        print("=" * 60)
        
        # 디렉토리 생성
        for directory in directories:
            self.create_directory(directory)
            
        # 기본 파일 생성
        self.create_default_files()
        
        # .gitkeep 파일 생성 (빈 디렉토리 유지용)
        self.create_gitkeep_files()
        
        # 설정 파일 생성
        self.create_config_files()
        
        print("=" * 60)
        print(f"✅ 디렉토리 구조 설정 완료!")
        print(f"📁 생성된 디렉토리: {len(self.created_dirs)}개")
        print(f"📄 생성된 파일: {len(self.created_files)}개")
        
        # 요약 리포트 생성
        self.generate_setup_report()
        
    def create_directory(self, dir_path: str):
        """개별 디렉토리 생성"""
        full_path = self.project_root / dir_path
        
        if not full_path.exists():
            try:
                full_path.mkdir(parents=True, exist_ok=True)
                self.created_dirs.append(str(dir_path))
                print(f"✅ 생성: {dir_path}")
            except Exception as e:
                print(f"❌ 실패: {dir_path} - {str(e)}")
        else:
            print(f"⚠️  존재: {dir_path}")
    
    def create_default_files(self):
        """기본 파일들 생성"""
        
        # __init__.py 파일들
        init_dirs = [
            "monitoring",
            "utils",
            "tests",
            "config"
        ]
        
        for dir_name in init_dirs:
            self.create_file(f"{dir_name}/__init__.py", '"""LottoPro-AI 모듈"""\n')
        
        # README 파일들
        readme_files = {
            "monitoring/README.md": "# 성능 모니터링 모듈\n\n실시간 성능 모니터링 및 알림 시스템\n",
            "utils/README.md": "# 유틸리티 모듈\n\n캐시 관리 및 헬퍼 함수들\n",
            "logs/README.md": "# 로그 디렉토리\n\n애플리케이션 로그 파일들이 저장됩니다.\n",
            "data/README.md": "# 데이터 디렉토리\n\n임시 데이터 및 백업 파일들이 저장됩니다.\n",
            "tests/README.md": "# 테스트 디렉토리\n\n단위 테스트 및 통합 테스트 파일들\n"
        }
        
        for file_path, content in readme_files.items():
            self.create_file(file_path, content)
    
    def create_gitkeep_files(self):
        """빈 디렉토리 유지를 위한 .gitkeep 파일 생성"""
        
        empty_dirs = [
            "logs/access",
            "logs/error", 
            "logs/performance",
            "logs/cache",
            "data/backup",
            "data/exports",
            "data/imports",
            "data/temp",
            "backups",
            "archives",
            "ssl"
        ]
        
        for dir_path in empty_dirs:
            self.create_file(f"{dir_path}/.gitkeep", "# 빈 디렉토리 유지용\n")
    
    def create_config_files(self):
        """설정 파일들 생성"""
        
        # 로깅 설정
        logging_config = {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                },
                "detailed": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(module)s - %(funcName)s - %(message)s"
                },
                "json": {
                    "format": "%(asctime)s %(name)s %(levelname)s %(message)s",
                    "class": "pythonjsonlogger.jsonlogger.JsonFormatter"
                }
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "level": "INFO",
                    "formatter": "default",
                    "stream": "ext://sys.stdout"
                },
                "file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "level": "INFO", 
                    "formatter": "detailed",
                    "filename": "logs/lottopro.log",
                    "maxBytes": 10485760,
                    "backupCount": 5
                },
                "performance": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "level": "INFO",
                    "formatter": "json",
                    "filename": "logs/performance/performance.log",
                    "maxBytes": 10485760,
                    "backupCount": 10
                },
                "cache": {
                    "class": "logging.handlers.RotatingFileHandler", 
                    "level": "DEBUG",
                    "formatter": "json",
                    "filename": "logs/cache/cache.log",
                    "maxBytes": 5242880,
                    "backupCount": 5
                }
            },
            "loggers": {
                "": {
                    "level": "INFO",
                    "handlers": ["console", "file"]
                },
                "monitoring.performance_monitor": {
                    "level": "INFO",
                    "handlers": ["performance"],
                    "propagate": False
                },
                "utils.cache_manager": {
                    "level": "DEBUG", 
                    "handlers": ["cache"],
                    "propagate": False
                }
            }
        }
        
        self.create_file(
            "config/logging.json", 
            json.dumps(logging_config, indent=2, ensure_ascii=False)
        )
        
        # 모니터링 설정
        monitoring_config = {
            "performance_monitor": {
                "collection_interval": 30,
                "data_retention_hours": 24,
                "alert_thresholds": {
                    "response_time": 10.0,
                    "error_rate": 0.05,
                    "cpu_usage": 80.0,
                    "memory_usage": 85.0,
                    "disk_usage": 95.0
                },
                "alert_cooldown_minutes": 15,
                "export_formats": ["json", "csv"],
                "dashboard_refresh_seconds": 30
            },
            "cache_monitor": {
                "hit_rate_threshold": 80.0,
                "memory_usage_threshold": 90.0,
                "eviction_rate_threshold": 10.0,
                "warming_enabled": True,
                "warming_schedules": [
                    {"pattern": "stats:*", "interval_minutes": 10},
                    {"pattern": "prediction:*", "interval_minutes": 5}
                ]
            }
        }
        
        self.create_file(
            "config/monitoring.json",
            json.dumps(monitoring_config, indent=2, ensure_ascii=False)
        )
        
        # 개발환경 설정
        dev_config = {
            "flask": {
                "debug": True,
                "testing": False,
                "secret_key": "dev-secret-key-change-in-production"
            },
            "redis": {
                "url": "redis://localhost:6379/1",
                "decode_responses": True,
                "socket_timeout": 5
            },
            "monitoring": {
                "enabled": True,
                "collection_interval": 60,
                "alerts_enabled": False
            },
            "cache": {
                "type": "redis",
                "default_ttl": 300,
                "compression": False,
                "warming": True
            },
            "rate_limiting": {
                "enabled": False,
                "default_limit": "1000/hour"
            }
        }
        
        self.create_file(
            "config/development.json",
            json.dumps(dev_config, indent=2, ensure_ascii=False)
        )
        
        # 프로덕션 환경 설정
        prod_config = {
            "flask": {
                "debug": False,
                "testing": False,
                "secret_key": "${SECRET_KEY}"
            },
            "redis": {
                "url": "${REDIS_URL}",
                "decode_responses": True,
                "socket_timeout": 3,
                "socket_connect_timeout": 3,
                "max_connections": 20
            },
            "monitoring": {
                "enabled": True,
                "collection_interval": 30,
                "alerts_enabled": True
            },
            "cache": {
                "type": "redis",
                "default_ttl": 300,
                "compression": True,
                "warming": True
            },
            "rate_limiting": {
                "enabled": True,
                "default_limit": "100/hour",
                "predict_limit": "30/hour"
            },
            "security": {
                "secure_cookies": True,
                "force_https": True,
                "content_security_policy": True
            }
        }
        
        self.create_file(
            "config/production.json",
            json.dumps(prod_config, indent=2, ensure_ascii=False)
        )
        
    def create_file(self, file_path: str, content: str):
        """개별 파일 생성"""
        full_path = self.project_root / file_path
        
        # 디렉토리가 없으면 생성
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        if not full_path.exists():
            try:
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                self.created_files.append(str(file_path))
                print(f"📄 생성: {file_path}")
            except Exception as e:
                print(f"❌ 파일 생성 실패: {file_path} - {str(e)}")
        else:
            print(f"⚠️  파일 존재: {file_path}")
    
    def generate_setup_report(self):
        """설정 완료 리포트 생성"""
        
        report = {
            "setup_timestamp": datetime.now().isoformat(),
            "project_root": str(self.project_root),
            "created_directories": self.created_dirs,
            "created_files": self.created_files,
            "summary": {
                "total_directories": len(self.created_dirs),
                "total_files": len(self.created_files)
            },
            "next_steps": [
                "1. .env 파일 생성 및 환경 변수 설정",
                "2. Redis 서버 설치 및 실행",
                "3. requirements.txt에서 패키지 설치",
                "4. 애플리케이션 실행 및 테스트",
                "5. 모니터링 대시보드 확인"
            ],
            "important_notes": [
                "logs/ 디렉토리는 애플리케이션이 쓰기 권한을 가져야 합니다",
                "data/ 디렉토리도 쓰기 권한이 필요합니다",
                "SSL 인증서는 ssl/ 디렉토리에 배치하세요",
                "프로덕션 환경에서는 SECRET_KEY를 반드시 변경하세요"
            ]
        }
        
        report_path = self.project_root / "setup_report.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"📊 설정 리포트 생성: setup_report.json")
        
        # 콘솔에도 다음 단계 출력
        print("\n🎯 다음 단계:")
        for step in report["next_steps"]:
            print(f"   {step}")
            
        print("\n⚠️  중요 사항:")
        for note in report["important_notes"]:
            print(f"   • {note}")
    
    def validate_setup(self):
        """설정 완료 후 검증"""
        print("\n🔍 설정 검증 중...")
        
        # 필수 디렉토리 확인
        required_dirs = [
            "static", "templates", "monitoring", "utils", 
            "logs", "data", "config"
        ]
        
        missing_dirs = []
        for dir_name in required_dirs:
            if not (self.project_root / dir_name).exists():
                missing_dirs.append(dir_name)
        
        if missing_dirs:
            print(f"❌ 누락된 필수 디렉토리: {missing_dirs}")
            return False
        
        # 권한 확인 (Linux/Mac)
        if os.name != 'nt':  # Windows가 아닌 경우
            writable_dirs = ["logs", "data", "backups"]
            permission_issues = []
            
            for dir_name in writable_dirs:
                dir_path = self.project_root / dir_name
                if dir_path.exists() and not os.access(dir_path, os.W_OK):
                    permission_issues.append(dir_name)
            
            if permission_issues:
                print(f"⚠️  쓰기 권한 문제: {permission_issues}")
                print("   sudo chmod 755 <directory> 명령으로 권한을 수정하세요.")
        
        print("✅ 설정 검증 완료!")
        return True

def main():
    """메인 실행 함수"""
    
    # 명령행 인자 처리
    project_root = sys.argv[1] if len(sys.argv) > 1 else "."
    
    try:
        # 디렉토리 설정 실행
        setup = DirectorySetup(project_root)
        setup.create_directory_structure()
        
        # 설정 검증
        if setup.validate_setup():
            print("\n🎉 LottoPro-AI 디렉토리 설정이 성공적으로 완료되었습니다!")
            print("\n다음 단계:")
            print("1. cd <project_directory>")
            print("2. cp .env.example .env")  
            print("3. nano .env  # 환경 변수 수정")
            print("4. pip install -r requirements.txt")
            print("5. python app.py")
        else:
            print("\n⚠️  설정에 문제가 있습니다. 위 메시지를 확인하고 수정하세요.")
            
    except KeyboardInterrupt:
        print("\n\n⏹️  설정이 중단되었습니다.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 오류 발생: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
