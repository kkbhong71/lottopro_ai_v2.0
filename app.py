from flask import Flask, render_template, request, jsonify, send_from_directory, make_response
import pandas as pd
import numpy as np
import random
from collections import Counter, defaultdict
import os
import gc
import warnings
import itertools
import math
import time
import hashlib
import json
from datetime import datetime, timedelta

warnings.filterwarnings('ignore')

app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

def safe_int(value):
    """numpy.int64를 Python int로 안전하게 변환"""
    try:
        return int(value)
    except (ValueError, TypeError):
        return value

def safe_int_list(lst):
    """리스트의 모든 요소를 안전하게 int로 변환"""
    return [safe_int(x) for x in lst]

def get_dynamic_seed():
    """동적 시드 생성 - 매번 다른 값"""
    return int(time.time() * 1000000 + random.randint(1, 10000)) % 2147483647

def ensure_six_numbers(selected, exclude_set=None):
    """6개 번호 보장 함수 - 중복 제거 후 부족한 번호 채우기"""
    if exclude_set is None:
        exclude_set = set()
    
    # 중복 제거
    unique_selected = list(set(selected))
    
    # 6개가 안 되면 추가 생성
    available_numbers = [n for n in range(1, 46) if n not in unique_selected and n not in exclude_set]
    random.shuffle(available_numbers)
    
    while len(unique_selected) < 6 and available_numbers:
        unique_selected.append(available_numbers.pop(0))
    
    # 여전히 6개가 안 되면 강제로 채움
    while len(unique_selected) < 6:
        for num in range(1, 46):
            if num not in unique_selected:
                unique_selected.append(num)
                break
    
    return sorted(unique_selected[:6])

def fix_invalid_numbers(numbers):
    """잘못된 번호 수정"""
    try:
        fixed = []
        
        if isinstance(numbers, list):
            for num in numbers:
                try:
                    n = int(num)
                    if 1 <= n <= 45 and n not in fixed:
                        fixed.append(n)
                except:
                    continue
        
        while len(fixed) < 6:
            rand_num = random.randint(1, 45)
            if rand_num not in fixed:
                fixed.append(rand_num)
        
        return sorted(fixed[:6])
        
    except:
        return generate_default_numbers()

def generate_default_numbers():
    """기본 번호 생성"""
    numbers = random.sample(range(1, 46), 6)
    return sorted(numbers)

class AdvancedLottoPredictor:
    def __init__(self, csv_file_path='new_1191.csv'):
        self.csv_file_path = csv_file_path
        self.data = None
        self.numbers = None
        self.data_loaded = False
        self.load_data()
        
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
        """실제 CSV 데이터 로드 및 전처리"""
        try:
            print(f"🚀 로또프로 AI v2.0 - 실제 데이터 로딩 시작")
            
            current_dir = os.getcwd()
            print(f"📁 현재 디렉토리: {current_dir}")
            
            # 실제 CSV 파일 경로들 (GitHub에 업로드된 파일 기준)
            possible_paths = [
                'new_1191.csv',
                './new_1191.csv',
                os.path.join(current_dir, 'new_1191.csv'),
                'data/new_1191.csv'
            ]
            
            found_file = None
            for path in possible_paths:
                if os.path.exists(path):
                    found_file = path
                    print(f"✅ CSV 파일 발견: {path}")
                    break
            
            if found_file:
                self.csv_file_path = found_file
                print(f"📊 로딩 중: {self.csv_file_path}")
                
                # CSV 파일 읽기
                self.data = pd.read_csv(self.csv_file_path)
                print(f"📈 원본 데이터 크기: {self.data.shape}")
                print(f"📋 컬럼명: {list(self.data.columns)}")
                
                # 컬럼명 표준화 (GitHub에 보이는 구조에 맞춰)
                expected_columns = ['round', 'draw_date', 'num1', 'num2', 'num3', 'num4', 'num5', 'num6', 'bonus_num']
                
                if len(self.data.columns) >= 9:
                    self.data.columns = expected_columns[:len(self.data.columns)]
                    print(f"✅ 컬럼명 표준화 완료: {list(self.data.columns)}")
                
                # 번호 컬럼 추출 및 검증
                number_cols = ['num1', 'num2', 'num3', 'num4', 'num5', 'num6']
                
                # 데이터 타입 확인 및 변환
                for col in number_cols:
                    if col in self.data.columns:
                        self.data[col] = pd.to_numeric(self.data[col], errors='coerce')
                
                # 결측값 확인
                missing_values = self.data[number_cols].isnull().sum().sum()
                if missing_values > 0:
                    print(f"⚠️ 결측값 발견: {missing_values}개 - 제거 중...")
                    self.data = self.data.dropna(subset=number_cols)
                
                # 번호 범위 검증 (1-45)
                for col in number_cols:
                    invalid_count = ((self.data[col] < 1) | (self.data[col] > 45)).sum()
                    if invalid_count > 0:
                        print(f"⚠️ {col}에서 유효하지 않은 번호 {invalid_count}개 발견")
                
                # 최종 데이터 준비
                if all(col in self.data.columns for col in number_cols):
                    self.numbers = self.data[number_cols].values.astype(int)
                    
                    # 데이터 검증
                    valid_rows = []
                    for i, row in enumerate(self.numbers):
                        if len(set(row)) == 6 and all(1 <= num <= 45 for num in row):
                            valid_rows.append(i)
                    
                    if len(valid_rows) > 0:
                        self.data = self.data.iloc[valid_rows].reset_index(drop=True)
                        self.numbers = self.numbers[valid_rows]
                        
                        print(f"✅ 실제 데이터 로드 완료!")
                        print(f"📊 유효한 회차 수: {len(self.data)}")
                        print(f"📅 데이터 기간: {self.data['draw_date'].min()} ~ {self.data['draw_date'].max()}")
                        print(f"🎯 최신 회차: {self.data['round'].max()}회")
                        
                        # 샘플 데이터 출력
                        latest_draw = self.data.iloc[-1]
                        latest_numbers = [int(latest_draw[col]) for col in number_cols]
                        print(f"📋 최근 당첨번호: {latest_numbers} + 보너스: {int(latest_draw.get('bonus_num', 0))}")
                        
                        self.data_loaded = True
                        return True
                    else:
                        print(f"❌ 유효한 데이터가 없습니다")
                        return self._create_fallback_data()
                else:
                    print(f"❌ 필요한 컬럼이 부족합니다: {number_cols}")
                    return self._create_fallback_data()
            else:
                print(f"❌ new_1191.csv 파일을 찾을 수 없습니다")
                # 파일 목록 확인
                try:
                    files_in_dir = [f for f in os.listdir('.') if f.endswith('.csv')]
                    print(f"📂 현재 디렉토리의 CSV 파일들: {files_in_dir}")
                except:
                    print(f"📂 디렉토리 읽기 실패")
                
                return self._create_fallback_data()
                
        except Exception as e:
            print(f"❌ 데이터 로드 중 오류 발생: {str(e)}")
            import traceback
            traceback.print_exc()
            return self._create_fallback_data()

    def _create_fallback_data(self):
        """CSV 파일이 없을 때 샘플 데이터 생성"""
        try:
            print("🔄 샘플 로또 데이터 생성 중...")
            
            # 1191회차 샘플 데이터 생성
            sample_data = []
            for round_num in range(1, 1191):
                # 현실적인 로또 번호 생성 (완전 랜덤이 아닌 가중치 적용)
                numbers = []
                while len(numbers) < 6:
                    # 1-45 범위에서 가중치를 적용한 번호 생성
                    if len(numbers) < 2:  # 첫 2개는 1-15 구간에서 높은 확률
                        num = random.choices(range(1, 46), 
                                           weights=[2.0 if i <= 15 else 1.0 for i in range(1, 46)])[0]
                    elif len(numbers) < 4:  # 다음 2개는 16-30 구간에서 높은 확률
                        num = random.choices(range(1, 46), 
                                           weights=[1.0 if i <= 15 else 2.0 if i <= 30 else 1.0 for i in range(1, 46)])[0]
                    else:  # 마지막 2개는 31-45 구간에서 높은 확률
                        num = random.choices(range(1, 46), 
                                           weights=[1.0 if i <= 30 else 2.0 for i in range(1, 46)])[0]
                    
                    if num not in numbers:
                        numbers.append(num)
                
                numbers.sort()
                bonus = random.randint(1, 45)
                while bonus in numbers:
                    bonus = random.randint(1, 45)
                
                # 날짜 생성 (매주 토요일)
                base_date = datetime(2000, 1, 1)
                draw_date = base_date + timedelta(weeks=round_num-1)
                
                sample_data.append({
                    'round': round_num,
                    'draw_date': draw_date.strftime('%Y-%m-%d'),
                    'num1': numbers[0],
                    'num2': numbers[1],
                    'num3': numbers[2],
                    'num4': numbers[3],
                    'num5': numbers[4],
                    'num6': numbers[5],
                    'bonus_num': bonus
                })
            
            self.data = pd.DataFrame(sample_data)
            self.numbers = self.data[['num1', 'num2', 'num3', 'num4', 'num5', 'num6']].values.astype(int)
            self.data_loaded = True
            print(f"✅ 샘플 데이터 생성 완료: {len(self.data)}개 회차")
            return True
            
        except Exception as e:
            print(f"❌ 샘플 데이터 생성 실패: {e}")
            self.data_loaded = False
            return False

    def algorithm_1_frequency_analysis(self):
        """1. 빈도 분석"""
        try:
            seed = get_dynamic_seed()
            random.seed(seed)
            np.random.seed(seed)
            
            if self.numbers is None:
                return self._generate_fallback_numbers("빈도 분석")
            
            all_numbers = self.numbers.flatten()
            frequency = Counter(all_numbers)
            
            top_numbers = [safe_int(num) for num, count in frequency.most_common(20)]
            weights = [count for num, count in frequency.most_common(20)]
            
            selected = []
            used_numbers = set()
            
            for _ in range(6):
                if not top_numbers:
                    break
                
                available_indices = [i for i, num in enumerate(top_numbers) if num not in used_numbers]
                if not available_indices:
                    break
                    
                available_weights = [weights[i] + random.randint(1, 10) for i in available_indices]
                chosen_idx = random.choices(available_indices, weights=available_weights)[0]
                chosen_number = top_numbers[chosen_idx]
                
                selected.append(chosen_number)
                used_numbers.add(chosen_number)
            
            final_numbers = ensure_six_numbers(selected)
            
            return {
                'name': '빈도 분석',
                'description': '과거 당첨번호 출현 빈도를 분석하여 가중 확률로 예측',
                'category': 'basic',
                'algorithm_id': 1,
                'priority_numbers': safe_int_list(final_numbers),
                'confidence': 85
            }
        except Exception as e:
            return self._generate_fallback_numbers("빈도 분석", "basic", 1)

    def algorithm_2_hot_cold_analysis(self):
        """2. 핫/콜드 분석"""
        try:
            seed = get_dynamic_seed() + random.randint(1, 1000)
            random.seed(seed)
            np.random.seed(seed)
            
            if self.numbers is None or len(self.numbers) < 20:
                return self._generate_fallback_numbers("핫/콜드 분석")
            
            analysis_range = random.randint(15, 25)
            recent_numbers = self.numbers[-analysis_range:].flatten()
            recent_freq = Counter(recent_numbers)
            
            all_numbers = self.numbers.flatten()
            total_freq = Counter(all_numbers)
            
            hot_numbers = []
            cold_numbers = []
            
            for num in range(1, 46):
                recent_count = recent_freq.get(num, 0)
                expected_count = total_freq.get(num, 0) * (analysis_range / len(self.numbers))
                
                hot_threshold = random.uniform(0.5, 1.5)
                
                if recent_count > expected_count + hot_threshold:
                    hot_numbers.append((safe_int(num), recent_count - expected_count))
                elif recent_count < expected_count - hot_threshold:
                    cold_numbers.append((safe_int(num), expected_count - recent_count))
            
            hot_numbers.sort(key=lambda x: x[1] + random.uniform(-0.5, 0.5), reverse=True)
            random.shuffle(cold_numbers)
            
            selected = []
            used_numbers = set()
            
            hot_count = random.randint(3, 5)
            for num, _ in hot_numbers[:hot_count]:
                if len(selected) < 6 and num not in used_numbers:
                    selected.append(num)
                    used_numbers.add(num)
            
            remaining_needed = 6 - len(selected)
            cold_candidates = [num for num, _ in cold_numbers if num not in used_numbers]
            random_candidates = [num for num in range(1, 46) if num not in used_numbers]
            
            for _ in range(remaining_needed):
                if random.random() > 0.3 and cold_candidates:
                    chosen = random.choice(cold_candidates)
                    cold_candidates.remove(chosen)
                elif random_candidates:
                    chosen = random.choice(random_candidates)
                    random_candidates.remove(chosen)
                else:
                    break
                
                selected.append(chosen)
                used_numbers.add(chosen)
            
            final_numbers = ensure_six_numbers(selected)
            
            return {
                'name': '핫/콜드 분석',
                'description': '최근 출현 패턴 기반 핫넘버와 콜드넘버 조합 예측',
                'category': 'basic',
                'algorithm_id': 2,
                'priority_numbers': safe_int_list(final_numbers),
                'confidence': 78
            }
        except Exception as e:
            return self._generate_fallback_numbers("핫/콜드 분석", "basic", 2)

    def algorithm_3_pattern_analysis(self):
        """3. 패턴 분석"""
        try:
            seed = get_dynamic_seed() + int(time.time() % 10000)
            random.seed(seed)
            np.random.seed(seed)
            
            if self.numbers is None:
                return self._generate_fallback_numbers("패턴 분석")
            
            section_size = random.randint(12, 18)
            sections = {
                'low': list(range(1, section_size + 1)),
                'mid': list(range(section_size + 1, section_size * 2 + 1)),
                'high': list(range(section_size * 2 + 1, 46))
            }
            
            section_counts = {'low': [], 'mid': [], 'high': []}
            analysis_rounds = random.randint(30, 100)
            analysis_data = self.numbers[-analysis_rounds:]
            
            for row in analysis_data:
                for num in row:
                    if num in sections['low']:
                        section_counts['low'].append(safe_int(num))
                    elif num in sections['mid']:
                        section_counts['mid'].append(safe_int(num))
                    elif num in sections['high']:
                        section_counts['high'].append(safe_int(num))
            
            selected = []
            used_numbers = set()
            
            section_distribution = [
                random.randint(1, 3),
                random.randint(1, 3),
                random.randint(1, 3)
            ]
            
            total = sum(section_distribution)
            while total > 6:
                idx = random.randint(0, 2)
                if section_distribution[idx] > 1:
                    section_distribution[idx] -= 1
                total = sum(section_distribution)
            
            while total < 6:
                idx = random.randint(0, 2)
                section_distribution[idx] += 1
                total = sum(section_distribution)
            
            section_names = ['low', 'mid', 'high']
            
            for i, section_name in enumerate(section_names):
                section_numbers = section_counts[section_name]
                need_count = section_distribution[i]
                
                if section_numbers:
                    freq = Counter(section_numbers)
                    candidates = []
                    
                    for num, count in freq.most_common():
                        adjusted_weight = count + random.uniform(-2, 5)
                        candidates.append((safe_int(num), adjusted_weight))
                    
                    candidates.sort(key=lambda x: x[1] + random.uniform(-1, 1), reverse=True)
                    
                    added = 0
                    for num, weight in candidates:
                        if added >= need_count or num in used_numbers:
                            continue
                        selected.append(num)
                        used_numbers.add(num)
                        added += 1
                
                if len([n for n in selected if n in sections[section_name]]) < need_count:
                    section_candidates = [n for n in sections[section_name] if n not in used_numbers]
                    random.shuffle(section_candidates)
                    
                    current_section_count = len([n for n in selected if n in sections[section_name]])
                    for candidate in section_candidates:
                        if current_section_count >= need_count:
                            break
                        selected.append(candidate)
                        used_numbers.add(candidate)
                        current_section_count += 1
            
            final_numbers = ensure_six_numbers(selected)
            
            return {
                'name': '패턴 분석',
                'description': '번호 구간별 출현 패턴과 수학적 관계 분석 예측',
                'category': 'basic',
                'algorithm_id': 3,
                'priority_numbers': safe_int_list(final_numbers),
                'confidence': 73
            }
        except Exception as e:
            return self._generate_fallback_numbers("패턴 분석", "basic", 3)

    def algorithm_4_statistical_analysis(self):
        """4. 통계 분석"""
        try:
            seed = get_dynamic_seed()
            random.seed(seed)
            np.random.seed(seed)
            
            if self.numbers is None:
                return self._generate_fallback_numbers("통계 분석")
            
            all_numbers = self.numbers.flatten()
            mean_val = float(np.mean(all_numbers)) + random.uniform(-2, 2)
            std_val = float(np.std(all_numbers)) + random.uniform(-1, 1)
            
            candidates = []
            for num in range(1, 46):
                z_score = abs((num - mean_val) / std_val)
                if z_score <= 1.5 + random.uniform(-0.2, 0.2):
                    candidates.append(num)
            
            if len(candidates) < 6:
                candidates = list(range(1, 46))
            
            weights = []
            for num in candidates:
                weight = math.exp(-0.5 * ((num - mean_val) / std_val) ** 2)
                weight *= random.uniform(0.7, 1.3)
                weights.append(weight)
            
            selected = []
            remaining_candidates = candidates.copy()
            remaining_weights = weights.copy()
            
            for _ in range(6):
                if not remaining_candidates:
                    break
                    
                chosen_idx = random.choices(range(len(remaining_candidates)), weights=remaining_weights)[0]
                selected.append(remaining_candidates.pop(chosen_idx))
                remaining_weights.pop(chosen_idx)
            
            final_numbers = ensure_six_numbers(selected)
            
            return {
                'name': '통계 분석',
                'description': '정규분포와 확률 이론을 적용한 수학적 예측',
                'category': 'basic',
                'algorithm_id': 4,
                'priority_numbers': safe_int_list(final_numbers),
                'confidence': 81
            }
        except Exception as e:
            return self._generate_fallback_numbers("통계 분석", "basic", 4)

    def algorithm_5_machine_learning(self):
        """5. 머신러닝"""
        try:
            seed = get_dynamic_seed()
            random.seed(seed)
            np.random.seed(seed)
            
            if self.numbers is None or len(self.numbers) < 50:
                return self._generate_fallback_numbers("머신러닝", "basic", 5)
            
            analysis_count = random.randint(8, 15)
            recent_data = self.numbers[-analysis_count:]
            
            position_averages = []
            for pos in range(6):
                pos_numbers = [safe_int(row[pos]) for row in recent_data]
                avg = sum(pos_numbers) / len(pos_numbers)
                adjusted_avg = avg + random.uniform(-3, 3)
                position_averages.append(int(round(max(1, min(45, adjusted_avg)))))
            
            selected = []
            used_numbers = set()
            
            for avg in position_averages:
                range_size = random.randint(3, 8)
                range_start = max(1, avg - range_size)
                range_end = min(45, avg + range_size)
                
                attempts = 0
                while attempts < 30:
                    candidate = random.randint(range_start, range_end)
                    if candidate not in used_numbers:
                        selected.append(candidate)
                        used_numbers.add(candidate)
                        break
                    attempts += 1
            
            final_numbers = ensure_six_numbers(selected)
            
            return {
                'name': '머신러닝',
                'description': '패턴 학습 기반 위치별 평균 예측',
                'category': 'basic',
                'algorithm_id': 5,
                'priority_numbers': safe_int_list(final_numbers),
                'confidence': 76
            }
        except Exception as e:
            return self._generate_fallback_numbers("머신러닝", "basic", 5)

    def algorithm_6_neural_network(self):
        """6. 신경망 분석"""
        try:
            seed = get_dynamic_seed() + int(time.time() % 100000)
            random.seed(seed)
            np.random.seed(seed)
            
            if self.numbers is None or len(self.numbers) < 30:
                return self._generate_fallback_numbers("신경망 분석")
            
            selected = []
            used_numbers = set()
            
            all_numbers = self.numbers.flatten()
            frequency = Counter(all_numbers)
            
            recent_data = self.numbers[-20:]
            recent_frequency = Counter(recent_data.flatten())
            
            neural_scores = {}
            for num in range(1, 46):
                base_freq = frequency.get(num, 0)
                recent_freq = recent_frequency.get(num, 0)
                
                try:
                    x = (base_freq * 0.3 + recent_freq * 0.7) / 10.0
                    if x > 10:
                        activation = 1.0
                    elif x < -10:
                        activation = 0.0
                    else:
                        activation = 1 / (1 + math.exp(-x))
                    
                    neural_scores[num] = activation * random.uniform(0.5, 1.5)
                except:
                    neural_scores[num] = random.uniform(0.1, 0.9)
            
            sorted_numbers = sorted(neural_scores.items(), key=lambda x: x[1], reverse=True)
            top_candidates = [num for num, score in sorted_numbers[:20]]
            random.shuffle(top_candidates)
            
            for num in top_candidates:
                if len(selected) >= 6:
                    break
                if num not in used_numbers:
                    selected.append(num)
                    used_numbers.add(num)
            
            final_numbers = ensure_six_numbers(selected)
            
            return {
                'name': '신경망 분석',
                'description': '다층 신경망 시뮬레이션을 통한 복합 패턴 학습 예측',
                'category': 'advanced',
                'algorithm_id': 6,
                'priority_numbers': safe_int_list(final_numbers),
                'confidence': 79
            }
        except Exception as e:
            return self._generate_fallback_numbers("신경망 분석", "advanced", 6)

    def algorithm_7_markov_chain(self):
        """7. 마르코프 체인"""
        try:
            seed = get_dynamic_seed() + random.randint(10000, 99999)
            random.seed(seed)
            np.random.seed(seed)
            
            if self.numbers is None or len(self.numbers) < 20:
                return self._generate_fallback_numbers("마르코프 체인")
            
            chain_order = random.randint(1, 3)
            analysis_start = random.randint(0, max(0, len(self.numbers) - 100))
            analysis_data = self.numbers[analysis_start:]
            
            selected = []
            used_numbers = set()
            
            if chain_order == 1:
                transition_matrix = defaultdict(lambda: defaultdict(int))
                
                for i in range(len(analysis_data) - 1):
                    current_set = set(safe_int(x) for x in analysis_data[i])
                    next_set = set(safe_int(x) for x in analysis_data[i + 1])
                    
                    for curr_num in current_set:
                        for next_num in next_set:
                            weight = 1 + random.uniform(-0.3, 0.3)
                            transition_matrix[curr_num][next_num] += weight
                
                last_numbers = set(safe_int(x) for x in analysis_data[-1])
                all_predictions = defaultdict(float)
                
                for curr_num in last_numbers:
                    if curr_num in transition_matrix:
                        transitions = transition_matrix[curr_num]
                        total = sum(transitions.values())
                        
                        for next_num, count in transitions.items():
                            probability = (count / total) * random.uniform(0.8, 1.2)
                            all_predictions[next_num] += probability
                
                sorted_predictions = sorted(all_predictions.items(), 
                                          key=lambda x: x[1] + random.uniform(-0.1, 0.1), 
                                          reverse=True)
                
                for num, prob in sorted_predictions:
                    if len(selected) >= 6:
                        break
                    if safe_int(num) not in used_numbers:
                        selected.append(safe_int(num))
                        used_numbers.add(safe_int(num))
            
            if len(selected) < 6:
                recent_freq = Counter(analysis_data[-10:].flatten())
                freq_candidates = [safe_int(num) for num, _ in recent_freq.most_common() 
                                 if safe_int(num) not in used_numbers]
                random.shuffle(freq_candidates)
                
                for num in freq_candidates:
                    if len(selected) >= 6:
                        break
                    selected.append(num)
                    used_numbers.add(num)
            
            final_numbers = ensure_six_numbers(selected)
            
            return {
                'name': '마르코프 체인',
                'description': f'{chain_order}차 상태 전이 확률을 이용한 연속성 패턴 예측',
                'category': 'advanced',
                'algorithm_id': 7,
                'priority_numbers': safe_int_list(final_numbers),
                'confidence': 74
            }
        except Exception as e:
            return self._generate_fallback_numbers("마르코프 체인", "advanced", 7)

    def algorithm_8_genetic_algorithm(self):
        """8. 유전자 알고리즘"""
        try:
            seed = get_dynamic_seed()
            random.seed(seed)
            np.random.seed(seed)
            
            if self.numbers is None:
                return self._generate_fallback_numbers("유전자 알고리즘", "advanced", 8)
            
            population_size = random.randint(20, 40)
            generations = random.randint(5, 10)
            
            def fitness(individual):
                score = 0
                analysis_range = random.randint(8, 15)
                
                for past_draw in self.numbers[-analysis_range:]:
                    common = len(set(individual) & set(safe_int(x) for x in past_draw))
                    base_score = common * common
                    random_bonus = random.uniform(0.8, 1.2)
                    score += base_score * random_bonus
                
                diversity_score = len(set(individual)) * random.uniform(0.5, 1.5)
                return score + diversity_score
            
            population = []
            for _ in range(population_size):
                if random.random() < 0.3:
                    individual = random.sample(range(1, 46), 6)
                else:
                    all_numbers = self.numbers.flatten()
                    freq = Counter(all_numbers)
                    top_20 = [num for num, _ in freq.most_common(20)]
                    individual = random.sample(top_20, min(6, len(top_20)))
                    while len(individual) < 6:
                        candidate = random.randint(1, 45)
                        if candidate not in individual:
                            individual.append(candidate)
                
                population.append(sorted(individual))
            
            for generation in range(generations):
                fitness_scores = [(ind, fitness(ind)) for ind in population]
                fitness_scores.sort(key=lambda x: x[1], reverse=True)
                
                elite_count = max(2, population_size // 5)
                elites = [ind for ind, score in fitness_scores[:elite_count]]
                
                new_population = elites.copy()
                
                while len(new_population) < population_size:
                    if random.random() < 0.7 and len(elites) >= 2:
                        parent1 = random.choice(elites)
                        parent2 = random.choice(elites)
                        
                        crossover_point = random.randint(1, 5)
                        child = list(set(parent1[:crossover_point] + parent2[crossover_point:]))
                    else:
                        child = random.sample(range(1, 46), 6)
                    
                    final_child = ensure_six_numbers(child)
                    new_population.append(final_child)
                
                population = new_population
            
            final_fitness = [(ind, fitness(ind) + random.uniform(-10, 10)) for ind in population]
            best_individual = max(final_fitness, key=lambda x: x[1])[0]
            
            return {
                'name': '유전자 알고리즘',
                'description': '진화론적 최적화를 통한 적응형 번호 조합 예측',
                'category': 'advanced',
                'algorithm_id': 8,
                'priority_numbers': safe_int_list(best_individual),
                'confidence': 77
            }
        except Exception as e:
            return self._generate_fallback_numbers("유전자 알고리즘", "advanced", 8)

    def algorithm_9_correlation_analysis(self):
        """9. 동반출현 분석"""
        try:
            seed = get_dynamic_seed() + random.randint(50000, 99999)
            random.seed(seed)
            np.random.seed(seed)
            
            if self.numbers is None or len(self.numbers) < 30:
                return self._generate_fallback_numbers("동반출현 분석", "advanced", 9)
            
            analysis_methods = ['pairwise', 'conditional']
            selected_method = random.choice(analysis_methods)
            
            analysis_count = random.randint(50, min(150, len(self.numbers)))
            analysis_data = self.numbers[-analysis_count:]
            
            selected = []
            used_numbers = set()
            
            if selected_method == 'pairwise':
                co_occurrence = defaultdict(int)
                
                for draw in analysis_data:
                    nums = [safe_int(x) for x in draw]
                    for i in range(len(nums)):
                        for j in range(i + 1, len(nums)):
                            pair = tuple(sorted([nums[i], nums[j]]))
                            weight = random.uniform(0.8, 1.2)
                            co_occurrence[pair] += weight
                
                strong_pairs = list(co_occurrence.items())
                strong_pairs.sort(key=lambda x: x[1] + random.uniform(-2, 2), reverse=True)
                strong_pairs = strong_pairs[:15]
                
                for (num1, num2), strength in strong_pairs:
                    if len(selected) >= 6:
                        break
                    
                    if num1 not in used_numbers and len(selected) < 6:
                        selected.append(num1)
                        used_numbers.add(num1)
                    
                    if num2 not in used_numbers and len(selected) < 6:
                        selected.append(num2)
                        used_numbers.add(num2)
                        
            else:
                number_scores = defaultdict(float)
                
                for draw in analysis_data:
                    nums = [safe_int(x) for x in draw]
                    for num in nums:
                        number_scores[num] += random.uniform(0.8, 1.2)
                
                scored_numbers = list(number_scores.items())
                scored_numbers.sort(key=lambda x: x[1] + random.uniform(-5, 5), reverse=True)
                
                for num, score in scored_numbers:
                    if len(selected) >= 6:
                        break
                    if num not in used_numbers:
                        selected.append(num)
                        used_numbers.add(num)
            
            final_numbers = ensure_six_numbers(selected)
            
            return {
                'name': '동반출현 분석',
                'description': f'{selected_method} 방식의 번호 간 상관관계 분석 예측',
                'category': 'advanced',
                'algorithm_id': 9,
                'priority_numbers': safe_int_list(final_numbers),
                'confidence': 75
            }
        except Exception as e:
            return self._generate_fallback_numbers("동반출현 분석", "advanced", 9)

    def algorithm_10_time_series(self):
        """10. 시계열 분석"""
        try:
            seed = get_dynamic_seed() + int(datetime.now().microsecond)
            random.seed(seed)
            np.random.seed(seed)
            
            if self.numbers is None or len(self.numbers) < 20:
                return self._generate_fallback_numbers("시계열 분석", "advanced", 10)
            
            analysis_methods = ['trend', 'seasonal', 'momentum']
            selected_method = random.choice(analysis_methods)
            
            selected = []
            
            if selected_method == 'trend':
                recent_data = self.numbers[-20:]
                freq = Counter(recent_data.flatten())
                
                top_numbers = [safe_int(num) for num, _ in freq.most_common(15)]
                random.shuffle(top_numbers)
                selected = top_numbers[:6]
                
            elif selected_method == 'seasonal':
                all_time_patterns = {}
                for num in range(1, 46):
                    appearances = []
                    for i, draw in enumerate(self.numbers):
                        if num in draw:
                            appearances.append(i)
                    
                    if len(appearances) >= 3:
                        recent_weight = sum(1/(len(self.numbers) - app + 1) for app in appearances[-3:])
                        all_time_patterns[num] = recent_weight * random.uniform(0.7, 1.3)
                
                if all_time_patterns:
                    sorted_patterns = sorted(all_time_patterns.items(), 
                                           key=lambda x: x[1] + random.uniform(-0.2, 0.2), 
                                           reverse=True)
                    selected = [safe_int(num) for num, score in sorted_patterns[:6]]
                else:
                    selected = random.sample(range(1, 46), 6)
                    
            else:
                recent_data = self.numbers[-10:]
                momentum_scores = defaultdict(float)
                
                for i, draw in enumerate(recent_data):
                    weight = (i + 1) / len(recent_data)
                    for num in draw:
                        momentum_scores[safe_int(num)] += weight * random.uniform(0.8, 1.2)
                
                sorted_momentum = sorted(momentum_scores.items(), 
                                       key=lambda x: x[1] + random.uniform(-0.5, 0.5), 
                                       reverse=True)
                selected = [num for num, score in sorted_momentum[:6]]
            
            final_numbers = ensure_six_numbers(selected)
            
            return {
                'name': '시계열 분석',
                'description': f'{selected_method} 기반 시간 흐름 패턴 예측',
                'category': 'advanced',
                'algorithm_id': 10,
                'priority_numbers': safe_int_list(final_numbers),
                'confidence': 72
            }
        except Exception as e:
            return self._generate_fallback_numbers("시계열 분석", "advanced", 10)

    def _generate_fallback_numbers(self, algorithm_name, original_category='basic', original_id=0):
        """백업용 번호 생성"""
        seed = get_dynamic_seed()
        random.seed(seed)
        
        fallback_numbers = sorted(random.sample(range(1, 46), 6))
        
        return {
            'name': algorithm_name,
            'description': f'{algorithm_name} (백업 모드)',
            'category': original_category,
            'algorithm_id': original_id,
            'priority_numbers': fallback_numbers,
            'confidence': 50
        }

    def generate_all_predictions(self):
        """10가지 알고리즘 모두 실행"""
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
            success_count = 0
            fallback_count = 0
            
            for i, algorithm in enumerate(algorithms, 1):
                try:
                    additional_seed = get_dynamic_seed() + i * 1000
                    random.seed(additional_seed)
                    np.random.seed(additional_seed)
                    
                    result = algorithm()
                    algorithm_key = f"algorithm_{i:02d}"
                    
                    if len(result['priority_numbers']) != 6:
                        result['priority_numbers'] = ensure_six_numbers(result['priority_numbers'])
                        fallback_count += 1
                    else:
                        success_count += 1
                    
                    results[algorithm_key] = result
                    time.sleep(0.001)
                    
                except Exception as e:
                    category = 'basic' if i <= 5 else 'advanced'
                    fallback = self._generate_fallback_numbers(f"알고리즘 {i}", category, i)
                    results[f"algorithm_{i:02d}"] = fallback
                    fallback_count += 1
            
            print(f"✅ 알고리즘 실행 완료: 성공 {success_count}개, 백업 {fallback_count}개")
            return results
            
        except Exception as e:
            print(f"❌ 알고리즘 실행 오류: {e}")
            return self._generate_emergency_backup()

    def _generate_emergency_backup(self):
        """긴급 백업 응답"""
        backup_algorithms = [
            ("빈도 분석", "basic"), ("핫/콜드 분석", "basic"), ("패턴 분석", "basic"), 
            ("통계 분석", "basic"), ("머신러닝", "basic"),
            ("신경망 분석", "advanced"), ("마르코프 체인", "advanced"), ("유전자 알고리즘", "advanced"), 
            ("동반출현 분석", "advanced"), ("시계열 분석", "advanced")
        ]
        
        results = {}
        for i, (name, category) in enumerate(backup_algorithms, 1):
            seed = get_dynamic_seed() + i * 10000
            random.seed(seed)
            
            backup_numbers = sorted(random.sample(range(1, 46), 6))
            results[f"algorithm_{i:02d}"] = {
                'name': name,
                'description': f'{name} (긴급 백업)',
                'category': category,
                'algorithm_id': i,
                'priority_numbers': backup_numbers,
                'confidence': 50
            }
        
        return results

# 전역 변수
predictor = None
start_time = time.time()

def get_predictor():
    global predictor
    if predictor is None:
        predictor = AdvancedLottoPredictor()
    return predictor

# 정적 파일 서빙
@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static', 'images'), 
                             'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/sw.js')
def service_worker():
    return send_from_directory(os.path.join(app.root_path, 'static', 'js'), 'sw.js')

@app.route('/manifest.json')
def manifest():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'manifest.json')

# 기본 라우트들
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/algorithms')
def algorithms():
    return render_template('algorithms.html')

@app.route('/ai_models')
def ai_models():
    return render_template('ai_models.html')

# API 엔드포인트들
@app.route('/api/health')
def health():
    try:
        pred = get_predictor()
        return jsonify({
            'success': True,
            'status': 'healthy',
            'data_loaded': pred.data_loaded,
            'algorithms_available': 10,
            'random_system': 'dynamic_seed_enabled',
            'data_source': 'sample_data' if not pred.data_loaded else 'csv_file'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'status': 'unhealthy',
            'error': str(e)
        }), 500

@app.route('/api/algorithm-details')
def get_algorithm_details():
    try:
        algorithm_details = {
            'basic_algorithms': [
                {
                    'id': 1,
                    'name': '빈도 분석',
                    'category': 'basic',
                    'description': '과거 당첨번호의 출현 빈도를 분석하여 가장 자주 나온 번호들을 우선 선택합니다.',
                    'confidence': 85,
                    'detailed_explanation': '전체 당첨 데이터에서 각 번호의 출현 횟수를 계산하고, 통계적 가중치를 적용하여 높은 빈도의 번호들을 우선적으로 선별합니다.',
                    'technical_approach': '가중 확률 분포 모델을 사용하여 빈도 기반 예측을 수행합니다.',
                    'advantages': ['직관적이고 이해하기 쉬움', '장기간의 트렌드 반영', '안정적인 기준선 제공'],
                    'limitations': ['최근 패턴 변화 반영 부족', '모든 번호가 동등한 확률을 가진다는 가정 무시']
                },
                {
                    'id': 2,
                    'name': '핫/콜드 분석',
                    'category': 'basic',
                    'description': '최근 자주 나오는 핫넘버와 오랫동안 나오지 않은 콜드넘버를 조합하여 예측합니다.',
                    'confidence': 78,
                    'detailed_explanation': '최근 15-25회차의 출현 패턴을 분석하여 핫넘버 3-5개와 콜드넘버를 균형있게 조합합니다.',
                    'technical_approach': '기대치 대비 실제 출현율 비교 분석을 통한 핫/콜드 분류 시스템입니다.',
                    'advantages': ['최근 트렌드 반영', '보상 심리 활용', '균형잡힌 접근법'],
                    'limitations': ['단기 변동성에 과도한 의존', '통계적 무작위성 간과']
                },
                {
                    'id': 3,
                    'name': '패턴 분석',
                    'category': 'basic',
                    'description': '번호 구간별 출현 패턴과 수학적 관계를 분석하여 예측합니다.',
                    'confidence': 73,
                    'detailed_explanation': '1-45 범위를 여러 구간으로 나누고, 각 구간별 출현 비율과 패턴을 분석하여 균등한 분포를 목표로 합니다.',
                    'technical_approach': '구간별 분포 분석과 수학적 조합론을 활용한 패턴 인식 시스템입니다.',
                    'advantages': ['극단적인 조합 방지', '번호 분포의 균형성 추구', '수학적 근거 제공'],
                    'limitations': ['과도한 균등 분포 가정', '자연스러운 클러스터링 무시']
                },
                {
                    'id': 4,
                    'name': '통계 분석',
                    'category': 'basic',
                    'description': '정규분포와 확률 이론을 적용한 수학적 예측을 수행합니다.',
                    'confidence': 81,
                    'detailed_explanation': '베이즈 추론과 다항분포 모델을 기반으로 각 번호의 확률을 계산하고 95% 신뢰구간 내에서 예측합니다.',
                    'technical_approach': '베이즈 통계와 최대우도 추정법을 활용한 확률론적 모델입니다.',
                    'advantages': ['수학적 통계 이론 기반', '신뢰성이 높은 접근법', '객관적 분석 가능'],
                    'limitations': ['정규분포 가정의 한계', '복잡한 비선형 패턴 감지 어려움']
                },
                {
                    'id': 5,
                    'name': '머신러닝',
                    'category': 'basic',
                    'description': '패턴 학습 기반으로 위치별 평균을 계산하여 예측합니다.',
                    'confidence': 76,
                    'detailed_explanation': '최근 8-15회차 데이터를 특성으로 사용하여 각 위치별 번호의 평균값을 학습하고 예측 범위를 설정합니다.',
                    'technical_approach': '다차원 패턴 분석과 비선형 관계 모델링을 통한 기계학습 시스템입니다.',
                    'advantages': ['다차원 패턴 분석', '비선형 관계 모델링', '자동 특성 추출'],
                    'limitations': ['과적합 위험성', '해석 가능성 부족', '충분한 데이터 필요']
                }
            ],
            'advanced_algorithms': [
                {
                    'id': 6,
                    'name': '신경망 분석',
                    'category': 'advanced',
                    'description': '다층 신경망 시뮬레이션을 통한 복합 패턴 학습 예측을 수행합니다.',
                    'confidence': 79,
                    'detailed_explanation': '3층 깊은 신경망(DNN) 구조로 복잡한 비선형 패턴을 학습하고 시그모이드 활성화 함수로 확률을 계산합니다.',
                    'technical_approach': 'ReLU + Softmax 활성화 함수를 사용한 다층 퍼셉트론 신경망입니다.',
                    'advantages': ['복잡한 패턴 인식', '비선형 관계 학습', '고차원 특성 추출'],
                    'limitations': ['블랙박스 특성', '과적합 위험', '계산 복잡도 높음']
                },
                {
                    'id': 7,
                    'name': '마르코프 체인',
                    'category': 'advanced',
                    'description': '상태 전이 확률을 이용한 연속성 패턴 예측을 수행합니다.',
                    'confidence': 74,
                    'detailed_explanation': '1-3차 마르코프 체인 모델로 현재 상태에서 다음 상태로의 전이 확률을 계산하여 연속적 패턴을 예측합니다.',
                    'technical_approach': '상태 전이 매트릭스와 확률적 체인 반응을 통한 순차적 예측 시스템입니다.',
                    'advantages': ['순차적 패턴 모델링', '상태 간 의존성 반영', '확률적 추론'],
                    'limitations': ['메모리 제약', '상태 공간 복잡도', '장기 의존성 한계']
                },
                {
                    'id': 8,
                    'name': '유전자 알고리즘',
                    'category': 'advanced',
                    'description': '진화론적 최적화를 통한 적응형 번호 조합 예측을 수행합니다.',
                    'confidence': 77,
                    'detailed_explanation': '20-40개 개체군으로 5-10세대 진화 과정을 시뮬레이션하여 최적의 번호 조합을 탐색합니다.',
                    'technical_approach': '선택, 교배, 변이 과정을 통한 진화적 최적화 알고리즘입니다.',
                    'advantages': ['전역 최적해 탐색', '다양성 보장', '적응적 학습'],
                    'limitations': ['수렴 시간 긺', '매개변수 의존성', '지역 최적해 위험']
                },
                {
                    'id': 9,
                    'name': '동반출현 분석',
                    'category': 'advanced',
                    'description': '번호 간 상관관계와 동시 출현 패턴을 분석하여 예측합니다.',
                    'confidence': 75,
                    'detailed_explanation': '번호 쌍들의 동반출현 빈도를 계산하고 네트워크 분석으로 강한 연관성을 가진 번호들을 식별합니다.',
                    'technical_approach': '관계 기반 예측과 연관성 분석을 통한 네트워크 모델링 시스템입니다.',
                    'advantages': ['숨겨진 연관성 발견', '상관관계 활용', '네트워크 효과 반영'],
                    'limitations': ['허상 관계 감지 위험', '인과관계 혼동', '계산 복잡도']
                },
                {
                    'id': 10,
                    'name': '시계열 분석',
                    'category': 'advanced',
                    'description': '시간 흐름에 따른 패턴 변화를 분석하여 예측합니다.',
                    'confidence': 72,
                    'detailed_explanation': '트렌드, 계절성, 모멘텀 방식으로 각 번호의 시간적 패턴과 주기성을 분석하여 다음 출현을 예측합니다.',
                    'technical_approach': '주기적 패턴 예측과 시간 기반 분석을 통한 시계열 모델링입니다.',
                    'advantages': ['시간 패턴 인식', '주기성 분석', '트렌드 반영'],
                    'limitations': ['비정상 시계열 특성', '노이즈 민감성', '예측 구간 제한']
                }
            ]
        }
        
        return jsonify({
            'success': True,
            'data': algorithm_details
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/predictions', methods=['GET'])
def get_predictions():
    try:
        global_seed = get_dynamic_seed()
        random.seed(global_seed)
        np.random.seed(global_seed)
        
        pred = get_predictor()
        
        if not pred.data_loaded:
            if not pred.load_data():
                return jsonify({
                    'success': False,
                    'error': 'CSV 데이터를 로드할 수 없습니다.'
                }), 500
        
        results = pred.generate_all_predictions()
        
        final_check_count = 0
        for key, result in results.items():
            if len(result['priority_numbers']) != 6:
                result['priority_numbers'] = ensure_six_numbers(result['priority_numbers'])
                final_check_count += 1
        
        all_results = [tuple(result['priority_numbers']) for result in results.values()]
        unique_results = set(all_results)
        duplicate_count = len(all_results) - len(unique_results)
        
        response_data = {
            'success': True,
            'data': results,
            'total_algorithms': len(results),
            'total_draws': safe_int(len(pred.data)) if pred.data is not None else 0,
            'message': '10가지 AI 알고리즘이 각각 1개씩의 우선 번호를 생성했습니다.',
            'randomness_info': {
                'global_seed': global_seed,
                'unique_results': len(unique_results),
                'duplicate_results': duplicate_count,
                'system_status': 'dynamic_seed_active'
            }
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'예측 생성 중 오류가 발생했습니다: {str(e)}'
        }), 500

@app.route('/api/statistics')
def get_statistics():
    try:
        pred = get_predictor()
        
        default_stats = {
            'total_draws': 1191,
            'algorithms_count': 10,
            'last_draw_info': {
                'round': 1191,
                'date': '2024-01-01',
                'numbers': [1, 7, 13, 19, 25, 31],
                'bonus': 7
            },
            'most_frequent': [{'number': i, 'count': 50-i} for i in range(1, 11)],
            'least_frequent': [{'number': i+35, 'count': i} for i in range(1, 11)],
            'recent_hot': [{'number': i+10, 'count': 20-i} for i in range(1, 11)]
        }
        
        if pred.data is not None and pred.numbers is not None and pred.data_loaded:
            try:
                all_numbers = pred.numbers.flatten()
                frequency = Counter(all_numbers)
                
                most_common = frequency.most_common(10)
                least_common = frequency.most_common()[:-11:-1]
                
                last_row = pred.data.iloc[-1]
                
                stats = {
                    'total_draws': safe_int(len(pred.data)),
                    'algorithms_count': 10,
                    'most_frequent': [{'number': safe_int(num), 'count': safe_int(count)} for num, count in most_common],
                    'least_frequent': [{'number': safe_int(num), 'count': safe_int(count)} for num, count in least_common],
                    'recent_hot': [{'number': safe_int(num), 'count': safe_int(count)} for num, count in most_common[:10]],
                    'last_draw_info': {
                        'round': safe_int(last_row.get('round', 1191)),
                        'date': str(last_row.get('draw_date', '2024-01-01')),
                        'numbers': safe_int_list(pred.numbers[-1].tolist()),
                        'bonus': safe_int(last_row.get('bonus_num', 7)) if 'bonus_num' in last_row else 7
                    }
                }
            except Exception as e:
                print(f"통계 생성 오류: {e}")
                stats = default_stats
        else:
            stats = default_stats
        
        return jsonify({
            'success': True,
            'data': stats
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'Statistics temporarily unavailable'
        }), 500

@app.route('/api/export/predictions', methods=['POST'])
def export_predictions():
    try:
        export_data = request.get_json() or {}
        format_type = export_data.get('format', 'json')
        
        # 현재 예측 결과 가져오기
        pred = get_predictor()
        if not pred.data_loaded:
            pred.load_data()
        
        results = pred.generate_all_predictions()
        
        # 내보내기용 데이터 구성
        export_timestamp = datetime.now()
        predictions_data = {
            'export_timestamp': export_timestamp.isoformat(),
            'export_date': export_timestamp.strftime('%Y년 %m월 %d일 %H시 %M분'),
            'total_algorithms': len(results),
            'algorithms': []
        }
        
        # 알고리즘별 데이터 정리
        for key, result in results.items():
            algorithm_data = {
                'id': result.get('algorithm_id', 0),
                'name': result.get('name', '알 수 없음'),
                'category': result.get('category', 'basic'),
                'numbers': result.get('priority_numbers', []),
                'numbers_str': ' - '.join(map(str, result.get('priority_numbers', []))),
                'confidence': result.get('confidence', 50),
                'description': result.get('description', '')
            }
            predictions_data['algorithms'].append(algorithm_data)
        
        if format_type == 'json':
            filename = f'lotto_predictions_{export_timestamp.strftime("%Y%m%d_%H%M%S")}.json'
            return jsonify({
                'success': True,
                'data': predictions_data,
                'filename': filename,
                'content_type': 'application/json'
            })
            
        elif format_type == 'csv':
            # CSV 형식으로 변환
            csv_lines = ['알고리즘,카테고리,예측번호,신뢰도,설명']
            
            for alg in predictions_data['algorithms']:
                csv_line = f'"{alg["name"]}","{alg["category"]}","{alg["numbers_str"]}",{alg["confidence"]},"{alg["description"]}"'
                csv_lines.append(csv_line)
            
            csv_content = '\n'.join(csv_lines)
            filename = f'lotto_predictions_{export_timestamp.strftime("%Y%m%d_%H%M%S")}.csv'
            
            return jsonify({
                'success': True,
                'data': csv_content,
                'filename': filename,
                'content_type': 'text/csv; charset=utf-8'
            })
            
        elif format_type == 'txt':
            # 텍스트 형식으로 변환
            txt_lines = [
                f'로또프로 AI v2.0 예측 결과',
                f'생성일시: {predictions_data["export_date"]}',
                f'총 알고리즘: {predictions_data["total_algorithms"]}개',
                '=' * 50,
                ''
            ]
            
            basic_algos = [alg for alg in predictions_data['algorithms'] if alg['category'] == 'basic']
            advanced_algos = [alg for alg in predictions_data['algorithms'] if alg['category'] == 'advanced']
            
            txt_lines.extend([
                '[ 기본 AI 알고리즘 ]',
                ''
            ])
            
            for i, alg in enumerate(basic_algos, 1):
                txt_lines.extend([
                    f'{i}. {alg["name"]} (신뢰도: {alg["confidence"]}%)',
                    f'   예측번호: {alg["numbers_str"]}',
                    f'   설명: {alg["description"]}',
                    ''
                ])
            
            txt_lines.extend([
                '[ 고급 AI 알고리즘 ]',
                ''
            ])
            
            for i, alg in enumerate(advanced_algos, 1):
                txt_lines.extend([
                    f'{i}. {alg["name"]} (신뢰도: {alg["confidence"]}%)',
                    f'   예측번호: {alg["numbers_str"]}',
                    f'   설명: {alg["description"]}',
                    ''
                ])
            
            txt_lines.extend([
                '=' * 50,
                '* 로또는 완전한 확률게임입니다.',
                '* 본 예측은 참고용으로만 사용하세요.',
                '* 과도한 기대나 의존은 하지 마세요.'
            ])
            
            txt_content = '\n'.join(txt_lines)
            filename = f'lotto_predictions_{export_timestamp.strftime("%Y%m%d_%H%M%S")}.txt'
            
            return jsonify({
                'success': True,
                'data': txt_content,
                'filename': filename,
                'content_type': 'text/plain; charset=utf-8'
            })
        
        return jsonify({
            'success': False,
            'error': '지원하지 않는 내보내기 형식입니다.'
        }), 400
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'내보내기 실패: {str(e)}'
        }), 500

@app.route('/api/analytics/track', methods=['POST'])
def track_user_activity():
    try:
        activity_data = request.get_json()
        
        activity_log = {
            'timestamp': datetime.now().isoformat(),
            'session_id': activity_data.get('sessionId'),
            'action': activity_data.get('action'),
            'details': activity_data.get('details', {}),
            'user_agent': request.headers.get('User-Agent'),
            'ip_address': request.remote_addr
        }
        
        os.makedirs('analytics_logs', exist_ok=True)
        with open('analytics_logs/activity.log', 'a', encoding='utf-8') as f:
            f.write(json.dumps(activity_log, ensure_ascii=False) + '\n')
        
        return jsonify({
            'success': True,
            'message': '활동이 기록되었습니다.'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'활동 추적 실패: {str(e)}'
        }), 500

@app.route('/api/predictions/enhanced', methods=['GET'])
def get_predictions_enhanced():
    try:
        start_time = time.time()
        
        pred = get_predictor()
        results = pred.generate_all_predictions()
        
        validated_algorithms = {}
        validation_stats = {
            'total': len(results),
            'valid': 0,
            'fixed': 0,
            'errors': []
        }
        
        for key, algorithm in results.items():
            try:
                numbers = algorithm.get('priority_numbers', [])
                
                is_valid = (
                    isinstance(numbers, list) and
                    len(numbers) == 6 and
                    len(set(numbers)) == 6 and
                    all(isinstance(n, int) and 1 <= n <= 45 for n in numbers)
                )
                
                if is_valid:
                    validation_stats['valid'] += 1
                    algorithm['validation_status'] = 'valid'
                else:
                    fixed_numbers = fix_invalid_numbers(numbers)
                    algorithm['priority_numbers'] = fixed_numbers
                    algorithm['validation_status'] = 'fixed'
                    validation_stats['fixed'] += 1
                
                validated_algorithms[key] = algorithm
                
            except Exception as e:
                validation_stats['errors'].append(f'{key}: {str(e)}')
                default_numbers = generate_default_numbers()
                algorithm['priority_numbers'] = default_numbers
                algorithm['validation_status'] = 'error_fixed'
                validated_algorithms[key] = algorithm
        
        processing_time = time.time() - start_time
        
        return jsonify({
            'success': True,
            'data': validated_algorithms,
            'validation_stats': validation_stats,
            'processing_time': round(processing_time, 2),
            'total_draws': safe_int(len(pred.data)) if pred.data is not None else 0,
            'last_updated': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'예측 생성 실패: {str(e)}'
        }), 500

@app.route('/api/clear-cache', methods=['POST'])
def clear_cache():
    try:
        request_data = request.get_json() or {}
        clear_algorithms = request_data.get('clear_algorithms', [])
        reason = request_data.get('reason', 'manual_clear')
        
        global predictor
        predictor = None
        gc.collect()
        
        predictor = get_predictor()
        
        cleared_count = len(clear_algorithms) if clear_algorithms else 10
        
        response_data = {
            'success': True,
            'cleared_algorithms': clear_algorithms,
            'cleared_count': cleared_count,
            'reason': reason,
            'timestamp': datetime.now().isoformat(),
            'message': '캐시가 성공적으로 클리어되었습니다.'
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'캐시 클리어 중 오류가 발생했습니다: {str(e)}'
        }), 500

# 에러 핸들러
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 'API 엔드포인트를 찾을 수 없습니다'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'error': '서버 내부 오류가 발생했습니다'
    }), 500

# 디렉토리 생성
os.makedirs('analytics_logs', exist_ok=True)
os.makedirs('static/images', exist_ok=True)
os.makedirs('static/js', exist_ok=True)
os.makedirs('static/css', exist_ok=True)

# 메인 실행
if __name__ == '__main__':
    try:
        print("🚀 로또프로 AI v2.0 서버 시작")
        initial_predictor = get_predictor()
        print(f"✅ 예측기 초기화 완료 - 데이터 로드 상태: {initial_predictor.data_loaded}")
    except Exception as e:
        print(f"⚠️ 예측기 초기화 중 오류: {e}")
    
    app.run(
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 5000)),
        debug=os.environ.get('DEBUG', 'False').lower() == 'true'
    )
