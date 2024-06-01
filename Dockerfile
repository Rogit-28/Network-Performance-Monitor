# Multi-stage Dockerfile for Network Performance Monitor
FROM python:3.11-slim as backend-builder

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy Python requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Frontend builder stage
FROM node:18-alpine as frontend-builder

# Set working directory
WORKDIR /app

# Copy frontend files
COPY frontend/app1/ ./frontend/app1/

# Change to frontend directory and install dependencies
WORKDIR /app/frontend/app1
RUN npm ci --only=production

# Build the Next.js application
RUN npm run build

# Production stage
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy Python dependencies from builder stage
COPY --from=backend-builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages

# Copy application code
COPY . .

# Copy built frontend from builder stage
COPY --from=frontend-builder /app/frontend/app1/.next ./.next
COPY --from=frontend-builder /app/frontend/app1/public ./public
COPY --from=frontend-builder /app/frontend/app1/node_modules ./node_modules
COPY --from=frontend-builder /app/frontend/app1/package.json ./package.json
COPY --from=frontend-builder /app/frontend/app1/next.config.ts ./next.config.ts

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser && \
    chown -R appuser:appuser /app
USER appuser

# Expose ports
EXPOSE 8000 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

# Start both backend and frontend
CMD ["sh", "-c", "python -m uvicorn backend.api.main:app --host 0.0.0.0 --port 8000 --workers 4 & cd frontend/app1 && npm start"]
