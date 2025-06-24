"""
RadioX Content Service
Handles content generation, GPT interactions, and script creation
"""

from fastapi import FastAPI, HTTPException
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
    title="RadioX Content Service",
    description="Content Generation and GPT Service",
    version="1.0.0"
)

# Redis Connection
redis_client: Optional[redis.Redis] = None

@app.on_event("startup")
async def startup_event():
    global redis_client
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    redis_client = redis.from_url(redis_url, decode_responses=True)
    logger.info("Content Service started successfully")

@app.on_event("shutdown")
async def shutdown_event():
    if redis_client:
        await redis_client.close()
    logger.info("Content Service shutdown complete")

# Pydantic Models
class ContentRequest(BaseModel):
    news_count: int = 2
    language: str = "de"
    location: Optional[str] = None

class ScriptRequest(BaseModel):
    preset_name: Optional[str] = None
    primary_speaker: Optional[str] = None
    secondary_speaker: Optional[str] = None
    content: Dict[str, Any]
    config: Dict[str, Any]

class ContentService:
    """Handles content generation and GPT interactions"""
    
    def __init__(self):
        self.openai_client = None
        self.supabase_client = None
    
    async def initialize_clients(self):
        """Initialize external API clients"""
        # Will be extracted from existing services
        pass
    
    async def get_content(self, request: ContentRequest) -> Dict[str, Any]:
        """Get content for show generation"""
        try:
            # Get news content
            news_content = await self._get_news_content(request.news_count)
            
            # Get Bitcoin data
            bitcoin_content = await self._get_bitcoin_content()
            
            # Get weather data if location provided
            weather_content = None
            if request.location:
                weather_content = await self._get_weather_content(request.location)
            
            content = {
                "news": news_content,
                "bitcoin": bitcoin_content,
                "weather": weather_content,
                "timestamp": datetime.now().isoformat()
            }
            
            # Cache content
            if redis_client:
                await redis_client.setex(
                    f"content:{datetime.now().strftime('%Y%m%d_%H%M')}", 
                    1800,  # 30 minutes TTL
                    json.dumps(content)
                )
            
            return content
            
        except Exception as e:
            logger.error(f"Content generation failed: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Content generation failed: {str(e)}")
    
    async def generate_script(self, request: ScriptRequest) -> Dict[str, Any]:
        """Generate radio script using GPT"""
        try:
            # Get speaker configurations
            speakers = await self._get_speaker_configs(
                request.primary_speaker, 
                request.secondary_speaker
            )
            
            # Get show preset
            preset = await self._get_show_preset(request.preset_name)
            
            # Generate script using GPT
            script = await self._generate_gpt_script(
                content=request.content,
                speakers=speakers,
                preset=preset,
                config=request.config
            )
            
            # Store GPT prompts for dashboard
            await self._store_gpt_prompts(script.get("gpt_prompts", []))
            
            return script
            
        except Exception as e:
            logger.error(f"Script generation failed: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Script generation failed: {str(e)}")
    
    async def _get_news_content(self, count: int) -> List[Dict[str, Any]]:
        """Get news content from data sources"""
        # Will be extracted from existing data collection service
        return [
            {
                "title": "Sample News 1",
                "content": "Sample news content 1",
                "source": "Example Source"
            },
            {
                "title": "Sample News 2", 
                "content": "Sample news content 2",
                "source": "Example Source"
            }
        ][:count]
    
    async def _get_bitcoin_content(self) -> Dict[str, Any]:
        """Get Bitcoin analysis content"""
        # Will be extracted from existing bitcoin service
        return {
            "price": 50000,
            "change_24h": 2.5,
            "analysis": "Bitcoin shows positive momentum"
        }
    
    async def _get_weather_content(self, location: str) -> Dict[str, Any]:
        """Get weather content for location"""
        return {
            "location": location,
            "temperature": 20,
            "condition": "sunny",
            "forecast": "Clear skies expected"
        }
    
    async def _get_speaker_configs(self, primary: Optional[str], secondary: Optional[str]) -> Dict[str, Any]:
        """Get speaker configurations"""
        return {
            "primary": {"name": primary or "default", "voice_id": "default"},
            "secondary": {"name": secondary or "default", "voice_id": "default"}
        }
    
    async def _get_show_preset(self, preset_name: Optional[str]) -> Dict[str, Any]:
        """Get show preset configuration"""
        return {
            "name": preset_name,
            "format": "news_talk",
            "duration_target": 180
        }
    
    async def _generate_gpt_script(
        self, 
        content: Dict[str, Any], 
        speakers: Dict[str, Any], 
        preset: Dict[str, Any],
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate script using GPT"""
        # This will be extracted from existing broadcast generation service
        return {
            "segments": [
                {
                    "type": "intro",
                    "speaker": speakers["primary"]["name"],
                    "text": "Welcome to RadioX!",
                    "duration": 10
                },
                {
                    "type": "news",
                    "speaker": speakers["primary"]["name"],
                    "text": f"Today's news: {content['news'][0]['title']}",
                    "duration": 30
                }
            ],
            "total_duration": 180,
            "gpt_prompts": [
                {
                    "stage": "script_generation",
                    "model": "gpt-4",
                    "purpose": "Generate radio script",
                    "prompt": "Generate a radio script...",
                    "response": "Generated script content"
                }
            ]
        }
    
    async def _store_gpt_prompts(self, prompts: List[Dict[str, Any]]):
        """Store GPT prompts for dashboard display"""
        if redis_client:
            await redis_client.setex(
                f"gpt_prompts:{datetime.now().strftime('%Y%m%d_%H%M')}", 
                3600,  # 1 hour TTL
                json.dumps(prompts)
            )

content_service = ContentService()

# Health Check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "content-service"}

# Content Generation
@app.get("/content")
async def get_content(news_count: int = 2, language: str = "de", location: Optional[str] = None):
    """Get content for show generation"""
    request = ContentRequest(
        news_count=news_count,
        language=language,
        location=location
    )
    return await content_service.get_content(request)

@app.post("/script")
async def generate_script(request: ScriptRequest):
    """Generate radio script"""
    return await content_service.generate_script(request)

@app.get("/news")
async def get_news(limit: int = 5):
    """Get latest news"""
    return await content_service._get_news_content(limit)

@app.get("/bitcoin")
async def get_bitcoin_data():
    """Get Bitcoin analysis"""
    return await content_service._get_bitcoin_content()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 