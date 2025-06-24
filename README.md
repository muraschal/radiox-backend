# RadioX Backend - AI Radio Microservices

<div align="center">

![Python](https://img.shields.io/badge/python-3.9+-blue)
![Microservices](https://img.shields.io/badge/microservices-8-orange)
![License](https://img.shields.io/badge/license-MIT-blue)

**🎙️ AI-Powered Radio Show Generation System**

> 8 specialized microservices for automated radio production with GPT-4, ElevenLabs TTS, and professional audio engineering

[🚀 Quick Start](#quick-start) • [📚 Documentation](docs/) • [🏗️ Architecture](docs/developer-guide/architecture.md) • [🌐 Production API](https://api.radiox.cloud) • [📊 Live Status](https://api.radiox.cloud/health)

</div>

---

## Quick Start

```bash
# 1. Clone & Setup
git clone https://github.com/muraschal/radiox-backend.git
cd radiox-backend
cp env.example .env
# Configure: SUPABASE_URL, SUPABASE_KEY, OPENAI_API_KEY, ELEVENLABS_API_KEY

# 2. Start All Services
make up                         # Start 8 microservices + Redis
make health                     # Check service health

# 3. Generate Radio Show
python main.py --news-count 3 --preset zurich
```

## Architecture Overview

```
Frontend (radiox.cloud) → API Gateway (8000) → 8 Microservices → Supabase
```

| Service | Port | Purpose |
|---------|------|---------|
| **API Gateway** | 8000 | Central routing & service discovery |
| **Show Service** | 8001 | Show generation orchestration |
| **Content Service** | 8002 | News collection & GPT processing |
| **Audio Service** | 8003 | ElevenLabs TTS + professional mixing |
| **Media Service** | 8004 | File management & dashboards |
| **Speaker Service** | 8005 | Voice configuration |
| **Data Service** | 8006 | Database access & caching |
| **Analytics Service** | 8007 | Metrics & performance tracking |

## Key Features

- 🤖 **GPT-4 Powered Scripts** - Natural dialogue generation
- 🎙️ **Professional Audio** - ElevenLabs TTS + FFmpeg engineering
- 🎵 **Smart Jingle Integration** - 3-phase audio mixing
- 📊 **Real-time Data** - 25+ RSS feeds, weather, crypto
- 🎨 **AI Cover Art** - DALL-E 3 generated images
- 🌍 **Multi-language** - English/German support

## Documentation

### **🎯 Quick Access**
- **[🌐 Production API](https://api.radiox.cloud)** - Live production system
- **[📊 Live Status](https://api.radiox.cloud/services/status)** - Real-time monitoring
- **[🔧 API Docs](https://api.radiox.cloud/docs)** - Interactive Swagger UI

### **📚 Complete Documentation**

| 📖 Guide | 🎯 Audience | 📝 Content |
|----------|-------------|-------------|
| **[User Guide](docs/user-guide/)** | Content Creators | Show generation, voice setup |
| • **[Frontend API Integration](docs/user-guide/frontend-api-integration.md)** | Frontend Devs | Complete API documentation + examples |
| • **[Frontend Quick Reference](docs/user-guide/frontend-quick-reference.md)** | Frontend Devs | Copy-paste ready code snippets |
| **[Developer Guide](docs/developer-guide/)** | Engineers | Architecture, development |
| • **[Tech Stack](docs/developer-guide/tech-stack.md)** | Tech Teams | Complete technology overview |
| • **[AI Pipeline](docs/developer-guide/ai-pipeline.md)** | AI Engineers | GPT-4, TTS, ML integration |
| • **[Architecture](docs/developer-guide/architecture.md)** | System Architects | Design principles, patterns |
| **[Deployment Guide](docs/deployment/)** | DevOps | Production setup, monitoring |
| • **[Production Status](docs/deployment/production-status.md)** | Operations | Live system overview |
| • **[Cloudflare Setup](docs/deployment/cloudflare-setup.md)** | Infrastructure | CDN, security, tunnels |

## Production Environment

**🌐 Live API**: [`https://api.radiox.cloud`](https://api.radiox.cloud)

```bash
# Production Health Checks
curl https://api.radiox.cloud/health           # API Health Status
curl https://api.radiox.cloud/services/status  # All Microservices Status

# API Documentation
open https://api.radiox.cloud/docs             # Interactive Swagger UI
```

**📊 [Production Status](docs/deployment/production-status.md)** - Complete deployment details

## Development Commands

```bash
# Service Management
make up                         # Start all services
make down                       # Stop all services
make logs                       # View logs
make health                     # Check health

# Show Generation
python main.py --help          # See all options
python main.py --data-only     # Data collection only
python main.py --health-check  # Service health check
```

## Production Deployment

### Prerequisites
1. **[Cloudflare Setup](docs/deployment/cloudflare-setup.md)** - Domain & Tunnel konfigurieren
2. **Proxmox LXC** mit Docker installiert

### Deployment
```bash
# Setup Cloudflare Tunnel (once)
make setup-tunnel               # Creates https://api.radiox.cloud

# Deploy to Proxmox LXC
LXC_IP=192.168.1.100 make deploy-proxmox

# Complete production deployment
LXC_IP=192.168.1.100 make deploy-production

# Production management
make prod-up                    # Start production services
make prod-logs                  # View production logs
make prod-status                # Check service status
```

## Contributing

1. Read [Contributing Guide](docs/developer-guide/contributing.md)
2. Follow [Development Setup](docs/developer-guide/development.md)
3. Check [Architecture Docs](docs/developer-guide/architecture.md)

## License

MIT License - Professional radio production powered by AI.

---

<div align="center">

**🎙️ Ready to create broadcast-quality AI radio shows?**

[📚 Full Documentation](docs/) • [🏗️ Architecture](docs/developer-guide/architecture.md) • [🚀 Quick Start](#quick-start)

</div>
