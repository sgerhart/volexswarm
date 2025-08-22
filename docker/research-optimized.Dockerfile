# Multi-stage build for Research Agent
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements-minimal.txt /app/requirements.txt

# Install Python dependencies in a virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.11-slim

WORKDIR /app

# Install only runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    openssl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code
COPY ./agents /app/agents/
COPY ./common /app/common/

# Copy the main.py file to the app root
COPY ./agents/research/main.py /app/main.py

# Create necessary directories
RUN mkdir -p /app/logs /app/data /app/security

# Create non-root user for security
RUN useradd -m -u 1000 research && \
    chown -R research:research /app && \
    chmod 755 /app && \
    chmod 700 /app/security

# Switch to non-root user
USER research

# Set environment variables
ENV PYTHONPATH=/app
ENV SECURITY_ENABLED=true
ENV JWT_SECRET=${JWT_SECRET:-volexswarm-jwt-secret-2024}
ENV SECURITY_LOG_LEVEL=INFO

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["python", "main.py"] 