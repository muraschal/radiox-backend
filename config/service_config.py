"""
RadioX Service Configuration - Environment Variables with Defaults
80/20 Best Practice: Simple, effective, no bloat
"""

import os
from typing import Optional

class ServiceConfig:
    """Environment-based configuration with sensible defaults"""
    
    # Service URLs
    DATABASE_URL: str = os.getenv("DATABASE_URL", "http://localhost:8001")
    KEY_SERVICE_URL: str = os.getenv("KEY_SERVICE_URL", "http://localhost:8002") 
    DATA_COLLECTOR_URL: str = os.getenv("DATA_COLLECTOR_URL", "http://localhost:8004")
    SHOW_SERVICE_URL: str = os.getenv("SHOW_SERVICE_URL", "http://localhost:8005")
    
    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
    @classmethod
    def log_config(cls):
        """Log current configuration (for debugging)"""
        print(f"🔧 SERVICE CONFIG:")
        print(f"   Database: {cls.DATABASE_URL}")
        print(f"   Key Service: {cls.KEY_SERVICE_URL}")
        print(f"   Data Collector: {cls.DATA_COLLECTOR_URL}")
        print(f"   Redis: {cls.REDIS_URL}")
        print(f"   Environment: {cls.ENVIRONMENT}")

# Global instance
config = ServiceConfig() 