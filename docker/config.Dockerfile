FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt /app/

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy agent code
COPY ./agents/config /app/
COPY ./common /app/common/

# Create user for security
RUN useradd -m -u 1000 config && chown -R config:config /app

# Switch to non-root user
USER config

# Expose port
EXPOSE 8012

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8012/health || exit 1

# Run the application
CMD ["python", "main.py"] 