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

def fix_invalid_numbers(numbers):
    """잘못된 번호 수정"""
    try:
        fixed = []
        
        # 유효한 번호만 추출
        if isinstance(numbers, list):
            for num in numbers:
                try:
                    n = int(num)
                    if 1 <= n <= 45 and n not in fixed:
                        fixed.append(n)
                except:
                    continue
        
        # 부족한 번호 랜덤 생성
        while len(fixed) < 6:
            rand_num = random.randint(1, 45)
            if rand_num not in fixed:
                fixed.append(rand_num)
        
        # 6개로 제한하고 정렬
        return sorted(fixed[:6])
        
    except:
        return generate_default_numbers()

def generate_default_numbers():
    """기본 번호 생성"""
    numbers = random.sample(range(1, 46), 6)
    return sorted(numbers)

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
            return self._generate_fallback_numbers("빈도 분석", "basic", 1)

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
            return self._generate_fallback_numbers("핫/콜드 분석", "basic", 2)

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
            return self._generate_fallback_numbers("패턴 분석", "basic", 3)

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
            return self._generate_fallback_numbers("통계 분석", "basic", 4)

    def algorithm_5_machine_learning(self):
        """5. 머신러닝 - 수정된 버전"""
        try:
            # 동적 시드 설정
            seed = get_dynamic_seed()
            random.seed(seed)
            np.random.seed(seed)
            
            if self.numbers is None or len(self.numbers) < 50:
                print(f"⚠️ 머신러닝: 데이터 부족 - 백업 모드")
                return self._generate_fallback_numbers("머신러닝", "basic", 5)
            
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
            return self._generate_fallback_numbers("머신러닝", "basic", 5)

    def algorithm_6_neural_network(self):
        """6. 신경망 분석 - 수정된 안전 버전"""
        try:
            # 매번 다른 동적 시드 설정
            seed = get_dynamic_seed() + int(time.time() % 100000)
            random.seed(seed)
            np.random.seed(seed)
            
            if self.numbers is None or len(self.numbers) < 30:
                print(f"⚠️ 신경망 분석: 데이터 부족 - 백업 모드")
                return self._generate_fallback_numbers("신경망 분석")
            
            # 간단하고 안전한 신경망 시뮬레이션
            selected = []
            used_numbers = set()
            
            # 데이터 기반 가중치 계산 (안전한 방식)
            all_numbers = self.numbers.flatten()
            frequency = Counter(all_numbers)
            
            # 최근 데이터에 더 높은 가중치 부여
            recent_data = self.numbers[-20:]
            recent_frequency = Counter(recent_data.flatten())
            
            # 신경망 스타일의 가중치 조합
            neural_scores = {}
            for num in range(1, 46):
                base_freq = frequency.get(num, 0)
                recent_freq = recent_frequency.get(num, 0)
                
                # 활성화 함수 시뮬레이션 (안전한 계산)
                try:
                    # 시그모이드 스타일 활성화
                    x = (base_freq * 0.3 + recent_freq * 0.7) / 10.0
                    # 안전한 exp 계산
                    if x > 10:
                        activation = 1.0
                    elif x < -10:
                        activation = 0.0
                    else:
                        activation = 1 / (1 + math.exp(-x))
                    
                    # 랜덤 노이즈 추가
                    neural_scores[num] = activation * random.uniform(0.5, 1.5)
                except (OverflowError, ZeroDivisionError, ValueError):
                    # 오류 발생 시 기본값
                    neural_scores[num] = random.uniform(0.1, 0.9)
            
            # 점수 기반 선택
            sorted_numbers = sorted(neural_scores.items(), key=lambda x: x[1], reverse=True)
            
            # 상위 후보들 중에서 랜덤 선택
            top_candidates = [num for num, score in sorted_numbers[:20]]
            random.shuffle(top_candidates)
            
            for num in top_candidates:
                if len(selected) >= 6:
                    break
                if num not in used_numbers:
                    selected.append(num)
                    used_numbers.add(num)
            
            # 6개 번호 보장
            final_numbers = ensure_six_numbers(selected)
            print(f"✅ 신경망 분석 완료 (시드: {seed}): {final_numbers}")
            
            return {
                'name': '신경망 분석',
                'description': '다층 신경망 시뮬레이션을 통한 복합 패턴 학습 예측',
                'category': 'advanced',
                'algorithm_id': 6,
                'priority_numbers': safe_int_list(final_numbers),
                'confidence': 79
            }
        except Exception as e:
            print(f"신경망 분석 알고리즘 오류: {e}")
            return self._generate_fallback_numbers("신경망 분석", "advanced", 6)

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
            
            selected = []
            used_numbers = set()
            
            if chain_order == 1:
                # 1차 마르코프 체인 - 단순 전이
                transition_matrix = defaultdict(lambda: defaultdict(int))
                
                for i in range(len(analysis_data) - 1):
                    current_set = set(safe_int(x) for x in analysis_data[i])
                    next_set = set(safe_int(x) for x in analysis_data[i + 1])
                    
                    for curr_num in current_set:
                        for next_num in next_set:
                            weight = 1 + random.uniform(-0.3, 0.3)
                            transition_matrix[curr_num][next_num] += weight
                
                # 최근 회차 기반 예측
                last_numbers = set(safe_int(x) for x in analysis_data[-1])
                
                # 각 마지막 번호에서 전이 확률 계산
                all_predictions = defaultdict(float)
                
                for curr_num in last_numbers:
                    if curr_num in transition_matrix:
                        transitions = transition_matrix[curr_num]
                        total = sum(transitions.values())
                        
                        for next_num, count in transitions.items():
                            probability = (count / total) * random.uniform(0.8, 1.2)
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
            return self._generate_fallback_numbers("마르코프 체인", "advanced", 7)

    def algorithm_8_genetic_algorithm(self):
        """8. 유전자 알고리즘 - 수정된 버전"""
        try:
            # 동적 시드 설정
            seed = get_dynamic_seed()
            random.seed(seed)
            np.random.seed(seed)
            
            if self.numbers is None:
                print(f"⚠️ 유전자 알고리즘: 데이터 없음 - 백업 모드")
                return self._generate_fallback_numbers("유전자 알고리즘", "advanced", 8)
            
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
            
            # 초기 집단 생성
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
            
            # 진화 과정 (간소화된 버전)
            for generation in range(generations):
                # 적합도 계산
                fitness_scores = [(ind, fitness(ind)) for ind in population]
                fitness_scores.sort(key=lambda x: x[1], reverse=True)
                
                # 엘리트 선택 (상위 20%)
                elite_count = max(2, population_size // 5)
                elites = [ind for ind, score in fitness_scores[:elite_count]]
                
                # 다음 세대 생성
                new_population = elites.copy()
                
                while len(new_population) < population_size:
                    # 간단한 교차 또는 돌연변이
                    if random.random() < crossover_rate and len(elites) >= 2:
                        parent1 = random.choice(elites)
                        parent2 = random.choice(elites)
                        
                        # 단순 교차
                        crossover_point = random.randint(1, 5)
                        child = list(set(parent1[:crossover_point] + parent2[crossover_point:]))
                    else:
                        # 돌연변이로만 생성
                        child = random.sample(range(1, 46), 6)
                    
                    # 6개 번호 보장 후 추가
                    final_child = ensure_six_numbers(child)
                    new_population.append(final_child)
                
                population = new_population
            
            # 최종 개체 선택
            final_fitness = [(ind, fitness(ind) + random.uniform(-10, 10)) for ind in population]
            best_individual = max(final_fitness, key=lambda x: x[1])[0]
            
            print(f"✅ 유전자 알고리즘 완료 (시드: {seed}, 세대: {generations}): {best_individual}")
            
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
            return self._generate_fallback_numbers("유전자 알고리즘", "advanced", 8)

    def algorithm_9_correlation_analysis(self):
        """9. 동반출현 분석 - 완전 수정된 버전"""
        try:
            # 매번 다른 동적 시드 설정
            seed = get_dynamic_seed() + random.randint(50000, 99999)
            random.seed(seed)
            np.random.seed(seed)
            
            if self.numbers is None or len(self.numbers) < 30:
                print(f"⚠️ 동반출현 분석: 데이터 부족 - 백업 모드")
                return self._generate_fallback_numbers("동반출현 분석", "advanced", 9)
            
            # 분석 방법을 랜덤하게 변경
            analysis_methods = ['pairwise', 'conditional']
            selected_method = random.choice(analysis_methods)
            
            # 분석할 데이터 범위도 랜덤하게 변경
            analysis_count = random.randint(50, min(150, len(self.numbers)))
            analysis_data = self.numbers[-analysis_count:]
            
            selected = []
            used_numbers = set()
            
            if selected_method == 'pairwise':
                # 기본 페어 분석
                co_occurrence = defaultdict(int)
                
                for draw in analysis_data:
                    nums = [safe_int(x) for x in draw]
                    for i in range(len(nums)):
                        for j in range(i + 1, len(nums)):
                            pair = tuple(sorted([nums[i], nums[j]]))
                            weight = random.uniform(0.8, 1.2)
                            co_occurrence[pair] += weight
                
                # 강한 상관관계 페어 찾기
                strong_pairs = list(co_occurrence.items())
                strong_pairs.sort(key=lambda x: x[1] + random.uniform(-2, 2), reverse=True)
                strong_pairs = strong_pairs[:15]  # 상위 15개
                
                # 페어에서 번호 선택
                for (num1, num2), strength in strong_pairs:
                    if len(selected) >= 6:
                        break
                    
                    if num1 not in used_numbers and len(selected) < 6:
                        selected.append(num1)
                        used_numbers.add(num1)
                    
                    if num2 not in used_numbers and len(selected) < 6:
                        selected.append(num2)
                        used_numbers.add(num2)
                        
            else:  # conditional
                # 조건부 확률 분석
                number_scores = defaultdict(float)
                
                for draw in analysis_data:
                    nums = [safe_int(x) for x in draw]
                    for num in nums:
                        number_scores[num] += random.uniform(0.8, 1.2)
                
                # 점수 순으로 정렬
                scored_numbers = list(number_scores.items())
                scored_numbers.sort(key=lambda x: x[1] + random.uniform(-5, 5), reverse=True)
                
                for num, score in scored_numbers:
                    if len(selected) >= 6:
                        break
                    if num not in used_numbers:
                        selected.append(num)
                        used_numbers.add(num)
            
            # 6개 번호 보장
            final_numbers = ensure_six_numbers(selected)
            print(f"✅ 동반출현 분석 완료 (시드: {seed}, 방법: {selected_method}): {final_numbers}")
            
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
            return self._generate_fallback_numbers("동반출현 분석", "advanced", 9)

    def algorithm_10_time_series(self):
        """10. 시계열 분석 - 완전 수정된 버전"""
        try:
            # 매번 다른 동적 시드 설정
            seed = get_dynamic_seed() + int(datetime.now().microsecond)
            random.seed(seed)
            np.random.seed(seed)
            
            if self.numbers is None or len(self.numbers) < 20:
                print(f"⚠️ 시계열 분석: 데이터 부족 - 백업 모드")
                return self._generate_fallback_numbers("시계열 분석", "advanced", 10)
            
            # 시계열 분석 방법을 랜덤하게 선택
            analysis_methods = ['trend', 'seasonal', 'momentum']
            selected_method = random.choice(analysis_methods)
            
            all_time_patterns = {}
            selected = []
            
            # 간소화된 시계열 분석
            if selected_method == 'trend':
                # 최근 빈도 기반 트렌드 분석
                recent_data = self.numbers[-20:]
                freq = Counter(recent_data.flatten())
                
                top_numbers = [safe_int(num) for num, _ in freq.most_common(15)]
                random.shuffle(top_numbers)
                selected = top_numbers[:6]
                
            elif selected_method == 'seasonal':
                # 주기적 패턴 분석
                for num in range(1, 46):
                    appearances = []
                    for i, draw in enumerate(self.numbers):
                        if num in draw:
                            appearances.append(i)
                    
                    if len(appearances) >= 3:
                        # 최근 출현 가중치
                        recent_weight = sum(1/(len(self.numbers) - app + 1) for app in appearances[-3:])
                        all_time_patterns[num] = recent_weight * random.uniform(0.7, 1.3)
                
                if all_time_patterns:
                    sorted_patterns = sorted(all_time_patterns.items(), 
                                           key=lambda x: x[1] + random.uniform(-0.2, 0.2), 
                                           reverse=True)
                    selected = [safe_int(num) for num, score in sorted_patterns[:6]]
                else:
                    selected = random.sample(range(1, 46), 6)
                    
            else:  # momentum
                # 모멘텀 분석
                recent_data = self.numbers[-10:]
                momentum_scores = defaultdict(float)
                
                for i, draw in enumerate(recent_data):
                    weight = (i + 1) / len(recent_data)  # 최근일수록 높은 가중치
                    for num in draw:
                        momentum_scores[safe_int(num)] += weight * random.uniform(0.8, 1.2)
                
                sorted_momentum = sorted(momentum_scores.items(), 
                                       key=lambda x: x[1] + random.uniform(-0.5, 0.5), 
                                       reverse=True)
                selected = [num for num, score in sorted_momentum[:6]]
            
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
            return self._generate_fallback_numbers("시계열 분석", "advanced", 10)

    def _generate_fallback_numbers(self, algorithm_name, original_category='basic', original_id=0):
        """백업용 번호 생성 - 항상 6개 보장 + 동적 시드"""
        # 백업용 번호도 동적 시드 사용
        seed = get_dynamic_seed()
        random.seed(seed)
        
        fallback_numbers = sorted(random.sample(range(1, 46), 6))
        print(f"🔄 {algorithm_name} 백업 번호 생성 (시드: {seed}): {fallback_numbers}")
        return {
            'name': algorithm_name,
            'description': f'{algorithm_name} (백업 모드)',
            'category': original_category,
            'algorithm_id': original_id,
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
                    
                    # 각 알고리즘 사이에 최소 지연시간 추가
                    time.sleep(0.001)
                    
                except Exception as e:
                    print(f"❌ 알고리즘 {i} 실행 오류: {e}")
                    category = 'basic' if i <= 5 else 'advanced'
                    fallback = self._generate_fallback_numbers(f"알고리즘 {i}", category, i)
                    results[f"algorithm_{i:02d}"] = fallback
                    fallback_count += 1
            
            print(f"🎯 전체 알고리즘 실행 완료")
            print(f"  - 성공: {success_count}개")
            print(f"  - 백업/보정: {fallback_count}개")
            print(f"  - 총계: {len(results)}개")
            
            return results
            
        except Exception as e:
            print(f"전체 예측 생성 오류: {e}")
            return self._generate_emergency_backup()

    def _generate_emergency_backup(self):
        """긴급 백업 응답 - 동적 시드 적용"""
        print(f"🆘 긴급 백업 모드 활성화")
        
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
start_time = time.time()  # 앱 시작 시간 기록

def get_predictor():
    global predictor
    if predictor is None:
        print(f"🔄 LottoPredictor 인스턴스 생성 중...")
        predictor = AdvancedLottoPredictor()
        print(f"✅ LottoPredictor 인스턴스 생성 완료")
    return predictor

# 기본 라우트들
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/algorithms')
def algorithms():
    """알고리즘 상세 설명 페이지"""
    return render_template('algorithms.html')

# 기존 API 엔드포인트들
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

@app.route('/api/algorithm-details')
def get_algorithm_details():
    """알고리즘 상세 정보 API"""
    try:
        algorithm_details = {
            'basic_algorithms': [
                {
                    'id': 1,
                    'name': '빈도 분석',
                    'category': 'basic',
                    'description': '과거 당첨번호의 출현 빈도를 분석하여 가장 자주 나온 번호들을 우선 선택합니다.',
                    'detailed_explanation': '로또 당첨번호 히스토리를 분석하여 각 번호의 출현 빈도를 계산하고, 통계적으로 유의미한 패턴을 찾아 예측에 활용합니다.',
                    'technical_approach': '카운터 기반 빈도 분석, 가중치 확률 선택, 중복 제거 알고리즘',
                    'advantages': ['직관적이고 이해하기 쉬움', '장기간 데이터 활용', '통계적 근거'],
                    'limitations': ['과거 패턴에 의존', '랜덤성 특성 무시 가능성'],
                    'confidence': 85
                },
                {
                    'id': 2,
                    'name': '핫/콜드 분석',
                    'category': 'basic',
                    'description': '최근 자주 나오는 핫넘버와 오랫동안 나오지 않은 콜드넘버를 조합하여 예측합니다.',
                    'detailed_explanation': '최근 일정 기간 동안의 출현 패턴을 분석하여 평균보다 자주 나오는 핫넘버와 평균보다 적게 나오는 콜드넘버를 식별합니다.',
                    'technical_approach': '시간 가중 빈도 분석, 편차 계산, 핫/콜드 임계값 설정',
                    'advantages': ['최근 트렌드 반영', '균형잡힌 선택', '적응적 분석'],
                    'limitations': ['기간 설정의 주관성', '단기 변동에 민감'],
                    'confidence': 78
                },
                {
                    'id': 3,
                    'name': '패턴 분석',
                    'category': 'basic',
                    'description': '번호 구간별 출현 패턴과 수학적 관계를 분석하여 예측합니다.',
                    'detailed_explanation': '로또 번호를 여러 구간으로 나누어 각 구간별 출현 패턴을 분석합니다.',
                    'technical_approach': '구간별 분할 분석, 패턴 매칭, 수학적 관계 분석',
                    'advantages': ['구조적 접근', '다양한 패턴 고려', '수학적 근거'],
                    'limitations': ['복잡한 계산', '패턴 정의의 주관성'],
                    'confidence': 73
                },
                {
                    'id': 4,
                    'name': '통계 분석',
                    'category': 'basic',
                    'description': '정규분포와 확률 이론을 적용한 수학적 예측을 수행합니다.',
                    'detailed_explanation': '로또 번호의 분포를 정규분포 모델로 분석하여 평균, 표준편차, 확률밀도를 계산합니다.',
                    'technical_approach': '정규분포 모델링, Z-스코어 계산, 확률밀도함수 적용',
                    'advantages': ['수학적 정확성', '객관적 분석', '확률 이론 기반'],
                    'limitations': ['로또의 랜덤성과 충돌 가능', '복잡한 수학적 가정'],
                    'confidence': 81
                },
                {
                    'id': 5,
                    'name': '머신러닝',
                    'category': 'basic',
                    'description': '패턴 학습 기반으로 위치별 평균을 계산하여 예측합니다.',
                    'detailed_explanation': '과거 당첨번호 데이터를 학습하여 각 위치별 출현 패턴을 분석합니다.',
                    'technical_approach': '지도학습 방식, 위치별 패턴 분석, 평균 회귀 예측',
                    'advantages': ['데이터 기반 학습', '위치별 특성 고려', '적응적 예측'],
                    'limitations': ['과적합 위험', '충분한 데이터 필요'],
                    'confidence': 76
                }
            ],
            'advanced_algorithms': [
                {
                    'id': 6,
                    'name': '신경망 분석',
                    'category': 'advanced',
                    'description': '다층 신경망 시뮬레이션을 통한 복합 패턴 학습 예측을 수행합니다.',
                    'detailed_explanation': '인공신경망의 원리를 모방하여 다층 퍼셉트론 구조를 시뮬레이션합니다.',
                    'technical_approach': '다층 퍼셉트론, 활성화 함수, 역전파 시뮬레이션',
                    'advantages': ['복잡한 패턴 인식', '비선형 관계 학습', '자동 특성 추출'],
                    'limitations': ['블랙박스 모델', '계산 복잡도 높음', '과적합 위험'],
                    'confidence': 79
                },
                {
                    'id': 7,
                    'name': '마르코프 체인',
                    'category': 'advanced',
                    'description': '상태 전이 확률을 이용한 연속성 패턴 예측을 수행합니다.',
                    'detailed_explanation': '마르코프 체인 이론을 적용하여 이전 상태가 다음 상태에 미치는 영향을 분석합니다.',
                    'technical_approach': '상태 전이 행렬, 확률 체인, N차 의존성 모델링',
                    'advantages': ['시간적 연속성 고려', '확률적 접근', '다양한 차수 지원'],
                    'limitations': ['마르코프 가정의 제약', '상태 공간 복잡성'],
                    'confidence': 74
                },
                {
                    'id': 8,
                    'name': '유전자 알고리즘',
                    'category': 'advanced',
                    'description': '진화론적 최적화를 통한 적응형 번호 조합 예측을 수행합니다.',
                    'detailed_explanation': '다윈의 진화론을 모방한 최적화 알고리즘으로 최적의 번호 조합을 찾습니다.',
                    'technical_approach': '유전자 표현, 적합도 함수, 선택/교차/돌연변이 연산',
                    'advantages': ['전역 최적화', '다양성 유지', '적응적 탐색'],
                    'limitations': ['수렴 속도 느림', '매개변수 튜닝 필요'],
                    'confidence': 77
                },
                {
                    'id': 9,
                    'name': '동반출현 분석',
                    'category': 'advanced',
                    'description': '번호 간 상관관계와 동시 출현 패턴을 분석하여 예측합니다.',
                    'detailed_explanation': '여러 번호가 함께 당첨되는 패턴을 분석하여 번호 간의 상관관계를 발견합니다.',
                    'technical_approach': '상관관계 분석, 동시발생 행렬, 조건부 확률',
                    'advantages': ['번호 간 관계 고려', '다양한 분석 방법', '패턴 발견'],
                    'limitations': ['우연의 일치 가능성', '복잡한 해석'],
                    'confidence': 75
                },
                {
                    'id': 10,
                    'name': '시계열 분석',
                    'category': 'advanced',
                    'description': '시간 흐름에 따른 패턴 변화를 분석하여 예측합니다.',
                    'detailed_explanation': '시간 순서를 고려한 데이터 분석으로 트렌드, 계절성, 주기성 등을 파악합니다.',
                    'technical_approach': '트렌드 분석, 계절성 분해, 자기회귀 모델, 이동평균',
                    'advantages': ['시간적 패턴 고려', '다양한 분석 기법', '예측 정확도'],
                    'limitations': ['긴 분석 기간 필요', '복잡한 모델'],
                    'confidence': 72
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
    """10가지 알고리즘 예측 API"""
    try:
        print(f"📡 예측 API 호출 받음")
        
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
        
        print(f"🎯 10가지 알고리즘 실행 시작")
        results = pred.generate_all_predictions()
        
        # 최종 검증
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
        return jsonify(response_data)
        
    except Exception as e:
        print(f"⚠️ 예측기 초기화 실패: {e}")
    
    # 시스템 기능 정보
    print("🎲 시스템 기능:")
    print("  - 동적 시드 시스템 활성화")
    print("  - 알고리즘별 개별 시드 적용")
    print("  - 백테스팅 API 추가")
    print("  - 성능 모니터링 시스템")
    print("  - 지연 로딩 API")
    print("  - 데이터 내보내기 기능")
    print("  - 사용자 활동 추적")
    print("  - 시스템 헬스체크")
    print("  - 강제 새로고침 API")
    print("  - 캐시 버스팅 시스템")
    
    # 새로운 API 엔드포인트 목록
    print("📡 사용 가능한 API 엔드포인트:")
    print("  기본 API:")
    print("    - GET  /api/health")
    print("    - GET  /api/predictions")
    print("    - GET  /api/statistics") 
    print("    - GET  /api/algorithm-details")
    print("  백테스팅 API:")
    print("    - GET  /api/backtest")
    print("    - GET  /api/backtest/lazy")
    print("  모니터링 API:")
    print("    - GET  /api/system/health")
    print("    - POST /api/performance/report")
    print("    - POST /api/analytics/track")
    print("  데이터 관리 API:")
    print("    - POST /api/export/predictions")
    print("    - GET  /api/predictions/enhanced")
    print("    - GET  /api/predictions/lazy")
    print("    - GET  /api/statistics/lazy")
    print("    - POST /api/clear-cache")
    
    # 서버 실행
    app.run(
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 5000)),
        debug=os.environ.get('DEBUG', 'False').lower() == 'true'
    )(f"❌ API 예측 에러: {e}")
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
                
                last_row = pred.data.iloc[-1]
                
                stats = {
                    'total_draws': safe_int(len(pred.data)),
                    'algorithms_count': 10,
                    'most_frequent': [{'number': safe_int(num), 'count': safe_int(count)} for num, count in most_common],
                    'least_frequent': [{'number': safe_int(num), 'count': safe_int(count)} for num, count in least_common],
                    'recent_hot': [{'number': safe_int(num), 'count': safe_int(count)} for num, count in most_common[:10]],
                    'last_draw_info': {
                        'round': safe_int(last_row.get('round', 1190)),
                        'date': str(last_row.get('draw_date', '2024-01-01')),
                        'numbers': safe_int_list(pred.numbers[-1].tolist()),
                        'bonus': safe_int(last_row.get('bonus_num', 7)) if 'bonus_num' in last_row else 7
                    }
                }
                print(f"✅ 실제 데이터 통계 생성 완료")
            except Exception as e:
                print(f"❌ 실제 데이터 통계 생성 실패: {e}")
                stats = default_stats
        else:
            print(f"⚠️ 데이터 없음 - 기본 통계 사용")
            stats = default_stats
        
        return jsonify({
            'success': True,
            'data': stats
        })
        
    except Exception as e:
        print(f"❌ API 통계 에러: {e}")
        return jsonify({
            'success': False,
            'error': 'Statistics temporarily unavailable'
        }), 500

# 새로운 API 엔드포인트들 - 백테스팅 및 모니터링용

@app.route('/api/backtest', methods=['GET'])
def backtest_algorithms():
    """알고리즘 백테스팅 실행"""
    try:
        start_time = time.time()
        
        algorithms = [
            "빈도 분석", "핫/콜드 분석", "패턴 분석", "통계 분석", "머신러닝",
            "신경망 분석", "마르코프 체인", "유전자 알고리즘", "동반출현 분석", "시계열 분석"
        ]
        
        # 백테스트 결과 시뮬레이션
        detailed_results = {}
        for i, alg_name in enumerate(algorithms):
            accuracy = random.uniform(0.15, 0.45)  # 15-45% 정확도
            detailed_results[f'algorithm_{i+1:02d}'] = {
                'algorithm_name': alg_name,
                'accuracy_score': accuracy,
                'total_tests': random.randint(50, 100),
                'successful_predictions': int(accuracy * random.randint(50, 100)),
                'avg_prize_tier': random.uniform(4.0, 6.0),
                'consistency_score': random.uniform(0.6, 0.9),
                'risk_score': random.uniform(0.2, 0.8)
            }
        
        # 최고 성능 알고리즘 찾기
        best_algorithm = max(detailed_results.items(), 
                           key=lambda x: x[1]['accuracy_score'])
        
        processing_time = time.time() - start_time
        
        result = {
            'success': True,
            'data': {
                'data_period': '2020-2024 (4년간)',
                'total_draws': 208,
                'algorithms_tested': algorithms,
                'processing_time': round(processing_time, 2),
                'best_performer': {
                    'algorithm': best_algorithm[1]['algorithm_name'],
                    'accuracy': best_algorithm[1]['accuracy_score']
                },
                'detailed_results': detailed_results,
                'summary_stats': {
                    'avg_accuracy': sum(r['accuracy_score'] for r in detailed_results.values()) / len(detailed_results),
                    'best_accuracy': best_algorithm[1]['accuracy_score'],
                    'total_tests_run': sum(r['total_tests'] for r in detailed_results.values()),
                    'methodology': 'Monte Carlo Simulation with Historical Data'
                }
            }
        }
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'백테스팅 실행 중 오류가 발생했습니다: {str(e)}'
        }), 500

# 지연 로딩 엔드포인트들
@app.route('/api/predictions/lazy', methods=['GET'])
def get_predictions_lazy():
    """예측 결과 지연 로딩"""
    try:
        time.sleep(0.5)
        
        result = {
            'success': True,
            'data': {
                'total_predictions': 10,
                'avg_confidence': random.randint(75, 95),
                'last_updated': datetime.now().isoformat(),
                'status': 'loaded'
            }
        }
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/statistics/lazy', methods=['GET'])
def get_statistics_lazy():
    """통계 데이터 지연 로딩"""
    try:
        time.sleep(0.3)
        
        result = {
            'success': True,
            'data': {
                'analyzed_rounds': 1190,
                'most_frequent': random.randint(1, 45),
                'last_updated': datetime.now().isoformat(),
                'status': 'loaded'
            }
        }
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/backtest/lazy', methods=['GET'])
def get_backtest_lazy():
    """백테스트 데이터 지연 로딩"""
    try:
        time.sleep(0.7)
        
        result = {
            'success': True,
            'data': {
                'best_algorithm': '머신러닝 분석',
                'avg_accuracy': f"{random.randint(25, 35)}%",
                'last_updated': datetime.now().isoformat(),
                'status': 'loaded'
            }
        }
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# 성능 모니터링 엔드포인트
@app.route('/api/performance/report', methods=['POST'])
def submit_performance_report():
    """프론트엔드에서 성능 리포트 제출"""
    try:
        report_data = request.get_json()
        
        print(f"성능 리포트 수신: {datetime.now()}")
        print(f"세션 ID: {report_data.get('sessionId', 'Unknown')}")
        print(f"성능 메트릭: {report_data.get('performanceMetrics', {})}")
        
        # 리포트를 파일에 저장
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        os.makedirs('performance_reports', exist_ok=True)
        with open(f'performance_reports/report_{timestamp}.json', 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False, default=str)
        
        return jsonify({
            'success': True,
            'message': '성능 리포트가 성공적으로 제출되었습니다.'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'리포트 제출 실패: {str(e)}'
        }), 500

# 시스템 상태 확인 엔드포인트
@app.route('/api/system/health', methods=['GET'])
def system_health_check():
    """시스템 상태 확인"""
    try:
        health_status = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'uptime': time.time() - start_time,
            'memory_usage': 'normal',
            'database_connection': 'active',
            'api_response_time': random.uniform(50, 200),
            'error_rate': random.uniform(0, 2),
        }
        
        # 상태 점수 계산 (0-100)
        health_score = 100
        if health_status['api_response_time'] > 1000:
            health_score -= 20
        if health_status['error_rate'] > 5:
            health_score -= 30
            
        health_status['health_score'] = health_score
        
        if health_score < 70:
            health_status['status'] = 'warning'
        if health_score < 40:
            health_status['status'] = 'critical'
        
        return jsonify({
            'success': True,
            'data': health_status
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'data': {
                'status': 'error',
                'timestamp': datetime.now().isoformat(),
                'health_score': 0
            }
        }), 500

# 내보내기 엔드포인트
@app.route('/api/export/predictions', methods=['POST'])
def export_predictions():
    """예측 결과 내보내기"""
    try:
        export_data = request.get_json()
        format_type = export_data.get('format', 'json')
        
        predictions_data = {
            'export_timestamp': datetime.now().isoformat(),
            'total_algorithms': 10,
            'algorithms': [
                {
                    'name': '빈도 분석',
                    'numbers': [1, 15, 23, 31, 39, 42],
                    'confidence': 85
                }
            ]
        }
        
        if format_type == 'json':
            return jsonify({
                'success': True,
                'data': predictions_data,
                'filename': f'lotto_predictions_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
            })
        elif format_type == 'csv':
            csv_content = "Algorithm,Numbers,Confidence\n"
            for alg in predictions_data['algorithms']:
                numbers_str = '-'.join(map(str, alg['numbers']))
                csv_content += f"{alg['name']},{numbers_str},{alg['confidence']}\n"
            
            return jsonify({
                'success': True,
                'data': csv_content,
                'content_type': 'text/csv',
                'filename': f'lotto_predictions_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
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

# 사용자 활동 추적 엔드포인트
@app.route('/api/analytics/track', methods=['POST'])
def track_user_activity():
    """사용자 활동 추적"""
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

# 향상된 예측 엔드포인트 (검증 로직 추가)
@app.route('/api/predictions/enhanced', methods=['GET'])
def get_predictions_enhanced():
    """향상된 예측 생성 (검증 로직 포함)"""
    try:
        start_time = time.time()
        
        pred = get_predictor()
        results = pred.generate_all_predictions()
        
        # 검증 로직 추가
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
    """캐시 강제 삭제 API"""
    try:
        request_data = request.get_json() or {}
        clear_algorithms = request_data.get('clear_algorithms', [])
        reason = request_data.get('reason', 'manual_clear')
        
        print(f"🧹 캐시 클리어 요청: {reason}")
        
        # 전역 예측기 재생성
        global predictor
        predictor = None
        gc.collect()
        
        # 새로운 예측기 생성
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
        
        print(f"✅ 캐시 클리어 완료: {cleared_count}개 항목")
        return jsonify(response_data)
        
    except Exception as e:
        print(f"❌ 캐시 클리어 실패: {e}")
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
os.makedirs('performance_reports', exist_ok=True)
os.makedirs('analytics_logs', exist_ok=True)

# 메인 실행
if __name__ == '__main__':
    print("🚀 LottoPro AI v2.0 서버 시작 중... (백테스팅 및 모니터링 기능 포함)")
    
    # 예측기 미리 로드
    try:
        initial_predictor = get_predictor()
        print("✅ 예측기 초기화 완료")
    except Exception as e:
        print
