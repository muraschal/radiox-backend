#!/usr/bin/env python3
"""Show Service - HIGH PERFORMANCE CONFIGURATION ENGINE

Google Engineering Best Practices:
- Single Responsibility (Show configuration management)
- Dependency Injection (Database abstraction)
- Performance Optimization (Caching, lazy loading)
- Error Handling (Graceful degradation)
- Resource Management (Memory efficient)
"""

import asyncio
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field
from loguru import logger

# Database import
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))
from database.supabase_client import get_db


@dataclass(frozen=True)
class ShowConfiguration:
    """Immutable show configuration with performance optimization"""
    
    # Core configuration
    preset_name: str
    display_name: str
    description: str
    city_focus: str
    primary_speaker: str
    
    # Optional configuration
    secondary_speaker: Optional[str] = None
    weather_speaker: Optional[str] = None
    rss_feed_filter: Dict[str, Any] = field(default_factory=dict)
    news_categories: List[str] = field(default_factory=list)
    exclude_categories: List[str] = field(default_factory=list)
    show_behavior: Dict[str, Any] = field(default_factory=dict)
    
    # Metadata
    min_priority: int = 5
    max_feeds_per_category: int = 10
    is_active: bool = True
    preset_id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    @property
    def is_duo_show(self) -> bool:
        """Check if this is a duo show"""
        return self.secondary_speaker is not None
    
    @property
    def speaker_count(self) -> int:
        """Get number of speakers"""
        return 2 if self.secondary_speaker else 1
    
    @property
    def all_speakers(self) -> Tuple[str, ...]:
        """Get all speakers as immutable tuple"""
        speakers = [self.primary_speaker]
        if self.secondary_speaker:
            speakers.append(self.secondary_speaker)
        return tuple(speakers)


class ShowService:
    """High-Performance Show Configuration Engine
    
    Implements Google Engineering Best Practices:
    - Single Responsibility (Configuration management)
    - Performance First (Caching, lazy loading)
    - Resource Management (Efficient database usage)
    - Error Handling (Graceful degradation)
    """
    
    __slots__ = ('_db', '_show_cache', '_speaker_cache', '_cache_timestamp', '_cache_ttl')
    
    def __init__(self):
        self._db = None  # Lazy loading
        self._show_cache = {}
        self._speaker_cache = {}
        self._cache_timestamp = None
        self._cache_ttl = 300  # 5 minutes
        
        logger.info("🎭 Show Service initialisiert")
    
    @property
    def db(self):
        """Lazy database connection"""
        if self._db is None:
            self._db = get_db()
        return self._db
    
    def _is_cache_valid(self) -> bool:
        """Check if cache is still valid"""
        if not self._cache_timestamp:
            return False
        return (datetime.now() - self._cache_timestamp).total_seconds() < self._cache_ttl
    
    def _invalidate_cache(self) -> None:
        """Invalidate all caches"""
        self._show_cache.clear()
        self._speaker_cache.clear()
        self._cache_timestamp = None
    
    async def get_show_preset(self, preset_name: str) -> Optional[ShowConfiguration]:
        """Get show preset with caching"""
        logger.info(f"🎭 Lade Show-Preset: {preset_name}")
        
        # Check cache first
        if self._is_cache_valid() and preset_name in self._show_cache:
            logger.debug(f"📋 Cache hit for preset: {preset_name}")
            return self._show_cache[preset_name]
        
        try:
            response = await asyncio.to_thread(
                lambda: self.db.client.table("show_presets")
                .select("*")
                .eq("preset_name", preset_name)
                .execute()
            )
            
            if not response.data:
                logger.warning(f"⚠️ Show-Preset '{preset_name}' nicht gefunden")
                return None
            
            config = self._convert_to_show_config(response.data[0])
            
            # Update cache
            self._show_cache[preset_name] = config
            self._cache_timestamp = datetime.now()
            
            logger.info(f"✅ Show-Preset '{preset_name}' geladen: {config.display_name}")
            return config
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden des Show-Presets '{preset_name}': {e}")
            return None
    
    async def get_all_show_presets(self, active_only: bool = True) -> List[ShowConfiguration]:
        """Get all show presets with caching"""
        cache_key = f"all_presets_{active_only}"
        
        if self._is_cache_valid() and cache_key in self._show_cache:
            logger.debug(f"📋 Cache hit for all presets")
            return self._show_cache[cache_key]
        
        try:
            query_func = lambda: (
                self.db.client.table("show_presets")
                .select("*")
                .eq("is_active", True) if active_only 
                else self.db.client.table("show_presets").select("*")
            ).order("display_name").execute()
            
            response = await asyncio.to_thread(query_func)
            
            if not response.data:
                logger.warning("⚠️ Keine Show-Presets gefunden")
                return []
            
            # Convert to configurations efficiently
            show_configs = [self._convert_to_show_config(data) for data in response.data]
            
            # Update cache
            self._show_cache[cache_key] = show_configs
            self._cache_timestamp = datetime.now()
            
            logger.info(f"✅ {len(show_configs)} Show-Presets geladen")
            return show_configs
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden der Show-Presets: {e}")
            return []
    
    async def get_speaker_configuration(self, speaker_name: str) -> Optional[Dict[str, Any]]:
        """Get speaker configuration with caching"""
        logger.info(f"🎤 Lade Sprecher-Konfiguration: {speaker_name}")
        
        # Check cache first
        if self._is_cache_valid() and speaker_name in self._speaker_cache:
            logger.debug(f"📋 Cache hit for speaker: {speaker_name}")
            return self._speaker_cache[speaker_name]
        
        try:
            response = await asyncio.to_thread(
                lambda: self.db.client.table("voice_configurations")
                .select("*")
                .eq("voice_name", speaker_name.title())
                .eq("is_active", True)
                .execute()
            )
            
            if not response.data:
                logger.warning(f"⚠️ Sprecher '{speaker_name}' nicht gefunden")
                return None
            
            speaker_config = response.data[0]
            
            # Update cache
            self._speaker_cache[speaker_name] = speaker_config
            self._cache_timestamp = datetime.now()
            
            logger.info(f"✅ Sprecher-Konfiguration geladen: {speaker_config['voice_name']}")
            return speaker_config
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden der Sprecher-Konfiguration '{speaker_name}': {e}")
            return None
    
    async def prepare_show_generation(self, preset_name: str) -> Optional[Dict[str, Any]]:
        """Prepare complete show generation configuration"""
        logger.info(f"🎬 Bereite Show-Generierung vor: {preset_name}")
        
        try:
            # Load show preset
            show_config = await self.get_show_preset(preset_name)
            if not show_config:
                return None
            
            # Load speaker configurations in parallel
            speaker_tasks = [
                self.get_speaker_configuration(show_config.primary_speaker)
            ]
            
            if show_config.secondary_speaker:
                speaker_tasks.append(
                    self.get_speaker_configuration(show_config.secondary_speaker)
                )
            
            if show_config.weather_speaker:
                speaker_tasks.append(
                    self.get_speaker_configuration(show_config.weather_speaker)
                )
            
            speaker_configs = await asyncio.gather(*speaker_tasks, return_exceptions=True)
            
            # Process speaker configurations
            primary_speaker = speaker_configs[0] if not isinstance(speaker_configs[0], Exception) else None
            secondary_speaker = None
            weather_speaker = None
            
            # Determine which configs correspond to which speakers
            config_index = 1
            if show_config.secondary_speaker and len(speaker_configs) > config_index:
                secondary_speaker = speaker_configs[config_index] if not isinstance(speaker_configs[config_index], Exception) else None
                config_index += 1
            
            if show_config.weather_speaker and len(speaker_configs) > config_index:
                weather_speaker = speaker_configs[config_index] if not isinstance(speaker_configs[config_index], Exception) else None
            
            if not primary_speaker:
                logger.error(f"❌ Primary speaker configuration missing for {show_config.primary_speaker}")
                return None
            
            # Create comprehensive show generation config
            generation_config = {
                "show": {
                    "preset_name": show_config.preset_name,
                    "display_name": show_config.display_name,
                    "description": show_config.description,
                    "city_focus": show_config.city_focus,
                    "is_duo_show": show_config.is_duo_show
                },
                "speaker": primary_speaker,
                "secondary_speaker": secondary_speaker,
                "weather_speaker": weather_speaker,
                "content": {
                    "categories": show_config.news_categories,
                    "exclude_categories": show_config.exclude_categories,
                    "min_priority": show_config.min_priority,
                    "max_feeds_per_category": show_config.max_feeds_per_category,
                    "rss_filter": show_config.rss_feed_filter
                },
                "behavior": show_config.show_behavior,
                "generation_timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"✅ Show-Generierung vorbereitet für '{show_config.display_name}'")
            logger.info(f"   🎤 Primary Sprecher: {primary_speaker['voice_name']} ({primary_speaker['language']})")
            if secondary_speaker:
                logger.info(f"   🎤 Secondary Sprecher: {secondary_speaker['voice_name']} ({secondary_speaker['language']})")
            if weather_speaker:
                logger.info(f"   🌤️ Weather Sprecher: {weather_speaker['voice_name']} ({weather_speaker['language']})")
            logger.info(f"   🏙️ Stadt-Fokus: {show_config.city_focus}")
            logger.info(f"   📰 Kategorien: {', '.join(show_config.news_categories)}")
            
            return generation_config
            
        except Exception as e:
            logger.error(f"❌ Fehler bei Show-Generierung Vorbereitung: {e}")
            return None
    
    def _convert_to_show_config(self, preset_data: Dict[str, Any]) -> ShowConfiguration:
        """Convert database data to ShowConfiguration efficiently"""
        return ShowConfiguration(
            preset_name=preset_data.get("preset_name", ""),
            display_name=preset_data.get("display_name", ""),
            description=preset_data.get("description", ""),
            city_focus=preset_data.get("city_focus", ""),
            primary_speaker=preset_data.get("primary_speaker", "marcel"),
            secondary_speaker=preset_data.get("secondary_speaker"),
            weather_speaker=preset_data.get("weather_speaker"),

            rss_feed_filter=preset_data.get("rss_feed_filter", {}),
            news_categories=preset_data.get("news_categories", []),
            exclude_categories=preset_data.get("exclude_categories", []),
            show_behavior=preset_data.get("show_behavior", {}),
            min_priority=preset_data.get("min_priority", 5),
            max_feeds_per_category=preset_data.get("max_feeds_per_category", 10),
            is_active=preset_data.get("is_active", True),
            preset_id=preset_data.get("id"),
            created_at=self._parse_datetime(preset_data.get("created_at")),
            updated_at=self._parse_datetime(preset_data.get("updated_at"))
        )
    
    def _parse_datetime(self, dt_str: Optional[str]) -> Optional[datetime]:
        """Parse datetime string safely"""
        if not dt_str:
            return None
        try:
            return datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        except:
            return None
    
    async def get_show_statistics(self) -> Dict[str, Any]:
        """Get show service statistics"""
        try:
            all_presets = await self.get_all_show_presets(active_only=False)
            active_presets = [p for p in all_presets if p.is_active]
            
            return {
                "total_presets": len(all_presets),
                "active_presets": len(active_presets),
                "cache_size": len(self._show_cache) + len(self._speaker_cache),
                "cache_valid": self._is_cache_valid(),
                "available_presets": [p.preset_name for p in active_presets]
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    async def invalidate_cache(self) -> None:
        """Public method to invalidate cache"""
        self._invalidate_cache()
        logger.info("🗑️ Show service cache invalidated")


# Singleton instance for global access
_show_service_instance = None

async def get_show_service() -> ShowService:
    """Get singleton show service instance"""
    global _show_service_instance
    if _show_service_instance is None:
        _show_service_instance = ShowService()
    return _show_service_instance

async def get_show_for_generation(preset_name: str) -> Optional[Dict[str, Any]]:
    """Convenience function for show generation"""
    service = await get_show_service()
    return await service.prepare_show_generation(preset_name)

async def test_show_service() -> bool:
    """Test show service functionality"""
    try:
        service = await get_show_service()
        
        # Test preset loading
        zurich_config = await service.get_show_preset("zurich")
        if not zurich_config:
            return False
        
        # Test speaker loading
        marcel_config = await service.get_speaker_configuration("marcel")
        if not marcel_config:
            return False
        
        # Test show generation preparation
        generation_config = await service.prepare_show_generation("zurich")
        if not generation_config:
            return False
        
        return True
        
    except Exception:
        return False


if __name__ == "__main__":
    asyncio.run(test_show_service()) 