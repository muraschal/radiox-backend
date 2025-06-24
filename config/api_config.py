#!/usr/bin/env python3
"""Central API Configuration for RadioX Backend

Eliminates ALL hardcoded API URLs, model names, and service configurations.
All external API configurations are centralized here.
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional
from .settings import get_settings

@dataclass(frozen=True)
class APIEndpoints:
    """Centralized API endpoint configuration"""
    
    # ElevenLabs API
    elevenlabs_base: str = "https://api.elevenlabs.io/v1"
    elevenlabs_models: str = "https://api.elevenlabs.io/v1/models"
    elevenlabs_voices: str = "https://api.elevenlabs.io/v1/voices"
    
    # OpenAI API
    openai_base: str = "https://api.openai.com/v1"
    openai_chat: str = "https://api.openai.com/v1/chat/completions"
    openai_images: str = "https://api.openai.com/v1/images/generations"
    openai_models: str = "https://api.openai.com/v1/models"
    
    # Weather API
    openweather_base: str = "https://api.openweathermap.org/data/2.5"
    openweather_current: str = "https://api.openweathermap.org/data/2.5/weather"
    openweather_forecast: str = "https://api.openweathermap.org/data/2.5/forecast"

@dataclass(frozen=True)
class ModelConfiguration:
    """Centralized model configuration - NO hardcoded model names"""
    
    # GPT Models (from environment or database)
    default_gpt_model: str = "gpt-4"  # Can be overridden by settings
    fallback_gpt_model: str = "gpt-3.5-turbo"
    
    # ElevenLabs Default Model (fallback only - prefer database)
    default_elevenlabs_model: str = "eleven_turbo_v2"
    
    # Image Generation Models
    default_dalle_model: str = "dall-e-3"
    fallback_dalle_model: str = "dall-e-2"

@dataclass(frozen=True)
class SystemCategories:
    """Minimal system configuration - let database extend these"""
    
    # Only ESSENTIAL categories - everything else from database
    ESSENTIAL_CATEGORIES = [
        "weather",  # Core weather functionality
        "news"      # Core news functionality  
        # NO "crypto", "sports" etc. - those come from database!
    ]
    
    # Essential speaker roles only
    ESSENTIAL_SPEAKER_ROLES = [
        "primary_speaker",
        "weather_speaker"  
        # Additional roles come from database configuration
    ]
    
    # Core languages - additional ones from database
    ESSENTIAL_LANGUAGES = [
        "en",
        "de"
        # Additional languages from database
    ]

@dataclass(frozen=True)
class APIConfiguration:
    """Master API configuration - replaces ALL hardcoded values"""
    
    endpoints: APIEndpoints
    models: ModelConfiguration  
    categories: SystemCategories
    
    # Timeout configurations
    default_timeout: int = 30
    long_timeout: int = 180
    
    # Retry configurations
    max_retries: int = 3
    retry_delay: float = 1.0

def get_api_config() -> APIConfiguration:
    """
    Get centralized API configuration
    
    Returns:
        Complete API configuration with all endpoints and settings
    """
    settings = get_settings()
    
    # Allow environment overrides for model names
    models = ModelConfiguration(
        default_gpt_model=getattr(settings, 'default_gpt_model', 'gpt-4'),
        fallback_gpt_model=getattr(settings, 'fallback_gpt_model', 'gpt-3.5-turbo'),
        default_elevenlabs_model=getattr(settings, 'default_elevenlabs_model', 'eleven_turbo_v2'),
        default_dalle_model=getattr(settings, 'default_dalle_model', 'dall-e-3'),
        fallback_dalle_model=getattr(settings, 'fallback_dalle_model', 'dall-e-2')
    )
    
    return APIConfiguration(
        endpoints=APIEndpoints(),
        models=models,
        categories=SystemCategories()
    )

# Singleton instance  
_api_config: Optional[APIConfiguration] = None

def get_api_configuration() -> APIConfiguration:
    """Get singleton API configuration instance"""
    global _api_config
    if _api_config is None:
        _api_config = get_api_config()
    return _api_config

# Convenience functions to replace hardcoded values
def get_elevenlabs_base_url() -> str:
    """Replace hardcoded 'https://api.elevenlabs.io/v1'"""
    return get_api_configuration().endpoints.elevenlabs_base

def get_openai_images_url() -> str:
    """Replace hardcoded 'https://api.openai.com/v1/images/generations'"""
    return get_api_configuration().endpoints.openai_images

def get_openai_chat_url() -> str:
    """Replace hardcoded 'https://api.openai.com/v1/chat/completions'"""
    return get_api_configuration().endpoints.openai_chat

def get_default_gpt_model() -> str:
    """Replace hardcoded 'gpt-4'"""
    return get_api_configuration().models.default_gpt_model

def get_default_elevenlabs_model() -> str:
    """Get default ElevenLabs model dynamically from database - replaces hardcoded 'eleven_turbo_v2'"""
    try:
        # Try to load from database first
        from pathlib import Path
        import sys
        sys.path.append(str(Path(__file__).parent.parent / "src"))
        from services.infrastructure.supabase_service import SupabaseService
        
        db = SupabaseService()
        
        # Get best mid-quality model (most balanced for default use)
        result = db.client.table('elevenlabs_models').select('model_id').eq('quality_tier', 'mid').eq('is_active', True).order('latency_ms', desc=False).limit(1).execute()
        
        if result.data and len(result.data) > 0:
            return result.data[0]['model_id']
            
    except Exception:
        # Silent fallback to prevent initialization issues
        pass
    
    # Ultimate fallback for bootstrap scenarios
    return get_api_configuration().models.default_elevenlabs_model

def get_content_categories() -> list[str]:
    """Get essential categories - database can extend these"""
    return get_api_configuration().categories.ESSENTIAL_CATEGORIES.copy()

def get_speaker_roles() -> list[str]:
    """Get essential speaker roles - database can extend these"""
    return get_api_configuration().categories.ESSENTIAL_SPEAKER_ROLES.copy()

def get_supported_languages() -> list[str]:
    """Get essential languages - database can extend these"""
    return get_api_configuration().categories.ESSENTIAL_LANGUAGES.copy() 