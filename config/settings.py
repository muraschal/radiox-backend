"""
🚀 RadioX Settings - ULTIMATE CONFIGURATION MANAGEMENT
====================================================

Google Engineering Level Configuration:
- Type-Safe Pydantic Settings
- Environment-Specific Defaults
- Secret Management
- Configuration Validation
- Hot Reloading Support

ELIMINATES ALL REDUNDANT CONFIG LOADING ACROSS 8 MICROSERVICES!

Author: Marcel & Claude - Building the Next Unicorn 🦄
"""

import os
from typing import Optional, Dict, Any, List
from functools import lru_cache
from pathlib import Path
from loguru import logger

from pydantic_settings import BaseSettings
from pydantic import Field, validator, root_validator, AnyHttpUrl
from typing import Union


class DatabaseSettings(BaseSettings):
    """🗄️ Database configuration"""
    
    # Supabase Configuration - Support both old and new env var names
    supabase_url: AnyHttpUrl = Field(default="https://zwcvvbgkqhexfcldwuxq.supabase.co", env="SUPABASE_URL")
    supabase_anon_key: str = Field(default="", env="SUPABASE_ANON_KEY")  
    supabase_service_role_key: Optional[str] = Field(default=None, env="SUPABASE_SERVICE_KEY")
    
    # Connection Pool Settings
    max_connections: int = Field(default=25, env="DB_MAX_CONNECTIONS")
    connection_timeout: float = Field(default=30.0, env="DB_CONNECTION_TIMEOUT")
    
    # Cache Settings
    cache_ttl_seconds: int = Field(default=300, env="DB_CACHE_TTL")  # 5 minutes
    max_cache_size: int = Field(default=1000, env="DB_MAX_CACHE_SIZE")
    
    @validator("supabase_url")
    def validate_supabase_url(cls, v):
        if not str(v).startswith("https://"):
            raise ValueError("Supabase URL must use HTTPS")
        return v
    
    class Config:
        env_prefix = ""


class RedisSettings(BaseSettings):
    """🔴 Redis configuration"""
    
    redis_url: str = Field("redis://localhost:6379", env="REDIS_URL")
    redis_password: Optional[str] = Field(None, env="REDIS_PASSWORD")
    redis_db: int = Field(0, env="REDIS_DB")
    
    # Connection Pool
    max_connections: int = Field(20, env="REDIS_MAX_CONNECTIONS")
    connection_timeout: float = Field(5.0, env="REDIS_CONNECTION_TIMEOUT")
    
    # TTL Settings
    default_ttl: int = Field(3600, env="REDIS_DEFAULT_TTL")  # 1 hour
    
    class Config:
        env_prefix = "REDIS_"


class APISettings(BaseSettings):
    """🔑 API Keys and External Services"""
    
    # OpenAI
    openai_api_key: Optional[str] = Field(None, env="OPENAI_API_KEY")
    openai_model: str = Field("gpt-4o", env="OPENAI_MODEL")
    openai_max_tokens: int = Field(4000, env="OPENAI_MAX_TOKENS")
    openai_temperature: float = Field(0.8, env="OPENAI_TEMPERATURE")
    
    # ElevenLabs
    elevenlabs_api_key: Optional[str] = Field(None, env="ELEVENLABS_API_KEY")
    elevenlabs_model: str = Field("eleven_multilingual_v2", env="ELEVENLABS_MODEL")
    
    # News APIs
    news_api_key: Optional[str] = Field(None, env="NEWS_API_KEY")
    
    # Weather APIs
    weather_api_key: Optional[str] = Field(None, env="WEATHER_API_KEY")
    
    @validator("openai_temperature")
    def validate_temperature(cls, v):
        if not 0.0 <= v <= 2.0:
            raise ValueError("Temperature must be between 0.0 and 2.0")
        return v
    
    class Config:
        env_prefix = "API_"


class ServiceSettings(BaseSettings):
    """🌐 Microservice URLs and Timeouts"""
    
    # Service URLs
    api_gateway_url: AnyHttpUrl = Field("http://localhost:8000", env="API_GATEWAY_URL")
    show_service_url: AnyHttpUrl = Field("http://show-service:8000", env="SHOW_SERVICE_URL")
    content_service_url: AnyHttpUrl = Field("http://content-service:8000", env="CONTENT_SERVICE_URL")
    audio_service_url: AnyHttpUrl = Field("http://audio-service:8000", env="AUDIO_SERVICE_URL")
    media_service_url: AnyHttpUrl = Field("http://media-service:8000", env="MEDIA_SERVICE_URL")
    speaker_service_url: AnyHttpUrl = Field("http://speaker-service:8000", env="SPEAKER_SERVICE_URL")
    data_service_url: AnyHttpUrl = Field("http://data-service:8000", env="DATA_SERVICE_URL")
    analytics_service_url: AnyHttpUrl = Field("http://analytics-service:8000", env="ANALYTICS_SERVICE_URL")
    
    # Timeout Configurations
    fast_timeout: float = Field(5.0, env="FAST_TIMEOUT")          # Health checks
    standard_timeout: float = Field(30.0, env="STANDARD_TIMEOUT") # Normal requests
    slow_timeout: float = Field(120.0, env="SLOW_TIMEOUT")        # Audio processing
    ultra_slow_timeout: float = Field(300.0, env="ULTRA_SLOW_TIMEOUT")  # Show generation
    
    # Retry Configuration
    max_retries: int = Field(3, env="MAX_RETRIES")
    retry_delay_base: float = Field(1.0, env="RETRY_DELAY_BASE")
    
    class Config:
        env_prefix = "SERVICE_"


class SecuritySettings(BaseSettings):
    """🔒 Security and Authentication"""
    
    # JWT Settings
    jwt_secret_key: str = Field("radiox-super-secret-key-change-in-production", env="JWT_SECRET_KEY")
    jwt_algorithm: str = Field("HS256", env="JWT_ALGORITHM")
    jwt_expiration_hours: int = Field(24, env="JWT_EXPIRATION_HOURS")
    
    # CORS Settings
    cors_origins: List[str] = Field(["*"], env="CORS_ORIGINS")
    cors_allow_credentials: bool = Field(True, env="CORS_ALLOW_CREDENTIALS")
    
    # Rate Limiting
    rate_limit_per_minute: int = Field(100, env="RATE_LIMIT_PER_MINUTE")
    
    @validator("cors_origins", pre=True)
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    class Config:
        env_prefix = "SECURITY_"


class LoggingSettings(BaseSettings):
    """📊 Logging and Monitoring"""
    
    log_level: str = Field("INFO", env="LOG_LEVEL")
    log_format: str = Field("json", env="LOG_FORMAT")  # json or text
    log_file_path: Optional[Path] = Field(None, env="LOG_FILE_PATH")
    
    # Performance Monitoring
    enable_metrics: bool = Field(True, env="ENABLE_METRICS")
    metrics_port: int = Field(9090, env="METRICS_PORT")
    
    # Health Check Settings
    health_check_interval: int = Field(30, env="HEALTH_CHECK_INTERVAL")
    
    @validator("log_level")
    def validate_log_level(cls, v):
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of: {valid_levels}")
        return v.upper()
    
    class Config:
        env_prefix = "LOG_"


class EnvironmentSettings(BaseSettings):
    """🌍 Environment-Specific Settings"""
    
    environment: str = Field("development", env="ENVIRONMENT")
    debug: bool = Field(False, env="DEBUG")
    testing: bool = Field(False, env="TESTING")
    
    # Application Info
    app_name: str = Field("RadioX Backend", env="APP_NAME")
    app_version: str = Field("2.0.0", env="APP_VERSION")
    
    # Deployment Info
    deployment_id: Optional[str] = Field(None, env="DEPLOYMENT_ID")
    git_commit: Optional[str] = Field(None, env="GIT_COMMIT")
    build_timestamp: Optional[str] = Field(None, env="BUILD_TIMESTAMP")
    
    @validator("environment")
    def validate_environment(cls, v):
        valid_envs = ["development", "staging", "production"]
        if v.lower() not in valid_envs:
            raise ValueError(f"Environment must be one of: {valid_envs}")
        return v.lower()
    
    @root_validator(skip_on_failure=True)
    def validate_production_settings(cls, values):
        env = values.get("environment")
        debug = values.get("debug")
        
        if env == "production" and debug:
            raise ValueError("Debug mode cannot be enabled in production")
        
        return values
    
    class Config:
        env_prefix = ""  # No prefix needed since we specify env names explicitly


class RadioXSettings(BaseSettings):
    """🚀 Master RadioX Configuration - ULTIMATE SETTINGS"""
    
    # Sub-configurations - Initialize with empty dicts to avoid conflicts
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    api: APISettings = Field(default_factory=APISettings)
    services: ServiceSettings = Field(default_factory=ServiceSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    environment: EnvironmentSettings = Field(default_factory=EnvironmentSettings)
    
    # BACKWARDS COMPATIBILITY - Direct access to nested settings
    @property
    def supabase_url(self) -> str:
        """🔙 Backwards compatibility for supabase_url"""
        return str(self.database.supabase_url)
    
    @property
    def supabase_anon_key(self) -> str:
        """🔙 Backwards compatibility for supabase_anon_key"""
        return self.database.supabase_anon_key
    
    @property
    def supabase_service_role_key(self) -> Optional[str]:
        """🔙 Backwards compatibility for supabase_service_role_key"""
        return self.database.supabase_service_role_key
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "allow"  # Allow extra fields for backwards compatibility
    
    def get_service_url(self, service_name: str) -> str:
        """🎯 Get service URL by name"""
        service_urls = {
            "api-gateway": str(self.services.api_gateway_url),
            "show": str(self.services.show_service_url),
            "content": str(self.services.content_service_url),
            "audio": str(self.services.audio_service_url),
            "media": str(self.services.media_service_url),
            "speaker": str(self.services.speaker_service_url),
            "data": str(self.services.data_service_url),
            "analytics": str(self.services.analytics_service_url)
        }
        
        if service_name not in service_urls:
            raise ValueError(f"Unknown service: {service_name}")
        
        return service_urls[service_name]
    
    def get_timeout_for_request_type(self, request_type: str) -> float:
        """⏱️ Get timeout for request type"""
        timeouts = {
            "fast": self.services.fast_timeout,
            "standard": self.services.standard_timeout,
            "slow": self.services.slow_timeout,
            "ultra_slow": self.services.ultra_slow_timeout
        }
        
        return timeouts.get(request_type, self.services.standard_timeout)
    
    def is_production(self) -> bool:
        """🏭 Check if running in production"""
        return self.environment.environment == "production"
    
    def is_development(self) -> bool:
        """🔧 Check if running in development"""
        return self.environment.environment == "development"
    
    def get_all_api_keys(self) -> Dict[str, Optional[str]]:
        """🔑 Get all API keys (for Data Service)"""
        return {
            "openai": self.api.openai_api_key,
            "elevenlabs": self.api.elevenlabs_api_key,
            "news": self.api.news_api_key,
            "weather": self.api.weather_api_key
        }
    
    def validate_required_keys_for_service(self, service_name: str) -> bool:
        """✅ Validate required API keys for specific service"""
        required_keys = {
            "show": ["openai"],
            "audio": ["elevenlabs"],
            "content": ["news", "weather"],
            "analytics": [],
            "media": [],
            "speaker": [],
            "data": [],
            "api-gateway": []
        }
        
        if service_name not in required_keys:
            return True
        
        api_keys = self.get_all_api_keys()
        missing_keys = []
        
        for key in required_keys[service_name]:
            if not api_keys.get(key):
                missing_keys.append(key)
        
        if missing_keys:
            logger.warning(f"⚠️ Service {service_name} missing API keys: {missing_keys}")
            return False
        
        return True
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """📊 Get performance configuration summary"""
        return {
            "database": {
                "max_connections": self.database.max_connections,
                "cache_ttl": self.database.cache_ttl_seconds,
                "max_cache_size": self.database.max_cache_size
            },
            "redis": {
                "max_connections": self.redis.max_connections,
                "default_ttl": self.redis.default_ttl
            },
            "services": {
                "max_retries": self.services.max_retries,
                "timeouts": {
                    "fast": self.services.fast_timeout,
                    "standard": self.services.standard_timeout,
                    "slow": self.services.slow_timeout,
                    "ultra_slow": self.services.ultra_slow_timeout
                }
            },
            "environment": {
                "name": self.environment.environment,
                "debug": self.environment.debug,
                "version": self.environment.app_version
            }
        }


@lru_cache()
def get_settings() -> RadioXSettings:
    """🎯 Get cached settings instance - SINGLETON PATTERN"""
    try:
        settings = RadioXSettings()
        logger.info(f"🚀 Settings loaded for environment: {settings.environment.environment}")
        return settings
    except Exception as e:
        logger.error(f"❌ Failed to load settings: {e}")
        raise


def reload_settings() -> RadioXSettings:
    """🔄 Force reload settings (clears cache)"""
    get_settings.cache_clear()
    return get_settings()


# 🎯 CONVENIENCE FUNCTIONS

def get_database_config() -> DatabaseSettings:
    """Get database configuration"""
    return get_settings().database


def get_redis_config() -> RedisSettings:
    """Get Redis configuration"""
    return get_settings().redis


def get_api_config() -> APISettings:
    """Get API configuration"""
    return get_settings().api


def get_service_config() -> ServiceSettings:
    """Get service configuration"""
    return get_settings().services


def is_production() -> bool:
    """Check if running in production"""
    return get_settings().is_production()


def is_development() -> bool:
    """Check if running in development"""
    return get_settings().is_development()


# 🚀 INITIALIZE SETTINGS ON IMPORT
try:
    _settings = get_settings()
    logger.info("🦄 RADIOX SETTINGS INITIALIZED - READY FOR UNICORN CONFIGURATION!")
except Exception as e:
    logger.error(f"💥 Settings initialization failed: {e}")
    raise 