# Use Python 3.11 slim image as base
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY tools/file_operations /app/tools/file_operations
COPY config.yaml /app/config.yaml

# Create necessary directories
RUN mkdir -p /app/.ai_cache /app/exports /app/logs

# Set environment variables
ENV PYTHONPATH=/app
ENV OPENROUTER_API_KEY=""
ENV CONFIG_PATH=/app/config.yaml

# Create non-root user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Set entrypoint
ENTRYPOINT ["python", "-m", "tools.file_operations.cli"]

# Default command (can be overridden)
CMD ["--help"]
