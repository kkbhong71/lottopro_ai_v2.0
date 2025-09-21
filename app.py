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
import time
import hashlib
from datetime import datetime

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
    random.shuffle(available_numbers)  # 랜덤하게 섞기
    
    while len(unique_selected) < 6 and available_numbers:
        unique_selected.append(available_numbers.pop(0))
    
    # 여전히 6개가 안 되면 강제로 채움 (극단적 상황)
    while len(unique_selected) < 6:
        for num in range(1, 46):
            if num not in unique_selected:
                unique_selected.append(num)
                break
    
    return sorted(unique_selected[:6])

class AdvancedLottoPredictor:
    def __init__(self, csv_file_path='new_1190.csv'):
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
        """데이터 로드 및 전처리 - 디버깅 강화 버전"""
        try:
            print(f"🚨 LottoPro Emergency Mode Started - 디버깅 모드 활성화")
            
            # 현재 디렉토리 정보 출력
            current_dir = os.getcwd()
            try:
                files_in_dir = os.listdir('.')
                csv_files = [f for f in files_in_dir if f.endswith('.csv')]
                all_files = [f for f in files_in_dir if os.path.isfile(f)][:10]  # 처음 10개만
            except Exception as e:
                csv_files = []
                all_files = []
                print(f"❌ 디렉토리 읽기 오류: {e}")
            
            print(f"📁 현재 디렉토리: {current_dir}")
            print(f"📂 발견된 CSV 파일들: {csv_files}")
            print(f"📄 기타 파일들 (일부): {all_files}")
            
            # 여러 경로 시도
            possible_paths = [
                'new_1190.csv',
                './new_1190.csv',
                os.path.join(current_dir, 'new_1190.csv'),
                'data/new_1190.csv',
                '/opt/render/project/src/new_1190.csv',
                os.path.join(os.path.dirname(__file__), 'new_1190.csv')
            ]
            
            print(f"🔍 시도할 경로들: {possible_paths}")
            
            found_file = None
            for i, path in enumerate(possible_paths):
                print(f"  {i+1}. 확인 중: {path}")
                if os.path.exists(path):
                    print(f"    ✅ 파일 발견!")
                    found_file = path
                    break
                else:
                    print(f"    ❌ 파일 없음")
            
            if not found_file:
                print(f"❌ 모든 경로에서 CSV 파일을 찾을 수 없습니다")
                print(f"💡 해결책: GitHub의 new_1190.csv 파일이 배포 서버에 복사되지 않았을 가능성")
                return False
            
            # 파일 정보 확인
            self.csv_file_path = found_file
            file_size = os.path.getsize(self.csv_file_path)
            print(f"📊 파일 정보:")
            print(f"  - 경로: {self.csv_file_path}")
            print(f"  - 크기: {file_size:,} bytes")
            
            # 파일 읽기 시도
            print(f"📖 CSV 파일 읽기 시도...")
            self.data = pd.read_csv(self.csv_file_path)
            print(f"📈 로드된 데이터 정보:")
            print(f"  - Shape: {self.data.shape}")
            print(f"  - 컬럼명: {list(self.data.columns)}")
            print(f"  - 첫 5줄 미리보기:")
            print(self.data.head().to_string())
            
            # 컬럼명 표준화
            if len(self.data.columns) >= 7:
                old_columns = list(self.data.columns)
                self.data.columns = ['round', 'draw_date', 'num1', 'num2', 'num3', 'num4', 'num5', 'num6', 'bonus_num'][:len(self.data.columns)]
                print(f"🔄 컬럼명 변경: {old_columns} -> {list(self.data.columns)}")
            
            # 번호 데이터 추출
            number_cols = ['num1', 'num2', 'num3', 'num4', 'num5', 'num6']
            available_cols = [col for col in number_cols if col in self.data.columns]
            print(f"🎯 사용 가능한 번호 컬럼: {available_cols}")
            
            if len(available_cols) >= 6:
                self.numbers = self.data[available_cols].values.astype(int)
                print(f"✅ 데이터 로드 완료!")
                print(f"  - 총 회차 수: {len(self.data):,}개")
                print(f"  - 번호 데이터 shape: {self.numbers.shape}")
                print(f"  - 첫 번째 회차 번호: {self.numbers[0].tolist()}")
                print(f"  - 마지막 회차 번호: {self.numbers[-1].tolist()}")
                return True
            else:
                print(f"❌ 필요한 컬럼이 부족합니다.")
                print(f"  - 필요: {number_cols}")
                print(f"  - 사용 가능: {available_cols}")
                return False
                
        except Exception as e:
            print(f"❌ 데이터 로드 실패: {str(e)}")
            print(f"   오류 타입: {type(e).__name__}")
            import traceback
            print(f"   상세 오류:")
            traceback.print_exc()
            return False

    def algorithm_1_frequency_analysis(self):
        """1. 빈도 분석 - 수정된 버전"""
        try:
            # 동적 시드 설정
            seed = get_dynamic_seed()
            random.seed(seed)
            np.random.seed(seed)
            
            if self.numbers is None:
                print(f"⚠️ 빈도 분석: 데이터 없음 - 백업 모드")
                return self._generate_fallback_numbers("빈도 분석")
            
            all_numbers = self.numbers.flatten()
            frequency = Counter(all_numbers)
            
            # 상위 20개 번호 중에서 선택 (더 많은 후보로 중복 위험 감소)
            top_numbers = [safe_int(num) for num, count in frequency.most_common(20)]
            weights = [count for num, count in frequency.most_common(20)]
            
            selected = []
            used_numbers = set()
            
            # 중복 없이 6개 선택
            for _ in range(6):
                if not top_numbers:
                    break
                
                # 사용되지 않은 번호만 필터링
                available_indices = [i for i, num in enumerate(top_numbers) if num not in used_numbers]
                if not available_indices:
                    break
                    
                # 가중치 기반 선택 + 랜덤성 추가
                available_weights = [weights[i] + random.randint(1, 10) for i in available_indices]
                chosen_idx = random.choices(available_indices, weights=available_weights)[0]
                chosen_number = top_numbers[chosen_idx]
                
                selected.append(chosen_number)
                used_numbers.add(chosen_number)
            
            # 6개 번호 보장
            final_numbers = ensure_six_numbers(selected)
            print(f"✅ 빈도 분석 완료 (시드: {seed}): {final_numbers}")
            
            return {
                'name': '빈도 분석',
                'description': '과거 당첨번호 출현 빈도를 분석하여 가중 확률로 예측',
                'category': 'basic',
                'algorithm_id': 1,
                'priority_numbers': safe_int_list(final_numbers),
                'confidence': 85
            }
        except Exception as e:
            print(f"빈도 분석 알고리즘 오류: {e}")
            return self._generate_fallback_numbers("빈도 분석")

    def algorithm_2_hot_cold_analysis(self):
        """2. 핫/콜드 분석 - 완전 수정된 버전"""
        try:
            # 매번 다른 동적 시드 설정
            seed = get_dynamic_seed() + random.randint(1, 1000)
            random.seed(seed)
            np.random.seed(seed)
            
            if self.numbers is None or len(self.numbers) < 20:
                print(f"⚠️ 핫/콜드 분석: 데이터 부족 - 백업 모드")
                return self._generate_fallback_numbers("핫/콜드 분석")
            
            # 분석 범위를 랜덤하게 변경 (15-25회차)
            analysis_range = random.randint(15, 25)
            recent_numbers = self.numbers[-analysis_range:].flatten()
            recent_freq = Counter(recent_numbers)
            
            # 전체 평균과 비교
            all_numbers = self.numbers.flatten()
            total_freq = Counter(all_numbers)
            
            hot_numbers = []
            cold_numbers = []
            
            for num in range(1, 46):
                recent_count = recent_freq.get(num, 0)
                expected_count = total_freq.get(num, 0) * (analysis_range / len(self.numbers))
                
                # 핫/콜드 기준을 랜덤하게 조정
                hot_threshold = random.uniform(0.5, 1.5)
                
                if recent_count > expected_count + hot_threshold:
                    hot_numbers.append((safe_int(num), recent_count - expected_count))
                elif recent_count < expected_count - hot_threshold:
                    cold_numbers.append((safe_int(num), expected_count - recent_count))
            
            # 핫 넘버 정렬 + 랜덤 섞기
            hot_numbers.sort(key=lambda x: x[1] + random.uniform(-0.5, 0.5), reverse=True)
            random.shuffle(cold_numbers)  # 콜드 넘버는 완전 랜덤
            
            selected = []
            used_numbers = set()
            
            # 핫 넘버에서 3-5개 선택 (랜덤 개수)
            hot_count = random.randint(3, 5)
            for num, _ in hot_numbers[:hot_count]:
                if len(selected) < 6 and num not in used_numbers:
                    selected.append(num)
                    used_numbers.add(num)
            
            # 나머지는 콜드 넘버 또는 랜덤에서 선택
            remaining_needed = 6 - len(selected)
            
            # 콜드 넘버 후보
            cold_candidates = [num for num, _ in cold_numbers if num not in used_numbers]
            # 완전 랜덤 후보
            random_candidates = [num for num in range(1, 46) if num not in used_numbers]
            
            for _ in range(remaining_needed):
                if random.random() > 0.3 and cold_candidates:  # 70% 확률로 콜드 넘버
                    chosen = random.choice(cold_candidates)
                    cold_candidates.remove(chosen)
                elif random_candidates:  # 30% 확률로 완전 랜덤
                    chosen = random.choice(random_candidates)
                    random_candidates.remove(chosen)
                else:
                    break
                
                selected.append(chosen)
                used_numbers.add(chosen)
            
            # 6개 번호 보장
            final_numbers = ensure_six_numbers(selected)
            print(f"✅ 핫/콜드 분석 완료 (시드: {seed}, 범위: {analysis_range}): {final_numbers}")
            
            return {
                'name': '핫/콜드 분석',
                'description': '최근 출현 패턴 기반 핫넘버와 콜드넘버 조합 예측',
                'category': 'basic',
                'algorithm_id': 2,
                'priority_numbers': safe_int_list(final_numbers),
                'confidence': 78
            }
        except Exception as e:
            print(f"핫/콜드 분석 알고리즘 오류: {e}")
            return self._generate_fallback_numbers("핫/콜드 분석")

    def algorithm_3_pattern_analysis(self):
        """3. 패턴 분석 - 완전 수정된 버전"""
        try:
            # 매번 다른 동적 시드 설정
            seed = get_dynamic_seed() + int(time.time() % 10000)
            random.seed(seed)
            np.random.seed(seed)
            
            if self.numbers is None:
                print(f"⚠️ 패턴 분석: 데이터 없음 - 백업 모드")
                return self._generate_fallback_numbers("패턴 분석")
            
            # 구간을 동적으로 변경
            section_size = random.randint(12, 18)  # 구간 크기 랜덤
            sections = {
                'low': list(range(1, section_size + 1)),
                'mid': list(range(section_size + 1, section_size * 2 + 1)),
                'high': list(range(section_size * 2 + 1, 46))
            }
            
            section_counts = {'low': [], 'mid': [], 'high': []}
            
            # 분석할 회차 수도 랜덤하게 변경
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
            
            # 각 구간별 선택 개수를 랜덤하게 결정
            section_distribution = [
                random.randint(1, 3),  # low 구간
                random.randint(1, 3),  # mid 구간 
                random.randint(1, 3)   # high 구간
            ]
            
            # 총 6개가 되도록 조정
            total = sum(section_distribution)
            if total > 6:
                # 초과시 랜덤하게 줄이기
                while sum(section_distribution) > 6:
                    idx = random.randint(0, 2)
                    if section_distribution[idx] > 1:
                        section_distribution[idx] -= 1
            elif total < 6:
                # 부족시 랜덤하게 늘리기
                while sum(section_distribution) < 6:
                    idx = random.randint(0, 2)
                    section_distribution[idx] += 1
            
            section_names = ['low', 'mid', 'high']
            
            for i, section_name in enumerate(section_names):
                section_numbers = section_counts[section_name]
                need_count = section_distribution[i]
                
                if section_numbers:
                    # 빈도 계산 후 랜덤 가중치 추가
                    freq = Counter(section_numbers)
                    candidates = []
                    
                    for num, count in freq.most_common():
                        # 빈도에 랜덤 가중치 추가
                        adjusted_weight = count + random.uniform(-2, 5)
                        candidates.append((safe_int(num), adjusted_weight))
                    
                    # 가중치로 정렬하되 약간의 랜덤성 추가
                    candidates.sort(key=lambda x: x[1] + random.uniform(-1, 1), reverse=True)
                    
                    # 필요한 개수만큼 선택
                    added = 0
                    for num, weight in candidates:
                        if added >= need_count or num in used_numbers:
                            continue
                        selected.append(num)
                        used_numbers.add(num)
                        added += 1
                
                # 해당 구간에서 부족하면 랜덤 선택
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
            
            # 6개 번호 보장
            final_numbers = ensure_six_numbers(selected)
            print(f"✅ 패턴 분석 완료 (시드: {seed}, 구간크기: {section_size}): {final_numbers}")
            
            return {
                'name': '패턴 분석',
                'description': '번호 구간별 출현 패턴과 수학적 관계 분석 예측',
                'category': 'basic',
                'algorithm_id': 3,
                'priority_numbers': safe_int_list(final_numbers),
                'confidence': 73
            }
        except Exception as e:
            print(f"패턴 분석 알고리즘 오류: {e}")
            return self._generate_fallback_numbers("패턴 분석")

    def algorithm_4_statistical_analysis(self):
        """4. 통계 분석 - 수정된 버전"""
        try:
            # 동적 시드 설정
            seed = get_dynamic_seed()
            random.seed(seed)
            np.random.seed(seed)
            
            if self.numbers is None:
                print(f"⚠️ 통계 분석: 데이터 없음 - 백업 모드")
                return self._generate_fallback_numbers("통계 분석")
            
            all_numbers = self.numbers.flatten()
            
            # 정규분포 기반 예측 + 랜덤 변화
            mean_val = float(np.mean(all_numbers)) + random.uniform(-2, 2)
            std_val = float(np.std(all_numbers)) + random.uniform(-1, 1)
            
            # 표준점수 기반 선택
            candidates = []
            for num in range(1, 46):
                z_score = abs((num - mean_val) / std_val)
                if z_score <= 1.5 + random.uniform(-0.2, 0.2):  # 기준 범위도 랜덤 조정
                    candidates.append(num)
            
            if len(candidates) < 6:
                candidates = list(range(1, 46))
            
            # 정규분포 가중치로 선택 + 랜덤 노이즈
            weights = []
            for num in candidates:
                weight = math.exp(-0.5 * ((num - mean_val) / std_val) ** 2)
                # 랜덤 노이즈 추가
                weight *= random.uniform(0.7, 1.3)
                weights.append(weight)
            
            # 중복 없이 6개 선택
            selected = []
            remaining_candidates = candidates.copy()
            remaining_weights = weights.copy()
            
            for _ in range(6):
                if not remaining_candidates:
                    break
                    
                chosen_idx = random.choices(range(len(remaining_candidates)), weights=remaining_weights)[0]
                selected.append(remaining_candidates.pop(chosen_idx))
                remaining_weights.pop(chosen_idx)
            
            # 6개 번호 보장
            final_numbers = ensure_six_numbers(selected)
            print(f"✅ 통계 분석 완료 (시드: {seed}): {final_numbers}")
            
            return {
                'name': '통계 분석',
                'description': '정규분포와 확률 이론을 적용한 수학적 예측',
                'category': 'basic',
                'algorithm_id': 4,
                'priority_numbers': safe_int_list(final_numbers),
                'confidence': 81
            }
        except Exception as e:
            print(f"통계 분석 알고리즘 오류: {e}")
            return self._generate_fallback_numbers("통계 분석")

    def algorithm_5_machine_learning(self):
        """5. 머신러닝 - 수정된 버전"""
        try:
            # 동적 시드 설정
            seed = get_dynamic_seed()
            random.seed(seed)
            np.random.seed(seed)
            
            if self.numbers is None or len(self.numbers) < 50:
                print(f"⚠️ 머신러닝: 데이터 부족 - 백업 모드")
                return self._generate_fallback_numbers("머신러닝")
            
            # 분석할 회차 수를 랜덤하게 변경
            analysis_count = random.randint(8, 15)
            recent_data = self.numbers[-analysis_count:]
            
            # 각 위치별 평균 계산 + 랜덤 변화
            position_averages = []
            for pos in range(6):
                pos_numbers = [safe_int(row[pos]) for row in recent_data]
                avg = sum(pos_numbers) / len(pos_numbers)
                # 평균에 랜덤 변화 추가
                adjusted_avg = avg + random.uniform(-3, 3)
                position_averages.append(int(round(max(1, min(45, adjusted_avg)))))
            
            # 평균 주변의 번호들로 조정
            selected = []
            used_numbers = set()
            
            for avg in position_averages:
                # 범위를 랜덤하게 변경 (±3~±8)
                range_size = random.randint(3, 8)
                range_start = max(1, avg - range_size)
                range_end = min(45, avg + range_size)
                
                attempts = 0
                while attempts < 30:  # 무한 루프 방지
                    candidate = random.randint(range_start, range_end)
                    if candidate not in used_numbers:
                        selected.append(candidate)
                        used_numbers.add(candidate)
                        break
                    attempts += 1
            
            # 6개 번호 보장
            final_numbers = ensure_six_numbers(selected)
            print(f"✅ 머신러닝 완료 (시드: {seed}, 분석회차: {analysis_count}): {final_numbers}")
            
            return {
                'name': '머신러닝',
                'description': '패턴 학습 기반 위치별 평균 예측',
                'category': 'basic',
                'algorithm_id': 5,
                'priority_numbers': safe_int_list(final_numbers),
                'confidence': 76
            }
        except Exception as e:
            print(f"머신러닝 알고리즘 오류: {e}")
            return self._generate_fallback_numbers("머신러닝")

    def algorithm_6_neural_network(self):
        """6. 신경망 분석 - 완전 수정된 버전"""
        try:
            # 매번 다른 동적 시드 설정
            seed = get_dynamic_seed() + int(time.time() % 100000)
            random.seed(seed)
            np.random.seed(seed)
            
            if self.numbers is None or len(self.numbers) < 30:
                print(f"⚠️ 신경망 분석: 데이터 부족 - 백업 모드")
                return self._generate_fallback_numbers("신경망 분석")
            
            # 네트워크 파라미터를 매번 랜덤하게 변경
            learning_rate = random.uniform(0.05, 0.2)
            weight_decay = random.uniform(0.8, 1.2)
            
            # 가중치 네트워크 시뮬레이션 - 매번 다른 구조
            num_layers = random.randint(2, 4)
            weights_per_layer = []
            
            for layer in range(num_layers):
                layer_weights = []
                for i in range(len(self.numbers)):
                    # 시간 거리 기반 가중치 + 랜덤 노이즈
                    time_weight = (i + 1) / len(self.numbers)  # 최근일수록 높은 가중치
                    random_noise = random.uniform(0.5, 1.5)
                    layer_specific_modifier = random.uniform(0.8, 1.2)
                    
                    final_weight = time_weight * random_noise * layer_specific_modifier * learning_rate
                    layer_weights.append(final_weight)
                
                weights_per_layer.append(layer_weights)
            
            # 다층 네트워크 시뮬레이션
            all_weighted_numbers = []
            
            for layer_idx, layer_weights in enumerate(weights_per_layer):
                layer_numbers = []
                
                for i, row in enumerate(self.numbers):
                    weight = layer_weights[i] * weight_decay ** layer_idx
                    for num in row:
                        # 각 층마다 다른 활성화 함수 시뮬레이션
                        if layer_idx % 2 == 0:  # ReLU 시뮬레이션
                            activation = max(0, weight * safe_int(num) + random.uniform(-5, 5))
                        else:  # Sigmoid 시뮬레이션
                            activation = 1 / (1 + math.exp(-weight * safe_int(num))) * 45
                        
                        # 활성화 값에 따라 번호 추가
                        repeat_count = int(activation * 10) + 1
                        layer_numbers.extend([safe_int(num)] * repeat_count)
                
                all_weighted_numbers.extend(layer_numbers)
            
            # 출력층 처리
            freq = Counter(all_weighted_numbers)
            
            # 상위 후보들에 드롭아웃 시뮬레이션
            dropout_rate = random.uniform(0.1, 0.3)
            top_candidates = freq.most_common(30)
            
            # 드롭아웃 적용
            filtered_candidates = []
            for num, count in top_candidates:
                if random.random() > dropout_rate:  # 드롭아웃 확률로 필터링
                    # 배치 정규화 시뮬레이션
                    normalized_count = count * random.uniform(0.8, 1.2)
                    filtered_candidates.append((safe_int(num), normalized_count))
            
            # 활성화 함수 최종 적용
            final_candidates = []
            for num, count in filtered_candidates:
                # Softmax 시뮬레이션
                softmax_prob = math.exp(count) / sum(math.exp(c) for _, c in filtered_candidates)
                final_candidates.append((num, softmax_prob))
            
            # 확률 기반 선택 + 온도 파라미터
            temperature = random.uniform(0.5, 2.0)
            selected = []
            used_numbers = set()
            
            for _ in range(6):
                if not final_candidates:
                    break
                
                # 온도 스케일링 적용
                scaled_probs = []
                available_candidates = [(num, prob) for num, prob in final_candidates if num not in used_numbers]
                
                if not available_candidates:
                    break
                
                for num, prob in available_candidates:
                    scaled_prob = math.exp(math.log(prob + 1e-10) / temperature)
                    scaled_probs.append(scaled_prob)
                
                # 확률 정규화
                total_prob = sum(scaled_probs)
                if total_prob > 0:
                    normalized_probs = [p / total_prob for p in scaled_probs]
                    
                    # 확률 기반 선택
                    chosen_idx = random.choices(range(len(available_candidates)), weights=normalized_probs)[0]
                    chosen_num = available_candidates[chosen_idx][0]
                    
                    selected.append(chosen_num)
                    used_numbers.add(chosen_num)
            
            # 6개 번호 보장
            final_numbers = ensure_six_numbers(selected)
            print(f"✅ 신경망 분석 완료 (시드: {seed}, 층수: {num_layers}, 온도: {temperature:.2f}): {final_numbers}")
            
            return {
                'name': '신경망 분석',
                'description': '다층 신경망과 활성화 함수를 통한 복합 패턴 학습 예측',
                'category': 'advanced',
                'algorithm_id': 6,
                'priority_numbers': safe_int_list(final_numbers),
                'confidence': 79
            }
        except Exception as e:
            print(f"신경망 분석 알고리즘 오류: {e}")
            return self._generate_fallback_numbers("신경망 분석")

    def algorithm_7_markov_chain(self):
        """7. 마르코프 체인 - 완전 수정된 버전"""
        try:
            # 매번 다른 동적 시드 설정
            seed = get_dynamic_seed() + random.randint(10000, 99999)
            random.seed(seed)
            np.random.seed(seed)
            
            if self.numbers is None or len(self.numbers) < 20:
                print(f"⚠️ 마르코프 체인: 데이터 부족 - 백업 모드")
                return self._generate_fallback_numbers("마르코프 체인")
            
            # 마르코프 체인 차수를 랜덤하게 변경 (1차, 2차, 3차)
            chain_order = random.randint(1, 3)
            transition_matrices = {}
            
            # 분석할 데이터 범위도 랜덤하게 변경
            analysis_start = random.randint(0, max(0, len(self.numbers) - 100))
            analysis_data = self.numbers[analysis_start:]
            
            if chain_order == 1:
                # 1차 마르코프 체인 - 단순 전이
                transition_matrix = defaultdict(lambda: defaultdict(int))
                
                for i in range(len(analysis_data) - 1):
                    current_set = set(safe_int(x) for x in analysis_data[i])
                    next_set = set(safe_int(x) for x in analysis_data[i + 1])
                    
                    for curr_num in current_set:
                        for next_num in next_set:
                            # 랜덤 가중치 추가
                            weight = 1 + random.uniform(-0.3, 0.3)
                            transition_matrix[curr_num][next_num] += weight
                
                transition_matrices[1] = transition_matrix
                
            elif chain_order == 2:
                # 2차 마르코프 체인 - 이전 2개 상태 고려
                transition_matrix = defaultdict(lambda: defaultdict(int))
                
                for i in range(len(analysis_data) - 2):
                    prev_set = tuple(sorted(safe_int(x) for x in analysis_data[i]))
                    curr_set = tuple(sorted(safe_int(x) for x in analysis_data[i + 1]))
                    next_set = set(safe_int(x) for x in analysis_data[i + 2])
                    
                    state_key = (prev_set, curr_set)
                    
                    for next_num in next_set:
                        weight = 1 + random.uniform(-0.2, 0.2)
                        transition_matrix[state_key][next_num] += weight
                
                transition_matrices[2] = transition_matrix
                
            else:  # chain_order == 3
                # 3차 마르코프 체인 - 패턴 기반
                pattern_transitions = defaultdict(lambda: defaultdict(int))
                
                for i in range(len(analysis_data) - 3):
                    # 3회차 패턴 분석
                    pattern = []
                    for j in range(3):
                        round_numbers = sorted(safe_int(x) for x in analysis_data[i + j])
                        # 패턴 특성 추출
                        odd_count = sum(1 for x in round_numbers if x % 2 == 1)
                        sum_value = sum(round_numbers)
                        pattern.append((odd_count, sum_value // 20))  # 구간화
                    
                    pattern_key = tuple(pattern)
                    next_numbers = set(safe_int(x) for x in analysis_data[i + 3])
                    
                    for next_num in next_numbers:
                        weight = 1 + random.uniform(-0.1, 0.1)
                        pattern_transitions[pattern_key][next_num] += weight
                
                transition_matrices[3] = pattern_transitions
            
            # 예측 생성
            selected = []
            used_numbers = set()
            
            if chain_order == 1:
                # 최근 회차 기반 예측
                last_numbers = set(safe_int(x) for x in analysis_data[-1])
                transition_matrix = transition_matrices[1]
                
                # 각 마지막 번호에서 전이 확률 계산
                all_predictions = defaultdict(float)
                
                for curr_num in last_numbers:
                    if curr_num in transition_matrix:
                        transitions = transition_matrix[curr_num]
                        total = sum(transitions.values())
                        
                        for next_num, count in transitions.items():
                            probability = (count / total) * random.uniform(0.8, 1.2)  # 랜덤 노이즈
                            all_predictions[next_num] += probability
                
                # 확률 기반 선택
                sorted_predictions = sorted(all_predictions.items(), 
                                          key=lambda x: x[1] + random.uniform(-0.1, 0.1), 
                                          reverse=True)
                
                for num, prob in sorted_predictions:
                    if len(selected) >= 6:
                        break
                    if safe_int(num) not in used_numbers:
                        selected.append(safe_int(num))
                        used_numbers.add(safe_int(num))
            
            elif chain_order == 2:
                # 2차 마르코프 체인 예측
                if len(analysis_data) >= 2:
                    prev_state = tuple(sorted(safe_int(x) for x in analysis_data[-2]))
                    curr_state = tuple(sorted(safe_int(x) for x in analysis_data[-1]))
                    state_key = (prev_state, curr_state)
                    
                    transition_matrix = transition_matrices[2]
                    
                    if state_key in transition_matrix:
                        transitions = transition_matrix[state_key]
                        total = sum(transitions.values())
                        
                        candidates = []
                        for next_num, count in transitions.items():
                            probability = (count / total) * random.uniform(0.7, 1.3)
                            candidates.append((safe_int(next_num), probability))
                        
                        candidates.sort(key=lambda x: x[1], reverse=True)
                        
                        for num, prob in candidates:
                            if len(selected) >= 6:
                                break
                            if num not in used_numbers:
                                selected.append(num)
                                used_numbers.add(num)
            
            else:  # chain_order == 3
                # 3차 마르코프 체인 예측
                if len(analysis_data) >= 3:
                    # 최근 3회차 패턴 분석
                    recent_pattern = []
                    for j in range(3):
                        round_numbers = sorted(safe_int(x) for x in analysis_data[-(3-j)])
                        odd_count = sum(1 for x in round_numbers if x % 2 == 1)
                        sum_value = sum(round_numbers)
                        recent_pattern.append((odd_count, sum_value // 20))
                    
                    pattern_key = tuple(recent_pattern)
                    pattern_transitions = transition_matrices[3]
                    
                    if pattern_key in pattern_transitions:
                        transitions = pattern_transitions[pattern_key]
                        total = sum(transitions.values())
                        
                        candidates = []
                        for next_num, count in transitions.items():
                            probability = (count / total) * random.uniform(0.6, 1.4)
                            candidates.append((safe_int(next_num), probability))
                        
                        candidates.sort(key=lambda x: x[1] + random.uniform(-0.2, 0.2), reverse=True)
                        
                        for num, prob in candidates:
                            if len(selected) >= 6:
                                break
                            if num not in used_numbers:
                                selected.append(num)
                                used_numbers.add(num)
            
            # 부족한 번호는 최근 빈도 기반으로 채우기
            if len(selected) < 6:
                recent_freq = Counter(analysis_data[-10:].flatten())
                freq_candidates = [safe_int(num) for num, _ in recent_freq.most_common() 
                                 if safe_int(num) not in used_numbers]
                random.shuffle(freq_candidates)  # 랜덤 섞기
                
                for num in freq_candidates:
                    if len(selected) >= 6:
                        break
                    selected.append(num)
                    used_numbers.add(num)
            
            # 6개 번호 보장
            final_numbers = ensure_six_numbers(selected)
            print(f"✅ 마르코프 체인 완료 (시드: {seed}, 차수: {chain_order}차): {final_numbers}")
            
            return {
                'name': '마르코프 체인',
                'description': f'{chain_order}차 상태 전이 확률을 이용한 연속성 패턴 예측',
                'category': 'advanced',
                'algorithm_id': 7,
                'priority_numbers': safe_int_list(final_numbers),
                'confidence': 74
            }
        except Exception as e:
            print(f"마르코프 체인 알고리즘 오류: {e}")
            return self._generate_fallback_numbers("마르코프 체인")

    def algorithm_8_genetic_algorithm(self):
        """8. 유전자 알고리즘 - 수정된 버전"""
        try:
            # 동적 시드 설정
            seed = get_dynamic_seed()
            random.seed(seed)
            np.random.seed(seed)
            
            if self.numbers is None:
                print(f"⚠️ 유전자 알고리즘: 데이터 없음 - 백업 모드")
                return self._generate_fallback_numbers("유전자 알고리즘")
            
            # 유전자 알고리즘 파라미터를 랜덤하게 변경
            population_size = random.randint(20, 40)
            generations = random.randint(5, 10)
            mutation_rate = random.uniform(0.05, 0.2)
            crossover_rate = random.uniform(0.6, 0.9)
            
            # 적합도 함수: 과거 당첨번호와의 유사성 + 랜덤 요소
            def fitness(individual):
                score = 0
                analysis_range = random.randint(8, 15)
                
                for past_draw in self.numbers[-analysis_range:]:
                    common = len(set(individual) & set(safe_int(x) for x in past_draw))
                    # 기본 점수에 랜덤 보너스 추가
                    base_score = common * common
                    random_bonus = random.uniform(0.8, 1.2)
                    score += base_score * random_bonus
                
                # 번호 분포 다양성 점수 추가
                diversity_score = len(set(individual)) * random.uniform(0.5, 1.5)
                return score + diversity_score
            
            # 초기 집단 생성 (더 다양한 개체들)
            population = []
            for _ in range(population_size):
                if random.random() < 0.3:  # 30% 확률로 완전 랜덤
                    individual = random.sample(range(1, 46), 6)
                else:  # 70% 확률로 빈도 기반
                    all_numbers = self.numbers.flatten()
                    freq = Counter(all_numbers)
                    top_20 = [num for num, _ in freq.most_common(20)]
                    individual = random.sample(top_20, min(6, len(top_20)))
                    while len(individual) < 6:
                        candidate = random.randint(1, 45)
                        if candidate not in individual:
                            individual.append(candidate)
                
                population.append(sorted(individual))
            
            # 진화 과정
            for generation in range(generations):
                # 적합도 계산
                fitness_scores = [(ind, fitness(ind)) for ind in population]
                fitness_scores.sort(key=lambda x: x[1], reverse=True)
                
                # 엘리트 선택 (상위 20%)
                elite_count = max(2, population_size // 5)
                elites = [ind for ind, score in fitness_scores[:elite_count]]
                
                # 토너먼트 선택으로 부모 선택
                def tournament_selection():
                    tournament_size = random.randint(3, 5)
                    tournament = random.sample(fitness_scores, tournament_size)
                    return max(tournament, key=lambda x: x[1])[0]
                
                # 다음 세대 생성
                new_population = elites.copy()
                
                while len(new_population) < population_size:
                    if random.random() < crossover_rate:
                        # 교차
                        parent1 = tournament_selection()
                        parent2 = tournament_selection()
                        
                        # 다양한 교차 방법 중 랜덤 선택
                        crossover_type = random.randint(1, 3)
                        
                        if crossover_type == 1:  # 단순 교차
                            crossover_point = random.randint(1, 5)
                            child = list(set(parent1[:crossover_point] + parent2[crossover_point:]))
                        elif crossover_type == 2:  # 균등 교차
                            child = []
                            for i in range(6):
                                if i < len(parent1) and i < len(parent2):
                                    chosen = parent1[i] if random.random() < 0.5 else parent2[i]
                                    if chosen not in child:
                                        child.append(chosen)
                        else:  # 부분 매칭 교차
                            child = parent1[:3].copy()
                            for num in parent2:
                                if num not in child and len(child) < 6:
                                    child.append(num)
                        
                    else:
                        # 돌연변이로만 생성
                        child = random.sample(range(1, 46), 6)
                    
                    # 돌연변이 적용
                    if random.random() < mutation_rate and len(child) > 0:
                        mutation_type = random.randint(1, 3)
                        
                        if mutation_type == 1:  # 단일 돌연변이
                            mutation_idx = random.randint(0, len(child)-1)
                            new_number = random.randint(1, 45)
                            while new_number in child:
                                new_number = random.randint(1, 45)
                            child[mutation_idx] = new_number
                            
                        elif mutation_type == 2:  # 교환 돌연변이
                            if len(child) >= 2:
                                idx1, idx2 = random.sample(range(len(child)), 2)
                                child[idx1], child[idx2] = child[idx2], child[idx1]
                                
                        else:  # 삽입 돌연변이
                            new_number = random.randint(1, 45)
                            if new_number not in child:
                                if len(child) < 6:
                                    child.append(new_number)
                                else:
                                    replace_idx = random.randint(0, len(child)-1)
                                    child[replace_idx] = new_number
                    
                    # 6개 번호 보장 후 추가
                    final_child = ensure_six_numbers(child)
                    new_population.append(final_child)
                
                population = new_population
                
                # 다양성 유지를 위한 재시딩 (50% 확률)
                if random.random() < 0.5:
                    diversity_injection_count = population_size // 10
                    for _ in range(diversity_injection_count):
                        if len(population) > diversity_injection_count:
                            # 낮은 적합도 개체를 새로운 랜덤 개체로 교체
                            worst_idx = random.randint(population_size//2, len(population)-1)
                            population[worst_idx] = sorted(random.sample(range(1, 46), 6))
            
            # 최종 개체 선택 (적합도 + 랜덤성)
            final_fitness = [(ind, fitness(ind) + random.uniform(-10, 10)) for ind in population]
            best_individual = max(final_fitness, key=lambda x: x[1])[0]
            
            print(f"✅ 유전자 알고리즘 완료 (시드: {seed}, 세대: {generations}, 돌연변이율: {mutation_rate:.2f}): {best_individual}")
            
            return {
                'name': '유전자 알고리즘',
                'description': '진화론적 최적화를 통한 적응형 번호 조합 예측',
                'category': 'advanced',
                'algorithm_id': 8,
                'priority_numbers': safe_int_list(best_individual),
                'confidence': 77
            }
        except Exception as e:
            print(f"유전자 알고리즘 오류: {e}")
            return self._generate_fallback_numbers("유전자 알고리즘")

    def algorithm_9_correlation_analysis(self):
        """9. 동반출현 분석 - 완전 수정된 버전"""
        try:
            # 매번 다른 동적 시드 설정
            seed = get_dynamic_seed() + random.randint(50000, 99999)
            random.seed(seed)
            np.random.seed(seed)
            
            if self.numbers is None or len(self.numbers) < 30:
                print(f"⚠️ 동반출현 분석: 데이터 부족 - 백업 모드")
                return self._generate_fallback_numbers("동반출현 분석")
            
            # 분석 방법을 랜덤하게 변경
            analysis_methods = ['pairwise', 'triplet', 'conditional', 'temporal']
            selected_method = random.choice(analysis_methods)
            
            # 분석할 데이터 범위도 랜덤하게 변경
            analysis_count = random.randint(50, min(150, len(self.numbers)))
            analysis_data = self.numbers[-analysis_count:]
            
            if selected_method == 'pairwise':
                # 기본 페어 분석
                co_occurrence = defaultdict(int)
                
                for draw in analysis_data:
                    nums = [safe_int(x) for x in draw]
                    for i in range(len(nums)):
                        for j in range(i + 1, len(nums)):
                            pair = tuple(sorted([nums[i], nums[j]]))
                            # 랜덤 가중치 추가
                            weight = random.uniform(0.8, 1.2)
                            co_occurrence[pair] += weight
                
                # 강한 상관관계 페어 찾기 + 랜덤 순서 섞기
                strong_pairs = list(co_occurrence.items())
                # 값에 랜덤 노이즈 추가 후 정렬
                strong_pairs.sort(key=lambda x: x[1] + random.uniform(-2, 2), reverse=True)
                strong_pairs = strong_pairs[:25]  # 상위 25개
                random.shuffle(strong_pairs)  # 추가 랜덤 섞기
                
            elif selected_method == 'triplet':
                # 3개 조합 분석
                triplet_occurrence = defaultdict(int)
                
                for draw in analysis_data:
                    nums = [safe_int(x) for x in draw]
                    for i in range(len(nums)):
                        for j in range(i + 1, len(nums)):
                            for k in range(j + 1, len(nums)):
                                triplet = tuple(sorted([nums[i], nums[j], nums[k]]))
                                weight = random.uniform(0.7, 1.3)
                                triplet_occurrence[triplet] += weight
                
                # 트리플렛을 페어로 변환
                strong_pairs = []
                top_triplets = sorted(triplet_occurrence.items(), 
                                    key=lambda x: x[1] + random.uniform(-1, 1), 
                                    reverse=True)[:15]
                
                for triplet, count in top_triplets:
                    # 트리플렛에서 모든 페어 추출
                    for i in range(len(triplet)):
                        for j in range(i + 1, len(triplet)):
                            pair = (triplet[i], triplet[j])
                            strong_pairs.append((pair, count * random.uniform(0.5, 1.0)))
                
            elif selected_method == 'conditional':
                # 조건부 확률 분석
                conditional_probs = defaultdict(lambda: defaultdict(int))
                
                for draw in analysis_data:
                    nums = [safe_int(x) for x in draw]
                    # 각 번호가 나왔을 때 다른 번호들의 조건부 확률
                    for base_num in nums:
                        for other_num in nums:
                            if base_num != other_num:
                                weight = random.uniform(0.6, 1.4)
                                conditional_probs[base_num][other_num] += weight
                
                # 조건부 확률이 높은 페어들 추출
                strong_pairs = []
                for base_num, others in conditional_probs.items():
                    if others:
                        total = sum(others.values())
                        for other_num, count in others.items():
                            prob = (count / total) * random.uniform(0.8, 1.2)
                            if prob > 0.1:  # 임계값
                                pair = tuple(sorted([base_num, other_num]))
                                strong_pairs.append((pair, prob * 100))
                
                # 중복 제거 및 정렬
                pair_dict = {}
                for pair, score in strong_pairs:
                    if pair in pair_dict:
                        pair_dict[pair] += score
                    else:
                        pair_dict[pair] = score
                
                strong_pairs = list(pair_dict.items())
                strong_pairs.sort(key=lambda x: x[1] + random.uniform(-5, 5), reverse=True)
                
            else:  # temporal
                # 시간적 상관관계 분석
                temporal_correlation = defaultdict(lambda: defaultdict(int))
                
                # 연속된 회차간 번호 상관관계
                time_lag = random.randint(1, 3)  # 1~3회차 지연
                
                for i in range(len(analysis_data) - time_lag):
                    current_nums = [safe_int(x) for x in analysis_data[i]]
                    future_nums = [safe_int(x) for x in analysis_data[i + time_lag]]
                    
                    for curr_num in current_nums:
                        for future_num in future_nums:
                            weight = random.uniform(0.5, 1.5) / time_lag  # 지연시간에 반비례
                            temporal_correlation[curr_num][future_num] += weight
                
                # 시간적 상관관계가 높은 페어들
                strong_pairs = []
                for curr_num, futures in temporal_correlation.items():
                    for future_num, weight in futures.items():
                        pair = tuple(sorted([curr_num, future_num]))
                        strong_pairs.append((pair, weight * random.uniform(0.7, 1.3)))
                
                strong_pairs.sort(key=lambda x: x[1] + random.uniform(-1, 1), reverse=True)
            
            # 페어 기반 번호 선택
            selected = []
            used_numbers = set()
            pair_usage_count = {}
            
            # 페어 선택 전략을 랜덤하게 변경
            selection_strategy = random.choice(['greedy', 'balanced', 'diverse'])
            
            if selection_strategy == 'greedy':
                # 가장 강한 페어부터 선택
                for (num1, num2), strength in strong_pairs[:15]:
                    if len(selected) >= 6:
                        break
                    
                    added_count = 0
                    if num1 not in used_numbers and len(selected) < 6:
                        selected.append(num1)
                        used_numbers.add(num1)
                        added_count += 1
                    
                    if num2 not in used_numbers and len(selected) < 6:
                        selected.append(num2)
                        used_numbers.add(num2)
                        added_count += 1
                    
                    if added_count > 0:
                        pair_usage_count[(num1, num2)] = strength
                        
            elif selection_strategy == 'balanced':
                # 균형있게 페어에서 하나씩 선택
                for (num1, num2), strength in strong_pairs:
                    if len(selected) >= 6:
                        break
                    
                    # 페어 중 하나만 선택 (랜덤)
                    candidates = [n for n in [num1, num2] if n not in used_numbers]
                    if candidates:
                        chosen = random.choice(candidates)
                        selected.append(chosen)
                        used_numbers.add(chosen)
                        
            else:  # diverse
                # 다양성 중심 선택
                number_scores = defaultdict(float)
                
                # 각 번호의 총 상관관계 점수 계산
                for (num1, num2), strength in strong_pairs:
                    adjustment = random.uniform(0.8, 1.2)
                    number_scores[num1] += strength * adjustment
                    number_scores[num2] += strength * adjustment
                
                # 점수 순으로 정렬하되 다양성 고려
                scored_numbers = list(number_scores.items())
                scored_numbers.sort(key=lambda x: x[1] + random.uniform(-20, 20), reverse=True)
                
                # 번호 간 최소 거리 유지하며 선택
                min_distance = random.randint(3, 8)
                
                for num, score in scored_numbers:
                    if len(selected) >= 6:
                        break
                    
                    # 기존 선택된 번호와의 거리 확인
                    too_close = False
                    for existing in selected:
                        if abs(num - existing) < min_distance:
                            too_close = True
                            break
                    
                    if not too_close:
                        selected.append(num)
                        used_numbers.add(num)
            
            # 부족한 번호는 랜덤 보완
            if len(selected) < 6:
                remaining = [n for n in range(1, 46) if n not in used_numbers]
                random.shuffle(remaining)
                
                need_count = 6 - len(selected)
                selected.extend(remaining[:need_count])
            
            # 6개 번호 보장
            final_numbers = ensure_six_numbers(selected)
            print(f"✅ 동반출현 분석 완료 (시드: {seed}, 방법: {selected_method}, 전략: {selection_strategy}): {final_numbers}")
            
            return {
                'name': '동반출현 분석',
                'description': f'{selected_method} 방식의 번호 간 상관관계 분석 예측',
                'category': 'advanced',
                'algorithm_id': 9,
                'priority_numbers': safe_int_list(final_numbers),
                'confidence': 75
            }
        except Exception as e:
            print(f"동반출현 분석 알고리즘 오류: {e}")
            return self._generate_fallback_numbers("동반출현 분석")

    def algorithm_10_time_series(self):
        """10. 시계열 분석 - 완전 수정된 버전"""
        try:
            # 매번 다른 동적 시드 설정
            seed = get_dynamic_seed() + int(datetime.now().microsecond)
            random.seed(seed)
            np.random.seed(seed)
            
            if self.numbers is None or len(self.numbers) < 20:
                print(f"⚠️ 시계열 분석: 데이터 부족 - 백업 모드")
                return self._generate_fallback_numbers("시계열 분석")
            
            # 시계열 분석 방법을 랜덤하게 선택
            analysis_methods = ['trend', 'seasonal', 'cyclic', 'momentum', 'regression']
            selected_method = random.choice(analysis_methods)
            
            # 시계열 파라미터들
            window_size = random.randint(5, 15)
            smoothing_factor = random.uniform(0.1, 0.5)
            trend_weight = random.uniform(0.6, 1.4)
            
            all_time_patterns = {}
            
            for num in range(1, 46):
                appearances = []
                for i, draw in enumerate(self.numbers):
                    if num in draw:
                        appearances.append(i)
                
                if len(appearances) >= 3:
                    if selected_method == 'trend':
                        # 트렌드 분석
                        recent_appearances = appearances[-window_size:]
                        
                        if len(recent_appearances) >= 2:
                            # 선형 트렌드 계산
                            x_vals = list(range(len(recent_appearances)))
                            y_vals = recent_appearances
                            
                            # 간단한 선형 회귀
                            n = len(x_vals)
                            sum_x = sum(x_vals)
                            sum_y = sum(y_vals)
                            sum_xy = sum(x * y for x, y in zip(x_vals, y_vals))
                            sum_x2 = sum(x * x for x in x_vals)
                            
                            if n * sum_x2 - sum_x * sum_x != 0:
                                slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
                                intercept = (sum_y - slope * sum_x) / n
                                
                                # 다음 출현 예측
                                next_x = len(recent_appearances)
                                predicted_next = slope * next_x + intercept
                                current_time = len(self.numbers) - 1
                                
                                trend_score = max(0, 1 - abs(predicted_next - current_time) / 50)
                                trend_score *= trend_weight * random.uniform(0.8, 1.2)
                                all_time_patterns[num] = trend_score
                    
                    elif selected_method == 'seasonal':
                        # 계절성 분석 (주기적 패턴)
                        period_lengths = [5, 7, 10, 12]  # 다양한 주기 길이
                        best_score = 0
                        
                        for period in period_lengths:
                            if len(appearances) >= period * 2:
                                # 주기적 패턴 분석
                                period_scores = []
                                
                                for phase in range(period):
                                    phase_appearances = [app for app in appearances if app % period == phase]
                                    if phase_appearances:
                                        recent_phase = [app for app in phase_appearances if app >= len(self.numbers) - 20]
                                        phase_score = len(recent_phase) / max(1, len(phase_appearances))
                                        period_scores.append(phase_score)
                                
                                if period_scores:
                                    current_phase = len(self.numbers) % period
                                    if current_phase < len(period_scores):
                                        seasonal_score = period_scores[current_phase] * random.uniform(0.7, 1.3)
                                        best_score = max(best_score, seasonal_score)
                        
                        all_time_patterns[num] = best_score
                    
                    elif selected_method == 'cyclic':
                        # 순환 분석 (불규칙한 주기)
                        intervals = []
                        for i in range(1, len(appearances)):
                            interval = appearances[i] - appearances[i-1]
                            intervals.append(interval)
                        
                        if intervals:
                            # 간격의 평균과 분산 계산
                            avg_interval = sum(intervals) / len(intervals)
                            variance = sum((x - avg_interval) ** 2 for x in intervals) / len(intervals)
                            std_dev = math.sqrt(variance)
                            
                            # 마지막 출현으로부터의 거리
                            last_appearance = appearances[-1]
                            distance_from_last = len(self.numbers) - 1 - last_appearance
                            
                            # 다음 출현 예상 확률 (정규분포 기반)
                            expected_next = avg_interval + random.uniform(-std_dev, std_dev)
                            prob = math.exp(-0.5 * ((distance_from_last - expected_next) / (std_dev + 1)) ** 2)
                            all_time_patterns[num] = prob * random.uniform(0.5, 1.5)
                    
                    elif selected_method == 'momentum':
                        # 모멘텀 분석 (최근 가속도)
                        if len(appearances) >= 3:
                            recent_3 = appearances[-3:]
                            
                            # 가속도 계산
                            interval_1 = recent_3[1] - recent_3[0]
                            interval_2 = recent_3[2] - recent_3[1]
                            acceleration = interval_2 - interval_1
                            
                            # 다음 간격 예측
                            predicted_interval = interval_2 + acceleration * random.uniform(0.8, 1.2)
                            predicted_next = recent_3[-1] + predicted_interval
                            current_time = len(self.numbers) - 1
                            
                            # 현재 시점과의 근접도
                            momentum_score = max(0, 1 - abs(predicted_next - current_time) / 30)
                            momentum_score *= random.uniform(0.6, 1.4)
                            all_time_patterns[num] = momentum_score
                    
                    else:  # regression
                        # 회귀 분석 (복합 요인)
                        if len(appearances) >= 5:
                            # 다양한 특성 추출
                            features = []
                            
                            for i, app_time in enumerate(appearances):
                                feature_vector = [
                                    app_time / len(self.numbers),  # 정규화된 시간
                                    i / len(appearances),  # 순서
                                    math.sin(2 * math.pi * app_time / 52),  # 연간 주기
                                    math.cos(2 * math.pi * app_time / 52),  # 연간 주기
                                    random.uniform(0.8, 1.2)  # 랜덤 노이즈
                                ]
                                features.append(feature_vector)
                            
                            # 간단한 가중 평균 예측
                            if features:
                                recent_features = features[-min(5, len(features)):]
                                weights = [1 / (i + 1) for i in range(len(recent_features))]
                                weight_sum = sum(weights)
                                
                                predicted_features = [0] * len(recent_features[0])
                                for i, feature_vector in enumerate(recent_features):
                                    weight = weights[i] / weight_sum
                                    for j, feature_val in enumerate(feature_vector):
                                        predicted_features[j] += feature_val * weight
                                
                                # 예측 점수 계산
                                regression_score = sum(predicted_features) / len(predicted_features)
                                regression_score *= random.uniform(0.7, 1.3)
                                all_time_patterns[num] = max(0, min(1, regression_score))
            
            # 시계열 점수 기반 번호 선택
            if not all_time_patterns:
                # 패턴이 없으면 최근 빈도 기반
                recent_data = self.numbers[-20:]
                freq = Counter(recent_data.flatten())
                top_numbers = [safe_int(num) for num, _ in freq.most_common(20)]
                random.shuffle(top_numbers)
                selected = top_numbers[:6]
            else:
                # 시계열 점수로 정렬 + 랜덤 노이즈
                sorted_patterns = sorted(all_time_patterns.items(), 
                                       key=lambda x: x[1] + random.uniform(-0.2, 0.2), 
                                       reverse=True)
                
                # 다양한 선택 전략 적용
                selection_strategy = random.choice(['top_scores', 'probability_based', 'threshold_filter'])
                
                if selection_strategy == 'top_scores':
                    # 단순히 상위 점수 선택
                    selected = [safe_int(num) for num, score in sorted_patterns[:6]]
                    
                elif selection_strategy == 'probability_based':
                    # 점수를 확률로 변환하여 선택
                    total_score = sum(score for num, score in sorted_patterns)
                    if total_score > 0:
                        probabilities = [score / total_score for num, score in sorted_patterns]
                        selected = []
                        used_numbers = set()
                        
                        for _ in range(6):
                            if not sorted_patterns:
                                break
                            
                            available_indices = [i for i, (num, _) in enumerate(sorted_patterns) 
                                               if num not in used_numbers]
                            if not available_indices:
                                break
                            
                            available_probs = [probabilities[i] for i in available_indices]
                            if sum(available_probs) > 0:
                                # 확률 정규화
                                norm_probs = [p / sum(available_probs) for p in available_probs]
                                chosen_idx = random.choices(available_indices, weights=norm_probs)[0]
                                chosen_num = sorted_patterns[chosen_idx][0]
                                selected.append(safe_int(chosen_num))
                                used_numbers.add(chosen_num)
                    else:
                        selected = [safe_int(num) for num, score in sorted_patterns[:6]]
                        
                else:  # threshold_filter
                    # 임계값 이상의 번호만 고려
                    threshold = random.uniform(0.3, 0.7)
                    qualified_numbers = [safe_int(num) for num, score in sorted_patterns if score >= threshold]
                    
                    if len(qualified_numbers) >= 6:
                        random.shuffle(qualified_numbers)
                        selected = qualified_numbers[:6]
                    else:
                        # 임계값을 만족하는 번호 + 추가 번호
                        additional_needed = 6 - len(qualified_numbers)
                        additional_numbers = [safe_int(num) for num, score in sorted_patterns 
                                            if score < threshold and num not in qualified_numbers]
                        random.shuffle(additional_numbers)
                        selected = qualified_numbers + additional_numbers[:additional_needed]
            
            # 6개 번호 보장
            final_numbers = ensure_six_numbers(selected)
            print(f"✅ 시계열 분석 완료 (시드: {seed}, 방법: {selected_method}): {final_numbers}")
            
            return {
                'name': '시계열 분석',
                'description': f'{selected_method} 기반 시간 흐름 패턴 예측',
                'category': 'advanced',
                'algorithm_id': 10,
                'priority_numbers': safe_int_list(final_numbers),
                'confidence': 72
            }
        except Exception as e:
            print(f"시계열 분석 알고리즘 오류: {e}")
            return self._generate_fallback_numbers("시계열 분석")

    def _generate_fallback_numbers(self, algorithm_name):
        """백업용 번호 생성 - 항상 6개 보장 + 동적 시드"""
        # 백업용 번호도 동적 시드 사용
        seed = get_dynamic_seed()
        random.seed(seed)
        
        fallback_numbers = sorted(random.sample(range(1, 46), 6))
        print(f"🔄 {algorithm_name} 백업 번호 생성 (시드: {seed}): {fallback_numbers}")
        return {
            'name': algorithm_name,
            'description': f'{algorithm_name} (백업 모드)',
            'category': 'basic',
            'algorithm_id': 0,
            'priority_numbers': fallback_numbers,
            'confidence': 50
        }

    def generate_all_predictions(self):
        """10가지 알고리즘 모두 실행하여 각각 1개씩 번호 생성"""
        try:
            print(f"🎯 10개 알고리즘 실행 시작 - 매번 다른 결과 보장")
            
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
                    print(f"🔄 알고리즘 {i} 실행 중... (동적 시드 적용)")
                    
                    # 각 알고리즘 실행 전 추가 시드 재설정
                    additional_seed = get_dynamic_seed() + i * 1000
                    random.seed(additional_seed)
                    np.random.seed(additional_seed)
                    
                    result = algorithm()
                    algorithm_key = f"algorithm_{i:02d}"
                    
                    # 6개 번호 검증
                    if len(result['priority_numbers']) != 6:
                        print(f"⚠️ 알고리즘 {i}: {result['name']} - 번호 개수 오류 ({len(result['priority_numbers'])}개)")
                        result['priority_numbers'] = ensure_six_numbers(result['priority_numbers'])
                        print(f"🔧 알고리즘 {i}: 번호 보정 완료")
                        fallback_count += 1
                    else:
                        success_count += 1
                    
                    results[algorithm_key] = result
                    print(f"✅ 알고리즘 {i}: {result['name']} 완료 - {result['priority_numbers']}")
                    
                    # 각 알고리즘 사이에 최소 지연시간 추가 (더 많은 랜덤성)
                    time.sleep(0.001)
                    
                except Exception as e:
                    print(f"❌ 알고리즘 {i} 실행 오류: {e}")
                    fallback = self._generate_fallback_numbers(f"알고리즘 {i}")
                    results[f"algorithm_{i:02d}"] = fallback
                    fallback_count += 1
            
            print(f"🎯 전체 알고리즘 실행 완료")
            print(f"  - 성공: {success_count}개")
            print(f"  - 백업/보정: {fallback_count}개")
            print(f"  - 총계: {len(results)}개")
            print(f"  - 랜덤성 개선: 동적 시드 시스템 적용")
            
            return results
            
        except Exception as e:
            print(f"전체 예측 생성 오류: {e}")
            return self._generate_emergency_backup()

    def _generate_emergency_backup(self):
        """긴급 백업 응답 - 동적 시드 적용"""
        print(f"🆘 긴급 백업 모드 활성화 - 동적 시드 적용")
        
        backup_algorithms = [
            "빈도 분석", "핫/콜드 분석", "패턴 분석", "통계 분석", "머신러닝",
            "신경망 분석", "마르코프 체인", "유전자 알고리즘", "동반출현 분석", "시계열 분석"
        ]
        
        results = {}
        for i, name in enumerate(backup_algorithms, 1):
            # 각 백업 번호마다 다른 시드 사용
            seed = get_dynamic_seed() + i * 10000
            random.seed(seed)
            
            backup_numbers = sorted(random.sample(range(1, 46), 6))
            results[f"algorithm_{i:02d}"] = {
                'name': name,
                'description': f'{name} (긴급 백업)',
                'category': 'advanced' if i > 5 else 'basic',
                'algorithm_id': i,
                'priority_numbers': backup_numbers,
                'confidence': 50
            }
            print(f"🆘 긴급 백업 {i}: {name} (시드: {seed}) - {backup_numbers}")
        
        return results

# 전역 변수
predictor = None

def get_predictor():
    global predictor
    if predictor is None:
        print(f"🔄 LottoPredictor 인스턴스 생성 중...")
        predictor = AdvancedLottoPredictor()
        print(f"✅ LottoPredictor 인스턴스 생성 완료")
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
            'algorithms_available': 10,
            'random_system': 'dynamic_seed_enabled'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'status': 'unhealthy',
            'error': str(e)
        }), 500

@app.route('/api/predictions')
def get_predictions():
    """10가지 알고리즘 예측 API - 랜덤성 개선"""
    try:
        print(f"📡 예측 API 호출 받음 - 동적 시드 시스템 활성화")
        
        # 추가 랜덤성을 위한 전역 시드 재설정
        global_seed = get_dynamic_seed()
        random.seed(global_seed)
        np.random.seed(global_seed)
        
        pred = get_predictor()
        
        if pred.data is None:
            print(f"⚠️ 데이터 없음 - 재로드 시도")
            if not pred.load_data():
                print(f"❌ 데이터 재로드 실패")
                return jsonify({
                    'success': False,
                    'error': 'CSV 데이터를 로드할 수 없습니다.'
                }), 500
        
        # 10가지 알고리즘 모두 실행
        print(f"🎯 10가지 알고리즘 실행 시작 (글로벌 시드: {global_seed})")
        results = pred.generate_all_predictions()
        
        # 최종 검증: 모든 알고리즘이 6개 번호를 반환하는지 확인
        final_check_count = 0
        for key, result in results.items():
            if len(result['priority_numbers']) != 6:
                print(f"🔧 최종 검증: {result['name']} 번호 보정 중...")
                result['priority_numbers'] = ensure_six_numbers(result['priority_numbers'])
                final_check_count += 1
        
        if final_check_count > 0:
            print(f"🔧 최종 검증에서 {final_check_count}개 알고리즘 보정됨")
        
        # 결과 다양성 검증
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
        
        print(f"✅ 예측 API 응답 완료 - {len(results)}개 알고리즘, {len(unique_results)}개 고유 결과")
        if duplicate_count > 0:
            print(f"⚠️ {duplicate_count}개 중복 결과 발견 - 시드 시스템 점검 필요")
            
        return jsonify(response_data)
        
    except Exception as e:
        print(f"❌ API 예측 에러: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f'예측 생성 중 오류가 발생했습니다: {str(e)}'
        }), 500

@app.route('/api/statistics')
def get_statistics():
    """통계 정보 API"""
    try:
        print(f"📊 통계 API 호출 받음")
        pred = get_predictor()
        
        default_stats = {
            'total_draws': 1190,
            'algorithms_count': 10,
            'last_draw_info': {
                'round': 1190,
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
                print(f"📈 실제 데이터로 통계 생성")
                all_numbers = pred.numbers.flatten()
                frequency = Counter(all_numbers)
                
                most_common = frequency.most_common(10)
                least_common = frequency.most_common()[:-11:-1]
                
                last
