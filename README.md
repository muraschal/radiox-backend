# 🚀 RadioX Backend - Google Engineering Standards
**Professional AI Radio Show Generation Platform**

[![Architecture](https://img.shields.io/badge/Architecture-Microservices-blue)](https://microservices.io/)
[![Standards](https://img.shields.io/badge/Standards-Google%20Engineering-green)](https://google.github.io/eng-practices/)
[![Status](https://img.shields.io/badge/Status-Production%20Ready-success)](https://github.com/marcel/radiox-backend)

## 🏗️ **Clean Architecture Overview**

RadioX follows **Google Engineering Principles**:
- **Single Responsibility**: Each service has one clear purpose
- **Separation of Concerns**: Database, HTTP, and business logic separated
- **Fail Fast**: Early validation and clear error handling
- **DRY Principle**: Centralized configuration and shared components
- **Self-Documenting**: Clear naming and comprehensive documentation

```
🦄 RADIOX MICROSERVICES ARCHITECTURE
┌─────────────────────────────────────────────────────────────┐
│                    API Gateway (8000)                      │
│                   Central Routing Hub                      │
└─────────────────────────┬───────────────────────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
   ┌────▼────┐      ┌─────▼─────┐      ┌───▼────┐
   │  Show   │      │  Content  │      │  Audio │
   │ Service │      │  Service  │      │ Service│
   └─────────┘      └───────────┘      └────────┘
        │                 │                 │
   ┌────▼────┐      ┌─────▼─────┐      ┌───▼────┐
   │ Speaker │      │   Data    │      │ Media  │
   │ Service │      │  Service  │      │ Service│
   └─────────┘      └───────────┘      └────────┘
        │                 │                 │
        └─────────────────┼─────────────────┘
                          │
                   ┌─────▼─────┐
                   │Analytics  │
                   │ Service   │
                   └───────────┘
```

## 🚀 **Quick Start**

### **Production Deployment**
```bash
# 1. Clone and setup
git clone https://github.com/marcel/radiox-backend.git
cd radiox-backend

# 2. Configure environment
cp .env.example .env
# Edit .env with your API keys

# 3. Deploy with Google Engineering standards
./scripts/deploy-ultimate-radiox.sh

# 4. Verify deployment
curl http://localhost:8000/health
```

### **Development**
```bash
# Start all services
docker-compose up -d

# Check service health
curl http://localhost:8000/health | jq

# Generate a show
curl -X POST http://localhost:8000/shows/generate \
  -H "Content-Type: application/json" \
  -d '{"channel":"zurich","language":"de","news_count":2}'
```

## 📋 **Service Architecture**

| Service | Port | Purpose | Dependencies |
|---------|------|---------|-------------|
| **API Gateway** | 8000 | Central routing, auth, rate limiting | All services |
| **Show Service** | Internal | AI show generation orchestration | Content, Audio, Data |
| **Content Service** | Internal | News aggregation, weather, crypto | External APIs |
| **Audio Service** | Internal | TTS generation, audio processing | ElevenLabs API |
| **Media Service** | Internal | File upload, image processing | Supabase Storage |
| **Speaker Service** | Internal | Voice configuration management | Supabase |
| **Data Service** | Internal | Database operations, caching | Supabase, Redis |
| **Analytics Service** | Internal | Performance monitoring, metrics | All services |

## 🔧 **Configuration Management**

### **Centralized Configuration**
- `config/settings.py` - Application settings
- `config/api_config.py` - API configurations  
- `config/http_client_factory.py` - HTTP client management
- `database/client_factory.py` - Database connection factory

### **Environment Variables**
```bash
# Required
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_anon_key

# Optional
OPENAI_API_KEY=your_openai_key
ELEVENLABS_API_KEY=your_elevenlabs_key
NEWS_API_KEY=your_news_api_key
WEATHER_API_KEY=your_weather_api_key
```

## 🧪 **Quality Assurance**

### **Testing**
```bash
# Validate all configurations
./scripts/validate-ports.sh

# Test all services
./scripts/test-all-services.sh

# Monitor performance
./scripts/monitor-radiox.sh
```

### **Health Monitoring**
```bash
# Overall system health
curl http://localhost:8000/health

# Database performance
curl http://localhost:8000/database/stats

# HTTP client performance  
curl http://localhost:8000/http/stats
```

## 📊 **API Reference**

### **Show Generation**
```bash
# Generate show
POST /shows/generate
{
  "channel": "zurich",
  "language": "de", 
  "news_count": 2,
  "duration_minutes": 3
}

# List shows
GET /shows?limit=10&offset=0

# Get specific show
GET /shows/{session_id}

# Show statistics
GET /shows/stats
```

### **Content & Configuration**
```bash
# Get content (news, weather, crypto)
GET /content?news_count=3&language=de&location=zurich

# Speaker configurations
GET /speakers
GET /speakers/{speaker_name}

# System configuration
GET /config
```

## 🔒 **Security & Performance**

### **Security Features**
- Row Level Security (RLS) on all database tables
- API key validation and rotation
- Rate limiting and request validation
- Secure environment variable management

### **Performance Optimizations**
- Database connection pooling with factory pattern
- HTTP client connection reuse
- Redis caching for frequently accessed data
- Optimized Docker images with multi-stage builds

## 🚀 **Deployment**

### **Production Deployment**
```bash
# Full deployment with validation
./scripts/deploy-ultimate-radiox.sh

# Production environment
docker-compose -f docker-compose.production.yml up -d
```

### **Monitoring**
```bash
# Real-time monitoring
./scripts/monitor-radiox.sh

# Service logs
docker-compose logs -f [service-name]
```

## 📚 **Documentation**

- [API Reference](docs/user-guide/api-reference.md)
- [Frontend Integration](docs/user-guide/frontend-api-integration.md)
- [Architecture Guide](docs/developer-guide/architecture.md)
- [Local Development](docs/developer-guide/local-development.md)
- [Tech Stack](docs/developer-guide/tech-stack.md)

## 🏆 **Google Engineering Standards Compliance**

✅ **Single Responsibility Principle**: Each service has one clear purpose  
✅ **Separation of Concerns**: Clean architecture layers  
✅ **Fail Fast**: Early validation and error handling  
✅ **DRY Principle**: Centralized configuration and shared components  
✅ **Self-Documenting Code**: Clear naming and comprehensive docs  
✅ **Performance First**: Optimized factories and caching  
✅ **Security by Design**: RLS, validation, and secure practices  

---

**Built with ❤️ using Google Engineering Principles**  
*Professional AI Radio Show Generation Platform* 