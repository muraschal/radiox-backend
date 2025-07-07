"""
RadioX Data Collector Service - PURE FAIL FAST
Collects raw data from RSS feeds, Weather, and Bitcoin APIs
FAIL FAST PRINCIPLE - No fallbacks, dependencies must work
CLEAN ARCHITECTURE - Gets API keys from Key Service
80/20 BEST PRACTICE: Environment config
"""

from fastapi import FastAPI, HTTPException
import httpx
import redis.asyncio as redis
import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import os
import sys
from loguru import logger
from pydantic import BaseModel
import feedparser

# Add parent directory to path for config import
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from config.service_config import config
from config.retry_decorator import retry_async

app = FastAPI(
    title="RadioX Data Collector Service - Fail Fast",
    description="Raw Data Collection Service - RSS, Weather, Bitcoin - NO FALLBACKS",
    version="3.0.0-fail-fast"
)

# Global Services
redis_client: Optional[redis.Redis] = None
api_keys_cache: Dict[str, str] = {}

@app.on_event("startup")
async def startup_event():
    global redis_client, api_keys_cache
    
    logger.info("🚀 Data Collector Service startup - FAIL FAST MODE")
    
    # Initialize Redis - FAIL FAST
    try:
        redis_client = redis.from_url(config.REDIS_URL, decode_responses=True)
        await redis_client.ping()
        logger.info("✅ Redis connection verified")
    except Exception as e:
        logger.error(f"❌ FAIL FAST: Redis connection failed: {e}")
        raise Exception(f"Data Collector Service REQUIRES Redis connection: {e}")
    
    # Test Key Service connection - FAIL FAST (REQUIRED for API keys)
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{config.KEY_SERVICE_URL}/health")
            if response.status_code != 200:
                raise Exception(f"Key Service unhealthy: {response.status_code}")
        logger.info("✅ Key Service connection verified - API keys available")
    except Exception as e:
        logger.error(f"❌ FAIL FAST: Key Service connection failed: {e}")
        raise Exception(f"Data Collector Service REQUIRES Key Service for API keys: {e}")
    
    # Test Database Service connection - FAIL FAST (REQUIRED for RSS feeds)
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{config.DATABASE_URL}/health")
            if response.status_code != 200:
                raise Exception(f"Database Service unhealthy: {response.status_code}")
        logger.info("✅ Database Service connection verified - RSS feeds available")
    except Exception as e:
        logger.error(f"❌ FAIL FAST: Database Service connection failed: {e}")
        raise Exception(f"Data Collector Service REQUIRES Database Service for RSS feeds: {e}")
    
    # Load API keys from Key Service - FAIL FAST
    try:
        api_keys_cache = await load_api_keys_from_key_service()
    except Exception as e:
        logger.error(f"❌ FAIL FAST: API keys loading failed: {e}")
        raise Exception(f"Data Collector Service REQUIRES API keys from Key Service: {e}")
    
    logger.info("✅ Data Collector Service startup complete - ALL DEPENDENCIES VERIFIED")

async def load_api_keys_from_key_service() -> Dict[str, str]:
    """Load API keys from Key Service - FAIL FAST if unavailable"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Get OpenWeather API key
            response = await client.get(f"{config.KEY_SERVICE_URL}/keys/openweather_api_key")
            if response.status_code != 200:
                raise Exception(f"OpenWeather API key not found in Key Service: {response.status_code}")
            openweather_key = response.json().get("key_value")
            
            if not openweather_key:
                raise Exception("OpenWeather API key is empty in Key Service")
            
            logger.info("✅ OpenWeather API key loaded from Key Service")
            
            # Try to get CoinMarketCap key (optional)
            coinmarketcap_key = None
            try:
                response = await client.get(f"{config.KEY_SERVICE_URL}/keys/coinmarketcap_api_key")
                if response.status_code == 200:
                    coinmarketcap_key = response.json().get("key_value")
                    if coinmarketcap_key:
                        logger.info("✅ CoinMarketCap API key loaded from Key Service")
            except:
                logger.info("ℹ️ CoinMarketCap API key not available (optional)")
            
            result = {
                "openweather_api_key": openweather_key
            }
            
            # Only add CoinMarketCap key if it exists
            if coinmarketcap_key:
                result["coinmarketcap_api_key"] = coinmarketcap_key
                
            return result
            
    except Exception as e:
        logger.error(f"❌ Failed to load API keys from Key Service: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    if redis_client:
        await redis_client.close()
    logger.info("Data Collector Service shutdown complete")

# Pydantic Models
class ContentRequest(BaseModel):
    news_count: int = 10  # Just get more, let others filter
    language: str = "de"
    location: Optional[str] = None
    feed_categories: Optional[str] = None  # Comma-separated categories like "zuerich,wetter"

class SimpleRSSCollector:
    """Simple RSS Feed Collector - FAIL FAST ONLY"""
    
    async def get_rss_feeds(self, feed_categories: Optional[str] = None) -> Dict[str, str]:
        """Get RSS feeds from Database Service - optionally filtered by categories"""
        try:
            logger.info("🔍 Fetching RSS feeds from Database Service")
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{config.DATABASE_URL}/rss-feeds")
                
                if response.status_code == 200:
                    feeds_data = response.json()
                    if feeds_data:
                        logger.info(f"✅ Loaded {len(feeds_data)} RSS feeds from Database Service")
                        
                        # Filter by categories if provided
                        if feed_categories:
                            # Split comma-separated categories and strip whitespace
                            target_categories = [cat.strip().lower() for cat in feed_categories.split(',')]
                            
                            # Filter feeds that match any of the target categories
                            filtered_feeds = [
                                feed for feed in feeds_data 
                                if feed.get('feed_category', '').lower() in target_categories
                            ]
                            
                            logger.info(f"📝 Filtered to {len(filtered_feeds)} feeds matching categories: {target_categories}")
                            feeds_data = filtered_feeds
                        
                        # Convert to dict format expected by collect_all_news
                        return {feed['source_name']: feed['feed_url'] for feed in feeds_data}
                    else:
                        raise Exception("Database Service returned empty RSS feeds")
                else:
                    raise Exception(f"Database Service RSS feeds endpoint failed: {response.status_code}")
        except Exception as e:
            logger.error(f"❌ FAIL FAST: RSS feeds lookup failed: {e}")
            raise HTTPException(
                status_code=503,
                detail=f"Data Collector Service: Database Service connection required for RSS feeds: {e}"
            )
    
    async def collect_all_news(self, hours_back: int = 24, feed_categories: Optional[str] = None) -> List[Dict[str, Any]]:
        """Collect news from RSS feeds - optionally filtered by categories - FAIL FAST if Database Service unavailable"""
        try:
            # Check Redis cache first - include categories in cache key
            cache_key = f"news_articles_{hours_back}h"
            if feed_categories:
                # Include categories in cache key for category-specific caching
                categories_hash = "_".join(sorted(feed_categories.split(',')))
                cache_key = f"news_articles_{hours_back}h_{categories_hash}"
                
            if redis_client:
                cached_news = await redis_client.get(cache_key)
                if cached_news:
                    import json
                    cached_data = json.loads(cached_news)
                    logger.info(f"📦 {len(cached_data)} news articles loaded from cache ({hours_back}h, categories: {feed_categories or 'all'})")
                    return cached_data
            
            # FAIL FAST - no fallbacks
            feeds = await self.get_rss_feeds(feed_categories)
            all_news = []
            
            if feed_categories:
                logger.info(f"🔄 Collecting fresh news from {len(feeds)} RSS feeds (filtered by: {feed_categories})...")
            else:
                logger.info(f"🔄 Collecting fresh news from {len(feeds)} RSS feeds...")
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                for source, feed_url in feeds.items():
                    try:
                        logger.info(f"📰 Fetching RSS from {source}...")
                        
                        # Use retry logic for unstable RSS feeds (80/20 Best Practice)
                        @retry_async(max_attempts=3, delay=1.0, backoff=2.0)
                        async def fetch_rss_with_retry():
                            response = await client.get(feed_url)
                            if response.status_code != 200:
                                raise Exception(f"RSS {source} returned {response.status_code}")
                            return response
                        
                        response = await fetch_rss_with_retry()
                        news_items = self._parse_rss_simple(response.text, source)
                        all_news.extend(news_items)
                        logger.info(f"✅ {len(news_items)} articles from {source}")
                        
                    except Exception as e:
                        logger.error(f"❌ Error fetching RSS from {source} after retries: {str(e)}")
                        continue
            
            # Only filter by time - NO OTHER LOGIC
            cutoff_time = datetime.now() - timedelta(hours=hours_back)
            recent_news = [
                item for item in all_news 
                if item.get('timestamp', datetime.min) > cutoff_time
            ]
            
            # Cache the results for 10 minutes - news don't change very often
            if redis_client:
                import json
                await redis_client.setex(cache_key, 600, json.dumps(recent_news, default=str))
                logger.info(f"💾 {len(recent_news)} news articles cached for 10 minutes")
            
            if feed_categories:
                logger.info(f"📰 Collected {len(recent_news)} recent articles (filtered by: {feed_categories})")
            else:
                logger.info(f"📰 Collected {len(recent_news)} recent articles")
            return recent_news
            
        except HTTPException:
            # Re-raise HTTP exceptions (like Data Service failure)
            raise
        except Exception as e:
            logger.error(f"❌ RSS collection failed: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Data Collector Service: RSS collection failed: {e}"
            )
    
    def _parse_rss_simple(self, rss_content: str, source: str) -> List[Dict[str, Any]]:
        """Parse RSS feed content - MINIMAL PROCESSING"""
        try:
            feed = feedparser.parse(rss_content)
            news_items = []
            
            for entry in feed.entries:
                try:
                    # Parse published time
                    timestamp = datetime.now()
                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                        timestamp = datetime(*entry.published_parsed[:6])
                    
                    # Extract raw content - NO CATEGORIZATION
                    news_item = {
                        'title': entry.get('title', ''),
                        'summary': entry.get('summary', ''),
                        'link': entry.get('link', ''),
                        'source': source,
                        'timestamp': timestamp,
                        'raw_entry': {
                            'published': entry.get('published', ''),
                            'author': entry.get('author', ''),
                            'tags': [tag.get('term', '') for tag in entry.get('tags', [])]
                        }
                    }
                    
                    news_items.append(news_item)
                    
                except Exception as e:
                    logger.warning(f"⚠️ Error parsing RSS entry from {source}: {str(e)}")
                    continue
            
            return news_items
            
        except Exception as e:
            logger.error(f"❌ RSS parsing failed for {source}: {str(e)}")
            return []

class SimpleWeatherCollector:
    """Simple Weather Data Collector - FAIL FAST ONLY"""
    
    def __init__(self):
        self.base_url = "https://api.openweathermap.org/data/2.5/weather"
    
    async def collect_weather(self, location: str = "Zurich") -> Dict[str, Any]:
        """Collect raw weather data - FAIL FAST if API key missing"""
        try:
            # Check Redis cache first - weather doesn't change often
            cache_key = f"weather_{location.lower()}"
            if redis_client:
                cached_weather = await redis_client.get(cache_key)
                if cached_weather:
                    import json
                    cached_data = json.loads(cached_weather)
                    logger.info(f"📦 Weather data for {location} loaded from cache")
                    return cached_data
            
            # FAIL FAST - get API key from Key Service cache
            api_key = api_keys_cache.get("openweather_api_key")
            
            if not api_key:
                raise HTTPException(
                    status_code=503,
                    detail="Data Collector Service: OpenWeather API key not available from Key Service"
                )

            params = {
                "q": location,
                "appid": api_key,
                "units": "metric",
                "lang": "de"
            }
            
            logger.info(f"🌤️ Fetching fresh weather data for {location}...")
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(self.base_url, params=params)
                
                if response.status_code == 200:
                    raw_data = response.json()
                    # Return raw data with minimal formatting
                    weather_data = {
                        "raw_data": raw_data,
                        "location": location,
                        "temperature": raw_data.get("main", {}).get("temp"),
                        "description": raw_data.get("weather", [{}])[0].get("description"),
                        "humidity": raw_data.get("main", {}).get("humidity"),
                        "status": "success",
                        "api_key_source": "key_service",
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    # Cache for 5 minutes - weather changes moderately
                    if redis_client:
                        import json
                        await redis_client.setex(cache_key, 300, json.dumps(weather_data))
                        logger.info(f"💾 Weather data for {location} cached for 5 minutes")
                    
                    return weather_data
                elif response.status_code == 401:
                    raise HTTPException(
                        status_code=503,
                        detail="Data Collector Service: Invalid OpenWeather API key from Key Service"
                    )
                else:
                    raise HTTPException(
                        status_code=503,
                        detail=f"Data Collector Service: Weather API error {response.status_code}"
                    )
                    
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ Weather collection error: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Data Collector Service: Weather collection failed: {e}"
            )

class SimpleBitcoinCollector:
    """Simple Bitcoin Data Collector - FAIL FAST ONLY"""
    
    def __init__(self):
        self.base_url = "https://api.coingecko.com/api/v3/simple/price"
    
    async def collect_bitcoin(self) -> Dict[str, Any]:
        """Collect raw Bitcoin data - FAIL FAST if API unavailable"""
        try:
            # Check Redis cache first - crypto prices change frequently, short cache
            cache_key = "bitcoin_data"
            if redis_client:
                cached_bitcoin = await redis_client.get(cache_key)
                if cached_bitcoin:
                    import json
                    cached_data = json.loads(cached_bitcoin)
                    logger.info("📦 Bitcoin data loaded from cache")
                    return cached_data
            
            params = {
                "ids": "bitcoin",
                "vs_currencies": "usd,eur,chf",
                "include_24hr_change": "true",
                "include_market_cap": "true",
                "include_24hr_vol": "true"
            }
            
            # CoinGecko API key is optional (they have free tier)
            coinmarketcap_key = api_keys_cache.get("coinmarketcap_api_key")
            if coinmarketcap_key:
                # If we have CoinMarketCap key, use that instead
                logger.info("Using CoinMarketCap API (premium)")
                # TODO: Implement CoinMarketCap if needed
            
            logger.info("💰 Fetching fresh Bitcoin data...")
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(self.base_url, params=params)
                
                if response.status_code == 200:
                    raw_data = response.json()
                    bitcoin_data_raw = raw_data.get("bitcoin", {})
                    
                    # Return raw data with minimal processing
                    bitcoin_data = {
                        "raw_data": raw_data,
                        "price_usd": bitcoin_data_raw.get("usd"),
                        "price_eur": bitcoin_data_raw.get("eur"),
                        "price_chf": bitcoin_data_raw.get("chf"),
                        "change_24h": bitcoin_data_raw.get("usd_24h_change"),
                        "market_cap": bitcoin_data_raw.get("usd_market_cap"),
                        "volume_24h": bitcoin_data_raw.get("usd_24h_vol"),
                        "status": "success",
                        "api_source": "coingecko_free",
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    # Cache for 1 minute - crypto prices change frequently
                    if redis_client:
                        import json
                        await redis_client.setex(cache_key, 60, json.dumps(bitcoin_data))
                        logger.info("💾 Bitcoin data cached for 1 minute")
                    
                    return bitcoin_data
                else:
                    raise HTTPException(
                        status_code=503,
                        detail=f"Data Collector Service: Bitcoin API error {response.status_code}"
                    )
                    
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ Bitcoin collection error: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Data Collector Service: Bitcoin collection failed: {e}"
            )

class PureDataCollector:
    """Pure Data Collector - FAIL FAST ONLY"""
    
    def __init__(self):
        self.rss_collector = SimpleRSSCollector()
        self.weather_collector = SimpleWeatherCollector()
        self.bitcoin_collector = SimpleBitcoinCollector()
    
    async def collect_all_content(self, request: ContentRequest) -> Dict[str, Any]:
        """Collect all raw content - FAIL FAST if any critical dependency fails"""
        try:
            logger.info(f"📊 Collecting raw content for: {request.location or 'default'}")
            
            # Parallel collection - FAIL FAST on critical errors
            news_task = self.rss_collector.collect_all_news(24, request.feed_categories)
            weather_task = self.weather_collector.collect_weather(request.location or "Zurich")
            bitcoin_task = self.bitcoin_collector.collect_bitcoin()
            
            # Wait for all tasks
            news, weather, bitcoin = await asyncio.gather(
                news_task, weather_task, bitcoin_task,
                return_exceptions=True
            )
            
            # Handle exceptions - FAIL FAST for critical dependencies
            if isinstance(news, HTTPException):
                # RSS feeds are critical - fail fast
                raise news
            elif isinstance(news, Exception):
                raise HTTPException(status_code=500, detail=f"News collection failed: {news}")
                
            if isinstance(weather, HTTPException):
                # Weather API issues should fail fast
                raise weather
            elif isinstance(weather, Exception):
                raise HTTPException(status_code=500, detail=f"Weather collection failed: {weather}")
                
            if isinstance(bitcoin, HTTPException):
                # Bitcoin API issues should fail fast
                raise bitcoin
            elif isinstance(bitcoin, Exception):
                raise HTTPException(status_code=500, detail=f"Bitcoin collection failed: {bitcoin}")
            
            return {
                "news": news,
                "weather": weather,
                "bitcoin": bitcoin,
                "collection_info": {
                    "total_news_collected": len(news) if isinstance(news, list) else 0,
                    "requested_location": request.location,
                    "language": request.language,
                    "collected_at": datetime.now().isoformat(),
                    "collector_version": "3.0.0-fail-fast",
                    "fail_fast_enabled": True,
                    "api_keys_source": "key_service"
                }
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ Content collection failed: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Data Collector Service: Content collection failed: {str(e)}")

# Initialize collector
data_collector = PureDataCollector()

# API Endpoints - FAIL FAST
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "data-collector-service",
        "version": "3.0.0-fail-fast",
        "description": "Pure Data Collector - FAIL FAST PRINCIPLE",
        "dependencies": ["Key Service", "Database Service", "Redis"],
        "api_keys_loaded": list(api_keys_cache.keys()),
        "fail_fast_enabled": True,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/content")
async def get_content(
    news_count: int = 10, 
    language: str = "de", 
    location: Optional[str] = None,
    feed_categories: Optional[str] = None
):
    """Get raw content - FAIL FAST if dependencies unavailable
    
    Args:
        feed_categories: Comma-separated list of categories (e.g., "zuerich,wetter")
    """
    request = ContentRequest(
        news_count=news_count, 
        language=language, 
        location=location,
        feed_categories=feed_categories
    )
    return await data_collector.collect_all_content(request)

@app.get("/news")
async def get_news_only(hours_back: int = 24, feed_categories: Optional[str] = None):
    """Get raw news only - optionally filtered by categories - FAIL FAST if Data Service unavailable"""
    news = await data_collector.rss_collector.collect_all_news(hours_back, feed_categories)
    return {
        "news": news, 
        "total_collected": len(news),
        "hours_back": hours_back,
        "filtered_by_categories": feed_categories,
        "collected_at": datetime.now().isoformat(),
        "fail_fast_enabled": True
    }

@app.get("/weather")
async def get_weather_only(location: str = "Zurich"):
    """Get raw weather only - FAIL FAST if API key missing"""
    return await data_collector.weather_collector.collect_weather(location)

@app.get("/bitcoin")
async def get_bitcoin_only():
    """Get raw Bitcoin data only - FAIL FAST if API unavailable"""
    return await data_collector.bitcoin_collector.collect_bitcoin()

@app.get("/feeds")
async def get_rss_feeds(feed_categories: Optional[str] = None):
    """Get configured RSS feeds - optionally filtered by categories - FAIL FAST if Database Service unavailable"""
    feeds = await data_collector.rss_collector.get_rss_feeds(feed_categories)
    
    return {
        "feeds": feeds,
        "total_feeds": len(feeds),
        "filtered_by_categories": feed_categories,
        "description": "RSS feed URLs from Database Service (with optional category filtering)",
        "fail_fast_enabled": True
    }

@app.get("/api-keys")
async def get_api_keys_status():
    """Get API keys status - for debugging"""
    return {
        "api_keys_loaded": list(api_keys_cache.keys()),
        "key_service_url": os.getenv("KEY_SERVICE_URL", "http://localhost:8002"),
        "keys_source": "key_service",
        "fail_fast_enabled": True
    }

@app.post("/cache/refresh/news")
async def refresh_news_cache():
    """Refresh news cache - clear all cached news articles"""
    try:
        if redis_client:
            # Clear all news caches (different hours_back values)
            keys_to_delete = []
            async for key in redis_client.scan_iter(match="news_articles_*"):
                keys_to_delete.append(key)
            
            if keys_to_delete:
                await redis_client.delete(*keys_to_delete)
                logger.info(f"🔄 Cleared {len(keys_to_delete)} news cache entries")
            else:
                logger.info("🔄 No news cache entries to clear")
            
            return {"success": True, "message": f"News cache refreshed ({len(keys_to_delete)} entries cleared)"}
        else:
            return {"success": False, "message": "Redis not available"}
    except Exception as e:
        logger.error(f"❌ Failed to refresh news cache: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to refresh news cache: {str(e)}")

@app.post("/cache/refresh/weather")
async def refresh_weather_cache():
    """Refresh weather cache - clear all cached weather data"""
    try:
        if redis_client:
            # Clear all weather caches (different locations)
            keys_to_delete = []
            async for key in redis_client.scan_iter(match="weather_*"):
                keys_to_delete.append(key)
            
            if keys_to_delete:
                await redis_client.delete(*keys_to_delete)
                logger.info(f"🔄 Cleared {len(keys_to_delete)} weather cache entries")
            else:
                logger.info("🔄 No weather cache entries to clear")
            
            return {"success": True, "message": f"Weather cache refreshed ({len(keys_to_delete)} entries cleared)"}
        else:
            return {"success": False, "message": "Redis not available"}
    except Exception as e:
        logger.error(f"❌ Failed to refresh weather cache: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to refresh weather cache: {str(e)}")

@app.post("/cache/refresh/bitcoin")
async def refresh_bitcoin_cache():
    """Refresh bitcoin cache - clear cached bitcoin data"""
    try:
        if redis_client:
            deleted = await redis_client.delete("bitcoin_data")
            if deleted:
                logger.info("🔄 Bitcoin cache cleared")
                return {"success": True, "message": "Bitcoin cache refreshed"}
            else:
                logger.info("🔄 No bitcoin cache to clear")
                return {"success": True, "message": "No bitcoin cache to clear"}
        else:
            return {"success": False, "message": "Redis not available"}
    except Exception as e:
        logger.error(f"❌ Failed to refresh bitcoin cache: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to refresh bitcoin cache: {str(e)}")

@app.post("/cache/refresh/all")
async def refresh_all_cache():
    """Refresh all caches - clear news, weather, and bitcoin data"""
    try:
        if redis_client:
            # Clear all Data Collector Service caches
            patterns = ["news_articles_*", "weather_*", "bitcoin_data"]
            total_deleted = 0
            
            for pattern in patterns:
                keys_to_delete = []
                async for key in redis_client.scan_iter(match=pattern):
                    keys_to_delete.append(key)
                
                if keys_to_delete:
                    await redis_client.delete(*keys_to_delete)
                    total_deleted += len(keys_to_delete)
            
            logger.info(f"🔄 Cleared {total_deleted} total cache entries")
            return {"success": True, "message": f"All caches refreshed ({total_deleted} entries cleared)"}
        else:
            return {"success": False, "message": "Redis not available"}
    except Exception as e:
        logger.error(f"❌ Failed to refresh all caches: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to refresh all caches: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004) 