#!/usr/bin/env python3
"""
🧠 DATA SELECTOR SERVICE - INTELLIGENT NEWS CURATION
Port: 8005

PIPELINE POSITION:
Data Collector (8004) → RAW DATA → Data Selector (8005) → CURATED DATA → Show Service (8008)

RESPONSIBILITIES:
1. Fetch raw data from Data Collector Service (news, weather, bitcoin)
2. Use GPT-4 to intelligently select most relevant 3-5 news articles
3. Cache curated data for multiple show generations
4. Provide clean, relevant data to Show Service

DEPENDENCIES:
- Key Service (8002) for OpenAI API key
- Data Collector Service (8004) for raw news data
- Redis for caching curated selections
"""

import os
import asyncio
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import httpx
import redis.asyncio as redis
from fastapi import FastAPI, HTTPException
from loguru import logger

# FastAPI app initialization
app = FastAPI(
    title="RadioX Data Selector Service", 
    version="1.0.0",
    description="🧠 Intelligent News Curation with GPT-4"
)

# Global clients
redis_client: Optional[redis.Redis] = None
openai_api_key: Optional[str] = None

# Service URLs from environment
KEY_SERVICE_URL = os.getenv("KEY_SERVICE_URL", "http://localhost:8002")
DATA_COLLECTOR_SERVICE_URL = os.getenv("DATA_COLLECTOR_SERVICE_URL", "http://localhost:8004")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
DATA_SELECTOR_SERVICE_PORT = int(os.getenv("DATA_SELECTOR_SERVICE_PORT", "8005"))

@app.on_event("startup")
async def startup_event():
    """Service startup with fail-fast dependency validation"""
    global redis_client, openai_api_key
    
    logger.info("🚀 Data Selector Service startup - FAIL FAST MODE")
    
    # 1. Redis connection (REQUIRED for caching curated data)
    try:
        redis_client = redis.from_url(REDIS_URL, decode_responses=True)
        await redis_client.ping()
        logger.info("✅ Redis connection verified")
    except Exception as e:
        logger.error(f"❌ FAIL FAST: Redis connection failed - {e}")
        raise RuntimeError("Redis required for Data Selector Service")
    
    # 2. Key Service dependency validation (REQUIRED for OpenAI key)
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{KEY_SERVICE_URL}/health")
            if response.status_code != 200:
                raise Exception(f"Key Service unhealthy: {response.status_code}")
        logger.info("✅ Key Service connection verified")
    except Exception as e:
        logger.error(f"❌ FAIL FAST: Key Service connection failed - {e}")
        raise RuntimeError("Key Service required for OpenAI API key")
    
    # 3. Data Collector Service dependency validation (REQUIRED for raw data)
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{DATA_COLLECTOR_SERVICE_URL}/health")
            if response.status_code != 200:
                raise Exception(f"Data Collector Service unhealthy: {response.status_code}")
        logger.info("✅ Data Collector Service connection verified")
    except Exception as e:
        logger.error(f"❌ FAIL FAST: Data Collector Service connection failed - {e}")
        raise RuntimeError("Data Collector Service required for raw news data")
    
    # 4. Load OpenAI API key (REQUIRED for GPT-4 curation)
    try:
        openai_api_key = await load_openai_key_from_key_service()
        if not openai_api_key:
            raise Exception("OpenAI API key not available")
        logger.info("✅ OpenAI API key loaded for GPT-4 curation")
    except Exception as e:
        logger.error(f"❌ FAIL FAST: OpenAI API key loading failed - {e}")
        raise RuntimeError("OpenAI API key required for intelligent news curation")
    
    logger.info("✅ Data Selector Service startup complete - INTELLIGENT CURATION READY")

@app.on_event("shutdown")
async def shutdown_event():
    """Service shutdown"""
    global redis_client
    
    if redis_client:
        await redis_client.close()
    logger.info("🛑 Data Selector Service shutdown complete")

async def load_openai_key_from_key_service() -> Optional[str]:
    """Load OpenAI API key from Key Service"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{KEY_SERVICE_URL}/keys/openai_api_key")
            if response.status_code == 200:
                key_data = response.json()
                return key_data.get("key_value")
            return None
    except Exception as e:
        logger.warning(f"⚠️ OpenAI API key loading failed: {e}")
        return None

async def fetch_raw_data_from_collector() -> Dict[str, Any]:
    """Fetch raw news, weather, bitcoin data from Data Collector Service"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Get all raw data from Data Collector
            response = await client.get(f"{DATA_COLLECTOR_SERVICE_URL}/content")
            if response.status_code == 200:
                raw_data = response.json()
                logger.info(f"📡 Fetched raw data: {len(raw_data.get('news', []))} articles, weather, bitcoin")
                return raw_data
            else:
                raise Exception(f"Data Collector returned {response.status_code}")
    except Exception as e:
        logger.error(f"❌ Failed to fetch raw data from Data Collector Service: {e}")
        raise HTTPException(status_code=503, detail="Data Collector Service unavailable")

async def curate_news_with_gpt4(raw_data: Dict[str, Any]) -> Dict[str, Any]:
    """Use GPT-4 to intelligently select most relevant news for Swiss radio"""
    news_articles = raw_data.get("news", [])
    weather_data = raw_data.get("weather", {})
    bitcoin_data = raw_data.get("bitcoin", {})
    
    if not news_articles:
        raise HTTPException(status_code=400, detail="No news articles available for curation")
    
    # Prepare news articles for GPT-4 curation
    news_summaries = []
    for i, article in enumerate(news_articles[:20]):  # Limit to 20 articles for GPT-4
        summary = f"{i+1}. {article.get('title', 'No title')} - {article.get('description', 'No description')[:100]}..."
        news_summaries.append(summary)
    
    # GPT-4 curation prompt
    curation_prompt = f"""Du bist ein erfahrener Schweizer Radio-Redakteur. Analysiere die folgenden {len(news_summaries)} Nachrichten und wähle die 3-5 relevantesten Artikel für eine Schweizer Radio-Sendung aus.

KRITERIEN:
- Relevanz für Schweizer Hörer
- Aktuelle Wichtigkeit
- Ausgewogenheit (lokale + internationale News)
- Interessanter Mix

VERFÜGBARE NACHRICHTEN:
{chr(10).join(news_summaries)}

ANTWORT: Gib nur die Nummern der ausgewählten Artikel zurück, getrennt durch Kommas (z.B. "1,5,8,12,15")"""
    
    try:
        # GPT-4 API call for intelligent curation
        async with httpx.AsyncClient(timeout=30.0) as client:
            headers = {
                "Authorization": f"Bearer {openai_api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "gpt-4",
                "messages": [
                    {"role": "system", "content": "Du bist ein professioneller Schweizer Radio-Redakteur."},
                    {"role": "user", "content": curation_prompt}
                ],
                "max_tokens": 50,
                "temperature": 0.3
            }
            
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload
            )
            
            if response.status_code == 200:
                gpt_response = response.json()
                selected_indices_str = gpt_response["choices"][0]["message"]["content"].strip()
                
                # Parse selected indices
                try:
                    selected_indices = [int(x.strip()) - 1 for x in selected_indices_str.split(",")]  # Convert to 0-based
                    selected_articles = [news_articles[i] for i in selected_indices if 0 <= i < len(news_articles)]
                    
                    logger.info(f"🧠 GPT-4 selected {len(selected_articles)} articles from {len(news_articles)} available")
                    
                    return {
                        "curated_news": selected_articles,
                        "weather": weather_data,
                        "bitcoin": bitcoin_data,
                        "curation_metadata": {
                            "total_articles_analyzed": len(news_articles),
                            "articles_selected": len(selected_articles),
                            "curation_timestamp": datetime.now().isoformat(),
                            "gpt4_selection": selected_indices_str
                        }
                    }
                    
                except (ValueError, IndexError) as e:
                    logger.warning(f"⚠️ GPT-4 selection parsing failed: {e}, using first 3 articles as fallback")
                    # Fallback: select first 3 articles
                    return {
                        "curated_news": news_articles[:3],
                        "weather": weather_data,
                        "bitcoin": bitcoin_data,
                        "curation_metadata": {
                            "total_articles_analyzed": len(news_articles),
                            "articles_selected": 3,
                            "curation_timestamp": datetime.now().isoformat(),
                            "fallback_used": True
                        }
                    }
            else:
                raise Exception(f"OpenAI API returned {response.status_code}")
                
    except Exception as e:
        logger.error(f"❌ GPT-4 curation failed: {e}")
        # Fallback: use first 3 articles without AI curation
        return {
            "curated_news": news_articles[:3],
            "weather": weather_data,
            "bitcoin": bitcoin_data,
            "curation_metadata": {
                "total_articles_analyzed": len(news_articles),
                "articles_selected": 3,
                "curation_timestamp": datetime.now().isoformat(),
                "error_fallback": str(e)
            }
        }

# HEALTH ENDPOINT
@app.get("/health")
async def health_check():
    """Health check with dependency validation"""
    try:
        # Check Key Service dependency
        async with httpx.AsyncClient(timeout=5.0) as client:
            key_service_response = await client.get(f"{KEY_SERVICE_URL}/health")
            key_service_healthy = key_service_response.status_code == 200
        
        # Check Data Collector Service dependency
        async with httpx.AsyncClient(timeout=5.0) as client:
            collector_response = await client.get(f"{DATA_COLLECTOR_SERVICE_URL}/health")
            collector_healthy = collector_response.status_code == 200
            
        # Check Redis
        redis_healthy = await redis_client.ping() if redis_client else False
        
        return {
            "status": "healthy",
            "service": "data-selector-service",
            "port": DATA_SELECTOR_SERVICE_PORT,
            "dependencies": {
                "key_service": key_service_healthy,
                "data_collector_service": collector_healthy,
                "redis": redis_healthy,
                "openai_key_available": bool(openai_api_key)
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Health check failed: {e}")

# CURATED DATA ENDPOINT
@app.get("/curated-data")
async def get_curated_data():
    """Get intelligently curated news data for radio show generation"""
    
    # Check Redis cache first (30 minute cache)
    cache_key = "curated_data"
    if redis_client:
        try:
            cached_data = await redis_client.get(cache_key)
            if cached_data:
                logger.info("📦 Returning cached curated data")
                return json.loads(cached_data)
        except Exception as e:
            logger.warning(f"⚠️ Redis cache read failed: {e}")
    
    # Fetch fresh raw data from Data Collector
    raw_data = await fetch_raw_data_from_collector()
    
    # Curate with GPT-4
    curated_data = await curate_news_with_gpt4(raw_data)
    
    # Cache the curated result (30 minutes)
    if redis_client:
        try:
            await redis_client.setex(cache_key, 1800, json.dumps(curated_data))  # 30 minutes
            logger.info("💾 Curated data cached for 30 minutes")
        except Exception as e:
            logger.warning(f"⚠️ Redis cache write failed: {e}")
    
    return curated_data

# REFRESH CURATION ENDPOINT
@app.post("/refresh-curation")
async def refresh_curation():
    """Force refresh of curated data (clear cache and regenerate)"""
    
    # Clear cache
    if redis_client:
        try:
            await redis_client.delete("curated_data")
            logger.info("🗑️ Curated data cache cleared")
        except Exception as e:
            logger.warning(f"⚠️ Cache clear failed: {e}")
    
    # Generate fresh curated data
    curated_data = await get_curated_data()
    
    return {
        "status": "success",
        "message": "Curation refreshed with fresh GPT-4 analysis",
        "articles_selected": len(curated_data.get("curated_news", [])),
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=DATA_SELECTOR_SERVICE_PORT) 