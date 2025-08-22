FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy agent code
COPY agents/news_sentiment/ ./agents/news_sentiment/
COPY agents/agentic_framework/ ./agents/agentic_framework/
COPY common/ ./common/

# Create necessary directories
RUN mkdir -p logs

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Create non-root user for security
RUN useradd -m -u 1000 news_sentiment && chown -R news_sentiment:news_sentiment /app
USER news_sentiment

# Expose port (kept for compatibility, but agentic version doesn't use HTTP)
EXPOSE 8024

# Health check - agentic version doesn't have HTTP endpoints, so we'll check if process is running
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD ps aux | grep "python.*main.py" | grep -v grep || exit 1

# Run the agentic application
CMD ["python", "agents/news_sentiment/main.py"] 