from flask import Flask, render_template, request, jsonify
import pandas as pd
import numpy as np
import random
from collections import Counter, defaultdict
import os
import json
from datetime import datetime, timedelta
import gc
import warnings
warnings.filterwarnings('ignore')

app = Flask(__name__)

# 메모리 절약을 위한 설정
app.config['JSON_SORT_KEYS'] = False
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False

class LottoPredictor:
    def __init__(self, csv_file_path='new_1187.csv'):
        self.csv_file_path = csv_file_path
        self.data = None
        self.numbers = None
        self.load_data_optimized()
    
    def load_data_optimized(self):
        """메모리 최적화된 데이터 로드"""
        try:
            # 필요한 컬럼만 로드하여 메모리 절약
            required_columns = ['round', 'draw_date', 'num1', 'num2', 'num3', 'num4', 'num5', 'num6', 'bonus_num']
            self.data = pd.read_csv(self.csv_file_path, usecols=lambda x: x in required_columns)
            
            # 컬럼명 정규화
            if len(self.data.columns) >= 7:
                self.data.columns = required_columns[:len(self.data.columns)]
            
            # int32로 메모리 사용량 절약 (int64 대신)
            number_cols = ['num1', 'num2', 'num3', 'num4', 'num5', 'num6']
            for col in number_cols:
                if col in self.data.columns:
                    self.data[col] = self.data[col].astype('int32')
            
            # 번호 배열만 추출 (메모리 효율성)
            self.numbers = self.data[number_cols].values.astype('int32')
            
            print(f"✅ 데이터 로드 완료: {len(self.data)}개 회차")
            
            # 가비지 컬렉션으로 메모리 정리
            gc.collect()
            
        except Exception as e:
            print(f"❌ 데이터 로드 실패: {e}")
            self.data = None
            self.numbers = None
    
    def frequency_analysis_algorithm(self):
        """경량화된 빈도 분석 알고리즘"""
        try:
            # 최근 500회차만 사용하여 메모리 절약
            recent_numbers = self.numbers[-500:] if len(self.numbers) > 500 else self.numbers
            all_numbers = recent_numbers.flatten()
            frequency = Counter(all_numbers)
            most_common = [num for num, count in frequency.most_common(15)]
            
            predictions = []
            for _ in range(3):  # 5개 대신 3개로 축소
                selected = []
                weights = [frequency[num] for num in most_common]
                total_weight = sum(weights)
                
                if total_weight > 0:
                    weights = [w/total_weight for w in weights]
                    
                    while len(selected) < 6:
                        chosen = np.random.choice(most_common, p=weights)
                        if chosen not in selected:
                            selected.append(int(chosen))
                else:
                    selected = random.sample(range(1, 46), 6)
                
                predictions.append(sorted(selected))
            
            return predictions
        except Exception as e:
            print(f"빈도분석 알고리즘 오류: {e}")
            return self.generate_random_numbers(3)
    
    def hot_cold_algorithm(self):
        """경량화된 핫/콜드 번호 알고리즘"""
        try:
            recent_draws = 15  # 20에서 15로 축소
            recent_data = self.numbers[-recent_draws:]
            recent_numbers = recent_data.flatten()
            
            hot_counter = Counter(recent_numbers)
            hot_numbers = [num for num, count in hot_counter.most_common(12)]
            
            all_numbers_set = set(range(1, 46))
            recent_numbers_set = set(recent_numbers)
            cold_numbers = list(all_numbers_set - recent_numbers_set)[:8]
            
            predictions = []
            for _ in range(3):  # 5개 대신 3개로 축소
                hot_count = random.randint(3, 4)
                hot_selected = random.sample(hot_numbers[:10], min(hot_count, len(hot_numbers[:10])))
                cold_selected = random.sample(cold_numbers, min(6 - len(hot_selected), len(cold_numbers)))
                
                selected = hot_selected + cold_selected
                while len(selected) < 6:
                    num = random.randint(1, 45)
                    if num not in selected:
                        selected.append(num)
                
                predictions.append(sorted(selected[:6]))
            
            return predictions
        except Exception as e:
            print(f"핫콜드 알고리즘 오류: {e}")
            return self.generate_random_numbers(3)
    
    def pattern_analysis_algorithm(self):
        """경량화된 패턴 분석 알고리즘"""
        try:
            predictions = []
            recent_data = self.numbers[-20:]  # 30에서 20으로 축소
            
            # 구간별 분포 계산
            zones = [0, 0, 0, 0, 0]
            for draw in recent_data:
                for num in draw:
                    if 1 <= num <= 9: zones[0] += 1
                    elif 10 <= num <= 18: zones[1] += 1
                    elif 19 <= num <= 27: zones[2] += 1
                    elif 28 <= num <= 36: zones[3] += 1
                    elif 37 <= num <= 45: zones[4] += 1
            
            total = sum(zones)
            zone_probs = [z/total for z in zones] if total > 0 else [0.2] * 5
            
            for _ in range(3):  # 5개 대신 3개로 축소
                selected = []
                for i, prob in enumerate(zone_probs):
                    zone_count = max(1, int(prob * 6))
                    if i == 0: zone_range = list(range(1, 10))
                    elif i == 1: zone_range = list(range(10, 19))
                    elif i == 2: zone_range = list(range(19, 28))
                    elif i == 3: zone_range = list(range(28, 37))
                    else: zone_range = list(range(37, 46))
                    
                    available = [n for n in zone_range if n not in selected]
                    if available:
                        selected.extend(random.sample(available, min(zone_count, len(available))))
                
                while len(selected) < 6:
                    num = random.randint(1, 45)
                    if num not in selected:
                        selected.append(num)
                
                predictions.append(sorted(selected[:6]))
            
            return predictions
        except Exception as e:
            print(f"패턴분석 알고리즘 오류: {e}")
            return self.generate_random_numbers(3)
    
    def statistical_algorithm(self):
        """경량화된 통계적 분석 알고리즘"""
        try:
            predictions = []
            
            # 최근 300회차만 사용하여 메모리 절약
            recent_numbers = self.numbers[-300:] if len(self.numbers) > 300 else self.numbers
            
            position_stats = []
            for pos in range(6):
                pos_numbers = recent_numbers[:, pos]
                mean = float(np.mean(pos_numbers))
                std = float(np.std(pos_numbers))
                position_stats.append({'mean': mean, 'std': std})
            
            for _ in range(3):  # 5개 대신 3개로 축소
                selected = []
                for pos, stats_info in enumerate(position_stats):
                    num = int(np.random.normal(stats_info['mean'], stats_info['std']))
                    num = max(1, min(45, num))
                    
                    attempts = 0
                    while num in selected and attempts < 50:  # 100에서 50으로 축소
                        num = int(np.random.normal(stats_info['mean'], stats_info['std']))
                        num = max(1, min(45, num))
                        attempts += 1
                    
                    if num not in selected:
                        selected.append(num)
                
                while len(selected) < 6:
                    num = random.randint(1, 45)
                    if num not in selected:
                        selected.append(num)
                
                predictions.append(sorted(selected[:6]))
            
            # 메모리 정리
            del position_stats
            gc.collect()
            
            return predictions
        except Exception as e:
            print(f"통계분석 알고리즘 오류: {e}")
            return self.generate_random_numbers(3)
    
    def co_occurrence_algorithm(self):
        """경량화된 동반출현 분석 알고리즘"""
        try:
            # 최근 200회차만 사용하여 메모리 절약
            recent_numbers = self.numbers[-200:] if len(self.numbers) > 200 else self.numbers
            
            co_occurrence = defaultdict(int)
            
            for draw in recent_numbers:
                for i in range(6):
                    for j in range(i+1, 6):
                        pair = tuple(sorted([draw[i], draw[j]]))
                        co_occurrence[pair] += 1
            
            number_partners = defaultdict(list)
            for (num1, num2), count in co_occurrence.items():
                number_partners[num1].append((num2, count))
                number_partners[num2].append((num1, count))
            
            for num in number_partners:
                number_partners[num].sort(key=lambda x: x[1], reverse=True)
                number_partners[num] = number_partners[num][:10]  # 상위 10개만 유지
            
            predictions = []
            for _ in range(3):  # 5개 대신 3개로 축소
                selected = []
                
                recent_freq = Counter(recent_numbers[-10:].flatten())
                start_candidates = [num for num, count in recent_freq.most_common(10)]
                
                if start_candidates:
                    start_num = random.choice(start_candidates)
                    selected.append(start_num)
                    
                    while len(selected) < 6:
                        current_num = selected[-1]
                        if current_num in number_partners:
                            available_partners = [
                                (partner, count) for partner, count in number_partners[current_num]
                                if partner not in selected
                            ][:5]  # 상위 5개만 고려
                            
                            if available_partners:
                                partners = [p[0] for p in available_partners]
                                weights = [p[1] for p in available_partners]
                                
                                if sum(weights) > 0:
                                    weights = np.array(weights, dtype=np.float32) / sum(weights)
                                    chosen = np.random.choice(partners, p=weights)
                                    selected.append(int(chosen))
                                else:
                                    num = random.randint(1, 45)
                                    if num not in selected:
                                        selected.append(num)
                            else:
                                num = random.randint(1, 45)
                                if num not in selected:
                                    selected.append(num)
                        else:
                            num = random.randint(1, 45)
                            if num not in selected:
                                selected.append(num)
                
                while len(selected) < 6:
                    num = random.randint(1, 45)
                    if num not in selected:
                        selected.append(num)
                
                predictions.append(sorted(selected[:6]))
            
            # 메모리 정리
            del co_occurrence, number_partners
            gc.collect()
            
            return predictions
        except Exception as e:
            print(f"동반출현 알고리즘 오류: {e}")
            return self.generate_random_numbers(3)
    
    def generate_random_numbers(self, count):
        """랜덤 번호 생성"""
        predictions = []
        for _ in range(count):
            numbers = random.sample(range(1, 46), 6)
            predictions.append(sorted(numbers))
        return predictions
    
    def get_optimized_predictions(self):
        """메모리 최적화된 예측 결과 (5개 알고리즘만 실행)"""
        algorithms = {
            'frequency': {'name': '빈도 분석', 'description': '자주 나온 번호 기반 예측', 'category': 'basic'},
            'hot_cold': {'name': '핫/콜드 분석', 'description': '최근 출현 패턴 기반 예측', 'category': 'basic'},
            'pattern': {'name': '패턴 분석', 'description': '번호 분포 패턴 기반 예측', 'category': 'basic'},
            'statistical': {'name': '통계 분석', 'description': '통계적 모델 기반 예측', 'category': 'basic'},
            'co_occurrence': {'name': '동반출현 분석', 'description': '함께 나오는 번호 패턴 분석', 'category': 'advanced'}
        }
        
        results = {}
        successful_algorithms = 0
        
        for algo_key, algo_info in algorithms.items():
            try:
                print(f"🔄 실행 중: {algo_info['name']} ({algo_key})")
                
                # 각 알고리즘 실행
                if algo_key == 'frequency':
                    predictions = self.frequency_analysis_algorithm()
                elif algo_key == 'hot_cold':
                    predictions = self.hot_cold_algorithm()
                elif algo_key == 'pattern':
                    predictions = self.pattern_analysis_algorithm()
                elif algo_key == 'statistical':
                    predictions = self.statistical_algorithm()
                elif algo_key == 'co_occurrence':
                    predictions = self.co_occurrence_algorithm()
                
                # 예측 결과 검증
                if predictions and len(predictions) >= 3:
                    results[algo_key] = {
                        'name': algo_info['name'],
                        'description': algo_info['description'],
                        'category': algo_info['category'],
                        'predictions': predictions
                    }
                    successful_algorithms += 1
                    print(f"✅ {algo_info['name']} 완료: {len(predictions)}개 세트 생성")
                else:
                    raise ValueError("예측 결과가 부족합니다.")
                
                # 각 알고리즘 후 메모리 정리
                gc.collect()
                
            except Exception as e:
                print(f"❌ {algo_key} 알고리즘 실행 오류: {e}")
                results[algo_key] = {
                    'name': algo_info['name'],
                    'description': f"{algo_info['description']} (안전 모드)",
                    'category': algo_info['category'],
                    'predictions': self.generate_random_numbers(3)
                }
        
        print(f"📊 알고리즘 실행 완료: {successful_algorithms}/{len(algorithms)}개 성공")
        
        # 최종 메모리 정리
        gc.collect()
        
        return results

# 지연 로딩으로 메모리 절약
predictor = None

def get_predictor():
    """예측기 인스턴스 지연 생성"""
    global predictor
    if predictor is None:
        predictor = LottoPredictor()
    return predictor

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/predictions')
def get_predictions():
    """최적화된 예측 결과 API"""
    try:
        pred = get_predictor()
        if pred is None or pred.data is None:
            return jsonify({
                'success': False,
                'error': 'Data not available'
            }), 500
        
        results = pred.get_optimized_predictions()
        
        return jsonify({
            'success': True,
            'data': results,
            'total_draws': len(pred.data),
            'last_draw': int(pred.data.iloc[-1]['round']) if 'round' in pred.data.columns else None
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Prediction error: {str(e)}'
        }), 500

@app.route('/api/statistics')
def get_statistics():
    """최적화된 통계 정보 API"""
    try:
        pred = get_predictor()
        if pred is None or pred.data is None or pred.numbers is None:
            return jsonify({
                'success': False, 
                'error': 'No data available'
            }), 500
        
        # 최근 500회차만 사용하여 메모리 절약
        recent_limit = min(500, len(pred.numbers))
        recent_numbers = pred.numbers[-recent_limit:]
        all_numbers = recent_numbers.flatten()
        
        frequency = Counter(all_numbers)
        most_common = frequency.most_common(10)
        least_common = frequency.most_common()[:-11:-1]
        
        # 최근 20회차 통계
        very_recent_numbers = pred.numbers[-20:].flatten()
        recent_frequency = Counter(very_recent_numbers)
        
        # 안전한 데이터 접근
        try:
            last_row = pred.data.iloc[-1]
            last_draw_info = {
                'round': int(last_row.get('round', 0)),
                'date': str(last_row.get('draw_date', 'Unknown')),
                'numbers': pred.numbers[-1].tolist(),
                'bonus': int(last_row.get('bonus_num', 0)) if 'bonus_num' in last_row else 0
            }
        except:
            last_draw_info = {
                'round': 0,
                'date': 'Unknown',
                'numbers': [1, 2, 3, 4, 5, 6],
                'bonus': 0
            }
        
        stats = {
            'total_draws': len(pred.data),
            'most_frequent': [{'number': int(num), 'count': int(count)} for num, count in most_common],
            'least_frequent': [{'number': int(num), 'count': int(count)} for num, count in least_common],
            'recent_hot': [{'number': int(num), 'count': int(count)} for num, count in recent_frequency.most_common(10)],
            'last_draw_info': last_draw_info
        }
        
        # 메모리 정리
        del frequency, recent_frequency, all_numbers, very_recent_numbers
        gc.collect()
        
        return jsonify({
            'success': True,
            'data': stats
        })
    except Exception as e:
        print(f"Statistics API error: {e}")
        return jsonify({
            'success': False,
            'error': f'Statistics error: {str(e)}'
        }), 500

@app.route('/api/health')
def health_check():
    """헬스체크 API"""
    try:
        pred = get_predictor()
        return jsonify({
            'success': True,
            'status': 'healthy',
            'data_loaded': pred is not None and pred.data is not None
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'status': 'unhealthy',
            'error': str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)  # debug=False로 메모리 절약
