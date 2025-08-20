# LottoPro AI v2.0 Gunicorn Configuration
# High-performance WSGI server configuration for production deployment

import os
import multiprocessing

# =============================================================================
# SERVER SOCKET
# =============================================================================

# The socket to bind
bind = f"0.0.0.0:{os.environ.get('PORT', '5000')}"

# The maximum number of pending connections
backlog = 2048

# =============================================================================
# WORKER PROCESSES
# =============================================================================

# The number of worker processes for handling requests
workers = int(os.environ.get('WEB_CONCURRENCY', multiprocessing.cpu_count() * 2))

# The type of workers to run (sync, gevent, eventlet, tornado)
worker_class = "sync"

# The maximum number of simultaneous clients per worker
worker_connections = 1000

# Workers silent for more than this many seconds are killed and restarted
timeout = int(os.environ.get('TIMEOUT', '120'))

# The number of seconds to wait for requests on a Keep-Alive connection
keepalive = 2

# The maximum number of requests a worker will process before restarting
max_requests = 1000

# Randomize the max_requests to prevent workers from restarting at the same time
max_requests_jitter = 50

# =============================================================================
# SECURITY
# =============================================================================

# Limit the allowed size of an HTTP request line
limit_request_line = 0

# Limit the number of HTTP request header fields
limit_request_fields = 100

# Limit the allowed size of an HTTP request header field
limit_request_field_size = 8190

# =============================================================================
# APPLICATION
# =============================================================================

# The Python path to the WSGI module and callable
wsgi_module = "app:app"

# Preload the application before forking workers
preload_app = True

# =============================================================================
# LOGGING
# =============================================================================

# The access log file to write to
accesslog = "-"  # stdout

# The error log file to write to
errorlog = "-"   # stderr

# The granularity of error log outputs
loglevel = os.environ.get('LOG_LEVEL', 'info').lower()

# The access log format
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# =============================================================================
# PROCESS NAMING
# =============================================================================

# A base to use with setproctitle for process naming
proc_name = "lottopro-ai-v2"

# =============================================================================
# DEVELOPMENT SETTINGS
# =============================================================================

# Reload the application when source code changes (development only)
reload = os.environ.get('DEBUG', 'False').lower() == 'true'

# =============================================================================
# PERFORMANCE TUNING
# =============================================================================

# Maximum size of HTTP request line in bytes
max_requests_header = 100

# Enable sendfile() for serving static files (if applicable)
sendfile = True

# =============================================================================
# HOOKS
# =============================================================================

def on_starting(server):
    """Called just before the master process is initialized."""
    server.log.info("🚀 LottoPro AI v2.0 starting up...")

def on_reload(server):
    """Called to recycle workers during a reload via SIGHUP."""
    server.log.info("🔄 LottoPro AI v2.0 reloading...")

def when_ready(server):
    """Called just after the server is started."""
    server.log.info("✅ LottoPro AI v2.0 is ready to serve requests!")

def worker_int(worker):
    """Called just after a worker exited on SIGINT or SIGQUIT."""
    worker.log.info(f"👷 Worker {worker.pid} received INT or QUIT signal")

def pre_fork(server, worker):
    """Called just before a worker is forked."""
    server.log.debug(f"👶 Forking worker {worker.pid}")

def post_fork(server, worker):
    """Called just after a worker has been forked."""
    server.log.debug(f"🎉 Worker {worker.pid} spawned")

def post_worker_init(worker):
    """Called just after a worker has initialized the application."""
    worker.log.debug(f"🏗️ Worker {worker.pid} initialized")

def worker_abort(worker):
    """Called when a worker received the SIGABRT signal."""
    worker.log.warning(f"⚠️ Worker {worker.pid} aborted")

def pre_exec(server):
    """Called just before a new master process is forked."""
    server.log.info("🔄 Master process executing...")

def on_exit(server):
    """Called just before exiting."""
    server.log.info("👋 LottoPro AI v2.0 shutting down...")

# =============================================================================
# ENVIRONMENT SPECIFIC CONFIGURATIONS
# =============================================================================

# Production optimizations
if os.environ.get('ENVIRONMENT') == 'production':
    # Increase worker count for production
    workers = max(workers, 4)
    
    # Longer timeout for production
    timeout = 300
    
    # More aggressive request limits
    max_requests = 2000
    max_requests_jitter = 100
    
    # Disable reload in production
    reload = False

# Development settings
elif os.environ.get('ENVIRONMENT') == 'development':
    # Single worker for development
    workers = 1
    
    # Enable reload for development
    reload = True
    
    # Shorter timeout for development
    timeout = 60
    
    # More verbose logging
    loglevel = 'debug'

# =============================================================================
# ADDITIONAL CONFIGURATION
# =============================================================================

# Enable/disable request logging based on environment
if os.environ.get('DISABLE_ACCESS_LOG'):
    accesslog = None

# Custom environment variables
raw_env = [
    'LOTTOPRO_VERSION=v2.0.0',
    f'WORKER_ID={os.getpid()}',
]
