"""
🔹 DATABASE SERVICE - CLEAN ARCHITECTURE DATA ACCESS LAYER
Pure data access layer for all RadioX services
Follows Google Design Principles for Microservices
"""

import asyncio
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
import redis
import httpx
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from loguru import logger

# Direct Supabase imports for this service only
from supabase import create_client, Client

app = FastAPI(
    title="RadioX Database Service",
    description="Pure Data Access Layer - Clean Architecture Foundation",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Redis and Supabase
redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
supabase_client: Optional[Client] = None

# Cache timeouts
CACHE_TIMEOUT_SHORT = 300   # 5 minutes for keys/configuration
CACHE_TIMEOUT_MEDIUM = 600  # 10 minutes for presets/feeds
CACHE_TIMEOUT_LONG = 1800   # 30 minutes for static data

@app.on_event("startup")
async def startup_event():
    """Initialize connections with fail-fast pattern"""
    global supabase_client
    
    logger.info("🚀 Database Service startup - FAIL FAST MODE")
    
    # Test Redis connection
    try:
        redis_client.ping()
        logger.info("✅ Redis connection verified")
    except Exception as e:
        logger.error(f"❌ FAIL FAST: Redis connection failed: {e}")
        raise Exception(f"Database Service REQUIRES Redis connection: {e}")
    
    # Initialize Supabase 
    try:
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_ANON_KEY") 
        
        if not supabase_url or not supabase_key:
            raise Exception("Missing SUPABASE_URL or SUPABASE_ANON_KEY")
            
        supabase_client = create_client(supabase_url, supabase_key)
        
        # Test connection with a simple query
        test_response = supabase_client.table('keys').select('id').limit(1).execute()
        logger.info("✅ Supabase connection verified")
        
    except Exception as e:
        logger.error(f"❌ FAIL FAST: Supabase connection failed: {e}")
        raise Exception(f"Database Service REQUIRES Supabase connection: {e}")
    
    logger.info("✅ Database Service startup complete - DATA ACCESS LAYER READY")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test Redis
        redis_client.ping()
        
        # Test Supabase 
        supabase_client.table('keys').select('id').limit(1).execute()
        
        return {
            "status": "🏥 DATABASE HEALTHY", 
            "timestamp": datetime.now().isoformat(),
            "services": {
                "redis": "connected",
                "supabase": "connected"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database Service unhealthy: {e}")

# ============================================================================
# API KEYS ENDPOINTS
# ============================================================================

@app.get("/api-keys")
async def get_all_api_keys():
    """Get all API keys from database"""
    cache_key = "database:api_keys"
    
    # Check Redis cache first
    cached_data = redis_client.get(cache_key)
    if cached_data:
        logger.info("📦 API keys loaded from cache")
        return json.loads(cached_data)
    
    try:
        logger.info("🔍 Fetching API keys from database")
        response = supabase_client.table('keys').select('name,value,description').execute()
        
        # Cache for 5 minutes
        redis_client.setex(cache_key, CACHE_TIMEOUT_SHORT, json.dumps(response.data))
        logger.info("💾 API keys cached for 5 minutes")
        logger.info(f"✅ Fetched {len(response.data)} API keys from database")
        
        return response.data
        
    except Exception as e:
        logger.error(f"❌ Database query failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch API keys: {e}")

# ============================================================================
# HIERARCHICAL CONFIGURATION ENDPOINTS (Google Design Principles)
# ============================================================================

@app.get("/config/{category}")
async def get_config_category(category: str):
    """Get all configuration for a specific category"""
    cache_key = f"database:config_category:{category}"
    
    # Check Redis cache first
    cached_data = redis_client.get(cache_key)
    if cached_data:
        logger.info(f"📦 Config category '{category}' loaded from cache")
        return json.loads(cached_data)
    
    try:
        logger.info(f"🔍 Fetching config category '{category}' from database")
        response = supabase_client.table('dynamic_config').select('*').eq('config_category', category).eq('is_active', True).execute()
        
        # Transform to key-value structure
        config_data = {}
        for item in response.data:
            key = item['config_key']
            value = item['config_value'] if item['config_value'] else item['config_json']
            config_data[key] = value
        
        # Cache for 5 minutes
        redis_client.setex(cache_key, CACHE_TIMEOUT_SHORT, json.dumps(config_data))
        logger.info(f"💾 Config category '{category}' cached for 5 minutes")
        logger.info(f"✅ Fetched {len(config_data)} config items for category '{category}'")
        
        return config_data
        
    except Exception as e:
        logger.error(f"❌ Database query failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch config category '{category}': {e}")

@app.get("/config/{category}/{key}")
async def get_config_value(category: str, key: str):
    """Get specific configuration value"""
    cache_key = f"database:config_value:{category}:{key}"
    
    # Check Redis cache first
    cached_data = redis_client.get(cache_key)
    if cached_data:
        logger.info(f"📦 Config '{category}.{key}' loaded from cache")
        return json.loads(cached_data)
    
    try:
        logger.info(f"🔍 Fetching config '{category}.{key}' from database")
        response = supabase_client.table('dynamic_config').select('config_value,config_json').eq('config_category', category).eq('config_key', key).eq('is_active', True).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail=f"Configuration '{category}.{key}' not found")
        
        item = response.data[0]
        value = item['config_value'] if item['config_value'] else item['config_json']
        
        result = {"category": category, "key": key, "value": value}
        
        # Cache for 5 minutes
        redis_client.setex(cache_key, CACHE_TIMEOUT_SHORT, json.dumps(result))
        logger.info(f"💾 Config '{category}.{key}' cached for 5 minutes")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Database query failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch config '{category}.{key}': {e}")

@app.get("/config")
async def get_all_config():
    """Get all configuration hierarchically organized"""
    cache_key = "database:all_config"
    
    # Check Redis cache first
    cached_data = redis_client.get(cache_key)
    if cached_data:
        logger.info("📦 All config loaded from cache")
        return json.loads(cached_data)
    
    try:
        logger.info("🔍 Fetching all configuration from database")
        response = supabase_client.table('dynamic_config').select('*').eq('is_active', True).execute()
        
        # Transform to hierarchical structure
        config_data = {}
        for item in response.data:
            category = item['config_category']
            key = item['config_key']
            value = item['config_value'] if item['config_value'] else item['config_json']
            
            if category not in config_data:
                config_data[category] = {}
            
            config_data[category][key] = value
        
        # Cache for 5 minutes
        redis_client.setex(cache_key, CACHE_TIMEOUT_SHORT, json.dumps(config_data))
        logger.info("💾 All config cached for 5 minutes")
        logger.info(f"✅ Fetched hierarchical configuration: {len(config_data)} categories")
        
        return config_data
        
    except Exception as e:
        logger.error(f"❌ Database query failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch all configuration: {e}")

# ============================================================================
# LEGACY ENDPOINTS (maintained for backwards compatibility)
# ============================================================================

@app.get("/system-configuration")
async def get_system_configuration():
    """LEGACY: Get system configuration (now redirects to dynamic_config)"""
    logger.warning("⚠️ DEPRECATED: /system-configuration endpoint used - redirecting to /config")
    return await get_all_config()

# ============================================================================
# EXISTING ENDPOINTS (show-presets, rss-feeds, speakers, shows)
# ============================================================================

@app.get("/show-presets")
async def get_show_presets():
    """Get all active show presets"""
    cache_key = "database:show_presets"
    
    # Check Redis cache first
    cached_data = redis_client.get(cache_key)
    if cached_data:
        logger.info("📦 Show presets loaded from cache")
        return json.loads(cached_data)
    
    try:
        logger.info("🔍 Fetching show presets from database")
        response = supabase_client.table('show_presets').select('*').eq('is_active', True).execute()
        
        # Cache for 10 minutes
        redis_client.setex(cache_key, CACHE_TIMEOUT_MEDIUM, json.dumps(response.data))
        logger.info("💾 Show presets cached for 10 minutes")
        logger.info(f"✅ Fetched {len(response.data)} active show presets")
        
        return response.data
        
    except Exception as e:
        logger.error(f"❌ Database query failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch show presets: {e}")

@app.get("/rss-feeds")
async def get_rss_feeds():
    """Get all active RSS feeds"""
    cache_key = "database:rss_feeds"
    
    # Check Redis cache first
    cached_data = redis_client.get(cache_key)
    if cached_data:
        logger.info("📦 RSS feeds loaded from cache")
        return json.loads(cached_data)
    
    try:
        logger.info("🔍 Fetching RSS feeds from database")
        response = supabase_client.table('rss_feeds').select('source_name,feed_category,feed_url,description').eq('is_active', True).execute()
        
        # Cache for 10 minutes
        redis_client.setex(cache_key, CACHE_TIMEOUT_MEDIUM, json.dumps(response.data))
        logger.info("💾 RSS feeds cached for 10 minutes")
        logger.info(f"✅ Fetched {len(response.data)} RSS feeds from database")
        
        return response.data
        
    except Exception as e:
        logger.error(f"❌ Database query failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch RSS feeds: {e}")

@app.get("/speakers")
async def get_speakers():
    """Get all active voice configurations"""
    try:
        logger.info("🔍 Fetching speakers from database")
        response = supabase_client.table('voice_configurations').select('*').eq('is_active', True).execute()
        
        logger.info(f"✅ Fetched {len(response.data)} active speakers")
        return response.data
        
    except Exception as e:
        logger.error(f"❌ Database query failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch speakers: {e}")

@app.get("/shows")
async def get_shows(limit: int = 10):
    """Get recent shows"""
    try:
        logger.info(f"🔍 Fetching {limit} recent shows from database")
        response = supabase_client.table('shows').select('*').order('created_at', desc=True).limit(limit).execute()
        
        logger.info(f"✅ Fetched {len(response.data)} recent shows")
        return response.data
        
    except Exception as e:
        logger.error(f"❌ Database query failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch shows: {e}")

# ============================================================================
# CACHE MANAGEMENT
# ============================================================================

@app.post("/cache/flush")
async def flush_cache():
    """Flush all Redis cache"""
    try:
        redis_client.flushdb()
        logger.info("🧹 All cache flushed")
        return {"status": "Cache flushed successfully"}
    except Exception as e:
        logger.error(f"❌ Cache flush failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to flush cache: {e}")

@app.post("/cache/flush/{pattern}")
async def flush_cache_pattern(pattern: str):
    """Flush cache by pattern"""
    try:
        keys = redis_client.keys(f"database:{pattern}*")
        if keys:
            redis_client.delete(*keys)
            logger.info(f"🧹 Cache flushed for pattern: {pattern} ({len(keys)} keys)")
        return {"status": f"Cache flushed for pattern: {pattern}", "keys_deleted": len(keys)}
    except Exception as e:
        logger.error(f"❌ Cache flush failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to flush cache pattern: {e}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001) 