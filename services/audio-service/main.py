"""
RadioX Audio Service
Handles audio generation with ElevenLabs and audio processing
"""

from fastapi import FastAPI, HTTPException
import redis.asyncio as redis
from typing import Dict, Any, Optional
import os
from loguru import logger
from pydantic import BaseModel

app = FastAPI(
    title="RadioX Audio Service",
    description="Audio Generation and Processing Service",
    version="1.0.0"
)

# Redis Connection
redis_client: Optional[redis.Redis] = None

@app.on_event("startup")
async def startup_event():
    global redis_client
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    redis_client = redis.from_url(redis_url, decode_responses=True)
    logger.info("Audio Service started successfully")

@app.on_event("shutdown")
async def shutdown_event():
    if redis_client:
        await redis_client.close()
    logger.info("Audio Service shutdown complete")

class AudioGenerationRequest(BaseModel):
    show_id: str
    script: Dict[str, Any]
    speakers: Dict[str, str]

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "audio-service"}

@app.post("/generate")
async def generate_audio(request: AudioGenerationRequest):
    """Generate audio from script"""
    # Will be extracted from existing audio generation service
    return {
        "show_id": request.show_id,
        "file_path": f"/temp/{request.show_id}.mp3",
        "duration": 180,
        "segments": len(request.script.get("segments", []))
    }

@app.get("/voices")
async def get_voices():
    """Get available voices"""
    return [
        {"id": "pNInz6obpgDQGcFmaJgB", "name": "Marcel", "language": "de"},
        {"id": "N2lVS1w4EtoT3dr4eOWO", "name": "Brad", "language": "en"},
        {"id": "XB0fDUnXU5powFXDhCwa", "name": "Lucy", "language": "en"}
    ]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 