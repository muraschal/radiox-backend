# 8 Microservices Documentation

<div align="center">

![Microservices](https://img.shields.io/badge/microservices-8-blue)
![Docker](https://img.shields.io/badge/docker-compose-2496ED)
![FastAPI](https://img.shields.io/badge/FastAPI-009688)

**Complete guide to RadioX 8-service architecture**

[🏠 Documentation](../) • [🏗️ Architecture](architecture.md) • [🛠️ Development](development.md) • [🚀 Deployment](../deployment/)

</div>

---

## Service Overview

RadioX operates **8 specialized microservices** orchestrated via Docker Compose, each handling specific business domains with clean API boundaries.

### Service Registry

| Port | Service | Responsibility | Technology Stack |
|------|---------|---------------|-----------------|
| **8000** | **API Gateway** | Central routing, service discovery | FastAPI + Redis |
| **8001** | **Key Service** | Central API key management | FastAPI + Supabase |
| **8002** | **Data Service** | Database operations | FastAPI + PostgreSQL |
| **8003** | **Content Service** | News collection, GPT processing | FastAPI + OpenAI |
| **8004** | **Audio Service** | TTS, audio mixing, jingles | FastAPI + ElevenLabs |
| **8005** | **Media Service** | File management, cover art | FastAPI + DALL-E |
| **8006** | **Speaker Service** | Voice configuration | FastAPI + Supabase |
| **8007** | **Show Service** | Show generation orchestration | FastAPI + Celery |
| **8008** | **Analytics Service** | Metrics, monitoring | FastAPI + Prometheus |

---

## 🌐 API Gateway (Port 8000)

### Purpose
**Central entry point** providing service discovery, request routing, and cross-cutting concerns.

### Container Configuration
```dockerfile
# services/api-gateway/Dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY main.py .
EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Key Responsibilities
- **Service Discovery** - Dynamic service registry and health monitoring
- **Request Routing** - Intelligent routing to appropriate microservices
- **Authentication** - JWT token validation and user session management
- **Rate Limiting** - Per-client request throttling and abuse prevention
- **CORS Handling** - Cross-origin request policy enforcement
- **API Documentation** - OpenAPI spec generation and Swagger UI

### API Endpoints
```python
# Core Gateway Endpoints
GET  /health                    # Gateway health check
GET  /services/status           # All services health
GET  /services/discovery        # Service registry
POST /api/v1/auth/login        # Authentication
POST /api/v1/*                 # Route to services

# Service Proxying
POST /api/v1/shows/generate    # → Show Service (8007)
GET  /api/v1/content/news      # → Content Service (8003)
POST /api/v1/audio/generate    # → Audio Service (8004)
```

### Dependencies
```yaml
External:
  - Redis (session storage)
  - Service discovery mechanism

Internal:
  - All 7 business services (8001-8007)
```

---

## 🎭 Show Service (Port 8007)

### Purpose
**Orchestration hub** for complete radio show generation workflows.

### Container Configuration
```dockerfile
# services/show-service/Dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY main.py .
EXPOSE 8007

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8007"]
```

### Key Responsibilities
- **Workflow Orchestration** - Coordinate multi-service show generation
- **State Management** - Track show generation progress and status
- **Business Logic** - Show configuration and preset management
- **Error Handling** - Graceful failure recovery and rollback
- **Dashboard Generation** - HTML dashboard with show metadata

### API Endpoints
```python
# Show Management
POST /generate                 # Generate complete radio show
GET  /shows/{show_id}         # Retrieve show details
GET  /shows                   # List all shows
DELETE /shows/{show_id}       # Delete show

# Dashboard & UI
GET  /dashboard/{show_id}     # Show dashboard HTML
GET  /status/{show_id}        # Generation status

# Configuration
GET  /presets                 # Available show presets
POST /presets                 # Create show preset
```

### Workflow Example
```python
async def generate_complete_show(preset_name: str, news_count: int) -> ShowResponse:
    """Complete show generation orchestration"""
    
    # 1. Get configuration from Data Service
    config = await data_client.get_preset(preset_name)
    
    # 2. Collect content from Content Service
    content = await content_client.get_recent_news(news_count)
    
    # 3. Generate script via Content Service
    script = await content_client.generate_script(content, config)
    
    # 4. Parallel media generation
    audio_task = audio_client.generate_audio(script, config.voices)
    cover_task = media_client.generate_cover(script.summary)
    
    audio, cover = await asyncio.gather(audio_task, cover_task)
    
    # 5. Persist show data
    show = await data_client.create_show(script, audio, cover)
    
    return ShowResponse(
        show_id=show.id,
        status="completed",
        audio_url=audio.url,
        cover_url=cover.url,
        dashboard_url=f"/dashboard/{show.id}"
    )
```

### Dependencies
```yaml
Internal Services:
  - Content Service (8003) - News and script generation
  - Audio Service (8004) - Audio production
  - Media Service (8005) - Cover art generation
  - Data Service (8002) - Configuration and persistence
```

---

## 📰 Content Service (Port 8003)

### Purpose
**Content aggregation and AI processing** for news collection and script generation.

### Key Responsibilities
- **RSS Feed Aggregation** - 25+ Swiss and international news sources
- **Content Filtering** - Deduplication and quality filtering
- **GPT-4 Integration** - Professional radio script generation
- **News Categorization** - Automatic content classification
- **Caching Layer** - Redis-based content caching for performance

### API Endpoints
```python
# Content Collection
GET  /content/news             # Recent news articles
GET  /content/feeds            # RSS feed status
POST /content/refresh          # Force content refresh

# Script Generation
POST /content/script           # Generate radio script
POST /content/process          # Process raw content

# Configuration
GET  /sources                  # Available news sources
POST /sources                  # Add news source
```

### RSS Sources Integration
```python
ACTIVE_RSS_SOURCES = {
    "nzz": {
        "feeds": ["zurich", "schweiz", "wirtschaft", "international"],
        "priority": 10,
        "weight": 3.0,
        "language": "de"
    },
    "srf": {
        "feeds": ["news", "schweiz", "international", "wirtschaft"],
        "priority": 9,
        "weight": 2.0,
        "language": "de"
    },
    "20min": {
        "feeds": ["weather", "zurich", "crypto", "tech"],
        "priority": 10,
        "weight": 0.8,
        "language": "de"
    }
    # ... 22 more sources
}
```

### GPT-4 Script Generation
```python
async def generate_radio_script(content: List[NewsItem], config: ShowConfig) -> RadioScript:
    """Generate professional radio script using GPT-4"""
    
    prompt = f"""
    Create a professional Swiss radio show script for {config.preset_name}.
    
    Style: {config.show_behavior}
    Duration: {config.duration_minutes} minutes
    Speakers: {config.primary_speaker}, {config.secondary_speaker}
    
    News Content:
    {format_news_for_prompt(content)}
    
    Requirements:
    - Natural dialogue between speakers
    - Swiss German cultural references
    - Professional radio broadcasting style
    - Include weather and crypto updates
    """
    
    response = await openai_client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=2000
    )
    
    return RadioScript(
        content=response.choices[0].message.content,
        metadata={
            "model": "gpt-4",
            "tokens_used": response.usage.total_tokens,
            "generation_time": datetime.now(),
            "news_sources": [item.source for item in content]
        }
    )
```

### Dependencies
```yaml
External APIs:
  - OpenAI GPT-4 API
  - 25+ RSS feed endpoints

Internal Services:
  - Data Service (8002) - RSS configuration
  - Redis - Content caching
```

---

## 🎤 Audio Service (Port 8004)

### Purpose
**Professional audio production** with ElevenLabs TTS and advanced mixing.

### Key Responsibilities
- **Text-to-Speech** - ElevenLabs V3 API integration
- **Voice Management** - Multiple speaker voice profiles
- **Audio Mixing** - Professional 3-phase jingle system
- **FFmpeg Processing** - Audio mastering and format conversion
- **MP3 Generation** - Final audio file assembly with metadata

### API Endpoints
```python
# Audio Generation
POST /generate                 # Generate audio from script
GET  /voices                   # Available voice models
POST /process                  # Audio post-processing

# Queue Management
GET  /status                   # Generation queue status
GET  /jobs/{job_id}           # Job status and progress
```

### 3-Phase Audio System
```python
class AudioMixer:
    """Professional 3-phase jingle integration system"""
    
    async def create_professional_audio(self, segments: List[AudioSegment], jingle_path: str) -> AudioFile:
        """
        PHASE 1 - INTRO (0-12s):
        - 0-3s: 100% pure jingle (powerful intro)
        - 3-13s: Ultra-smooth fade 100% → 10%
        
        PHASE 2 - BACKGROUND (12s-End-7s):
        - Speech: 100% volume (dominant)
        - Jingle: 10% volume (subtle backing)
        
        PHASE 3 - OUTRO (Last 7s):
        - Ultra-smooth ramp-up 10% → 100%
        """
        
        # Load jingle and speech audio
        jingle = AudioSegment.from_file(jingle_path)
        speech_audio = await self.combine_speech_segments(segments)
        
        # Phase 1: Pure jingle intro (3s) + fade to 10% (10s)
        intro_jingle = jingle[:3000]  # First 3 seconds at 100%
        fade_jingle = jingle[3000:13000].apply_gain(-20)  # Fade to 10%
        
        # Phase 2: 10% backing jingle + 100% speech
        backing_duration = len(speech_audio) - 7000  # All except last 7s
        backing_jingle = jingle[:backing_duration].apply_gain(-20)  # 10% volume
        
        # Phase 3: Ramp up to 100% outro
        outro_jingle = jingle[-7000:].fade_in(7000)  # 7s fade-in to 100%
        
        # Combine all phases
        final_audio = intro_jingle + fade_jingle + backing_jingle.overlay(speech_audio[:-7000]) + outro_jingle
        
        return AudioFile(
            content=final_audio.export(format="mp3", bitrate="192k"),
            duration_seconds=len(final_audio) / 1000,
            metadata=self.generate_metadata()
        )
```

### ElevenLabs Integration
```python
async def generate_speech_segment(self, text: str, voice_id: str, settings: VoiceSettings) -> bytes:
    """Generate speech using ElevenLabs V3 TTS"""
    
    url = "https://api.elevenlabs.io/v1/text-to-speech"
    headers = {"Authorization": f"Bearer {self.api_key}"}
    
    payload = {
        "text": text,
        "voice_id": voice_id,
        "model": "eleven_turbo_v2",
        "voice_settings": {
            "stability": settings.stability,
            "similarity_boost": settings.similarity_boost,
            "style": settings.style,
            "use_speaker_boost": settings.use_speaker_boost
        }
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.content
```

### Dependencies
```yaml
External APIs:
  - ElevenLabs V3 TTS API

Internal Services:
  - Speaker Service (8006) - Voice configurations
  - Media Service (8005) - File storage

System Dependencies:
  - FFmpeg for audio processing
  - Pydub for audio manipulation
```

---

## 📁 Media Service (Port 8005)

### Purpose
**File management and visual content generation** for cover art and media storage.

### Key Responsibilities
- **File Storage** - Supabase Storage integration
- **Cover Art Generation** - DALL-E 3 AI-generated images
- **Archive Management** - Automatic file archiving and cleanup
- **Static File Serving** - HTTP file delivery with streaming
- **Metadata Management** - File indexing and search

### API Endpoints
```python
# File Management
POST /upload                   # File upload handler
GET  /files/{file_id}         # File retrieval
DELETE /files/{file_id}       # File deletion

# Cover Art Generation
POST /generate/cover          # Generate cover art
GET  /covers/{show_id}        # Retrieve cover image

# Archive Management
GET  /archive                 # List archived files
POST /archive/{file_id}       # Archive specific file
```

### DALL-E Cover Generation
```python
async def generate_cover_art(self, script_summary: str, style: str = "professional") -> CoverImage:
    """Generate AI cover art using DALL-E 3"""
    
    prompt = f"""
    Create a professional radio show cover image.
    
    Content: {script_summary}
    Style: Modern, clean, broadcast-quality
    Colors: Professional blue and white theme
    Elements: Radio waves, Swiss elements, modern typography
    Format: Square aspect ratio, high resolution
    
    The image should convey trust, professionalism, and Swiss radio broadcasting.
    No text or words in the image - pure visual design.
    """
    
    response = await openai_client.images.generate(
        model="dall-e-3",
        prompt=prompt,
        size="1024x1024",
        quality="standard",
        n=1
    )
    
    # Download and store image
    image_url = response.data[0].url
    image_data = await self.download_image(image_url)
    
    # Store in Supabase Storage
    file_path = f"covers/radiox_{datetime.now().strftime('%y%m%d_%H%M')}.png"
    storage_url = await self.supabase_storage.upload(file_path, image_data)
    
    return CoverImage(
        url=storage_url,
        path=file_path,
        size_bytes=len(image_data),
        generated_at=datetime.now(),
        prompt_used=prompt
    )
```

### Dependencies
```yaml
External APIs:
  - OpenAI DALL-E 3 API
  - Supabase Storage

Internal Services:
  - Data Service (8002) - File metadata storage
```

---

## 🗣️ Speaker Service (Port 8006)

### Purpose
**Voice configuration and speaker profile management** for consistent audio quality.

### Key Responsibilities
- **Voice Profile Management** - ElevenLabs voice configurations
- **Speaker Registry** - Available speakers and their characteristics
- **Voice Quality Optimization** - TTS parameter tuning
- **Multi-language Support** - German and English voice models

### API Endpoints
```python
# Speaker Management
GET  /speakers                 # List available speakers
POST /speakers                 # Create speaker profile
PUT  /speakers/{id}           # Update speaker configuration
DELETE /speakers/{id}         # Remove speaker

# Voice Configuration
GET  /voices/{speaker_id}     # Get voice settings
POST /voices/test             # Test voice generation
```

### Speaker Profiles
```python
SPEAKER_PROFILES = {
    "marcel": {
        "voice_id": "21m00Tcm4TlvDq8ikWAM",
        "name": "Marcel",
        "description": "Host, main presenter, energetic",
        "language": "de",
        "settings": {
            "stability": 0.75,
            "similarity_boost": 0.85,
            "style": 0.65,
            "use_speaker_boost": True
        },
        "use_cases": ["hosting", "main_presenter", "conversation"]
    },
    "jarvis": {
        "voice_id": "EXAVITQu4vr4xnSDxMaL",
        "name": "Jarvis",
        "description": "AI assistant, technical content, precise",
        "language": "en",
        "settings": {
            "stability": 0.80,
            "similarity_boost": 0.90,
            "style": 0.60,
            "use_speaker_boost": True
        },
        "use_cases": ["ai_assistant", "technical_content", "precise_delivery"]
    },
    "lucy": {
        "voice_id": "pNInz6obpgDQGcFmaJgB",
        "name": "Lucy",
        "description": "Weather reports, sultry delivery",
        "language": "en",
        "settings": {
            "stability": 0.70,
            "similarity_boost": 0.80,
            "style": 0.75,
            "use_speaker_boost": False
        },
        "use_cases": ["weather_reports", "atmospheric_content"]
    }
}
```

### Dependencies
```yaml
External APIs:
  - ElevenLabs API (voice validation)

Internal Services:
  - Data Service (8002) - Profile persistence
```

---

## 🔑 Key Service (Port 8001)

### Purpose
**Central API key management and distribution** for all microservices.

### Container Configuration
```dockerfile
# services/key-service/Dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY main.py .
EXPOSE 8001

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
```

### Key Responsibilities
- **Centralized Key Storage** - All API keys stored in Supabase `keys` table
- **Automatic Distribution** - Services fetch keys on startup and refresh
- **Environment Integration** - Keys automatically set as environment variables
- **Security Management** - Masked key responses, secure key retrieval
- **Cache Management** - 5-minute refresh intervals for optimal performance

### API Endpoints
```python
# Key Management
GET  /keys                     # List available keys (masked)
GET  /keys/{key_name}         # Get specific API key value
POST /refresh                 # Manually refresh keys from database
GET  /env/{env_var}           # Get environment variable value

# Health & Status
GET  /health                  # Service health check
```

### Service Integration
```python
# Usage in other services
from config.key_client import get_api_key

# Get OpenAI API Key
openai_key = await get_api_key("openai_api_key")

# Get ElevenLabs API Key  
elevenlabs_key = await get_api_key("elevenlabs_api_key")

# Automatic environment variable setting
# Keys are automatically available as: OPENAI_API_KEY, ELEVENLABS_API_KEY, etc.
```

### Database Schema
```sql
-- Supabase keys table
CREATE TABLE keys (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,  -- e.g., "openai_api_key"
    value TEXT NOT NULL,                -- The actual API key
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### Important Configuration
**🔐 Supabase RLS Setup Required**
- Supabase Row Level Security must be properly configured
- Anonymous access policy needed for key retrieval
- **⚠️ Common Issue**: Service returns "No API keys found" despite HTTP 200
- **✅ Solution**: See [Supabase RLS Configuration](supabase-rls-configuration.md) for complete setup

### Dependencies
```yaml
External:
  - Supabase (key storage)

Internal:
  - None (infrastructure service)
```

---

## 💾 Data Service (Port 8002)

### Purpose
**Database operations and configuration management** for all microservices.

### Container Configuration
```dockerfile
# services/data-service/Dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY main.py .
EXPOSE 8002

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002"]
```

### Key Responsibilities
- **Database Operations** - CRUD operations for all services
- **Configuration Management** - System configuration and defaults
- **Service Configuration** - Service URL registry and settings
- **Validation Layer** - Data validation and schema enforcement
- **Cache Coordination** - Redis cache strategies

### API Endpoints
```python
# Configuration
GET  /config                  # System configuration
GET  /config/services         # Service URL registry
GET  /config/defaults         # Default values
GET  /config/{category}/{key} # Specific config value

# Database Operations
GET  /shows                   # List shows
GET  /shows/{id}             # Get specific show
POST /shows                  # Create show
PUT  /shows/{id}             # Update show
DELETE /shows/{id}           # Delete show

# Health & Status
GET  /health                 # Database health check
```

### Dependencies
```yaml
External:
  - Supabase PostgreSQL
  - Redis cache

Internal:
  - Key Service (8001) - API keys
```

---

## 📊 Analytics Service (Port 8008)

### Purpose
**Metrics collection and system monitoring** for operational insights.

### Key Responsibilities
- **Prometheus Metrics** - Application and business metrics
- **Performance Monitoring** - Service response times and throughput
- **Usage Analytics** - Show generation patterns and trends
- **Health Dashboards** - System health aggregation
- **Alerting** - Automated notification system

### API Endpoints
```python
# Metrics Collection
GET  /metrics                  # Prometheus metrics format
POST /events                   # Event tracking
GET  /health                   # Service health aggregation

# Analytics & Reporting
GET  /analytics/shows         # Show generation analytics
GET  /analytics/usage         # System usage reports
GET  /analytics/performance   # Performance metrics
```

### Prometheus Integration
```python
from prometheus_client import Counter, Histogram, Gauge

# Business metrics
SHOWS_GENERATED = Counter('radiox_shows_generated_total', 'Total shows generated', ['preset', 'status'])
GENERATION_DURATION = Histogram('radiox_show_generation_duration_seconds', 'Show generation time')
ACTIVE_SESSIONS = Gauge('radiox_active_sessions', 'Current active sessions')

# Service metrics
SERVICE_REQUESTS = Counter('radiox_service_requests_total', 'Service requests', ['service', 'endpoint', 'status'])
SERVICE_RESPONSE_TIME = Histogram('radiox_service_response_time_seconds', 'Service response time', ['service'])

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    """Collect metrics for all requests"""
    start_time = time.time()
    
    response = await call_next(request)
    
    SERVICE_REQUESTS.labels(
        service="analytics",
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    
    SERVICE_RESPONSE_TIME.labels(service="analytics").observe(time.time() - start_time)
    
    return response
```

### Dependencies
```yaml
External Services:
  - Prometheus (metrics collection)
  - Grafana (visualization)

Internal Services:
  - All services (metrics aggregation)
```

---

## Service Communication

### HTTP Client Pattern
```python
class ServiceClient:
    """Base class for inter-service communication"""
    
    def __init__(self, base_url: str, timeout: int = 30):
        self.base_url = base_url
        self.client = httpx.AsyncClient(
            base_url=base_url,
            timeout=timeout,
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
        )
    
    async def get(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        response = await self.client.get(endpoint, **kwargs)
        response.raise_for_status()
        return response.json()
    
    async def post(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        response = await self.client.post(endpoint, **kwargs)
        response.raise_for_status()
        return response.json()

# Usage example
content_client = ServiceClient("http://content-service:8003")
news_data = await content_client.get("/content/news", params={"limit": 10})
```

### Error Handling & Resilience
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
async def resilient_service_call(client: ServiceClient, endpoint: str, **kwargs):
    """Resilient service call with exponential backoff"""
    try:
        return await client.get(endpoint, **kwargs)
    except httpx.HTTPStatusError as e:
        if e.response.status_code >= 500:
            # Retry on server errors
            raise
        else:
            # Don't retry on client errors
            return {"error": f"Client error: {e.response.status_code}"}
    except httpx.RequestError:
        # Network errors - retry
        raise
```

---

## Development & Testing

### Local Development
```bash
# Start specific service
cd services/content-service
python -m uvicorn main:app --reload --port 8003

# Start all services
docker-compose up

# View service logs
docker-compose logs -f content-service
```

### Service Testing
```python
# Unit testing with pytest
@pytest.mark.asyncio
async def test_content_service_news_collection():
    """Test news collection functionality"""
    async with httpx.AsyncClient(app=app, base_url="http://testserver") as client:
        response = await client.get("/content/news?limit=5")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 5
        assert all("title" in item for item in data)

# Integration testing
@pytest.mark.integration
async def test_show_generation_workflow():
    """Test complete show generation across services"""
    # Mock external API calls
    with patch('openai.ChatCompletion.create') as mock_openai:
        mock_openai.return_value = {"choices": [{"message": {"content": "Mock script"}}]}
        
        # Test workflow
        show_response = await show_service.generate_complete_show(
            preset_name="zurich",
            news_count=3
        )
        
        assert show_response.status == "completed"
        assert show_response.audio_url is not None
```

---

## Related Documentation

- **[🏗️ Architecture Overview](architecture.md)** - System design and patterns
- **[🛠️ Development Setup](development.md)** - Local environment setup
- **[🚀 Deployment Guide](../deployment/production.md)** - Production deployment
- **[📊 Monitoring](../deployment/monitoring.md)** - Service monitoring

---

<div align="center">

**🔧 8 microservices working in perfect harmony**

[🛠️ Setup Development](development.md) • [🏗️ View Architecture](architecture.md) • [🚀 Deploy Production](../deployment/production.md)

</div> 