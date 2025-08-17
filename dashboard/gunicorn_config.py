# Production Dashboard Server (Gunicorn)
# More stable than Flask development server

import multiprocessing
from app import app

# Gunicorn configuration
bind = "0.0.0.0:5000"
workers = 2
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100
timeout = 60
keepalive = 5
preload_app = True
reload = False

# Logging
accesslog = "/volume1/Main/Main/ParkerPOsOCR/dashboard/logs/access.log"
errorlog = "/volume1/Main/Main/ParkerPOsOCR/dashboard/logs/error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# Process naming
proc_name = "parker_dashboard"

# Security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
