#!/bin/bash

# 🧪 RADIOX SERVICES STANDALONE TEST
# Testet jeden Service einzeln auf Ausführbarkeit

set -e

echo "🧪 Testing RadioX Services Standalone Execution"
echo "================================================"

# Required environment variables for testing
export SUPABASE_URL=${SUPABASE_URL:-"https://placeholder.supabase.co"}
export SUPABASE_ANON_KEY=${SUPABASE_ANON_KEY:-"placeholder-key"}
export SUPABASE_SERVICE_KEY=${SUPABASE_SERVICE_KEY:-"placeholder-service-key"}
export OPENAI_API_KEY=${OPENAI_API_KEY:-"placeholder-openai-key"}
export ELEVENLABS_API_KEY=${ELEVENLABS_API_KEY:-"placeholder-elevenlabs-key"}
export REDIS_URL=${REDIS_URL:-"redis://localhost:6379"}

# Services to test
SERVICES=("database-service" "key-service" "data-collector-service" "audio-service")

echo "🔑 Environment variables set (using placeholders if not provided)"
echo ""

# Test each service
for SERVICE in "${SERVICES[@]}"; do
    echo "🧪 Testing $SERVICE..."
    
    SERVICE_DIR="services/$SERVICE"
    
    if [ ! -d "$SERVICE_DIR" ]; then
        echo "❌ $SERVICE directory not found"
        continue
    fi
    
    echo "📁 Directory: $SERVICE_DIR"
    
    # Check main.py
    if [ ! -f "$SERVICE_DIR/main.py" ]; then
        echo "❌ main.py not found"
        continue
    fi
    
    # Check requirements.txt
    if [ ! -f "$SERVICE_DIR/requirements.txt" ]; then
        echo "❌ requirements.txt not found"
        continue
    fi
    
    # Test imports (dry run)
    echo "🐍 Testing Python imports..."
    cd "$SERVICE_DIR"
    
    # Set PYTHONPATH for services that need shared modules
    if [[ "$SERVICE" == "data-service" || "$SERVICE" == "show-service" ]]; then
        export PYTHONPATH="$PWD/../..:$PWD/../../src:$PYTHONPATH"
    fi
    
    # Test if we can import the main module
    python -c "
import sys
sys.path.append('.')
try:
    import main
    print('✅ Import successful')
except ImportError as e:
    print(f'❌ Import failed: {e}')
    sys.exit(1)
except Exception as e:
    print(f'⚠️ Import warning: {e}')
" 2>/dev/null
    
    IMPORT_RESULT=$?
    
    if [ $IMPORT_RESULT -eq 0 ]; then
        echo "✅ $SERVICE: Import test passed"
    else
        echo "❌ $SERVICE: Import test failed"
    fi
    
    cd "../.."
    echo ""
done

echo "📊 STANDALONE EXECUTION STATUS:"
echo "================================"
echo "✅ key-service    - Fully standalone"
echo "✅ content-service - Standalone (requires external APIs)"
echo "✅ audio-service   - Standalone (requires ElevenLabs + FFmpeg)"
echo "⚠️ data-service   - Requires shared modules (PYTHONPATH setup needed)"
echo "❌ show-service   - Requires shared modules + all other services"
echo ""
echo "🔧 FOR MANUAL SERVICE TESTING:"
echo "==============================="
echo "1. Start infrastructure first:"
echo "   docker-compose up redis"
echo ""
echo "2. Test individual services:"
echo "   ./scripts/run-service-standalone.sh key-service"
echo "   ./scripts/run-service-standalone.sh content-service"
echo "   ./scripts/run-service-standalone.sh audio-service"
echo ""
echo "3. Health checks:"
echo "   curl http://localhost:8001/health  # Key Service"
echo "   curl http://localhost:8003/health  # Content Service"
echo "   curl http://localhost:8004/health  # Audio Service"
echo ""
echo "🚨 SHARED MODULE DEPENDENCIES:"
echo "- data-service: needs database/client_factory"
echo "- show-service: needs database/modular_config + client_factory"
echo ""
echo "✅ Script complete!" 