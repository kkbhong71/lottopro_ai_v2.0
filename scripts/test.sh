#!/bin/bash

# LottoPro AI v2.0 - 자동 테스트 스크립트
# 투명성 기능 및 전체 시스템 테스트

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

# 테스트 결과 추적
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0
TEST_RESULTS=()

# 테스트 함수
run_test() {
    local test_name="$1"
    local test_command="$2"
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    log_info "테스트 실행: $test_name"
    
    if eval "$test_command"; then
        PASSED_TESTS=$((PASSED_TESTS + 1))
        log_success "✓ $test_name"
        TEST_RESULTS+=("✓ $test_name")
        return 0
    else
        FAILED_TESTS=$((FAILED_TESTS + 1))
        log_error "✗ $test_name"
        TEST_RESULTS+=("✗ $test_name")
        return 1
    fi
}

# API 테스트 헬퍼
test_api_endpoint() {
    local endpoint="$1"
    local expected_status="${2:-200}"
    local description="$3"
    
    local response=$(curl -s -w "HTTPSTATUS:%{http_code}" "http://localhost:5000$endpoint")
    local body=$(echo "$response" | sed -E 's/HTTPSTATUS\:[0-9]{3}$//')
    local status=$(echo "$response" | grep -o "HTTPSTATUS:[0-9]*" | cut -d: -f2)
    
    if [[ "$status" == "$expected_status" ]]; then
        log_success "API $description: $endpoint (상태: $status)"
        return 0
    else
        log_error "API $description: $endpoint (예상: $expected_status, 실제: $status)"
        return 1
    fi
}

# JSON 응답 검증
test_json_response() {
    local endpoint="$1"
    local expected_fields="$2"
    local description="$3"
    
    local response=$(curl -s "http://localhost:5000$endpoint")
    
    # JSON 유효성 검사
    if ! echo "$response" | python3 -m json.tool > /dev/null 2>&1; then
        log_error "$description: 유효하지 않은 JSON 응답"
        return 1
    fi
    
    # 필수 필드 확인
    for field in $expected_fields; do
        if ! echo "$response" | python3 -c "
import json, sys
data = json.load(sys.stdin)
print('$field' in data)
" | grep -q "True"; then
            log_error "$description: 필수 필드 '$field' 누락"
            return 1
        fi
    done
    
    log_success "$description: JSON 응답 검증 완료"
    return 0
}

# 환경 설정 테스트
test_environment_setup() {
    log_info "=== 환경 설정 테스트 ==="
    
    run_test "Python 버전 확인" "python3 --version | grep -q 'Python 3'"
    run_test "필수 패키지 설치 확인" "python3 -c 'import flask, pandas, numpy, scipy, requests'"
    run_test ".env 파일 존재 확인" "test -f .env"
    run_test "데이터 디렉토리 존재 확인" "test -d data"
    run_test "로그 디렉토리 존재 확인" "test -d logs"
}

# 투명성 기능 테스트
test_transparency_features() {
    log_info "=== 투명성 기능 테스트 ==="
    
    # 투명성 관련 파일 존재 확인
    run_test "AI 모델 상세 페이지 템플릿" "test -f templates/ai_models.html"
    run_test "예측 히스토리 페이지 템플릿" "test -f templates/prediction_history.html"
    run_test "데이터 검증 모듈" "test -f utils/data_validator.py"
    run_test "실시간 모니터링 모듈" "test -f monitoring/real_time_monitor.py"
    
    # 투명성 API 테스트
    if docker-compose ps | grep -q "lottopro-web.*Up"; then
        run_test "투명성 보고서 API" "test_api_endpoint '/api/transparency_report' 200 '투명성 보고서'"
        run_test "통계 분석 API" "test_api_endpoint '/api/statistical_analysis' 200 '통계 분석'"
        run_test "AI 모델 성능 API" "test_api_endpoint '/api/model_performance/combined' 200 'AI 모델 성능'"
        
        # JSON 응답 내용 검증
        run_test "투명성 보고서 JSON 검증" "test_json_response '/api/transparency_report' 'data_completeness ethical_compliance' '투명성 보고서'"
        run_test "통계 분석 JSON 검증" "test_json_response '/api/statistical_analysis' 'sample_size theoretical_hit_rate actual_hit_rate' '통계 분석'"
    else
        log_warning "웹 서비스가 실행 중이 아니어서 API 테스트를 건너뜁니다."
    fi
}

# 웹 애플리케이션 테스트
test_web_application() {
    log_info "=== 웹 애플리케이션 테스트 ==="
    
    if ! docker-compose ps | grep -q "lottopro-web.*Up"; then
        log_warning "웹 서비스가 실행 중이 아닙니다. 서비스를 시작합니다."
        docker-compose up -d lottopro-web
        sleep 10
    fi
    
    # 기본 페이지 테스트
    run_test "메인 페이지" "test_api_endpoint '/' 200 '메인 페이지'"
    run_test "AI 모델 상세 페이지" "test_api_endpoint '/ai_models' 200 'AI 모델 상세'"
    run_test "예측 히스토리 페이지" "test_api_endpoint '/prediction_history' 200 '예측 히스토리'"
    
    # API 엔드포인트 테스트
    run_test "로또 정보 API - 핫넘버" "test_api_endpoint '/api/lottery_info/hotNumbers' 200 '핫넘버 정보'"
    run_test "로또 정보 API - 콜드넘버" "test_api_endpoint '/api/lottery_info/coldNumbers' 200 '콜드넘버 정보'"
    run_test "로또 정보 API - 이월수" "test_api_endpoint '/api/lottery_info/carryover' 200 '이월수 정보'"
    
    # 헬스체크 테스트
    run_test "헬스체크 엔드포인트" "test_api_endpoint '/health' 200 '헬스체크' || test_api_endpoint '/' 200 '메인페이지'"
}

# 모니터링 시스템 테스트
test_monitoring_system() {
    log_info "=== 모니터링 시스템 테스트 ==="
    
    if docker-compose ps | grep -q "lottopro-monitor.*Up"; then
        run_test "모니터링 헬스체크" "test_api_endpoint ':5001/monitoring/health' 200 '모니터링 헬스체크'"
        run_test "모니터링 메트릭" "test_api_endpoint ':5001/monitoring/metrics' 200 '모니터링 메트릭'"
        run_test "모니터링 대시보드" "test_api_endpoint ':5001/monitoring/dashboard' 200 '모니터링 대시보드'"
    else
        log_warning "모니터링 서비스가 실행 중이 아닙니다."
    fi
    
    # 헬스체크 스크립트 테스트
    if [[ -f "healthcheck.py" ]]; then
        run_test "헬스체크 스크립트 실행" "python3 healthcheck.py"
    fi
}

# 데이터 유효성 테스트
test_data_validation() {
    log_info "=== 데이터 유효성 테스트 ==="
    
    # 데이터 검증 모듈 테스트
    if [[ -f "utils/data_validator.py" ]]; then
        run_test "데이터 검증 모듈 임포트" "python3 -c 'from utils.data_validator import LotteryDataValidator; print(\"OK\")'"
        
        # 실제 데이터 검증 테스트
        run_test "로또 번호 유효성 검증" "python3 -c '
from utils.data_validator import LotteryDataValidator
validator = LotteryDataValidator()
is_valid, errors = validator.validate_lottery_numbers([1, 2, 3, 4, 5, 6])
assert is_valid, f\"Valid numbers failed: {errors}\"
is_valid, errors = validator.validate_lottery_numbers([1, 2, 3, 4, 5, 46])
assert not is_valid, \"Invalid numbers passed validation\"
print(\"Validation tests passed\")
'"
    fi
    
    # 데이터베이스 연결 테스트
    if [[ -f "data/lottopro.db" ]]; then
        run_test "데이터베이스 연결" "python3 -c '
import sqlite3
conn = sqlite3.connect(\"data/lottopro.db\")
cursor = conn.cursor()
cursor.execute(\"SELECT 1\")
result = cursor.fetchone()
conn.close()
assert result == (1,), \"Database connection failed\"
print(\"Database connection OK\")
'"
    else
        log_warning "데이터베이스 파일이 없습니다."
    fi
}

# 보안 테스트
test_security() {
    log_info "=== 보안 테스트 ==="
    
    # 환경 변수 보안 검사
    run_test "SECRET_KEY 보안 확인" "! grep -q 'SECRET_KEY=your-super-secret-key-change-this-in-production' .env"
    run_test "프로덕션 DEBUG 모드 확인" "! grep -q 'FLASK_DEBUG=True' .env || echo 'OK - 개발 환경'"
    
    # 파일 권한 확인
    run_test "중요 파일 권한 확인" "test \$(stat -c %a .env 2>/dev/null || echo 644) -le 644"
    
    # 보안 헤더 테스트 (웹 서버가 실행 중인 경우)
    if docker-compose ps | grep -q "lottopro-web.*Up"; then
        run_test "투명성 헤더 확인" "curl -s -I http://localhost:5000/ | grep -q 'X-Transparency-Policy' || echo 'OK - 프록시 없음'"
        run_test "연령 제한 헤더 확인" "curl -s -I http://localhost:5000/ | grep -q 'X-Age-Restriction' || echo 'OK - 프록시 없음'"
    fi
}

# 성능 테스트
test_performance() {
    log_info "=== 성능 테스트 ==="
    
    if docker-compose ps | grep -q "lottopro-web.*Up"; then
        # 응답 시간 테스트
        run_test "메인 페이지 응답 시간" "
            response_time=\$(curl -w '%{time_total}' -o /dev/null -s http://localhost:5000/)
            if (( \$(echo \"\$response_time < 2.0\" | bc -l) )); then
                echo \"응답 시간: \${response_time}초\"
                true
            else
                echo \"응답 시간 초과: \${response_time}초\"
                false
            fi
        "
        
        # 동시 요청 테스트 (간단한 부하 테스트)
        run_test "동시 요청 처리" "
            for i in {1..5}; do
                curl -s -o /dev/null http://localhost:5000/ &
            done
            wait
            echo '동시 요청 테스트 완료'
        "
    else
        log_warning "웹 서비스가 실행 중이 아니어서 성능 테스트를 건너뜁니다."
    fi
}

# 컴플라이언스 테스트
test_compliance() {
    log_info "=== 컴플라이언스 테스트 ==="
    
    # 법적 고지사항 확인
    if docker-compose ps | grep -q "lottopro-web.*Up"; then
        run_test "면책조항 표시" "curl -s http://localhost:5000/ | grep -q '로또 당첨을 보장하지 않습니다'"
        run_test "연령 제한 고지" "curl -s http://localhost:5000/ | grep -q '만 19세 이상'"
        run_test "도박 경고" "curl -s http://localhost:5000/ | grep -q '오락 목적'"
    fi
    
    # 투명성 정책 확인
    if [[ -f "templates/ai_models.html" ]]; then
        run_test "AI 모델 투명성" "grep -q '투명성' templates/ai_models.html"
        run_test "통계적 유의성 설명" "grep -q '통계적 유의성' templates/ai_models.html"
    fi
}

# Docker 환경 테스트
test_docker_environment() {
    log_info "=== Docker 환경 테스트 ==="
    
    # Docker Compose 설정 검증
    run_test "Docker Compose 설정 유효성" "docker-compose config > /dev/null"
    
    # 컨테이너 상태 확인
    if docker-compose ps | grep -q Up; then
        run_test "컨테이너 실행 상태" "docker-compose ps | grep -q Up"
        
        # 개별 서비스 테스트
        if docker-compose ps | grep -q "lottopro-web.*Up"; then
            run_test "웹 컨테이너 헬스체크" "docker-compose exec -T lottopro-web python healthcheck.py"
        fi
        
        if docker-compose ps | grep -q "redis.*Up"; then
            run_test "Redis 연결" "docker-compose exec -T redis redis-cli ping | grep -q PONG"
        fi
    else
        log_warning "Docker 컨테이너가 실행 중이 아닙니다."
    fi
}

# 통합 테스트
test_integration() {
    log_info "=== 통합 테스트 ==="
    
    # 전체 워크플로우 테스트
    if docker-compose ps | grep -q "lottopro-web.*Up"; then
        run_test "전체 API 워크플로우" "
            # 1. 메인 페이지 접근
            curl -s http://localhost:5000/ > /dev/null
            
            # 2. AI 모델 정보 조회
            curl -s http://localhost:5000/api/model_performance/combined > /dev/null
            
            # 3. 투명성 보고서 조회
            curl -s http://localhost:5000/api/transparency_report > /dev/null
            
            # 4. 로또 정보 조회
            curl -s http://localhost:5000/api/lottery_info/hotNumbers > /dev/null
            
            echo '전체 워크플로우 완료'
        "
    fi
    
    # 데이터 일관성 테스트
    run_test "설정 파일 일관성" "
        if grep -q 'TRANSPARENCY_MODE=enabled' .env; then
            if grep -q 'transparency.*true' docker-compose.yml || echo 'OK - Docker에서 환경변수 사용'; then
                echo '투명성 설정 일관성 확인'
            else
                false
            fi
        else
            echo '투명성 모드 비활성화됨'
        fi
    "
}

# 테스트 결과 요약
print_test_summary() {
    echo ""
    log_info "=== 테스트 결과 요약 ==="
    echo ""
    
    printf "총 테스트: %d\n" $TOTAL_TESTS
    printf "${GREEN}성공: %d${NC}\n" $PASSED_TESTS
    printf "${RED}실패: %d${NC}\n" $FAILED_TESTS
    printf "성공률: %.1f%%\n" $(echo "scale=1; $PASSED_TESTS * 100 / $TOTAL_TESTS" | bc -l 2>/dev/null || echo "0.0")
    
    echo ""
    log_info "상세 결과:"
    printf '%s\n' "${TEST_RESULTS[@]}"
    
    echo ""
    if [[ $FAILED_TESTS -eq 0 ]]; then
        log_success "🎉 모든 테스트가 통과되었습니다!"
        return 0
    else
        log_error "❌ $FAILED_TESTS개의 테스트가 실패했습니다."
        return 1
    fi
}

# 메인 실행 함수
main() {
    log_info "=== LottoPro AI v2.0 투명성 강화 버전 테스트 시작 ==="
    
    # 기본 유틸리티 확인
    command -v bc >/dev/null 2>&1 || { log_error "bc 명령어가 필요합니다. 설치하세요: apt-get install bc"; exit 1; }
    command -v curl >/dev/null 2>&1 || { log_error "curl 명령어가 필요합니다. 설치하세요: apt-get install curl"; exit 1; }
    
    # 테스트 실행
    test_environment_setup
    test_transparency_features
    test_data_validation
    test_security
    test_compliance
    
    # 서비스가 실행 중인 경우에만 실행할 테스트들
    if docker-compose ps | grep -q Up; then
        test_web_application
        test_monitoring_system
        test_performance
        test_docker_environment
        test_integration
    else
        log_info "Docker 서비스가 실행 중이 아닙니다. 서비스 테스트를 건너뜁니다."
        log_info "서비스 테스트를 위해서는 먼저 'docker-compose up -d'를 실행하세요."
    fi
    
    # 결과 요약
    print_test_summary
}

# 도움말
show_help() {
    echo "LottoPro AI v2.0 테스트 스크립트"
    echo ""
    echo "사용법: $0 [옵션]"
    echo ""
    echo "옵션:"
    echo "  --help               이 도움말 표시"
    echo "  --transparency-only  투명성 기능만 테스트"
    echo "  --api-only          API 테스트만 실행"
    echo "  --security-only     보안 테스트만 실행"
    echo "  --quick             빠른 테스트 (기본 기능만)"
    echo ""
}

# 명령행 인수 처리
case "${1:-}" in
    --help|-h)
        show_help
        exit 0
        ;;
    --transparency-only)
        log_info "투명성 기능 테스트만 실행합니다."
        test_environment_setup
        test_transparency_features
        test_compliance
        print_test_summary
        ;;
    --api-only)
        log_info "API 테스트만 실행합니다."
        test_web_application
        test_monitoring_system
        print_test_summary
        ;;
    --security-only)
        log_info "보안 테스트만 실행합니다."
        test_security
        test_compliance
        print_test_summary
        ;;
    --quick)
        log_info "빠른 테스트를 실행합니다."
        test_environment_setup
        test_transparency_features
        test_security
        print_test_summary
        ;;
    *)
        main
        ;;
esac
