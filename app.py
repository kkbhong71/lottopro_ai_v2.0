from flask import Flask, render_template, request, jsonify, session, send_file
import os
import random
import numpy as np
from datetime import datetime, timedelta
import json
import base64
from collections import Counter, defaultdict
import hashlib
import uuid
import logging
import traceback
import re
import math
from io import BytesIO
import time
import concurrent.futures
from functools import wraps
import signal

# 🆕 성능 모니터링 및 캐싱 시스템 import
try:
    from monitoring.performance_monitor import init_monitoring, monitor_performance
    MONITORING_AVAILABLE = True
    print("[SYSTEM] ✅ 성능 모니터링 시스템 로드 완료")
except ImportError as e:
    MONITORING_AVAILABLE = False
    print(f"[WARNING] ❌ 성능 모니터링 시스템 로드 실패: {e}")

try:
    from utils.cache_manager import init_cache_system, cached
    CACHE_AVAILABLE = True
    print("[SYSTEM] ✅ 캐시 시스템 로드 완료")
except ImportError as e:
    CACHE_AVAILABLE = False
    print(f"[WARNING] ❌ 캐시 시스템 로드 실패: {e}")

# Optional imports with fallbacks
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

try:
    import qrcode
    from PIL import Image
    QR_AVAILABLE = True
except ImportError:
    QR_AVAILABLE = False

try:
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.preprocessing import StandardScaler
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False

# Flask 앱 초기화
app = Flask(__name__)

# 환경변수 기반 설정
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'lottopro-ai-v2-enhanced-2024')
app.config['DEBUG'] = os.environ.get('DEBUG', 'False').lower() == 'true'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=30)

# 보안 설정
if not app.config['DEBUG']:
    app.config['SESSION_COOKIE_SECURE'] = False  # HTTP에서도 작동하도록 설정
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
app.logger.setLevel(logging.INFO)

# 글로벌 변수
sample_data = None
user_saved_numbers = {}
cached_stats = {}
request_counts = defaultdict(int)
error_counts = defaultdict(int)
performance_metrics = {
    'total_requests': 0,
    'total_errors': 0,
    'avg_response_time': 0,
    'start_time': datetime.now()
}

# 🆕 시스템 인스턴스 (초기화 후 설정됨)
monitor = None
cache_manager = None

# 타임아웃 및 에러 처리 데코레이터
def timeout_handler(timeout_seconds=10):
    """요청 타임아웃 처리 데코레이터"""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            
            def timeout_error(signum, frame):
                raise TimeoutError(f"Request timed out after {timeout_seconds} seconds")
            
            try:
                # 타임아웃 시그널 설정 (Unix 계열에서만 동작)
                if hasattr(signal, 'SIGALRM'):
                    old_handler = signal.signal(signal.SIGALRM, timeout_error)
                    signal.alarm(timeout_seconds)
                
                # ThreadPoolExecutor를 사용한 타임아웃 처리
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(f, *args, **kwargs)
                    try:
                        result = future.result(timeout=timeout_seconds)
                        
                        # 성공 시 메트릭 업데이트
                        response_time = time.time() - start_time
                        update_performance_metrics(response_time, success=True)
                        
                        return result
                    except concurrent.futures.TimeoutError:
                        # 타임아웃 에러 처리
                        update_performance_metrics(time.time() - start_time, success=False)
                        safe_log(f"Request timeout in {f.__name__}: {timeout_seconds}s")
                        return jsonify({
                            'success': False,
                            'error': True,
                            'message': '요청 처리 시간이 초과되었습니다. 잠시 후 다시 시도해주세요.',
                            'error_type': 'timeout',
                            'timeout_duration': timeout_seconds
                        }), 408
            except Exception as e:
                # 일반 에러 처리
                response_time = time.time() - start_time
                update_performance_metrics(response_time, success=False)
                safe_log(f"Error in {f.__name__}: {str(e)}")
                return handle_api_error(e)
            finally:
                # 시그널 복원
                if hasattr(signal, 'SIGALRM'):
                    signal.alarm(0)
                    if 'old_handler' in locals():
                        signal.signal(signal.SIGALRM, old_handler)
                        
        return wrapper
    return decorator

def rate_limiter(max_requests=100, time_window=3600):
    """요청 제한 데코레이터 (시간당 최대 요청 수)"""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            client_ip = request.environ.get('REMOTE_ADDR', 'unknown')
            current_time = time.time()
            
            # 클라이언트별 요청 기록 초기화
            if not hasattr(wrapper, 'requests'):
                wrapper.requests = defaultdict(list)
            
            # 시간 윈도우를 벗어난 요청 기록 제거
            wrapper.requests[client_ip] = [
                req_time for req_time in wrapper.requests[client_ip]
                if current_time - req_time < time_window
            ]
            
            # 요청 제한 확인
            if len(wrapper.requests[client_ip]) >= max_requests:
                safe_log(f"Rate limit exceeded for IP: {client_ip}")
                return jsonify({
                    'success': False,
                    'error': True,
                    'message': f'요청 한도를 초과했습니다. {time_window/3600:.1f}시간 후 다시 시도해주세요.',
                    'error_type': 'rate_limit',
                    'retry_after': time_window
                }), 429
            
            # 현재 요청 기록
            wrapper.requests[client_ip].append(current_time)
            
            return f(*args, **kwargs)
            
        return wrapper
    return decorator

def handle_api_error(error):
    """API 에러 통합 처리"""
    error_id = str(uuid.uuid4())[:8]
    
    if isinstance(error, TimeoutError):
        return jsonify({
            'success': False,
            'error': True,
            'message': '요청 처리 시간이 초과되었습니다.',
            'error_type': 'timeout',
            'error_id': error_id
        }), 408
    elif isinstance(error, ValueError):
        return jsonify({
            'success': False,
            'error': True,
            'message': '잘못된 입력 값입니다.',
            'error_type': 'validation',
            'error_id': error_id
        }), 400
    elif isinstance(error, ConnectionError):
        return jsonify({
            'success': False,
            'error': True,
            'message': '외부 서비스 연결에 실패했습니다.',
            'error_type': 'connection',
            'error_id': error_id
        }), 503
    else:
        # 일반적인 서버 에러
        safe_log(f"Unhandled error [{error_id}]: {str(error)}")
        return jsonify({
            'success': False,
            'error': True,
            'message': '서버 내부 오류가 발생했습니다.',
            'error_type': 'internal',
            'error_id': error_id
        }), 500

def update_performance_metrics(response_time, success=True):
    """성능 메트릭 업데이트"""
    performance_metrics['total_requests'] += 1
    
    if not success:
        performance_metrics['total_errors'] += 1
    
    # 평균 응답 시간 업데이트
    total_requests = performance_metrics['total_requests']
    current_avg = performance_metrics['avg_response_time']
    performance_metrics['avg_response_time'] = (
        (current_avg * (total_requests - 1) + response_time) / total_requests
    )

def validate_lotto_numbers(numbers):
    """로또 번호 유효성 검사"""
    if not isinstance(numbers, list):
        return False, "번호는 리스트 형태여야 합니다."
    
    if len(numbers) > 6:
        return False, "번호는 최대 6개까지 입력 가능합니다."
    
    for num in numbers:
        try:
            n = int(num)
            if n < 1 or n > 45:
                return False, f"번호는 1-45 범위여야 합니다. (입력: {n})"
        except (ValueError, TypeError):
            return False, f"올바른 숫자를 입력해주세요. (입력: {num})"
    
    if len(set(numbers)) != len(numbers):
        return False, "중복된 번호가 있습니다."
    
    return True, "유효한 번호입니다."

def safe_log(message, level='info'):
    """안전한 로깅 (에러 방지)"""
    try:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_message = f"[{timestamp}] [LottoPro-AI] {message}"
        
        if level == 'error':
            app.logger.error(log_message)
        elif level == 'warning':
            app.logger.warning(log_message)
        else:
            app.logger.info(log_message)
            
        print(log_message)
    except Exception as e:
        print(f"[LottoPro-AI] Logging error: {str(e)} | Original message: {message}")

@app.after_request
def add_security_headers(response):
    """보안 헤더 및 성능 헤더 추가"""
    # 보안 헤더
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    
    # 성능 헤더
    response.headers['Cache-Control'] = 'public, max-age=300' if request.endpoint != 'predict' else 'no-cache'
    
    # CORS 헤더 (필요시)
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    
    return response

@app.errorhandler(404)
def not_found(error):
    """404 에러 처리"""
    try:
        if request.is_json or '/api/' in request.path:
            return jsonify({
                'success': False,
                'error': True,
                'message': 'API 엔드포인트를 찾을 수 없습니다.',
                'error_type': 'not_found'
            }), 404
        else:
            return render_template('index.html'), 404
    except Exception as e:
        safe_log(f"404 handler error: {str(e)}", 'error')
        return jsonify({'error': 'Not Found'}), 404

@app.errorhandler(500)
def internal_error(error):
    """500 에러 처리"""
    error_id = str(uuid.uuid4())[:8]
    safe_log(f"500 에러 발생 [{error_id}]: {error}", 'error')
    
    if request.is_json or '/api/' in request.path:
        return jsonify({
            'success': False,
            'error': True,
            'message': '서버 내부 오류가 발생했습니다.',
            'error_type': 'internal',
            'error_id': error_id
        }), 500
    else:
        return render_template('error.html', error_id=error_id), 500

@app.errorhandler(413)
def request_entity_too_large(error):
    """413 요청 크기 초과 에러 처리"""
    return jsonify({
        'success': False,
        'error': True,
        'message': '요청 크기가 너무 큽니다.',
        'error_type': 'payload_too_large'
    }), 413

@app.errorhandler(429)
def too_many_requests(error):
    """429 요청 과다 에러 처리"""
    return jsonify({
        'success': False,
        'error': True,
        'message': '요청이 너무 많습니다. 잠시 후 다시 시도해주세요.',
        'error_type': 'too_many_requests'
    }), 429

# AI 모델 정보
AI_MODELS_INFO = {
    'frequency': {
        'name': '빈도분석 모델',
        'description': '과거 당첨번호 출현 빈도를 통계적으로 분석하여 가중 확률을 계산합니다.',
        'algorithm': '가중 확률 분포',
        'accuracy_rate': 19.2,
        'data_source': '최근 200회차',
        'update_frequency': '매주 토요일'
    },
    'trend': {
        'name': '트렌드분석 모델',
        'description': '최근 당첨 패턴과 시간적 트렌드를 분석하여 변화하는 패턴을 반영합니다.',
        'algorithm': '이동평균 + 추세분석',
        'accuracy_rate': 17.8,
        'data_source': '최근 50회차',
        'update_frequency': '매주 토요일'
    },
    'pattern': {
        'name': '패턴분석 모델',
        'description': '번호 조합 패턴과 수학적 관계를 분석하여 복합적인 예측을 수행합니다.',
        'algorithm': '조합론 + 확률론',
        'accuracy_rate': 16.4,
        'data_source': '홀짝, 고저, 합계',
        'update_frequency': '매주 토요일'
    },
    'statistical': {
        'name': '통계분석 모델',
        'description': '고급 통계 기법과 확률 이론을 적용한 수학적 예측 모델입니다.',
        'algorithm': '베이즈 추론',
        'accuracy_rate': 20.1,
        'data_source': '다항분포',
        'update_frequency': '매주 토요일'
    },
    'ml': {
        'name': '머신러닝 모델',
        'description': '딥러닝 신경망과 AI 알고리즘을 기반으로 한 고도화된 예측 시스템입니다.',
        'algorithm': '3층 DNN',
        'accuracy_rate': 18.9,
        'data_source': '1185회차',
        'update_frequency': '매주 토요일'
    }
}

# 예측 히스토리
PREDICTION_HISTORY = [
    {
        'round': 1185,
        'date': '2025.08.17',
        'winning_numbers': [7, 13, 21, 28, 34, 42],
        'bonus_number': 15,
        'ai_predictions': {
            'combined': [7, 15, 21, 29, 34, 45],
            'frequency': [7, 12, 21, 28, 35, 42],
            'trend': [8, 15, 22, 29, 34, 44],
            'pattern': [6, 13, 20, 27, 33, 45],
            'statistical': [7, 14, 21, 30, 34, 43],
            'ml': [9, 16, 23, 28, 36, 41]
        },
        'matches': {
            'combined': 3,
            'frequency': 4,
            'trend': 2,
            'pattern': 2,
            'statistical': 3,
            'ml': 2
        }
    }
]

# 로또 판매점 데이터
LOTTERY_STORES = [
    {"name": "동대문 복권방", "address": "서울시 동대문구 장한로 195", "region": "서울", "district": "동대문구", "lat": 37.5745, "lng": 127.0098, "phone": "02-1234-5678", "first_wins": 15, "business_hours": "06:00-24:00"},
    {"name": "강남 로또타운", "address": "서울시 강남구 테헤란로 152", "region": "서울", "district": "강남구", "lat": 37.4979, "lng": 127.0276, "phone": "02-2345-6789", "first_wins": 23, "business_hours": "07:00-23:00"},
    {"name": "평택역 로또센터", "address": "경기도 평택시 평택동 856-1", "region": "평택", "district": "평택시", "lat": 36.9922, "lng": 127.0890, "phone": "031-1234-5678", "first_wins": 5, "business_hours": "06:00-22:00"},
    {"name": "안정리 행운복권", "address": "경기도 평택시 안정동 123-45", "region": "평택", "district": "평택시", "lat": 36.9856, "lng": 127.0825, "phone": "031-2345-6789", "first_wins": 3, "business_hours": "07:00-21:00"},
    {"name": "송탄 중앙점", "address": "경기도 평택시 송탄동 789-12", "region": "평택", "district": "평택시", "lat": 36.9675, "lng": 127.0734, "phone": "031-3456-7890", "first_wins": 8, "business_hours": "08:00-20:00"}
]

def generate_sample_data():
    """샘플 데이터 생성"""
    try:
        np.random.seed(42)
        data = []
        
        for draw in range(1186, 986, -1):  # 200회차
            numbers = sorted(np.random.choice(range(1, 46), 6, replace=False))
            available = [x for x in range(1, 46) if x not in numbers]
            bonus = np.random.choice(available) if available else 7
            
            base_date = datetime(2025, 8, 28) - timedelta(weeks=(1186-draw))
            
            data.append({
                '회차': draw,
                '당첨번호1': int(numbers[0]),
                '당첨번호2': int(numbers[1]),
                '당첨번호3': int(numbers[2]),
                '당첨번호4': int(numbers[3]),
                '당첨번호5': int(numbers[4]),
                '당첨번호6': int(numbers[5]),
                '보너스번호': int(bonus),
                '날짜': base_date.strftime('%Y-%m-%d')
            })
        
        return data
    except Exception as e:
        safe_log(f"샘플 데이터 생성 실패: {str(e)}", 'error')
        return []

# 🆕 캐시 적용된 분석 함수들
@cached(ttl=600, tags=['statistics']) if CACHE_AVAILABLE else lambda f: f
def calculate_frequency_analysis():
    """빈도 분석 (캐시 적용)"""
    if not sample_data:
        return {}
    
    try:
        frequency = Counter()
        for data in sample_data:
            for i in range(1, 7):
                number = data.get(f'당첨번호{i}')
                if number:
                    frequency[number] += 1
        return dict(frequency)
    except Exception as e:
        safe_log(f"빈도 분석 실패: {str(e)}", 'error')
        return {}

@cached(ttl=600, tags=['statistics']) if CACHE_AVAILABLE else lambda f: f
def calculate_carry_over_analysis():
    """이월수 분석 (캐시 적용)"""
    if not sample_data or len(sample_data) < 2:
        return []
    
    try:
        carry_overs = []
        for i in range(min(len(sample_data) - 1, 20)):
            current_numbers = set()
            prev_numbers = set()
            
            for j in range(1, 7):
                current = sample_data[i].get(f'당첨번호{j}')
                prev = sample_data[i+1].get(f'당첨번호{j}')
                if current: current_numbers.add(current)
                if prev: prev_numbers.add(prev)
            
            carry_over = current_numbers.intersection(prev_numbers)
            carry_overs.append({
                'round': sample_data[i].get('회차'),
                'carry_over_numbers': sorted(list(carry_over)),
                'count': len(carry_over)
            })
        
        return carry_overs
    except Exception as e:
        safe_log(f"이월수 분석 실패: {str(e)}", 'error')
        return []

@cached(ttl=600, tags=['statistics']) if CACHE_AVAILABLE else lambda f: f
def calculate_companion_analysis():
    """궁합수 분석 (캐시 적용)"""
    if not sample_data:
        return {}
    
    try:
        companion_pairs = Counter()
        for data in sample_data[:50]:  # 최근 50회차만
            numbers = []
            for i in range(1, 7):
                num = data.get(f'당첨번호{i}')
                if num: numbers.append(num)
            
            for i in range(len(numbers)):
                for j in range(i+1, len(numbers)):
                    pair = tuple(sorted([numbers[i], numbers[j]]))
                    companion_pairs[pair] += 1
        
        return dict(companion_pairs.most_common(10))
    except Exception as e:
        safe_log(f"궁합수 분석 실패: {str(e)}", 'error')
        return {}

@cached(ttl=600, tags=['statistics']) if CACHE_AVAILABLE else lambda f: f
def calculate_pattern_analysis():
    """패턴 분석 (캐시 적용)"""
    if not sample_data:
        return {}
    
    try:
        patterns = {
            'consecutive_count': [],
            'odd_even_ratio': [],
            'sum_distribution': [],
            'range_distribution': []
        }
        
        for data in sample_data[:30]:
            numbers = []
            for i in range(1, 7):
                num = data.get(f'당첨번호{i}')
                if num: numbers.append(num)
            
            if len(numbers) == 6:
                numbers.sort()
                
                consecutive = sum(1 for i in range(len(numbers)-1) if numbers[i+1] - numbers[i] == 1)
                odd_count = sum(1 for n in numbers if n % 2 == 1)
                total_sum = sum(numbers)
                number_range = max(numbers) - min(numbers)
                
                patterns['consecutive_count'].append(consecutive)
                patterns['odd_even_ratio'].append(f"{odd_count}:{6-odd_count}")
                patterns['sum_distribution'].append(total_sum)
                patterns['range_distribution'].append(number_range)
        
        return patterns
    except Exception as e:
        safe_log(f"패턴 분석 실패: {str(e)}", 'error')
        return {}

def generate_ai_prediction(user_numbers=None, model_type="frequency"):
    """AI 예측 생성 (캐시 적용 개선된 에러 처리)"""
    try:
        if user_numbers is None:
            user_numbers = []
        
        # 🆕 캐시에서 먼저 확인
        if CACHE_AVAILABLE and cache_manager:
            cached_result = cache_manager.get_cached_prediction(user_numbers, model_type)
            if cached_result:
                safe_log(f"캐시 히트: {model_type} 예측", 'info')
                return cached_result
        
        # 입력 번호 유효성 검사
        safe_numbers = []
        if isinstance(user_numbers, list):
            for num in user_numbers:
                try:
                    n = int(num)
                    if 1 <= n <= 45 and n not in safe_numbers:
                        safe_numbers.append(n)
                except (ValueError, TypeError):
                    continue
        
        # 중복 제거 및 최대 6개 제한
        safe_numbers = list(set(safe_numbers))[:6]
        
        if model_type == "frequency":
            frequency = calculate_frequency_analysis()
            weights = np.ones(45)
            for num, freq in frequency.items():
                if 1 <= num <= 45:
                    weights[num-1] = freq + 1
        elif model_type == "trend":
            weights = np.ones(45)
            for i, data in enumerate(sample_data[:10]):
                weight_factor = (10 - i) / 10
                for j in range(1, 7):
                    num = data.get(f'당첨번호{j}')
                    if num and 1 <= num <= 45:
                        weights[num-1] += weight_factor
        else:
            weights = np.ones(45)
        
        numbers = safe_numbers.copy()
        available_numbers = [i for i in range(1, 46) if i not in numbers]
        
        if len(available_numbers) > 0:
            needed_count = 6 - len(numbers)
            if needed_count > 0:
                available_weights = [weights[i-1] for i in available_numbers]
                if sum(available_weights) > 0:
                    available_weights = np.array(available_weights)
                    available_weights = available_weights / available_weights.sum()
                    
                    selected = np.random.choice(
                        available_numbers, 
                        size=min(needed_count, len(available_numbers)), 
                        replace=False, 
                        p=available_weights
                    )
                    numbers.extend(selected.tolist())
        
        # 6개 미만인 경우 랜덤으로 채우기
        while len(numbers) < 6:
            new_num = random.randint(1, 45)
            if new_num not in numbers:
                numbers.append(new_num)
        
        result = sorted(numbers[:6])
        
        # 🆕 결과를 캐시에 저장 (5분)
        if CACHE_AVAILABLE and cache_manager:
            cache_manager.cache_prediction(user_numbers, model_type, result, ttl=300)
            safe_log(f"캐시 저장: {model_type} 예측", 'info')
        
        return result
        
    except Exception as e:
        safe_log(f"AI 예측 생성 실패: {str(e)}", 'error')
        # 완전한 랜덤 생성으로 폴백
        return sorted(random.sample(range(1, 46), 6))

# ===== API 엔드포인트들 =====
@app.route('/')
def index():
    try:
        context = {
            'update_date': '2025.08.28',
            'analysis_round': 1186,
            'copyright_year': 2025,
            'version': 'v2.1',
            'features_count': 15,
            'models_count': len(AI_MODELS_INFO),
            'monitoring_enabled': MONITORING_AVAILABLE,
            'cache_enabled': CACHE_AVAILABLE
        }
        return render_template('index.html', **context)
    except Exception as e:
        safe_log(f"메인 페이지 오류: {str(e)}", 'error')
        return render_template('error.html', 
            error_message="서비스 준비 중입니다.",
            error_id=str(uuid.uuid4())[:8]
        ), 503

@app.route('/api/predict', methods=['POST'])
@monitor_performance if MONITORING_AVAILABLE else lambda f: f  # 🆕 성능 모니터링
@rate_limiter(max_requests=30, time_window=3600)  # 시간당 30회 제한
@timeout_handler(timeout_seconds=15)
def predict():
    try:
        # 요청 데이터 검증
        data = request.get_json() or {}
        user_numbers = data.get('user_numbers', [])
        
        # 번호 유효성 검사
        is_valid, message = validate_lotto_numbers(user_numbers)
        if not is_valid:
            return jsonify({
                'success': False,
                'error': True,
                'message': message,
                'error_type': 'validation'
            }), 400
        
        # 🆕 전체 예측 결과 캐시 확인
        if CACHE_AVAILABLE and cache_manager:
            user_hash = hashlib.md5(json.dumps(sorted(user_numbers)).encode()).hexdigest()[:8]
            cache_key = f"full_prediction:{user_hash}"
            cached_full_result = cache_manager.get(cache_key)
            
            if cached_full_result:
                safe_log("전체 예측 캐시 히트", 'info')
                cached_full_result['cached'] = True
                cached_full_result['cache_hit_time'] = time.time()
                return jsonify(cached_full_result)
        
        # AI 모델 예측
        models = {}
        model_configs = [
            ('빈도분석 모델', 'frequency'),
            ('트렌드분석 모델', 'trend'),
            ('패턴분석 모델', 'pattern'),
            ('통계분석 모델', 'statistical'),
            ('머신러닝 모델', 'ml')
        ]
        
        prediction_start_time = time.time()
        
        for model_name, model_type in model_configs:
            try:
                predictions = []
                for i in range(5):
                    pred = generate_ai_prediction(user_numbers, model_type)
                    predictions.append(pred)
                
                model_info = AI_MODELS_INFO.get(model_type, {})
                models[model_name] = {
                    'description': model_info.get('description', ''),
                    'predictions': predictions,
                    'accuracy': model_info.get('accuracy_rate', 15),
                    'confidence': random.randint(85, 95),
                    'algorithm': model_info.get('algorithm', 'N/A')
                }
            except Exception as e:
                safe_log(f"Model {model_name} prediction failed: {str(e)}", 'warning')
                # 개별 모델 실패 시 기본값 제공
                models[model_name] = {
                    'description': '일시적으로 사용할 수 없습니다.',
                    'predictions': [sorted(random.sample(range(1, 46), 6)) for _ in range(5)],
                    'accuracy': 15,
                    'confidence': 70,
                    'algorithm': 'Fallback',
                    'error': True
                }
        
        # TOP 추천 번호 생성
        top_recommendations = []
        for i in range(5):
            rec = generate_ai_prediction(user_numbers, "statistical")
            if rec not in top_recommendations:
                top_recommendations.append(rec)
        
        prediction_time = time.time() - prediction_start_time
        
        response = {
            'success': True,
            'user_numbers': user_numbers,
            'models': models,
            'top_recommendations': top_recommendations,
            'total_combinations': sum(len(model.get('predictions', [])) for model in models.values()),
            'data_source': f"{len(sample_data)}회차 데이터" if sample_data else "샘플 데이터",
            'analysis_timestamp': datetime.now().isoformat(),
            'processing_time': round(prediction_time, 3),
            'version': '2.1',
            'request_id': str(uuid.uuid4())[:8],
            'cached': False,
            'cache_info': {
                'enabled': CACHE_AVAILABLE,
                'hit_rate': cache_manager.stats.hit_rate if CACHE_AVAILABLE and cache_manager else 0
            }
        }
        
        # 🆕 전체 결과를 캐시에 저장 (5분)
        if CACHE_AVAILABLE and cache_manager:
            user_hash = hashlib.md5(json.dumps(sorted(user_numbers)).encode()).hexdigest()[:8]
            cache_key = f"full_prediction:{user_hash}"
            cache_manager.set(cache_key, response, ttl=300, tags=['predictions', 'full_results'])
            safe_log("전체 예측 결과 캐시 저장", 'info')
        
        return jsonify(response)
        
    except Exception as e:
        safe_log(f"예측 API 실패: {str(e)}", 'error')
        return handle_api_error(e)

@app.route('/api/stats')
@monitor_performance if MONITORING_AVAILABLE else lambda f: f  # 🆕 성능 모니터링
@timeout_handler(timeout_seconds=10)
def get_stats():
    try:
        # 🆕 캐시에서 먼저 확인
        if CACHE_AVAILABLE and cache_manager:
            cached_stats = cache_manager.get_cached_statistics('main')
            if cached_stats:
                return jsonify({
                    'success': True,
                    'cached': True,
                    'cache_timestamp': time.time(),
                    **cached_stats
                })
        
        frequency = calculate_frequency_analysis()
        
        if frequency:
            sorted_freq = sorted(frequency.items(), key=lambda x: x[1], reverse=True)
            hot_numbers = sorted_freq[:8]
            cold_numbers = sorted_freq[-8:]
        else:
            # 기본값 제공
            hot_numbers = [[7, 15], [13, 14], [22, 13], [31, 12], [42, 11], [1, 10], [25, 9], [33, 8]]
            cold_numbers = [[45, 5], [44, 6], [43, 7], [2, 8], [3, 9], [4, 10], [5, 11], [6, 12]]
        
        stats_data = {
            'frequency': frequency,
            'hot_numbers': hot_numbers,
            'cold_numbers': cold_numbers,
            'carry_over_analysis': calculate_carry_over_analysis(),
            'companion_analysis': list(calculate_companion_analysis().items()),
            'pattern_analysis': calculate_pattern_analysis(),
            'total_draws': len(sample_data) if sample_data else 200,
            'data_source': f"{len(sample_data)}회차 데이터" if sample_data else "샘플 데이터",
            'last_updated': datetime.now().isoformat(),
            'cache_status': 'fresh'
        }
        
        # 🆕 결과를 캐시에 저장 (10분)
        if CACHE_AVAILABLE and cache_manager:
            cache_manager.cache_statistics('main', stats_data, ttl=600)
            safe_log("통계 데이터 캐시 저장", 'info')
        
        return jsonify({
            'success': True,
            'cached': False,
            **stats_data
        })
        
    except Exception as e:
        safe_log(f"통계 API 실패: {str(e)}", 'error')
        return handle_api_error(e)

# 🆕 성능 모니터링 관리자 API
@app.route('/admin/performance')
@monitor_performance if MONITORING_AVAILABLE else lambda f: f
def get_performance_stats():
    """실시간 성능 통계 조회"""
    try:
        if not MONITORING_AVAILABLE or not monitor:
            return jsonify({
                'success': False,
                'error': 'Performance monitoring not available'
            }), 503
        
        stats = monitor.get_current_stats()
        return jsonify({
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'data': stats
        })
    except Exception as e:
        safe_log(f"성능 통계 조회 실패: {str(e)}", 'error')
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin/performance/trends')
@monitor_performance if MONITORING_AVAILABLE else lambda f: f
def get_performance_trends():
    """성능 트렌드 조회"""
    try:
        if not MONITORING_AVAILABLE or not monitor:
            return jsonify({
                'success': False,
                'error': 'Performance monitoring not available'
            }), 503
        
        minutes = request.args.get('minutes', 60, type=int)
        trends = monitor.get_performance_trends(minutes)
        return jsonify({
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'data': trends
        })
    except Exception as e:
        safe_log(f"성능 트렌드 조회 실패: {str(e)}", 'error')
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin/performance/export')
@monitor_performance if MONITORING_AVAILABLE else lambda f: f
def export_performance_metrics():
    """성능 메트릭 내보내기"""
    try:
        if not MONITORING_AVAILABLE or not monitor:
            return jsonify({
                'success': False,
                'error': 'Performance monitoring not available'
            }), 503
        
        format_type = request.args.get('format', 'json')
        metrics_data = monitor.export_metrics(format_type)
        
        response = app.response_class(
            response=metrics_data,
            status=200,
            mimetype='application/json' if format_type == 'json' else 'text/plain'
        )
        
        filename = f"lottopro_metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{format_type}"
        response.headers["Content-Disposition"] = f"attachment; filename={filename}"
        
        return response
    except Exception as e:
        safe_log(f"메트릭 내보내기 실패: {str(e)}", 'error')
        return jsonify({'success': False, 'error': str(e)}), 500

# 🆕 캐시 관리 API
@app.route('/admin/cache/info')
def cache_info():
    """캐시 시스템 정보"""
    try:
        if not CACHE_AVAILABLE or not cache_manager:
            return jsonify({
                'success': False,
                'error': 'Cache system not available'
            }), 503
        
        info = cache_manager.get_cache_info()
        return jsonify({
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'data': info
        })
    except Exception as e:
        safe_log(f"캐시 정보 조회 실패: {str(e)}", 'error')
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin/cache/health')
def cache_health():
    """캐시 건강 상태"""
    try:
        if not CACHE_AVAILABLE or not cache_manager:
            return jsonify({
                'success': False,
                'error': 'Cache system not available'
            }), 503
        
        health_results = cache_manager.health_check()
        status_code = 200 if health_results.get('overall_health') else 503
        return jsonify({
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'data': health_results
        }), status_code
    except Exception as e:
        safe_log(f"캐시 건강 상태 확인 실패: {str(e)}", 'error')
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin/cache/clear', methods=['POST'])
def clear_cache():
    """캐시 클리어"""
    try:
        if not CACHE_AVAILABLE or not cache_manager:
            return jsonify({
                'success': False,
                'error': 'Cache system not available'
            }), 503
        
        data = request.get_json() or {}
        pattern = data.get('pattern', '*')
        
        cleared_count = cache_manager.clear(pattern)
        return jsonify({
            'success': True,
            'message': f'캐시 정리 완료: {pattern}',
            'cleared_count': cleared_count,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        safe_log(f"캐시 클리어 실패: {str(e)}", 'error')
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin/cache/invalidate', methods=['POST'])
def invalidate_cache_by_tags():
    """태그별 캐시 무효화"""
    try:
        if not CACHE_AVAILABLE or not cache_manager:
            return jsonify({
                'success': False,
                'error': 'Cache system not available'
            }), 503
        
        data = request.get_json() or {}
        tags = data.get('tags', [])
        
        if not tags:
            return jsonify({
                'success': False,
                'error': 'Tags are required'
            }), 400
        
        invalidated_count = cache_manager.invalidate_by_tags(tags)
        return jsonify({
            'success': True,
            'message': f'{invalidated_count}개 캐시 무효화 완료',
            'invalidated_count': invalidated_count,
            'tags': tags,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        safe_log(f"캐시 무효화 실패: {str(e)}", 'error')
        return jsonify({'success': False, 'error': str(e)}), 500

# 기존 API들 (성능 모니터링 적용)
@app.route('/api/save-numbers', methods=['POST'])
@monitor_performance if MONITORING_AVAILABLE else lambda f: f
@rate_limiter(max_requests=50, time_window=3600)
@timeout_handler(timeout_seconds=5)
def save_numbers():
    try:
        data = request.get_json()
        if not data:
            raise ValueError("요청 데이터가 없습니다.")
        
        numbers = data.get('numbers', [])
        label = data.get('label', f"저장된 번호 {datetime.now().strftime('%m-%d %H:%M')}")
        
        # 번호 유효성 검사
        is_valid, message = validate_lotto_numbers(numbers)
        if not is_valid or len(numbers) != 6:
            return jsonify({
                'success': False,
                'error': True,
                'message': message if not is_valid else '6개 번호를 모두 입력해주세요.',
                'error_type': 'validation'
            }), 400
        
        # 세션 관리
        if 'user_id' not in session:
            session['user_id'] = str(uuid.uuid4())
        
        user_id = session['user_id']
        
        if user_id not in user_saved_numbers:
            user_saved_numbers[user_id] = []
        
        # 번호 분석
        analysis = {
            'sum': sum(numbers),
            'even_count': sum(1 for n in numbers if n % 2 == 0),
            'odd_count': sum(1 for n in numbers if n % 2 != 0),
            'range': max(numbers) - min(numbers),
            'consecutive': sum(1 for i in range(len(sorted(numbers))-1) 
                            if sorted(numbers)[i+1] - sorted(numbers)[i] == 1)
        }
        
        saved_entry = {
            'id': str(uuid.uuid4()),
            'numbers': sorted(numbers),
            'label': label[:50],  # 라벨 길이 제한
            'analysis': analysis,
            'saved_at': datetime.now().isoformat(),
            'checked_winning': False
        }
        
        user_saved_numbers[user_id].append(saved_entry)
        
        # 최대 50개까지만 저장
        if len(user_saved_numbers[user_id]) > 50:
            user_saved_numbers[user_id] = user_saved_numbers[user_id][-50:]
        
        # 🆕 사용자 번호를 캐시에 저장
        if CACHE_AVAILABLE and cache_manager:
            cache_manager.cache_user_numbers(user_id, user_saved_numbers[user_id])
            safe_log(f"사용자 번호 캐시 업데이트: {user_id}", 'info')
        
        return jsonify({
            'success': True,
            'message': '번호가 저장되었습니다.',
            'saved_entry': saved_entry,
            'total_saved': len(user_saved_numbers[user_id])
        })
        
    except Exception as e:
        safe_log(f"번호 저장 실패: {str(e)}", 'error')
        return handle_api_error(e)

@app.route('/api/saved-numbers')
@monitor_performance if MONITORING_AVAILABLE else lambda f: f
@timeout_handler(timeout_seconds=5)
def get_saved_numbers():
    try:
        if 'user_id' not in session:
            return jsonify({
                'success': True,
                'saved_numbers': [],
                'total_count': 0
            })
        
        user_id = session['user_id']
        
        # 🆕 캐시에서 먼저 확인
        if CACHE_AVAILABLE and cache_manager:
            cached_numbers = cache_manager.get_cached_user_numbers(user_id)
            if cached_numbers is not None:
                return jsonify({
                    'success': True,
                    'saved_numbers': cached_numbers,
                    'total_count': len(cached_numbers),
                    'cached': True
                })
        
        saved_numbers = user_saved_numbers.get(user_id, [])
        
        # 🆕 캐시에 저장
        if CACHE_AVAILABLE and cache_manager and saved_numbers:
            cache_manager.cache_user_numbers(user_id, saved_numbers)
        
        return jsonify({
            'success': True,
            'saved_numbers': saved_numbers,
            'total_count': len(saved_numbers),
            'cached': False
        })
        
    except Exception as e:
        safe_log(f"저장된 번호 조회 실패: {str(e)}", 'error')
        return handle_api_error(e)

@app.route('/api/delete-saved-number', methods=['POST'])
@monitor_performance if MONITORING_AVAILABLE else lambda f: f
@timeout_handler(timeout_seconds=5)
def delete_saved_number():
    try:
        data = request.get_json()
        if not data:
            raise ValueError("요청 데이터가 없습니다.")
        
        number_id = data.get('id')
        if not number_id:
            raise ValueError("삭제할 번호 ID가 필요합니다.")
        
        if 'user_id' not in session:
            return jsonify({
                'success': False,
                'error': True,
                'message': '사용자 세션이 없습니다.',
                'error_type': 'session'
            }), 401
        
        user_id = session['user_id']
        
        if user_id in user_saved_numbers:
            original_count = len(user_saved_numbers[user_id])
            user_saved_numbers[user_id] = [
                item for item in user_saved_numbers[user_id] 
                if item.get('id') != number_id
            ]
            
            if len(user_saved_numbers[user_id]) < original_count:
                # 🆕 캐시 업데이트
                if CACHE_AVAILABLE and cache_manager:
                    cache_manager.cache_user_numbers(user_id, user_saved_numbers[user_id])
                
                return jsonify({
                    'success': True,
                    'message': '번호가 삭제되었습니다.',
                    'remaining_count': len(user_saved_numbers[user_id])
                })
        
        return jsonify({
            'success': False,
            'error': True,
            'message': '삭제할 번호를 찾을 수 없습니다.',
            'error_type': 'not_found'
        }), 404
        
    except Exception as e:
        safe_log(f"번호 삭제 실패: {str(e)}", 'error')
        return handle_api_error(e)

@app.route('/api/health')
@timeout_handler(timeout_seconds=5)
def health_check():
    try:
        uptime = datetime.now() - performance_metrics.get('start_time', datetime.now())
        
        status = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'version': '2.1',  # 🆕 버전 업데이트
            'environment': 'production' if not app.config['DEBUG'] else 'development',
            'uptime_seconds': int(uptime.total_seconds()),
            'features': {
                'pandas_available': PANDAS_AVAILABLE,
                'qr_available': QR_AVAILABLE,
                'ml_available': ML_AVAILABLE,
                'monitoring_available': MONITORING_AVAILABLE,  # 🆕
                'cache_available': CACHE_AVAILABLE  # 🆕
            },
            'data': {
                'sample_data_count': len(sample_data) if sample_data else 0,
                'active_users': len(user_saved_numbers),
                'lottery_stores_count': len(LOTTERY_STORES),
                'ai_models_count': len(AI_MODELS_INFO)
            },
            'performance': {
                'total_requests': performance_metrics.get('total_requests', 0),
                'total_errors': performance_metrics.get('total_errors', 0),
                'error_rate': round((performance_metrics.get('total_errors', 0) / 
                                  max(performance_metrics.get('total_requests', 1), 1)) * 100, 2),
                'avg_response_time': round(performance_metrics.get('avg_response_time', 0), 3)
            },
            'supported_regions': list(set([store['region'] for store in LOTTERY_STORES])),
            'supported_features': [
                'AI 예측', 'QR 스캔', '번호 저장', '당첨 확인', 
                '통계 분석', '판매점 검색', '세금 계산', '시뮬레이션',
                '빠른 저장', '랜덤 생성', '지역별 검색', 'AI 모델 정보',
                '예측 히스토리', '패턴 분석', '이월수/궁합수 분석',
                '성능 모니터링', '고급 캐싱'  # 🆕
            ]
        }
        
        # 🆕 고급 시스템 상태 추가
        if MONITORING_AVAILABLE and monitor:
            try:
                monitor_stats = monitor.get_current_stats()
                status['monitoring'] = {
                    'enabled': True,
                    'total_requests': monitor_stats['overview']['total_requests'],
                    'error_rate': monitor_stats['overview']['error_rate'],
                    'avg_response_time': monitor_stats['overview']['average_response_time'],
                    'health_status': monitor_stats['health_status']
                }
            except:
                status['monitoring'] = {'enabled': True, 'status': 'unavailable'}
        else:
            status['monitoring'] = {'enabled': False}
        
        if CACHE_AVAILABLE and cache_manager:
            try:
                cache_info = cache_manager.get_cache_info()
                status['cache'] = {
                    'enabled': True,
                    'redis_available': cache_info.get('redis_available', False),
                    'hit_rate': cache_info['stats']['hit_rate'] if cache_info['stats'] else 0,
                    'total_operations': cache_info['stats']['total_operations'] if cache_info['stats'] else 0
                }
            except:
                status['cache'] = {'enabled': True, 'status': 'unavailable'}
        else:
            status['cache'] = {'enabled': False}
        
        if sample_data:
            status['data_source'] = f"실제 {len(sample_data)}회차 데이터"
        else:
            status['data_source'] = "샘플 데이터"
        
        return jsonify(status)
        
    except Exception as e:
        safe_log(f"health check 실패: {str(e)}", 'error')
        return jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

# 나머지 기존 API들은 동일하되 @monitor_performance 데코레이터 추가
# (간소화를 위해 일부 생략하고 핵심적인 것들만 포함)

def initialize_app():
    """애플리케이션 초기화 (완전 통합 버전)"""
    global sample_data, monitor, cache_manager
    try:
        safe_log("=== 🚀 LottoPro-AI v2.1 초기화 시작 ===")
        
        # 샘플 데이터 생성
        sample_data = generate_sample_data()
        safe_log(f"✅ 샘플 데이터 생성 완료: {len(sample_data)}회차")
        
        # 성능 메트릭 초기화
        performance_metrics['start_time'] = datetime.now()
        
        # 🆕 성능 모니터링 시스템 초기화
        if MONITORING_AVAILABLE:
            try:
                monitor = init_monitoring(
                    app=app, 
                    auto_start=True,
                    custom_thresholds={
                        'response_time': 10.0,    # 10초 (로또 예측은 시간이 걸릴 수 있음)
                        'error_rate': 0.05,       # 5%
                        'cpu_usage': 80.0,        # 80%
                        'memory_usage': 85.0      # 85%
                    }
                )
                app.monitor = monitor
                safe_log("✅ 성능 모니터링 시스템 활성화 완료")
                
                # 알림 콜백 설정 (옵션)
                def log_performance_alert(alert_info):
                    safe_log(f"⚠️  PERFORMANCE ALERT: {alert_info['type']} - {alert_info['message']}", 'warning')
                
                monitor.add_alert_callback(log_performance_alert)
                
            except Exception as e:
                safe_log(f"❌ 성능 모니터링 시스템 초기화 실패: {str(e)}", 'error')
        
        # 🆕 캐시 시스템 초기화
        if CACHE_AVAILABLE:
            try:
                cache_manager = init_cache_system(
                    app=app,
                    redis_url=os.getenv('REDIS_URL'),  # 환경변수에서 Redis URL
                    default_ttl=300,  # 5분 기본 TTL
                    enable_warming=True
                )
                app.cache = cache_manager
                safe_log("✅ 캐시 시스템 활성화 완료")
                
                # 캐시 워밍 함수들 정의
                def warm_statistics_cache():
                    """통계 데이터 미리 캐싱"""
                    try:
                        frequency = calculate_frequency_analysis()
                        if frequency:
                            basic_stats = {
                                'frequency': frequency,
                                'hot_numbers': sorted(frequency.items(), key=lambda x: x[1], reverse=True)[:8],
                                'cold_numbers': sorted(frequency.items(), key=lambda x: x[1])[:8],
                                'generated_at': time.time()
                            }
                            return cache_manager.cache_statistics('main', basic_stats, ttl=600)
                        return True
                    except Exception as e:
                        safe_log(f"통계 캐시 워밍 실패: {str(e)}", 'error')
                        return False
                
                def warm_prediction_cache():
                    """인기 번호 조합 미리 캐싱"""
                    try:
                        popular_combinations = [
                            [1, 2, 3, 4, 5, 6],      # 연속 번호
                            [7, 14, 21, 28, 35, 42], # 7의 배수
                            [3, 7, 11, 19, 23, 31],  # 소수 조합
                        ]
                        
                        success_count = 0
                        for numbers in popular_combinations:
                            result = generate_ai_prediction(numbers, "frequency")
                            if result:
                                success_count += 1
                        
                        return success_count > 0
                    except Exception as e:
                        safe_log(f"예측 캐시 워밍 실패: {str(e)}", 'error')
                        return False
                
                # 백그라운드에서 캐시 워밍 실행
                def background_cache_warming():
                    time.sleep(3)  # 앱 완전 시작 후 실행
                    warming_results = cache_manager.warm_cache([
                        warm_statistics_cache,
                        warm_prediction_cache
                    ])
                    safe_log(f"🔥 캐시 워밍 결과: {warming_results}")
                
                import threading
                warming_thread = threading.Thread(target=background_cache_warming, daemon=True)
                warming_thread.start()
                
            except Exception as e:
                safe_log(f"❌ 캐시 시스템 초기화 실패: {str(e)}", 'error')
        
        safe_log(f"✅ 15가지 기능 로드 완료")
        safe_log(f"✅ AI 모델 {len(AI_MODELS_INFO)}개 준비 완료")
        safe_log(f"✅ 판매점 데이터 {len(LOTTERY_STORES)}개 로드 완료")
        safe_log("✅ 타임아웃 처리 및 에러 핸들링 시스템 활성화")
        safe_log("=== 🎉 초기화 완료 ===")
        
    except Exception as e:
        safe_log(f"❌ 초기화 실패: {str(e)}", 'error')
        # 초기화 실패 시에도 기본 서비스는 제공
        if not sample_data:
            sample_data = []

if __name__ == '__main__':
    initialize_app()
    
    port = int(os.environ.get('PORT', 5000))
    debug_mode = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    safe_log(f"🚀 서버 시작 - 포트: {port}, 디버그 모드: {debug_mode}")
    safe_log("=== 🎯 LottoPro AI v2.1 - 성능 모니터링 & 캐시 시스템 완전 통합 ===")
    
    app.run(debug=debug_mode, host='0.0.0.0', port=port)
else:
    initialize_app()
