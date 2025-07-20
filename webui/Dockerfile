# Multi-stage build for VolexSwarm Web UI
FROM node:18-alpine AS frontend-builder

WORKDIR /app
COPY package*.json ./
RUN npm install --production --legacy-peer-deps

COPY . .
RUN npm run build

# Backend stage
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements and install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ ./backend/

# Copy built frontend
COPY --from=frontend-builder /app/build ./webui/build

# Expose port
EXPOSE 8005

# Run the application
CMD ["python", "backend/main.py"] 