"""
RadioX Supabase Database Client
Zentrale Datenbankverbindung und CRUD-Operationen
"""

from supabase import create_client, Client
from typing import List, Dict, Any, Optional, Union, Callable
from datetime import datetime, timezone
from dataclasses import dataclass, field
import uuid
import sys
import os
from loguru import logger
from dotenv import load_dotenv
import asyncio
import aiohttp
import time
from collections import defaultdict
import weakref
import threading
from concurrent.futures import ThreadPoolExecutor
import hashlib

# Load environment variables FIRST
load_dotenv()

# Backend-Pfad hinzufügen für relative Imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from config.settings import get_settings

settings = get_settings()

@dataclass
class CacheEntry:
    """Advanced cache entry with TTL and hit tracking"""
    data: Any
    timestamp: float
    ttl: float
    hits: int = 0
    last_access: float = field(default_factory=time.time)
    
    @property
    def is_expired(self) -> bool:
        return time.time() - self.timestamp > self.ttl
    
    def touch(self):
        """Update access stats"""
        self.hits += 1
        self.last_access = time.time()

@dataclass
class PerformanceStats:
    """Advanced performance monitoring"""
    total_queries: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    avg_response_time: float = 0.0
    peak_concurrent_connections: int = 0
    current_connections: int = 0
    error_rate: float = 0.0
    
    @property
    def cache_hit_rate(self) -> float:
        total = self.cache_hits + self.cache_misses
        return (self.cache_hits / total * 100) if total > 0 else 0.0

class SupabaseClient:
    """🚀 OPTIMIZED RadioX Supabase Database Client"""
    
    def __init__(self, max_connections: int = 25):
        # Core client
        self.client: Client = create_client(
            settings.supabase_url or "",
            settings.supabase_anon_key or ""
        )
        
        # ⚡ CONNECTION POOL & PERFORMANCE OPTIMIZATION
        self.max_connections = max_connections
        self.connection_semaphore = asyncio.Semaphore(max_connections)
        
        # 🧠 SIMPLE CACHE
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._cache_timestamps: Dict[str, float] = {}
        self.cache_ttl = 300  # 5 minutes default
        
        # 📊 BASIC STATS
        self.query_count = 0
        self.cache_hits = 0
        
        logger.info(f"🚀 OPTIMIZED Supabase Client initialisiert:")
        logger.info(f"   ⚡ Max Connections: {max_connections}")
        logger.info(f"   🧠 Cache TTL: {self.cache_ttl}s")
    
    async def _execute_with_pool(self, func):
        """Execute database operation with connection pooling"""
        async with self.connection_semaphore:
            self.query_count += 1
            start_time = time.time()
            
            try:
                result = await asyncio.to_thread(func)
                execution_time = time.time() - start_time
                
                if execution_time > 1.0:  # Log slow queries
                    logger.warning(f"⚠️ Slow query: {execution_time:.2f}s")
                
                return result
                
            except Exception as e:
                logger.error(f"❌ Database operation failed: {e}")
                raise
    
    def _get_cache_key(self, table: str, operation: str, **params) -> str:
        """Generate simple cache key"""
        param_str = "_".join(f"{k}{v}" for k, v in sorted(params.items()))
        return f"{table}:{operation}:{param_str}"
    
    def _get_cached(self, cache_key: str) -> Optional[Any]:
        """Get from cache if not expired"""
        if cache_key in self._cache:
            age = time.time() - self._cache_timestamps.get(cache_key, 0)
            if age < self.cache_ttl:
                self.cache_hits += 1
                logger.debug(f"🎯 Cache HIT: {cache_key}")
                return self._cache[cache_key]
            else:
                # Remove expired
                del self._cache[cache_key]
                del self._cache_timestamps[cache_key]
        return None
    
    def _set_cached(self, cache_key: str, data: Any):
        """Set cache with timestamp"""
        self._cache[cache_key] = data
        self._cache_timestamps[cache_key] = time.time()
        logger.debug(f"💾 Cache SET: {cache_key}")
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get basic performance stats"""
        total_requests = self.query_count
        hit_rate = (self.cache_hits / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "total_queries": total_requests,
            "cache_hits": self.cache_hits,
            "cache_hit_rate": f"{hit_rate:.1f}%",
            "cache_size": len(self._cache),
            "max_connections": self.max_connections
        }
    
    async def preload_speakers(self):
        """🚀 Preload critical speaker data"""
        logger.info("🚀 Preloading speakers...")
        try:
            # Preload all active speakers in one query
            result = await self._execute_with_pool(
                lambda: self.client.table("voice_configurations")
                .select("*")
                .eq("is_active", True)
                .execute()
            )
            
            # Cache each speaker individually
            for speaker in result.data:
                cache_key = self._get_cache_key("voice_configurations", "get_speaker", speaker=speaker["voice_name"].lower())
                self._set_cached(cache_key, speaker)
            
            logger.info(f"✅ Preloaded {len(result.data)} speakers")
            
        except Exception as e:
            logger.error(f"❌ Speaker preload failed: {e}")

    # ==================== STREAMS ====================

    # ==================== OPTIMIZED SPEAKER QUERIES ====================
    
    async def get_speaker_config_optimized(self, speaker_name: str) -> Optional[Dict[str, Any]]:
        """🚀 Optimized speaker configuration with caching"""
        # Check cache first
        cache_key = self._get_cache_key("voice_configurations", "get_speaker", speaker=speaker_name)
        cached_result = self._get_cached(cache_key)
        if cached_result:
            return cached_result
        
        # Query database with connection pooling
        try:
            result = await self._execute_with_pool(
                lambda: self.client.table("voice_configurations")
                .select("*")
                .eq("voice_name", speaker_name.title())
                .eq("is_active", True)
                .execute()
            )
            
            if result.data:
                speaker_config = result.data[0]
                self._set_cached(cache_key, speaker_config)
                return speaker_config
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Optimized speaker query failed for '{speaker_name}': {e}")
            return None
    
    # ==================== OPTIMIZED CRUD OPERATIONS ====================
    
    async def create_stream(self, title: str, description: Optional[str] = None, duration_minutes: int = 60, persona: str = "cyberpunk") -> Dict[str, Any]:
        """🚀 Optimized stream creation"""
        stream_data = {"title": title, "description": description, "duration_minutes": duration_minutes, "persona": persona, "status": "planned"}
        
        try:
            async def _create():
                return self.client.table("streams").insert(stream_data).execute()
            
            result = await self._track_performance(_create)
            await self.clear_cache("streams")  # Invalidate stream cache
            logger.info(f"Stream erstellt: {title}")
            return result.data[0]
        except Exception as e:
            logger.error(f"Fehler beim Erstellen des Streams: {e}")
            raise

    async def get_stream(self, stream_id: str) -> Optional[Dict[str, Any]]:
        """🚀 Optimized stream retrieval with caching"""
        cache_key = self._generate_cache_key("streams", "get_by_id", stream_id=stream_id)
        
        cached_result = await self._get_from_cache(cache_key)
        if cached_result:
            return cached_result
        
        try:
            async def _query():
                return self.client.table("streams").select("*").eq("id", stream_id).execute()
            
            result = await self._track_performance(_query)
            
            if result.data:
                stream_data = result.data[0]
                await self._set_cache(cache_key, stream_data, ttl=300.0)  # 5 min cache
                return stream_data
            
            return None
        except Exception as e:
            logger.error(f"Fehler beim Abrufen des Streams {stream_id}: {e}")
            return None

    async def get_recent_streams(self, limit: int = 10) -> List[Dict[str, Any]]:
        """🚀 Optimized recent streams with caching"""
        cache_key = self._generate_cache_key("streams", "get_recent", limit=limit)
        
        cached_result = await self._get_from_cache(cache_key)
        if cached_result:
            return cached_result
        
        try:
            async def _query():
                return self.client.table("streams").select("*").order("created_at", desc=True).limit(limit).execute()
            
            result = await self._track_performance(_query)
            
            await self._set_cache(cache_key, result.data, ttl=60.0)  # 1 min cache for recent data
            return result.data
        except Exception as e:
            logger.error(f"Fehler beim Abrufen der neuesten Streams: {e}")
            return []

    async def get_active_categories(self) -> List[Dict[str, Any]]:
        """🚀 Optimized categories with long-term caching"""
        cache_key = self._generate_cache_key("content_categories", "get_active")
        
        cached_result = await self._get_from_cache(cache_key)
        if cached_result:
            return cached_result
        
        try:
            async def _query():
                return self.client.table("content_categories").select("*").eq("is_active", True).order("priority_level").execute()
            
            result = await self._track_performance(_query)
            
            await self._set_cache(cache_key, result.data, ttl=3600.0)  # 1 hour cache
            return result.data
        except Exception as e:
            logger.error(f"Fehler beim Abrufen der aktiven Kategorien: {e}")
            return []

    async def get_content_sources_by_category(self, category_slug: str, source_type: Optional[str] = None, active_only: bool = True) -> List[Dict[str, Any]]:
        """🚀 Optimized content sources with caching"""
        cache_key = self._generate_cache_key("content_sources", "get_by_category", category=category_slug, type=source_type, active=active_only)
        
        cached_result = await self._get_from_cache(cache_key)
        if cached_result:
            return cached_result
        
        try:
            async def _query():
                query = self.client.table("content_sources").select("*, content_categories!inner(slug)").eq("content_categories.slug", category_slug)
                if source_type:
                    query = query.eq("source_type", source_type)
                if active_only:
                    query = query.eq("is_active", True)
                return query.order("priority_level").execute()
            
            result = await self._track_performance(_query)
            
            await self._set_cache(cache_key, result.data, ttl=1800.0)  # 30 min cache
            return result.data
        except Exception as e:
            logger.error(f"Fehler beim Abrufen der Content Sources: {e}")
            return []

# Singleton Instance - Lazy Loading
_db_instance = None

def get_db():
    """Lazy loading der Supabase Client Instanz"""
    global _db_instance
    if _db_instance is None:
        try:
            _db_instance = SupabaseClient()
        except Exception as e:
            logger.error(f"Fehler beim Initialisieren der Supabase-Verbindung: {e}")
            raise
    return _db_instance 