"""
RadioX Analytics Service
Handles metrics, performance tracking, and analytics data
"""

from fastapi import FastAPI, HTTPException
import redis.asyncio as redis
from typing import Dict, Any, Optional, List
import os
from datetime import datetime, timedelta
from loguru import logger
from pydantic import BaseModel

app = FastAPI(
    title="RadioX Analytics Service",
    description="Metrics and Performance Tracking Service",
    version="1.0.0"
)

# Redis Connection
redis_client: Optional[redis.Redis] = None

@app.on_event("startup")
async def startup_event():
    global redis_client
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    redis_client = redis.from_url(redis_url, decode_responses=True)
    logger.info("Analytics Service started successfully")

@app.on_event("shutdown")
async def shutdown_event():
    if redis_client:
        await redis_client.close()
    logger.info("Analytics Service shutdown complete")

class ShowAnalytics(BaseModel):
    show_id: str
    preset: Optional[str]
    duration: int
    speakers: List[str]
    news_count: int
    generated_at: str

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "analytics-service"}

@app.post("/shows")
async def store_show_analytics(analytics: ShowAnalytics):
    """Store show analytics data"""
    # Store in Redis for now, will be moved to database
    if redis_client:
        await redis_client.setex(
            f"analytics:show:{analytics.show_id}",
            86400,  # 24 hours TTL
            analytics.json()
        )
    
    return {"message": "Analytics stored successfully"}

@app.get("/shows")
async def get_show_analytics(days: int = 7):
    """Get show analytics for the last N days"""
    # Mock data for now
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    return {
        "period": {
            "start": start_date.isoformat(),
            "end": end_date.isoformat(),
            "days": days
        },
        "summary": {
            "total_shows": 15,
            "total_duration": 2700,  # seconds
            "avg_duration": 180,
            "most_used_preset": "zurich",
            "most_used_speaker": "marcel"
        },
        "shows": [
            {
                "show_id": "radiox_250614_0840",
                "preset": "zurich",
                "duration": 180,
                "speakers": ["marcel"],
                "news_count": 2,
                "generated_at": "2025-01-14T08:40:00"
            },
            {
                "show_id": "radiox_250613_1515",
                "preset": "global",
                "duration": 202,
                "speakers": ["brad", "lucy"],
                "news_count": 2,
                "generated_at": "2025-01-13T15:15:00"
            }
        ]
    }

@app.get("/performance")
async def get_performance_metrics():
    """Get system performance metrics"""
    return {
        "timestamp": datetime.now().isoformat(),
        "services": {
            "api_gateway": {"status": "healthy", "response_time": 45},
            "show_service": {"status": "healthy", "response_time": 120},
            "content_service": {"status": "healthy", "response_time": 80},
            "audio_service": {"status": "healthy", "response_time": 2500},
            "media_service": {"status": "healthy", "response_time": 200}
        },
        "system": {
            "cpu_usage": "15%",
            "memory_usage": "60%",
            "disk_usage": "45%",
            "redis_memory": "120MB"
        },
        "generation_stats": {
            "avg_generation_time": 180,  # seconds
            "success_rate": 98.5,
            "error_rate": 1.5,
            "last_24h_shows": 8
        }
    }

@app.get("/usage")
async def get_usage_statistics():
    """Get usage statistics"""
    return {
        "daily_shows": [
            {"date": "2025-01-14", "count": 3},
            {"date": "2025-01-13", "count": 5},
            {"date": "2025-01-12", "count": 2}
        ],
        "preset_usage": {
            "zurich": 60,
            "global": 40
        },
        "speaker_usage": {
            "marcel": 60,
            "brad": 25,
            "lucy": 15
        },
        "average_metrics": {
            "duration": 185,
            "news_count": 2.2,
            "generation_time": 175
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 