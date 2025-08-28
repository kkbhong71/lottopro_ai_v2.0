# LottoPro AI v2.0 - 투명성 강화 버전
FROM python:3.9-slim

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 패키지 업데이트 및 필요한 패키지 설치
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성 파일 복사
COPY requirements.txt .

# Python 패키지 설치
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY . .

# 정적 파일 디렉토리 생성
RUN mkdir -p static/css static/js static/images

# 로그 디렉토리 생성
RUN mkdir -p logs

# 데이터베이스 디렉토리 생성
RUN mkdir -p data

# 권한 설정
RUN useradd -m -u 1000 lottopro && \
    chown -R lottopro:lottopro /app
USER lottopro

# 환경 변수 설정
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV PYTHONPATH=/app
ENV TRANSPARENCY_MODE=enabled

# 헬스 체크 스크립트 추가
COPY --chown=lottopro:lottopro healthcheck.py /app/

# 포트 노출
EXPOSE 5000

# 헬스 체크 설정
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python healthcheck.py

# 애플리케이션 시작 명령
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "120", "--access-logfile", "-", "--error-logfile", "-", "app:app"]
