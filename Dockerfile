# Havilah OS — Production Dockerfile
# Multi-stage build for minimal image size

# ── Stage 1: Builder ───────────────────────────────────────────
FROM python:3.13-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ── Stage 2: Runtime ───────────────────────────────────────────
FROM python:3.13-slim AS runtime

WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 havilah && chown -R havilah:havilah /app
USER havilah

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    HAVILAH_ENV=production

# Default port (Railway injects PORT env var at runtime)
ENV PORT=8000
EXPOSE 8000

# Health check (uses $PORT so it works regardless of injected port)
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/health || exit 1

# Run with uvicorn — shell form so $PORT is expanded at runtime
# Railway overrides this with the startCommand in railway.json,
# but this CMD makes the image runnable standalone too (e.g. fly.io, local docker)
CMD sh -c 'uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 4'
