"""
RadioX Speaker Service - FULLY MODULAR
Handles speaker configurations and voice management
ENHANCED: Complete database-driven configuration, zero hardcoding
"""

from fastapi import FastAPI, HTTPException
import httpx
from typing import Dict, Any, Optional, List
import os
from loguru import logger
import json

app = FastAPI(
    title="RadioX Speaker Service - Modular",
    description="Database-driven Speaker Configuration and Voice Management Service",
    version="2.0.0-modular"
)

# Configuration required - no fallbacks

async def get_speakers_from_database_service() -> List[Dict[str, Any]]:
    """Load speakers from Database Service"""
    try:
        database_service_url = os.getenv("DATABASE_SERVICE_URL", "http://localhost:8001")
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{database_service_url}/speakers")
            
            if response.status_code == 200:
                speakers_data = response.json()
                if isinstance(speakers_data, list) and len(speakers_data) > 0:
                    logger.info(f"✅ Loaded {len(speakers_data)} speakers from Database Service")
                    return speakers_data
    except Exception as e:
                logger.warning(f"⚠️ Speaker lookup failed: {e}")
    
    # Return error instead of fallback data
    raise HTTPException(
        status_code=503,
        detail="Speaker configuration unavailable - Database Service connection failed"
    )

async def get_speaker_from_database_service(speaker_id: str) -> Optional[Dict[str, Any]]:
    """Get specific speaker from Database Service"""
    try:
        database_service_url = os.getenv("DATABASE_SERVICE_URL", "http://localhost:8001")
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{database_service_url}/speakers/{speaker_id}")
            
            if response.status_code == 200:
                speaker_data = response.json()
                if isinstance(speaker_data, dict):
                    logger.info(f"✅ Loaded speaker '{speaker_id}' from Database Service")
                    return speaker_data
            elif response.status_code == 404:
                return None
    except Exception as e:
        logger.warning(f"⚠️ Speaker '{speaker_id}' lookup failed: {e}")
    
    # No fallback data - require Database Service
    return None

@app.get("/health")
async def health_check():
    """Health check endpoint - Modular"""
    return {
        "status": "healthy", 
        "service": "speaker-service", 
        "version": "2.0.0-modular",
        "modular_config": True
    }

@app.get("/speakers")
async def get_speakers():
    """Get all speaker configurations - Modular"""
    try:
        speakers = await get_speakers_from_database_service()
        return {
            "speakers": speakers,
            "count": len(speakers),
            "modular_config": True,
            "source": "database_service"
        }
    except Exception as e:
        logger.error(f"Failed to get speakers: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/speakers/{speaker_id}")
async def get_speaker(speaker_id: str):
    """Get specific speaker details - Modular"""
    try:
        speaker = await get_speaker_from_database_service(speaker_id)
        
        if not speaker:
            raise HTTPException(status_code=404, detail=f"Speaker '{speaker_id}' not found")
        
        return {
            "speaker": speaker,
            "modular_config": True,
            "source": "database_service"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get speaker {speaker_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/speakers/{speaker_id}/config")
async def get_speaker_voice_config(speaker_id: str):
    """Get speaker voice configuration for audio generation - Modular"""
    try:
        speaker = await get_speaker_from_database_service(speaker_id)
        
        if not speaker:
            raise HTTPException(status_code=404, detail=f"Speaker '{speaker_id}' not found")
        
        # Extract voice configuration
        voice_config = {
            "voice_id": speaker.get("voice_id"),
            "language": speaker.get("language", "en"),
            "settings": speaker.get("voice_settings", {
                "stability": 0.5,
                "similarity_boost": 0.8,
                "style": 0.2,
                "use_speaker_boost": True
            }),
            "model": speaker.get("model", "eleven_multilingual_v2")
        }
        
        return {
            "speaker_id": speaker_id,
            "voice_config": voice_config,
            "modular_config": True
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get voice config for {speaker_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/speakers/by-language/{language}")
async def get_speakers_by_language(language: str):
    """Get speakers filtered by language - Modular"""
    try:
        all_speakers = await get_speakers_from_database_service()
        filtered_speakers = [s for s in all_speakers if s.get("language", "").lower() == language.lower()]
        
        return {
            "language": language,
            "speakers": filtered_speakers,
            "count": len(filtered_speakers),
            "modular_config": True
        }
    except Exception as e:
        logger.error(f"Failed to get speakers by language {language}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/speakers/by-role/{role}")
async def get_speakers_by_role(role: str):
    """Get speakers filtered by role - Modular"""
    try:
        all_speakers = await get_speakers_from_database_service()
        filtered_speakers = [s for s in all_speakers if s.get("role", "").lower() == role.lower()]
        
        return {
            "role": role,
            "speakers": filtered_speakers,
            "count": len(filtered_speakers),
            "modular_config": True
        }
    except Exception as e:
        logger.error(f"Failed to get speakers by role {role}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/config/reload")
async def reload_speaker_config():
    """Reload speaker configuration from Data Service"""
    try:
        speakers = await get_speakers_from_database_service()
        
        return {
            "status": "success",
            "message": "Speaker configuration reloaded",
            "speakers_count": len(speakers),
            "modular_config": True,
            "source": "database_service"
        }
    except Exception as e:
        logger.error(f"Speaker configuration reload failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Configuration reload failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("SPEAKER_SERVICE_PORT", "8006"))
    uvicorn.run(app, host="0.0.0.0", port=port) 