"""
Gunicorn configuration for production deployment.
"""

import multiprocessing

# Bind to all interfaces on port 5000
bind = "0.0.0.0:5000"

# Workers = 2 × CPU cores + 1  (capped for ML workloads)
workers = min(multiprocessing.cpu_count() * 2 + 1, 4)

# Timeout (seconds) — generous for model loading
timeout = 120

# Graceful restart timeout
graceful_timeout = 30

# Preload app so model loads once, shared across workers (copy-on-write)
preload_app = True

# Access log
accesslog = "-"
errorlog = "-"
loglevel = "info"
