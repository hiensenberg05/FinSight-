# ========================================================
# FinSight Unified Full-Stack Dockerfile
# Builds React Frontend + FastAPI Backend in a Single Container
# ========================================================

# --------------------------------------------------------
# Stage 1: Build React 19 / Vite Frontend SPA
# --------------------------------------------------------
FROM node:20-alpine AS frontend-builder

WORKDIR /build

# Copy dependency manifests
COPY frontend/package*.json ./
RUN npm ci || npm install

# Copy frontend source
COPY frontend ./

# Build production bundle into /build/dist
RUN npm run build

# --------------------------------------------------------
# Stage 2: Production ASGI Server (Python 3.11 + Playwright)
# --------------------------------------------------------
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    PORT=8000

WORKDIR /app

# Install system dependencies for Playwright headless Chromium
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

# Install Python requirements
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /app/requirements.txt

# Install Playwright Chromium browser binary
RUN playwright install chromium

# Copy backend source code & config
COPY backend /app/backend
COPY alembic.ini /app/alembic.ini

# Copy compiled frontend SPA bundle into /app/frontend/dist
COPY --from=frontend-builder /build/dist /app/frontend/dist

EXPOSE 8000

# Healthcheck against /health endpoint
HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/health || exit 1

# Start Uvicorn ASGI server with dynamic cloud $PORT binding
CMD ["sh", "-c", "uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
