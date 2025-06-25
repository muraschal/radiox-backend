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
import asyncio

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
    global redis_client, supabase_client, data_service
    
    # Initialize Redis
    redis_url = os.getenv("REDIS_URL", "redis://redis:6379")
    redis_client = redis.from_url(redis_url, decode_responses=True)
    
    # Initialize Supabase
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if supabase_url and supabase_key:
        supabase_client = create_client(supabase_url, supabase_key)
        logger.info("✅ Supabase client initialized")
        
        # Initialize Show Storage Interface AFTER Supabase is ready
        if supabase_client:
            data_service.show_storage = SupabaseShowStorage(supabase_client)
            logger.info("✅ Show storage interface initialized after Supabase connection")
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
    """Enhanced DataService with Clean Architecture - Google Style"""
    
    def __init__(self):
        self.config_cache = {}
        self.config_cache_timestamp = 0
        
        # Initialize clean storage interface
        global supabase_client
        if supabase_client:
            self.show_storage = SupabaseShowStorage(supabase_client)
            logger.info("✅ Clean show storage initialized")
        else:
            self.show_storage = None
            logger.warning("⚠️ Show storage unavailable - Supabase not connected")
    
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

    async def store_show_data(self, show_data: Dict[str, Any]) -> bool:
        """Store show data using clean architecture - Single Responsibility"""
        logger.info(f"🔍 store_show_data called, current show_storage: {self.show_storage}")
        
        # ALWAYS try to initialize show_storage if it's None
        if not self.show_storage:
            logger.info("🔄 Attempting lazy initialization of show storage")
            supabase_url = os.getenv("SUPABASE_URL")
            supabase_key = os.getenv("SUPABASE_KEY")
            
            logger.info(f"🔑 Supabase URL exists: {bool(supabase_url)}, Key exists: {bool(supabase_key)}")
            
            if supabase_url and supabase_key:
                try:
                    from supabase import create_client
                    local_supabase_client = create_client(supabase_url, supabase_key)
                    self.show_storage = SupabaseShowStorage(local_supabase_client)
                    logger.info("✅ Show storage initialized lazily with direct credentials")
                except Exception as e:
                    logger.error(f"❌ Failed to create Supabase client: {str(e)}")
                    return False
            else:
                logger.error("❌ Supabase credentials not available for show storage")
                return False
        else:
            logger.info("ℹ️ Show storage already exists")
        
        if not self.show_storage:
            logger.error("❌ Show storage still not available after lazy initialization")
            return False
        
        try:
            # Convert to clean data model
            show_record = ShowRecord(
                session_id=show_data["session_id"],
                title=f"{show_data.get('broadcast_style', 'Show')} - {show_data.get('channel', 'Default').title()}",
                script_content=show_data["script_content"],
                script_preview="",  # Will be auto-generated in __post_init__
                broadcast_style=show_data["broadcast_style"],
                channel=show_data["channel"],
                language=show_data["language"],
                news_count=show_data["news_count"],
                estimated_duration_minutes=show_data.get("estimated_duration_minutes", 0),
                metadata={
                    "created_at": show_data["created_at"],
                    "generation_source": "show_service"
                }
            )
            
            # Store with clean interface - Fail Fast
            success = await self.show_storage.store_show(show_record)
            
            if success:
                logger.info(f"✅ Show {show_record.session_id} stored successfully")
            else:
                logger.error(f"❌ Failed to store show {show_record.session_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Show storage failed: {str(e)}")
            return False
    
    async def get_show_data(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get show data using clean architecture"""
        if not self.show_storage:
            return None
        
        try:
            show_record = await self.show_storage.get_show(session_id)
            
            if show_record:
                # Convert back to API format
                return {
                    "session_id": show_record.session_id,
                    "title": show_record.title,
                    "script_content": show_record.script_content,
                    "script_preview": show_record.script_preview,
                    "broadcast_style": show_record.broadcast_style,
                    "channel": show_record.channel,
                    "language": show_record.language,
                    "news_count": show_record.news_count,
                    "estimated_duration_minutes": show_record.estimated_duration_minutes,
                    "audio_url": show_record.audio_url,
                    "audio_duration_seconds": show_record.audio_duration_seconds,
                    "metadata": show_record.metadata,
                    "created_at": show_record.created_at
                }
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Show retrieval failed: {str(e)}")
            return None
    
    async def list_shows_data(self, limit: int = 10, offset: int = 0) -> Dict[str, Any]:
        """List shows using clean architecture"""
        if not self.show_storage:
            return {"shows": [], "total": 0, "limit": limit, "offset": offset}
        
        try:
            # Get shows and count in parallel for performance
            shows_task = self.show_storage.list_shows(limit, offset)
            count_task = self.show_storage.get_shows_count()
            
            shows, total_count = await asyncio.gather(shows_task, count_task)
            
            # Convert to API format
            show_list = []
            for show in shows:
                show_list.append({
                    "id": show.session_id,
                    "title": show.title,
                    "script_preview": show.script_preview,
                    "channel": show.channel,
                    "language": show.language,
                    "news_count": show.news_count,
                    "broadcast_style": show.broadcast_style,
                    "created_at": show.created_at
                })
            
            return {
                "shows": show_list,
                "total": total_count,
                "limit": limit,
                "offset": offset,
                "has_more": offset + limit < total_count
            }
            
        except Exception as e:
            logger.error(f"❌ Shows listing failed: {str(e)}")
            return {"shows": [], "total": 0, "limit": limit, "offset": offset}

# Global data service instance - initialized after class definition
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

# Add clean data models and interfaces at the top after imports

# Clean Data Models - Google Style
@dataclass
class ShowRecord:
    """Clean data model for Show storage - Single Responsibility"""
    session_id: str
    title: str
    script_content: str
    script_preview: str
    broadcast_style: str
    channel: str
    language: str
    news_count: int
    estimated_duration_minutes: int
    audio_url: Optional[str] = None
    audio_duration_seconds: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: Optional[str] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.created_at is None:
            self.created_at = datetime.utcnow().isoformat()
        if not self.script_preview:
            self.script_preview = self.script_content[:200] + "..." if len(self.script_content) > 200 else self.script_content

@dataclass 
class ShowSummary:
    """Lightweight show summary for listings - Performance Optimized"""
    id: str
    session_id: str
    title: str
    script_preview: str
    channel: str
    language: str
    news_count: int
    broadcast_style: str
    created_at: str

class ShowStorageInterface:
    """Clean interface for show storage - Separation of Concerns"""
    
    async def store_show(self, show: ShowRecord) -> bool:
        """Store show with transaction consistency"""
        raise NotImplementedError
    
    async def get_show(self, session_id: str) -> Optional[ShowRecord]:
        """Get single show by session_id"""
        raise NotImplementedError
    
    async def list_shows(self, limit: int = 10, offset: int = 0) -> List[ShowSummary]:
        """List shows with pagination"""
        raise NotImplementedError
    
    async def get_shows_count(self) -> int:
        """Get total shows count"""
        raise NotImplementedError

class SupabaseShowStorage(ShowStorageInterface):
    """Google-Style Implementation: Single Responsibility + Fail Fast"""
    
    def __init__(self, supabase_client: Client):
        self.client = supabase_client
        self.table_name = "shows"
    
    async def store_show(self, show: ShowRecord) -> bool:
        """Store show with proper error handling and transaction consistency"""
        try:
            # Prepare record for database
            show_dict = {
                "session_id": show.session_id,
                "title": show.title,
                "script_content": show.script_content,
                "script_preview": show.script_preview,
                "broadcast_style": show.broadcast_style,
                "channel": show.channel,
                "language": show.language,
                "news_count": show.news_count,
                "estimated_duration_minutes": show.estimated_duration_minutes,
                "audio_url": show.audio_url,
                "audio_duration_seconds": show.audio_duration_seconds,
                "metadata": show.metadata,
                "created_at": show.created_at
            }
            
            # Atomic operation - Fail Fast
            result = await asyncio.to_thread(
                lambda: self.client.table(self.table_name).upsert(show_dict).execute()
            )
            
            if result.data:
                logger.info(f"✅ Show {show.session_id} stored successfully")
                return True
            else:
                logger.error(f"❌ Failed to store show {show.session_id}: No data returned")
                return False
                
        except Exception as e:
            logger.error(f"❌ Show storage failed: {str(e)}")
            return False
    
    async def get_show(self, session_id: str) -> Optional[ShowRecord]:
        """Get show with proper error handling"""
        try:
            result = await asyncio.to_thread(
                lambda: self.client.table(self.table_name)
                .select("*")
                .eq("session_id", session_id)
                .single()
                .execute()
            )
            
            if result.data:
                return ShowRecord(
                    session_id=result.data["session_id"],
                    title=result.data["title"],
                    script_content=result.data["script_content"],
                    script_preview=result.data["script_preview"],
                    broadcast_style=result.data["broadcast_style"],
                    channel=result.data["channel"],
                    language=result.data["language"],
                    news_count=result.data["news_count"],
                    estimated_duration_minutes=result.data["estimated_duration_minutes"],
                    audio_url=result.data.get("audio_url"),
                    audio_duration_seconds=result.data.get("audio_duration_seconds"),
                    metadata=result.data.get("metadata", {}),
                    created_at=result.data["created_at"]
                )
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Show retrieval failed: {str(e)}")
            return None
    
    async def list_shows(self, limit: int = 10, offset: int = 0) -> List[ShowSummary]:
        """Efficient show listing with pagination"""
        try:
            result = await asyncio.to_thread(
                lambda: self.client.table(self.table_name)
                .select("session_id, title, script_preview, channel, language, news_count, broadcast_style, created_at")
                .order("created_at", desc=True)
                .range(offset, offset + limit - 1)
                .execute()
            )
            
            shows = []
            for row in result.data:
                shows.append(ShowSummary(
                    id=row["session_id"],
                    session_id=row["session_id"], 
                    title=row["title"],
                    script_preview=row["script_preview"],
                    channel=row["channel"],
                    language=row["language"],
                    news_count=row["news_count"],
                    broadcast_style=row["broadcast_style"],
                    created_at=row["created_at"]
                ))
            
            return shows
            
        except Exception as e:
            logger.error(f"❌ Shows listing failed: {str(e)}")
            return []
    
    async def get_shows_count(self) -> int:
        """Get total shows count efficiently"""
        try:
            result = await asyncio.to_thread(
                lambda: self.client.table(self.table_name)
                .select("session_id")
                .execute()
            )
            
            return result.count if result.count else 0
            
        except Exception as e:
            logger.error(f"❌ Shows count failed: {str(e)}")
            return 0

# Add clean API endpoints at the end

# ================================
# CLEAN API ENDPOINTS - Google Style
# ================================

@app.post("/shows")
async def store_show(show_data: Dict[str, Any]):
    """Store show data with clean architecture - Single Responsibility"""
    try:
        success = await data_service.store_show_data(show_data)
        
        if success:
            return {"success": True, "message": "Show stored successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to store show")
    
    except Exception as e:
        logger.error(f"❌ Store show endpoint failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Store show failed: {str(e)}")

@app.get("/shows")
async def list_shows(limit: int = 10, offset: int = 0):
    """List shows with clean architecture and pagination"""
    try:
        # Validate parameters - Fail Fast
        if limit < 1 or limit > 100:
            raise HTTPException(status_code=400, detail="Limit must be between 1 and 100")
        
        if offset < 0:
            raise HTTPException(status_code=400, detail="Offset must be non-negative")
        
        result = await data_service.list_shows_data(limit, offset)
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ List shows endpoint failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to list shows")

@app.get("/shows/{session_id}")
async def get_show(session_id: str):
    """Get single show with clean architecture"""
    try:
        # Validate session_id - Fail Fast
        if not session_id or len(session_id) < 10:
            raise HTTPException(status_code=400, detail="Invalid session_id")
        
        show_data = await data_service.get_show_data(session_id)
        
        if show_data:
            return {"success": True, "show": show_data}
        else:
            raise HTTPException(status_code=404, detail="Show not found")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Get show endpoint failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get show")

@app.get("/shows/stats")
async def get_shows_stats():
    """Get show statistics with clean architecture"""
    try:
        if not data_service.show_storage:
            raise HTTPException(status_code=503, detail="Show storage not available")
        
        total_count = await data_service.show_storage.get_shows_count()
        
        # Get recent shows for additional stats
        recent_shows = await data_service.show_storage.list_shows(limit=5, offset=0)
        
        # Calculate basic stats
        channels = set()
        languages = set()
        for show in recent_shows:
            channels.add(show.channel)
            languages.add(show.language)
        
        return {
            "total_shows": total_count,
            "recent_shows_count": len(recent_shows),
            "active_channels": list(channels),
            "active_languages": list(languages),
            "last_generated": recent_shows[0].created_at if recent_shows else None
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Show stats endpoint failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get show statistics")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8006) 