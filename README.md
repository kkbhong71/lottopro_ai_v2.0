# 🎯 LottoPro AI v2.0

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/flask-2.3.3-green.svg)](https://flask.palletsprojects.com/)
[![Deploy to Render](https://img.shields.io/badge/deploy-render-46e3b7.svg)](https://render.com)

> **5가지 독자적인 AI 모델이 과거 데이터를 분석하여 최적의 로또 예상번호를 무료로 추천하는 차세대 서비스**

## 🌟 주요 특징

- **🤖 5가지 AI 예측 모델**: 빈도분석, 트렌드분석, 패턴분석, 통계분석, 머신러닝
- **📱 QR코드 당첨 확인**: 로또 용지 QR스캔으로 즉시 당첨 확인
- **💾 번호 저장 및 관리**: 소중한 번호들을 안전하게 저장
- **📊 실시간 통계 분석**: 핫/콜드 넘버, 이월수/궁합수 분석
- **🎰 당첨 시뮬레이션**: 특정 번호로 몇 번이나 당첨될지 시뮬레이션
- **💰 세금 계산기**: 당첨금 세금 자동 계산
- **🗺️ 로또 판매점 찾기**: 근처 판매점 검색
- **📱 PWA 지원**: 앱처럼 설치 가능
- **🔄 오프라인 지원**: 인터넷 없어도 기본 기능 사용

## 🚀 빠른 시작

### 온라인 사용
👉 **[LottoPro AI v2.0 바로 사용하기](https://lottopro-ai.onrender.com)**

### 로컬 설치

```bash
# 1. 저장소 클론
git clone https://github.com/yourusername/lottopro-ai-v2.git
cd lottopro-ai-v2

# 2. 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. 의존성 설치
pip install -r requirements.txt

# 4. 환경변수 설정
cp .env.example .env
# .env 파일 편집 후 SECRET_KEY 설정

# 5. 애플리케이션 실행
python app.py
```

애플리케이션이 `http://localhost:5000`에서 실행됩니다.

## 🔧 배포

### Render.com 배포 (권장)

1. **Render.com 계정 생성** 및 GitHub 연동
2. **New Web Service** 선택
3. **저장소 연결** 후 다음 설정:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app --bind 0.0.0.0:$PORT --workers 2`
   - **Environment Variables**:
     ```
     PORT=5000
     SECRET_KEY=your-super-secret-key-here
     DEBUG=False
     CSV_PATH=new_1185.csv
     ```

### Heroku 배포

```bash
# Heroku CLI 설치 후
heroku create lottopro-ai
heroku config:set SECRET_KEY="your-secret-key"
git push heroku main
```

### Docker 배포

```bash
# Docker 이미지 빌드
docker build -t lottopro-ai .

# 컨테이너 실행
docker run -p 5000:5000 -e SECRET_KEY="your-secret-key" lottopro-ai
```

## 📊 API 엔드포인트

| 엔드포인트 | 메서드 | 설명 |
|-----------|--------|------|
| `/api/predict` | POST | AI 예측 번호 생성 |
| `/api/stats` | GET | 통계 정보 조회 |
| `/api/save-numbers` | POST | 번호 저장 |
| `/api/check-winning` | POST | 당첨 확인 |
| `/api/simulation` | POST | 당첨 시뮬레이션 |
| `/api/tax-calculator` | POST | 세금 계산 |
| `/api/health` | GET | 서비스 상태 확인 |

## 🛠️ 기술 스택

- **Backend**: Python 3.11, Flask 2.3.3
- **Frontend**: HTML5, CSS3, JavaScript ES6+
- **UI Framework**: Bootstrap 5.3.0
- **Icons**: Font Awesome 6.4.0
- **Data Analysis**: NumPy, Pandas, Scikit-learn
- **PWA**: Service Worker, Web App Manifest
- **Deployment**: Render.com, Heroku, Docker

## 📱 PWA 기능

- **오프라인 지원**: 캐시된 데이터로 기본 기능 사용 가능
- **앱 설치**: 홈 화면에 추가하여 네이티브 앱처럼 사용
- **푸시 알림**: 새로운 당첨 정보 알림 (추후 추가 예정)
- **배경 동기화**: 오프라인에서 입력한 데이터 자동 동기화

## 🔐 보안

- **HTTPS 강제**: 모든 통신 암호화
- **CSP 헤더**: XSS 공격 방지
- **입력 검증**: 모든 사용자 입력 검증
- **환경변수**: 민감한 정보 환경변수로 관리

## 📈 성능

- **CDN 활용**: 정적 파일 빠른 로딩
- **이미지 최적화**: WebP 포맷 지원
- **캐싱 전략**: 적극적인 브라우저 캐싱
- **지연 로딩**: 필요한 시점에 리소스 로드

## 🤝 기여하기

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 `LICENSE` 파일을 참조하세요.

## ⚠️ 면책 조항

본 서비스는 예측 정보 제공 목적이며, 당첨을 보장하지 않습니다. 책임감 있는 구매를 권장하며, 모든 투자 결정에 대한 최종 책임은 사용자에게 있습니다.

## 📞 문의

- **이메일**: support@lottopro-ai.com
- **이슈**: [GitHub Issues](https://github.com/yourusername/lottopro-ai-v2/issues)

---

<div align="center">

**🎯 LottoPro AI v2.0 - AI가 예측하는 로또 당첨번호**

Made with ❤️ by LottoPro AI Team

</div>