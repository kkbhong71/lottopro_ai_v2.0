from flask import Flask, render_template, request, jsonify
import pandas as pd
import numpy as np
import random
from collections import Counter, defaultdict
from sklearn.ensemble import RandomForestRegressor
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.metrics import mean_squared_error
import os
import json
from datetime import datetime, timedelta
import itertools
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

app = Flask(__name__)

class LottoPredictor:
    def __init__(self, csv_file_path='new_1187.csv'):
        self.csv_file_path = csv_file_path
        self.data = None
        self.load_data()
    
    def load_data(self):
        """CSV 파일에서 당첨번호 데이터 로드"""
        try:
            self.data = pd.read_csv(self.csv_file_path)
            # 컬럼명 정규화
            self.data.columns = ['round', 'draw_date', 'num1', 'num2', 'num3', 'num4', 'num5', 'num6', 'bonus_num']
            # 번호 컬럼들만 추출
            self.numbers = self.data[['num1', 'num2', 'num3', 'num4', 'num5', 'num6']].values
            print(f"✅ 데이터 로드 완료: {len(self.data)}개 회차")
        except Exception as e:
            print(f"❌ 데이터 로드 실패: {e}")
    
    def frequency_analysis_algorithm(self):
        """빈도 분석 알고리즘 - 자주 나온 번호 기반"""
        try:
            all_numbers = self.numbers.flatten()
            frequency = Counter(all_numbers)
            most_common = [num for num, count in frequency.most_common(20)]
            
            predictions = []
            for _ in range(5):
                selected = []
                weights = [frequency[num] for num in most_common]
                
                while len(selected) < 6:
                    chosen = np.random.choice(most_common, p=np.array(weights)/sum(weights))
                    if chosen not in selected:
                        selected.append(int(chosen))
                
                predictions.append(sorted(selected))
            
            return predictions
        except Exception as e:
            print(f"빈도분석 알고리즘 오류: {e}")
            return self.generate_random_numbers(5)
    
    def hot_cold_algorithm(self):
        """핫/콜드 번호 알고리즘 - 최근 출현 패턴 기반"""
        try:
            recent_draws = 20
            recent_data = self.numbers[-recent_draws:]
            recent_numbers = recent_data.flatten()
            
            hot_counter = Counter(recent_numbers)
            hot_numbers = [num for num, count in hot_counter.most_common(15)]
            
            all_numbers_set = set(range(1, 46))
            recent_numbers_set = set(recent_numbers)
            cold_numbers = list(all_numbers_set - recent_numbers_set)
            
            if len(cold_numbers) < 10:
                all_counter = Counter(self.numbers.flatten())
                least_common = [num for num, count in all_counter.most_common()[:-11:-1]]
                cold_numbers.extend(least_common)
            
            predictions = []
            for _ in range(5):
                hot_count = random.randint(3, 4)
                hot_selected = random.sample(hot_numbers[:12], min(hot_count, len(hot_numbers[:12])))
                cold_selected = random.sample(cold_numbers[:10], 6 - len(hot_selected))
                
                selected = hot_selected + cold_selected
                while len(selected) < 6:
                    selected.append(random.randint(1, 45))
                
                predictions.append(sorted(list(set(selected))[:6]))
            
            return predictions
        except Exception as e:
            print(f"핫콜드 알고리즘 오류: {e}")
            return self.generate_random_numbers(5)
    
    def pattern_analysis_algorithm(self):
        """패턴 분석 알고리즘 - 번호 간격과 분포 패턴 분석"""
        try:
            predictions = []
            recent_data = self.numbers[-30:]
            
            zones = [0, 0, 0, 0, 0]
            for draw in recent_data:
                for num in draw:
                    if 1 <= num <= 10: zones[0] += 1
                    elif 11 <= num <= 20: zones[1] += 1
                    elif 21 <= num <= 30: zones[2] += 1
                    elif 31 <= num <= 40: zones[3] += 1
                    elif 41 <= num <= 45: zones[4] += 1
            
            total = sum(zones)
            zone_probs = [z/total for z in zones] if total > 0 else [0.2] * 5
            
            for _ in range(5):
                selected = []
                for i, prob in enumerate(zone_probs):
                    zone_count = max(1, int(prob * 6))
                    if i == 0: zone_range = list(range(1, 11))
                    elif i == 1: zone_range = list(range(11, 21))
                    elif i == 2: zone_range = list(range(21, 31))
                    elif i == 3: zone_range = list(range(31, 41))
                    else: zone_range = list(range(41, 46))
                    
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
            return self.generate_random_numbers(5)
    
    def statistical_algorithm(self):
        """통계적 분석 알고리즘 - 평균, 표준편차, 상관관계 기반"""
        try:
            predictions = []
            position_stats = []
            
            for pos in range(6):
                pos_numbers = self.numbers[:, pos]
                mean = np.mean(pos_numbers)
                std = np.std(pos_numbers)
                position_stats.append({'mean': mean, 'std': std})
            
            for _ in range(5):
                selected = []
                for pos, stats in enumerate(position_stats):
                    num = int(np.random.normal(stats['mean'], stats['std']))
                    num = max(1, min(45, num))
                    
                    attempts = 0
                    while num in selected and attempts < 100:
                        num = int(np.random.normal(stats['mean'], stats['std']))
                        num = max(1, min(45, num))
                        attempts += 1
                    
                    if num not in selected:
                        selected.append(num)
                
                while len(selected) < 6:
                    num = random.randint(1, 45)
                    if num not in selected:
                        selected.append(num)
                
                predictions.append(sorted(selected[:6]))
            
            return predictions
        except Exception as e:
            print(f"통계분석 알고리즘 오류: {e}")
            return self.generate_random_numbers(5)
    
    def machine_learning_algorithm(self):
        """머신러닝 알고리즘 - 랜덤포레스트 기반 예측"""
        try:
            if len(self.numbers) < 50:
                return self.generate_random_numbers(5)
            
            window_size = 10
            X, y = [], []
            
            for i in range(window_size, len(self.numbers)):
                features = self.numbers[i-window_size:i].flatten()
                target = self.numbers[i]
                X.append(features)
                y.append(target)
            
            X = np.array(X)
            y = np.array(y)
            
            predictions = []
            for _ in range(5):
                prediction_set = []
                
                for pos in range(6):
                    try:
                        model = RandomForestRegressor(n_estimators=50, random_state=random.randint(1, 1000))
                        model.fit(X, y[:, pos])
                        
                        last_features = self.numbers[-window_size:].flatten().reshape(1, -1)
                        pred = model.predict(last_features)[0]
                        pred = max(1, min(45, int(round(pred))))
                        
                        if pred not in prediction_set:
                            prediction_set.append(pred)
                    except:
                        num = random.randint(1, 45)
                        if num not in prediction_set:
                            prediction_set.append(num)
                
                while len(prediction_set) < 6:
                    num = random.randint(1, 45)
                    if num not in prediction_set:
                        prediction_set.append(num)
                
                predictions.append(sorted(prediction_set[:6]))
            
            return predictions
        except Exception as e:
            print(f"머신러닝 알고리즘 오류: {e}")
            return self.generate_random_numbers(5)
    
    def neural_network_algorithm(self):
        """신경망 알고리즘 - 딥러닝 기반 패턴 학습"""
        try:
            if len(self.numbers) < 100:
                return self.generate_random_numbers(5)
            
            # 특성 생성: 최근 번호들의 패턴을 학습
            window_size = 15
            X, y = [], []
            
            for i in range(window_size, len(self.numbers)):
                features = []
                # 이전 회차들의 번호 패턴
                for j in range(window_size):
                    prev_numbers = self.numbers[i-j-1]
                    features.extend(prev_numbers)
                    # 번호간 차이값도 추가
                    if j < window_size - 1:
                        features.extend(np.diff(sorted(prev_numbers)))
                
                X.append(features)
                y.append(self.numbers[i])
            
            X = np.array(X)
            y = np.array(y)
            
            # 정규화
            scaler_X = StandardScaler()
            X_scaled = scaler_X.fit_transform(X)
            
            predictions = []
            for _ in range(5):
                prediction_set = []
                
                for pos in range(6):
                    try:
                        # 신경망 모델
                        model = MLPRegressor(
                            hidden_layer_sizes=(100, 50, 25),
                            activation='relu',
                            max_iter=200,
                            random_state=random.randint(1, 1000),
                            alpha=0.01
                        )
                        
                        model.fit(X_scaled, y[:, pos])
                        
                        # 최근 데이터로 예측
                        last_features = []
                        for j in range(window_size):
                            prev_numbers = self.numbers[-(j+1)]
                            last_features.extend(prev_numbers)
                            if j < window_size - 1:
                                last_features.extend(np.diff(sorted(prev_numbers)))
                        
                        last_features_scaled = scaler_X.transform([last_features])
                        pred = model.predict(last_features_scaled)[0]
                        pred = max(1, min(45, int(round(pred))))
                        
                        if pred not in prediction_set:
                            prediction_set.append(pred)
                    except:
                        num = random.randint(1, 45)
                        if num not in prediction_set:
                            prediction_set.append(num)
                
                while len(prediction_set) < 6:
                    num = random.randint(1, 45)
                    if num not in prediction_set:
                        prediction_set.append(num)
                
                predictions.append(sorted(prediction_set[:6]))
            
            return predictions
        except Exception as e:
            print(f"신경망 알고리즘 오류: {e}")
            return self.generate_random_numbers(5)
    
    def markov_chain_algorithm(self):
        """마르코프 체인 알고리즘 - 상태 전이 확률 기반 예측"""
        try:
            # 상태 전이 매트릭스 구축
            transitions = defaultdict(lambda: defaultdict(int))
            
            for i in range(len(self.numbers) - 1):
                current_state = tuple(sorted(self.numbers[i]))
                next_state = tuple(sorted(self.numbers[i + 1]))
                
                # 각 번호별 전이 확률 계산
                for curr_num in current_state:
                    for next_num in next_state:
                        transitions[curr_num][next_num] += 1
            
            # 전이 확률 정규화
            for curr_num in transitions:
                total = sum(transitions[curr_num].values())
                if total > 0:
                    for next_num in transitions[curr_num]:
                        transitions[curr_num][next_num] /= total
            
            predictions = []
            for _ in range(5):
                # 최근 당첨번호를 시작 상태로 사용
                last_numbers = sorted(self.numbers[-1])
                selected = []
                
                for _ in range(6):
                    if not last_numbers:
                        selected.append(random.randint(1, 45))
                        continue
                    
                    # 각 번호에서 다음 번호로의 전이 확률 계산
                    next_probs = defaultdict(float)
                    for curr_num in last_numbers:
                        if curr_num in transitions:
                            for next_num, prob in transitions[curr_num].items():
                                if next_num not in selected:
                                    next_probs[next_num] += prob
                    
                    if next_probs:
                        # 확률에 따라 선택
                        numbers = list(next_probs.keys())
                        probs = list(next_probs.values())
                        if sum(probs) > 0:
                            probs = np.array(probs) / sum(probs)
                            chosen = np.random.choice(numbers, p=probs)
                            selected.append(int(chosen))
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
            
            return predictions
        except Exception as e:
            print(f"마르코프체인 알고리즘 오류: {e}")
            return self.generate_random_numbers(5)
    
    def genetic_algorithm(self):
        """유전자 알고리즘 - 진화론적 최적화"""
        try:
            def fitness_function(numbers):
                """적합도 함수: 과거 패턴과의 유사성 평가"""
                score = 0
                
                # 빈도 점수
                all_numbers = self.numbers.flatten()
                frequency = Counter(all_numbers)
                for num in numbers:
                    score += frequency.get(num, 0)
                
                # 최근 출현 점수
                recent_numbers = self.numbers[-10:].flatten()
                recent_freq = Counter(recent_numbers)
                for num in numbers:
                    score += recent_freq.get(num, 0) * 2
                
                # 분포 점수 (고른 분포 선호)
                zones = [0, 0, 0, 0, 0]
                for num in numbers:
                    if 1 <= num <= 9: zones[0] += 1
                    elif 10 <= num <= 18: zones[1] += 1
                    elif 19 <= num <= 27: zones[2] += 1
                    elif 28 <= num <= 36: zones[3] += 1
                    elif 37 <= num <= 45: zones[4] += 1
                
                # 균등 분포에 가까울수록 보너스
                ideal_distribution = 1.2  # 각 구간에 1-2개씩
                distribution_score = sum(1 for zone in zones if 1 <= zone <= 2) * 10
                score += distribution_score
                
                return score
            
            def crossover(parent1, parent2):
                """교배 함수"""
                child = []
                for i in range(6):
                    if random.random() < 0.5:
                        if parent1[i] not in child:
                            child.append(parent1[i])
                    else:
                        if parent2[i] not in child:
                            child.append(parent2[i])
                
                # 부족한 번호 채우기
                while len(child) < 6:
                    num = random.randint(1, 45)
                    if num not in child:
                        child.append(num)
                
                return sorted(child[:6])
            
            def mutate(individual):
                """변이 함수"""
                if random.random() < 0.3:  # 30% 확률로 변이
                    idx = random.randint(0, 5)
                    new_num = random.randint(1, 45)
                    if new_num not in individual:
                        individual[idx] = new_num
                return sorted(individual)
            
            predictions = []
            
            for _ in range(5):
                # 초기 개체군 생성
                population_size = 50
                population = []
                for _ in range(population_size):
                    individual = sorted(random.sample(range(1, 46), 6))
                    population.append(individual)
                
                # 진화 과정
                generations = 30
                for generation in range(generations):
                    # 적합도 평가
                    fitness_scores = [fitness_function(ind) for ind in population]
                    
                    # 선택 (상위 50% 선택)
                    sorted_population = [x for _, x in sorted(zip(fitness_scores, population), reverse=True)]
                    selected = sorted_population[:population_size//2]
                    
                    # 새로운 세대 생성
                    new_population = selected[:]
                    
                    while len(new_population) < population_size:
                        parent1 = random.choice(selected)
                        parent2 = random.choice(selected)
                        child = crossover(parent1, parent2)
                        child = mutate(child)
                        new_population.append(child)
                    
                    population = new_population
                
                # 최적 개체 선택
                final_fitness = [fitness_function(ind) for ind in population]
                best_individual = population[np.argmax(final_fitness)]
                predictions.append(best_individual)
            
            return predictions
        except Exception as e:
            print(f"유전자 알고리즘 오류: {e}")
            return self.generate_random_numbers(5)
    
    def co_occurrence_algorithm(self):
        """동반출현 분석 알고리즘 - 함께 나오는 번호 패턴 분석"""
        try:
            # 번호 쌍별 동반출현 빈도 계산
            co_occurrence = defaultdict(int)
            
            for draw in self.numbers:
                # 6개 번호 중 2개씩 조합하여 동반출현 횟수 계산
                for i in range(6):
                    for j in range(i+1, 6):
                        pair = tuple(sorted([draw[i], draw[j]]))
                        co_occurrence[pair] += 1
            
            # 각 번호별로 자주 함께 나오는 번호들 찾기
            number_partners = defaultdict(list)
            for (num1, num2), count in co_occurrence.items():
                number_partners[num1].append((num2, count))
                number_partners[num2].append((num1, count))
            
            # 파트너 번호들을 빈도순으로 정렬
            for num in number_partners:
                number_partners[num].sort(key=lambda x: x[1], reverse=True)
            
            predictions = []
            for _ in range(5):
                selected = []
                
                # 시작 번호 선택 (최근 자주 나온 번호 중에서)
                recent_numbers = self.numbers[-20:].flatten()
                recent_freq = Counter(recent_numbers)
                start_candidates = [num for num, count in recent_freq.most_common(15)]
                
                if start_candidates:
                    start_num = random.choice(start_candidates)
                    selected.append(start_num)
                    
                    # 동반출현이 높은 번호들을 순차적으로 선택
                    while len(selected) < 6:
                        current_num = selected[-1]
                        if current_num in number_partners:
                            # 이미 선택된 번호 제외하고 파트너 중 선택
                            available_partners = [
                                (partner, count) for partner, count in number_partners[current_num]
                                if partner not in selected
                            ]
                            
                            if available_partners:
                                # 상위 파트너들 중에서 가중치를 두고 선택
                                top_partners = available_partners[:8]
                                partners = [p[0] for p in top_partners]
                                weights = [p[1] for p in top_partners]
                                
                                if sum(weights) > 0:
                                    weights = np.array(weights) / sum(weights)
                                    chosen = np.random.choice(partners, p=weights)
                                    selected.append(int(chosen))
                                else:
                                    # 가중치가 없으면 랜덤 선택
                                    num = random.randint(1, 45)
                                    if num not in selected:
                                        selected.append(num)
                            else:
                                # 파트너가 없으면 랜덤 선택
                                num = random.randint(1, 45)
                                if num not in selected:
                                    selected.append(num)
                        else:
                            # 파트너 정보가 없으면 랜덤 선택
                            num = random.randint(1, 45)
                            if num not in selected:
                                selected.append(num)
                
                # 부족한 번호 채우기
                while len(selected) < 6:
                    num = random.randint(1, 45)
                    if num not in selected:
                        selected.append(num)
                
                predictions.append(sorted(selected[:6]))
            
            return predictions
        except Exception as e:
            print(f"동반출현 알고리즘 오류: {e}")
            return self.generate_random_numbers(5)
    
    def time_series_algorithm(self):
        """시계열 분석 알고리즘 - ARIMA 모델 기반 시간 패턴 분석"""
        try:
            predictions = []
            
            # 각 번호의 출현 간격을 시계열로 분석
            number_intervals = defaultdict(list)
            
            for num in range(1, 46):
                appearances = []
                for i, draw in enumerate(self.numbers):
                    if num in draw:
                        appearances.append(i)
                
                # 출현 간격 계산
                if len(appearances) > 1:
                    intervals = [appearances[i+1] - appearances[i] for i in range(len(appearances)-1)]
                    number_intervals[num] = intervals
            
            for _ in range(5):
                selected = []
                
                # 각 번호의 다음 출현 예상 시점 계산
                current_round = len(self.numbers)
                number_scores = {}
                
                for num in range(1, 46):
                    if num in number_intervals and number_intervals[num]:
                        intervals = number_intervals[num]
                        
                        # 마지막 출현 위치 찾기
                        last_appearance = -1
                        for i in range(len(self.numbers)-1, -1, -1):
                            if num in self.numbers[i]:
                                last_appearance = i
                                break
                        
                        if last_appearance >= 0:
                            # 평균 간격 계산
                            avg_interval = np.mean(intervals)
                            std_interval = np.std(intervals) if len(intervals) > 1 else avg_interval * 0.3
                            
                            # 현재까지의 간격
                            current_interval = current_round - last_appearance
                            
                            # 출현 확률 계산 (정규분포 기반)
                            if std_interval > 0:
                                z_score = (current_interval - avg_interval) / std_interval
                                probability = 1 / (1 + np.exp(-z_score))  # 시그모이드 함수
                            else:
                                probability = 0.5
                            
                            # 최근 빈도도 고려
                            recent_count = sum(1 for draw in self.numbers[-10:] if num in draw)
                            frequency_bonus = recent_count * 0.1
                            
                            number_scores[num] = probability + frequency_bonus
                        else:
                            # 한번도 안나온 번호는 높은 점수
                            number_scores[num] = 0.8
                    else:
                        # 데이터 부족시 중간 점수
                        number_scores[num] = 0.5
                
                # 점수가 높은 번호들 중에서 선택
                sorted_numbers = sorted(number_scores.items(), key=lambda x: x[1], reverse=True)
                
                # 상위 20개 번호 중에서 가중치를 두고 선택
                top_candidates = sorted_numbers[:20]
                candidates = [num for num, score in top_candidates]
                weights = [score for num, score in top_candidates]
                
                while len(selected) < 6 and candidates:
                    if sum(weights) > 0:
                        weights_norm = np.array(weights) / sum(weights)
                        chosen_idx = np.random.choice(len(candidates), p=weights_norm)
                        chosen_num = candidates[chosen_idx]
                        selected.append(chosen_num)
                        
                        # 선택된 번호 제거
                        candidates.pop(chosen_idx)
                        weights.pop(chosen_idx)
                    else:
                        break
                
                # 부족한 번호 채우기
                while len(selected) < 6:
                    num = random.randint(1, 45)
                    if num not in selected:
                        selected.append(num)
                
                predictions.append(sorted(selected[:6]))
            
            return predictions
        except Exception as e:
            print(f"시계열분석 알고리즘 오류: {e}")
            return self.generate_random_numbers(5)
    
    def generate_random_numbers(self, count):
        """랜덤 번호 생성 (백업용)"""
        predictions = []
        for _ in range(count):
            numbers = random.sample(range(1, 46), 6)
            predictions.append(sorted(numbers))
        return predictions
    
    def get_all_predictions(self):
        """모든 알고리즘의 예측 결과 반환 (메모리 최적화)"""
        algorithms = {
            'frequency': {'name': '빈도 분석', 'description': '자주 나온 번호 기반 예측', 'category': 'basic'},
            'hot_cold': {'name': '핫/콜드 분석', 'description': '최근 출현 패턴 기반 예측', 'category': 'basic'},
            'pattern': {'name': '패턴 분석', 'description': '번호 분포 패턴 기반 예측', 'category': 'basic'},
            'statistical': {'name': '통계 분석', 'description': '통계적 모델 기반 예측', 'category': 'basic'},
            'machine_learning': {'name': '머신러닝', 'description': '랜덤포레스트 기반 예측', 'category': 'basic'},
            'neural_network': {'name': '신경망 분석', 'description': '경량 AI 기반 패턴 학습', 'category': 'advanced'},
            'markov_chain': {'name': '마르코프 체인', 'description': '상태 전이 확률 기반 예측', 'category': 'advanced'},
            'genetic': {'name': '유전자 알고리즘', 'description': '진화론적 최적화 예측', 'category': 'advanced'},
            'co_occurrence': {'name': '동반출현 분석', 'description': '함께 나오는 번호 패턴 분석', 'category': 'advanced'},
            'time_series': {'name': '시계열 분석', 'description': '시간 패턴 기반 예측', 'category': 'advanced'}
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
                elif algo_key == 'machine_learning':
                    predictions = self.machine_learning_algorithm()
                elif algo_key == 'neural_network':
                    predictions = self.neural_network_algorithm()
                elif algo_key == 'markov_chain':
                    predictions = self.markov_chain_algorithm()
                elif algo_key == 'genetic':
                    predictions = self.genetic_algorithm()
                elif algo_key == 'co_occurrence':
                    predictions = self.co_occurrence_algorithm()
                elif algo_key == 'time_series':
                    predictions = self.time_series_algorithm()
                
                # 예측 결과 검증
                if predictions and len(predictions) >= 5:
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
                
            except Exception as e:
                print(f"❌ {algo_key} 알고리즘 실행 오류: {e}")
                # 오류 발생시 안전한 랜덤 예측 사용
                results[algo_key] = {
                    'name': algo_info['name'],
                    'description': f"{algo_info['description']} (안전 모드)",
                    'category': algo_info['category'],
                    'predictions': self.generate_random_numbers(5)
                }
        
        print(f"📊 알고리즘 실행 완료: {successful_algorithms}/{len(algorithms)}개 성공")
        
        # 최소 5개 알고리즘은 성공해야 함
        if successful_algorithms < 5:
            print("⚠️ 성공한 알고리즘이 너무 적어 추가 보완 실행")
            # 기본 알고리즘들을 추가로 실행
            for i in range(5 - successful_algorithms):
                backup_key = f"backup_{i+1}"
                results[backup_key] = {
                    'name': f'백업 알고리즘 {i+1}',
                    'description': '안정성을 위한 백업 예측',
                    'category': 'basic',
                    'predictions': self.generate_random_numbers(5)
                }
        
        return results

# 전역 예측기 인스턴스
predictor = LottoPredictor()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/predictions')
def get_predictions():
    """모든 알고리즘의 예측 결과 API"""
    try:
        results = predictor.get_all_predictions()
        return jsonify({
            'success': True,
            'data': results,
            'total_draws': len(predictor.data) if predictor.data is not None else 0,
            'last_draw': predictor.data.iloc[-1]['round'] if predictor.data is not None else None
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/statistics')
def get_statistics():
    """통계 정보 API"""
    try:
        if predictor.data is None:
            return jsonify({'success': False, 'error': 'No data available'})
        
        all_numbers = predictor.numbers.flatten()
        frequency = Counter(all_numbers)
        
        most_common = frequency.most_common(10)
        least_common = frequency.most_common()[:-11:-1]
        
        recent_numbers = predictor.numbers[-20:].flatten()
        recent_frequency = Counter(recent_numbers)
        
        stats = {
            'total_draws': len(predictor.data),
            'most_frequent': [{'number': num, 'count': count} for num, count in most_common],
            'least_frequent': [{'number': num, 'count': count} for num, count in least_common],
            'recent_hot': [{'number': num, 'count': count} for num, count in recent_frequency.most_common(10)],
            'last_draw_info': {
                'round': int(predictor.data.iloc[-1]['round']),
                'date': predictor.data.iloc[-1]['draw_date'],
                'numbers': predictor.numbers[-1].tolist(),
                'bonus': int(predictor.data.iloc[-1]['bonus_num'])
            }
        }
        
        return jsonify({
            'success': True,
            'data': stats
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
