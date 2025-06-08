#!/usr/bin/env python3

"""
RSS Service - HIGH PERFORMANCE
============================

Google Engineering Best Practices:
- Resource Management (Proper Session Cleanup)
- Performance Optimization (Connection Pooling)
- Error Handling (Graceful Degradation)
- Clean Code (DRY, SOLID)

Service für das Sammeln und Verarbeiten von RSS Feed Daten.
Teil der Data Layer in der Clean Architecture.
"""

import asyncio
import aiohttp
import feedparser
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, AsyncContextManager
from dataclasses import dataclass
from loguru import logger
from contextlib import asynccontextmanager

# Import Supabase Client
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))
from database.supabase_client import get_db


@dataclass(frozen=True)
class RSSConfig:
    """Immutable RSS configuration"""
    timeout: int = 15
    user_agent: str = 'RadioX RSS Reader 2.0'
    max_concurrent: int = 8
    retry_attempts: int = 2


@dataclass
class RSSNewsItem:
    """RSS news article data structure"""
    title: str
    summary: str
    link: str
    published: datetime
    source: str
    category: str
    priority: int = 5
    weight: float = 1.0


class RSSService:
    """High-Performance RSS Service with proper resource management"""
    
    __slots__ = ('_db', '_config')
    
    def __init__(self):
        self._db = get_db()
        self._config = RSSConfig()
    
    @asynccontextmanager
    async def _session_manager(self) -> AsyncContextManager[aiohttp.ClientSession]:
        """Context manager for proper session lifecycle"""
        connector = aiohttp.TCPConnector(
            limit=self._config.max_concurrent,
            limit_per_host=2,
            ttl_dns_cache=300,
            use_dns_cache=True
        )
        
        timeout = aiohttp.ClientTimeout(total=self._config.timeout)
        headers = {'User-Agent': self._config.user_agent}
        
        session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers=headers
        )
        
        try:
            yield session
        finally:
            await session.close()
            await connector.close()
    
    async def get_all_active_feeds(self) -> List[Dict[str, Any]]:
        """Get active RSS feeds from database"""
        try:
            response = self._db.client.table('rss_feed_preferences').select('*').eq('is_active', True).execute()
            return response.data or []
        except Exception as e:
            logger.error(f"❌ RSS Feeds laden fehlgeschlagen: {e}")
            return []
    
    async def get_all_recent_news(self) -> List[RSSNewsItem]:
        """Collect all news from active feeds with proper session management"""
        feeds = await self.get_all_active_feeds()
        if not feeds:
            return []
        
        logger.info(f"🚀 Sammle News von {len(feeds)} Feeds parallel...")
        
        async with self._session_manager() as session:
            # Process feeds in batches to prevent overwhelming
            semaphore = asyncio.Semaphore(self._config.max_concurrent)
            tasks = [self._fetch_feed_with_semaphore(session, feed, semaphore) for feed in feeds]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            return self._process_results(results, feeds)
    
    async def _fetch_feed_with_semaphore(
        self, session: aiohttp.ClientSession, feed: Dict[str, Any], semaphore: asyncio.Semaphore
    ) -> List[RSSNewsItem]:
        """Fetch feed with concurrency control"""
        async with semaphore:
            return await self._fetch_feed_news(session, feed)
    
    def _process_results(self, results: List, feeds: List[Dict[str, Any]]) -> List[RSSNewsItem]:
        """Process and aggregate results with performance metrics"""
        all_news = []
        successful_feeds = 0
        failed_feeds = 0
        feed_summary = []
        
        for i, result in enumerate(results):
            feed_name = feeds[i].get('source_name', 'Unknown')
            
            if isinstance(result, list):
                all_news.extend(result)
                successful_feeds += 1
                if result:
                    feed_summary.append(f"{feed_name}[{len(result)}]")
            else:
                failed_feeds += 1
                feed_summary.append(f"{feed_name}[❌]")
        
        # Sort by publication date (newest first)
        all_news.sort(key=lambda x: x.published, reverse=True)
        
        # Compact logging
        status = "✅" if failed_feeds == 0 else "⚠️"
        logger.info(f"{status} {len(all_news)} News | {successful_feeds} Feeds OK | {failed_feeds} Fehler")
        
        # Source summary with intelligent line breaks
        self._log_source_summary(feed_summary)
        
        return all_news
    
    def _log_source_summary(self, feed_summary: List[str]) -> None:
        """Log source summary with optimal formatting"""
        if not feed_summary:
            return
        
        chunks = []
        current_chunk = []
        current_length = 0
        max_line_length = 80
        
        for item in feed_summary:
            item_length = len(item) + 2  # +2 for ", "
            
            if current_length + item_length > max_line_length and current_chunk:
                chunks.append(", ".join(current_chunk))
                current_chunk = [item]
                current_length = len(item)
            else:
                current_chunk.append(item)
                current_length += item_length
        
        if current_chunk:
            chunks.append(", ".join(current_chunk))
        
        for chunk in chunks:
            logger.info(f"📊 {chunk}")
    
    async def _fetch_feed_news(self, session: aiohttp.ClientSession, feed: Dict[str, Any]) -> List[RSSNewsItem]:
        """Fetch news from single feed with error handling"""
        feed_name = feed.get('source_name', 'Unknown')
        feed_url = feed.get('feed_url', '')
        feed_category = feed.get('feed_category', 'general')
        
        if not feed_url:
            return []
        
        for attempt in range(self._config.retry_attempts):
            try:
                content = await self._fetch_content(session, feed_url)
                if not content:
                    continue
                
                parsed_feed = feedparser.parse(content)
                
                return [
                    self._create_news_item(entry, feed_name, feed_category, feed)
                    for entry in parsed_feed.entries
                    if self._is_valid_entry(entry)
                ]
                
            except Exception:
                if attempt == self._config.retry_attempts - 1:
                    return []
                await asyncio.sleep(0.5 * (attempt + 1))  # Exponential backoff
        
        return []
    
    async def _fetch_content(self, session: aiohttp.ClientSession, url: str) -> Optional[str]:
        """Fetch content from URL with proper error handling"""
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    return await response.text()
                return None
        except Exception:
            return None
    
    def _create_news_item(self, entry: Dict[str, Any], feed_name: str, category: str, feed: Dict[str, Any]) -> RSSNewsItem:
        """Create RSSNewsItem from feed entry"""
        return RSSNewsItem(
            title=entry.get('title', 'Kein Titel'),
            summary=entry.get('summary', entry.get('description', 'Keine Beschreibung')),
            link=entry.get('link', ''),
            published=self._parse_date(entry),
            source=self._clean_source_name(feed_name),
            category=category,
            priority=feed.get('priority', 5),
            weight=feed.get('weight', 1.0)
        )
    
    def _is_valid_entry(self, entry: Dict[str, Any]) -> bool:
        """Check if entry has minimum required fields"""
        return bool(entry.get('title') or entry.get('summary') or entry.get('description'))
    
    def _parse_date(self, entry: Dict[str, Any]) -> datetime:
        """Parse entry date with fallbacks"""
        # Try parsed date fields first
        for field in ['published_parsed', 'updated_parsed', 'created_parsed']:
            if hasattr(entry, field) and getattr(entry, field):
                try:
                    return datetime(*getattr(entry, field)[:6])
                except:
                    continue
        
        # Try string date fields
        for field in ['published', 'updated', 'created']:
            if hasattr(entry, field) and getattr(entry, field):
                try:
                    from dateutil import parser
                    return parser.parse(getattr(entry, field))
                except:
                    continue
        
        return datetime.now()
    
    def _clean_source_name(self, name: str) -> str:
        """Clean and normalize source name"""
        return name.lower().replace('_', ' ').replace('-', ' ').title()
    
    async def fetch_feed_items(self, feed_url: str, max_items: int = 10) -> List[Dict[str, Any]]:
        """Fetch specific feed items with session management"""
        async with self._session_manager() as session:
            try:
                content = await self._fetch_content(session, feed_url)
                if not content:
                    return []
                
                parsed_feed = feedparser.parse(content)
                return [
                    {
                        'title': entry.get('title', ''),
                        'link': entry.get('link', ''),
                        'summary': entry.get('summary', ''),
                        'published': self._parse_date(entry).isoformat()
                    }
                    for entry in parsed_feed.entries[:max_items]
                    if self._is_valid_entry(entry)
                ]
                
            except Exception as e:
                logger.error(f"❌ Feed fetch error for {feed_url}: {e}")
                return []
    
    async def test_connection(self) -> bool:
        """Test RSS service connectivity"""
        test_url = "https://feeds.bbci.co.uk/news/rss.xml"
        
        async with self._session_manager() as session:
            try:
                content = await self._fetch_content(session, test_url)
                return bool(content)
            except Exception:
                return False