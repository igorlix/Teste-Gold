# ================================
# Multi-stage Dockerfile for AWS ECS
# Busca Avançada API
# ================================

# ========== Stage 1: Builder ==========
FROM python:3.11-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /build

# Copy requirements first (better layer caching)
COPY requirements.txt .

# Install Python dependencies in a virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt


# ========== Stage 2: Runtime ==========
FROM python:3.11-slim

# Install runtime dependencies only
RUN apt-get update && apt-get install -y \
    --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN useradd -m -u 1000 appuser && \
    mkdir -p /app && \
    chown -R appuser:appuser /app

# Set working directory
WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder --chown=appuser:appuser /opt/venv /opt/venv

# Set environment variables
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    WHO_IS_RUNNING_THIS=ENDPOINT_MLFLOW \
    ENVIRONMENT=production \
    LOG_LEVEL=INFO

# Copy application code
COPY --chown=appuser:appuser ./src /app/src
COPY --chown=appuser:appuser ./api /app/api

# Switch to non-root user
USER appuser

# Expose port (ECS will map this)
EXPOSE 9001

# Health check for AWS ECS
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:9001/health || exit 1

# Run FastAPI with uvicorn
# Using --workers 1 for ECS (horizontal scaling preferred over multiple workers)
CMD ["uvicorn", "api.main:app", \
     "--host", "0.0.0.0", \
     "--port", "9001", \
     "--workers", "1", \
     "--log-level", "info", \
     "--access-log"]
