"""
RadioX Media Service
Handles media processing, file management, and dashboard generation
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
import redis.asyncio as redis
from typing import Dict, Any, Optional
import os
from loguru import logger
from pydantic import BaseModel

app = FastAPI(
    title="RadioX Media Service",
    description="Media Processing and File Management Service",
    version="1.0.0"
)

# Redis Connection
redis_client: Optional[redis.Redis] = None

@app.on_event("startup")
async def startup_event():
    global redis_client
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    redis_client = redis.from_url(redis_url, decode_responses=True)
    logger.info("Media Service started successfully")

@app.on_event("shutdown")
async def shutdown_event():
    if redis_client:
        await redis_client.close()
    logger.info("Media Service shutdown complete")

class MediaProcessingRequest(BaseModel):
    show_id: str
    audio_file: str
    metadata: Dict[str, Any]

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "media-service"}

@app.post("/process")
async def process_media(request: MediaProcessingRequest):
    """Process media files"""
    # Will be extracted from existing media processing
    return {
        "show_id": request.show_id,
        "final_path": f"/web/{request.show_id}.mp3",
        "web_url": f"https://radiox.com/{request.show_id}.mp3",
        "dashboard_url": f"/dashboard/{request.show_id}"
    }

@app.get("/files")
async def list_media_files():
    """List media files"""
    return {
        "files": [
            {"name": "radiox_250614_0840.mp3", "size": "15MB", "created": "2025-01-14"},
            {"name": "radiox_250613_1515.mp3", "size": "12MB", "created": "2025-01-13"}
        ]
    }

@app.get("/dashboard/{show_id}", response_class=HTMLResponse)
async def get_dashboard(show_id: str):
    """Generate dashboard HTML for show"""
    # Will be extracted from existing dashboard service
    return HTMLResponse(content=f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>RadioX Dashboard - {show_id}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            .header {{ background: #333; color: white; padding: 20px; }}
            .content {{ margin: 20px 0; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>RadioX Show Dashboard</h1>
            <h2>{show_id}</h2>
        </div>
        <div class="content">
            <p>Dashboard wird geladen...</p>
            <p>Show ID: {show_id}</p>
        </div>
    </body>
    </html>
    """)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 