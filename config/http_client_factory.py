"""
🚀 RadioX HTTP Client Factory - ULTIMATE NETWORKING EDITION
=========================================================

Google Engineering Level HTTP Client Management:
- Connection Pooling with Keep-Alive
- Exponential Backoff Retry Logic
- Circuit Breaker Pattern
- Request/Response Monitoring
- Timeout Management
- Performance Analytics

ELIMINATES ALL REDUNDANT HTTP CLIENTS ACROSS 8 MICROSERVICES!

Author: Marcel & Claude - Building the Next Unicorn 🦄
"""

import asyncio
import time
import json
from typing import Dict, Any, Optional, List, Callable, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import threading
import hashlib
from contextlib import asynccontextmanager
from loguru import logger
import os

import httpx
from httpx import AsyncClient, Response, Timeout, Limits

from config.simple_settings import get_simple_settings

settings = get_simple_settings()


class RequestType(Enum):
    """Request types for different timeout configurations"""
    FAST = "fast"           # 5s timeout - health checks, config
    STANDARD = "standard"   # 30s timeout - content, data
    SLOW = "slow"          # 120s timeout - audio processing
    ULTRA_SLOW = "ultra_slow"  # 300s timeout - show generation


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"       # Normal operation
    OPEN = "open"          # Circuit breaker triggered
    HALF_OPEN = "half_open" # Testing recovery


@dataclass
class RequestStats:
    """Advanced request statistics"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    timeout_requests: int = 0
    retry_requests: int = 0
    avg_response_time: float = 0.0
    peak_response_time: float = 0.0
    circuit_breaks: int = 0
    last_error: Optional[str] = None
    uptime_start: datetime = field(default_factory=datetime.now)
    
    @property
    def success_rate(self) -> float:
        if self.total_requests == 0:
            return 100.0
        return (self.successful_requests / self.total_requests) * 100
    
    @property
    def error_rate(self) -> float:
        return 100.0 - self.success_rate
    
    @property
    def uptime_hours(self) -> float:
        return (datetime.now() - self.uptime_start).total_seconds() / 3600


@dataclass
class CircuitBreaker:
    """Circuit breaker for service protection"""
    failure_threshold: int = 5
    recovery_timeout: float = 60.0  # seconds
    failure_count: int = 0
    state: CircuitState = CircuitState.CLOSED
    last_failure_time: Optional[float] = None
    
    def should_allow_request(self) -> bool:
        """Check if request should be allowed"""
        if self.state == CircuitState.CLOSED:
            return True
        elif self.state == CircuitState.OPEN:
            if time.time() - (self.last_failure_time or 0) > self.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
                return True
            return False
        else:  # HALF_OPEN
            return True
    
    def record_success(self):
        """Record successful request"""
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.CLOSED
        self.failure_count = 0
    
    def record_failure(self):
        """Record failed request"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            logger.warning(f"🔴 Circuit breaker OPENED after {self.failure_count} failures")


class HTTPClientFactory:
    """🚀 ULTIMATE HTTP Client Factory - Singleton Pattern"""
    
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
        
        # Client configurations
        self._clients: Dict[RequestType, AsyncClient] = {}
        self._circuit_breakers: Dict[str, CircuitBreaker] = {}
        self._stats = RequestStats()
        self._client_lock = threading.Lock()
        
        # Timeout configurations
        self.timeout_configs = {
            RequestType.FAST: Timeout(5.0, connect=2.0),
            RequestType.STANDARD: Timeout(30.0, connect=5.0),
            RequestType.SLOW: Timeout(120.0, connect=10.0),
            RequestType.ULTRA_SLOW: Timeout(300.0, connect=15.0)
        }
        
        # Connection limits for optimal performance
        self.connection_limits = Limits(
            max_keepalive_connections=20,
            max_connections=100,
            keepalive_expiry=30.0
        )
        
        # Retry configuration
        self.max_retries = 3
        self.retry_delays = [1, 2, 4]  # Exponential backoff
        
        # Initialize clients
        self._initialize_clients()
        
        self._initialized = True
        logger.info("🚀 HTTP CLIENT FACTORY INITIALIZED - READY FOR UNICORN NETWORKING!")
    
    def _initialize_clients(self):
        """Initialize HTTP clients for different request types"""
        
        # Common headers for all requests
        common_headers = {
            "User-Agent": "RadioX-Backend/2.0.0",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        
        for request_type, timeout in self.timeout_configs.items():
            self._clients[request_type] = AsyncClient(
                timeout=timeout,
                limits=self.connection_limits,
                headers=common_headers,
                follow_redirects=True,
                verify=True  # SSL verification
            )
            logger.info(f"✅ HTTP client initialized for {request_type.value}")
    
    def _get_circuit_breaker(self, service_name: str) -> CircuitBreaker:
        """Get or create circuit breaker for service"""
        if service_name not in self._circuit_breakers:
            self._circuit_breakers[service_name] = CircuitBreaker()
        return self._circuit_breakers[service_name]
    
    @asynccontextmanager
    async def get_client(self, request_type: RequestType = RequestType.STANDARD):
        """🎯 Get optimized HTTP client with automatic cleanup"""
        
        if request_type not in self._clients:
            raise ValueError(f"Client type {request_type} not available")
        
        client = self._clients[request_type]
        
        try:
            yield client
        finally:
            # Client cleanup is handled by the factory
            pass
    
    async def request_with_retry(
        self,
        method: str,
        url: str,
        request_type: RequestType = RequestType.STANDARD,
        service_name: Optional[str] = None,
        max_retries: Optional[int] = None,
        **kwargs
    ) -> Response:
        """🧠 Make HTTP request with intelligent retry logic and circuit breaker"""
        
        # Extract service name from URL if not provided
        if not service_name:
            try:
                from urllib.parse import urlparse
                parsed = urlparse(url)
                service_name = parsed.hostname or "unknown"
            except:
                service_name = "unknown"
        
        # Check circuit breaker
        circuit_breaker = self._get_circuit_breaker(service_name)
        if not circuit_breaker.should_allow_request():
            raise httpx.RequestError(f"Circuit breaker OPEN for {service_name}")
        
        # Use provided max_retries or default
        retries = max_retries if max_retries is not None else self.max_retries
        last_exception = None
        
        for attempt in range(retries + 1):
            start_time = time.time()
            
            try:
                async with self.get_client(request_type) as client:
                    # Make the request
                    response = await client.request(method, url, **kwargs)
                    
                    # Update performance stats
                    execution_time = time.time() - start_time
                    self._update_stats(execution_time, success=True)
                    
                    # Record circuit breaker success
                    circuit_breaker.record_success()
                    
                    # Check if response indicates an error
                    if response.status_code >= 500:
                        raise httpx.HTTPStatusError(
                            f"Server error: {response.status_code}",
                            request=response.request,
                            response=response
                        )
                    
                    return response
                    
            except (httpx.TimeoutException, httpx.ConnectTimeout) as e:
                execution_time = time.time() - start_time
                self._update_stats(execution_time, success=False, timeout=True)
                last_exception = e
                logger.warning(f"⏰ Timeout on attempt {attempt + 1} for {url}")
                
            except (httpx.HTTPStatusError, httpx.RequestError) as e:
                execution_time = time.time() - start_time
                self._update_stats(execution_time, success=False)
                last_exception = e
                logger.warning(f"❌ HTTP error on attempt {attempt + 1} for {url}: {e}")
                
            except Exception as e:
                execution_time = time.time() - start_time
                self._update_stats(execution_time, success=False)
                last_exception = e
                logger.error(f"💥 Unexpected error on attempt {attempt + 1} for {url}: {e}")
            
            # Don't retry on the last attempt
            if attempt < retries:
                # Exponential backoff
                delay = self.retry_delays[min(attempt, len(self.retry_delays) - 1)]
                logger.info(f"🔄 Retrying in {delay}s... (attempt {attempt + 1}/{retries})")
                await asyncio.sleep(delay)
                self._stats.retry_requests += 1
        
        # All retries failed - record circuit breaker failure
        circuit_breaker.record_failure()
        
        # Raise the last exception
        if last_exception:
            raise last_exception
        else:
            raise httpx.RequestError(f"All {retries} retries failed for {url}")
    
    async def get(self, url: str, **kwargs) -> Response:
        """🚀 Optimized GET request"""
        return await self.request_with_retry("GET", url, **kwargs)
    
    async def post(self, url: str, **kwargs) -> Response:
        """🚀 Optimized POST request"""
        return await self.request_with_retry("POST", url, **kwargs)
    
    async def put(self, url: str, **kwargs) -> Response:
        """🚀 Optimized PUT request"""
        return await self.request_with_retry("PUT", url, **kwargs)
    
    async def delete(self, url: str, **kwargs) -> Response:
        """🚀 Optimized DELETE request"""
        return await self.request_with_retry("DELETE", url, **kwargs)
    
    def _update_stats(self, execution_time: float, success: bool = True, timeout: bool = False):
        """Update performance statistics"""
        self._stats.total_requests += 1
        
        if success:
            self._stats.successful_requests += 1
        else:
            self._stats.failed_requests += 1
            
        if timeout:
            self._stats.timeout_requests += 1
        
        # Update response time stats
        if self._stats.avg_response_time == 0:
            self._stats.avg_response_time = execution_time
        else:
            # Rolling average (90% old, 10% new)
            self._stats.avg_response_time = (
                0.9 * self._stats.avg_response_time + 0.1 * execution_time
            )
        
        # Update peak response time
        self._stats.peak_response_time = max(
            self._stats.peak_response_time, 
            execution_time
        )
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """📊 Get comprehensive performance statistics"""
        return {
            "requests": {
                "total": self._stats.total_requests,
                "successful": self._stats.successful_requests,
                "failed": self._stats.failed_requests,
                "timeout": self._stats.timeout_requests,
                "retries": self._stats.retry_requests,
                "success_rate_percent": round(self._stats.success_rate, 2),
                "error_rate_percent": round(self._stats.error_rate, 2)
            },
            "performance": {
                "avg_response_time_ms": round(self._stats.avg_response_time * 1000, 2),
                "peak_response_time_ms": round(self._stats.peak_response_time * 1000, 2)
            },
            "circuit_breakers": {
                service: {
                    "state": cb.state.value,
                    "failure_count": cb.failure_count,
                    "last_failure": cb.last_failure_time
                }
                for service, cb in self._circuit_breakers.items()
            },
            "clients": {
                "active_clients": len(self._clients),
                "connection_pool": {
                    "max_connections": self.connection_limits.max_connections,
                    "max_keepalive": self.connection_limits.max_keepalive_connections
                }
            },
            "uptime": {
                "hours": round(self._stats.uptime_hours, 2),
                "start_time": self._stats.uptime_start.isoformat()
            },
            "status": "🚀 UNICORN NETWORKING!" if self._stats.error_rate < 5 else "⚠️ NEEDS ATTENTION"
        }
    
    async def health_check_service(self, service_name: str, service_url: str) -> Dict[str, Any]:
        """🏥 Health check for a specific service"""
        try:
            start_time = time.time()
            
            response = await self.get(
                f"{service_url}/health",
                request_type=RequestType.FAST,
                service_name=service_name
            )
            
            execution_time = time.time() - start_time
            
            return {
                "service": service_name,
                "status": "healthy" if response.status_code == 200 else "unhealthy",
                "response_time_ms": round(execution_time * 1000, 2),
                "status_code": response.status_code,
                "circuit_breaker": self._get_circuit_breaker(service_name).state.value
            }
            
        except Exception as e:
            return {
                "service": service_name,
                "status": "error",
                "error": str(e),
                "circuit_breaker": self._get_circuit_breaker(service_name).state.value
            }
    
    async def close_all_clients(self):
        """🧹 Close all HTTP clients"""
        for client in self._clients.values():
            await client.aclose()
        logger.info("🧹 All HTTP clients closed")


# 🎯 CONVENIENCE FUNCTIONS FOR EASY MIGRATION

def get_http_client() -> HTTPClientFactory:
    """Get HTTP client factory - REPLACES ALL REDUNDANT httpx.AsyncClient() calls"""
    return HTTPClientFactory()


async def http_get(url: str, **kwargs) -> Response:
    """Make optimized GET request - ULTIMATE PERFORMANCE"""
    factory = get_http_client()
    return await factory.get(url, **kwargs)


async def http_post(url: str, **kwargs) -> Response:
    """Make optimized POST request - ULTIMATE PERFORMANCE"""
    factory = get_http_client()
    return await factory.post(url, **kwargs)


def get_http_stats() -> Dict[str, Any]:
    """Get HTTP client performance statistics"""
    factory = get_http_client()
    return factory.get_performance_stats()


# 🚀 INITIALIZE FACTORY ON IMPORT
_http_factory = HTTPClientFactory()

logger.info("🦄 HTTP CLIENT FACTORY READY - LET'S NETWORK LIKE A UNICORN!")


class RadioXHttpClient:
    """Zentraler HTTP Client mit automatischem Key Management"""
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.key_service_url = os.getenv("KEY_SERVICE_URL", "http://key-service:8001")
        self.api_keys: Dict[str, str] = {}
        self.keys_loaded = False
        
    async def load_api_keys(self) -> bool:
        """Lade API Keys vom Key Service"""
        try:
            response = await self.client.get(f"{self.key_service_url}/keys")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"🔑 Loaded {data.get('count', 0)} keys from Key Service")
                
                # Load individual keys
                for key_name in data.get('keys', {}):
                    key_response = await self.client.get(f"{self.key_service_url}/keys/{key_name}")
                    if key_response.status_code == 200:
                        key_data = key_response.json()
                        self.api_keys[key_name] = key_data['key_value']
                        
                        # Set as environment variable too
                        env_var_name = key_name.upper()
                        os.environ[env_var_name] = key_data['key_value']
                        
                self.keys_loaded = True
                logger.info(f"✅ API Keys loaded: {list(self.api_keys.keys())}")
                return True
                
        except Exception as e:
            logger.warning(f"⚠️ Key Service not available: {e}")
            
        return False
    
    async def get_api_key(self, key_name: str) -> Optional[str]:
        """Hole einen spezifischen API Key"""
        if not self.keys_loaded:
            await self.load_api_keys()
            
        return self.api_keys.get(key_name) or os.getenv(key_name.upper())
    
    async def request(self, method: str, url: str, **kwargs) -> httpx.Response:
        """HTTP Request mit automatischem Key Management"""
        # Ensure keys are loaded
        if not self.keys_loaded:
            await self.load_api_keys()
            
        return await self.client.request(method, url, **kwargs)
    
    async def get(self, url: str, **kwargs) -> httpx.Response:
        """GET Request"""
        return await self.request("GET", url, **kwargs)
    
    async def post(self, url: str, **kwargs) -> httpx.Response:
        """POST Request"""
        return await self.request("POST", url, **kwargs)
    
    async def close(self):
        """Close client"""
        await self.client.aclose()

# Global client instance
_radiox_http_client: Optional[RadioXHttpClient] = None

async def get_radiox_http_client() -> RadioXHttpClient:
    """Get or create RadioX HTTP client instance"""
    global _radiox_http_client
    
    if _radiox_http_client is None:
        _radiox_http_client = RadioXHttpClient()
        await _radiox_http_client.load_api_keys()
    
    return _radiox_http_client

async def get_api_key_from_service(key_name: str) -> Optional[str]:
    """Helper function to get API key from Key Service"""
    client = await get_radiox_http_client()
    return await client.get_api_key(key_name)

async def close_radiox_http_client():
    """Close global RadioX HTTP client"""
    global _radiox_http_client
    if _radiox_http_client:
        await _radiox_http_client.close()
        _radiox_http_client = None 