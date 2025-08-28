#!/bin/bash

# LottoPro AI v2.0 - 자동 배포 스크립트
# 투명성 강화 버전 배포 자동화

set -e  # 오류 발생 시 중단

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 로그 함수들
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

# 환경 변수 설정
DEPLOY_ENV=${1:-production}
PROJECT_NAME="lottopro-ai"
BACKUP_DIR="/tmp/${PROJECT_NAME}-backup-$(date +%Y%m%d-%H%M%S)"
DEPLOY_USER=${DEPLOY_USER:-"lottopro"}

log_info "=== LottoPro AI v2.0 투명성 강화 버전 배포 시작 ==="
log_info "배포 환경: $DEPLOY_ENV"
log_info "백업 디렉토리: $BACKUP_DIR"

# 배포 전 검증
validate_environment() {
    log_info "환경 검증 중..."
    
    # 필수 명령어 확인
    local required_commands=("docker" "docker-compose" "git" "curl")
    for cmd in "${required_commands[@]}"; do
        if ! command -v $cmd &> /dev/null; then
            log_error "$cmd 명령어를 찾을 수 없습니다."
            exit 1
        fi
    done
    
    # Docker 서비스 확인
    if ! docker info &> /dev/null; then
        log_error "Docker 서비스가 실행되지 않고 있습니다."
        exit 1
    fi
    
    # 환경 파일 확인
    if [[ ! -f ".env" ]]; then
        if [[ -f ".env.example" ]]; then
            log_warning ".env 파일이 없습니다. .env.example을 복사합니다."
            cp .env.example .env
            log_warning ".env 파일을 수정하여 실제 설정값을 입력하세요."
        else
            log_error ".env 파일과 .env.example 파일이 모두 없습니다."
            exit 1
        fi
    fi
    
    log_success "환경 검증 완료"
}

# 기존 서비스 백업
backup_current_deployment() {
    log_info "기존 배포 백업 중..."
    
    mkdir -p $BACKUP_DIR
    
    # 현재 실행 중인 컨테이너 정보 저장
    docker-compose ps > $BACKUP_DIR/containers_status.txt 2>/dev/null || true
    
    # 데이터베이스 백업
    if docker-compose ps | grep -q "lottopro-web.*Up"; then
        log_info "데이터베이스 백업 중..."
        docker-compose exec -T lottopro-web python -c "
import sqlite3
import shutil
import os
from datetime import datetime

backup_path = '/app/data/backup_$(date +%Y%m%d_%H%M%S).db'
if os.path.exists('/app/data/lottopro.db'):
    shutil.copy2('/app/data/lottopro.db', backup_path)
    print(f'Database backed up to {backup_path}')
" || log_warning "데이터베이스 백업 실패 (서비스가 실행 중이 아닐 수 있습니다)"
    fi
    
    # 설정 파일 백업
    cp -r . $BACKUP_DIR/source_backup/ 2>/dev/null || true
    
    log_success "백업 완료: $BACKUP_DIR"
}

# 투명성 검증
verify_transparency_features() {
    log_info "투명성 기능 검증 중..."
    
    # 필수 투명성 파일들 확인
    local transparency_files=(
        "templates/ai_models.html"
        "templates/prediction_history.html"
        "utils/data_validator.py"
        "monitoring/real_time_monitor.py"
    )
    
    for file in "${transparency_files[@]}"; do
        if [[ ! -f "$file" ]]; then
            log_error "투명성 필수 파일이 없습니다: $file"
            exit 1
        fi
    done
    
    # 환경 변수에서 투명성 모드 확인
    if ! grep -q "TRANSPARENCY_MODE=enabled" .env; then
        log_warning "투명성 모드가 활성화되지 않았습니다."
        log_warning ".env 파일에서 TRANSPARENCY_MODE=enabled로 설정하세요."
    fi
    
    log_success "투명성 기능 검증 완료"
}

# 보안 검증
security_check() {
    log_info "보안 설정 검증 중..."
    
    # SECRET_KEY 확인
    if grep -q "SECRET_KEY=your-super-secret-key-change-this-in-production" .env; then
        log_error "기본 SECRET_KEY를 사용하고 있습니다. 반드시 변경하세요."
        exit 1
    fi
    
    # 프로덕션 환경에서 DEBUG 모드 확인
    if [[ "$DEPLOY_ENV" == "production" ]] && grep -q "FLASK_DEBUG=True" .env; then
        log_error "프로덕션 환경에서 DEBUG 모드가 활성화되어 있습니다."
        exit 1
    fi
    
    # SSL 인증서 확인 (프로덕션 환경)
    if [[ "$DEPLOY_ENV" == "production" ]]; then
        if [[ ! -f "nginx/ssl/cert.pem" ]] || [[ ! -f "nginx/ssl/key.pem" ]]; then
            log_warning "SSL 인증서가 없습니다. HTTPS 설정을 확인하세요."
        fi
    fi
    
    log_success "보안 설정 검증 완료"
}

# Docker 이미지 빌드
build_images() {
    log_info "Docker 이미지 빌드 중..."
    
    # 이전 이미지 정리
    docker-compose down 2>/dev/null || true
    
    # 캐시 없이 새로 빌드
    docker-compose build --no-cache --pull
    
    log_success "Docker 이미지 빌드 완료"
}

# 헬스체크 함수
health_check() {
    local url=$1
    local service_name=$2
    local max_attempts=30
    local attempt=1
    
    log_info "$service_name 헬스체크 중..."
    
    while [[ $attempt -le $max_attempts ]]; do
        if curl -f -s -o /dev/null "$url"; then
            log_success "$service_name 서비스 정상"
            return 0
        fi
        
        log_info "헬스체크 시도 $attempt/$max_attempts..."
        sleep 10
        ((attempt++))
    done
    
    log_error "$service_name 헬스체크 실패"
    return 1
}

# 서비스 배포
deploy_services() {
    log_info "서비스 배포 중..."
    
    # 네트워크 및 볼륨 생성
    docker network create lottopro-network 2>/dev/null || true
    docker volume create lottopro-data 2>/dev/null || true
    docker volume create lottopro-logs 2>/dev/null || true
    
    # 데이터 디렉토리 생성
    mkdir -p data logs backups
    chmod 755 data logs backups
    
    # 소유권 설정 (1000:1000은 컨테이너 내 lottopro 사용자)
    sudo chown -R 1000:1000 data logs backups 2>/dev/null || true
    
    # 서비스 시작 (단계별)
    log_info "Redis 서비스 시작..."
    docker-compose up -d redis
    sleep 5
    
    log_info "웹 애플리케이션 시작..."
    docker-compose up -d lottopro-web
    sleep 10
    
    log_info "모니터링 서비스 시작..."
    docker-compose up -d lottopro-monitor
    sleep 5
    
    log_info "Nginx 프록시 시작..."
    docker-compose up -d nginx
    sleep 5
    
    # 로그 수집 서비스 (선택사항)
    if docker-compose config --services | grep -q fluentd; then
        log_info "로그 수집 서비스 시작..."
        docker-compose up -d fluentd
    fi
    
    log_success "모든 서비스 배포 완료"
}

# 배포 후 검증
post_deploy_verification() {
    log_info "배포 후 검증 중..."
    
    # 컨테이너 상태 확인
    log_info "컨테이너 상태 확인..."
    docker-compose ps
    
    # 헬스체크
    if ! health_check "http://localhost:5000/health" "웹 애플리케이션"; then
        log_error "웹 애플리케이션 헬스체크 실패"
        rollback_deployment
        exit 1
    fi
    
    if ! health_check "http://localhost:5001/monitoring/health" "모니터링 서비스"; then
        log_warning "모니터링 서비스 헬스체크 실패 (계속 진행)"
    fi
    
    # 투명성 API 확인
    log_info "투명성 API 확인 중..."
    if curl -f -s -o /dev/null "http://localhost:5000/api/transparency_report"; then
        log_success "투명성 API 정상"
    else
        log_warning "투명성 API 응답 없음"
    fi
    
    # 로그 확인
    log_info "최근 로그 확인..."
    docker-compose logs --tail=20 lottopro-web
    
    log_success "배포 후 검증 완료"
}

# 롤백 함수
rollback_deployment() {
    log_warning "배포 롤백 중..."
    
    docker-compose down
    
    if [[ -d "$BACKUP_DIR/source_backup" ]]; then
        log_info "이전 소스 코드 복원 중..."
        # 현재 디렉토리를 백업하고 이전 버전 복원
        mv . ./failed_deployment_$(date +%Y%m%d_%H%M%S) 2>/dev/null || true
        cp -r $BACKUP_DIR/source_backup/* . 2>/dev/null || true
    fi
    
    log_warning "롤백 완료. 이전 상태로 복원되었습니다."
}

# 배포 정보 출력
print_deployment_info() {
    log_success "=== 배포 완료 ==="
    echo ""
    echo "🌐 웹 애플리케이션: http://localhost"
    echo "📊 모니터링 대시보드: http://localhost:5001"
    echo "🔍 투명성 보고서: http://localhost/ai_models"
    echo "📈 예측 히스토리: http://localhost/prediction_history"
    echo ""
    echo "📋 유용한 명령어:"
    echo "  로그 확인: docker-compose logs -f"
    echo "  상태 확인: docker-compose ps"
    echo "  서비스 중지: docker-compose down"
    echo "  재시작: docker-compose restart"
    echo ""
    echo "📁 백업 위치: $BACKUP_DIR"
    echo ""
    log_info "투명성 정책에 따라 모든 AI 모델과 예측 과정이 공개됩니다."
    log_info "법적 고지사항과 연령 제한을 준수해주세요."
}

# 정리 함수
cleanup() {
    log_info "정리 작업 중..."
    
    # 일주일 이상 된 백업 제거
    find /tmp -name "${PROJECT_NAME}-backup-*" -type d -mtime +7 -exec rm -rf {} + 2>/dev/null || true
    
    # 사용하지 않는 Docker 이미지 정리
    docker image prune -f >/dev/null 2>&1 || true
    
    log_success "정리 완료"
}

# 메인 실행 함수
main() {
    # 인터럽트 신호 처리
    trap 'log_error "배포가 중단되었습니다."; exit 1' INT TERM
    
    # 단계별 실행
    validate_environment
    verify_transparency_features
    security_check
    backup_current_deployment
    build_images
    deploy_services
    post_deploy_verification
    cleanup
    print_deployment_info
    
    log_success "LottoPro AI v2.0 투명성 강화 버전 배포가 완료되었습니다!"
}

# 도움말 출력
show_help() {
    echo "LottoPro AI v2.0 배포 스크립트"
    echo ""
    echo "사용법: $0 [환경] [옵션]"
    echo ""
    echo "환경:"
    echo "  development  개발 환경 배포"
    echo "  production   프로덕션 환경 배포 (기본값)"
    echo "  testing      테스트 환경 배포"
    echo ""
    echo "옵션:"
    echo "  --help       이 도움말 표시"
    echo "  --dry-run    실제 배포 없이 검증만 수행"
    echo ""
    echo "예시:"
    echo "  $0 production              # 프로덕션 배포"
    echo "  $0 development --dry-run   # 개발 환경 검증"
    echo ""
}

# 명령행 인수 처리
case "${1:-}" in
    --help|-h)
        show_help
        exit 0
        ;;
    --dry-run)
        log_info "Dry run 모드: 실제 배포 없이 검증만 수행합니다."
        validate_environment
        verify_transparency_features
        security_check
        log_success "모든 검증이 완료되었습니다. 실제 배포를 위해서는 --dry-run 옵션을 제거하세요."
        exit 0
        ;;
    *)
        main
        ;;
esac
