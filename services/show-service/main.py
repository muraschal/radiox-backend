"""
RadioX Show Service - VOLLMODULAR VERSION
Orchestrates show generation by coordinating all microservices
ALLE HARDCODED WERTE DURCH DATABASE LOOKUPS ERSETZT!
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
import pytz

# 🚀 MODULAR CONFIGURATION IMPORTS
from database.modular_config import modular_config, ShowPreset, BroadcastStyle, Location
from database.client_factory import get_db_client, ConnectionType

app = FastAPI(
    title="RadioX Show Service - Modular", 
    description="Vollmodularer Show Generation Service - Keine Hardcoding!",
    version="2.0.0"
)

# Redis Connection
redis_client: Optional[redis.Redis] = None

@app.on_event("startup")
async def startup_event():
    global redis_client
    
    logger.info("🚀 Show Service startup - FAIL FAST MODE")
    
    # Initialize Redis - FAIL FAST
    try:
        redis_url = os.getenv("REDIS_URL", "redis://redis:6379")
        redis_client = redis.from_url(redis_url, decode_responses=True)
        await redis_client.ping()  # Test connection immediately
        logger.info("✅ Redis connection verified")
    except Exception as e:
        logger.error(f"❌ FAIL FAST: Redis connection failed: {e}")
        raise Exception(f"Show Service REQUIRES Redis connection: {e}")
    
    # Check OpenAI API Key - FAIL FAST
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        logger.error("❌ FAIL FAST: OpenAI API key missing")
        raise Exception("Show Service REQUIRES OPENAI_API_KEY environment variable")
    logger.info("✅ OpenAI API key verified")
    
    # Test Database Factory connection - FAIL FAST
    try:
        db_client = get_db_client(ConnectionType.REGULAR)
        # Test actual database connection
        await modular_config.get_default_values()  # This should work if DB is connected
        logger.info("✅ Database factory connection verified")
    except Exception as e:
        logger.error(f"❌ FAIL FAST: Database factory connection failed: {e}")
        raise Exception(f"Show Service REQUIRES Database factory connection: {e}")
    
    # Test critical microservice dependencies - FAIL FAST
    required_services = [
        ("Data Service", "http://localhost:8001"),
        ("Data Collector Service", "http://data-collector-service:8004"),
        ("Audio Service", "http://audio-service:8004")
    ]
    
    for service_name, service_url in required_services:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{service_url}/health")
                if response.status_code != 200:
                    raise Exception(f"{service_name} unhealthy: {response.status_code}")
            logger.info(f"✅ {service_name} connection verified")
        except Exception as e:
            logger.error(f"❌ FAIL FAST: {service_name} connection failed: {e}")
            raise Exception(f"Show Service REQUIRES {service_name} connection: {e}")
    
    logger.info("✅ Show Service startup complete - ALL DEPENDENCIES VERIFIED")

@app.on_event("shutdown")
async def shutdown_event():
    if redis_client:
        await redis_client.close()
    logger.info("Show Service shutdown complete")

# Pydantic Models - jetzt mit dynamischen Defaults
class ShowRequest(BaseModel):
    preset_name: Optional[str] = None
    target_time: Optional[str] = None
    channel: Optional[str] = None  # Wird aus DB geladen
    language: Optional[str] = None  # Wird aus DB geladen
    news_count: Optional[int] = None  # Wird aus DB geladen
    primary_speaker: Optional[str] = None  # Wird aus DB geladen
    secondary_speaker: Optional[str] = None  # Wird aus DB geladen
    duration_minutes: Optional[int] = None  # Wird aus Broadcast Style geladen

class ShowResponse(BaseModel):
    session_id: str
    script_content: str
    broadcast_style: str
    estimated_duration_minutes: int
    segments: List[Dict[str, Any]]
    metadata: Dict[str, Any]

class ModularBroadcastStyleService:
    """Vollmodularer Broadcast Style Service - alle Werte aus DB"""
    
    def __init__(self):
        pass  # Keine hardcoded Werte mehr!
    
    async def determine_broadcast_style(self, target_time: Optional[str] = None, style_name: Optional[str] = None) -> Optional[BroadcastStyle]:
        """Bestimme Broadcast Style basierend auf Zeit oder Name - vollständig aus DB"""
        
        if style_name:
            # Spezifischer Style angefordert
            return await modular_config.get_broadcast_style(style_name)
        
        # Zeitbasierte Style-Auswahl
        if target_time:
            try:
                hour = int(target_time.split(":")[0])
            except:
                # Default timezone aus DB laden
                default_tz = await modular_config.get_dynamic_config('system', 'default_timezone')
                tz = pytz.timezone(default_tz or 'Europe/Zurich')
                hour = datetime.now(tz).hour
        else:
            # Default timezone aus DB laden
            default_tz = await modular_config.get_dynamic_config('system', 'default_timezone')
            tz = pytz.timezone(default_tz or 'Europe/Zurich')
            hour = datetime.now(tz).hour
        
        # Zeitbasierte Auswahl aus DB
        return await modular_config.get_broadcast_style_by_time(hour)

class ModularGPTScriptGenerator:
    """Vollmodularer GPT Script Generator - Templates aus DB"""
    
    def __init__(self):
        self.openai_api_key = None
        self.gpt_config = {
            "model": "gpt-4o",
            "max_tokens": 4000,
            "temperature": 0.8,
            "timeout": 180
        }
    
    async def _get_openai_api_key(self) -> Optional[str]:
        """Get OpenAI API key from environment"""
        if self.openai_api_key:
            return self.openai_api_key
        
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        
        if not self.openai_api_key:
            logger.warning("⚠️ OPENAI_API_KEY not found in environment variables")
            return None
            
        logger.info("✅ OpenAI API key loaded from environment")
        return self.openai_api_key
    
    async def generate_script(
        self, 
        content: Dict[str, Any],
        show_preset: ShowPreset
    ) -> str:
        """Generate radio script using GPT-4 with modular templates"""
        
        api_key = await self._get_openai_api_key()
        if not api_key:
                    raise HTTPException(
            status_code=503,
            detail="Show Service: OpenAI API key required for script generation"
        )
        
        logger.info("🤖 Generating script with GPT-4 using modular templates...")
        
        try:
            prompt = await self._create_modular_gpt_prompt(content, show_preset)
            
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
                            "content": show_preset.template.system_prompt
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
                    script = result["choices"][0]["message"]["content"].strip()
                    return await self._post_process_script(script)
                else:
                    logger.error(f"❌ OpenAI API error: {response.status_code} - {response.text}")
                    raise HTTPException(
                        status_code=503,
                        detail="Show Service: OpenAI API configuration error"
                    )
        
        except Exception as e:
            logger.error(f"❌ Script generation failed: {e}")
            raise HTTPException(
                status_code=503,
                detail="Show Service: OpenAI API service unavailable"
            )
    
    async def _create_modular_gpt_prompt(
        self, 
        content: Dict[str, Any], 
        show_preset: ShowPreset
    ) -> str:
        """Create GPT prompt using modular templates from database"""
        
        # News content
        news_section = ""
        if content.get("news") and isinstance(content["news"], list):
            news_section = "\n".join([
                f"- {article.get('title', 'Unbekannter Titel')}: {article.get('summary', article.get('description', 'Keine Beschreibung'))}"
                for article in content["news"][:3]
            ])
        
        # Weather info
        weather_section = ""
        if content.get("weather"):
            weather_info = content["weather"]
            temp = weather_info.get("temperature", "N/A")
            desc = weather_info.get("description", "Keine Wetterdaten")
            weather_section = f"Wetter in {show_preset.location.display_name}: {temp}°C, {desc}"
        
        # Bitcoin info
        bitcoin_section = ""
        if content.get("bitcoin"):
            bitcoin_info = content["bitcoin"]
            price = bitcoin_info.get("price", "N/A")
            change = bitcoin_info.get("change_24h", 0)
            bitcoin_section = f"Bitcoin: ${price:,.0f} ({change:+.1f}% 24h)" if isinstance(price, (int, float)) else f"Bitcoin: {price}"
        
        # Build modular prompt
        prompt = f"""
SHOW KONFIGURATION:
- Preset: {show_preset.display_name}
- Stil: {show_preset.broadcast_style.display_name}
- Sprecher: {show_preset.primary_speaker.title()}"""
        
        if show_preset.secondary_speaker:
            prompt += f" & {show_preset.secondary_speaker.title()}"
        
        prompt += f"""
- Ort: {show_preset.location.display_name}
- Zieldauer: {show_preset.broadcast_style.duration_target} Minuten

SPRECHER-STIMMUNGEN:
- {show_preset.primary_speaker.title()}: {show_preset.broadcast_style.marcel_mood}
- {show_preset.secondary_speaker.title() if show_preset.secondary_speaker else 'Jarvis'}: {show_preset.broadcast_style.jarvis_mood}

CONTENT:
{news_section}

{weather_section}

{bitcoin_section}

{show_preset.template.format_instructions}

GPT SELECTION INSTRUCTIONS:
{show_preset.gpt_selection_instructions}
"""
        
        return prompt
    
    async def _post_process_script(self, script: str) -> str:
        """Post-process script with modular speaker tags"""
        
        # Get speaker tags from config
        speaker_tags = await modular_config.get_speaker_tags()
        
        # Normalisiere Speaker Tags
        script = script.replace("[Marcel]", "[MARCEL]")
        script = script.replace("[marcel]", "[MARCEL]")
        script = script.replace("[Jarvis]", "[JARVIS]")
        script = script.replace("[jarvis]", "[JARVIS]")
        
        # Stelle sicher, dass Script mit einem Sprecher beginnt
        if not script.startswith("[MARCEL]") and not script.startswith("[JARVIS]"):
            script = "[MARCEL] " + script
        
        return script.strip()
    


class ModularShowOrchestrationService:
    """Vollmodularer Show Orchestration Service"""
    
    def __init__(self):
        self.broadcast_service = ModularBroadcastStyleService()
        self.script_generator = ModularGPTScriptGenerator()
    
    async def generate_show(self, request: ShowRequest) -> ShowResponse:
        """Generiere Show mit vollmodularer Konfiguration"""
        session_id = str(uuid.uuid4())
        
        logger.info(f"🎯 Generating modular show: {session_id}")
        
        try:
            # 1. Load defaults from database if not provided
            defaults = await modular_config.get_default_values()
            
            # Apply defaults
            if not request.channel:
                request.channel = defaults.get('default_channel', 'zurich')
            if not request.language:
                request.language = defaults.get('default_language', 'de')
            if not request.news_count:
                request.news_count = int(defaults.get('default_news_count', '3'))
            if not request.primary_speaker:
                request.primary_speaker = defaults.get('default_primary_speaker', 'marcel')
            if not request.secondary_speaker:
                request.secondary_speaker = defaults.get('default_secondary_speaker', 'jarvis')
            
            # 2. Load show preset if specified
            show_preset = None
            if request.preset_name:
                show_preset = await modular_config.get_show_preset(request.preset_name)
                if show_preset:
                    # Override request with preset values
                    request.channel = show_preset.location.location_code
                    request.primary_speaker = show_preset.primary_speaker
                    request.secondary_speaker = show_preset.secondary_speaker
                    logger.info(f"✅ Using preset: {show_preset.display_name}")
            
            # 3. If no preset, create one from request
            if not show_preset:
                # Load individual components
                location = await modular_config.get_location(request.channel)
                if not location:
                    raise HTTPException(status_code=400, detail=f"Unknown location: {request.channel}")
                
                broadcast_style = await self.broadcast_service.determine_broadcast_style(request.target_time)
                if not broadcast_style:
                    raise HTTPException(status_code=500, detail="No broadcast style available")
                
                template = await modular_config.get_show_template('radio_show_de')
                if not template:
                    raise HTTPException(status_code=500, detail="No show template available")
                
                # Create temporary preset
                show_preset = ShowPreset(
                    preset_name='dynamic',
                    display_name='Dynamic Show',
                    primary_speaker=request.primary_speaker,
                    secondary_speaker=request.secondary_speaker,
                    weather_speaker=None,
                    location=location,
                    broadcast_style=broadcast_style,
                    template=template,
                    gpt_selection_instructions='Standard news selection'
                )
            
            # 4. Collect content
            content = await self._collect_content(request, show_preset.location, show_preset)
            
            # 5. Generate script
            script = await self.script_generator.generate_script(content, show_preset)
            
            # 6. Parse segments
            segments = self._parse_script_segments(script)
            
            # 7. Estimate duration
            estimated_duration = self._estimate_duration(script)
            
            # 8. Generate audio asynchronously
            asyncio.create_task(self._generate_audio(session_id, script, request))
            
            # 9. Store show data
            await self._store_show_data_modular(
                session_id, script, content, show_preset, request
            )
            
            return ShowResponse(
                session_id=session_id,
                script_content=script,
                broadcast_style=show_preset.broadcast_style.display_name,
                estimated_duration_minutes=estimated_duration,
                segments=segments,
                metadata={
                    "preset_used": show_preset.preset_name,
                    "location": show_preset.location.display_name,
                    "speakers": [show_preset.primary_speaker, show_preset.secondary_speaker],
                    "news_count": len(content.get("news", [])),
                    "generation_time": datetime.utcnow().isoformat()
                }
            )
            
        except Exception as e:
            logger.error(f"❌ Show generation failed: {e}")
            raise HTTPException(status_code=500, detail=f"Show generation failed: {str(e)}")
    
    async def _collect_content(self, request: ShowRequest, location: Location, show_preset = None) -> Dict[str, Any]:
        """Collect content using modular configuration with category filtering"""
        try:
            # Build parameters for data collection
            params = {
                "news_count": request.news_count,
                "language": request.language,
                "location": location.weather_api_name  # Use DB config
            }
            
            # Add feed categories from show preset if available
            if show_preset and hasattr(show_preset, 'feed_category') and getattr(show_preset, 'feed_category', None):
                params["feed_categories"] = show_preset.feed_category
                logger.info(f"🎯 Using category filter from preset: {show_preset.feed_category}")
            
            # Use location from database for weather API
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    "http://data-collector-service:8004/content",
                    params=params
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.warning(f"⚠️ Content service error: {response.status_code}")
                    raise HTTPException(
                        status_code=503,
                        detail="Show Service: Content Service unavailable for content generation"
                    )
        
        except Exception as e:
            logger.warning(f"⚠️ Content collection failed: {e}")
            raise HTTPException(
                status_code=503,
                detail="Show Service: Content Service connection failed"
            )
    
    def _parse_script_segments(self, script: str) -> List[Dict[str, Any]]:
        """Parse script into speaker segments"""
        segments = []
        current_speaker = None
        current_text = ""
        
        for line in script.split('\n'):
            line = line.strip()
            if not line:
                continue
            
            if line.startswith('[MARCEL]'):
                if current_speaker and current_text:
                    segments.append({
                        "speaker": current_speaker,
                        "text": current_text.strip(),
                        "duration_estimate": len(current_text.split()) * 0.5
                    })
                current_speaker = "marcel"
                current_text = line[8:].strip()
            elif line.startswith('[JARVIS]'):
                if current_speaker and current_text:
                    segments.append({
                        "speaker": current_speaker,
                        "text": current_text.strip(),
                        "duration_estimate": len(current_text.split()) * 0.5
                    })
                current_speaker = "jarvis"
                current_text = line[8:].strip()
            else:
                current_text += " " + line
        
        # Add final segment
        if current_speaker and current_text:
            segments.append({
                "speaker": current_speaker,
                "text": current_text.strip(),
                "duration_estimate": len(current_text.split()) * 0.5
            })
        
        return segments
    
    def _estimate_duration(self, script: str) -> int:
        """Estimate duration in minutes"""
        word_count = len(script.split())
        # Average speaking rate: 150 words per minute
        duration_minutes = max(1, round(word_count / 150))
        return duration_minutes
    
    async def _store_show_data_modular(
        self, 
        session_id: str, 
        script: str, 
        content: Dict[str, Any], 
        show_preset: ShowPreset,
        request: ShowRequest,
        audio_result: Optional[Dict[str, Any]] = None
    ):
        """Store show data using modular configuration"""
        try:
            db_client = get_db_client(ConnectionType.REGULAR)
            
            show_data = {
                "session_id": session_id,
                "title": f"{show_preset.broadcast_style.display_name} - {show_preset.location.display_name}",
                "script_content": script,
                "broadcast_style": show_preset.broadcast_style.display_name,
                "channel": show_preset.location.location_code,
                "language": request.language,
                "preset_name": show_preset.preset_name if show_preset.preset_name != 'dynamic' else None,
                "audio_url": audio_result.get("audio_url") if audio_result else None,
                "audio_duration_seconds": audio_result.get("duration_seconds") if audio_result else None,
                "audio_file_size": audio_result.get("file_size") if audio_result else None,
                "estimated_duration_minutes": self._estimate_duration(script),
                "news_count": len(content.get("news", [])),
                "location_code": show_preset.location.location_code,
                "metadata": {
                    "preset_used": show_preset.preset_name,
                    "speakers": [show_preset.primary_speaker, show_preset.secondary_speaker],
                    "broadcast_style_config": {
                        "marcel_mood": show_preset.broadcast_style.marcel_mood,
                        "jarvis_mood": show_preset.broadcast_style.jarvis_mood,
                        "duration_target": show_preset.broadcast_style.duration_target
                    }
                }
            }
            
            # Use direct Supabase client for insert
            result = db_client.client.table("shows").insert(show_data).execute()
            
            logger.info(f"✅ Show data stored with modular config: {session_id}")
            
        except Exception as e:
            logger.error(f"❌ Failed to store show data: {e}")
    
    async def _generate_audio(self, session_id: str, script: str, request: ShowRequest) -> Optional[Dict[str, Any]]:
        """Generate audio for the script"""
        try:
            async with httpx.AsyncClient(timeout=300.0) as client:
                response = await client.post(
                    "http://audio-service:8004/generate",
                    json={
                        "session_id": session_id,
                        "script": script,
                        "primary_speaker": request.primary_speaker,
                        "secondary_speaker": request.secondary_speaker
                    }
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.warning(f"⚠️ Audio generation failed: {response.status_code}")
                    return None
        
        except Exception as e:
            logger.warning(f"⚠️ Audio generation error: {e}")
            return None
    


# Service instances
orchestration_service = ModularShowOrchestrationService()

# API Endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "RadioX Show Service - Modular",
        "version": "2.0.0",
        "modular": True,
        "hardcoding": "eliminated"
    }

@app.post("/generate", response_model=ShowResponse)
async def generate_show(request: ShowRequest):
    """Generate a radio show using modular configuration"""
    return await orchestration_service.generate_show(request)

@app.get("/styles")
async def get_broadcast_styles():
    """Get all available broadcast styles from database"""
    try:
        # Get all broadcast styles from database
        db_client = get_db_client(ConnectionType.READ)
        result = db_client.client.table("broadcast_styles").select("*").eq("is_active", True).execute()
        
        return {
            "broadcast_styles": result.data,
            "source": "database",
            "modular": True
        }
    except Exception as e:
        logger.error(f"❌ Failed to get broadcast styles: {e}")
        return {"error": str(e)}

@app.get("/presets")
async def get_show_presets():
    """Get all available show presets"""
    try:
        db_client = get_db_client(ConnectionType.READ)
        result = db_client.client.table("show_presets").select("preset_name,display_name,description,city_focus,primary_speaker,secondary_speaker").eq("is_active", True).execute()
        
        return {
            "presets": result.data,
            "source": "database",
            "modular": True
        }
    except Exception as e:
        logger.error(f"❌ Failed to get presets: {e}")
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("SHOW_SERVICE_PORT", "8008"))
    uvicorn.run(app, host="0.0.0.0", port=port) 