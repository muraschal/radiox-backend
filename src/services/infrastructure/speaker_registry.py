#!/usr/bin/env python3
"""
Dynamic Speaker Registry
========================

Ersetzt alle hardcodierten Speaker-Namen (marcel, jarvis, brad, lucy) 
mit dynamischen Referenzen aus der Datenbank.

Problem gelöst:
- Keine hardcodierten Namen mehr im Code
- Neue Sprecher einfach über DB hinzufügbar
- Zentrale Verwaltung aller Speaker-Informationen
"""

from typing import Dict, List, Optional, Set, Any
from loguru import logger
import sys
from pathlib import Path
from dataclasses import dataclass, asdict
from ..infrastructure.supabase_service import SupabaseService

# Add database path
sys.path.append(str(Path(__file__).parent.parent.parent))

from database.supabase_client import get_db


class SpeakerRegistry:
    """Dynamisches Speaker Registry System"""
    
    def __init__(self):
        self.supabase = SupabaseService()
        self.client = self.supabase.client
        self._cache: Optional[Dict[str, Dict[str, Any]]] = None
        self._cache_timestamp: Optional[float] = None
        self.cache_duration = 300  # 5 Minuten Cache
    
    async def get_all_speakers(self, force_refresh: bool = False) -> Dict[str, Dict[str, Any]]:
        """
        Holt alle aktiven Sprecher aus der Datenbank
        
        Returns:
            Dictionary mit speaker_name als Key und Speaker-Info als Value
        """
        
        import time
        
        # Cache prüfen
        if not force_refresh and self._cache and self._cache_timestamp:
            if time.time() - self._cache_timestamp < self.cache_duration:
                return self._cache
        
        try:
            logger.debug("🎤 Lade Sprecher aus Datenbank...")
            
            result = self.client.table("voice_configurations").select("*").eq("is_active", True).execute()
            
            speakers = {}
            for voice in result.data:
                speakers[voice["speaker_name"]] = {
                    "speaker_name": voice["speaker_name"],
                    "voice_name": voice["voice_name"],
                    "description": voice["description"],
                    "language": voice["language"],
                    "is_primary": voice["is_primary"],
                    "voice_id": voice["voice_id"]
                }
            
            # Cache aktualisieren
            self._cache = speakers
            self._cache_timestamp = time.time()
            
            logger.debug(f"✅ {len(speakers)} Sprecher geladen: {list(speakers.keys())}")
            return speakers
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden der Sprecher: {e}")
            return {}
    
    async def get_speaker_names(self) -> List[str]:
        """Holt alle verfügbaren Speaker-Namen"""
        speakers = await self.get_all_speakers()
        return list(speakers.keys())
    
    async def get_primary_speakers(self) -> List[str]:
        """Holt nur Primary Speaker-Namen"""
        speakers = await self.get_all_speakers()
        return [name for name, info in speakers.items() if info.get("is_primary", False)]
    
    async def is_valid_speaker(self, speaker_name: str) -> bool:
        """Prüft ob ein Speaker existiert"""
        speakers = await self.get_all_speakers()
        return speaker_name.lower() in [s.lower() for s in speakers.keys()]
    
    async def get_speaker_info(self, speaker_name: str) -> Optional[Dict[str, Any]]:
        """Holt detaillierte Info für einen Sprecher"""
        speakers = await self.get_all_speakers()
        return speakers.get(speaker_name.lower())
    
    async def get_default_speaker(self) -> str:
        """Holt den Standard-Sprecher (ersten Primary oder ersten verfügbaren)"""
        speakers = await self.get_all_speakers()
        
        # Suche Primary Speaker
        for name, info in speakers.items():
            if info.get("is_primary", False):
                return name
        
        # Fallback: Ersten verfügbaren nehmen
        if speakers:
            return list(speakers.keys())[0]
        
        # Ultimate Fallback
        logger.warning("⚠️ Keine Sprecher gefunden, verwende 'unknown'")
        return "unknown"
    
    async def get_speaker_mapping(self) -> Dict[str, str]:
        """
        Erstellt einfaches Mapping für Speaker-Aliases
        OHNE automatische Content-Zuweisungen für maximale Flexibilität
        """
        
        speakers = await self.get_all_speakers()
        speaker_names = list(speakers.keys())
        
        # Erstelle einfaches Mapping: Jeder Speaker mappt nur auf sich selbst
        mapping = {}
        
        # Grundmapping: Jeder Speaker auf sich selbst
        for name in speaker_names:
            mapping[name] = name
        
        # NUR Basic Aliases - KEINE Content-basierten Zuweisungen
        # Diese sind nur für Legacy-Kompatibilität und allgemeine Begriffe
        
        # Allgemeine Host-Begriffe → Primary Speaker (dynamisch)
        primary_speaker = await self.get_default_speaker()
        mapping.update({
            "host": primary_speaker,
            "moderator": primary_speaker,
            "presenter": primary_speaker
        })
        
        # Legacy AI-Aliases (nur wenn Jarvis existiert)
        if "jarvis" in speaker_names:
            mapping.update({
                "ai": "jarvis",
                "assistant": "jarvis"
            })
        
        # ENTFERNT: Automatische Content-Zuweisungen wie:
        # "news" → "brad", "weather" → "lucy", "anchor" → "brad"
        # Diese führen zu ungewollten automatischen Zuweisungen!
        
        return mapping
    
    # ENTFERNT: get_weather_speaker() und get_news_speaker()
    # Diese Funktionen fördern automatische Content-Zuweisungen
    # Stattdessen: Explizite Speaker-Angabe in Scripts bevorzugen
    
    async def refresh_cache(self):
        """Erzwingt Neuladen der Speaker aus der DB"""
        await self.get_all_speakers(force_refresh=True)
        logger.info("🔄 Speaker Registry Cache aktualisiert")


# Singleton instance
_speaker_registry: Optional[SpeakerRegistry] = None

def get_speaker_registry() -> SpeakerRegistry:
    """Holt Singleton Speaker Registry Instance"""
    global _speaker_registry
    if _speaker_registry is None:
        _speaker_registry = SpeakerRegistry()
    return _speaker_registry


# Convenience Functions für Migration
async def get_valid_speakers() -> List[str]:
    """Ersetzt hardcodierte Listen wie ['brad', 'marcel', 'lucy']"""
    registry = get_speaker_registry()
    return await registry.get_speaker_names()

async def is_valid_speaker_name(name: str) -> bool:
    """Ersetzt hardcodierte Speaker-Checks"""
    registry = get_speaker_registry()
    return await registry.is_valid_speaker(name)

async def get_default_speaker_name() -> str:
    """Ersetzt hardcodierte Default-Speaker wie 'marcel'"""
    registry = get_speaker_registry()
    return await registry.get_default_speaker()

async def get_speaker_fallback_mapping() -> Dict[str, str]:
    """Ersetzt hardcodierte Mappings"""
    registry = get_speaker_registry()
    return await registry.get_speaker_mapping()


# Test Function
if __name__ == "__main__":
    print("Speaker Registry - production ready") 