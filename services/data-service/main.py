"""
RadioX Data Service
Handles database access, configuration management, and data persistence
"""

from fastapi import FastAPI, HTTPException
import redis.asyncio as redis
import json
from datetime import datetime
from typing import Dict, Any, Optional, List
import os
from loguru import logger
from pydantic import BaseModel

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

@app.on_event("startup")
async def startup_event():
    global redis_client
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    redis_client = redis.from_url(redis_url, decode_responses=True)
    logger.info("Data Service started successfully")

@app.on_event("shutdown")
async def shutdown_event():
    if redis_client:
        await redis_client.close()
    logger.info("Data Service shutdown complete")

class DataService:
    """Handles database operations and configuration management"""
    
    def __init__(self):
        self.supabase_client = None
        self.config_cache = {}
    
    async def initialize_clients(self):
        """Initialize database clients"""
        # Will be extracted from existing services
        pass
    
    async def get_configuration(self) -> Dict[str, Any]:
        """Get complete system configuration"""
        try:
            # Check cache first
            if redis_client:
                cached_config = await redis_client.get("system_config")
                if cached_config:
                    return json.loads(cached_config)
            
            # Get configuration from database
            config = await self._load_configuration_from_db()
            
            # Cache configuration
            if redis_client:
                await redis_client.setex(
                    "system_config", 
                    300,  # 5 minutes TTL
                    json.dumps(config)
                )
            
            return config
            
        except Exception as e:
            logger.error(f"Configuration loading failed: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Configuration loading failed: {str(e)}")
    
    async def get_show_presets(self) -> List[Dict[str, Any]]:
        """Get all show presets"""
        try:
            # Check cache first
            if redis_client:
                cached_presets = await redis_client.get("show_presets")
                if cached_presets:
                    return json.loads(cached_presets)
            
            # Get presets from database
            presets = await self._load_presets_from_db()
            
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
            raise HTTPException(status_code=500, detail=f"Presets loading failed: {str(e)}")
    
    async def get_speakers(self) -> List[Dict[str, Any]]:
        """Get all speaker configurations"""
        try:
            # Check cache first
            if redis_client:
                cached_speakers = await redis_client.get("speakers")
                if cached_speakers:
                    return json.loads(cached_speakers)
            
            # Get speakers from database
            speakers = await self._load_speakers_from_db()
            
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
            raise HTTPException(status_code=500, detail=f"Speakers loading failed: {str(e)}")
    
    async def get_elevenlabs_models(self) -> List[Dict[str, Any]]:
        """Get ElevenLabs voice models"""
        try:
            # Check cache first
            if redis_client:
                cached_models = await redis_client.get("elevenlabs_models")
                if cached_models:
                    return json.loads(cached_models)
            
            # Get models from database
            models = await self._load_elevenlabs_models_from_db()
            
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
            raise HTTPException(status_code=500, detail=f"ElevenLabs models loading failed: {str(e)}")
    
    async def _load_configuration_from_db(self) -> Dict[str, Any]:
        """Load configuration from database"""
        # This will be extracted from existing ConfigurationService
        return {
            "api_keys": {
                "openai": os.getenv("OPENAI_API_KEY"),
                "elevenlabs": os.getenv("ELEVENLABS_API_KEY")
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
    
    async def _load_presets_from_db(self) -> List[Dict[str, Any]]:
        """Load show presets from database"""
        # This will be extracted from existing services
        return [
            {
                "id": "zurich",
                "name": "Zürich News",
                "description": "Zürich focused news show",
                "location": "zurich",
                "language": "de",
                "format": "news_talk",
                "duration_target": 180
            },
            {
                "id": "global",
                "name": "Global News Hot",
                "description": "International news show",
                "location": "global",
                "language": "en",
                "format": "news_talk",
                "duration_target": 200
            }
        ]
    
    async def _load_speakers_from_db(self) -> List[Dict[str, Any]]:
        """Load speaker configurations from database"""
        # This will be extracted from existing services
        return [
            {
                "id": "marcel",
                "name": "Marcel",
                "voice_id": "pNInz6obpgDQGcFmaJgB",
                "language": "de",
                "role": "primary",
                "description": "Primary German speaker"
            },
            {
                "id": "brad",
                "name": "Brad",
                "voice_id": "N2lVS1w4EtoT3dr4eOWO",
                "language": "en",
                "role": "primary",
                "description": "Primary English speaker"
            },
            {
                "id": "lucy",
                "name": "Lucy",
                "voice_id": "XB0fDUnXU5powFXDhCwa",
                "language": "en",
                "role": "secondary",
                "description": "Secondary English speaker"
            }
        ]
    
    async def _load_elevenlabs_models_from_db(self) -> List[Dict[str, Any]]:
        """Load ElevenLabs models from database"""
        # This will be extracted from existing services
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
    return {"status": "healthy", "service": "data-service"}

# Configuration Endpoints
@app.get("/config")
async def get_config():
    """Get system configuration"""
    return await data_service.get_configuration()

@app.get("/presets")
async def get_presets():
    """Get show presets"""
    return await data_service.get_show_presets()

@app.get("/speakers")
async def get_speakers():
    """Get speaker configurations"""
    return await data_service.get_speakers()

@app.get("/elevenlabs/models")
async def get_elevenlabs_models():
    """Get ElevenLabs voice models"""
    return await data_service.get_elevenlabs_models()

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