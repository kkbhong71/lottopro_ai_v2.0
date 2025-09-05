# Gunicorn 설정 파일 - 극한 메모리 최적화
import multiprocessing
import os

# 서버 소켓
bind = "0.0.0.0:10000"

# 워커 설정 - 극한 메모리 절약
workers = 1  # 단일 워커로 메모리 사용량 최소화
worker_class = "sync"
worker_connections = 100  # 연결 수 감소

# 메모리 관리 강화
max_requests = 200  # 요청 200개마다 워커 재시작 (더 자주 재시작)
max_requests_jitter = 20
worker_timeout = 300  # 타임아웃 5분으로 증가 (AI 계산 여유 확보)
graceful_timeout = 60  # 우아한 종료 시간
keepalive = 2

# 메모리 최적화 설정
preload_app = True  # 앱을 미리 로드해서 메모리 공유
max_worker_memory = 400  # 워커당 최대 메모리 400MB

# 로깅 최적화
loglevel = "warning"  # 로그 레벨을 warning으로 낮춤 (메모리 절약)
accesslog = None  # 액세스 로그 비활성화 (메모리 절약)
errorlog = "-"
capture_output = True

# 프로세스 이름
proc_name = "lottopro-ai-v2"

# 시작/종료 시 로그
def when_ready(server):
    server.log.warning("🚀 LottoPro AI v2.0 starting up with memory optimization...")

def worker_int(worker):
    worker.log.warning("⚠️ Worker %s terminated", worker.pid)

def on_starting(server):
    server.log.warning("✅ LottoPro AI v2.0 is ready with optimized settings!")

# 메모리 사용량 모니터링
def post_worker_init(worker):
    worker.log.warning("🔧 Worker %s initialized with extreme memory optimization", worker.pid)

# 워커 메모리 한계 도달 시 재시작
def worker_abort(worker):
    worker.log.error("💀 Worker %s aborted due to memory limit", worker.pid)
