"""
RadioX Content Service
Handles content generation, GPT interactions, and script creation
REAL IMPLEMENTATION with RSS, Weather, Bitcoin data collection
"""

from fastapi import FastAPI, HTTPException
import httpx
import redis.asyncio as redis
import json
import asyncio
from datetime import datetime, timedelta
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

class RSSService:
    """RSS News Collection Service"""
    
    def __init__(self):
        self.feeds = {
            "nzz": "https://www.nzz.ch/recent.rss",
            "20min": "https://www.20min.ch/rss/rss.tmpl",
            "srf": "https://www.srf.ch/news/bnf/rss/1646",
            "tagesanzeiger": "https://www.tagesanzeiger.ch/rss.html",
            "cash": "https://www.cash.ch/rss/news",
            "heise": "https://www.heise.de/rss/heise-atom.xml",
            "cointelegraph": "https://cointelegraph.com/rss",
            "techcrunch": "https://techcrunch.com/feed/",
            "theverge": "https://www.theverge.com/rss/index.xml",
            "rt": "https://www.rt.com/rss/",
            "bbc": "http://feeds.bbci.co.uk/news/world/rss.xml"
        }
    
    async def get_all_recent_news(self, hours_back: int = 24) -> List[Dict[str, Any]]:
        """Get recent news from all RSS feeds"""
        try:
            all_news = []
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                for source, feed_url in self.feeds.items():
                    try:
                        logger.info(f"📰 Fetching RSS from {source}...")
                        response = await client.get(feed_url)
                        
                        if response.status_code == 200:
                            news_items = await self._parse_rss_feed(response.text, source)
                            all_news.extend(news_items)
                            logger.info(f"✅ {len(news_items)} articles from {source}")
                        else:
                            logger.warning(f"⚠️ RSS {source} returned {response.status_code}")
                            
                    except Exception as e:
                        logger.error(f"❌ Error fetching RSS from {source}: {str(e)}")
                        continue
            
            # Filter by time
            cutoff_time = datetime.now() - timedelta(hours=hours_back)
            recent_news = [
                item for item in all_news 
                if item.get('timestamp', datetime.min) > cutoff_time
            ]
            
            # Sort by priority and time
            recent_news.sort(key=lambda x: (x.get('priority', 5), x.get('timestamp', datetime.min)), reverse=True)
            
            logger.info(f"📰 Total recent news: {len(recent_news)} articles")
            return recent_news
            
        except Exception as e:
            logger.error(f"❌ RSS collection failed: {str(e)}")
            return []
    
    async def _parse_rss_feed(self, rss_content: str, source: str) -> List[Dict[str, Any]]:
        """Parse RSS feed content"""
        try:
            import feedparser
            
            feed = feedparser.parse(rss_content)
            news_items = []
            
            for entry in feed.entries:
                try:
                    # Parse published time
                    timestamp = datetime.now()
                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                        timestamp = datetime(*entry.published_parsed[:6])
                    
                    # Extract content
                    title = entry.get('title', '')
                    summary = entry.get('summary', '')
                    link = entry.get('link', '')
                    
                    # Determine category and priority
                    category = self._categorize_article(title, summary)
                    priority = self._calculate_priority(title, summary, category)
                    
                    news_item = {
                        'title': title,
                        'summary': summary,
                        'link': link,
                        'source': source,
                        'category': category,
                        'priority': priority,
                        'timestamp': timestamp,
                        'age_hours': (datetime.now() - timestamp).total_seconds() / 3600,
                        'has_link': bool(link)
                    }
                    
                    news_items.append(news_item)
                    
                except Exception as e:
                    logger.warning(f"⚠️ Error parsing RSS entry from {source}: {str(e)}")
                    continue
            
            return news_items
            
        except Exception as e:
            logger.error(f"❌ RSS parsing failed for {source}: {str(e)}")
            return []
    
    def _categorize_article(self, title: str, summary: str) -> str:
        """Categorize article based on content"""
        text = (title + " " + summary).lower()
        
        if any(word in text for word in ['bitcoin', 'crypto', 'blockchain', 'ethereum']):
            return 'bitcoin'
        elif any(word in text for word in ['zürich', 'zurich', 'schweiz', 'swiss']):
            return 'zurich'
        elif any(word in text for word in ['tech', 'ai', 'software', 'internet', 'digital']):
            return 'tech'
        elif any(word in text for word in ['wirtschaft', 'economy', 'market', 'finance']):
            return 'wirtschaft'
        elif any(word in text for word in ['politik', 'politics', 'government']):
            return 'politik'
        else:
            return 'news'
    
    def _calculate_priority(self, title: str, summary: str, category: str) -> int:
        """Calculate article priority (1-10, 10 = highest)"""
        text = (title + " " + summary).lower()
        
        # High priority keywords
        if any(word in text for word in ['breaking', 'urgent', 'crisis', 'emergency']):
            return 10
        elif any(word in text for word in ['bitcoin', 'crypto', 'blockchain']):
            return 8
        elif any(word in text for word in ['zürich', 'zurich']):
            return 7
        elif category in ['tech', 'wirtschaft']:
            return 6
        else:
            return 5

class WeatherService:
    """Weather Data Service"""
    
    def __init__(self):
        self.api_key = None
        self.base_url = "http://api.openweathermap.org/data/2.5"
    
    async def _get_api_key(self) -> Optional[str]:
        """Get Weather API key from Data Service"""
        if self.api_key:
            return self.api_key
        
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get("http://data-service:8000/config")
                if response.status_code == 200:
                    config = response.json()
                    self.api_key = config.get("api_keys", {}).get("weather")
                    return self.api_key
        except Exception as e:
            logger.warning(f"⚠️ Failed to get API key from Data Service: {str(e)}")
        
        return None
    
    async def get_current_weather(self, location: str = "Zurich") -> Dict[str, Any]:
        """Get current weather data"""
        api_key = await self._get_api_key()
        if not api_key:
            logger.warning("⚠️ Weather API key not configured")
            return self._get_mock_weather()
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                url = f"{self.base_url}/weather"
                params = {
                    "q": location,
                    "appid": api_key,
                    "units": "metric",
                    "lang": "de"
                }
                
                response = await client.get(url, params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    return self._format_weather_data(data, location)
                else:
                    logger.warning(f"⚠️ Weather API returned {response.status_code}")
                    return self._get_mock_weather()
                    
        except Exception as e:
            logger.error(f"❌ Weather API error: {str(e)}")
            return self._get_mock_weather()
    
    def _format_weather_data(self, data: Dict[str, Any], location: str) -> Dict[str, Any]:
        """Format weather API response"""
        return {
            "location": location,
            "current": {
                "temperature": round(data["main"]["temp"]),
                "description": data["weather"][0]["description"],
                "humidity": data["main"]["humidity"],
                "wind_speed": round(data["wind"]["speed"] * 3.6)  # m/s to km/h
            },
            "timestamp": datetime.now().isoformat()
        }
    
    def _get_mock_weather(self) -> Dict[str, Any]:
        """Mock weather data when API unavailable"""
        return {
            "location": "Zürich",
            "current": {
                "temperature": 18,
                "description": "teilweise bewölkt",
                "humidity": 65,
                "wind_speed": 12
            },
            "timestamp": datetime.now().isoformat()
        }

class BitcoinService:
    """Bitcoin Price and Analysis Service"""
    
    def __init__(self):
        self.api_key = None
        self.base_url = "https://pro-api.coinmarketcap.com/v1"
    
    async def _get_api_key(self) -> Optional[str]:
        """Get CoinMarketCap API key from Data Service"""
        if self.api_key:
            return self.api_key
        
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get("http://data-service:8000/config")
                if response.status_code == 200:
                    config = response.json()
                    self.api_key = config.get("api_keys", {}).get("coinmarketcap")
                    return self.api_key
        except Exception as e:
            logger.warning(f"⚠️ Failed to get Bitcoin API key from Data Service: {str(e)}")
        
        return None
    
    async def get_bitcoin_data(self) -> Dict[str, Any]:
        """Get Bitcoin price and analysis"""
        api_key = await self._get_api_key()
        if not api_key:
            logger.warning("⚠️ CoinMarketCap API key not configured")
            return self._get_mock_bitcoin()
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                headers = {
                    "X-CMC_PRO_API_KEY": api_key,
                    "Accept": "application/json"
                }
                
                url = f"{self.base_url}/cryptocurrency/quotes/latest"
                params = {
                    "symbol": "BTC",
                    "convert": "USD"
                }
                
                response = await client.get(url, headers=headers, params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    return self._format_bitcoin_data(data)
                else:
                    logger.warning(f"⚠️ Bitcoin API returned {response.status_code}")
                    return self._get_mock_bitcoin()
                    
        except Exception as e:
            logger.error(f"❌ Bitcoin API error: {str(e)}")
            return self._get_mock_bitcoin()
    
    def _format_bitcoin_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Format Bitcoin API response"""
        btc_data = data["data"]["BTC"]["quote"]["USD"]
        
        return {
            "price": round(btc_data["price"], 2),
            "change_24h": round(btc_data["percent_change_24h"], 2),
            "market_cap": btc_data["market_cap"],
            "volume_24h": btc_data["volume_24h"],
            "analysis": self._generate_bitcoin_analysis(btc_data),
            "timestamp": datetime.now().isoformat()
        }
    
    def _generate_bitcoin_analysis(self, data: Dict[str, Any]) -> str:
        """Generate Bitcoin analysis text"""
        change = data["percent_change_24h"]
        
        if change > 5:
            return f"Bitcoin zeigt starkes Wachstum mit +{change:.1f}% in 24h"
        elif change > 2:
            return f"Bitcoin steigt moderat um {change:.1f}% heute"
        elif change > -2:
            return f"Bitcoin bewegt sich seitwärts mit {change:.1f}% Veränderung"
        elif change > -5:
            return f"Bitcoin korrigiert leicht um {change:.1f}% heute"
        else:
            return f"Bitcoin unter Druck mit {change:.1f}% Verlust in 24h"
    
    def _get_mock_bitcoin(self) -> Dict[str, Any]:
        """Mock Bitcoin data when API unavailable"""
        return {
            "price": 45000.00,
            "change_24h": 2.5,
            "market_cap": 850000000000,
            "volume_24h": 25000000000,
            "analysis": "Bitcoin zeigt moderate Aufwärtsbewegung",
            "timestamp": datetime.now().isoformat()
        }

class ContentService:
    """Handles content generation and GPT interactions"""
    
    def __init__(self):
        self.rss_service = RSSService()
        self.weather_service = WeatherService()
        self.bitcoin_service = BitcoinService()
    
    async def get_content(self, request: ContentRequest) -> Dict[str, Any]:
        """Get content for show generation - REAL IMPLEMENTATION"""
        try:
            logger.info("🚀 Starting real content collection...")
            
            # Collect all data in parallel
            news_task = self.rss_service.get_all_recent_news(24)
            weather_task = self.weather_service.get_current_weather(request.location or "Zurich")
            bitcoin_task = self.bitcoin_service.get_bitcoin_data()
            
            news, weather, bitcoin = await asyncio.gather(
                news_task, weather_task, bitcoin_task,
                return_exceptions=True
            )
            
            # Handle exceptions and ensure proper types
            if isinstance(news, Exception):
                logger.error(f"News collection failed: {str(news)}")
                news_list = []
            else:
                news_list = news
            
            if isinstance(weather, Exception):
                logger.error(f"Weather collection failed: {str(weather)}")
                weather_data = None
            else:
                weather_data = weather
            
            if isinstance(bitcoin, Exception):
                logger.error(f"Bitcoin collection failed: {str(bitcoin)}")
                bitcoin_data = None
            else:
                bitcoin_data = bitcoin
            
            # Select top news based on request
            selected_news = self._select_top_news(news_list, request.news_count, request.language)
            
            content = {
                "news": selected_news,
                "weather": weather_data,
                "bitcoin": bitcoin_data,
                "collection_stats": {
                    "total_news_collected": len(news_list),
                    "news_selected": len(selected_news),
                    "sources": list(set(item['source'] for item in news_list)) if news_list else [],
                    "categories": list(set(item['category'] for item in news_list)) if news_list else []
                },
                "timestamp": datetime.now().isoformat()
            }
            
            # Cache content
            if redis_client:
                await redis_client.setex(
                    f"content:{datetime.now().strftime('%Y%m%d_%H%M')}", 
                    1800,  # 30 minutes TTL
                    json.dumps(content, default=str)
                )
            
            logger.info(f"✅ Content collected: {len(selected_news)} news, weather: {'✓' if weather_data else '✗'}, bitcoin: {'✓' if bitcoin_data else '✗'}")
            return content
            
        except Exception as e:
            logger.error(f"Content generation failed: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Content generation failed: {str(e)}")
    
    def _select_top_news(self, news: List[Dict[str, Any]], count: int, language: str) -> List[Dict[str, Any]]:
        """Select top news based on priority and relevance"""
        if not news:
            return []
        
        # Filter by language preference (for Zurich shows prefer local news)
        if language == "de":
            # Prioritize Swiss/German sources and Zurich content
            news.sort(key=lambda x: (
                -x.get('priority', 5),
                -(10 if x.get('category') == 'zurich' else 0),
                -(5 if x.get('source') in ['nzz', 'srf', 'tagesanzeiger', '20min'] else 0),
                x.get('age_hours', 24)
            ))
        else:
            # For English, prioritize international sources
            news.sort(key=lambda x: (
                -x.get('priority', 5),
                -(5 if x.get('source') in ['bbc', 'techcrunch', 'theverge'] else 0),
                x.get('age_hours', 24)
            ))
        
        return news[:count]
    
    async def generate_script(self, request: ScriptRequest) -> Dict[str, Any]:
        """Generate radio script using GPT - PLACEHOLDER for now"""
        try:
            # For now, return a structured response
            # TODO: Implement real GPT integration
            
            script = {
                "segments": [
                    {
                        "type": "intro",
                        "speaker": request.primary_speaker or "marcel",
                        "text": f"Willkommen bei RadioX! Hier sind die aktuellen News.",
                        "duration": 10
                    }
                ],
                "total_duration": 60,
                "gpt_prompts": [
                    {
                        "stage": "script_generation",
                        "model": "gpt-4",
                        "purpose": "Generate radio script",
                        "prompt": "Generate a radio script based on the provided content...",
                        "response": "Generated script content (placeholder)"
                    }
                ],
                "metadata": {
                    "preset": request.preset_name,
                    "speakers": [request.primary_speaker, request.secondary_speaker],
                    "generated_at": datetime.now().isoformat()
                }
            }
            
            return script
            
        except Exception as e:
            logger.error(f"Script generation failed: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Script generation failed: {str(e)}")

content_service = ContentService()

# Health Check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "content-service"}

# Content Generation
@app.get("/content")
async def get_content(news_count: int = 2, language: str = "de", location: Optional[str] = None):
    """Get content for show generation - REAL RSS/Weather/Bitcoin data"""
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
    """Get latest news from RSS feeds"""
    news = await content_service.rss_service.get_all_recent_news(24)
    return news[:limit]

@app.get("/bitcoin")
async def get_bitcoin_data():
    """Get Bitcoin analysis"""
    return await content_service.bitcoin_service.get_bitcoin_data()

@app.get("/weather")
async def get_weather(location: str = "Zurich"):
    """Get weather data"""
    return await content_service.weather_service.get_current_weather(location)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 