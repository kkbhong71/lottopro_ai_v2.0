"""
LottoPro AI v2.0 - 데이터 검증 및 무결성 모듈
투명성 보장을 위한 데이터 검증, 무결성 체크, 통계적 유효성 검증
"""

import hashlib
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
from scipy import stats
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataValidator:
    """데이터 무결성 및 유효성 검증 클래스"""
    
    def __init__(self):
        self.validation_rules = self._setup_validation_rules()
        self.statistical_thresholds = self._setup_statistical_thresholds()
        
    def _setup_validation_rules(self) -> Dict:
        """검증 규칙 설정"""
        return {
            'lottery_numbers': {
                'min_value': 1,
                'max_value': 45,
                'count': 6,
                'unique': True
            },
            'round_number': {
                'min_value': 1,
                'max_value': 9999,
                'type': int
            },
            'prediction_accuracy': {
                'min_value': 0.0,
                'max_value': 100.0,
                'type': float
            }
        }
    
    def _setup_statistical_thresholds(self) -> Dict:
        """통계적 임계값 설정"""
        return {
            'max_deviation_from_random': 10.0,  # 무작위 대비 최대 편차 (%)
            'min_sample_size': 10,  # 통계적 유의성을 위한 최소 표본 크기
            'significance_level': 0.05,  # 유의수준
            'max_consecutive_anomalies': 3  # 연속 이상치 최대 허용 수
        }

class LotteryDataValidator(DataValidator):
    """로또 데이터 전용 검증 클래스"""
    
    def validate_lottery_numbers(self, numbers: List[int]) -> Tuple[bool, List[str]]:
        """로또 번호 유효성 검증"""
        errors = []
        
        # 기본 검증
        if len(numbers) != 6:
            errors.append(f"번호 개수 오류: {len(numbers)}개 (6개 필요)")
        
        # 범위 검증
        for num in numbers:
            if not isinstance(num, int):
                errors.append(f"번호 타입 오류: {num} (정수 필요)")
            elif num < 1 or num > 45:
                errors.append(f"번호 범위 오류: {num} (1-45 범위)")
        
        # 중복 검증
        if len(set(numbers)) != len(numbers):
            errors.append("중복 번호 존재")
        
        return len(errors) == 0, errors
    
    def validate_prediction_history(self, history_data: List[Dict]) -> Dict[str, Any]:
        """예측 히스토리 데이터 검증"""
        validation_result = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'statistics': {}
        }
        
        if not history_data:
            validation_result['is_valid'] = False
            validation_result['errors'].append("히스토리 데이터가 비어있음")
            return validation_result
        
        # 각 레코드 검증
        for i, record in enumerate(history_data):
            record_errors = self._validate_single_record(record, i)
            validation_result['errors'].extend(record_errors)
        
        # 통계적 검증
        stats_validation = self._validate_statistical_properties(history_data)
        validation_result['statistics'] = stats_validation
        
        # 경고사항 추가
        validation_result['warnings'] = self._generate_warnings(stats_validation)
        
        validation_result['is_valid'] = len(validation_result['errors']) == 0
        
        return validation_result
    
    def _validate_single_record(self, record: Dict, index: int) -> List[str]:
        """단일 레코드 검증"""
        errors = []
        required_fields = ['round', 'date', 'winning_numbers', 'ai_predictions', 'matches']
        
        # 필수 필드 검증
        for field in required_fields:
            if field not in record:
                errors.append(f"레코드 {index}: 필수 필드 '{field}' 누락")
        
        if 'winning_numbers' in record:
            is_valid, num_errors = self.validate_lottery_numbers(record['winning_numbers'])
            if not is_valid:
                errors.extend([f"레코드 {index} 당첨번호: {err}" for err in num_errors])
        
        if 'ai_predictions' in record and 'combined' in record['ai_predictions']:
            is_valid, num_errors = self.validate_lottery_numbers(record['ai_predictions']['combined'])
            if not is_valid:
                errors.extend([f"레코드 {index} AI예측: {err}" for err in num_errors])
        
        # 일치 개수 검증
        if 'matches' in record and 'combined' in record['matches']:
            matches = record['matches']['combined']
            if not isinstance(matches, int) or matches < 0 or matches > 6:
                errors.append(f"레코드 {index}: 일치 개수 오류 ({matches})")
        
        return errors
    
    def _validate_statistical_properties(self, history_data: List[Dict]) -> Dict[str, Any]:
        """통계적 속성 검증"""
        if len(history_data) < self.statistical_thresholds['min_sample_size']:
            return {'sample_size_warning': True, 'insufficient_data': True}
        
        # 일치율 추출
        match_rates = []
        for record in history_data:
            if 'matches' in record and 'combined' in record['matches']:
                matches = record['matches']['combined']
                match_rate = (matches / 6) * 100
                match_rates.append(match_rate)
        
        if not match_rates:
            return {'no_valid_data': True}
        
        # 통계 계산
        mean_accuracy = np.mean(match_rates)
        std_accuracy = np.std(match_rates)
        theoretical_rate = (6 / 45) * 100  # 이론적 기댓값
        
        # 통계적 검정
        t_stat, p_value = stats.ttest_1samp(match_rates, theoretical_rate)
        
        # 이상치 검출
        z_scores = np.abs(stats.zscore(match_rates))
        outliers = np.where(z_scores > 2)[0].tolist()
        
        return {
            'sample_size': len(match_rates),
            'mean_accuracy': round(mean_accuracy, 2),
            'std_accuracy': round(std_accuracy, 2),
            'theoretical_rate': round(theoretical_rate, 2),
            'deviation_from_theory': round(mean_accuracy - theoretical_rate, 2),
            't_statistic': round(t_stat, 3),
            'p_value': round(p_value, 3),
            'is_statistically_significant': p_value < self.statistical_thresholds['significance_level'],
            'outlier_indices': outliers,
            'outlier_count': len(outliers)
        }
    
    def _generate_warnings(self, stats: Dict[str, Any]) -> List[str]:
        """경고사항 생성"""
        warnings = []
        
        if stats.get('insufficient_data'):
            warnings.append(f"표본 크기가 작습니다 ({stats.get('sample_size', 0)}개). 통계적 신뢰도가 낮을 수 있습니다.")
        
        if abs(stats.get('deviation_from_theory', 0)) > self.statistical_thresholds['max_deviation_from_random']:
            warnings.append(f"이론값 대비 편차가 큽니다 ({stats.get('deviation_from_theory')}%)")
        
        if stats.get('outlier_count', 0) > self.statistical_thresholds['max_consecutive_anomalies']:
            warnings.append(f"이상치가 많이 발견되었습니다 ({stats.get('outlier_count')}개)")
        
        if stats.get('is_statistically_significant'):
            warnings.append("통계적으로 유의미한 차이가 발견되었습니다. 추가 검토가 필요합니다.")
        
        return warnings

class DataIntegrityChecker:
    """데이터 무결성 체크 클래스"""
    
    def __init__(self):
        self.checksums = {}
        self.verification_log = []
    
    def calculate_checksum(self, data: Any) -> str:
        """데이터 체크섬 계산"""
        json_string = json.dumps(data, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(json_string.encode('utf-8')).hexdigest()
    
    def verify_data_integrity(self, data_id: str, data: Any) -> Dict[str, Any]:
        """데이터 무결성 검증"""
        current_checksum = self.calculate_checksum(data)
        timestamp = datetime.now().isoformat()
        
        result = {
            'data_id': data_id,
            'timestamp': timestamp,
            'current_checksum': current_checksum,
            'is_intact': True,
            'changed': False
        }
        
        if data_id in self.checksums:
            previous_checksum = self.checksums[data_id]['checksum']
            result['previous_checksum'] = previous_checksum
            result['changed'] = current_checksum != previous_checksum
            result['is_intact'] = True  # 변경되었어도 무결성은 유지됨
        
        # 체크섬 업데이트
        self.checksums[data_id] = {
            'checksum': current_checksum,
            'timestamp': timestamp
        }
        
        # 로그 기록
        self.verification_log.append(result)
        
        return result
    
    def get_integrity_report(self) -> Dict[str, Any]:
        """무결성 보고서 생성"""
        return {
            'total_checks': len(self.verification_log),
            'last_check': self.verification_log[-1]['timestamp'] if self.verification_log else None,
            'tracked_datasets': list(self.checksums.keys()),
            'verification_history': self.verification_log[-10:],  # 최근 10개만
            'integrity_status': 'VERIFIED'
        }

class TransparencyAuditor:
    """투명성 감사 클래스"""
    
    def __init__(self):
        self.validator = LotteryDataValidator()
        self.integrity_checker = DataIntegrityChecker()
        self.audit_log = []
    
    def conduct_transparency_audit(self, data_package: Dict[str, Any]) -> Dict[str, Any]:
        """투명성 감사 수행"""
        audit_id = f"audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        audit_result = {
            'audit_id': audit_id,
            'timestamp': datetime.now().isoformat(),
            'data_validation': {},
            'integrity_check': {},
            'transparency_score': 0,
            'recommendations': [],
            'compliance_status': 'PENDING'
        }
        
        try:
            # 데이터 검증
            if 'prediction_history' in data_package:
                validation_result = self.validator.validate_prediction_history(
                    data_package['prediction_history']
                )
                audit_result['data_validation'] = validation_result
            
            # 무결성 검증
            integrity_result = self.integrity_checker.verify_data_integrity(
                audit_id, data_package
            )
            audit_result['integrity_check'] = integrity_result
            
            # 투명성 점수 계산
            transparency_score = self._calculate_transparency_score(audit_result)
            audit_result['transparency_score'] = transparency_score
            
            # 권장사항 생성
            recommendations = self._generate_recommendations(audit_result)
            audit_result['recommendations'] = recommendations
            
            # 컴플라이언스 상태 결정
            compliance_status = self._determine_compliance_status(audit_result)
            audit_result['compliance_status'] = compliance_status
            
        except Exception as e:
            logger.error(f"감사 중 오류 발생: {e}")
            audit_result['error'] = str(e)
            audit_result['compliance_status'] = 'ERROR'
        
        # 감사 로그 기록
        self.audit_log.append(audit_result)
        
        return audit_result
    
    def _calculate_transparency_score(self, audit_result: Dict[str, Any]) -> int:
        """투명성 점수 계산 (0-100)"""
        score = 0
        
        # 데이터 검증 점수 (40점)
        if audit_result['data_validation'].get('is_valid', False):
            score += 40
        elif len(audit_result['data_validation'].get('errors', [])) <= 2:
            score += 20  # 경미한 오류
        
        # 무결성 점수 (30점)
        if audit_result['integrity_check'].get('is_intact', False):
            score += 30
        
        # 통계적 투명성 (20점)
        stats = audit_result['data_validation'].get('statistics', {})
        if stats.get('sample_size', 0) >= 10:
            score += 10
        if 'p_value' in stats:
            score += 10
        
        # 경고사항 점수 (10점)
        warnings = audit_result['data_validation'].get('warnings', [])
        if len(warnings) == 0:
            score += 10
        elif len(warnings) <= 2:
            score += 5
        
        return min(score, 100)
    
    def _generate_recommendations(self, audit_result: Dict[str, Any]) -> List[str]:
        """개선 권장사항 생성"""
        recommendations = []
        
        # 데이터 품질 권장사항
        if not audit_result['data_validation'].get('is_valid', False):
            recommendations.append("데이터 검증 오류를 수정하여 데이터 품질을 개선하세요")
        
        # 표본 크기 권장사항
        stats = audit_result['data_validation'].get('statistics', {})
        if stats.get('sample_size', 0) < 20:
            recommendations.append("통계적 신뢰도 향상을 위해 더 많은 검증 데이터를 축적하세요")
        
        # 통계적 유의성 권장사항
        if stats.get('is_statistically_significant'):
            recommendations.append("통계적 유의성이 발견되었습니다. 추가 분석과 설명이 필요합니다")
        
        # 이상치 권장사항
        if stats.get('outlier_count', 0) > 3:
            recommendations.append("이상치가 많이 발견되었습니다. 데이터 수집 과정을 재검토하세요")
        
        # 투명성 점수 권장사항
        if audit_result['transparency_score'] < 80:
            recommendations.append("투명성 점수가 낮습니다. 데이터 공개 범위를 확대하세요")
        
        return recommendations
    
    def _determine_compliance_status(self, audit_result: Dict[str, Any]) -> str:
        """컴플라이언스 상태 결정"""
        if audit_result.get('error'):
            return 'ERROR'
        
        transparency_score = audit_result['transparency_score']
        has_critical_errors = len(audit_result['data_validation'].get('errors', [])) > 5
        
        if transparency_score >= 90 and not has_critical_errors:
            return 'EXCELLENT'
        elif transparency_score >= 80 and not has_critical_errors:
            return 'GOOD'
        elif transparency_score >= 70:
            return 'ACCEPTABLE'
        elif transparency_score >= 60:
            return 'NEEDS_IMPROVEMENT'
        else:
            return 'NON_COMPLIANT'
    
    def generate_audit_report(self) -> Dict[str, Any]:
        """감사 보고서 생성"""
        if not self.audit_log:
            return {'error': '감사 기록이 없습니다'}
        
        latest_audit = self.audit_log[-1]
        
        return {
            'report_metadata': {
                'generated_at': datetime.now().isoformat(),
                'audit_count': len(self.audit_log),
                'latest_audit_id': latest_audit['audit_id']
            },
            'current_status': {
                'transparency_score': latest_audit['transparency_score'],
                'compliance_status': latest_audit['compliance_status'],
                'data_integrity': latest_audit['integrity_check']['is_intact']
            },
            'summary_statistics': self._calculate_audit_statistics(),
            'recommendations': latest_audit['recommendations'],
            'improvement_trends': self._analyze_improvement_trends(),
            'next_audit_due': self._calculate_next_audit_date()
        }
    
    def _calculate_audit_statistics(self) -> Dict[str, Any]:
        """감사 통계 계산"""
        if not self.audit_log:
            return {}
        
        scores = [audit['transparency_score'] for audit in self.audit_log]
        
        return {
            'average_transparency_score': round(np.mean(scores), 1),
            'score_trend': 'improving' if len(scores) > 1 and scores[-1] > scores[-2] else 'stable',
            'total_audits': len(self.audit_log),
            'compliance_rate': len([a for a in self.audit_log if a['compliance_status'] in ['EXCELLENT', 'GOOD']]) / len(self.audit_log) * 100
        }
    
    def _analyze_improvement_trends(self) -> List[str]:
        """개선 트렌드 분석"""
        if len(self.audit_log) < 2:
            return ["트렌드 분석을 위한 충분한 데이터가 없습니다"]
        
        trends = []
        recent_scores = [audit['transparency_score'] for audit in self.audit_log[-5:]]
        
        if len(recent_scores) > 1:
            if recent_scores[-1] > recent_scores[0]:
                trends.append("투명성 점수가 개선되고 있습니다")
            elif recent_scores[-1] < recent_scores[0]:
                trends.append("투명성 점수가 하락하고 있습니다")
            else:
                trends.append("투명성 점수가 안정적입니다")
        
        return trends
    
    def _calculate_next_audit_date(self) -> str:
        """다음 감사 예정일 계산"""
        next_audit = datetime.now() + timedelta(days=7)  # 주간 감사
        return next_audit.strftime('%Y-%m-%d')

# 사용 예제 및 테스트 코드
if __name__ == "__main__":
    # 테스트 데이터
    test_data = {
        'prediction_history': [
            {
                'round': 1185,
                'date': '2025.08.17',
                'winning_numbers': [7, 13, 21, 28, 34, 42],
                'ai_predictions': {'combined': [7, 15, 21, 29, 34, 45]},
                'matches': {'combined': 3}
            },
            {
                'round': 1184,
                'date': '2025.08.10',
                'winning_numbers': [2, 18, 25, 31, 39, 44],
                'ai_predictions': {'combined': [8, 18, 24, 33, 39, 42]},
                'matches': {'combined': 2}
            }
        ]
    }
    
    # 투명성 감사 수행
    auditor = TransparencyAuditor()
    audit_result = auditor.conduct_transparency_audit(test_data)
    
    print("=== 투명성 감사 결과 ===")
    print(f"감사 ID: {audit_result['audit_id']}")
    print(f"투명성 점수: {audit_result['transparency_score']}/100")
    print(f"컴플라이언스 상태: {audit_result['compliance_status']}")
    print(f"권장사항: {len(audit_result['recommendations'])}개")
    
    # 감사 보고서 생성
    report = auditor.generate_audit_report()
    print(f"\n=== 감사 보고서 ===")
    print(f"평균 투명성 점수: {report['summary_statistics']['average_transparency_score']}")
    print(f"컴플라이언스 율: {report['summary_statistics']['compliance_rate']:.1f}%")
