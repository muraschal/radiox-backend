"""
RadioX Show Service
Orchestrates show generation by coordinating all microservices
REAL IMPLEMENTATION with GPT script generation and full orchestration
"""

from fastapi import FastAPI, HTTPException
import httpx
import redis.asyncio as redis
import json
import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import os
from loguru import logger
from pydantic import BaseModel
from supabase import create_client, Client

app = FastAPI(
    title="RadioX Show Service", 
    description="Show Generation Orchestration Service",
    version="1.0.0"
)

# Redis Connection
redis_client: Optional[redis.Redis] = None
supabase_client: Optional[Client] = None

@app.on_event("startup")
async def startup_event():
    global redis_client, supabase_client
    redis_url = os.getenv("REDIS_URL", "redis://redis:6379")
    redis_client = redis.from_url(redis_url, decode_responses=True)
    
    # Initialize Supabase client
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_ANON_KEY") or os.getenv("SUPABASE_KEY")
    if supabase_url and supabase_key:
        supabase_client = create_client(supabase_url, supabase_key)
        logger.info("✅ Supabase client initialized")
    else:
        logger.warning("⚠️ Supabase credentials missing")
    
    logger.info("Show Service started successfully")

@app.on_event("shutdown")
async def shutdown_event():
    if redis_client:
        await redis_client.close()
    logger.info("Show Service shutdown complete")

# Pydantic Models
class ShowRequest(BaseModel):
    preset_name: Optional[str] = None
    target_time: Optional[str] = None
    channel: str = "zurich"
    language: str = "de"
    news_count: int = 2
    primary_speaker: Optional[str] = "marcel"
    secondary_speaker: Optional[str] = "jarvis"
    duration_minutes: int = 3

class ShowResponse(BaseModel):
    session_id: str
    script_content: str
    broadcast_style: str
    estimated_duration_minutes: int
    segments: List[Dict[str, Any]]
    metadata: Dict[str, Any]

class BroadcastStyleService:
    """Manages broadcast styles and timing"""
    
    def __init__(self):
        # V3 ENGLISH BROADCAST STYLES - TIME-BASED PERSONALITIES
        self.broadcast_styles = {
            "morning": {
                "name": "High-Energy Morning",
                "description": "Energetic, motivational, optimistic vibes",
                "marcel_mood": "excited and passionate",
                "jarvis_mood": "witty and sharp",
                "tempo": "fast-paced",
                "duration_target": 8,
                "v3_style": "creative"
            },
            "afternoon": {
                "name": "Professional Afternoon", 
                "description": "Relaxed, informative, professional tone",
                "marcel_mood": "friendly and engaging",
                "jarvis_mood": "analytical and precise",
                "tempo": "medium-paced",
                "duration_target": 10,
                "v3_style": "natural"
            },
            "evening": {
                "name": "Chill Evening",
                "description": "Cozy, thoughtful, conversational",
                "marcel_mood": "thoughtful and warm",
                "jarvis_mood": "philosophical and deep", 
                "tempo": "slow and deliberate",
                "duration_target": 12,
                "v3_style": "natural"
            },
            "night": {
                "name": "Late Night Vibes",
                "description": "Calm, relaxing, introspective atmosphere",
                "marcel_mood": "calm and reflective",
                "jarvis_mood": "mysterious and contemplative",
                "tempo": "very slow and smooth",
                "duration_target": 15,
                "v3_style": "robust"
            }
        }
    
    def determine_broadcast_style(self, target_time: Optional[str] = None) -> Dict[str, Any]:
        """Determine broadcast style based on time of day"""
        if target_time:
            try:
                hour = int(target_time.split(":")[0])
            except:
                hour = datetime.now().hour
        else:
            hour = datetime.now().hour
        
        if 5 <= hour < 12:
            return self.broadcast_styles["morning"]
        elif 12 <= hour < 17:
            return self.broadcast_styles["afternoon"] 
        elif 17 <= hour < 22:
            return self.broadcast_styles["evening"]
        else:
            return self.broadcast_styles["night"]

class GPTScriptGenerator:
    """Handles GPT script generation"""
    
    def __init__(self):
        self.openai_api_key = None
        self.gpt_config = {
            "model": "gpt-4o",
            "max_tokens": 4000,
            "temperature": 0.8,
            "timeout": 180
        }
    
    async def _get_openai_api_key(self) -> Optional[str]:
        """Get OpenAI API key from Data Service"""
        if self.openai_api_key:
            return self.openai_api_key
        
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get("http://data-service:8000/config")
                if response.status_code == 200:
                    config = response.json()
                    self.openai_api_key = config.get("api_keys", {}).get("openai")
                    return self.openai_api_key
        except Exception as e:
            logger.warning(f"⚠️ Failed to get OpenAI API key from Data Service: {str(e)}")
        
        return None
    
    async def generate_script(
        self, 
        content: Dict[str, Any],
        broadcast_style: Dict[str, Any],
        channel: str,
        language: str = "de"
    ) -> str:
        """Generate radio script using GPT-4"""
        
        api_key = await self._get_openai_api_key()
        if not api_key:
            logger.warning("⚠️ OpenAI API key not configured, using mock script")
            return self._generate_mock_script(content, broadcast_style)
        
        logger.info("🤖 Generating script with GPT-4...")
        
        try:
            prompt = self._create_gpt_prompt(content, broadcast_style, channel, language)
            
            async with httpx.AsyncClient(timeout=self.gpt_config["timeout"]) as client:
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }
                
                data = {
                    "model": self.gpt_config["model"],
                    "messages": [
                        {
                            "role": "system", 
                            "content": "Du bist ein Experte für Radio-Skripte und erstellst natürliche, emotionale Dialoge zwischen AI-Moderatoren."
                        },
                        {
                            "role": "user", 
                            "content": prompt
                        }
                    ],
                    "max_tokens": self.gpt_config["max_tokens"],
                    "temperature": self.gpt_config["temperature"]
                }
                
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers=headers,
                    json=data
                )
                
                if response.status_code == 200:
                    result = response.json()
                    script = result['choices'][0]['message']['content'].strip()
                    
                    logger.info(f"✅ Script generated ({len(script)} characters)")
                    return self._post_process_script(script)
                else:
                    logger.error(f"❌ GPT Error {response.status_code}")
                    return self._generate_mock_script(content, broadcast_style)
                    
        except Exception as e:
            logger.error(f"❌ GPT generation failed: {str(e)}")
            return self._generate_mock_script(content, broadcast_style)
    
    def _create_gpt_prompt(
        self, 
        content: Dict[str, Any], 
        broadcast_style: Dict[str, Any],
        channel: str,
        language: str = "de"
    ) -> str:
        """Create GPT prompt for script generation"""
        
        if language == "en":
            return self._create_english_prompt(content, broadcast_style, channel)
        else:
            return self._create_german_prompt(content, broadcast_style, channel)
    
    def _create_german_prompt(
        self, 
        content: Dict[str, Any], 
        broadcast_style: Dict[str, Any],
        channel: str
    ) -> str:
        """Create German prompt for script generation"""
        
        # Prepare news context
        news_context = ""
        news_items = content.get("news", [])
        
        for i, news in enumerate(news_items, 1):
            news_context += f"{i}. [{news.get('category', 'GENERAL').upper()}] {news.get('title', '')}\n"
            news_context += f"   📰 {news.get('source', 'Unknown')} | ⏰ {news.get('age_hours', '?')}h alt\n"
            news_context += f"   📝 {news.get('summary', '')[:200]}...\n\n"
        
        # Context data
        weather_context = ""
        bitcoin_context = ""
        
        if content.get("weather"):
            weather = content["weather"]["current"]
            weather_context = f"🌡️ Wetter: {weather['temperature']}°C, {weather['description']}"
        
        if content.get("bitcoin"):
            bitcoin = content["bitcoin"]
            bitcoin_context = f"₿ Bitcoin: ${bitcoin['price']:,.2f} ({bitcoin['change_24h']:+.1f}%)"
        
        # Current time
        current_time = datetime.now()
        time_context = f"⏰ Zeit: {current_time.strftime('%H:%M')}, {current_time.strftime('%A')}, {current_time.strftime('%d.%m.%Y')}"
        
        # Location context
        location_context = self._get_location_context(channel)
        
        gpt_prompt = f"""Du bist der Chefproduzent von RadioX, einem innovativen Schweizer AI-Radio mit den Moderatoren Marcel (emotional, spontan) und Jarvis (analytisch, witzig).

🎙️ **RADIOX DEUTSCHE BROADCAST-GENERIERUNG**

KONTEXT:
{time_context}
🎭 Stil: {broadcast_style['name']} - {broadcast_style['description']}
🎯 Marcel: {broadcast_style['marcel_mood']} | Jarvis: {broadcast_style['jarvis_mood']}
⚡ Tempo: {broadcast_style['tempo']}
📍 Kanal: {channel.upper()} {location_context}
🎯 Zieldauer: {broadcast_style['duration_target']} Minuten

AKTUELLE DATEN:
{weather_context}
{bitcoin_context}

VERFÜGBARE NEWS:
{news_context}

AUFGABE: Erstelle ein {broadcast_style['duration_target']}-minütiges deutsches Broadcast-Skript mit dieser Struktur:

1. **INTRO** (1-2 Min)
   - Begrüssung mit aktueller Zeit/Wetter
   - Vorschau auf heutige Themen
   - Natürliches Geplänkel zwischen Marcel & Jarvis

2. **HAUPTNEWS-BLOCK** (3-4 Min)
   - Wichtigste Geschichten detailliert
   - Emotionale Reaktionen und Diskussion
   - Marcel: spontane Gefühle, Jarvis: analytische Einblicke

3. **CRYPTO & FINANZEN** (1-2 Min)
   - Bitcoin-Update mit Kontext
   - Marktanalyse
   - Jarvis erklärt, Marcel reagiert emotional

4. **WEITERE NEWS** (2-3 Min)
   - Restliche Geschichten kompakter
   - Schweizer/lokale Bezüge wo relevant
   - Interaktiver Dialog zwischen Moderatoren

5. **OUTRO** (1-2 Min)
   - Zusammenfassung der Kernpunkte
   - Vorschau nächste Sendung
   - Wetterprognose-Verabschiedung

🎭 **CHARAKTER-RICHTLINIEN:**
- **MARCEL**: Enthusiastisch, leidenschaftlich, authentische menschliche Emotionen
  - Wird AUFGEREGT bei Bitcoin/Tech-News
  - Nutzt natürliche deutsche Ausdrücke ("Krass!", "Das ist unglaublich!")
  - Spontane Reaktionen und Unterbrechungen
  - Warme, nahbare Persönlichkeit

- **JARVIS**: Analytische AI, witzig, leicht sarkastisch
  - Liefert datenbasierte Einblicke
  - Gelegentlicher trockener Humor über menschliches Verhalten
  - Technische Erklärungen verständlich gemacht
  - Philosophische Beobachtungen

📻 **TECHNISCHE ANFORDERUNGEN:**
- Verwende ALLE verfügbaren News im Skript
- Baue natürliche Übergänge zwischen Themen
- Inklusive realistische Unterbrechungen und Reaktionen
- Halte {broadcast_style['duration_target']}-Minuten Zieldauer ein
- Schweizer Bezüge und Lokalkolorit

**FORMAT**: Schreibe als Dialog mit klaren Sprecherwechseln:

MARCEL: [Text]
JARVIS: [Text]
MARCEL: [Text]
...

**STARTE DAS SKRIPT SOFORT - KEINE EINLEITUNG!**"""

        return gpt_prompt
    
    def _create_english_prompt(
        self, 
        content: Dict[str, Any], 
        broadcast_style: Dict[str, Any],
        channel: str
    ) -> str:
        """Create English V3-optimized prompt"""
        
        # Similar structure but in English
        news_context = ""
        news_items = content.get("news", [])
        
        for i, news in enumerate(news_items, 1):
            news_context += f"{i}. [{news.get('category', 'GENERAL').upper()}] {news.get('title', '')}\n"
            news_context += f"   📰 {news.get('source', 'Unknown')} | ⏰ {news.get('age_hours', '?')}h ago\n"
            news_context += f"   📝 {news.get('summary', '')[:200]}...\n\n"
        
        weather_context = ""
        bitcoin_context = ""
        
        if content.get("weather"):
            weather = content["weather"]["current"]
            weather_context = f"🌡️ Weather: {weather['temperature']}°C, {weather['description']}"
        
        if content.get("bitcoin"):
            bitcoin = content["bitcoin"]
            bitcoin_context = f"₿ Bitcoin: ${bitcoin['price']:,.2f} ({bitcoin['change_24h']:+.1f}%)"
        
        current_time = datetime.now()
        time_context = f"⏰ Time: {current_time.strftime('%H:%M')}, {current_time.strftime('%A')}, {current_time.strftime('%B %d, %Y')}"
        
        return f"""You are the head producer of RadioX, an innovative Swiss AI radio featuring hosts Marcel (emotional, spontaneous) and Jarvis (analytical, witty AI).

🎙️ **RADIOX ENGLISH V3 BROADCAST GENERATION**

CONTEXT:
{time_context}
🎭 Style: {broadcast_style['name']} - {broadcast_style['description']}
🎯 Marcel: {broadcast_style['marcel_mood']} | Jarvis: {broadcast_style['jarvis_mood']}
⚡ Pacing: {broadcast_style['tempo']}
📍 Channel: {channel.upper()}
🎯 Target Duration: {broadcast_style['duration_target']} minutes

CURRENT DATA:
{weather_context}
{bitcoin_context}

AVAILABLE NEWS:
{news_context}

Create a natural {broadcast_style['duration_target']}-minute English radio dialogue between Marcel and Jarvis covering all available news with Swiss context.

**FORMAT**: Write as dialogue with clear speaker changes:

MARCEL: [Text]
JARVIS: [Text]
MARCEL: [Text]
...

**START THE SCRIPT IMMEDIATELY!**"""
    
    def _get_location_context(self, channel: str) -> str:
        """Get location context for channel"""
        location_contexts = {
            "zurich": "- Fokus auf Zürich und Umgebung",
            "basel": "- Fokus auf Basel und Nordwestschweiz", 
            "bern": "- Fokus auf Bern und Mittelland"
        }
        return location_contexts.get(channel, "- Schweizweiter Fokus")
    
    def _post_process_script(self, script: str) -> str:
        """Post-process generated script"""
        lines = script.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            if line:
                cleaned_lines.append(line)
        
        # Ensure speaker names are correctly formatted
        processed_lines = []
        for line in cleaned_lines:
            if line.startswith("MARCEL:") or line.startswith("JARVIS:"):
                processed_lines.append(line)
            elif ":" in line and (line.upper().startswith("MARCEL") or line.upper().startswith("JARVIS")):
                if line.upper().startswith("MARCEL"):
                    processed_lines.append("MARCEL: " + line.split(":", 1)[1].strip())
                elif line.upper().startswith("JARVIS"):
                    processed_lines.append("JARVIS: " + line.split(":", 1)[1].strip())
            else:
                if processed_lines:
                    processed_lines[-1] += " " + line
        
        return '\n'.join(processed_lines)
    
    def _generate_mock_script(self, content: Dict[str, Any], broadcast_style: Dict[str, Any]) -> str:
        """Generate mock script when GPT unavailable"""
        news_count = len(content.get("news", []))
        weather_info = content.get("weather", {}).get("current", {})
        bitcoin_info = content.get("bitcoin", {})
        
        return f"""MARCEL: Willkommen bei RadioX! Es ist {datetime.now().strftime('%H:%M')} Uhr und hier sind die aktuellen News.

JARVIS: Guten Tag, Marcel. Heute haben wir {news_count} interessante Nachrichten für unsere Hörer. Das Wetter zeigt {weather_info.get('temperature', '?')}°C.

MARCEL: Perfekt! Und Bitcoin steht bei ${bitcoin_info.get('price', 0):,.0f} - das ist {broadcast_style['marcel_mood']}!

JARVIS: Genau, Marcel. Lass uns mit den wichtigsten Nachrichten beginnen...

MARCEL: Das war RadioX für heute. Bis zum nächsten Mal!"""

class ShowOrchestrationService:
    """Main orchestration service for show generation"""
    
    def __init__(self):
        self.broadcast_style_service = BroadcastStyleService()
        self.gpt_generator = GPTScriptGenerator()
        self.api_gateway_url = os.getenv("API_GATEWAY_URL", "http://localhost:8000")
    
    async def generate_show(self, request: ShowRequest) -> ShowResponse:
        """Orchestrate complete show generation"""
        try:
            logger.info(f"🎭 Generating show for channel '{request.channel}' at {request.target_time}")
            
            session_id = str(uuid.uuid4())
            
            # 1. Determine broadcast style
            broadcast_style = self.broadcast_style_service.determine_broadcast_style(request.target_time)
            logger.info(f"🎨 Style: {broadcast_style['name']}")
            
            # 2. Collect content from Content Service
            content = await self._collect_content(request)
            logger.info(f"📰 Content collected: {len(content.get('news', []))} news items")
            
            # 3. Get speaker configurations
            speakers = await self._get_speaker_configs(request.primary_speaker, request.secondary_speaker)
            
            # 4. Generate script with GPT
            script = await self.gpt_generator.generate_script(
                content=content,
                broadcast_style=broadcast_style,
                channel=request.channel,
                language=request.language
            )
            
            # 5. Parse script into segments
            segments = self._parse_script_segments(script)
            
            # 6. Estimate duration
            estimated_duration = self._estimate_duration(script)
            
            # 7. Generate audio via Audio Service
            audio_result = await self._generate_audio(session_id, script, request)
            
            # 8. Store show data with audio info
            await self._store_show_data(session_id, script, content, broadcast_style, request, audio_result)
            
            # 9. Build response
            response = ShowResponse(
                session_id=session_id,
                script_content=script,
                broadcast_style=broadcast_style["name"],
                estimated_duration_minutes=estimated_duration,
                segments=segments,
                metadata={
                    "preset": request.preset_name,
                    "channel": request.channel,
                    "language": request.language,
                    "speakers": speakers,
                    "content_stats": content.get("collection_stats", {}),
                    "generated_at": datetime.now().isoformat(),
                    "audio_file": audio_result.get("audio_file") if audio_result else None,
                    "audio_url": audio_result.get("audio_url") if audio_result else None,
                    "audio_duration": audio_result.get("duration_seconds") if audio_result else None
                }
            )
            
            logger.info(f"✅ Show generated: {session_id} ({estimated_duration} min)")
            return response
            
        except Exception as e:
            logger.error(f"❌ Show generation failed: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Show generation failed: {str(e)}")
    
    async def _collect_content(self, request: ShowRequest) -> Dict[str, Any]:
        """Collect content from Content Service"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    "http://content-service:8000/content",
                    params={
                        "news_count": request.news_count,
                        "language": request.language
                    }
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.warning(f"⚠️ Content service returned {response.status_code}")
                    return self._get_mock_content()
                    
        except Exception as e:
            logger.error(f"❌ Content collection failed: {str(e)}")
            return self._get_mock_content()
    
    async def _get_speaker_configs(self, primary: Optional[str], secondary: Optional[str]) -> Dict[str, Any]:
        """Get speaker configurations from Speaker Service"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Get primary speaker
                primary_response = await client.get(f"http://speaker-service:8000/speakers/{primary or 'marcel'}")
                secondary_response = await client.get(f"http://speaker-service:8000/speakers/{secondary or 'jarvis'}")
                
                primary_config = primary_response.json() if primary_response.status_code == 200 else {"name": primary or "marcel"}
                secondary_config = secondary_response.json() if secondary_response.status_code == 200 else {"name": secondary or "jarvis"}
                
                return {
                    "primary": primary_config,
                    "secondary": secondary_config
                }
                
        except Exception as e:
            logger.warning(f"⚠️ Speaker config failed: {str(e)}")
            return {
                "primary": {"name": primary or "marcel"},
                "secondary": {"name": secondary or "jarvis"}
            }
    
    def _parse_script_segments(self, script: str) -> List[Dict[str, Any]]:
        """Parse script into segments"""
        segments = []
        lines = script.split('\n')
        current_segment = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            if line.startswith("MARCEL:") or line.startswith("JARVIS:"):
                speaker, text = line.split(":", 1)
                segment = {
                    "type": "dialogue",
                    "speaker": speaker.lower(),
                    "text": text.strip(),
                    "estimated_duration": len(text.split()) / 2.5  # ~150 words/min
                }
                segments.append(segment)
        
        return segments
    
    def _estimate_duration(self, script: str) -> int:
        """Estimate script duration in minutes"""
        word_count = len(script.split())
        estimated_minutes = max(1, round(word_count / 150))  # ~150 words per minute
        return estimated_minutes
    
    async def _store_show_data(
        self, 
        session_id: str, 
        script: str, 
        content: Dict[str, Any], 
        broadcast_style: Dict[str, Any], 
        request: ShowRequest,
        audio_result: Optional[Dict[str, Any]] = None
    ):
        """Store show data using Clean Architecture - Google Style"""
        try:
            # Prepare clean show data model - Match Data Service ShowRecord
            show_data = {
                "session_id": session_id,
                "title": f"{broadcast_style['name']} - {request.channel.title()}",
                "script_content": script,
                "script_preview": script[:200] + "..." if len(script) > 200 else script,
                "broadcast_style": broadcast_style["name"],
                "channel": request.channel,
                "language": request.language,
                "news_count": len(content.get("news", [])),
                "estimated_duration_minutes": self._estimate_duration(script),
                "audio_url": audio_result.get("audio_url") if audio_result else None,
                "audio_duration_seconds": audio_result.get("duration_seconds") if audio_result else None,
                "created_at": datetime.now().isoformat(),
                "metadata": {
                    "content_sources": len(content.get("news", [])),
                    "has_weather": bool(content.get("weather")),
                    "has_bitcoin": bool(content.get("bitcoin")),
                    "generation_timestamp": datetime.now().isoformat()
                }
            }
            
            # Store in Redis cache for immediate access (Performance Layer)
            if redis_client:
                await redis_client.setex(
                    f"show:{session_id}",
                    3600,  # 1 hour TTL
                    json.dumps(show_data, default=str)
                )
                logger.info(f"✅ Show {session_id} cached in Redis")
            
            # Store in Data Service using Clean Architecture - Single Source of Truth
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    "http://172.18.0.10:8006/shows",
                    json=show_data
                )
                
                if response.status_code == 200:
                    logger.info(f"✅ Show {session_id} stored in database via Data Service")
                else:
                    logger.error(f"❌ Data Service storage failed: {response.status_code} - {response.text}")
                    # Don't fail the whole operation if database storage fails
                    # Redis cache ensures immediate availability
                
        except Exception as e:
            logger.error(f"❌ Show data storage failed: {str(e)}")
            # Don't raise exception - show generation should continue even if storage fails
    
    async def _generate_audio(self, session_id: str, script: str, request: ShowRequest) -> Optional[Dict[str, Any]]:
        """Generate audio via Audio Service"""
        try:
            logger.info(f"🎵 Generating audio for session: {session_id}")
            
            async with httpx.AsyncClient(timeout=120.0) as client:  # 2 minute timeout for audio generation
                audio_request = {
                    "script_content": script,
                    "session_id": session_id,
                    "include_music": False,
                    "export_format": "mp3",
                    "voice_quality": "mid",
                    "preset_name": request.preset_name or "default",
                    "duration_minutes": getattr(request, 'duration_minutes', 3)
                }
                
                response = await client.post(
                    "http://audio-service:8000/script",
                    json=audio_request
                )
                
                if response.status_code == 200:
                    audio_result = response.json()
                    logger.info(f"✅ Audio generated: {audio_result.get('segments_count', 0)} segments")
                    return audio_result
                else:
                    logger.error(f"❌ Audio Service error {response.status_code}: {response.text}")
                    return None
                    
        except Exception as e:
            logger.error(f"❌ Audio generation failed: {str(e)}")
            return None
    
    def _get_mock_content(self) -> Dict[str, Any]:
        """Mock content when services unavailable"""
        return {
            "news": [
                {
                    "title": "Mock News Article",
                    "summary": "This is a mock news article for testing purposes",
                    "source": "mock",
                    "category": "news",
                    "age_hours": 1
                }
            ],
            "weather": {
                "current": {
                    "temperature": 18,
                    "description": "teilweise bewölkt"
                }
            },
            "bitcoin": {
                "price": 45000,
                "change_24h": 2.5
            },
            "collection_stats": {
                "total_news_collected": 1,
                "news_selected": 1
            }
        }

show_service = ShowOrchestrationService()

# Health Check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "show-service"}

# Show Generation
@app.post("/generate", response_model=ShowResponse)
async def generate_show(request: ShowRequest):
    """Generate complete radio show"""
    return await show_service.generate_show(request)

# Shows List - Updated to use Supabase directly
@app.get("/shows")
async def list_shows(limit: int = 10, offset: int = 0):
    """List all generated shows using Supabase as primary source"""
    try:
        # Validate parameters - Fail Fast
        if limit < 1 or limit > 100:
            raise HTTPException(status_code=400, detail="Limit must be between 1 and 100")
        
        if offset < 0:
            raise HTTPException(status_code=400, detail="Offset must be non-negative")
        
        # Try Supabase first
        if supabase_client:
            try:
                import asyncio
                import functools
                
                # Run Supabase query in thread pool since it's sync
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None, 
                    functools.partial(
                        lambda: supabase_client.table("shows").select("*").order("created_at", desc=True).range(offset, offset + limit - 1).execute()
                    )
                )
                
                if response.data:
                    shows = []
                    for show in response.data:
                        show_summary = {
                            "id": show.get("id"),
                            "session_id": show.get("session_id"),
                            "title": show.get("title"),
                            "created_at": show.get("created_at"),
                            "channel": show.get("channel"),
                            "language": show.get("language"),
                            "news_count": show.get("news_count", 0),
                            "broadcast_style": show.get("broadcast_style"),
                            "script_preview": show.get("script_preview"),
                            "estimated_duration_minutes": show.get("estimated_duration_minutes")
                        }
                        shows.append(show_summary)
                    
                    # Get total count for pagination
                    count_response = await loop.run_in_executor(
                        None, 
                        functools.partial(
                            lambda: supabase_client.table("shows").select("id").execute()
                        )
                    )
                    total = len(count_response.data) if count_response.data else len(shows)
                    
                    logger.info(f"📋 Listed {len(shows)} shows via Supabase")
                    return {
                        "shows": shows,
                        "total": total,
                        "limit": limit,
                        "offset": offset,
                        "has_more": offset + limit < total,
                        "source": "supabase"
                    }
                
            except Exception as e:
                logger.error(f"❌ Supabase query failed: {str(e)}")
        
        # Fallback to Data Service
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                "http://data-service:8000/shows",
                params={"limit": limit, "offset": offset}
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"📋 Listed {len(data.get('shows', []))} shows via Data Service")
                return data
            else:
                logger.error(f"❌ Data Service failed: {response.status_code}")
                # Fallback to Redis if Data Service fails
                return await _fallback_list_from_redis(limit, offset)
                
    except Exception as e:
        logger.error(f"❌ List shows failed: {str(e)}")
        # Fallback to Redis for resilience
        return await _fallback_list_from_redis(limit, offset)

async def _fallback_list_from_redis(limit: int = 10, offset: int = 0):
    """Fallback method using Redis - Resilience Pattern"""
    try:
        if not redis_client:
            raise HTTPException(status_code=503, detail="No storage available")
        
        # Get all show keys from Redis
        show_keys = await redis_client.keys("show:*")
        
        if not show_keys:
            return {
                "shows": [],
                "total": 0,
                "limit": limit,
                "offset": offset,
                "has_more": False,
                "source": "redis_fallback"
            }
        
        # Sort keys by creation time (newest first)
        show_keys.sort(reverse=True)
        
        # Apply pagination
        paginated_keys = show_keys[offset:offset + limit]
        
        # Load show data for paginated keys
        shows = []
        for key in paginated_keys:
            try:
                show_data = await redis_client.get(key)
                if show_data:
                    parsed_show = json.loads(show_data)
                    # Add essential frontend info
                    show_summary = {
                        "id": parsed_show.get("session_id"),
                        "title": f"{parsed_show.get('broadcast_style', 'Show')} - {parsed_show.get('channel', 'Default').title()}",
                        "created_at": parsed_show.get("created_at"),
                        "channel": parsed_show.get("channel"),
                        "language": parsed_show.get("language"),
                        "news_count": parsed_show.get("news_count", 0),
                        "broadcast_style": parsed_show.get("broadcast_style"),
                        "script_preview": (parsed_show.get("script_content", "")[:200] + "...") if len(parsed_show.get("script_content", "")) > 200 else parsed_show.get("script_content", "")
                    }
                    shows.append(show_summary)
            except Exception as e:
                logger.warning(f"⚠️ Failed to load show {key}: {str(e)}")
                continue
        
        logger.warning(f"⚠️ Using Redis fallback: {len(shows)} shows loaded")
        
        return {
            "shows": shows,
            "total": len(show_keys),
            "limit": limit,
            "offset": offset,
            "has_more": offset + limit < len(show_keys),
            "source": "redis_fallback"
        }
        
    except Exception as e:
        logger.error(f"❌ Redis fallback failed: {str(e)}")
        raise HTTPException(status_code=503, detail="All storage systems unavailable")

@app.get("/shows/{session_id}")
async def get_show(session_id: str):
    """Get show by session ID"""
    try:
        if redis_client:
            show_data = await redis_client.get(f"show:{session_id}")
            if show_data:
                return json.loads(show_data)
        
        raise HTTPException(status_code=404, detail="Show not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/styles")
async def get_broadcast_styles():
    """Get available broadcast styles"""
    return show_service.broadcast_style_service.broadcast_styles

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 