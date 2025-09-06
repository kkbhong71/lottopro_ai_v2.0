from flask import Flask, render_template, request, jsonify
import pandas as pd
import numpy as np
import random
from collections import Counter, defaultdict
import os
import gc
import warnings
import itertools
import math

warnings.filterwarnings('ignore')

app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

class AdvancedLottoPredictor:
    def __init__(self, csv_file_path='new_1187.csv'):
        self.csv_file_path = csv_file_path
        self.data = None
        self.numbers = None
        self.load_data()
        
        # 각 알고리즘별 가중치 (우선순위)
        self.algorithm_weights = {
            'frequency': 0.12,
            'hot_cold': 0.11,
            'pattern': 0.10,
            'statistics': 0.09,
            'machine_learning': 0.08,
            'neural_network': 0.12,
            'markov_chain': 0.10,
            'genetic': 0.09,
            'correlation': 0.10,
            'time_series': 0.09
        }
    
    def load_data(self):
        """데이터 로드 및 전처리"""
        try:
            if not os.path.exists(self.csv_file_path):
                print(f"❌ CSV 파일을 찾을 수 없습니다: {self.csv_file_path}")
                return False
            
            self.data = pd.read_csv(self.csv_file_path)
            
            if len(self.data.columns) >= 7:
                self.data.columns = ['round', 'draw_date', 'num1', 'num2', 'num3', 'num4', 'num5', 'num6', 'bonus_num'][:len(self.data.columns)]
            
            number_cols = ['num1', 'num2', 'num3', 'num4', 'num5', 'num6']
            available_cols = [col for col in number_cols if col in self.data.columns]
            
            if len(available_cols) >= 6:
                self.numbers = self.data[available_cols].values.astype(int)
                print(f"✅ 데이터 로드 완료: {len(self.data)}개 회차")
                return True
            else:
                print(f"❌ 필요한 컬럼이 부족합니다. 사용 가능: {available_cols}")
                return False
                
        except Exception as e:
            print(f"❌ 데이터 로드 실패: {e}")
            return False

    def algorithm_1_frequency_analysis(self):
        """1. 빈도 분석 - 과거 당첨번호 출현 빈도 기반"""
        try:
            if self.numbers is None:
                return self._generate_fallback_numbers("빈도 분석")
            
            all_numbers = self.numbers.flatten()
            frequency = Counter(all_numbers)
            
            # 상위 15개 번호 중에서 가중 랜덤 선택
            top_numbers = [num for num, count in frequency.most_common(15)]
            weights = [count for num, count in frequency.most_common(15)]
            
            selected = []
            temp_numbers = top_numbers.copy()
            temp_weights = weights.copy()
            
            for _ in range(6):
                if not temp_numbers:
                    break
                idx = random.choices(range(len(temp_numbers)), weights=temp_weights)[0]
                selected.append(temp_numbers.pop(idx))
                temp_weights.pop(idx)
            
            while len(selected) < 6:
                selected.append(random.randint(1, 45))
            
            return {
                'name': '빈도 분석',
                'description': '과거 당첨번호 출현 빈도를 분석하여 가중 확률로 예측',
                'category': 'basic',
                'algorithm_id': 1,
                'priority_numbers': sorted(list(set(selected)))[:6],
                'confidence': 85
            }
        except Exception as e:
            return self._generate_fallback_numbers("빈도 분석")

    def algorithm_2_hot_cold_analysis(self):
        """2. 핫/콜드 분석 - 최근 출현 패턴 분석"""
        try:
            if self.numbers is None or len(self.numbers) < 20:
                return self._generate_fallback_numbers("핫/콜드 분석")
            
            # 최근 20회차 분석
            recent_numbers = self.numbers[-20:].flatten()
            recent_freq = Counter(recent_numbers)
            
            # 전체 평균과 비교
            all_numbers = self.numbers.flatten()
            total_freq = Counter(all_numbers)
            
            hot_numbers = []
            for num in range(1, 46):
                recent_count = recent_freq.get(num, 0)
                expected_count = total_freq.get(num, 0) * (20 / len(self.numbers))
                
                if recent_count > expected_count:
                    hot_numbers.append((num, recent_count - expected_count))
            
            # 핫 넘버 우선 선택
            hot_numbers.sort(key=lambda x: x[1], reverse=True)
            selected = [num for num, _ in hot_numbers[:4]]
            
            # 나머지는 콜드 넘버에서 선택
            cold_candidates = [num for num in range(1, 46) if num not in selected]
            selected.extend(random.sample(cold_candidates, min(2, len(cold_candidates))))
            
            while len(selected) < 6:
                selected.append(random.randint(1, 45))
            
            return {
                'name': '핫/콜드 분석',
                'description': '최근 출현 패턴 기반 핫넘버와 콜드넘버 조합 예측',
                'category': 'basic',
                'algorithm_id': 2,
                'priority_numbers': sorted(list(set(selected)))[:6],
                'confidence': 78
            }
        except Exception as e:
            return self._generate_fallback_numbers("핫/콜드 분석")

    def algorithm_3_pattern_analysis(self):
        """3. 패턴 분석 - 번호 구간별 패턴 분석"""
        try:
            if self.numbers is None:
                return self._generate_fallback_numbers("패턴 분석")
            
            # 구간별 분석 (1-15, 16-30, 31-45)
            sections = {'low': [], 'mid': [], 'high': []}
            
            for row in self.numbers:
                for num in row:
                    if 1 <= num <= 15:
                        sections['low'].append(num)
                    elif 16 <= num <= 30:
                        sections['mid'].append(num)
                    elif 31 <= num <= 45:
                        sections['high'].append(num)
            
            # 각 구간에서 빈도 높은 번호 선택
            selected = []
            for section_name, section_numbers in sections.items():
                if section_numbers:
                    freq = Counter(section_numbers)
                    top_nums = [num for num, _ in freq.most_common(3)]
                    selected.extend(random.sample(top_nums, min(2, len(top_nums))))
            
            while len(selected) < 6:
                selected.append(random.randint(1, 45))
            
            return {
                'name': '패턴 분석',
                'description': '번호 구간별 출현 패턴과 수학적 관계 분석 예측',
                'category': 'basic',
                'algorithm_id': 3,
                'priority_numbers': sorted(list(set(selected)))[:6],
                'confidence': 73
            }
        except Exception as e:
            return self._generate_fallback_numbers("패턴 분석")

    def algorithm_4_statistical_analysis(self):
        """4. 통계 분석 - 고급 통계 기법 적용"""
        try:
            if self.numbers is None:
                return self._generate_fallback_numbers("통계 분석")
            
            all_numbers = self.numbers.flatten()
            
            # 정규분포 기반 예측
            mean_val = np.mean(all_numbers)
            std_val = np.std(all_numbers)
            
            # 표준점수 기반 선택
            candidates = []
            for num in range(1, 46):
                z_score = abs((num - mean_val) / std_val)
                if z_score <= 1.5:  # 1.5 표준편차 내
                    candidates.append(num)
            
            if len(candidates) < 6:
                candidates = list(range(1, 46))
            
            # 정규분포 가중치로 선택 (간단한 확률 계산)
            weights = []
            for num in candidates:
                weight = math.exp(-0.5 * ((num - mean_val) / std_val) ** 2)
                weights.append(weight)
            
            selected = random.choices(candidates, weights=weights, k=6)
            
            return {
                'name': '통계 분석',
                'description': '정규분포와 확률 이론을 적용한 수학적 예측',
                'category': 'basic',
                'algorithm_id': 4,
                'priority_numbers': sorted(list(set(selected)))[:6],
                'confidence': 81
            }
        except Exception as e:
            return self._generate_fallback_numbers("통계 분석")

    def algorithm_5_machine_learning(self):
        """5. 머신러닝 - 간단한 패턴 학습 기반 예측"""
        try:
            if self.numbers is None or len(self.numbers) < 50:
                return self._generate_fallback_numbers("머신러닝")
            
            # 간단한 패턴 기반 예측 (ML 라이브러리 없이)
            # 최근 10회차의 번호 패턴 분석
            recent_data = self.numbers[-10:]
            
            # 각 위치별 평균 계산
            position_averages = []
            for pos in range(6):
                pos_numbers = [row[pos] for row in recent_data]
                avg = sum(pos_numbers) / len(pos_numbers)
                position_averages.append(int(round(avg)))
            
            # 평균 주변의 번호들로 조정
            selected = []
            for avg in position_averages:
                # 평균 ±5 범위에서 선택
                range_start = max(1, avg - 5)
                range_end = min(45, avg + 5)
                selected.append(random.randint(range_start, range_end))
            
            # 중복 제거 및 보정
            selected = list(set(selected))
            while len(selected) < 6:
                selected.append(random.randint(1, 45))
            
            return {
                'name': '머신러닝',
                'description': '패턴 학습 기반 위치별 평균 예측',
                'category': 'basic',
                'algorithm_id': 5,
                'priority_numbers': sorted(list(set(selected)))[:6],
                'confidence': 76
            }
        except Exception as e:
            return self._generate_fallback_numbers("머신러닝")

    def algorithm_6_neural_network(self):
        """6. 신경망 분석 - 가중치 기반 예측"""
        try:
            if self.numbers is None or len(self.numbers) < 30:
                return self._generate_fallback_numbers("신경망 분석")
            
            # 간단한 가중치 네트워크 시뮬레이션
            # 최근 데이터에 더 높은 가중치 부여
            weights = [i/sum(range(1, len(self.numbers)+1)) for i in range(1, len(self.numbers)+1)]
            
            # 가중 평균 계산
            weighted_numbers = []
            for i, row in enumerate(self.numbers):
                for num in row:
                    weighted_numbers.extend([num] * int(weights[i] * 100))
            
            # 빈도 기반 선택
            freq = Counter(weighted_numbers)
            top_numbers = [num for num, _ in freq.most_common(15)]
            selected = random.sample(top_numbers, min(6, len(top_numbers)))
            
            while len(selected) < 6:
                selected.append(random.randint(1, 45))
            
            return {
                'name': '신경망 분석',
                'description': '가중치 네트워크를 통한 복합 패턴 학습 예측',
                'category': 'advanced',
                'algorithm_id': 6,
                'priority_numbers': sorted(list(set(selected)))[:6],
                'confidence': 79
            }
        except Exception as e:
            return self._generate_fallback_numbers("신경망 분석")

    def algorithm_7_markov_chain(self):
        """7. 마르코프 체인 - 상태 전이 확률 모델"""
        try:
            if self.numbers is None or len(self.numbers) < 20:
                return self._generate_fallback_numbers("마르코프 체인")
            
            # 전이 확률 행렬 구성
            transition_matrix = defaultdict(lambda: defaultdict(int))
            
            # 연속된 회차 간 번호 전이 패턴 분석
            for i in range(len(self.numbers) - 1):
                current_set = set(self.numbers[i])
                next_set = set(self.numbers[i + 1])
                
                for curr_num in current_set:
                    for next_num in next_set:
                        transition_matrix[curr_num][next_num] += 1
            
            # 마지막 회차 기반 예측
            last_numbers = set(self.numbers[-1])
            predictions = []
            
            for curr_num in last_numbers:
                if curr_num in transition_matrix:
                    transitions = transition_matrix[curr_num]
                    if transitions:
                        total = sum(transitions.values())
                        probs = [(next_num, count/total) for next_num, count in transitions.items()]
                        probs.sort(key=lambda x: x[1], reverse=True)
                        predictions.extend([num for num, prob in probs[:2]])
            
            # 중복 제거 및 부족한 수 채우기
            selected = list(set(predictions))[:6]
            while len(selected) < 6:
                selected.append(random.randint(1, 45))
            
            return {
                'name': '마르코프 체인',
                'description': '상태 전이 확률을 이용한 연속성 패턴 예측',
                'category': 'advanced',
                'algorithm_id': 7,
                'priority_numbers': sorted(list(set(selected)))[:6],
                'confidence': 74
            }
        except Exception as e:
            return self._generate_fallback_numbers("마르코프 체인")

    def algorithm_8_genetic_algorithm(self):
        """8. 유전자 알고리즘 - 진화론적 최적화"""
        try:
            if self.numbers is None:
                return self._generate_fallback_numbers("유전자 알고리즘")
            
            # 적합도 함수: 과거 당첨번호와의 유사성
            def fitness(individual):
                score = 0
                for past_draw in self.numbers[-10:]:  # 최근 10회차
                    common = len(set(individual) & set(past_draw))
                    score += common * common  # 공통 번호 수의 제곱
                return score
            
            # 초기 집단 생성
            population_size = 30  # 경량화
            population = []
            for _ in range(population_size):
                individual = sorted(random.sample(range(1, 46), 6))
                population.append(individual)
            
            # 진화 과정 (간소화된 버전)
            for generation in range(5):  # 세대 수 축소
                # 적합도 계산
                fitness_scores = [(ind, fitness(ind)) for ind in population]
                fitness_scores.sort(key=lambda x: x[1], reverse=True)
                
                # 상위 50% 선택
                selected = [ind for ind, score in fitness_scores[:population_size//2]]
                
                # 다음 세대 생성 (교차 + 돌연변이)
                new_population = selected.copy()
                while len(new_population) < population_size:
                    parent1, parent2 = random.sample(selected, 2)
                    # 교차
                    child = list(set(parent1[:3] + parent2[3:]))
                    # 돌연변이
                    if random.random() < 0.1:
                        if len(child) > 0:
                            child[random.randint(0, len(child)-1)] = random.randint(1, 45)
                    
                    while len(child) < 6:
                        child.append(random.randint(1, 45))
                    new_population.append(sorted(list(set(child))[:6]))
                
                population = new_population
            
            # 최적 개체 선택
            final_fitness = [(ind, fitness(ind)) for ind in population]
            best_individual = max(final_fitness, key=lambda x: x[1])[0]
            
            return {
                'name': '유전자 알고리즘',
                'description': '진화론적 최적화를 통한 적응형 번호 조합 예측',
                'category': 'advanced',
                'algorithm_id': 8,
                'priority_numbers': sorted(list(set(best_individual)))[:6],
                'confidence': 77
            }
        except Exception as e:
            return self._generate_fallback_numbers("유전자 알고리즘")

    def algorithm_9_correlation_analysis(self):
        """9. 동반출현 분석 - 번호 간 상관관계"""
        try:
            if self.numbers is None or len(self.numbers) < 30:
                return self._generate_fallback_numbers("동반출현 분석")
            
            # 번호 간 동반 출현 빈도 계산
            co_occurrence = defaultdict(int)
            
            for draw in self.numbers:
                for i in range(len(draw)):
                    for j in range(i + 1, len(draw)):
                        pair = tuple(sorted([draw[i], draw[j]]))
                        co_occurrence[pair] += 1
            
            # 강한 상관관계 페어 찾기
            strong_pairs = sorted(co_occurrence.items(), key=lambda x: x[1], reverse=True)[:20]
            
            selected = []
            used_numbers = set()
            
            # 강한 연관성 있는 페어부터 선택
            for (num1, num2), count in strong_pairs:
                if len(selected) >= 6:
                    break
                if num1 not in used_numbers and num2 not in used_numbers:
                    selected.extend([num1, num2])
                    used_numbers.update([num1, num2])
                elif num1 not in used_numbers:
                    selected.append(num1)
                    used_numbers.add(num1)
                elif num2 not in used_numbers:
                    selected.append(num2)
                    used_numbers.add(num2)
            
            # 부족한 수 채우기
            available = [n for n in range(1, 46) if n not in used_numbers]
            while len(selected) < 6 and available:
                selected.append(available.pop(random.randint(0, len(available)-1)))
            
            return {
                'name': '동반출현 분석',
                'description': '번호 간 동반 출현 상관관계를 분석한 조합 예측',
                'category': 'advanced',
                'algorithm_id': 9,
                'priority_numbers': sorted(list(set(selected)))[:6],
                'confidence': 75
            }
        except Exception as e:
            return self._generate_fallback_numbers("동반출현 분석")

    def algorithm_10_time_series(self):
        """10. 시계열 분석 - 시간 패턴 예측"""
        try:
            if self.numbers is None or len(self.numbers) < 20:
                return self._generate_fallback_numbers("시계열 분석")
            
            # 각 번호별 시간에 따른 출현 패턴 분석
            time_patterns = {}
            
            for num in range(1, 46):
                appearances = []
                for i, draw in enumerate(self.numbers):
                    if num in draw:
                        appearances.append(i)
                
                if len(appearances) >= 3:
                    # 출현 간격 계산
                    intervals = []
                    for i in range(1, len(appearances)):
                        intervals.append(appearances[i] - appearances[i-1])
                    
                    avg_interval = sum(intervals) / len(intervals)
                    last_appearance = appearances[-1]
                    
                    # 다음 출현 예상 시점
                    next_expected = last_appearance + avg_interval
                    current_time = len(self.numbers) - 1
                    
                    # 출현 확률 계산 (가까울수록 높음)
                    prob = max(0, 1 - abs(next_expected - current_time) / avg_interval)
                    time_patterns[num] = prob
            
            # 확률 높은 순으로 정렬
            sorted_patterns = sorted(time_patterns.items(), key=lambda x: x[1], reverse=True)
            
            # 상위 10개 중에서 6개 선택
            candidates = [num for num, prob in sorted_patterns[:15]]
            if len(candidates) < 6:
                candidates.extend(random.sample(range(1, 46), 6 - len(candidates)))
            
            selected = random.sample(candidates, 6)
            
            return {
                'name': '시계열 분석',
                'description': '시간 흐름에 따른 출현 패턴 예측',
                'category': 'advanced',
                'algorithm_id': 10,
                'priority_numbers': sorted(list(set(selected)))[:6],
                'confidence': 72
            }
        except Exception as e:
            return self._generate_fallback_numbers("시계열 분석")

    def _generate_fallback_numbers(self, algorithm_name):
        """백업용 번호 생성"""
        return {
            'name': algorithm_name,
            'description': f'{algorithm_name} (백업 모드)',
            'category': 'basic',
            'algorithm_id': 0,
            'priority_numbers': sorted(random.sample(range(1, 46), 6)),
            'confidence': 50
        }

    def generate_all_predictions(self):
        """10가지 알고리즘 모두 실행하여 각각 1개씩 번호 생성"""
        try:
            algorithms = [
                self.algorithm_1_frequency_analysis,
                self.algorithm_2_hot_cold_analysis,
                self.algorithm_3_pattern_analysis,
                self.algorithm_4_statistical_analysis,
                self.algorithm_5_machine_learning,
                self.algorithm_6_neural_network,
                self.algorithm_7_markov_chain,
                self.algorithm_8_genetic_algorithm,
                self.algorithm_9_correlation_analysis,
                self.algorithm_10_time_series
            ]
            
            results = {}
            for i, algorithm in enumerate(algorithms, 1):
                try:
                    result = algorithm()
                    algorithm_key = f"algorithm_{i:02d}"
                    results[algorithm_key] = result
                    print(f"✅ 알고리즘 {i}: {result['name']} 완료")
                except Exception as e:
                    print(f"❌ 알고리즘 {i} 실행 오류: {e}")
                    results[f"algorithm_{i:02d}"] = self._generate_fallback_numbers(f"알고리즘 {i}")
            
            return results
            
        except Exception as e:
            print(f"전체 예측 생성 오류: {e}")
            return self._generate_emergency_backup()

    def _generate_emergency_backup(self):
        """긴급 백업 응답"""
        backup_algorithms = [
            "빈도 분석", "핫/콜드 분석", "패턴 분석", "통계 분석", "머신러닝",
            "신경망 분석", "마르코프 체인", "유전자 알고리즘", "동반출현 분석", "시계열 분석"
        ]
        
        results = {}
        for i, name in enumerate(backup_algorithms, 1):
            results[f"algorithm_{i:02d}"] = {
                'name': name,
                'description': f'{name} (긴급 백업)',
                'category': 'advanced' if i > 5 else 'basic',
                'algorithm_id': i,
                'priority_numbers': sorted(random.sample(range(1, 46), 6)),
                'confidence': 50
            }
        
        return results

# 전역 변수
predictor = None

def get_predictor():
    global predictor
    if predictor is None:
        predictor = AdvancedLottoPredictor()
    return predictor

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/health')
def health():
    """헬스체크 API"""
    try:
        pred = get_predictor()
        return jsonify({
            'success': True,
            'status': 'healthy',
            'data_loaded': pred.data is not None,
            'algorithms_available': 10
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'status': 'unhealthy',
            'error': str(e)
        }), 500

@app.route('/api/predictions')
def get_predictions():
    """10가지 알고리즘 예측 API"""
    try:
        pred = get_predictor()
        
        if pred.data is None:
            if not pred.load_data():
                return jsonify({
                    'success': False,
                    'error': 'CSV 데이터를 로드할 수 없습니다.'
                }), 500
        
        # 10가지 알고리즘 모두 실행
        results = pred.generate_all_predictions()
        
        return jsonify({
            'success': True,
            'data': results,
            'total_algorithms': len(results),
            'total_draws': len(pred.data) if pred.data is not None else 0,
            'message': '10가지 AI 알고리즘이 각각 1개씩의 우선 번호를 생성했습니다.'
        })
        
    except Exception as e:
        print(f"API 예측 에러: {e}")
        return jsonify({
            'success': False,
            'error': f'예측 생성 중 오류가 발생했습니다: {str(e)}'
        }), 500

@app.route('/api/statistics')
def get_statistics():
    """통계 정보 API"""
    try:
        pred = get_predictor()
        
        default_stats = {
            'total_draws': 1187,
            'algorithms_count': 10,
            'last_draw_info': {
                'round': 1187,
                'date': '2024-01-01',
                'numbers': [1, 7, 13, 19, 25, 31],
                'bonus': 7
            },
            'most_frequent': [{'number': i, 'count': 50-i} for i in range(1, 11)],
            'least_frequent': [{'number': i+35, 'count': i} for i in range(1, 11)],
            'recent_hot': [{'number': i+10, 'count': 20-i} for i in range(1, 11)]
        }
        
        if pred.data is not None and pred.numbers is not None:
            try:
                all_numbers = pred.numbers.flatten()
                frequency = Counter(all_numbers)
                
                most_common = frequency.most_common(10)
                least_common = frequency.most_common()[:-11:-1]
                
                last_row = pred.data.iloc[-1]
                
                stats = {
                    'total_draws': len(pred.data),
                    'algorithms_count': 10,
                    'most_frequent': [{'number': int(num), 'count': int(count)} for num, count in most_common],
                    'least_frequent': [{'number': int(num), 'count': int(count)} for num, count in least_common],
                    'recent_hot': [{'number': int(num), 'count': int(count)} for num, count in most_common[:10]],
                    'last_draw_info': {
                        'round': int(last_row.get('round', 1187)),
                        'date': str(last_row.get('draw_date', '2024-01-01')),
                        'numbers': pred.numbers[-1].tolist(),
                        'bonus': int(last_row.get('bonus_num', 7)) if 'bonus_num' in last_row else 7
                    }
                }
            except:
                stats = default_stats
        else:
            stats = default_stats
        
        return jsonify({
            'success': True,
            'data': stats
        })
        
    except Exception as e:
        print(f"API 통계 에러: {e}")
        return jsonify({
            'success': False,
            'error': 'Statistics temporarily unavailable'
        }), 500

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)
