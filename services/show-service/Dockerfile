# 🚀 RadioX Show Service - ULTIMATE DOCKER OPTIMIZATION
# Uses the new multi-stage base image - 90% less redundancy!
# Author: Marcel & Claude - Building the Next Unicorn 🦄

FROM radiox-service-base:latest as show-service

# Copy service-specific requirements
COPY services/show-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared modules
COPY database ./database
COPY config ./config

# Copy application code
COPY services/show-service/main.py .

# Service-specific environment
ENV SERVICE_NAME=show-service
ENV SERVICE_PORT=8000

# Override health check for show service (longer timeout for AI processing)
HEALTHCHECK --interval=45s --timeout=20s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start the show service
CMD ["uvicorn", "main:app", "--host", "0.0.0", "--port", "8000", "--workers", "1"] 