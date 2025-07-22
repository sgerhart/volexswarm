FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for scientific computing and health checks
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt /app/

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy agent code
COPY ./agents/signal /app/
COPY ./common /app/common/

# Create non-root user for security
RUN useradd -m -u 1000 signal && chown -R signal:signal /app
USER signal

# Expose port
EXPOSE 8003

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8003/health || exit 1

# Run the application
CMD ["python", "main.py"] 