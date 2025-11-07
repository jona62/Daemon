FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    sqlite3 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy source code first
COPY task_daemon/ ./task_daemon/
COPY examples/ ./examples/
COPY pyproject.toml README.md ./

# Install the package
RUN pip install -e .

# Create data directory
RUN mkdir -p /data

# Expose port
EXPOSE 8080

# Environment variables
ENV DAEMON_DB_PATH=/data/queue.db
ENV DAEMON_HOST=0.0.0.0
ENV DAEMON_PORT=8080
ENV DAEMON_WORKERS=4
ENV DAEMON_LOG_LEVEL=INFO

# Run Docker service example
CMD ["python", "examples/docker-service.py"]
