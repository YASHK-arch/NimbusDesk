# Stage 1: Build the React TypeScript frontend
FROM node:20-alpine AS frontend-builder
WORKDIR /app/ui

# Install dependencies
COPY ui/package.json ui/package-lock.json* ./
RUN npm ci || npm install

# Build production assets
COPY ui/ ./
RUN npm run build

# Stage 2: Python Backend runtime
FROM python:3.11-slim
WORKDIR /app

# Ensure curl is available for health checks
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

# Install Python backend dependencies
COPY pyproject.toml ./
RUN pip install --no-cache-dir .

# Copy backend application subsystems
COPY orchestrator/ ./orchestrator/
COPY agents/ ./agents/
COPY state/ ./state/
COPY simulation/ ./simulation/
COPY conflict/ ./conflict/
COPY verification/ ./verification/
COPY report/ ./report/
COPY api/ ./api/
COPY data/ ./data/

# Copy compiled frontend SPA from builder stage
COPY --from=frontend-builder /app/ui/dist ./ui/dist

EXPOSE 8000

ENV LLM_MODE=mock
ENV PYTHONUNBUFFERED=1

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "api.app:app", "--host", "0.0.0.0", "--port", "8000"]

