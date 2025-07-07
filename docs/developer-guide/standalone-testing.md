# 🧪 Standalone Service Testing Guide

## 🎯 Einzelne Services ausführen

Die RadioX Services sind **teilweise einzeln ausführbar** - ideal für debugging und Development!

### ✅ **VOLLSTÄNDIG STANDALONE SERVICES:**

| Service | Port | Status | Dependencies |
|---------|------|--------|--------------|
| **Key Service** | 8001 | ✅ Fully Standalone | Nur Supabase |
| **Content Service** | 8003 | ✅ Standalone | OpenAI API, RSS feeds |
| **Audio Service** | 8004 | ✅ Standalone | ElevenLabs API, FFmpeg |

### ⚠️ **PARTIALLY STANDALONE:**

| Service | Port | Status | Issues |
|---------|------|--------|--------|
| **Data Service** | 8002 | ⚠️ Needs PYTHONPATH | Shared modules required |
| **Show Service** | 8007 | ❌ Complex Dependencies | Needs all other services |

### 🚀 **Quick Start - Einzelne Services testen:**

#### 1. **Infrastructure starten:**
```bash
# Nur Redis starten (minimal infrastructure)
docker-compose up redis -d
```

#### 2. **Services einzeln starten:**
```bash
# Key Service (Infrastructure)
./scripts/run-service-standalone.sh key-service

# Content Service (Processing)  
./scripts/run-service-standalone.sh content-service

# Audio Service (Processing)
./scripts/run-service-standalone.sh audio-service
```

#### 3. **Health Checks:**
```bash
curl http://localhost:8001/health  # Key Service
curl http://localhost:8003/health  # Content Service  
curl http://localhost:8004/health  # Audio Service
```

### 🔧 **Manual Setup für komplexere Services:**

#### **Data Service (8002):**
```bash
# Setup PYTHONPATH für shared modules
export PYTHONPATH="$PWD:$PWD/src:$PYTHONPATH"

# Service starten
cd services/data-service
python main.py
```

#### **Show Service (8007):**
```bash
# Braucht ALLE anderen Services!
# 1. Infrastructure
docker-compose up redis -d

# 2. Key + Data Services
./scripts/run-service-standalone.sh key-service &
./scripts/run-service-standalone.sh data-service &

# 3. Processing Services  
./scripts/run-service-standalone.sh content-service &
./scripts/run-service-standalone.sh audio-service &

# 4. Show Service
./scripts/run-service-standalone.sh show-service
```

### 🔑 **Environment Variables:**

Erstelle `.env` mit:
```bash
# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-key

# AI APIs
OPENAI_API_KEY=your-openai-key
ELEVENLABS_API_KEY=your-elevenlabs-key

# Infrastructure  
REDIS_URL=redis://localhost:6379

# Service URLs
KEY_SERVICE_URL=http://localhost:8001
DATA_SERVICE_URL=http://localhost:8002
# ... etc
```

### 🧪 **Automatisierte Tests:**

```bash
# Test alle Services auf Import-Fähigkeit
./scripts/test-services-standalone.sh
```

### 📊 **Service Dependency Matrix:**

```
Key Service (8001)     → Keine Dependencies (Supabase only)
Data Service (8002)    → Key Service  
Content Service (8003) → Data Service, External APIs
Audio Service (8004)   → Data Service, ElevenLabs
Show Service (8007)    → ALLE anderen Services
```

### 🔧 **Debugging Workflow:**

1. **Start minimal**: Key Service + Redis
2. **Add layer**: Data Service  
3. **Add processing**: Content/Audio Services
4. **Add orchestration**: Show Service
5. **Test integration**: API Gateway

### ⚡ **Development Benefits:**

- ✅ **Schneller Iteration**: Nur relevanten Service neu starten
- ✅ **Isoliertes Testing**: Service-spezifische Probleme eingrenzen  
- ✅ **Resource Efficiency**: Nicht alle 8 Services für einen Test
- ✅ **Parallel Development**: Team kann an verschiedenen Services arbeiten

### 🚨 **Known Issues:**

- **Shared Modules**: Data/Show Service brauchen PYTHONPATH setup
- **Version Inconsistencies**: Requirements jetzt standardisiert auf 0.115.13
- **FFmpeg**: Audio Service braucht system-level FFmpeg installation

### 📝 **Next Steps:**

- [ ] Shared modules in separate packages extrahieren
- [ ] Docker-basierte standalone execution  
- [ ] Service-spezifische mock dependencies
- [ ] Integration test automation 