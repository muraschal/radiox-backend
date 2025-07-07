"""
🚀 RadioX Simple Settings - Quick Fix for Environment Variables
Author: Marcel & Claude - Building the Next Unicorn 🦄
"""

import os
from typing import Optional


class SimpleSettings:
    """Simple settings that just read environment variables"""
    
    def __init__(self):
        # Database settings
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_anon_key = os.getenv("SUPABASE_ANON_KEY")
        self.supabase_service_key = os.getenv("SUPABASE_SERVICE_KEY")
        
        # Redis settings
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        
        # Environment
        self.environment = os.getenv("ENVIRONMENT", "development")
        
        # Validate required settings
        if not self.supabase_url:
            raise ValueError("SUPABASE_URL is required")
        if not self.supabase_anon_key:
            raise ValueError("SUPABASE_ANON_KEY is required")


# Global instance
_settings = None

def get_simple_settings() -> SimpleSettings:
    """Get simple settings instance"""
    global _settings
    if _settings is None:
        _settings = SimpleSettings()
    return _settings 