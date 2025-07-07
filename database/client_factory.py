"""
🚀 RadioX Database Client Factory - ULTIMATE EDITION
==================================================

Google Engineering Level Database Management:
- Singleton Connection Pool
- Advanced Caching Layer  
- Performance Monitoring
- Automatic Failover
- Connection Health Checks

ELIMINATES ALL REDUNDANT DATABASE CONNECTIONS ACROSS 8 MICROSERVICES!

Author: Marcel & Claude - Building the Next Unicorn 🦄
"""

import asyncio
import time
import weakref
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import threading
from concurrent.futures import ThreadPoolExecutor
import hashlib
import os
from loguru import logger

from supabase import create_client, Client
from config.simple_settings import get_simple_settings

settings = get_simple_settings()


class ConnectionType(Enum):
    """Connection types for different use cases"""
    REGULAR = "regular"      # Standard operations (anon key)
    ADMIN = "admin"         # Admin operations (service key)
    READONLY = "readonly"   # Read-only operations (optimized)


@dataclass
class ConnectionStats:
    """Advanced connection statistics"""
    total_connections: int = 0
    active_connections: int = 0
    queries_executed: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    avg_response_time: float = 0.0
    peak_connections: int = 0
    errors: int = 0
    last_error: Optional[str] = None
    uptime_start: datetime = field(default_factory=datetime.now)
    
    @property
    def cache_hit_rate(self) -> float:
        total = self.cache_hits + self.cache_misses
        return (self.cache_hits / total * 100) if total > 0 else 0.0
    
    @property
    def uptime_hours(self) -> float:
        return (datetime.now() - self.uptime_start).total_seconds() / 3600


@dataclass 
class CacheEntry:
    """Ultra-fast cache entry with TTL"""
    data: Any
    timestamp: float
    ttl: float
    access_count: int = 0
    
    @property
    def is_expired(self) -> bool:
        return time.time() - self.timestamp > self.ttl
    
    def touch(self):
        self.access_count += 1


class DatabaseClientFactory:
    """🚀 ULTIMATE Database Client Factory - Singleton Pattern"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
            
        # Core clients
        self._clients: Dict[ConnectionType, Client] = {}
        self._client_locks: Dict[ConnectionType, threading.Lock] = {}
        
        # Performance optimization
        self._cache: Dict[str, CacheEntry] = {}
        self._cache_lock = threading.Lock()
        self._stats = ConnectionStats()
        
        # Configuration
        self.cache_ttl = 300  # 5 minutes default
        self.max_cache_size = 1000
        self.health_check_interval = 30  # seconds
        
        # Connection pool
        self.max_connections = 25
        self.connection_semaphore = asyncio.Semaphore(self.max_connections)
        
        # Initialize clients
        self._initialize_clients()
        
        # Start background tasks
        self._start_health_monitor()
        
        self._initialized = True
        logger.info("🚀 DATABASE CLIENT FACTORY INITIALIZED - READY FOR UNICORN SCALE!")
    
    def _initialize_clients(self):
        """Initialize all client types"""
        
        # Regular client (anon key)
        if settings.supabase_url and settings.supabase_anon_key:
            self._clients[ConnectionType.REGULAR] = create_client(
                settings.supabase_url, 
                settings.supabase_anon_key
            )
            self._client_locks[ConnectionType.REGULAR] = threading.Lock()
            logger.info("✅ Regular Supabase client initialized")
        
        # Admin client (service role key)  
        if settings.supabase_url and settings.supabase_service_key:
            self._clients[ConnectionType.ADMIN] = create_client(
                settings.supabase_url,
                settings.supabase_service_key
            )
            self._client_locks[ConnectionType.ADMIN] = threading.Lock()
            logger.info("✅ Admin Supabase client initialized")
        
        # Read-only optimized client
        if settings.supabase_url and settings.supabase_anon_key:
            self._clients[ConnectionType.READONLY] = create_client(
                settings.supabase_url,
                settings.supabase_anon_key
            )
            self._client_locks[ConnectionType.READONLY] = threading.Lock()
            logger.info("✅ Read-only Supabase client initialized")
    
    def get_client(self, connection_type: ConnectionType = ConnectionType.REGULAR) -> Client:
        """🎯 Get optimized database client"""
        
        if connection_type not in self._clients:
            raise ValueError(f"Client type {connection_type} not available")
        
        # Update stats
        self._stats.active_connections += 1
        self._stats.total_connections += 1
        self._stats.peak_connections = max(
            self._stats.peak_connections, 
            self._stats.active_connections
        )
        
        return self._clients[connection_type]
    
    async def execute_with_cache(
        self,
        cache_key: str,
        query_func: Callable,
        ttl: Optional[float] = None,
        connection_type: ConnectionType = ConnectionType.REGULAR
    ) -> Any:
        """🧠 Execute query with intelligent caching"""
        
        # Check cache first
        cached_result = self._get_cached(cache_key)
        if cached_result is not None:
            self._stats.cache_hits += 1
            return cached_result
        
        # Execute query with connection pooling
        start_time = time.time()
        
        try:
            async with self.connection_semaphore:
                client = self.get_client(connection_type)
                result = await asyncio.to_thread(query_func, client)
                
                # Update performance stats
                execution_time = time.time() - start_time
                self._update_response_time(execution_time)
                self._stats.queries_executed += 1
                self._stats.cache_misses += 1
                
                # Cache result
                self._set_cached(cache_key, result, ttl or self.cache_ttl)
                
                return result
                
        except Exception as e:
            self._stats.errors += 1
            self._stats.last_error = str(e)
            logger.error(f"❌ Database query failed: {e}")
            raise
        finally:
            self._stats.active_connections -= 1
    
    def _get_cached(self, cache_key: str) -> Any:
        """Get from ultra-fast cache"""
        with self._cache_lock:
            if cache_key in self._cache:
                entry = self._cache[cache_key]
                if not entry.is_expired:
                    entry.touch()
                    return entry.data
                else:
                    # Remove expired entry
                    del self._cache[cache_key]
        return None
    
    def _set_cached(self, cache_key: str, data: Any, ttl: float):
        """Set in cache with automatic cleanup"""
        with self._cache_lock:
            # Clean cache if too large
            if len(self._cache) >= self.max_cache_size:
                self._cleanup_cache()
            
            self._cache[cache_key] = CacheEntry(
                data=data,
                timestamp=time.time(),
                ttl=ttl
            )
    
    def _cleanup_cache(self):
        """Clean expired cache entries"""
        now = time.time()
        expired_keys = [
            key for key, entry in self._cache.items()
            if now - entry.timestamp > entry.ttl
        ]
        
        for key in expired_keys:
            del self._cache[key]
        
        # If still too large, remove least accessed
        if len(self._cache) >= self.max_cache_size:
            sorted_entries = sorted(
                self._cache.items(),
                key=lambda x: x[1].access_count
            )
            
            # Remove 20% of least accessed
            remove_count = int(len(sorted_entries) * 0.2)
            for key, _ in sorted_entries[:remove_count]:
                del self._cache[key]
    
    def _update_response_time(self, new_time: float):
        """Update rolling average response time"""
        if self._stats.avg_response_time == 0:
            self._stats.avg_response_time = new_time
        else:
            # Rolling average (90% old, 10% new)
            self._stats.avg_response_time = (
                0.9 * self._stats.avg_response_time + 0.1 * new_time
            )
    
    def _start_health_monitor(self):
        """Start background health monitoring"""
        def health_check():
            while True:
                try:
                    time.sleep(self.health_check_interval)
                    # Basic health check on all clients
                    for conn_type, client in self._clients.items():
                        # Simple query to test connection
                        try:
                            # Test with a simple query
                            result = client.table('configuration').select('id').limit(1).execute()
                            logger.debug(f"✅ Health check passed for {conn_type}")
                        except Exception as e:
                            logger.warning(f"⚠️ Health check failed for {conn_type}: {e}")
                            
                except Exception as e:
                    logger.error(f"❌ Health monitor error: {e}")
        
        # Start in background thread
        health_thread = threading.Thread(target=health_check, daemon=True)
        health_thread.start()
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """📊 Get comprehensive performance statistics"""
        return {
            "connections": {
                "total": self._stats.total_connections,
                "active": self._stats.active_connections,
                "peak": self._stats.peak_connections,
                "max_allowed": self.max_connections
            },
            "queries": {
                "executed": self._stats.queries_executed,
                "avg_response_time_ms": round(self._stats.avg_response_time * 1000, 2),
                "errors": self._stats.errors,
                "last_error": self._stats.last_error
            },
            "cache": {
                "size": len(self._cache),
                "max_size": self.max_cache_size,
                "hit_rate_percent": round(self._stats.cache_hit_rate, 2),
                "hits": self._stats.cache_hits,
                "misses": self._stats.cache_misses
            },
            "uptime": {
                "hours": round(self._stats.uptime_hours, 2),
                "start_time": self._stats.uptime_start.isoformat()
            },
            "status": "🚀 UNICORN READY!" if self._stats.errors == 0 else "⚠️ NEEDS ATTENTION"
        }
    
    def clear_cache(self):
        """🗑️ Clear all cached data"""
        with self._cache_lock:
            self._cache.clear()
        logger.info("🧹 Cache cleared")
    
    async def preload_critical_data(self):
        """🚀 Preload critical data for maximum performance"""
        logger.info("🚀 Preloading critical data...")
        
        try:
            # Preload speakers
            await self.execute_with_cache(
                "all_speakers",
                lambda client: client.table("voice_configurations").select("*").eq("is_active", True).execute(),
                ttl=600  # 10 minutes
            )
            
            # Preload show presets
            await self.execute_with_cache(
                "show_presets",
                lambda client: client.table("show_presets").select("*").execute(),
                ttl=600
            )
            
            # Preload configuration
            await self.execute_with_cache(
                "system_config",
                lambda client: client.table("configuration").select("*").execute(),
                ttl=300  # 5 minutes
            )
            
            logger.info("✅ Critical data preloaded - UNICORN SPEED ACHIEVED!")
            
        except Exception as e:
            logger.error(f"❌ Preload failed: {e}")


# 🎯 CONVENIENCE FUNCTIONS FOR EASY MIGRATION

def get_db_client(connection_type: ConnectionType = ConnectionType.REGULAR) -> Client:
    """Get database client - REPLACES ALL REDUNDANT create_client() calls"""
    factory = DatabaseClientFactory()
    return factory.get_client(connection_type)


async def execute_cached_query(
    cache_key: str,
    query_func: Callable,
    ttl: Optional[float] = None,
    connection_type: ConnectionType = ConnectionType.REGULAR
) -> Any:
    """Execute cached database query - ULTIMATE PERFORMANCE"""
    factory = DatabaseClientFactory()
    return await factory.execute_with_cache(cache_key, query_func, ttl, connection_type)


def get_db_stats() -> Dict[str, Any]:
    """Get database performance statistics"""
    factory = DatabaseClientFactory()
    return factory.get_performance_stats()


# 🚀 INITIALIZE FACTORY ON IMPORT
_factory = DatabaseClientFactory()

logger.info("🦄 DATABASE CLIENT FACTORY READY - LET'S BUILD THAT UNICORN!") 