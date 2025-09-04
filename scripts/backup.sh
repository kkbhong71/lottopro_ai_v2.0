#!/bin/bash

# LottoPro-AI 백업 및 유지보수 스크립트
# 데이터베이스, 로그, 설정, 캐시 데이터 백업

set -e  # 에러 시 스크립트 중단

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 설정
PROJECT_DIR="/opt/lottopro-ai"
BACKUP_DIR="/opt/lottopro-ai/backups"
ARCHIVE_DIR="/opt/lottopro-ai/archives"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="lottopro_backup_${DATE}"
RETENTION_DAYS=${RETENTION_DAYS:-30}

# S3 백업 설정 (선택사항)
S3_BUCKET=${S3_BACKUP_BUCKET:-""}
AWS_PROFILE=${AWS_PROFILE:-"default"}

# 알림 설정
SLACK_WEBHOOK=${SLACK_WEBHOOK_URL:-""}
EMAIL_RECIPIENT=${BACKUP_EMAIL:-""}

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1" | tee -a "${BACKUP_DIR}/backup.log"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "${BACKUP_DIR}/backup.log"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "${BACKUP_DIR}/backup.log"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "${BACKUP_DIR}/backup.log"
}

log_step() {
    echo -e "\n${PURPLE}==== $1 ====${NC}" | tee -a "${BACKUP_DIR}/backup.log"
}

# 사전 확인
check_prerequisites() {
    log_step "사전 확인"
    
    # 필수 디렉토리 생성
    mkdir -p "${BACKUP_DIR}" "${ARCHIVE_DIR}"
    
    # 권한 확인
    if [ ! -w "${BACKUP_DIR}" ]; then
        log_error "백업 디렉토리에 쓰기 권한이 없습니다: ${BACKUP_DIR}"
        exit 1
    fi
    
    # 디스크 공간 확인
    available_space=$(df -BG "${BACKUP_DIR}" | awk 'NR==2 {print $4}' | sed 's/G//')
    if [ "${available_space}" -lt 5 ]; then
        log_warning "디스크 여유 공간이 부족합니다: ${available_space}GB"
    fi
    
    # 필수 명령어 확인
    for cmd in tar gzip redis-cli; do
        if ! command -v "${cmd}" &> /dev/null; then
            log_warning "${cmd} 명령어를 찾을 수 없습니다."
        fi
    done
    
    log_info "사전 확인 완료"
}

# 애플리케이션 데이터 백업
backup_application_data() {
    log_step "애플리케이션 데이터 백업"
    
    local data_backup="${BACKUP_DIR}/${BACKUP_NAME}_data.tar.gz"
    
    # 중요한 애플리케이션 파일들
    tar -czf "${data_backup}" \
        -C "${PROJECT_DIR}" \
        --exclude='venv' \
        --exclude='__pycache__' \
        --exclude='*.pyc' \
        --exclude='logs/*.log' \
        --exclude='data/temp' \
        app.py \
        monitoring/ \
        utils/ \
        static/ \
        templates/ \
        config/ \
        scripts/ \
        requirements.txt \
        .env \
        data/ \
        2>/dev/null || true
    
    if [ -f "${data_backup}" ]; then
        local backup_size=$(du -h "${data_backup}" | cut -f1)
        log_success "애플리케이션 데이터 백업 완료 (${backup_size})"
    else
        log_error "애플리케이션 데이터 백업 실패"
        return 1
    fi
}

# Redis 데이터 백업
backup_redis_data() {
    log_step "Redis 데이터 백업"
    
    local redis_backup="${BACKUP_DIR}/${BACKUP_NAME}_redis.rdb"
    
    if redis-cli ping &>/dev/null; then
        # Redis 백그라운드 저장 실행
        redis-cli BGSAVE
        
        # 백그라운드 저장 완료 대기
        while [ "$(redis-cli LASTSAVE)" == "$(redis-cli LASTSAVE)" ]; do
            sleep 1
        done
        
        # RDB 파일 복사
        if [ -f "/var/lib/redis/dump.rdb" ]; then
            cp /var/lib/redis/dump.rdb "${redis_backup}"
            gzip "${redis_backup}"
            log_success "Redis 데이터 백업 완료"
        else
            log_warning "Redis RDB 파일을 찾을 수 없습니다."
        fi
    else
        log_warning "Redis 서버에 연결할 수 없습니다."
    fi
}

# 로그 파일 백업
backup_logs() {
    log_step "로그 파일 백업"
    
    local logs_backup="${BACKUP_DIR}/${BACKUP_NAME}_logs.tar.gz"
    
    if [ -d "${PROJECT_DIR}/logs" ]; then
        # 최근 7일간의 로그만 백업
        find "${PROJECT_DIR}/logs" -name "*.log" -mtime -7 -print0 | \
            tar -czf "${logs_backup}" --null -T - 2>/dev/null || true
        
        if [ -f "${logs_backup}" ]; then
            local backup_size=$(du -h "${logs_backup}" | cut -f1)
            log_success "로그 파일 백업 완료 (${backup_size})"
        else
            log_warning "로그 파일 백업 실패 또는 백업할 로그가 없음"
        fi
    else
        log_warning "로그 디렉토리를 찾을 수 없습니다."
    fi
}

# 시스템 정보 백업
backup_system_info() {
    log_step "시스템 정보 백업"
    
    local system_info="${BACKUP_DIR}/${BACKUP_NAME}_system_info.txt"
    
    {
        echo "=== LottoPro-AI 시스템 정보 ==="
        echo "백업 날짜: $(date)"
        echo "호스트명: $(hostname)"
        echo "사용자: $(whoami)"
        echo
        
        echo "=== 시스템 상태 ==="
        echo "가동시간: $(uptime)"
        echo "메모리 사용량:"
        free -h
        echo
        echo "디스크 사용량:"
        df -h
        echo
        
        echo "=== 프로세스 정보 ==="
        ps aux | grep -E "(python|redis|nginx)" | grep -v grep
        echo
        
        echo "=== 네트워크 연결 ==="
        netstat -tulpn | grep -E ":(5000|6379|80|443)"
        echo
        
        echo "=== Python 환경 ==="
        "${PROJECT_DIR}/venv/bin/python" --version
        "${PROJECT_DIR}/venv/bin/pip" freeze
        echo
        
        echo "=== 환경 변수 ==="
        env | grep -E "FLASK|REDIS|LOTTO" | sort
        echo
        
        echo "=== 서비스 상태 ==="
        systemctl status lottopro-ai --no-pager || echo "서비스 정보 없음"
        systemctl status redis --no-pager || echo "Redis 서비스 정보 없음"
        systemctl status nginx --no-pager || echo "Nginx 서비스 정보 없음"
        
    } > "${system_info}"
    
    log_success "시스템 정보 백업 완료"
}

# 설정 파일 백업
backup_configuration() {
    log_step "설정 파일 백업"
    
    local config_backup="${BACKUP_DIR}/${BACKUP_NAME}_config.tar.gz"
    
    # 시스템 설정 파일들
    tar -czf "${config_backup}" \
        -C / \
        --exclude='*.pid' \
        --exclude='*.sock' \
        etc/systemd/system/lottopro-ai.service \
        etc/logrotate.d/lottopro-ai \
        etc/nginx/sites-available/lottopro* \
        etc/redis/redis.conf \
        2>/dev/null || true
    
    if [ -f "${config_backup}" ]; then
        log_success "설정 파일 백업 완료"
    else
        log_warning "설정 파일 백업 실패"
    fi
}

# 데이터베이스 백업 (SQLite 등, 미래 확장용)
backup_database() {
    log_step "데이터베이스 백업"
    
    local db_file="${PROJECT_DIR}/data/lottopro.db"
    
    if [ -f "${db_file}" ]; then
        local db_backup="${BACKUP_DIR}/${BACKUP_NAME}_database.db"
        cp "${db_file}" "${db_backup}"
        gzip "${db_backup}"
        log_success "데이터베이스 백업 완료"
    else
        log_info "백업할 데이터베이스가 없습니다."
    fi
}

# 백업 파일 압축
create_full_backup() {
    log_step "전체 백업 아카이브 생성"
    
    local full_backup="${ARCHIVE_DIR}/${BACKUP_NAME}_full.tar.gz"
    
    # 백업 디렉토리의 모든 파일을 하나로 압축
    tar -czf "${full_backup}" -C "${BACKUP_DIR}" \
        $(ls -1 "${BACKUP_DIR}" | grep "${BACKUP_NAME}" | grep -v "full.tar.gz") \
        2>/dev/null || true
    
    if [ -f "${full_backup}" ]; then
        local backup_size=$(du -h "${full_backup}" | cut -f1)
        log_success "전체 백업 생성 완료: ${full_backup} (${backup_size})"
        
        # 개별 백업 파일들 삭제 (공간 절약)
        rm -f "${BACKUP_DIR}/${BACKUP_NAME}"_*.{tar.gz,rdb.gz,txt,db.gz} 2>/dev/null || true
    else
        log_error "전체 백업 생성 실패"
        return 1
    fi
}

# S3 업로드 (선택사항)
upload_to_s3() {
    if [ -n "${S3_BUCKET}" ] && command -v aws &>/dev/null; then
        log_step "S3에 백업 업로드"
        
        local full_backup="${ARCHIVE_DIR}/${BACKUP_NAME}_full.tar.gz"
        
        if [ -f "${full_backup}" ]; then
            aws s3 cp "${full_backup}" "s3://${S3_BUCKET}/lottopro-backups/" \
                --profile "${AWS_PROFILE}" \
                --storage-class STANDARD_IA
            
            if [ $? -eq 0 ]; then
                log_success "S3 업로드 완료"
            else
                log_error "S3 업로드 실패"
            fi
        fi
    else
        log_info "S3 백업 건너뜀 (설정되지 않음 또는 AWS CLI 없음)"
    fi
}

# 오래된 백업 정리
cleanup_old_backups() {
    log_step "오래된 백업 정리"
    
    # 로컬 백업 정리
    local deleted_count=$(find "${ARCHIVE_DIR}" -name "lottopro_backup_*.tar.gz" -mtime +${RETENTION_DAYS} -delete -print | wc -l)
    
    if [ "${deleted_count}" -gt 0 ]; then
        log_info "${deleted_count}개의 오래된 백업 파일 삭제"
    else
        log_info "정리할 오래된 백업이 없습니다."
    fi
    
    # S3 백업 정리 (설정된 경우)
    if [ -n "${S3_BUCKET}" ] && command -v aws &>/dev/null; then
        aws s3 ls "s3://${S3_BUCKET}/lottopro-backups/" --profile "${AWS_PROFILE}" | \
            awk '$1 < "'$(date -d "-${RETENTION_DAYS} days" '+%Y-%m-%d')'" {print $4}' | \
            while read file; do
                if [ -n "$file" ]; then
                    aws s3 rm "s3://${S3_BUCKET}/lottopro-backups/${file}" --profile "${AWS_PROFILE}"
                    log_info "S3에서 오래된 백업 삭제: ${file}"
                fi
            done
    fi
}

# 알림 전송
send_notification() {
    local status=$1
    local message=$2
    
    # Slack 알림
    if [ -n "${SLACK_WEBHOOK}" ]; then
        local color="good"
        if [ "${status}" != "success" ]; then
            color="warning"
        fi
        
        curl -X POST -H 'Content-type: application/json' \
            --data "{\"attachments\":[{\"color\":\"${color}\",\"title\":\"LottoPro-AI 백업 알림\",\"text\":\"${message}\",\"ts\":$(date +%s)}]}" \
            "${SLACK_WEBHOOK}" &>/dev/null || true
    fi
    
    # 이메일 알림 (mailutils 패키지 필요)
    if [ -n "${EMAIL_RECIPIENT}" ] && command -v mail &>/dev/null; then
        echo "${message}" | mail -s "LottoPro-AI 백업 알림 - ${status}" "${EMAIL_RECIPIENT}" || true
    fi
}

# 백업 검증
verify_backup() {
    log_step "백업 검증"
    
    local full_backup="${ARCHIVE_DIR}/${BACKUP_NAME}_full.tar.gz"
    
    if [ -f "${full_backup}" ]; then
        # 백업 파일 무결성 검사
        if tar -tzf "${full_backup}" &>/dev/null; then
            log_success "백업 파일 무결성 검증 완료"
            return 0
        else
            log_error "백업 파일 손상 감지"
            return 1
        fi
    else
        log_error "백업 파일을 찾을 수 없습니다."
        return 1
    fi
}

# 메인 실행 함수
main() {
    local start_time=$(date +%s)
    
    log_step "LottoPro-AI 백업 시작"
    log_info "백업 시작: $(date)"
    
    # 에러 처리를 위한 트랩 설정
    trap 'log_error "백업 중 에러 발생 (라인: $LINENO)"; send_notification "error" "백업 실패: 라인 $LINENO에서 에러 발생"; exit 1' ERR
    
    # 백업 실행
    check_prerequisites
    backup_application_data
    backup_redis_data
    backup_logs
    backup_system_info
    backup_configuration
    backup_database
    create_full_backup
    
    # 백업 검증
    if verify_backup; then
        upload_to_s3
        cleanup_old_backups
        
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        local backup_size=$(du -h "${ARCHIVE_DIR}/${BACKUP_NAME}_full.tar.gz" 2>/dev/null | cut -f1 || echo "Unknown")
        
        local success_message="백업 성공 완료!\n시간: ${duration}초\n크기: ${backup_size}\n위치: ${ARCHIVE_DIR}/${BACKUP_NAME}_full.tar.gz"
        
        log_success "${success_message}"
        send_notification "success" "${success_message}"
    else
        log_error "백업 검증 실패"
        send_notification "error" "백업 검증 실패"
        exit 1
    fi
}

# 사용법 출력
usage() {
    echo "사용법: $0 [OPTIONS]"
    echo ""
    echo "옵션:"
    echo "  -h, --help          도움말 출력"
    echo "  -r, --retention N   백업 보존 기간 (기본: 30일)"
    echo "  -s, --s3-only       S3에만 백업 (로컬 백업 안함)"
    echo "  -l, --local-only    로컬에만 백업 (S3 업로드 안함)"
    echo "  -v, --verify        백업 검증만 실행"
    echo ""
    echo "환경변수:"
    echo "  S3_BACKUP_BUCKET    S3 버킷 이름"
    echo "  SLACK_WEBHOOK_URL   Slack 웹훅 URL"
    echo "  BACKUP_EMAIL        알림 이메일 주소"
    echo ""
}

# 명령행 인수 처리
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            usage
            exit 0
            ;;
        -r|--retention)
            RETENTION_DAYS="$2"
            shift 2
            ;;
        -s|--s3-only)
            S3_ONLY=true
            shift
            ;;
        -l|--local-only)
            LOCAL_ONLY=true
            shift
            ;;
        -v|--verify)
            VERIFY_ONLY=true
            shift
            ;;
        *)
            log_error "알 수 없는 옵션: $1"
            usage
            exit 1
            ;;
    esac
done

# 검증 모드
if [ "${VERIFY_ONLY}" = true ]; then
    log_step "백업 검증 모드"
    
    # 최신 백업 파일 찾기
    latest_backup=$(ls -t "${ARCHIVE_DIR}"/lottopro_backup_*_full.tar.gz 2>/dev/null | head -1)
    
    if [ -n "${latest_backup}" ]; then
        BACKUP_NAME=$(basename "${latest_backup}" _full.tar.gz)
        verify_backup
    else
        log_error "검증할 백업 파일을 찾을 수 없습니다."
        exit 1
    fi
    
    exit 0
fi

# 메인 실행
main

log_success "백업 스크립트 실행 완료!"

# Crontab 설정 예시:
# 매일 오전 3시에 백업 실행
# 0 3 * * * /opt/lottopro-ai/scripts/backup.sh >> /opt/lottopro-ai/logs/backup_cron.log 2>&1

# 매주 일요일 오전 2시에 S3에만 백업
# 0 2 * * 0 /opt/lottopro-ai/scripts/backup.sh --s3-only >> /opt/lottopro-ai/logs/backup_cron.log 2>&1
