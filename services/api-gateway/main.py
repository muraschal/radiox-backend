"""
RadioX API Gateway
Central entry point for all microservices
"""

from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import httpx
import redis.asyncio as redis
import json
import time
from typing import Dict, Any, Optional
import os
from loguru import logger

# Service Configuration
SERVICES = {
    "show": {"url": "http://show-service:8000", "timeout": 300},
    "content": {"url": "http://content-service:8000", "timeout": 60},
    "audio": {"url": "http://audio-service:8000", "timeout": 120},
    "media": {"url": "http://media-service:8000", "timeout": 60},
    "speaker": {"url": "http://speaker-service:8000", "timeout": 30},
    "data": {"url": "http://data-service:8000", "timeout": 30},
    "analytics": {"url": "http://analytics-service:8000", "timeout": 30},
}

app = FastAPI(
    title="RadioX API Gateway",
    description="Central API Gateway for RadioX Microservices",
    version="1.0.0"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Redis Connection
redis_client = None

@app.on_event("startup")
async def startup_event():
    global redis_client
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    redis_client = redis.from_url(redis_url, decode_responses=True)
    logger.info("API Gateway started successfully")

@app.on_event("shutdown")
async def shutdown_event():
    if redis_client:
        await redis_client.close()
    logger.info("API Gateway shutdown complete")

class ServiceProxy:
    """Service proxy for routing requests to microservices"""
    
    def __init__(self):
        self.client = httpx.AsyncClient()
    
    async def forward_request(
        self, 
        service_name: str, 
        path: str, 
        method: str = "GET",
        data: Optional[Dict[Any, Any]] = None,
        params: Optional[Dict[str, str]] = None
    ) -> Dict[Any, Any]:
        """Forward request to appropriate microservice"""
        
        if service_name not in SERVICES:
            raise HTTPException(status_code=404, detail=f"Service {service_name} not found")
        
        service_config = SERVICES[service_name]
        url = f"{service_config['url']}{path}"
        timeout = service_config['timeout']
        
        try:
            # Log request
            logger.info(f"Forwarding {method} {url}")
            
            if method.upper() == "GET":
                response = await self.client.get(url, params=params, timeout=timeout)
            elif method.upper() == "POST":
                response = await self.client.post(url, json=data, params=params, timeout=timeout)
            elif method.upper() == "PUT":
                response = await self.client.put(url, json=data, params=params, timeout=timeout)
            elif method.upper() == "DELETE":
                response = await self.client.delete(url, params=params, timeout=timeout)
            else:
                raise HTTPException(status_code=405, detail="Method not allowed")
            
            response.raise_for_status()
            return response.json()
            
        except httpx.TimeoutException:
            logger.error(f"Timeout calling {service_name} service")
            raise HTTPException(status_code=504, detail=f"Service {service_name} timeout")
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error from {service_name}: {e.response.status_code}")
            raise HTTPException(status_code=e.response.status_code, detail=f"Service error: {e.response.text}")
        except Exception as e:
            logger.error(f"Error calling {service_name} service: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Internal service error")

proxy = ServiceProxy()

# Health Check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": time.time()}

@app.get("/services/status")
async def services_status():
    """Check status of all microservices"""
    status = {}
    
    for service_name, config in SERVICES.items():
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{config['url']}/health", timeout=5)
                status[service_name] = {
                    "status": "healthy" if response.status_code == 200 else "unhealthy",
                    "url": config['url']
                }
        except Exception as e:
            status[service_name] = {
                "status": "unreachable",
                "error": str(e),
                "url": config['url']
            }
    
    return status

# Show Service Routes
@app.post("/api/v1/shows/generate")
async def generate_show(request: Request):
    """Generate a new radio show"""
    data = await request.json()
    return await proxy.forward_request("show", "/generate", "POST", data)

@app.get("/api/v1/shows/{show_id}")
async def get_show(show_id: str):
    """Get show details"""
    return await proxy.forward_request("show", f"/shows/{show_id}", "GET")

@app.get("/api/v1/shows")
async def list_shows(limit: int = 10, offset: int = 0):
    """List shows"""
    params = {"limit": str(limit), "offset": str(offset)}
    return await proxy.forward_request("show", "/shows", "GET", params=params)

# Content Service Routes
@app.get("/api/v1/content/news")
async def get_news(limit: int = 5):
    """Get latest news"""
    params = {"limit": str(limit)}
    return await proxy.forward_request("content", "/news", "GET", params=params)

@app.get("/api/v1/content/bitcoin")
async def get_bitcoin_data():
    """Get Bitcoin analysis"""
    return await proxy.forward_request("content", "/bitcoin", "GET")

# Audio Service Routes
@app.post("/api/v1/audio/generate")
async def generate_audio(request: Request):
    """Generate audio from text"""
    data = await request.json()
    return await proxy.forward_request("audio", "/generate", "POST", data)

@app.get("/api/v1/audio/voices")
async def get_voices():
    """Get available voices"""
    return await proxy.forward_request("audio", "/voices", "GET")

# Media Service Routes
@app.post("/api/v1/media/process")
async def process_media(request: Request):
    """Process media files"""
    data = await request.json()
    return await proxy.forward_request("media", "/process", "POST", data)

@app.get("/api/v1/media/files")
async def list_media_files():
    """List media files"""
    return await proxy.forward_request("media", "/files", "GET")

# Speaker Service Routes
@app.get("/api/v1/speakers")
async def get_speakers():
    """Get available speakers"""
    return await proxy.forward_request("speaker", "/speakers", "GET")

@app.get("/api/v1/speakers/{speaker_id}")
async def get_speaker(speaker_id: str):
    """Get speaker details"""
    return await proxy.forward_request("speaker", f"/speakers/{speaker_id}", "GET")

# Data Service Routes
@app.get("/api/v1/data/presets")
async def get_presets():
    """Get show presets"""
    return await proxy.forward_request("data", "/presets", "GET")

@app.get("/api/v1/data/config")
async def get_config():
    """Get configuration"""
    return await proxy.forward_request("data", "/config", "GET")

# Analytics Service Routes
@app.get("/api/v1/analytics/shows")
async def get_show_analytics():
    """Get show analytics"""
    return await proxy.forward_request("analytics", "/shows", "GET")

@app.get("/api/v1/analytics/performance")
async def get_performance_metrics():
    """Get performance metrics"""
    return await proxy.forward_request("analytics", "/performance", "GET")

# Dashboard Route (Legacy Support)
@app.get("/dashboard/{show_id}")
async def get_dashboard(show_id: str):
    """Get dashboard for show (legacy support)"""
    return await proxy.forward_request("show", f"/dashboard/{show_id}", "GET")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 