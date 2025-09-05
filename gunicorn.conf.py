# Gunicorn 설정 파일 - 메모리 최적화
import multiprocessing
import os

# 서버 소켓
bind = "0.0.0.0:10000"

# 워커 설정 - 메모리 절약을 위해 최소화
workers = 2  # CPU 코어 수의 절반으로 제한
worker_class = "sync"
worker_connections = 1000

# 메모리 관리
max_requests = 500  # 요청 500개마다 워커 재시작 (메모리 누수 방지)
max_requests_jitter = 50
worker_timeout = 120  # 타임아웃 증가 (AI 계산 시간 확보)
keepalive = 2

# 로깅
loglevel = "info"
accesslog = "-"
errorlog = "-"
access_log_format = '%(h)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# 프로세스 이름
proc_name = "lottopro-ai-v2"

# 메모리 제한 설정
preload_app = True  # 앱을 미리 로드해서 메모리 공유

# 시작/종료 시 로그
def when_ready(server):
    server.log.info("🚀 LottoPro AI v2.0 starting up...")

def worker_int(worker):
    worker.log.info("⚠️ Worker %s aborted", worker.pid)

def on_starting(server):
    server.log.info("✅ LottoPro AI v2.0 is ready to serve requests!")

# 메모리 사용량 모니터링
def post_worker_init(worker):
    worker.log.info("🔧 Worker %s initialized with optimized settings", worker.pid)
