# RadioX Backend - Complete Tech Stack Documentation

**🏗️ Comprehensive Technical Architecture & Technology Stack**

> Production-ready AI Radio System with 8 Microservices, Global CDN, and Zero-Trust Security

---

## 📋 **Tech Stack Overview**

| Layer | Technologies | Purpose |
|-------|-------------|---------|
| **🌐 CDN & Edge** | Cloudflare CDN, HTTP/2, QUIC | Global content delivery, SSL termination |
| **🔒 Security** | Cloudflare Tunnel, Zero Trust, WAF | Secure access without open ports |
| **🖥️ Infrastructure** | Proxmox VE, LXC Containers, Ubuntu 22.04 | Virtualization and container hosting |
| **🐳 Orchestration** | Docker, Docker Compose, Bridge Networks | Container management and networking |
| **⚡ Cache & Queue** | Redis 7.x, In-Memory Store | Session storage, caching, pub/sub |
| **🗄️ Database** | Supabase (PostgreSQL), Row Level Security | Primary data storage with auth |
| **🎯 API Gateway** | FastAPI, Uvicorn, Python 3.9 | HTTP routing and load balancing |
| **🤖 AI Services** | OpenAI GPT-4, ElevenLabs TTS, DALL-E | Content generation and synthesis |
| **📊 Monitoring** | FastAPI Health Checks, Docker Stats | Service health and performance |

---

## 🏗️ **Complete System Architecture**

```mermaid
graph TB
    subgraph "🌍 Internet Layer"
        U[Global Users]
        A[API Clients]
    end
    
    subgraph "🌐 Cloudflare Edge Network"
        CDN[Cloudflare CDN<br/>190+ Edge Locations]
        WAF[Web Application Firewall]
        SSL[SSL/TLS Termination]
        DDOS[DDoS Protection]
    end
    
    subgraph "🔒 Secure Tunnel Layer"
        TUNNEL[Cloudflare Tunnel<br/>Zero-Trust Access]
        AUTH[Certificate Authentication]
    end
    
    subgraph "🖥️ Proxmox Infrastructure - PVE-3"
        HOST[Proxmox Host<br/>192.168.1.103]
        
        subgraph "📦 LXC Container 200"
            CONTAINER[Ubuntu 22.04 LTS<br/>4 CPU, 8GB RAM, 50GB]
            
            subgraph "🐳 Docker Network: radiox-network"
                GATEWAY[API Gateway<br/>:8000]
                SHOW[Show Service<br/>:8001]
                CONTENT[Content Service<br/>:8002]
                AUDIO[Audio Service<br/>:8003]
                MEDIA[Media Service<br/>:8004]
                SPEAKER[Speaker Service<br/>:8005]
                DATA[Data Service<br/>:8006]
                ANALYTICS[Analytics Service<br/>:8007]
                REDIS[Redis Cache<br/>:6379]
            end
        end
    end
    
    subgraph "🌐 External Services"
        SUPABASE[(Supabase<br/>PostgreSQL + Auth)]
        OPENAI[OpenAI API<br/>GPT-4 + DALL-E]
        ELEVENLABS[ElevenLabs<br/>Text-to-Speech]
    end
    
    U --> CDN
    CDN --> WAF
    WAF --> SSL
    SSL --> DDOS
    DDOS --> TUNNEL
    TUNNEL --> AUTH
    AUTH --> GATEWAY
    
    GATEWAY --> SHOW
    GATEWAY --> CONTENT
    GATEWAY --> AUDIO
    GATEWAY --> MEDIA
    GATEWAY --> SPEAKER
    GATEWAY --> DATA
    GATEWAY --> ANALYTICS
    
    SHOW --> REDIS
    CONTENT --> REDIS
    AUDIO --> REDIS
    
    DATA --> SUPABASE
    CONTENT --> OPENAI
    AUDIO --> ELEVENLABS
```

---

## 🔧 **Infrastructure Layer Details**

### **🖥️ Proxmox Virtual Environment**
- **Host OS**: Proxmox VE 8.x
- **Container Engine**: LXC (Linux Containers)
- **Base Image**: Ubuntu 22.04.3 LTS
- **Resources**: 4 vCPU, 8GB RAM, 50GB Storage
- **Network**: Bridge (vmbr0) with DHCP

### **🐳 Container Orchestration Stack**
- **Docker Engine**: 24.0.7
- **Docker Compose**: 2.21.0
- **Network**: Bridge driver (radiox-network)
- **Restart Policy**: unless-stopped
- **Security**: Unprivileged containers

---

## 🎯 **Application Layer Architecture**

### **📡 API Gateway - Central Router**
```yaml
Technology Stack:
  Framework: FastAPI 0.104.1
  Server: Uvicorn (ASGI)
  Port: 8000
  Purpose: HTTP routing and load balancing
  
Routing Rules:
  /shows/* → show-service:8001
  /content/* → content-service:8002
  /audio/* → audio-service:8003
  /media/* → media-service:8004
  /speakers/* → speaker-service:8005
  /data/* → data-service:8006
  /analytics/* → analytics-service:8007
```

### **🎵 Microservices Detailed Breakdown**

| Service | Port | Stack | Dependencies | Function |
|---------|------|-------|--------------|----------|
| **Show Service** | 8001 | FastAPI + asyncio | Redis, Data Service | Orchestrates radio show generation |
| **Content Service** | 8002 | FastAPI + OpenAI SDK | Redis, OpenAI, RSS | News collection + GPT-4 scripts |
| **Audio Service** | 8003 | FastAPI + ElevenLabs + FFmpeg | Redis, ElevenLabs, Supabase | TTS + audio mixing |
| **Media Service** | 8004 | FastAPI + Supabase Storage | Redis, Supabase, DALL-E | File management + cover art |
| **Speaker Service** | 8005 | FastAPI + JSON Config | Redis, Supabase | Voice configuration |
| **Data Service** | 8006 | FastAPI + Supabase SDK | Redis, Supabase | Database operations |
| **Analytics Service** | 8007 | FastAPI + metrics | Redis, Supabase | Performance monitoring |

---

## 🔗 **Network Architecture & Port Mapping**

### **🔌 Complete Port Configuration**

| Port | Service | Access | Protocol | Purpose |
|------|---------|--------|----------|---------|
| **443** | Cloudflare | 🌍 Global | HTTPS/HTTP2 | External access |
| **8000** | API Gateway | 🔒 Tunnel Only | HTTP/1.1 | Internal routing |
| **8001-8007** | Microservices | 🐳 Docker Only | HTTP/1.1 | Service APIs |
| **6379** | Redis | 🐳 Docker Only | Redis Protocol | Cache & sessions |

### **🌐 External Access Flow**
```
Client → Cloudflare CDN → Cloudflare Tunnel → API Gateway → Microservices
(HTTPS)     (Global)        (Secure)         (HTTP)       (Internal)
```

---

## 🔒 **Security Architecture**

### **🛡️ Zero-Trust Security Model**
- **Edge Protection**: Cloudflare WAF + DDoS (67 Tbps capacity)
- **Access Control**: Cloudflare Tunnel (Certificate-based auth)
- **Container Isolation**: Unprivileged LXC containers
- **Network Segmentation**: Docker bridge networks
- **API Security**: FastAPI request validation
- **Database Security**: Supabase Row Level Security

### **🔑 Security Features**
- ✅ Zero open ports (all traffic via tunnel)
- ✅ Automatic HTTPS with SSL termination
- ✅ Enterprise-grade DDoS protection
- ✅ Container isolation and sandboxing
- ✅ Internal network segmentation

---

## 📊 **Data Flow Architecture**

### **🎵 Radio Show Generation Flow**
```mermaid
sequenceDiagram
    participant Client
    participant Gateway
    participant Show
    participant Content
    participant Audio
    participant Data
    participant OpenAI
    participant ElevenLabs
    participant Supabase
    
    Client->>Gateway: POST /shows/generate
    Gateway->>Show: Orchestrate show
    
    Show->>Content: Collect news
    Content->>OpenAI: Generate script
    OpenAI-->>Content: GPT-4 script
    Content-->>Show: Formatted content
    
    Show->>Audio: Generate TTS
    Audio->>ElevenLabs: Text-to-speech
    ElevenLabs-->>Audio: Audio files
    Audio->>Audio: Mix with jingles
    Audio-->>Show: Final audio
    
    Show->>Data: Save show data
    Data->>Supabase: Store metadata
    Supabase-->>Data: Confirmation
    Data-->>Show: Success
    
    Show-->>Gateway: Show complete
    Gateway-->>Client: JSON response
```

---

## ⚡ **Performance & Scalability**

### **📈 Performance Metrics**
| Component | Current | Target | Strategy |
|-----------|---------|--------|----------|
| **CDN Response** | ~50ms | <100ms | Global edge caching |
| **API Gateway** | ~10ms | <50ms | Async FastAPI |
| **GPT-4 Calls** | ~3-5s | <10s | Caching + parallelization |
| **TTS Generation** | ~2-4s | <5s | Streaming + chunking |
| **Full Show** | ~15-30s | <60s | Pipeline optimization |

---

## 🛠️ **Development & Deployment Tools**

### **🔧 Technology Matrix**
- **Orchestration**: Docker Compose 2.21.0
- **Gateway**: FastAPI 0.104.1
- **Server**: Uvicorn 0.24.0
- **Database**: Supabase (PostgreSQL)
- **Cache**: Redis 7.2.3
- **Tunnel**: Cloudflared 2025.6.1
- **Build**: Docker 24.0.7
- **Process**: Make 4.3

### **📁 Project Structure**
```
radiox-backend/
├── docker-compose.production.yml    # Production orchestration
├── tunnel-config.yml               # Cloudflare tunnel config
├── Makefile                        # Build & deployment
├── services/                       # 8 Microservices
├── docs/                          # Documentation
├── config/                        # Configuration
└── scripts/                       # Deployment scripts
```

## 📊 **Monitoring & Health Checks**

### **🔍 Health Check Endpoints**
- `/health` - Service health status
- `/services/status` - All microservices status  
- `/docs` - API documentation
- `/metrics` - Performance metrics

### **📈 Live Production Status**
- **API**: https://api.radiox.cloud
- **Health**: https://api.radiox.cloud/health
- **Status**: https://api.radiox.cloud/services/status
- **Docs**: https://api.radiox.cloud/docs

---

**This comprehensive tech stack powers a production-ready AI radio system with global reach, enterprise security, and scalable microservices architecture.** 