#!/bin/bash

# 🔧 RADIOX SERVICE STANDALONE RUNNER
# Startet einzelne Services für debugging

set -e

if [ $# -eq 0 ]; then
    echo "❌ Usage: $0 <service-name> [port]"
    echo ""
    echo "Available services:"
    echo "  key-service     (default port: 8001)"
    echo "  database-service (default port: 8001)"
    echo "  content-service (default port: 8003)"
    echo "  audio-service   (default port: 8004)"
    echo "  media-service   (default port: 8005)"
    echo "  speaker-service (default port: 8006)"
    echo "  show-service    (default port: 8007)"
    echo "  analytics-service (default port: 8008)"
    echo ""
    echo "Example: $0 key-service 8001"
    exit 1
fi

SERVICE_NAME=$1
PORT=${2:-"auto"}

# Service directory mapping
declare -A SERVICE_DIRS=(
    ["key-service"]="services/key-service"
    ["database-service"]="services/database-service"
    ["content-service"]="services/content-service"
    ["audio-service"]="services/audio-service"
    ["media-service"]="services/media-service"
    ["speaker-service"]="services/speaker-service"
    ["show-service"]="services/show-service"
    ["analytics-service"]="services/analytics-service"
)

# Default ports
declare -A DEFAULT_PORTS=(
    ["key-service"]="8001"
    ["database-service"]="8001"
    ["content-service"]="8003"
    ["audio-service"]="8004"
    ["media-service"]="8005"
    ["speaker-service"]="8006"
    ["show-service"]="8007"
    ["analytics-service"]="8008"
)

# Check if service exists
if [[ ! -v SERVICE_DIRS[$SERVICE_NAME] ]]; then
    echo "❌ Unknown service: $SERVICE_NAME"
    exit 1
fi

SERVICE_DIR="${SERVICE_DIRS[$SERVICE_NAME]}"

if [ "$PORT" = "auto" ]; then
    PORT="${DEFAULT_PORTS[$SERVICE_NAME]}"
fi

echo "🚀 Starting $SERVICE_NAME on port $PORT"
echo "📁 Service directory: $SERVICE_DIR"

# Check if service directory exists
if [ ! -d "$SERVICE_DIR" ]; then
    echo "❌ Service directory not found: $SERVICE_DIR"
    exit 1
fi

# Check if main.py exists
if [ ! -f "$SERVICE_DIR/main.py" ]; then
    echo "❌ main.py not found in $SERVICE_DIR"
    exit 1
fi

# Load environment variables
if [ -f ".env" ]; then
    echo "🔑 Loading environment from .env"
    export $(cat .env | grep -v '^#' | xargs)
fi

# Set service-specific environment variables
export SERVICE_NAME=$SERVICE_NAME
export SERVICE_PORT=$PORT

# Special handling for services with shared modules
case $SERVICE_NAME in
    "database-service"|"show-service")
        echo "🔧 Setting up shared modules for $SERVICE_NAME"
        export PYTHONPATH="$PWD:$PWD/src:$PYTHONPATH"
        ;;
esac

# Start service
echo "⚡ Starting service..."
echo "🌐 Health check: http://localhost:$PORT/health"
echo "📚 API docs: http://localhost:$PORT/docs"
echo ""

cd "$SERVICE_DIR"

# Install dependencies if needed
if [ -f "requirements.txt" ]; then
    echo "📦 Installing dependencies..."
    pip install -r requirements.txt
fi

# Start the service
python main.py --port $PORT 2>&1 | tee "../../logs/${SERVICE_NAME}-standalone.log" 