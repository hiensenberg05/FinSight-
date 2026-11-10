# FinSight Backend Dockerfile
FROM python:3.11-slim

# Prevent Python from writing .pyc and enable buffer-less stdout
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    PORT=8000

WORKDIR /app

# Install system dependencies for Playwright, networking, and system libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    libglib2.0-0 \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /app/backend/requirements.txt

# Install Playwright browser binary
RUN playwright install chromium

# Copy backend application source
COPY backend /app/backend
COPY alembic.ini /app/alembic.ini

# Expose backend service port
EXPOSE 8000

# Health check against native /health endpoint
HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/health || exit 1

# Start Uvicorn ASGI server with dynamic port support (e.g. for Render $PORT)
CMD ["sh", "-c", "uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
