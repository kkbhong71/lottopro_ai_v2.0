# 긴급 수정 - 극도로 보수적인 설정
import os

# 서버 소켓
bind = "0.0.0.0:10000"

# 최소한의 워커 설정
workers = 1
worker_class = "sync"
worker_connections = 50
worker_timeout = 600  # 10분으로 증가

# 메모리 관리
max_requests = 100  # 더 자주 재시작
max_requests_jitter = 10
keepalive = 2

# 로깅 최소화
loglevel = "error"  # error만 로그
accesslog = None
errorlog = "-"

# 프로세스 이름
proc_name = "lottopro-emergency"

# 시작 로그
def on_starting(server):
    server.log.error("🚨 LottoPro Emergency Mode Started")
