# RadioX Microservices Architecture

## 🚀 Übersicht

RadioX wurde von einer Monolith-Architektur zu einer modernen Microservices-Architektur transformiert. Das System besteht aus 8 spezialisierten Services, die über ein API Gateway kommunizieren.

## 🏗️ Architektur

```
┌─────────────────┐
│   API Gateway   │ ← Zentraler Eingangspoint (Port 8000)
│   (Port 8000)   │
└─────────┬───────┘
          │
    ┌─────┴─────────────────────────────────────────┐
    │                                               │
┌───▼───┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐
│ Show  │ │Content  │ │ Audio   │ │ Media   │ │Speaker  │
│Service│ │Service  │ │Service  │ │Service  │ │Service  │
│ 8001  │ │  8002   │ │  8003   │ │  8004   │ │  8005   │
└───────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘
    │         │           │           │           │
    └─────────┼───────────┼───────────┼───────────┘
              │           │           │
        ┌─────▼─────┐ ┌───▼───┐ ┌─────▼─────┐
        │   Data    │ │ Redis │ │Analytics  │
        │ Service   │ │ Cache │ │ Service   │
        │   8006    │ │ 6379  │ │   8007    │
        └───────────┘ └───────┘ └───────────┘
```

## 📋 Services

### 🌐 API Gateway (Port 8000)
- **Zweck**: Zentraler Eingangspoint für alle Requests
- **Features**: 
  - Service Discovery & Load Balancing
  - Request Routing
  - Health Monitoring
  - CORS Handling
- **Endpoints**: `/health`, `/services/status`, `/api/v1/*`

### 🎵 Show Service (Port 8001)
- **Zweck**: Orchestriert Show-Generierung
- **Features**:
  - Show-Generierung koordinieren
  - Service-übergreifende Workflows
  - Show-Status Management
  - Dashboard Integration
- **Endpoints**: `/generate`, `/shows/{id}`, `/shows`, `/dashboard/{id}`

### 📝 Content Service (Port 8002)
- **Zweck**: Content-Generierung und GPT-Integration
- **Features**:
  - News-Content sammeln
  - Bitcoin-Analyse
  - GPT-Script-Generierung
  - Prompt-Management
- **Endpoints**: `/content`, `/script`, `/news`, `/bitcoin`

### 🎤 Audio Service (Port 8003)
- **Zweck**: Audio-Generierung mit ElevenLabs
- **Features**:
  - Text-to-Speech
  - Voice Management
  - Audio-Verarbeitung
  - Jingle-Integration
- **Endpoints**: `/generate`, `/voices`

### 📁 Media Service (Port 8004)
- **Zweck**: Medien-Verarbeitung und -Verwaltung
- **Features**:
  - File-Management
  - Web-Deployment
  - Dashboard-Generierung
  - Outplay-Integration
- **Endpoints**: `/process`, `/files`, `/dashboard/{id}`

### 👥 Speaker Service (Port 8005)
- **Zweck**: Speaker-Konfiguration und -Management
- **Features**:
  - Speaker-Registry
  - Voice-ID-Verwaltung
  - Sprach-Konfiguration
- **Endpoints**: `/speakers`, `/speakers/{id}`

### 🗄️ Data Service (Port 8006)
- **Zweck**: Datenbank-Zugriff und Konfiguration
- **Features**:
  - Supabase-Integration
  - Configuration Management
  - Caching-Layer
  - Preset-Verwaltung
- **Endpoints**: `/config`, `/presets`, `/speakers`, `/elevenlabs/models`

### 📊 Analytics Service (Port 8007)
- **Zweck**: Metriken und Performance-Tracking
- **Features**:
  - Show-Statistiken
  - Performance-Metriken
  - Usage-Analytics
- **Endpoints**: `/shows`, `/performance`

## 🛠️ Setup & Deployment

### Voraussetzungen
- Docker & Docker Compose
- Make (optional, für einfachere Commands)

### 1. Environment Setup
```bash
# .env Datei erstellen
make dev-setup

# API Keys in .env eintragen:
# SUPABASE_URL=your_supabase_url
# SUPABASE_KEY=your_supabase_key
# OPENAI_API_KEY=your_openai_key
# ELEVENLABS_API_KEY=your_elevenlabs_key
```

### 2. Services starten
```bash
# Alle Services bauen und starten
make dev

# Oder manuell:
docker-compose build
docker-compose up -d
```

### 3. Health Check
```bash
# Service-Status prüfen
make health
make status

# Oder direkt:
curl http://localhost:8000/services/status
```

## 🔧 Development

### Lokale Entwicklung
```bash
# Services mit Logs starten
make up-logs

# Einzelne Services rebuilden
make build-api
make build-show
make build-content

# Logs anzeigen
make logs-api
make logs-show
```

### Testing
```bash
# Show-Generierung testen
make test-show

# Health Checks
make health

# Service-Monitoring
make monitor
```

## 📡 API Endpoints

### Show-Generierung
```bash
# Neue Show generieren
POST /api/v1/shows/generate
{
  "preset_name": "zurich",
  "primary_speaker": "marcel",
  "secondary_speaker": null,
  "news_count": 2
}

# Show-Details abrufen
GET /api/v1/shows/{show_id}

# Shows auflisten
GET /api/v1/shows?limit=10&offset=0
```

### Content-Abfrage
```bash
# News abrufen
GET /api/v1/content/news?limit=5

# Bitcoin-Daten
GET /api/v1/content/bitcoin

# Konfiguration
GET /api/v1/data/config
```

## 🔄 Migration vom Monolith

### Phase 1: ✅ Grundstruktur
- [x] Docker Compose Setup
- [x] API Gateway
- [x] Core Services (Show, Content, Data)
- [x] Redis Integration
- [x] Health Monitoring

### Phase 2: 🚧 Service-Extraktion
- [ ] Monolith-Code in Services aufteilen
- [ ] Supabase-Integration migrieren
- [ ] Audio-Service implementieren
- [ ] Media-Service implementieren

### Phase 3: 📈 Erweiterungen
- [ ] Analytics-Service
- [ ] Speaker-Service
- [ ] Kubernetes-Deployment
- [ ] CI/CD Pipeline

## 🚀 Vorteile der Microservices-Architektur

### ✅ Skalierbarkeit
- Einzelne Services können unabhängig skaliert werden
- Horizontale Skalierung möglich
- Resource-optimierte Deployments

### ✅ Wartbarkeit
- Klare Trennung der Verantwortlichkeiten
- Unabhängige Development-Teams möglich
- Einfachere Testing-Strategien

### ✅ Technologie-Flexibilität
- Verschiedene Technologien pro Service
- Unabhängige Updates möglich
- Experimentelle Features isoliert

### ✅ Ausfallsicherheit
- Fehler in einem Service betreffen nicht das gesamte System
- Circuit Breaker Pattern
- Graceful Degradation

## 🔧 Troubleshooting

### Service startet nicht
```bash
# Logs prüfen
make logs-{service-name}

# Container-Status
docker-compose ps

# Service neu starten
docker-compose restart {service-name}
```

### Performance-Probleme
```bash
# Redis-Status prüfen
make logs-redis

# Service-Metriken
curl http://localhost:8000/services/status

# Resource-Usage
docker stats
```

### Netzwerk-Probleme
```bash
# Netzwerk-Konfiguration
docker network ls
docker network inspect radiox-network

# Service-Connectivity
docker-compose exec api-gateway ping show-service
```

## 📚 Weitere Ressourcen

- [Docker Compose Dokumentation](https://docs.docker.com/compose/)
- [FastAPI Dokumentation](https://fastapi.tiangolo.com/)
- [Redis Dokumentation](https://redis.io/docs/)
- [Microservices Best Practices](https://microservices.io/)

## 🤝 Contributing

1. Feature-Branch erstellen
2. Services lokal testen
3. Health Checks durchführen
4. Pull Request erstellen

```bash
# Development-Workflow
git checkout -b feature/new-service
make dev
make health
make test-show
```

## 📞 Support

Bei Problemen oder Fragen:
- Logs prüfen: `make logs`
- Health Status: `make health`
- Service Status: `make status`
- GitHub Issues erstellen 