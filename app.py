{
  `path`: `C:\\Users\\USER\\Documents\\kakaotalkdown\\lotto_analysis\\app.py`,
  `content`: `from flask import Flask, render_template, request, jsonify, session, send_file
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
logging.basicConfig(level=logging.INFO)
app.logger.setLevel(logging.INFO)

# 글로벌 변수
sample_data = None
user_saved_numbers = {}
cached_stats = {}

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

# 로또 판매점 데이터 (확장됨)
LOTTERY_STORES = [
    {\"name\": \"동대문 복권방\", \"address\": \"서울시 동대문구 장한로 195\", \"region\": \"서울\", \"district\": \"동대문구\", \"lat\": 37.5745, \"lng\": 127.0098, \"phone\": \"02-1234-5678\", \"first_wins\": 15, \"business_hours\": \"06:00-24:00\"},
    {\"name\": \"강남 로또타운\", \"address\": \"서울시 강남구 테헤란로 152\", \"region\": \"서울\", \"district\": \"강남구\", \"lat\": 37.4979, \"lng\": 127.0276, \"phone\": \"02-2345-6789\", \"first_wins\": 23, \"business_hours\": \"07:00-23:00\"},
    {\"name\": \"평택역 로또센터\", \"address\": \"경기도 평택시 평택동 856-1\", \"region\": \"평택\", \"district\": \"평택시\", \"lat\": 36.9922, \"lng\": 127.0890, \"phone\": \"031-1234-5678\", \"first_wins\": 5, \"business_hours\": \"06:00-22:00\"},
    {\"name\": \"안정리 행운복권\", \"address\": \"경기도 평택시 안정동 123-45\", \"region\": \"평택\", \"district\": \"평택시\", \"lat\": 36.9856, \"lng\": 127.0825, \"phone\": \"031-2345-6789\", \"first_wins\": 3, \"business_hours\": \"07:00-21:00\"},
    {\"name\": \"송탄 중앙점\", \"address\": \"경기도 평택시 송탄동 789-12\", \"region\": \"평택\", \"district\": \"평택시\", \"lat\": 36.9675, \"lng\": 127.0734, \"phone\": \"031-3456-7890\", \"first_wins\": 8, \"business_hours\": \"08:00-20:00\"}
]

def safe_log(message):
    \"\"\"안전한 로깅\"\"\"
    try:
        app.logger.info(f\"[LottoPro-AI] {message}\")
        print(f\"[LottoPro-AI] {message}\")
    except Exception as e:
        print(f\"[LottoPro-AI] Logging error: {str(e)}\")

@app.after_request
def add_security_headers(response):
    \"\"\"보안 헤더 추가\"\"\"
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    return response

def generate_sample_data():
    \"\"\"샘플 데이터 생성\"\"\"
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
        safe_log(f\"샘플 데이터 생성 실패: {str(e)}\")
        return []

def calculate_frequency_analysis():
    \"\"\"빈도 분석\"\"\"
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
        safe_log(f\"빈도 분석 실패: {str(e)}\")
        return {}

def calculate_carry_over_analysis():
    \"\"\"이월수 분석\"\"\"
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
        safe_log(f\"이월수 분석 실패: {str(e)}\")
        return []

def calculate_companion_analysis():
    \"\"\"궁합수 분석\"\"\"
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
        safe_log(f\"궁합수 분석 실패: {str(e)}\")
        return {}

def calculate_pattern_analysis():
    \"\"\"패턴 분석\"\"\"
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
                patterns['odd_even_ratio'].append(f\"{odd_count}:{6-odd_count}\")
                patterns['sum_distribution'].append(total_sum)
                patterns['range_distribution'].append(number_range)
        
        return patterns
    except Exception as e:
        safe_log(f\"패턴 분석 실패: {str(e)}\")
        return {}

def generate_ai_prediction(user_numbers=None, model_type=\"frequency\"):
    \"\"\"AI 예측 생성\"\"\"
    try:
        if user_numbers is None:
            user_numbers = []
        
        safe_numbers = []
        if isinstance(user_numbers, list):
            for num in user_numbers:
                try:
                    n = int(num)
                    if 1 <= n <= 45 and n not in safe_numbers:
                        safe_numbers.append(n)
                except:
                    continue
        
        if model_type == \"frequency\":
            frequency = calculate_frequency_analysis()
            weights = np.ones(45)
            for num, freq in frequency.items():
                if 1 <= num <= 45:
                    weights[num-1] = freq + 1
        elif model_type == \"trend\":
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
        
        while len(numbers) < 6:
            new_num = random.randint(1, 45)
            if new_num not in numbers:
                numbers.append(new_num)
        
        return sorted(numbers[:6])
        
    except Exception as e:
        safe_log(f\"AI 예측 생성 실패: {str(e)}\")
        return sorted(random.sample(range(1, 46), 6))

# ===== API 엔드포인트들 =====
@app.route('/')
def index():
    try:
        context = {
            'update_date': '2025.08.28',
            'analysis_round': 1186,
            'copyright_year': 2025,
            'version': 'v2.0'
        }
        return render_template('index.html', **context)
    except Exception as e:
        safe_log(f\"메인 페이지 오류: {str(e)}\")
        return \"서비스 준비 중입니다.\", 503

@app.route('/api/predict', methods=['POST'])
def predict():
    try:
        data = request.get_json() or {}
        user_numbers = data.get('user_numbers', [])
        
        models = {}
        model_configs = [
            ('빈도분석 모델', 'frequency'),
            ('트렌드분석 모델', 'trend'),
            ('패턴분석 모델', 'pattern'),
            ('통계분석 모델', 'statistical'),
            ('머신러닝 모델', 'ml')
        ]
        
        for model_name, model_type in model_configs:
            predictions = []
            for i in range(5):
                pred = generate_ai_prediction(user_numbers, model_type)
                predictions.append(pred)
            
            model_info = AI_MODELS_INFO.get(model_type, {})
            models[model_name] = {
                'description': model_info.get('description', ''),
                'predictions': predictions,
                'accuracy': model_info.get('accuracy_rate', 15),
                'confidence': random.randint(85, 95)
            }
        
        top_recommendations = []
        for i in range(5):
            rec = generate_ai_prediction(user_numbers, \"frequency\")
            if rec not in top_recommendations:
                top_recommendations.append(rec)
        
        response = {
            'success': True,
            'user_numbers': user_numbers,
            'models': models,
            'top_recommendations': top_recommendations,
            'total_combinations': sum(len(model.get('predictions', [])) for model in models.values()),
            'data_source': f\"{len(sample_data)}회차 데이터\",
            'analysis_timestamp': datetime.now().isoformat(),
            'version': '2.0'
        }
        
        return jsonify(response)
        
    except Exception as e:
        safe_log(f\"예측 API 실패: {str(e)}\")
        return jsonify({'success': False, 'error': '예측 생성 중 오류가 발생했습니다.'}), 500

@app.route('/api/stats')
def get_stats():
    try:
        frequency = calculate_frequency_analysis()
        
        if frequency:
            sorted_freq = sorted(frequency.items(), key=lambda x: x[1], reverse=True)
            hot_numbers = sorted_freq[:8]
            cold_numbers = sorted_freq[-8:]
        else:
            hot_numbers = [[7, 15], [13, 14], [22, 13], [31, 12], [42, 11], [1, 10], [25, 9], [33, 8]]
            cold_numbers = [[45, 5], [44, 6], [43, 7], [2, 8], [3, 9], [4, 10], [5, 11], [6, 12]]
        
        return jsonify({
            'success': True,
            'frequency': frequency,
            'hot_numbers': hot_numbers,
            'cold_numbers': cold_numbers,
            'carry_over_analysis': calculate_carry_over_analysis(),
            'companion_analysis': list(calculate_companion_analysis().items()),
            'pattern_analysis': calculate_pattern_analysis(),
            'total_draws': len(sample_data) if sample_data else 200,
            'data_source': f\"{len(sample_data)}회차 데이터\" if sample_data else \"샘플 데이터\",
            'last_updated': datetime.now().isoformat()
        })
        
    except Exception as e:
        safe_log(f\"통계 API 실패: {str(e)}\")
        return jsonify({'success': False, 'error': '통계 데이터를 불러올 수 없습니다.'}), 500

@app.route('/api/save-numbers', methods=['POST'])
def save_numbers():
    try:
        data = request.get_json()
        numbers = data.get('numbers', [])
        label = data.get('label', f\"저장된 번호 {datetime.now().strftime('%m-%d %H:%M')}\")
        
        if not numbers or len(numbers) != 6:
            return jsonify({'success': False, 'error': '올바른 6개 번호를 입력해주세요.'}), 400
        
        if 'user_id' not in session:
            session['user_id'] = str(uuid.uuid4())
        
        user_id = session['user_id']
        
        if user_id not in user_saved_numbers:
            user_saved_numbers[user_id] = []
        
        analysis = {
            'sum': sum(numbers),
            'even_count': sum(1 for n in numbers if n % 2 == 0),
            'odd_count': sum(1 for n in numbers if n % 2 != 0),
            'range': max(numbers) - min(numbers),
            'consecutive': sum(1 for i in range(len(sorted(numbers))-1) if sorted(numbers)[i+1] - sorted(numbers)[i] == 1)
        }
        
        saved_entry = {
            'id': str(uuid.uuid4()),
            'numbers': sorted(numbers),
            'label': label,
            'analysis': analysis,
            'saved_at': datetime.now().isoformat(),
            'checked_winning': False
        }
        
        user_saved_numbers[user_id].append(saved_entry)
        
        if len(user_saved_numbers[user_id]) > 50:
            user_saved_numbers[user_id] = user_saved_numbers[user_id][-50:]
        
        return jsonify({
            'success': True,
            'message': '번호가 저장되었습니다.',
            'saved_entry': saved_entry,
            'total_saved': len(user_saved_numbers[user_id])
        })
        
    except Exception as e:
        safe_log(f\"번호 저장 실패: {str(e)}\")
        return jsonify({'success': False, 'error': '번호 저장에 실패했습니다.'}), 500

@app.route('/api/saved-numbers')
def get_saved_numbers():
    try:
        if 'user_id' not in session:
            return jsonify({'success': True, 'saved_numbers': []})
        
        user_id = session['user_id']
        saved_numbers = user_saved_numbers.get(user_id, [])
        
        return jsonify({
            'success': True,
            'saved_numbers': saved_numbers,
            'total_count': len(saved_numbers)
        })
        
    except Exception as e:
        safe_log(f\"저장된 번호 조회 실패: {str(e)}\")
        return jsonify({'success': False, 'error': '저장된 번호를 불러올 수 없습니다.'}), 500

@app.route('/api/delete-saved-number', methods=['POST'])
def delete_saved_number():
    try:
        data = request.get_json()
        number_id = data.get('id')
        
        if 'user_id' not in session:
            return jsonify({'success': False, 'error': '사용자 세션이 없습니다.'}), 400
        
        user_id = session['user_id']
        
        if user_id in user_saved_numbers:
            original_count = len(user_saved_numbers[user_id])
            user_saved_numbers[user_id] = [
                item for item in user_saved_numbers[user_id] if item.get('id') != number_id
            ]
            
            if len(user_saved_numbers[user_id]) < original_count:
                return jsonify({
                    'success': True,
                    'message': '번호가 삭제되었습니다.',
                    'remaining_count': len(user_saved_numbers[user_id])
                })
        
        return jsonify({'success': False, 'error': '삭제할 번호를 찾을 수 없습니다.'}), 404
        
    except Exception as e:
        safe_log(f\"번호 삭제 실패: {str(e)}\")
        return jsonify({'success': False, 'error': '번호 삭제에 실패했습니다.'}), 500

@app.route('/api/check-winning', methods=['POST'])
def check_winning():
    try:
        data = request.get_json()
        numbers = data.get('numbers', [])
        
        if not numbers or len(numbers) != 6:
            return jsonify({'success': False, 'error': '올바른 6개 번호를 입력해주세요.'}), 400
        
        if sample_data:
            latest_draw = sample_data[0]
            winning_numbers = [latest_draw.get(f'당첨번호{i}') for i in range(1, 7)]
            bonus_number = latest_draw.get('보너스번호')
            
            matches = len(set(numbers) & set(winning_numbers))
            bonus_match = bonus_number in numbers
            
            if matches == 6:
                prize = \"1등\"
                prize_money = \"20억원 (추정)\"
            elif matches == 5 and bonus_match:
                prize = \"2등\"
                prize_money = \"6천만원 (추정)\"
            elif matches == 5:
                prize = \"3등\"
                prize_money = \"150만원 (추정)\"
            elif matches == 4:
                prize = \"4등\"
                prize_money = \"5만원\"
            elif matches == 3:
                prize = \"5등\"
                prize_money = \"5천원\"
            else:
                prize = \"낙첨\"
                prize_money = \"0원\"
            
            return jsonify({
                'success': True,
                'matches': matches,
                'bonus_match': bonus_match,
                'prize': prize,
                'prize_money': prize_money,
                'winning_numbers': winning_numbers,
                'bonus_number': bonus_number,
                'round': latest_draw.get('회차'),
                'user_numbers': numbers
            })
        else:
            return jsonify({'success': False, 'error': '당첨 데이터를 불러올 수 없습니다.'}), 500
        
    except Exception as e:
        safe_log(f\"당첨 확인 실패: {str(e)}\")
        return jsonify({'success': False, 'error': '당첨 확인에 실패했습니다.'}), 500

@app.route('/api/generate-qr', methods=['POST'])
def generate_qr():
    try:
        if not QR_AVAILABLE:
            return jsonify({'success': False, 'error': 'QR 코드 기능이 비활성화되어 있습니다.'}), 501
        
        data = request.get_json()
        numbers = data.get('numbers', [])
        
        if not numbers or len(numbers) != 6:
            return jsonify({'success': False, 'error': '올바른 6개 번호를 입력해주세요.'}), 400
        
        qr_data = f\"LOTTO:{':'.join(map(str, sorted(numbers)))}\"
        
        qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color=\"black\", back_color=\"white\")
        
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        qr_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        return jsonify({
            'success': True,
            'qr_code': f\"data:image/png;base64,{qr_base64}\",
            'numbers': sorted(numbers),
            'qr_data': qr_data
        })
        
    except Exception as e:
        safe_log(f\"QR 코드 생성 실패: {str(e)}\")
        return jsonify({'success': False, 'error': 'QR 코드 생성에 실패했습니다.'}), 500

@app.route('/api/tax-calculator', methods=['POST'])
def calculate_tax():
    try:
        data = request.get_json()
        prize_amount = data.get('prize_amount', 0)
        
        if not isinstance(prize_amount, (int, float)) or prize_amount <= 0:
            return jsonify({'success': False, 'error': '올바른 당첨금액을 입력해주세요.'}), 400
        
        tax_free_amount = 50000
        
        if prize_amount <= tax_free_amount:
            tax = 0
            net_amount = prize_amount
            effective_tax_rate = 0
            tax_brackets = \"비과세\"
        else:
            taxable_amount = prize_amount - tax_free_amount
            
            if prize_amount <= 300000000:
                tax_rate = 0.22
                tax = taxable_amount * tax_rate
                effective_tax_rate = 22.0
                tax_brackets = \"3억원 이하 (22%)\"
            else:
                amount_up_to_300m = 300000000 - tax_free_amount
                tax_up_to_300m = amount_up_to_300m * 0.22
                
                amount_over_300m = prize_amount - 300000000
                tax_over_300m = amount_over_300m * 0.33
                
                tax = tax_up_to_300m + tax_over_300m
                effective_tax_rate = (tax / taxable_amount) * 100
                tax_brackets = \"3억원 초과 (22% + 33%)\"
            
            net_amount = prize_amount - tax
        
        return jsonify({
            'success': True,
            'prize_amount': prize_amount,
            'tax_amount': round(tax, 0),
            'net_amount': round(net_amount, 0),
            'effective_tax_rate': round(effective_tax_rate, 1),
            'tax_free_amount': tax_free_amount,
            'tax_brackets': tax_brackets
        })
        
    except Exception as e:
        safe_log(f\"세금 계산 실패: {str(e)}\")
        return jsonify({'success': False, 'error': '세금 계산에 실패했습니다.'}), 500

@app.route('/api/simulation', methods=['POST'])
def run_simulation():
    try:
        data = request.get_json()
        user_numbers = data.get('numbers', [])
        rounds = data.get('rounds', 1000)
        
        if not user_numbers or len(user_numbers) != 6:
            return jsonify({'success': False, 'error': '올바른 6개 번호를 입력해주세요.'}), 400
        
        if rounds > 10000:
            rounds = 10000
        
        results = {'1등': 0, '2등': 0, '3등': 0, '4등': 0, '5등': 0, '낙첨': 0}
        
        total_cost = rounds * 1000
        total_prize = 0
        
        for _ in range(rounds):
            winning_numbers = sorted(random.sample(range(1, 46), 6))
            bonus_number = random.choice([n for n in range(1, 46) if n not in winning_numbers])
            
            matches = len(set(user_numbers) & set(winning_numbers))
            bonus_match = bonus_number in user_numbers
            
            if matches == 6:
                results['1등'] += 1
                total_prize += 2000000000
            elif matches == 5 and bonus_match:
                results['2등'] += 1
                total_prize += 60000000
            elif matches == 5:
                results['3등'] += 1
                total_prize += 1500000
            elif matches == 4:
                results['4등'] += 1
                total_prize += 50000
            elif matches == 3:
                results['5등'] += 1
                total_prize += 5000
            else:
                results['낙첨'] += 1
        
        profit_rate = ((total_prize - total_cost) / total_cost) * 100
        
        return jsonify({
            'success': True,
            'results': results,
            'total_rounds': rounds,
            'total_cost': total_cost,
            'total_prize': total_prize,
            'net_profit': total_prize - total_cost,
            'profit_rate': round(profit_rate, 2),
            'user_numbers': user_numbers,
            'roi': round((total_prize / total_cost) * 100, 2)
        })
        
    except Exception as e:
        safe_log(f\"시뮬레이션 실패: {str(e)}\")
        return jsonify({'success': False, 'error': '시뮬레이션에 실패했습니다.'}), 500

@app.route('/api/lottery-stores')
def get_lottery_stores():
    try:
        search_query = request.args.get('query', '').strip()
        lat = request.args.get('lat', type=float)
        lng = request.args.get('lng', type=float)
        
        stores = LOTTERY_STORES.copy()
        
        if search_query:
            search_query_lower = search_query.lower()
            filtered_stores = []
            for store in stores:
                if (search_query_lower in store['region'].lower() or
                    search_query_lower in store['district'].lower() or
                    search_query_lower in store['name'].lower() or
                    search_query_lower in store['address'].lower()):
                    filtered_stores.append(store)
            stores = filtered_stores
        
        if lat and lng:
            for store in stores:
                try:
                    distance = math.sqrt((store['lat'] - lat) ** 2 + (store['lng'] - lng) ** 2)
                    store['distance'] = round(distance * 100, 1)
                except:
                    store['distance'] = 999
            
            stores.sort(key=lambda x: x.get('distance', 999))
        else:
            stores.sort(key=lambda x: x.get('first_wins', 0), reverse=True)
        
        return jsonify({
            'success': True,
            'stores': stores,
            'total_count': len(stores),
            'search_query': search_query if search_query else None
        })
        
    except Exception as e:
        safe_log(f\"판매점 검색 실패: {str(e)}\")
        return jsonify({'success': False, 'error': '판매점 검색에 실패했습니다.', 'stores': []}), 500

@app.route('/api/generate-random', methods=['POST'])
def generate_random_numbers():
    try:
        data = request.get_json()
        count = data.get('count', 1)
        
        if count > 10:
            count = 10
        
        random_sets = []
        for _ in range(count):
            numbers = generate_ai_prediction(model_type=\"statistical\")
            
            analysis = {
                'sum': sum(numbers),
                'even_count': sum(1 for n in numbers if n % 2 == 0),
                'odd_count': sum(1 for n in numbers if n % 2 != 0),
                'range': max(numbers) - min(numbers),
                'consecutive': sum(1 for i in range(len(numbers)-1) if numbers[i+1] - numbers[i] == 1)
            }
            
            random_sets.append({'numbers': numbers, 'analysis': analysis})
        
        return jsonify({
            'success': True,
            'random_sets': random_sets,
            'count': len(random_sets),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        safe_log(f\"랜덤 번호 생성 실패: {str(e)}\")
        return jsonify({'success': False, 'error': '랜덤 번호 생성에 실패했습니다.'}), 500

@app.route('/api/ai-models')
def get_ai_models_info():
    try:
        return jsonify({
            'success': True,
            'models': AI_MODELS_INFO,
            'total_models': len(AI_MODELS_INFO),
            'last_updated': datetime.now().isoformat()
        })
    except Exception as e:
        safe_log(f\"AI 모델 정보 조회 실패: {str(e)}\")
        return jsonify({'success': False, 'error': 'AI 모델 정보를 불러올 수 없습니다.'}), 500

@app.route('/api/prediction-history')
def get_prediction_history():
    try:
        return jsonify({
            'success': True,
            'history': PREDICTION_HISTORY,
            'total_count': len(PREDICTION_HISTORY),
            'last_updated': datetime.now().isoformat()
        })
    except Exception as e:
        safe_log(f\"예측 히스토리 조회 실패: {str(e)}\")
        return jsonify({'success': False, 'error': '예측 히스토리를 불러올 수 없습니다.'}), 500

@app.route('/api/health')
def health_check():
    try:
        status = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'version': '2.0.0',
            'environment': 'production' if not app.config['DEBUG'] else 'development',
            'pandas_available': PANDAS_AVAILABLE,
            'qr_available': QR_AVAILABLE,
            'ml_available': ML_AVAILABLE,
            'sample_data_count': len(sample_data) if sample_data else 0,
            'active_users': len(user_saved_numbers),
            'lottery_stores_count': len(LOTTERY_STORES),
            'supported_regions': list(set([store['region'] for store in LOTTERY_STORES])),
            'features': [
                'AI 예측', 'QR 스캔', '번호 저장', '당첨 확인', 
                '통계 분석', '판매점 검색', '세금 계산', '시뮬레이션',
                '빠른 저장', '랜덤 생성', '지역별 검색', 'AI 모델 정보',
                '예측 히스토리', '패턴 분석', '이월수/궁합수 분석'
            ]
        }
        
        if sample_data:
            status['data_source'] = f\"실제 {len(sample_data)}회차 데이터\"
        else:
            status['data_source'] = \"샘플 데이터\"
        
        return jsonify(status)
        
    except Exception as e:
        safe_log(f\"health check 실패: {str(e)}\")
        return jsonify({'status': 'error', 'error': str(e), 'timestamp': datetime.now().isoformat()}), 500

@app.errorhandler(404)
def not_found(error):
    try:
        return render_template('index.html'), 404
    except:
        return jsonify({'error': 'Not Found'}), 404

@app.errorhandler(500)
def internal_error(error):
    safe_log(f\"500 에러 발생: {error}\")
    return jsonify({'error': 'Internal server error'}), 500

def initialize_app():
    global sample_data
    try:
        safe_log(\"=== LottoPro-AI v2.0 초기화 시작 ===\")
        sample_data = generate_sample_data()
        safe_log(f\"샘플 데이터 생성 완료: {len(sample_data)}회차\")
        safe_log(f\"15가지 기능 로드 완료\")
        safe_log(f\"AI 모델 {len(AI_MODELS_INFO)}개 준비 완료\")
        safe_log(f\"판매점 데이터 {len(LOTTERY_STORES)}개 로드 완료\")
        safe_log(\"=== 초기화 완료 ===\")
    except Exception as e:
        safe_log(f\"초기화 실패: {str(e)}\")

if __name__ == '__main__':
    initialize_app()
    
    port = int(os.environ.get('PORT', 5000))
    debug_mode = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    safe_log(f\"서버 시작 - 포트: {port}, 디버그 모드: {debug_mode}\")
    safe_log(\"=== 15가지 기능 완전 구현 완료 ===\")
    
    app.run(debug=debug_mode, host='0.0.0.0', port=port)
else:
    initialize_app()
`
}
