"""
RadioX Speaker Service
Handles speaker configurations and voice management
"""

from fastapi import FastAPI, HTTPException
import redis.asyncio as redis
from typing import Dict, Any, Optional, List
import os
from loguru import logger

app = FastAPI(
    title="RadioX Speaker Service",
    description="Speaker Configuration and Voice Management Service",
    version="1.0.0"
)

# Redis Connection
redis_client: Optional[redis.Redis] = None

@app.on_event("startup")
async def startup_event():
    global redis_client
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    redis_client = redis.from_url(redis_url, decode_responses=True)
    logger.info("Speaker Service started successfully")

@app.on_event("shutdown")
async def shutdown_event():
    if redis_client:
        await redis_client.close()
    logger.info("Speaker Service shutdown complete")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "speaker-service"}

@app.get("/speakers")
async def get_speakers():
    """Get all speaker configurations"""
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

@app.get("/speakers/{speaker_id}")
async def get_speaker(speaker_id: str):
    """Get specific speaker details"""
    speakers = await get_speakers()
    speaker = next((s for s in speakers if s["id"] == speaker_id), None)
    
    if not speaker:
        raise HTTPException(status_code=404, detail="Speaker not found")
    
    return speaker

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 