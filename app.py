from flask import Flask, render_template, request, jsonify
import pandas as pd
import numpy as np
import random
from collections import Counter
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
import os
import json
from datetime import datetime, timedelta

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
            # 모든 번호의 빈도 계산
            all_numbers = self.numbers.flatten()
            frequency = Counter(all_numbers)
            
            # 상위 빈도 번호들
            most_common = [num for num, count in frequency.most_common(20)]
            
            predictions = []
            for _ in range(5):
                # 상위 빈도 번호에서 가중치를 두고 선택
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
            recent_draws = 20  # 최근 20회차
            recent_data = self.numbers[-recent_draws:]
            recent_numbers = recent_data.flatten()
            
            # 핫 번호 (최근 자주 나온 번호)
            hot_counter = Counter(recent_numbers)
            hot_numbers = [num for num, count in hot_counter.most_common(15)]
            
            # 콜드 번호 (오랫동안 안 나온 번호)
            all_numbers_set = set(range(1, 46))
            recent_numbers_set = set(recent_numbers)
            cold_numbers = list(all_numbers_set - recent_numbers_set)
            
            if len(cold_numbers) < 10:
                # 콜드 번호가 부족하면 덜 자주 나온 번호로 보완
                all_counter = Counter(self.numbers.flatten())
                least_common = [num for num, count in all_counter.most_common()[:-11:-1]]
                cold_numbers.extend(least_common)
            
            predictions = []
            for _ in range(5):
                selected = []
                # 핫 번호 3-4개, 콜드 번호 2-3개 조합
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
            
            # 최근 30회차의 패턴 분석
            recent_data = self.numbers[-30:]
            
            # 구간별 분포 분석 (1-10, 11-20, 21-30, 31-40, 41-45)
            zones = [0, 0, 0, 0, 0]  # 각 구간별 선택 가중치
            
            for draw in recent_data:
                for num in draw:
                    if 1 <= num <= 10: zones[0] += 1
                    elif 11 <= num <= 20: zones[1] += 1
                    elif 21 <= num <= 30: zones[2] += 1
                    elif 31 <= num <= 40: zones[3] += 1
                    elif 41 <= num <= 45: zones[4] += 1
            
            # 정규화
            total = sum(zones)
            zone_probs = [z/total for z in zones] if total > 0 else [0.2] * 5
            
            for _ in range(5):
                selected = []
                
                # 각 구간에서 번호 선택
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
                
                # 부족한 번호 채우기
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
            
            # 각 자리별 통계 분석
            position_stats = []
            for pos in range(6):
                pos_numbers = self.numbers[:, pos]
                mean = np.mean(pos_numbers)
                std = np.std(pos_numbers)
                position_stats.append({'mean': mean, 'std': std})
            
            for _ in range(5):
                selected = []
                
                for pos, stats in enumerate(position_stats):
                    # 정규분포를 따른다고 가정하고 번호 생성
                    num = int(np.random.normal(stats['mean'], stats['std']))
                    num = max(1, min(45, num))  # 1-45 범위로 제한
                    
                    # 중복 방지
                    attempts = 0
                    while num in selected and attempts < 100:
                        num = int(np.random.normal(stats['mean'], stats['std']))
                        num = max(1, min(45, num))
                        attempts += 1
                    
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
            print(f"통계분석 알고리즘 오류: {e}")
            return self.generate_random_numbers(5)
    
    def machine_learning_algorithm(self):
        """머신러닝 알고리즘 - 랜덤포레스트 기반 예측"""
        try:
            if len(self.numbers) < 50:
                return self.generate_random_numbers(5)
            
            # 특성 생성: 최근 n회차의 번호들을 특성으로 사용
            window_size = 10
            X, y = [], []
            
            for i in range(window_size, len(self.numbers)):
                # 이전 window_size개 회차의 데이터를 특성으로
                features = self.numbers[i-window_size:i].flatten()
                target = self.numbers[i]
                X.append(features)
                y.append(target)
            
            X = np.array(X)
            y = np.array(y)
            
            predictions = []
            
            # 각 위치별로 모델 학습
            for _ in range(5):
                prediction_set = []
                
                for pos in range(6):
                    try:
                        model = RandomForestRegressor(n_estimators=50, random_state=random.randint(1, 1000))
                        model.fit(X, y[:, pos])
                        
                        # 최근 데이터로 예측
                        last_features = self.numbers[-window_size:].flatten().reshape(1, -1)
                        pred = model.predict(last_features)[0]
                        pred = max(1, min(45, int(round(pred))))
                        
                        if pred not in prediction_set:
                            prediction_set.append(pred)
                    except:
                        # 모델 실패시 랜덤 선택
                        num = random.randint(1, 45)
                        if num not in prediction_set:
                            prediction_set.append(num)
                
                # 부족한 번호 채우기
                while len(prediction_set) < 6:
                    num = random.randint(1, 45)
                    if num not in prediction_set:
                        prediction_set.append(num)
                
                predictions.append(sorted(prediction_set[:6]))
            
            return predictions
        except Exception as e:
            print(f"머신러닝 알고리즘 오류: {e}")
            return self.generate_random_numbers(5)
    
    def generate_random_numbers(self, count):
        """랜덤 번호 생성 (백업용)"""
        predictions = []
        for _ in range(count):
            numbers = random.sample(range(1, 46), 6)
            predictions.append(sorted(numbers))
        return predictions
    
    def get_all_predictions(self):
        """모든 알고리즘의 예측 결과 반환"""
        algorithms = {
            'frequency': {'name': '빈도 분석', 'description': '자주 나온 번호 기반 예측'},
            'hot_cold': {'name': '핫/콜드 분석', 'description': '최근 출현 패턴 기반 예측'},
            'pattern': {'name': '패턴 분석', 'description': '번호 분포 패턴 기반 예측'},
            'statistical': {'name': '통계 분석', 'description': '통계적 모델 기반 예측'},
            'machine_learning': {'name': '머신러닝', 'description': 'AI 모델 기반 예측'}
        }
        
        results = {}
        
        for algo_key, algo_info in algorithms.items():
            try:
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
                
                results[algo_key] = {
                    'name': algo_info['name'],
                    'description': algo_info['description'],
                    'predictions': predictions
                }
            except Exception as e:
                print(f"{algo_key} 알고리즘 실행 오류: {e}")
                results[algo_key] = {
                    'name': algo_info['name'],
                    'description': algo_info['description'],
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
        
        # 최고 빈도 번호들
        most_common = frequency.most_common(10)
        least_common = frequency.most_common()[:-11:-1]
        
        # 최근 출현 분석
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
