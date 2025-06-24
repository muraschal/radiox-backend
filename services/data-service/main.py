"""
RadioX Data Service
Handles database access, configuration management, and data persistence
"""

from fastapi import FastAPI, HTTPException
import redis.asyncio as redis
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import os
from loguru import logger
from pydantic import BaseModel
from supabase import create_client, Client
from dataclasses import dataclass, asdict

# Import shared services (will be extracted from monolith)
import sys
sys.path.append('/app/src')

app = FastAPI(
    title="RadioX Data Service",
    description="Database Access and Configuration Service",
    version="1.0.0"
)

# Redis Connection
redis_client: Optional[redis.Redis] = None

# Supabase Client
supabase_client: Optional[Client] = None

@app.on_event("startup")
async def startup_event():
    global redis_client, supabase_client
    
    # Initialize Redis
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    redis_client = redis.from_url(redis_url, decode_responses=True)
    
    # Initialize Supabase
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if supabase_url and supabase_key:
        supabase_client = create_client(supabase_url, supabase_key)
        logger.info("✅ Supabase client initialized")
    else:
        logger.warning("⚠️ Supabase credentials not found - running in mock mode")
    
    logger.info("Data Service started successfully")

@app.on_event("shutdown")
async def shutdown_event():
    if redis_client:
        await redis_client.close()
    logger.info("Data Service shutdown complete")

# Pydantic Models
class RadioScriptCreate(BaseModel):
    script_id: str
    station_type: str
    target_hour: str
    total_duration_seconds: int
    segment_count: int
    news_count: int
    tweet_count: int
    weather_city: str
    script_data: Dict[str, Any]
    metadata: Dict[str, Any]

class NewsContentCreate(BaseModel):
    title: str
    summary: str
    source: str
    category: str
    priority: int = 5
    content_type: str = "rss_news"
    metadata: Dict[str, Any]

class DataService:
    """Handles database operations and configuration management"""
    
    async def get_configuration(self) -> Dict[str, Any]:
        """Get complete system configuration"""
        try:
            logger.info("🔍 Getting configuration...")
            # Check cache first
            if redis_client:
                cached_config = await redis_client.get("system_config")
                if cached_config:
                    logger.info("📦 Configuration loaded from cache")
                    return json.loads(cached_config)
                else:
                    logger.info("❌ No cached configuration found")
            
            # Get configuration from database
            logger.info("🔄 Loading configuration from database...")
            config = await self._load_configuration_from_db()
            
            # Cache configuration
            if redis_client:
                await redis_client.setex(
                    "system_config", 
                    300,  # 5 minutes TTL
                    json.dumps(config)
                )
                logger.info("💾 Configuration cached for 5 minutes")
            
            return config
            
        except Exception as e:
            logger.error(f"Configuration loading failed: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Configuration loading failed: {str(e)}")
    
    async def get_show_presets(self) -> List[Dict[str, Any]]:
        """Get all show presets from database"""
        try:
            # Check cache first
            if redis_client:
                cached_presets = await redis_client.get("show_presets")
                if cached_presets:
                    return json.loads(cached_presets)
            
            # Get from Supabase if available
            if supabase_client:
                result = supabase_client.table('show_presets').select('*').execute()
                if result.data:
                    presets = result.data
                else:
                    presets = self._get_default_presets()
            else:
                presets = self._get_default_presets()
            
            # Cache presets
            if redis_client:
                await redis_client.setex(
                    "show_presets", 
                    300,  # 5 minutes TTL
                    json.dumps(presets)
                )
            
            return presets
            
        except Exception as e:
            logger.error(f"Presets loading failed: {str(e)}")
            return self._get_default_presets()
    
    async def get_speakers(self) -> List[Dict[str, Any]]:
        """Get all speaker configurations from database"""
        try:
            # Check cache first
            if redis_client:
                cached_speakers = await redis_client.get("speakers")
                if cached_speakers:
                    return json.loads(cached_speakers)
            
            # Get from Supabase if available
            if supabase_client:
                result = supabase_client.table('speakers').select('*').execute()
                if result.data:
                    speakers = result.data
                else:
                    speakers = self._get_default_speakers()
            else:
                speakers = self._get_default_speakers()
            
            # Cache speakers
            if redis_client:
                await redis_client.setex(
                    "speakers", 
                    300,  # 5 minutes TTL
                    json.dumps(speakers)
                )
            
            return speakers
            
        except Exception as e:
            logger.error(f"Speakers loading failed: {str(e)}")
            return self._get_default_speakers()
    
    async def get_elevenlabs_models(self) -> List[Dict[str, Any]]:
        """Get ElevenLabs voice models from database"""
        try:
            # Check cache first
            if redis_client:
                cached_models = await redis_client.get("elevenlabs_models")
                if cached_models:
                    return json.loads(cached_models)
            
            # Get from Supabase if available
            if supabase_client:
                result = supabase_client.table('elevenlabs_models').select('*').execute()
                if result.data:
                    models = result.data
                else:
                    models = self._get_default_elevenlabs_models()
            else:
                models = self._get_default_elevenlabs_models()
            
            # Cache models
            if redis_client:
                await redis_client.setex(
                    "elevenlabs_models", 
                    300,  # 5 minutes TTL
                    json.dumps(models)
                )
            
            return models
            
        except Exception as e:
            logger.error(f"ElevenLabs models loading failed: {str(e)}")
            return self._get_default_elevenlabs_models()
    
    async def save_radio_script(self, script_data: RadioScriptCreate) -> str:
        """Save radio script to database"""
        try:
            script_dict = script_data.dict()
            script_dict['created_at'] = datetime.utcnow().isoformat()
            script_dict['status'] = 'generated'
            
            if supabase_client:
                result = supabase_client.table('radio_scripts').insert(script_dict).execute()
                if result.data:
                    logger.info(f"✅ Radio script {script_data.script_id} saved to Supabase")
                    return script_data.script_id
            else:
                # Fallback to Redis cache
                if redis_client:
                    await redis_client.setex(
                        f"script:{script_data.script_id}",
                        3600,  # 1 hour TTL
                        json.dumps(script_dict)
                    )
                    return script_data.script_id
            
            return script_data.script_id
            
        except Exception as e:
            logger.error(f"Script save failed: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Script save failed: {str(e)}")
    
    async def get_radio_script(self, script_id: str) -> Optional[Dict[str, Any]]:
        """Get radio script from database"""
        try:
            # Check Redis first
            if redis_client:
                cached_script = await redis_client.get(f"script:{script_id}")
                if cached_script:
                    return json.loads(cached_script)
            
            # Get from Supabase
            if supabase_client:
                result = supabase_client.table('radio_scripts').select('*').eq('id', script_id).execute()
                if result.data and len(result.data) > 0:
                    return result.data[0]
            
            return None
            
        except Exception as e:
            logger.error(f"Script load failed: {str(e)}")
            return None
    
    async def save_news_content(self, news_items: List[NewsContentCreate]) -> int:
        """Save news content to database"""
        try:
            saved_count = 0
            
            for news_item in news_items:
                news_dict = news_item.dict()
                news_dict['created_at'] = datetime.utcnow().isoformat()
                news_dict['published_at'] = datetime.utcnow().isoformat()
                
                if supabase_client:
                    # Check for duplicates
                    existing = supabase_client.table('news_content').select('id').eq('title', news_item.title).execute()
                    
                    if not existing.data:
                        result = supabase_client.table('news_content').insert(news_dict).execute()
                        if result.data:
                            saved_count += 1
                else:
                    # Fallback to Redis
                    if redis_client:
                        news_id = f"news:{datetime.utcnow().timestamp()}"
                        await redis_client.setex(
                            news_id,
                            86400,  # 24 hours TTL
                            json.dumps(news_dict)
                        )
                        saved_count += 1
            
            logger.info(f"✅ {saved_count} news items saved")
            return saved_count
            
        except Exception as e:
            logger.error(f"News save failed: {str(e)}")
            return 0
    
    async def get_recent_content(self, content_type: Optional[str] = None, hours_back: int = 24, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent content from database"""
        try:
            if supabase_client:
                since_time = datetime.utcnow() - timedelta(hours=hours_back)
                
                query = supabase_client.table('news_content').select('*')
                
                if content_type:
                    query = query.eq('content_type', content_type)
                
                query = query.gte('published_at', since_time.isoformat())
                query = query.order('published_at', desc=True).limit(limit)
                
                result = query.execute()
                
                if result.data:
                    return result.data
            
            return []
            
        except Exception as e:
            logger.error(f"Content load failed: {str(e)}")
            return []
    
    async def _load_configuration_from_db(self) -> Dict[str, Any]:
        """Load configuration from database"""
        global supabase_client
        try:
            if supabase_client:
                logger.info("🔍 Loading configuration from Supabase...")
                # Get all configuration from database
                response = supabase_client.table('configuration').select('*').execute()
                logger.info(f"📊 Supabase response: {len(response.data) if response.data else 0} items")
                
                if response.data:
                    config_dict = {item['config_key']: item['config_value'] for item in response.data}
                    logger.info(f"🔑 Config keys loaded: {list(config_dict.keys())}")
                    
                    config = {
                        "api_keys": {
                            "openai": config_dict.get('openai_api_key'),
                            "elevenlabs": config_dict.get('elevenlabs_api_key'),
                            "weather": config_dict.get('weather_api_key'),
                            "coinmarketcap": config_dict.get('coinmarketcap_api_key')
                        },
                        "default_settings": {
                            "language": config_dict.get('default_language', 'de'),
                            "news_count": int(config_dict.get('default_news_count', '2')),
                            "show_duration": int(config_dict.get('default_show_duration', '180'))
                        },
                        "audio_settings": {
                            "sample_rate": int(config_dict.get('audio_sample_rate', '44100')),
                            "channels": int(config_dict.get('audio_channels', '2')),
                            "format": config_dict.get('audio_format', 'mp3')
                        }
                    }
                    logger.info(f"✅ Configuration loaded successfully: OpenAI={config['api_keys']['openai'] is not None}, ElevenLabs={config['api_keys']['elevenlabs'] is not None}")
                    return config
                else:
                    logger.warning("⚠️ No configuration data found in database")
            else:
                logger.warning("⚠️ Supabase client not available")
        except Exception as e:
            logger.error(f"❌ Failed to load configuration from database: {str(e)}")
        
        # Fallback configuration if database is not available
        logger.info("🔄 Using fallback configuration")
        return {
            "api_keys": {
                "openai": os.getenv("OPENAI_API_KEY"),
                "elevenlabs": os.getenv("ELEVENLABS_API_KEY"),
                "weather": None,
                "coinmarketcap": None
            },
            "default_settings": {
                "language": "de",
                "news_count": 2,
                "show_duration": 180
            },
            "audio_settings": {
                "sample_rate": 44100,
                "channels": 2,
                "format": "mp3"
            }
        }
    
    def _get_default_presets(self) -> List[Dict[str, Any]]:
        """Get default show presets"""
        return [
            {
                "id": "zurich",
                "name": "Zürich News",
                "description": "Zürich focused news show",
                "location": "zurich",
                "language": "de",
                "format": "news_talk",
                "duration_target": 180,
                "primary_speaker": "marcel",
                "secondary_speaker": None,
                "jingle_path": "/jingles/zurich_intro.mp3"
            },
            {
                "id": "global",
                "name": "Global News Hot",
                "description": "International news show",
                "location": "global",
                "language": "en",
                "format": "news_talk",
                "duration_target": 200,
                "primary_speaker": "brad",
                "secondary_speaker": "lucy",
                "jingle_path": "/jingles/global_intro.mp3"
            }
        ]
    
    def _get_default_speakers(self) -> List[Dict[str, Any]]:
        """Get default speaker configurations"""
        return [
            {
                "id": "marcel",
                "name": "Marcel",
                "voice_id": "pNInz6obpgDQGcFmaJgB",
                "language": "de",
                "role": "primary",
                "description": "Primary German speaker",
                "style": "professional"
            },
            {
                "id": "brad",
                "name": "Brad",
                "voice_id": "N2lVS1w4EtoT3dr4eOWO",
                "language": "en",
                "role": "primary",
                "description": "Primary English speaker",
                "style": "energetic"
            },
            {
                "id": "lucy",
                "name": "Lucy",
                "voice_id": "XB0fDUnXU5powFXDhCwa",
                "language": "en",
                "role": "secondary",
                "description": "Secondary English speaker",
                "style": "friendly"
            }
        ]
    
    def _get_default_elevenlabs_models(self) -> List[Dict[str, Any]]:
        """Get default ElevenLabs models"""
        return [
            {
                "id": "eleven_turbo_v2",
                "name": "Eleven Turbo v2",
                "quality": "high",
                "speed": "fast",
                "default": True
            },
            {
                "id": "eleven_multilingual_v2",
                "name": "Eleven Multilingual v2",
                "quality": "highest",
                "speed": "medium",
                "default": False
            }
        ]

data_service = DataService()

# Health Check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "data-service",
        "supabase": "connected" if supabase_client else "mock_mode",
        "redis": "connected" if redis_client else "disconnected"
    }

# Configuration Endpoints
@app.get("/config")
async def get_config():
    """Get system configuration"""
    logger.info("🚀 /config endpoint called")
    result = await data_service.get_configuration()
    logger.info(f"📋 Config result: OpenAI={result.get('api_keys', {}).get('openai') is not None}")
    return result

@app.get("/presets")
async def get_presets():
    """Get show presets"""
    return await data_service.get_show_presets()

@app.get("/speakers")
async def get_speakers():
    """Get speaker configurations"""
    return await data_service.get_speakers()

@app.get("/speakers/{speaker_name}")
async def get_speaker(speaker_name: str):
    """Get specific speaker configuration"""
    try:
        # Get voice configuration from Supabase
        if supabase_client:
            result = supabase_client.table('voice_configurations').select('*').eq('speaker_name', speaker_name.lower()).execute()
            
            if result.data and len(result.data) > 0:
                voice_config = result.data[0]
                return {
                    "speaker_name": voice_config["speaker_name"],
                    "voice_id": voice_config["voice_id"],
                    "voice_name": voice_config["voice_name"],
                    "language": voice_config["language"],
                    "stability": float(voice_config["stability"]),
                    "similarity_boost": float(voice_config["similarity_boost"]),
                    "style": float(voice_config["style"]),
                    "use_speaker_boost": voice_config["use_speaker_boost"],
                    "model": voice_config["model"],
                    "is_active": voice_config["is_active"]
                }
            else:
                raise HTTPException(status_code=404, detail=f"Speaker '{speaker_name}' not found")
        else:
            # Fallback to default speakers
            speakers = await data_service.get_speakers()
            for speaker in speakers:
                if speaker.get("id", "").lower() == speaker_name.lower():
                    return speaker
            
            raise HTTPException(status_code=404, detail=f"Speaker '{speaker_name}' not found")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Speaker lookup failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Speaker lookup failed: {str(e)}")

@app.get("/elevenlabs/models")
async def get_elevenlabs_models():
    """Get ElevenLabs voice models"""
    return await data_service.get_elevenlabs_models()

# Script Management
@app.post("/scripts")
async def save_script(script: RadioScriptCreate):
    """Save radio script"""
    script_id = await data_service.save_radio_script(script)
    return {"script_id": script_id, "status": "saved"}

@app.get("/scripts/{script_id}")
async def get_script(script_id: str):
    """Get radio script"""
    script = await data_service.get_radio_script(script_id)
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")
    return script

# News Content Management
@app.post("/news")
async def save_news(news_items: List[NewsContentCreate]):
    """Save news content"""
    count = await data_service.save_news_content(news_items)
    return {"saved_count": count}

@app.get("/content/recent")
async def get_recent_content(content_type: Optional[str] = None, hours_back: int = 24, limit: int = 50):
    """Get recent content"""
    return await data_service.get_recent_content(content_type, hours_back, limit)

# Cache Management
@app.post("/cache/clear")
async def clear_cache():
    """Clear configuration cache"""
    if redis_client:
        await redis_client.delete("system_config", "show_presets", "speakers", "elevenlabs_models")
        return {"message": "Cache cleared successfully"}
    return {"message": "Redis not available"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 