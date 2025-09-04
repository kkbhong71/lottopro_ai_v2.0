#!/bin/bash

# LottoPro-AI 배포 스크립트
# 성능 모니터링 및 캐싱 시스템 포함 완전 배포

set -e  # 에러 발생 시 스크립트 중단

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 함수 정의
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "\n${PURPLE}==== $1 ====${NC}"
}

# 배포 환경 설정
ENVIRONMENT=${1:-production}
PROJECT_DIR=$(pwd)
BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
SERVICE_NAME="lottopro-ai"

log_step "LottoPro-AI 배포 시작 (환경: $ENVIRONMENT)"

# 시스템 요구사항 확인
check_requirements() {
    log_step "시스템 요구사항 확인"
    
    # Python 버전 확인
    if command -v python3 &> /dev/null; then
        python_version=$(python3 -V 2>&1 | awk '{print $2}')
        log_info "Python 버전: $python_version"
    else
        log_error "Python 3가 설치되지 않았습니다."
        exit 1
    fi
    
    # Redis 확인
    if command -v redis-cli &> /dev/null; then
        log_info "Redis CLI 발견"
        if redis-cli ping &> /dev/null; then
            log_success "Redis 서버 연결 확인"
        else
            log_warning "Redis 서버가 실행 중이지 않습니다."
        fi
    else
        log_warning "Redis CLI가 설치되지 않았습니다. 설치가 필요할 수 있습니다."
    fi
    
    # Docker 확인 (선택사항)
    if command -v docker &> /dev/null; then
        docker_version=$(docker -v | awk '{print $3}' | sed 's/,//')
        log_info "Docker 버전: $docker_version"
        
        if command -v docker-compose &> /dev/null; then
            compose_version=$(docker-compose -v | awk '{print $3}' | sed 's/,//')
            log_info "Docker Compose 버전: $compose_version"
        fi
    fi
    
    # 디스크 공간 확인
    available_space=$(df -h . | awk 'NR==2 {print $4}')
    log_info "사용 가능한 디스크 공간: $available_space"
    
    # 메모리 확인
    if command -v free &> /dev/null; then
        total_memory=$(free -h | awk 'NR==2{print $2}')
        available_memory=$(free -h | awk 'NR==2{print $7}')
        log_info "총 메모리: $total_memory, 사용 가능: $available_memory"
    fi
}

# 백업 생성
create_backup() {
    log_step "기존 설정 백업"
    
    if [ -f "app.py" ]; then
        mkdir -p "$BACKUP_DIR"
        
        # 중요 파일들 백업
        cp app.py "$BACKUP_DIR/" 2>/dev/null || true
        cp -r static "$BACKUP_DIR/" 2>/dev/null || true
        cp -r templates "$BACKUP_DIR/" 2>/dev/null || true
        cp .env "$BACKUP_DIR/" 2>/dev/null || true
        cp -r logs "$BACKUP_DIR/" 2>/dev/null || true
        cp -r data "$BACKUP_DIR/" 2>/dev/null || true
        
        log_success "백업 완료: $BACKUP_DIR"
    else
        log_info "기존 설치가 없어 백업을 건너뜁니다."
    fi
}

# 환경 설정
setup_environment() {
    log_step "환경 설정"
    
    # .env 파일 확인 및 생성
    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            cp .env.example .env
            log_warning ".env 파일을 생성했습니다. 설정을 확인하고 수정하세요."
            
            # 기본 SECRET_KEY 생성
            secret_key=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
            if [[ "$OSTYPE" == "darwin"* ]]; then
                sed -i '' "s/your-super-secret-key-here-change-this/$secret_key/g" .env
            else
                sed -i "s/your-super-secret-key-here-change-this/$secret_key/g" .env
            fi
            log_success "SECRET_KEY 자동 생성 완료"
        else
            log_error ".env.example 파일이 없습니다."
            exit 1
        fi
    else
        log_success ".env 파일이 이미 존재합니다."
    fi
    
    # 환경별 설정
    if [ "$ENVIRONMENT" = "production" ]; then
        # 프로덕션 환경 설정
        sed -i.bak 's/FLASK_ENV=development/FLASK_ENV=production/' .env
        sed -i.bak 's/DEBUG=true/DEBUG=false/' .env
        log_info "프로덕션 환경으로 설정 완료"
    fi
    
    # Python 가상환경 생성
    if [ ! -d "venv" ]; then
        log_info "Python 가상환경 생성 중..."
        python3 -m venv venv
        log_success "가상환경 생성 완료"
    else
        log_info "기존 가상환경 사용"
    fi
    
    # 가상환경 활성화
    source venv/bin/activate
    
    # pip 업그레이드
    pip install --upgrade pip
    
    # 의존성 설치
    log_info "Python 패키지 설치 중..."
    pip install -r requirements.txt
    log_success "패키지 설치 완료"
}

# 디렉토리 구조 설정
setup_directories() {
    log_step "디렉토리 구조 설정"
    
    if [ -f "scripts/setup_directories.py" ]; then
        python3 scripts/setup_directories.py
        log_success "디렉토리 구조 설정 완료"
    else
        # 기본 디렉토리 생성
        mkdir -p logs/{access,error,performance,cache}
        mkdir -p data/{backup,exports,imports,temp}
        mkdir -p monitoring/{dashboards,alerts,reports}
        mkdir -p utils/{cache,helpers}
        mkdir -p backups
        log_success "기본 디렉토리 생성 완료"
    fi
    
    # 권한 설정
    chmod 755 logs data backups
    chmod 644 config/*.json 2>/dev/null || true
}

# Redis 설정 및 실행
setup_redis() {
    log_step "Redis 설정"
    
    # Redis 상태 확인
    if redis-cli ping &> /dev/null; then
        log_success "Redis 서버가 이미 실행 중입니다."
    else
        log_info "Redis 서버 시작을 시도합니다..."
        
        # Docker Compose 사용 시도
        if [ -f "docker-compose.yml" ] && command -v docker-compose &> /dev/null; then
            log_info "Docker Compose로 Redis 시작..."
            docker-compose up -d redis
            sleep 5
            
            if redis-cli ping &> /dev/null; then
                log_success "Docker Redis 시작 완료"
            else
                log_error "Docker Redis 시작 실패"
            fi
        else
            # 시스템 Redis 서비스 시작 시도
            if command -v systemctl &> /dev/null; then
                sudo systemctl start redis || log_warning "Redis 서비스 시작 실패"
            elif command -v service &> /dev/null; then
                sudo service redis-server start || log_warning "Redis 서비스 시작 실패"
            else
                log_warning "Redis를 자동으로 시작할 수 없습니다. 수동으로 시작하세요."
            fi
        fi
    fi
}

# 애플리케이션 테스트
test_application() {
    log_step "애플리케이션 테스트"
    
    # 기본 import 테스트
    python3 -c "
import sys
sys.path.append('.')

try:
    from app import app
    print('✓ Flask 앱 import 성공')
except Exception as e:
    print(f'✗ Flask 앱 import 실패: {e}')
    sys.exit(1)

try:
    from monitoring.performance_monitor import PerformanceMonitor
    print('✓ 성능 모니터링 모듈 import 성공')
except Exception as e:
    print(f'⚠ 성능 모니터링 모듈 import 실패: {e}')

try:
    from utils.cache_manager import CacheManager
    print('✓ 캐시 관리 모듈 import 성공')
except Exception as e:
    print(f'⚠ 캐시 관리 모듈 import 실패: {e}')
"
    
    # 설정 파일 테스트
    if python3 -c "
import json
try:
    with open('config/monitoring.json', 'r') as f:
        json.load(f)
    print('✓ 모니터링 설정 파일 유효')
except:
    print('⚠ 모니터링 설정 파일 문제')

try:
    with open('config/logging.json', 'r') as f:
        json.load(f)
    print('✓ 로깅 설정 파일 유효')
except:
    print('⚠ 로깅 설정 파일 문제')
"; then
        log_success "기본 테스트 통과"
    else
        log_error "기본 테스트 실패"
        exit 1
    fi
}

# 시스템 서비스 설정 (Linux)
setup_systemd_service() {
    if [ "$ENVIRONMENT" = "production" ] && [ -d "/etc/systemd/system" ]; then
        log_step "Systemd 서비스 설정"
        
        # 서비스 파일 생성
        sudo tee /etc/systemd/system/${SERVICE_NAME}.service > /dev/null << EOF
[Unit]
Description=LottoPro-AI Web Application
After=network.target redis.service
Requires=redis.service

[Service]
Type=simple
User=$(whoami)
WorkingDirectory=${PROJECT_DIR}
Environment=PATH=${PROJECT_DIR}/venv/bin
ExecStart=${PROJECT_DIR}/venv/bin/python app.py
ExecReload=/bin/kill -HUP \$MAINPID
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF
        
        # 서비스 활성화
        sudo systemctl daemon-reload
        sudo systemctl enable ${SERVICE_NAME}
        
        log_success "Systemd 서비스 설정 완료"
        log_info "서비스 시작: sudo systemctl start ${SERVICE_NAME}"
        log_info "서비스 상태: sudo systemctl status ${SERVICE_NAME}"
    fi
}

# 모니터링 대시보드 설정
setup_monitoring() {
    log_step "모니터링 대시보드 설정"
    
    # 모니터링 디렉토리 확인
    if [ ! -d "monitoring" ]; then
        mkdir -p monitoring
        log_info "모니터링 디렉토리 생성"
    fi
    
    # Grafana 대시보드 (Docker Compose 환경)
    if [ -f "docker-compose.yml" ] && grep -q "grafana" docker-compose.yml; then
        log_info "Grafana 대시보드를 Docker Compose로 설정할 수 있습니다."
        log_info "실행: docker-compose --profile monitoring up -d"
    fi
    
    log_success "모니터링 설정 완료"
}

# 성능 최적화 설정
optimize_performance() {
    log_step "성능 최적화 설정"
    
    # 파일 디스크립터 제한 확인
    ulimit_files=$(ulimit -n)
    if [ "$ulimit_files" -lt 4096 ]; then
        log_warning "파일 디스크립터 제한이 낮습니다 (현재: $ulimit_files)"
        log_info "권장: /etc/security/limits.conf에 '*    soft    nofile  4096' 추가"
    fi
    
    # 메모리 스왑 설정 확인 (Linux)
    if [ -f "/proc/sys/vm/swappiness" ]; then
        swappiness=$(cat /proc/sys/vm/swappiness)
        if [ "$swappiness" -gt 10 ]; then
            log_warning "메모리 스왑 설정이 높습니다 (현재: $swappiness)"
            log_info "권장: echo 'vm.swappiness=10' >> /etc/sysctl.conf"
        fi
    fi
    
    log_success "성능 최적화 확인 완료"
}

# 보안 설정
setup_security() {
    log_step "보안 설정"
    
    # 파일 권한 설정
    chmod 600 .env
    chmod 600 config/*.json 2>/dev/null || true
    chmod 700 backups 2>/dev/null || true
    
    # SSL 인증서 디렉토리 (있다면)
    if [ -d "ssl" ]; then
        chmod 700 ssl
        chmod 600 ssl/* 2>/dev/null || true
        log_info "SSL 디렉토리 권한 설정 완료"
    fi
    
    # 방화벽 안내 (수동 설정 필요)
    log_info "방화벽 설정을 확인하세요:"
    log_info "  - 포트 5000 (애플리케이션)"
    log_info "  - 포트 6379 (Redis, 외부 접근 차단 권장)"
    
    log_success "보안 설정 완료"
}

# 배포 완료 및 정보 출력
deployment_complete() {
    log_step "배포 완료"
    
    echo
    log_success "🎉 LottoPro-AI 배포가 완료되었습니다!"
    echo
    echo -e "${CYAN}===== 배포 정보 =====${NC}"
    echo -e "환경: ${GREEN}$ENVIRONMENT${NC}"
    echo -e "프로젝트 디렉토리: ${GREEN}$PROJECT_DIR${NC}"
    echo -e "백업 디렉토리: ${GREEN}$BACKUP_DIR${NC}"
    echo -e "Python 환경: ${GREEN}$(which python3)${NC}"
    echo
    echo -e "${CYAN}===== 시작 방법 =====${NC}"
    echo -e "${GREEN}1. 수동 실행:${NC}"
    echo "   cd $PROJECT_DIR"
    echo "   source venv/bin/activate"
    echo "   python app.py"
    echo
    echo -e "${GREEN}2. Docker Compose 실행:${NC}"
    echo "   docker-compose up -d"
    echo
    if [ -f "/etc/systemd/system/${SERVICE_NAME}.service" ]; then
        echo -e "${GREEN}3. 시스템 서비스 실행:${NC}"
        echo "   sudo systemctl start ${SERVICE_NAME}"
        echo "   sudo systemctl status ${SERVICE_NAME}"
        echo
    fi
    
    echo -e "${CYAN}===== 접속 정보 =====${NC}"
    echo -e "웹 애플리케이션: ${GREEN}http://localhost:5000${NC}"
    echo -e "모니터링 대시보드: ${GREEN}http://localhost:5000/admin/monitoring${NC}"
    echo -e "Redis Insight: ${GREEN}http://localhost:8001${NC} (Docker Compose 실행 시)"
    echo
    
    echo -e "${CYAN}===== 유용한 명령어 =====${NC}"
    echo -e "${GREEN}로그 확인:${NC}"
    echo "   tail -f logs/lottopro.log"
    echo "   tail -f logs/performance/performance.log"
    echo
    echo -e "${GREEN}서비스 상태 확인:${NC}"
    echo "   curl http://localhost:5000/api/health"
    echo
    echo -e "${GREEN}캐시 상태 확인:${NC}"
    echo "   redis-cli info stats"
    echo "   curl http://localhost:5000/admin/cache/info"
    echo
    echo -e "${GREEN}성능 메트릭 확인:${NC}"
    echo "   curl http://localhost:5000/admin/performance"
    echo
    
    echo -e "${YELLOW}⚠️  중요사항:${NC}"
    echo "1. .env 파일의 SECRET_KEY를 프로덕션용으로 변경하세요"
    echo "2. Redis 보안 설정을 확인하세요"
    echo "3. 방화벽 설정을 확인하세요"
    echo "4. 정기 백업 스케줄을 설정하세요"
    echo "5. 로그 로테이션을 설정하세요"
    echo
}

# 메인 실행
main() {
    # 사전 확인
    if [ ! -f "app.py" ] && [ ! -f "requirements.txt" ]; then
        log_error "LottoPro-AI 프로젝트 디렉토리에서 실행해주세요."
        exit 1
    fi
    
    # 배포 단계별 실행
    check_requirements
    create_backup
    setup_environment
    setup_directories
    setup_redis
    test_application
    setup_systemd_service
    setup_monitoring
    optimize_performance
    setup_security
    deployment_complete
    
    log_success "배포 스크립트 실행 완료!"
}

# 에러 처리
trap 'log_error "배포 중 에러가 발생했습니다. 라인: $LINENO"' ERR

# 스크립트 실행
main "$@"
