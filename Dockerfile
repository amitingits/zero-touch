# ============================================================================
# Stage 1 — Build dependencies
# ============================================================================
FROM python:3.11-slim AS builder

WORKDIR /build

# Install build-time OS dependencies (none needed for scikit-learn wheels,
# but this layer exists for future extensibility)
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc && \
    rm -rf /var/lib/apt/lists/*

COPY service/requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ============================================================================
# Stage 2 — Production image
# ============================================================================
FROM python:3.11-slim AS production

LABEL maintainer="Amit Das"
LABEL project="zero-touch-ml"
LABEL description="ML Inference API — Iris Random Forest Classifier"

# Security: run as non-root user
RUN groupadd -r mluser && useradd -r -g mluser -d /app -s /sbin/nologin mluser

WORKDIR /app

# Copy installed Python packages from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY model/artifacts/ ./model/artifacts/
COPY service/ ./service/

# Set ownership
RUN chown -R mluser:mluser /app

USER mluser

# Environment
ENV PORT=5000
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

EXPOSE 5000

# Health check — Kubernetes probes supplement this, but it's a Docker best practice
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/health')" || exit 1

# Production entrypoint via Gunicorn
CMD ["gunicorn", "--config", "service/gunicorn.conf.py", "service.app:app"]
