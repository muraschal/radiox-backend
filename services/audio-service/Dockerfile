# 🚀 RadioX Audio Service - STANDALONE VERSION
# Fully independent audio service without problematic base image imports
# Author: Marcel & Claude - Building the Next Unicorn 🦄

FROM python:3.9-slim as audio-service

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Create app user
RUN useradd -m -u 1000 app
RUN chown -R app:app /app

# Copy and install requirements
COPY services/audio-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY services/audio-service/main.py .

# Switch to app user
USER app

# Service-specific environment
ENV SERVICE_NAME=audio-service
ENV SERVICE_PORT=8002
ENV AUDIO_CACHE_DIR=/app/audio_cache

# Health check
HEALTHCHECK --interval=60s --timeout=30s --start-period=20s --retries=3 \
    CMD curl -f http://localhost:8002/health || exit 1

# Start the audio service - Use Python main for dynamic port
CMD ["python", "main.py"] 