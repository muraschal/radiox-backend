# Development Setup

<div align="center">

![Development](https://img.shields.io/badge/development-setup-green)
![Docker](https://img.shields.io/badge/docker-required-2496ED)
![Python](https://img.shields.io/badge/python-3.9+-blue)

**Complete development environment setup for RadioX microservices**

[🏠 Documentation](../) • [🏗️ Architecture](architecture.md) • [🔧 Services](services.md) • [🚀 Production](../deployment/production.md)

</div>

---

## Quick Start

### Prerequisites
```bash
# Required software
- Docker & Docker Compose (latest)
- Python 3.9+ (for CLI client)
- Git
- Make (optional, for convenience commands)
```

### 5-Minute Setup
```bash
# 1. Clone repository
git clone https://github.com/muraschal/radiox-backend.git
cd radiox-backend

# 2. Environment configuration
cp env.example .env
# Edit .env with your API keys

# 3. Start all microservices
make up                    # or: docker-compose up -d

# 4. Verify services
make health               # or: curl http://localhost:8000/services/status

# 5. Generate your first show
python main.py --news-count 3 --preset zurich
```

---

## Environment Configuration

### Required API Keys
```bash
# .env file configuration
# OpenAI (GPT-4 + DALL-E 3)
OPENAI_API_KEY=sk-your-key-here

# ElevenLabs (TTS)
ELEVENLABS_API_KEY=your-key-here

# Supabase (Database)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key-here

# Optional APIs
COINMARKETCAP_API_KEY=your-key-here        # Bitcoin data
OPENWEATHERMAP_API_KEY=your-key-here       # Weather data
```

### Service Configuration
```bash
# Docker network settings
DOCKER_NETWORK=radiox-network

# Service URLs (auto-configured in Docker)
API_GATEWAY_URL=http://localhost:8000
SHOW_SERVICE_URL=http://localhost:8001
CONTENT_SERVICE_URL=http://localhost:8002
AUDIO_SERVICE_URL=http://localhost:8003
MEDIA_SERVICE_URL=http://localhost:8004
SPEAKER_SERVICE_URL=http://localhost:8005
DATA_SERVICE_URL=http://localhost:8006
ANALYTICS_SERVICE_URL=http://localhost:8007

# Redis cache
REDIS_URL=redis://localhost:6379
```

---

## Microservices Architecture

### Service Structure
```
radiox-backend/
├── services/                    # 8 Docker microservices
│   ├── api-gateway/            # Port 8000 - Central routing
│   │   ├── Dockerfile
│   │   ├── main.py
│   │   └── requirements.txt
│   ├── show-service/           # Port 8001 - Show orchestration
│   ├── content-service/        # Port 8002 - News + GPT
│   ├── audio-service/          # Port 8003 - TTS + mixing
│   ├── media-service/          # Port 8004 - Files + cover art
│   ├── speaker-service/        # Port 8005 - Voice config
│   ├── data-service/           # Port 8006 - Database ops
│   └── analytics-service/      # Port 8007 - Metrics
├── main.py                     # CLI client (HTTP → services)
├── docker-compose.yml          # Service orchestration
├── Makefile                    # Development commands
└── docs/                       # Documentation
```

### Development Workflow
```bash
# Start all services in development mode
make dev                       # Start with auto-reload
make up                        # Start production mode
make down                      # Stop all services

# Individual service development
make up-service SERVICE=content-service
make logs-service SERVICE=show-service
make restart-service SERVICE=audio-service

# Health monitoring
make health                    # Check all services
make status                    # Detailed service status
make logs                      # View all logs
```

---

## Local Development

### Docker-First Development
```bash
# Build all services
make build

# Start with live reload (recommended for development)
make dev

# Access services
curl http://localhost:8000/health              # API Gateway
curl http://localhost:8001/health              # Show Service
curl http://localhost:8002/content/news        # Content Service
```

### Individual Service Development
```bash
# Develop specific service locally
cd services/content-service

# Install dependencies
pip install -r requirements.txt

# Run service locally (outside Docker)
python -m uvicorn main:app --reload --port 8002

# Test service
curl http://localhost:8002/health
```

### Hot Reload Setup
```yaml
# docker-compose.override.yml (auto-loaded in development)
version: '3.8'
services:
  content-service:
    volumes:
      - ./services/content-service:/app
    environment:
      - RELOAD=true
    command: uvicorn main:app --host 0.0.0.0 --port 8002 --reload
```

---

## Testing

### Unit Testing
```bash
# Test individual service
cd services/content-service
pytest tests/ -v --cov=.

# Test all services
make test

# Test with coverage
make test-coverage
```

### Integration Testing
```bash
# Start test environment
docker-compose -f docker-compose.test.yml up

# Run integration tests
pytest tests/integration/ -v

# End-to-end testing
python main.py --test-mode --news-count 1
```

### Service Health Testing
```bash
# Quick health check
make health

# Detailed service testing
curl -X POST http://localhost:8002/content/script \
  -H "Content-Type: application/json" \
  -d '{"content": "Test news", "preset": "zurich"}'
```

---

## Debugging

### Service Logs
```bash
# View all service logs
make logs

# View specific service
make logs-service SERVICE=content-service

# Follow logs in real-time
docker-compose logs -f content-service

# View last 100 lines
docker-compose logs --tail=100 show-service
```

### Debug Mode
```bash
# Start services in debug mode
DEBUG=true make up

# Debug specific service
cd services/audio-service
DEBUG=true python -m uvicorn main:app --reload --port 8003
```

### Service Communication Debug
```bash
# Test inter-service communication
docker-compose exec api-gateway curl http://content-service:8002/health
docker-compose exec show-service curl http://audio-service:8003/voices

# Network debugging
docker network ls
docker network inspect radiox_default
```

---

## Database Development

### Supabase Setup
```bash
# Database schema management
python -c "from database.schema_manager import setup_database; setup_database()"

# View database status
curl http://localhost:8006/health

# Manual database operations
python -c "
from database.supabase_client import get_supabase_client
client = get_supabase_client()
result = client.table('show_presets').select('*').execute()
print(result.data)
"
```

### Redis Development
```bash
# Connect to Redis
docker-compose exec redis redis-cli

# View cached data
redis-cli KEYS "*"
redis-cli GET "content:news:latest"

# Clear cache
redis-cli FLUSHALL
```

---

## Performance Development

### Profiling
```bash
# Profile service performance
cd services/content-service
python -m cProfile -o profile.stats main.py

# Memory profiling
pip install memory-profiler
python -m memory_profiler main.py
```

### Load Testing
```bash
# Install load testing tools
pip install locust

# Run load tests
locust -f tests/load/locustfile.py --host=http://localhost:8000
```

### Monitoring in Development

#### Live Monitoring Dashboard
```bash
# RadioX Live Monitoring Dashboard - Real-time service status
./scripts/monitor-radiox.sh

# Features:
# - Real-time service health (8 microservices)
# - Production API stats
# - Live activity logs
# - Interactive commands: [r] Restart | [l] Live Logs | [s] Status | [q] Quit
```

#### Traditional Monitoring Stack
```bash
# Start with monitoring stack
docker-compose -f docker-compose.monitoring.yml up

# Access monitoring
open http://localhost:9090    # Prometheus
open http://localhost:3000    # Grafana
open http://localhost:8080    # Service dashboards
```

#### Remote LXC Monitoring
```bash
# Monitor RadioX on remote LXC container
ssh root@radiox-backend
cd /opt/radiox-backend
./scripts/monitor-radiox.sh

# Features live status of:
# ✅ API Gateway (8000)      ✅ Show Service (8001) 
# ✅ Content Service (8002)  ✅ Audio Service (8003)
# ✅ Media Service (8004)    ✅ Speaker Service (8005)
# ✅ Data Service (8006)     ✅ Analytics Service (8007)
```

---

## CLI Development

### Main CLI Client
```bash
# CLI client development (main.py)
# This is now an HTTP client that communicates with microservices

# Basic usage
python main.py --help
python main.py --news-count 3
python main.py --preset basel --no-audio

# Development modes
python main.py --debug
python main.py --test-services
python main.py --health-check
```

### Service-Specific CLI Tools
```bash
# Content service testing
curl http://localhost:8002/content/news | jq .

# Audio service testing
curl -X POST http://localhost:8003/generate \
  -H "Content-Type: application/json" \
  -d '{"text": "Test audio", "voice_id": "marcel"}'

# Show generation testing
curl -X POST http://localhost:8001/generate \
  -H "Content-Type: application/json" \
  -d '{"preset_name": "zurich", "news_count": 2}'
```

---

## IDE Setup

### VS Code Configuration
```json
// .vscode/settings.json
{
    "python.defaultInterpreterPath": "./venv/bin/python",
    "python.formatting.provider": "black",
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": true,
    "files.exclude": {
        "**/__pycache__": true,
        "**/venv": true,
        "**/.pytest_cache": true
    },
    "docker.commands.build": "${workspaceFolder}/Makefile",
    "docker.commands.compose": "${workspaceFolder}/docker-compose.yml"
}
```

### Debug Configuration
```json
// .vscode/launch.json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Debug Content Service",
            "type": "python",
            "request": "launch",
            "program": "services/content-service/main.py",
            "cwd": "${workspaceFolder}/services/content-service",
            "env": {
                "DEBUG": "true"
            }
        },
        {
            "name": "Debug CLI Client",
            "type": "python",
            "request": "launch",
            "program": "main.py",
            "args": ["--news-count", "2", "--debug"],
            "cwd": "${workspaceFolder}"
        }
    ]
}
```

---

## Makefile Commands

### Available Commands
```bash
# Service Management
make up              # Start all services
make down            # Stop all services
make restart         # Restart all services
make build           # Build all Docker images
make clean           # Remove containers and volumes

# Development
make dev             # Start with hot reload
make logs            # View all logs
make health          # Check service health
make test            # Run all tests

# Individual Services
make up-service SERVICE=content-service
make logs-service SERVICE=show-service
make restart-service SERVICE=audio-service

# Database
make db-setup        # Initialize database
make db-reset        # Reset database
make db-backup       # Backup database

# Utilities
make format          # Format code with black
make lint            # Run linting
make docs            # Generate documentation
```

### Custom Development Commands
```bash
# Add to your ~/.bashrc or ~/.zshrc
alias radiox-start='cd ~/radiox-backend && make up'
alias radiox-stop='cd ~/radiox-backend && make down'
alias radiox-logs='cd ~/radiox-backend && make logs'
alias radiox-health='cd ~/radiox-backend && make health'
alias radiox-generate='cd ~/radiox-backend && python main.py --news-count 3'
```

---

## Troubleshooting

### Common Issues

#### Services Not Starting
```bash
# Check Docker daemon
docker --version
docker-compose --version

# Check ports availability
lsof -i :8000-8007

# Reset Docker environment
make clean
docker system prune -f
make build
make up
```

#### Database Connection Issues
```bash
# Check Supabase configuration
curl -H "apikey: $SUPABASE_KEY" "$SUPABASE_URL/rest/v1/"

# Test database service
curl http://localhost:8006/health

# Reset database connection
make restart-service SERVICE=data-service
```

#### API Key Issues
```bash
# Verify environment variables
docker-compose exec api-gateway env | grep API_KEY

# Test external APIs
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
  https://api.openai.com/v1/models

curl -H "Authorization: Bearer $ELEVENLABS_API_KEY" \
  https://api.elevenlabs.io/v1/voices
```

### Performance Issues
```bash
# Check resource usage
docker stats

# Check service health
make health

# View detailed logs
make logs-service SERVICE=audio-service | grep ERROR

# Monitor network traffic
docker-compose exec api-gateway netstat -tuln
```

---

## Related Documentation

- **[🏗️ Architecture](architecture.md)** - System design overview
- **[🔧 Services](services.md)** - Detailed service documentation
- **[🧪 Testing](testing.md)** - Testing strategies and tools
- **[🚀 Production](../deployment/production.md)** - Production deployment

---

<div align="center">

**🛠️ Development environment optimized for productivity**

[🏗️ View Architecture](architecture.md) • [🔧 Explore Services](services.md) • [🧪 Run Tests](testing.md)

</div> 