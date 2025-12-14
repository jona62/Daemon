FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies in single layer
RUN apt-get update && apt-get install -y --no-install-recommends \
    sqlite3 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy only requirements first for better caching
COPY pyproject.toml README.md ./

# Install dependencies
RUN pip install --no-cache-dir -e .

# Copy application code
COPY task_daemon/ ./task_daemon/
COPY examples/ ./examples/

# Create non-root user
RUN useradd -m -u 1000 taskuser && \
    mkdir -p /data && \
    chown -R taskuser:taskuser /app /data

# Switch to non-root user
USER taskuser

# Expose port
EXPOSE 8080

# Environment variables
ENV DAEMON_DB_PATH=/data/queue.db \
    DAEMON_HOST=0.0.0.0 \
    DAEMON_PORT=8080 \
    DAEMON_WORKERS=4 \
    DAEMON_LOG_LEVEL=INFO \
    PYTHONUNBUFFERED=1

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Run daemon
CMD ["python", "-m", "task_daemon"]
