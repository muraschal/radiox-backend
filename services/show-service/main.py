"""
RadioX Show Service
Handles show generation, management, and orchestration
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse
import httpx
import redis.asyncio as redis
import json
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, List
import os
from loguru import logger
from pydantic import BaseModel

# Import shared services (will be extracted from monolith)
import sys
sys.path.append('/app/src')

app = FastAPI(
    title="RadioX Show Service",
    description="Show Generation and Management Service",
    version="1.0.0"
)

# Redis Connection
redis_client: Optional[redis.Redis] = None

@app.on_event("startup")
async def startup_event():
    global redis_client
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    redis_client = redis.from_url(redis_url, decode_responses=True)
    logger.info("Show Service started successfully")

@app.on_event("shutdown")
async def shutdown_event():
    if redis_client:
        await redis_client.close()
    logger.info("Show Service shutdown complete")

# Pydantic Models
class ShowGenerationRequest(BaseModel):
    preset_name: Optional[str] = None
    primary_speaker: Optional[str] = None
    secondary_speaker: Optional[str] = None
    news_count: int = 2
    language: str = "de"
    location: Optional[str] = None

class ShowResponse(BaseModel):
    show_id: str
    status: str
    message: str
    duration: Optional[int] = None
    file_path: Optional[str] = None
    dashboard_url: Optional[str] = None

class ShowOrchestrator:
    """Orchestrates show generation across microservices"""
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=300.0)
    
    async def generate_show(self, request: ShowGenerationRequest) -> ShowResponse:
        """Generate a complete radio show"""
        show_id = f"radiox_{datetime.now().strftime('%y%m%d_%H%M')}"
        
        try:
            logger.info(f"Starting show generation: {show_id}")
            
            # Step 1: Get configuration from Data Service
            config_response = await self.client.get("http://data-service:8000/config")
            config = config_response.json()
            
            # Step 2: Get content from Content Service
            content_response = await self.client.get(
                f"http://content-service:8000/content",
                params={"news_count": request.news_count}
            )
            content = content_response.json()
            
            # Step 3: Generate script from Content Service
            script_response = await self.client.post(
                "http://content-service:8000/script",
                json={
                    "preset_name": request.preset_name,
                    "primary_speaker": request.primary_speaker,
                    "secondary_speaker": request.secondary_speaker,
                    "content": content,
                    "config": config
                }
            )
            script = script_response.json()
            
            # Step 4: Generate audio from Audio Service
            audio_response = await self.client.post(
                "http://audio-service:8000/generate",
                json={
                    "show_id": show_id,
                    "script": script,
                    "speakers": {
                        "primary": request.primary_speaker,
                        "secondary": request.secondary_speaker
                    }
                }
            )
            audio_result = audio_response.json()
            
            # Step 5: Process media from Media Service
            media_response = await self.client.post(
                "http://media-service:8000/process",
                json={
                    "show_id": show_id,
                    "audio_file": audio_result["file_path"],
                    "metadata": {
                        "duration": audio_result["duration"],
                        "preset": request.preset_name,
                        "speakers": [request.primary_speaker, request.secondary_speaker]
                    }
                }
            )
            media_result = media_response.json()
            
            # Step 6: Store analytics
            await self.client.post(
                "http://analytics-service:8000/shows",
                json={
                    "show_id": show_id,
                    "preset": request.preset_name,
                    "duration": audio_result["duration"],
                    "speakers": [request.primary_speaker, request.secondary_speaker],
                    "news_count": request.news_count,
                    "generated_at": datetime.now().isoformat()
                }
            )
            
            # Cache show data in Redis
            show_data = {
                "show_id": show_id,
                "status": "completed",
                "duration": audio_result["duration"],
                "file_path": media_result["final_path"],
                "dashboard_url": f"/dashboard/{show_id}",
                "metadata": {
                    "preset": request.preset_name,
                    "speakers": [request.primary_speaker, request.secondary_speaker],
                    "news_count": request.news_count,
                    "generated_at": datetime.now().isoformat()
                }
            }
            
            if redis_client:
                await redis_client.setex(
                    f"show:{show_id}", 
                    3600,  # 1 hour TTL
                    json.dumps(show_data)
                )
            
            logger.info(f"Show generation completed: {show_id}")
            
            return ShowResponse(
                show_id=show_id,
                status="completed",
                message="Show generated successfully",
                duration=audio_result["duration"],
                file_path=media_result["final_path"],
                dashboard_url=f"/dashboard/{show_id}"
            )
            
        except Exception as e:
            logger.error(f"Show generation failed: {str(e)}")
            
            # Store failed show data
            error_data = {
                "show_id": show_id,
                "status": "failed",
                "error": str(e),
                "generated_at": datetime.now().isoformat()
            }
            
            if redis_client:
                await redis_client.setex(
                    f"show:{show_id}", 
                    3600,
                    json.dumps(error_data)
                )
            
            raise HTTPException(status_code=500, detail=f"Show generation failed: {str(e)}")

orchestrator = ShowOrchestrator()

# Health Check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "show-service"}

# Show Generation
@app.post("/generate", response_model=ShowResponse)
async def generate_show(request: ShowGenerationRequest, background_tasks: BackgroundTasks):
    """Generate a new radio show"""
    return await orchestrator.generate_show(request)

@app.get("/shows/{show_id}")
async def get_show(show_id: str):
    """Get show details"""
    if not redis_client:
        raise HTTPException(status_code=503, detail="Redis not available")
    
    show_data = await redis_client.get(f"show:{show_id}")
    
    if not show_data:
        raise HTTPException(status_code=404, detail="Show not found")
    
    return json.loads(show_data)

@app.get("/shows")
async def list_shows(limit: int = 10, offset: int = 0):
    """List recent shows"""
    if not redis_client:
        raise HTTPException(status_code=503, detail="Redis not available")
    
    # Get show keys from Redis
    keys = await redis_client.keys("show:*")
    keys = sorted(keys, reverse=True)[offset:offset+limit]
    
    shows = []
    for key in keys:
        show_data = await redis_client.get(key)
        if show_data:
            shows.append(json.loads(show_data))
    
    return {"shows": shows, "total": len(keys)}

@app.get("/dashboard/{show_id}", response_class=HTMLResponse)
async def get_dashboard(show_id: str):
    """Get dashboard HTML for show"""
    # Forward to Media Service for dashboard generation
    async with httpx.AsyncClient() as client:
        response = await client.get(f"http://media-service:8000/dashboard/{show_id}")
        return HTMLResponse(content=response.text)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 