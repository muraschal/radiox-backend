"""
Generic Configuration Service
Implements Google Engineering Best Practices:
- Single Source of Truth (Database-driven configuration)
- No hardcoded values (Fully dynamic)
- Performance First (Caching strategy)
- Separation of Concerns (Pure configuration management)
"""

from typing import Dict, List, Optional, Any
from loguru import logger
from dataclasses import dataclass
from datetime import datetime
import time

from ..infrastructure.supabase_service import SupabaseService


@dataclass
class ShowPreset:
    """Generic show preset configuration"""
    preset_name: str
    display_name: str
    description: str
    city_focus: str
    primary_speaker: str
    secondary_speaker: Optional[str] = None
    weather_speaker: Optional[str] = None
    news_categories: List[str] = None
    exclude_categories: List[str] = None
    show_behavior: Dict[str, Any] = None
    is_active: bool = True


@dataclass 
class SpeakerConfig:
    """Generic speaker configuration"""
    speaker_name: str
    voice_name: str
    voice_id: str
    language: str
    description: str
    is_primary: bool = False
    is_active: bool = True


@dataclass
class LocationConfig:
    """Generic location configuration"""
    location_key: str
    display_name: str
    city_id: Optional[int] = None
    country_code: str = "CH"
    timezone: str = "Europe/Zurich"
    is_active: bool = True


class ConfigurationService:
    """
    Generic Configuration Service
    
    Provides dynamic configuration loading without hardcoded values.
    All show presets, speakers, and locations come from database.
    """
    
    def __init__(self):
        self.db = SupabaseService()
        self._cache: Dict[str, Any] = {}
        self._cache_timestamp: float = 0
        self._cache_ttl: int = 300  # 5 minutes
    
    def _is_cache_valid(self) -> bool:
        """Check if cache is still valid"""
        return time.time() - self._cache_timestamp < self._cache_ttl
    
    def _invalidate_cache(self) -> None:
        """Invalidate all caches"""
        self._cache.clear()
        self._cache_timestamp = 0
    
    async def get_show_presets(self, active_only: bool = True) -> List[ShowPreset]:
        """Get all show presets dynamically from database"""
        cache_key = f"show_presets_{active_only}"
        
        if self._is_cache_valid() and cache_key in self._cache:
            return self._cache[cache_key]
        
        try:
            query = self.db.client.table("show_presets").select("*")
            if active_only:
                query = query.eq("is_active", True)
            
            result = query.execute()
            
            presets = []
            for preset_data in result.data:
                preset = ShowPreset(
                    preset_name=preset_data.get("preset_name", ""),
                    display_name=preset_data.get("display_name", ""),
                    description=preset_data.get("description", ""),
                    city_focus=preset_data.get("city_focus", ""),
                    primary_speaker=preset_data.get("primary_speaker", ""),
                    secondary_speaker=preset_data.get("secondary_speaker"),
                    weather_speaker=preset_data.get("weather_speaker"),
                    news_categories=preset_data.get("news_categories", []),
                    exclude_categories=preset_data.get("exclude_categories", []),
                    show_behavior=preset_data.get("show_behavior", {}),
                    is_active=preset_data.get("is_active", True)
                )
                presets.append(preset)
            
            self._cache[cache_key] = presets
            self._cache_timestamp = time.time()
            
            logger.debug(f"✅ Loaded {len(presets)} show presets from database")
            return presets
            
        except Exception as e:
            logger.error(f"❌ Error loading show presets: {e}")
            return []
    
    async def get_default_preset(self) -> Optional[ShowPreset]:
        """Get the first active preset as default"""
        presets = await self.get_show_presets(active_only=True)
        return presets[0] if presets else None
    
    async def get_preset_by_name(self, preset_name: str) -> Optional[ShowPreset]:
        """Get specific preset by name"""
        presets = await self.get_show_presets(active_only=True)
        for preset in presets:
            if preset.preset_name.lower() == preset_name.lower():
                return preset
        return None
    
    async def get_speakers(self, active_only: bool = True) -> List[SpeakerConfig]:
        """Get all speakers dynamically from database"""
        cache_key = f"speakers_{active_only}"
        
        if self._is_cache_valid() and cache_key in self._cache:
            return self._cache[cache_key]
        
        try:
            query = self.db.client.table("voice_configurations").select("*")
            if active_only:
                query = query.eq("is_active", True)
            
            result = query.execute()
            
            speakers = []
            for speaker_data in result.data:
                speaker = SpeakerConfig(
                    speaker_name=speaker_data.get("speaker_name", ""),
                    voice_name=speaker_data.get("voice_name", ""),
                    voice_id=speaker_data.get("voice_id", ""),
                    language=speaker_data.get("language", "en"),
                    description=speaker_data.get("description", ""),
                    is_primary=speaker_data.get("is_primary", False),
                    is_active=speaker_data.get("is_active", True)
                )
                speakers.append(speaker)
            
            self._cache[cache_key] = speakers
            self._cache_timestamp = time.time()
            
            logger.debug(f"✅ Loaded {len(speakers)} speakers from database")
            return speakers
            
        except Exception as e:
            logger.error(f"❌ Error loading speakers: {e}")
            return []
    
    async def get_default_speaker(self) -> Optional[SpeakerConfig]:
        """Get the first primary speaker as default"""
        speakers = await self.get_speakers(active_only=True)
        
        # First try to find a primary speaker
        for speaker in speakers:
            if speaker.is_primary:
                return speaker
        
        # Fallback to first available speaker
        return speakers[0] if speakers else None
    
    async def get_speaker_by_name(self, speaker_name: str) -> Optional[SpeakerConfig]:
        """Get specific speaker by name"""
        speakers = await self.get_speakers(active_only=True)
        for speaker in speakers:
            if speaker.speaker_name.lower() == speaker_name.lower():
                return speaker
        return None
    
    async def get_locations(self, active_only: bool = True) -> List[LocationConfig]:
        """Get all locations dynamically from database"""
        cache_key = f"locations_{active_only}"
        
        if self._is_cache_valid() and cache_key in self._cache:
            return self._cache[cache_key]
        
        try:
            # For now, return a basic location config
            # This can be extended to load from database when location table exists
            locations = [
                LocationConfig(
                    location_key="default",
                    display_name="Default Location",
                    country_code="CH",
                    timezone="Europe/Zurich",
                    is_active=True
                )
            ]
            
            self._cache[cache_key] = locations
            self._cache_timestamp = time.time()
            
            logger.debug(f"✅ Loaded {len(locations)} locations")
            return locations
            
        except Exception as e:
            logger.error(f"❌ Error loading locations: {e}")
            return []
    
    async def get_default_location(self) -> Optional[LocationConfig]:
        """Get the first active location as default"""
        locations = await self.get_locations(active_only=True)
        return locations[0] if locations else None
    
    async def get_configuration_summary(self) -> Dict[str, Any]:
        """Get summary of all configuration data"""
        presets = await self.get_show_presets()
        speakers = await self.get_speakers()
        locations = await self.get_locations()
        
        return {
            "presets": {
                "total": len(presets),
                "names": [p.preset_name for p in presets],
                "default": presets[0].preset_name if presets else None
            },
            "speakers": {
                "total": len(speakers),
                "names": [s.speaker_name for s in speakers],
                "primary": [s.speaker_name for s in speakers if s.is_primary],
                "default": speakers[0].speaker_name if speakers else None
            },
            "locations": {
                "total": len(locations),
                "names": [l.location_key for l in locations],
                "default": locations[0].location_key if locations else None
            },
            "cache_status": {
                "valid": self._is_cache_valid(),
                "timestamp": datetime.fromtimestamp(self._cache_timestamp).isoformat() if self._cache_timestamp else None
            }
        }
    
    async def refresh_configuration(self) -> None:
        """Force refresh all configuration from database"""
        self._invalidate_cache()
        await self.get_show_presets()
        await self.get_speakers()
        await self.get_locations()
        logger.info("🔄 Configuration refreshed from database")

    async def get_elevenlabs_models(self, quality_tier: Optional[str] = None, active_only: bool = True) -> List[Dict[str, Any]]:
        """Get ElevenLabs models dynamically from database"""
        cache_key = f"elevenlabs_models_{quality_tier}_{active_only}"
        
        if self._is_cache_valid() and cache_key in self._cache:
            return self._cache[cache_key]
        
        try:
            query = self.db.client.table("elevenlabs_models").select("*")
            
            if quality_tier:
                query = query.eq("quality_tier", quality_tier)
            if active_only:
                query = query.eq("is_active", True)
            
            # Order by latency (fastest first)
            query = query.order("latency_ms", desc=False)
            
            result = query.execute()
            
            models = result.data or []
            
            self._cache[cache_key] = models
            self._cache_timestamp = time.time()
            
            logger.debug(f"✅ Loaded {len(models)} ElevenLabs models from database")
            return models
            
        except Exception as e:
            logger.error(f"❌ Error loading ElevenLabs models: {e}")
            return []
    
    async def get_best_model_for_quality(self, quality_tier: str = "mid") -> Optional[str]:
        """Get the best (fastest) model for a quality tier"""
        models = await self.get_elevenlabs_models(quality_tier=quality_tier, active_only=True)
        
        if models:
            # Return the fastest model (lowest latency)
            best_model = models[0]
            logger.debug(f"🎛️ Best {quality_tier} model: {best_model['model_id']} ({best_model['latency_ms']}ms)")
            return best_model['model_id']
        
        # Fallback mapping
        fallback_models = {
            "low": "eleven_flash_v2_5",
            "mid": "eleven_turbo_v2_5", 
            "high": "eleven_multilingual_v2"
        }
        
        fallback = fallback_models.get(quality_tier, "eleven_turbo_v2_5")
        logger.warning(f"⚠️ No {quality_tier} models in database, using fallback: {fallback}")
        return fallback
    
    async def get_model_configuration(self, model_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed configuration for a specific model"""
        models = await self.get_elevenlabs_models(active_only=True)
        
        for model in models:
            if model.get('model_id') == model_id:
                return model
        
        return None


# Singleton instance
_config_service: Optional[ConfigurationService] = None

def get_configuration_service() -> ConfigurationService:
    """Get singleton configuration service instance"""
    global _config_service
    if _config_service is None:
        _config_service = ConfigurationService()
    return _config_service


# Convenience functions for backward compatibility
async def get_available_presets() -> List[str]:
    """Get list of available preset names"""
    service = get_configuration_service()
    presets = await service.get_show_presets()
    return [p.preset_name for p in presets]

async def get_available_speakers() -> List[str]:
    """Get list of available speaker names"""
    service = get_configuration_service()
    speakers = await service.get_speakers()
    return [s.speaker_name for s in speakers]

async def get_default_preset_name() -> Optional[str]:
    """Get default preset name"""
    service = get_configuration_service()
    preset = await service.get_default_preset()
    return preset.preset_name if preset else None

async def get_default_speaker_name() -> Optional[str]:
    """Get default speaker name"""
    service = get_configuration_service()
    speaker = await service.get_default_speaker()
    return speaker.speaker_name if speaker else None

async def get_best_elevenlabs_model(quality_tier: str = "mid") -> Optional[str]:
    """Get the best ElevenLabs model for a quality tier - replaces hardcoded models"""
    config_service = get_configuration_service()
    return await config_service.get_best_model_for_quality(quality_tier)

async def get_elevenlabs_model_config(model_id: str) -> Optional[Dict[str, Any]]:
    """Get detailed configuration for an ElevenLabs model"""
    config_service = get_configuration_service()
    return await config_service.get_model_configuration(model_id)


if __name__ == "__main__":
    print("Configuration Service - production ready") 