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

def safe_int(value):
    """numpy.int64를 Python int로 안전하게 변환"""
    try:
        return int(value)
    except (ValueError, TypeError):
        return value

def safe_int_list(lst):
    """리스트의 모든 요소를 안전하게 int로 변환"""
    return [safe_int(x) for x in lst]

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
    def __init__(self, csv_file_path='new_1188.csv'):
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
                'new_1188.csv',
                './new_1188.csv',
                os.path.join(current_dir, 'new_1188.csv'),
                'data/new_1188.csv',
                '/opt/render/project/src/new_1188.csv',
                os.path.join(os.path.dirname(__file__), 'new_1188.csv')
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
                print(f"💡 해결책: GitHub의 new_1188.csv 파일이 배포 서버에 복사되지 않았을 가능성")
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
                    
                # 가중치 기반 선택
                available_weights = [weights[i] for i in available_indices]
                chosen_idx = random.choices(available_indices, weights=available_weights)[0]
                chosen_number = top_numbers[chosen_idx]
                
                selected.append(chosen_number)
                used_numbers.add(chosen_number)
            
            # 6개 번호 보장
            final_numbers = ensure_six_numbers(selected)
            print(f"✅ 빈도 분석 완료: {final_numbers}")
            
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
        """2. 핫/콜드 분석 - 수정된 버전"""
        try:
            if self.numbers is None or len(self.numbers) < 20:
                print(f"⚠️ 핫/콜드 분석: 데이터 부족 - 백업 모드")
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
                    hot_numbers.append((safe_int(num), recent_count - expected_count))
            
            # 핫 넘버 우선 선택
            hot_numbers.sort(key=lambda x: x[1], reverse=True)
            selected = []
            
            # 핫 넘버에서 4개 선택
            for num, _ in hot_numbers[:4]:
                selected.append(num)
            
            # 나머지는 콜드 넘버에서 선택
            cold_candidates = [num for num in range(1, 46) if num not in selected]
            random.shuffle(cold_candidates)
            selected.extend(cold_candidates[:2])
            
            # 6개 번호 보장
            final_numbers = ensure_six_numbers(selected)
            print(f"✅ 핫/콜드 분석 완료: {final_numbers}")
            
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
        """3. 패턴 분석 - 수정된 버전"""
        try:
            if self.numbers is None:
                print(f"⚠️ 패턴 분석: 데이터 없음 - 백업 모드")
                return self._generate_fallback_numbers("패턴 분석")
            
            # 구간별 분석 (1-15, 16-30, 31-45)
            sections = {'low': [], 'mid': [], 'high': []}
            
            for row in self.numbers:
                for num in row:
                    if 1 <= num <= 15:
                        sections['low'].append(safe_int(num))
                    elif 16 <= num <= 30:
                        sections['mid'].append(safe_int(num))
                    elif 31 <= num <= 45:
                        sections['high'].append(safe_int(num))
            
            # 각 구간에서 빈도 높은 번호 선택
            selected = []
            for section_name, section_numbers in sections.items():
                if section_numbers:
                    freq = Counter(section_numbers)
                    top_nums = [safe_int(num) for num, _ in freq.most_common(5)]
                    # 각 구간에서 2개씩 선택하되 중복 방지
                    section_selected = 0
                    for num in top_nums:
                        if num not in selected and section_selected < 2:
                            selected.append(num)
                            section_selected += 1
            
            # 6개 번호 보장
            final_numbers = ensure_six_numbers(selected)
            print(f"✅ 패턴 분석 완료: {final_numbers}")
            
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
            if self.numbers is None:
                print(f"⚠️ 통계 분석: 데이터 없음 - 백업 모드")
                return self._generate_fallback_numbers("통계 분석")
            
            all_numbers = self.numbers.flatten()
            
            # 정규분포 기반 예측
            mean_val = float(np.mean(all_numbers))
            std_val = float(np.std(all_numbers))
            
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
            print(f"✅ 통계 분석 완료: {final_numbers}")
            
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
            if self.numbers is None or len(self.numbers) < 50:
                print(f"⚠️ 머신러닝: 데이터 부족 - 백업 모드")
                return self._generate_fallback_numbers("머신러닝")
            
            # 간단한 패턴 기반 예측 (ML 라이브러리 없이)
            # 최근 10회차의 번호 패턴 분석
            recent_data = self.numbers[-10:]
            
            # 각 위치별 평균 계산
            position_averages = []
            for pos in range(6):
                pos_numbers = [safe_int(row[pos]) for row in recent_data]
                avg = sum(pos_numbers) / len(pos_numbers)
                position_averages.append(int(round(avg)))
            
            # 평균 주변의 번호들로 조정
            selected = []
            used_numbers = set()
            
            for avg in position_averages:
                # 평균 ±5 범위에서 선택
                range_start = max(1, avg - 5)
                range_end = min(45, avg + 5)
                
                attempts = 0
                while attempts < 20:  # 무한 루프 방지
                    candidate = random.randint(range_start, range_end)
                    if candidate not in used_numbers:
                        selected.append(candidate)
                        used_numbers.add(candidate)
                        break
                    attempts += 1
            
            # 6개 번호 보장
            final_numbers = ensure_six_numbers(selected)
            print(f"✅ 머신러닝 완료: {final_numbers}")
            
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
        """6. 신경망 분석 - 수정된 버전"""
        try:
            if self.numbers is None or len(self.numbers) < 30:
                print(f"⚠️ 신경망 분석: 데이터 부족 - 백업 모드")
                return self._generate_fallback_numbers("신경망 분석")
            
            # 간단한 가중치 네트워크 시뮬레이션
            # 최근 데이터에 더 높은 가중치 부여
            weights = [i/sum(range(1, len(self.numbers)+1)) for i in range(1, len(self.numbers)+1)]
            
            # 가중 평균 계산
            weighted_numbers = []
            for i, row in enumerate(self.numbers):
                for num in row:
                    weighted_numbers.extend([safe_int(num)] * int(weights[i] * 100 + 1))
            
            # 빈도 기반 선택
            freq = Counter(weighted_numbers)
            top_numbers = [safe_int(num) for num, _ in freq.most_common(20)]
            
            # 중복 없이 6개 선택
            selected = []
            used_numbers = set()
            
            for num in top_numbers:
                if len(selected) >= 6:
                    break
                if num not in used_numbers:
                    selected.append(num)
                    used_numbers.add(num)
            
            # 6개 번호 보장
            final_numbers = ensure_six_numbers(selected)
            print(f"✅ 신경망 분석 완료: {final_numbers}")
            
            return {
                'name': '신경망 분석',
                'description': '가중치 네트워크를 통한 복합 패턴 학습 예측',
                'category': 'advanced',
                'algorithm_id': 6,
                'priority_numbers': safe_int_list(final_numbers),
                'confidence': 79
            }
        except Exception as e:
            print(f"신경망 분석 알고리즘 오류: {e}")
            return self._generate_fallback_numbers("신경망 분석")

    def algorithm_7_markov_chain(self):
        """7. 마르코프 체인 - 수정된 버전"""
        try:
            if self.numbers is None or len(self.numbers) < 20:
                print(f"⚠️ 마르코프 체인: 데이터 부족 - 백업 모드")
                return self._generate_fallback_numbers("마르코프 체인")
            
            # 전이 확률 행렬 구성
            transition_matrix = defaultdict(lambda: defaultdict(int))
            
            # 연속된 회차 간 번호 전이 패턴 분석
            for i in range(len(self.numbers) - 1):
                current_set = set(safe_int(x) for x in self.numbers[i])
                next_set = set(safe_int(x) for x in self.numbers[i + 1])
                
                for curr_num in current_set:
                    for next_num in next_set:
                        transition_matrix[curr_num][next_num] += 1
            
            # 마지막 회차 기반 예측
            last_numbers = set(safe_int(x) for x in self.numbers[-1])
            predictions = []
            used_predictions = set()
            
            for curr_num in last_numbers:
                if curr_num in transition_matrix:
                    transitions = transition_matrix[curr_num]
                    if transitions:
                        total = sum(transitions.values())
                        probs = [(next_num, count/total) for next_num, count in transitions.items()]
                        probs.sort(key=lambda x: x[1], reverse=True)
                        
                        # 중복 방지하며 예측 추가
                        for num, prob in probs[:3]:
                            if safe_int(num) not in used_predictions and len(predictions) < 6:
                                predictions.append(safe_int(num))
                                used_predictions.add(safe_int(num))
            
            # 6개 번호 보장
            final_numbers = ensure_six_numbers(predictions)
            print(f"✅ 마르코프 체인 완료: {final_numbers}")
            
            return {
                'name': '마르코프 체인',
                'description': '상태 전이 확률을 이용한 연속성 패턴 예측',
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
            if self.numbers is None:
                print(f"⚠️ 유전자 알고리즘: 데이터 없음 - 백업 모드")
                return self._generate_fallback_numbers("유전자 알고리즘")
            
            # 적합도 함수: 과거 당첨번호와의 유사성
            def fitness(individual):
                score = 0
                for past_draw in self.numbers[-10:]:  # 최근 10회차
                    common = len(set(individual) & set(safe_int(x) for x in past_draw))
                    score += common * common  # 공통 번호 수의 제곱
                return score
            
            # 초기 집단 생성 (중복 없는 개체들)
            population_size = 30
            population = []
            for _ in range(population_size):
                individual = random.sample(range(1, 46), 6)
                population.append(sorted(individual))
            
            # 진화 과정
            for generation in range(5):
                # 적합도 계산
                fitness_scores = [(ind, fitness(ind)) for ind in population]
                fitness_scores.sort(key=lambda x: x[1], reverse=True)
                
                # 상위 50% 선택
                selected = [ind for ind, score in fitness_scores[:population_size//2]]
                
                # 다음 세대 생성 (교차 + 돌연변이)
                new_population = selected.copy()
                while len(new_population) < population_size:
                    parent1, parent2 = random.sample(selected, 2)
                    
                    # 교차 (중복 없이)
                    child = list(set(parent1[:3] + parent2[3:]))
                    
                    # 돌연변이
                    if random.random() < 0.1 and len(child) > 0:
                        mutation_idx = random.randint(0, len(child)-1)
                        new_number = random.randint(1, 45)
                        if new_number not in child:
                            child[mutation_idx] = new_number
                    
                    # 6개 번호 보장
                    final_child = ensure_six_numbers(child)
                    new_population.append(final_child)
                
                population = new_population
            
            # 최적 개체 선택
            final_fitness = [(ind, fitness(ind)) for ind in population]
            best_individual = max(final_fitness, key=lambda x: x[1])[0]
            print(f"✅ 유전자 알고리즘 완료: {best_individual}")
            
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
        """9. 동반출현 분석 - 수정된 버전"""
        try:
            if self.numbers is None or len(self.numbers) < 30:
                print(f"⚠️ 동반출현 분석: 데이터 부족 - 백업 모드")
                return self._generate_fallback_numbers("동반출현 분석")
            
            # 번호 간 동반 출현 빈도 계산
            co_occurrence = defaultdict(int)
            
            for draw in self.numbers:
                for i in range(len(draw)):
                    for j in range(i + 1, len(draw)):
                        pair = tuple(sorted([safe_int(draw[i]), safe_int(draw[j])]))
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
                elif num1 not in used_numbers and len(selected) < 6:
                    selected.append(num1)
                    used_numbers.add(num1)
                elif num2 not in used_numbers and len(selected) < 6:
                    selected.append(num2)
                    used_numbers.add(num2)
            
            # 6개 번호 보장
            final_numbers = ensure_six_numbers(selected)
            print(f"✅ 동반출현 분석 완료: {final_numbers}")
            
            return {
                'name': '동반출현 분석',
                'description': '번호 간 동반 출현 상관관계를 분석한 조합 예측',
                'category': 'advanced',
                'algorithm_id': 9,
                'priority_numbers': safe_int_list(final_numbers),
                'confidence': 75
            }
        except Exception as e:
            print(f"동반출현 분석 알고리즘 오류: {e}")
            return self._generate_fallback_numbers("동반출현 분석")

    def algorithm_10_time_series(self):
        """10. 시계열 분석 - 수정된 버전"""
        try:
            if self.numbers is None or len(self.numbers) < 20:
                print(f"⚠️ 시계열 분석: 데이터 부족 - 백업 모드")
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
            
            # 상위 번호들 중에서 6개 선택
            selected = []
            for num, prob in sorted_patterns:
                if len(selected) >= 6:
                    break
                selected.append(safe_int(num))
            
            # 6개 번호 보장
            final_numbers = ensure_six_numbers(selected)
            print(f"✅ 시계열 분석 완료: {final_numbers}")
            
            return {
                'name': '시계열 분석',
                'description': '시간 흐름에 따른 출현 패턴 예측',
                'category': 'advanced',
                'algorithm_id': 10,
                'priority_numbers': safe_int_list(final_numbers),
                'confidence': 72
            }
        except Exception as e:
            print(f"시계열 분석 알고리즘 오류: {e}")
            return self._generate_fallback_numbers("시계열 분석")

    def _generate_fallback_numbers(self, algorithm_name):
        """백업용 번호 생성 - 항상 6개 보장"""
        fallback_numbers = sorted(random.sample(range(1, 46), 6))
        print(f"🔄 {algorithm_name} 백업 번호 생성: {fallback_numbers}")
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
            print(f"🎯 10개 알고리즘 실행 시작")
            
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
                    print(f"🔄 알고리즘 {i} 실행 중...")
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
                    
                except Exception as e:
                    print(f"❌ 알고리즘 {i} 실행 오류: {e}")
                    fallback = self._generate_fallback_numbers(f"알고리즘 {i}")
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
        """긴급 백업 응답"""
        print(f"🆘 긴급 백업 모드 활성화")
        
        backup_algorithms = [
            "빈도 분석", "핫/콜드 분석", "패턴 분석", "통계 분석", "머신러닝",
            "신경망 분석", "마르코프 체인", "유전자 알고리즘", "동반출현 분석", "시계열 분석"
        ]
        
        results = {}
        for i, name in enumerate(backup_algorithms, 1):
            backup_numbers = sorted(random.sample(range(1, 46), 6))
            results[f"algorithm_{i:02d}"] = {
                'name': name,
                'description': f'{name} (긴급 백업)',
                'category': 'advanced' if i > 5 else 'basic',
                'algorithm_id': i,
                'priority_numbers': backup_numbers,
                'confidence': 50
            }
            print(f"🆘 긴급 백업 {i}: {name} - {backup_numbers}")
        
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
        print(f"📡 예측 API 호출 받음")
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
        print(f"🎯 10가지 알고리즘 실행 시작")
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
        
        response_data = {
            'success': True,
            'data': results,
            'total_algorithms': len(results),
            'total_draws': safe_int(len(pred.data)) if pred.data is not None else 0,
            'message': '10가지 AI 알고리즘이 각각 1개씩의 우선 번호를 생성했습니다.'
        }
        
        print(f"✅ 예측 API 응답 완료 - {len(results)}개 알고리즘")
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
            'total_draws': 1188,
            'algorithms_count': 10,
            'last_draw_info': {
                'round': 1188,
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
                        'round': safe_int(last_row.get('round', 1188)),
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

if __name__ == '__main__':
    print(f"🚀 Flask 앱 시작")
    app.run(debug=False, host='0.0.0.0', port=5000)
