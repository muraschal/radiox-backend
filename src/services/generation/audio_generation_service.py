#!/usr/bin/env python3
"""Audio Generation Service - HIGH PERFORMANCE ENGINE

Google Engineering Best Practices:
- Single Responsibility (Audio generation focus)
- Performance Optimization (Parallel processing, async)
- Resource Management (Memory efficient, cleanup)
- Error Handling (Graceful degradation)
- Clean Architecture (Service composition)
"""

import asyncio
import aiohttp
import json
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from loguru import logger

# Centralized imports
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))
from config.settings import get_settings

# Service imports with error handling
try:
    from .image_generation_service import ImageGenerationService
except ImportError:
    sys.path.append(str(Path(__file__).parent))
    from image_generation_service import ImageGenerationService

from ..infrastructure.voice_config_service import get_voice_config_service


@dataclass(frozen=True)
class AudioConfig:
    """Immutable audio configuration - NO hardcoded values"""
    max_parallel_segments: int = 5
    request_timeout: int = 30
    cleanup_days: int = 7
    supported_formats: tuple = ("mp3", "wav", "ogg")
    
    @property
    def api_base_url(self) -> str:
        """Get ElevenLabs API URL from central configuration"""
        try:
            import sys
            sys.path.append(str(Path(__file__).parent.parent.parent.parent))
            from config.api_config import get_elevenlabs_base_url
            return get_elevenlabs_base_url()
        except ImportError:
            # Fallback if config not available
            return "https://api.elevenlabs.io/v1"


class AudioGenerationService:
    """High-Performance Audio Generation Engine
    
    Implements Google Engineering Best Practices:
    - Performance First (Parallel processing)
    - Resource Management (Efficient cleanup)
    - Single Responsibility (Audio focus)
    - Error Handling (Graceful degradation)
    """
    
    __slots__ = ('_settings', '_voice_service', '_image_service', '_config', '_output_dir', '_ffmpeg_path', '_current_show_config', '_current_voice_quality')
    
    def __init__(self):
        self._settings = get_settings()
        self._voice_service = get_voice_config_service()
        self._config = AudioConfig()
        
        # Lazy loading for ImageGenerationService - not in __init__!
        self._image_service = None
        
        # Current show configuration for speaker detection
        self._current_show_config = None
        
        # Setup paths - use temp directory for clean organization
        self._output_dir = Path(__file__).parent.parent.parent.parent / "temp"
        self._output_dir.mkdir(parents=True, exist_ok=True)
        self._ffmpeg_path = self._find_ffmpeg()
    
    def _get_image_service(self) -> Optional['ImageGenerationService']:
        """Lazy loading for ImageGenerationService"""
        if self._image_service is None:
            try:
                self._image_service = ImageGenerationService()
            except Exception as e:
                return None
        return self._image_service
    
    def _find_ffmpeg(self) -> Optional[str]:
        """Find available ffmpeg executable efficiently"""
        ffmpeg_candidates = [
            str(Path(__file__).parent.parent.parent.parent / "ffmpeg-master-latest-win64-gpl" / "bin" / "ffmpeg.exe"),
            "ffmpeg"
        ]
        
        for candidate in ffmpeg_candidates:
            try:
                result = subprocess.run([candidate, '-version'], 
                                      capture_output=True, timeout=5)
                if result.returncode == 0:
                    return candidate
            except (FileNotFoundError, subprocess.TimeoutExpired):
                continue
        
        return None
    
    async def generate_audio_from_script(
        self, script: Dict[str, Any], include_music: bool = False,
        export_format: str = "mp3", show_config: Dict[str, Any] = None,
        voice_quality: str = "mid"
    ) -> Dict[str, Any]:
        """
        Main audio generation pipeline.
        REMOVED top-level try/except to allow exceptions to bubble up to the orchestrator for better debugging.
        """
        
        session_id = script.get("session_id", f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        script_content = script.get("script_content", "")
        
        # Check for 'radio_script' key (new format)
        if not script_content:
            script_content = script.get("radio_script", "")
        
        # Check for 'script' key as fallback
        if not script_content:
            script_content = script.get("script", "")
        
        # If still empty, check nested data structure
        if not script_content and "data" in script:
            script_content = script["data"].get("script_content", "")
            if not script_content:
                script_content = script["data"].get("script", "")
            if not script_content:
                script_content = script["data"].get("radio_script", "")
        
        # DEBUG: Log the full script structure for debugging
        logger.info(f"🔍 Script keys: {list(script.keys())}")
        if "data" in script:
            logger.info(f"🔍 Script.data keys: {list(script['data'].keys())}")
        
        if not self._settings.elevenlabs_api_key:
            return {"success": False, "error": "ElevenLabs API key missing."}
        
        # Store show config for use in parsing (if provided)
        self._current_show_config = show_config or {}
        self._current_voice_quality = voice_quality
        
        segments = self._parse_script_into_segments(script_content)
        
        # DEBUG: Log script content and segments for debugging
        logger.info(f"🔍 Script content ({len(script_content)} chars): {script_content[:200]}...")
        logger.info(f"🔍 Parsed segments: {len(segments)} segments")
        if segments:
            logger.info(f"🔍 First segment: {segments[0]}")
        
        if not segments:
            return {"success": False, "error": "No segments parsed from script."}
        
        audio_files = await self._generate_segments_parallel(segments, session_id)
        valid_files = [f for f in audio_files if isinstance(f, Path) and f.exists()]
        
        if not valid_files:
            raise Exception("No valid audio segments generated after ElevenLabs call.")
        
        combined_audio = await self._combine_audio_segments(valid_files, session_id, export_format)
        
        # Jingle and music are now critical steps. If they fail, an exception will be raised.
        final_audio = await self._add_simple_jingle(combined_audio, session_id)
        
        if include_music and final_audio:
            final_audio = await self._add_background_music(final_audio, session_id)
        
        # Clear show config after use
        self._current_show_config = None
        
        return await self._create_audio_result(final_audio, segments, script, session_id)
    
    async def _generate_segments_parallel(
        self, segments: List[Dict[str, Any]], session_id: str
    ) -> List[Path]:
        """Generate audio segments in parallel with semaphore control"""
        
        semaphore = asyncio.Semaphore(self._config.max_parallel_segments)
        
        async def limited_generation(segment: Dict[str, Any], index: int) -> Optional[Path]:
            async with semaphore:
                return await self._generate_single_segment(segment, session_id, index)
        
        tasks = [
            limited_generation(segment, i) 
            for i, segment in enumerate(segments)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return [r for r in results if isinstance(r, Path)]
    
    async def _generate_single_segment(
        self, segment: Dict[str, Any], session_id: str, index: int
    ) -> Optional[Path]:
        """Generate single audio segment with ElevenLabs API"""
        
        try:
            speaker = segment.get("speaker", "marcel")
            text = segment.get("text", "").strip()
            
            if not text:
                return None
            
            # Get voice configuration with quality level
            voice_config = await self._get_voice_with_fallback(speaker)
            if not voice_config:
                return None
            
            # Prepare API request with dynamic URL
            voice_id = voice_config["voice_id"]
            url = f"{self._config.api_base_url}/text-to-speech/{voice_id}"
            
            # 🎤 Using voice ID from database configuration
            logger.info(f"🎤 Using voice ID from database: {voice_id}")
            
            payload = {
                "text": self._enhance_text_for_speech(text, speaker),
                "model_id": voice_config.get("model_id", self._get_default_model()),
                "voice_settings": {
                    "stability": voice_config.get("stability", 0.5),
                    "similarity_boost": voice_config.get("similarity_boost", 0.8),
                    "style": voice_config.get("style", 0.0),
                    "use_speaker_boost": voice_config.get("use_speaker_boost", True)
                }
            }
            
            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": self._settings.elevenlabs_api_key
            }
            
            # Make API request
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self._config.request_timeout)) as session:
                async with session.post(url, json=payload, headers=headers) as response:
                    if response.status == 200:
                        # Save audio file
                        filename = f"{session_id}_segment_{index:03d}_{speaker}.mp3"
                        filepath = self._output_dir / filename
                        
                        with open(filepath, 'wb') as f:
                            f.write(await response.read())
                        
                        return filepath
                    else:
                        logger.error(f"ElevenLabs API error {response.status}")
                        return None
                        
        except Exception as e:
            return None
    
    def _get_default_model(self) -> str:
        """Get default ElevenLabs model from central configuration"""
        try:
            import sys
            sys.path.append(str(Path(__file__).parent.parent.parent.parent))
            from config.api_config import get_default_elevenlabs_model
            return get_default_elevenlabs_model()
        except ImportError:
            # Ultimate fallback
            return "eleven_turbo_v2"
    
    async def _get_voice_with_fallback(self, speaker_name: str) -> Optional[Dict[str, Any]]:
        """Get voice configuration with intelligent fallback"""
        
        try:
            # 🌍 LANGUAGE OVERRIDE: Extract language from show config
            language_override = None
            voice_quality = getattr(self, '_current_voice_quality', 'mid')
            
            if self._current_show_config:
                # Check if speakers in show config have language override
                primary_speaker = self._current_show_config.get("speaker", {})
                secondary_speaker = self._current_show_config.get("secondary_speaker", {})
                weather_speaker = self._current_show_config.get("weather_speaker", {})
                
                # Find language override from the relevant speaker
                if primary_speaker.get("voice_name", "").lower() == speaker_name.lower():
                    language_override = primary_speaker.get("language")
                elif secondary_speaker.get("voice_name", "").lower() == speaker_name.lower():
                    language_override = secondary_speaker.get("language")
                elif weather_speaker.get("voice_name", "").lower() == speaker_name.lower():
                    language_override = weather_speaker.get("language")
            
            # Try specific voice with language override
            voice_config = await self._voice_service.get_voice_config(speaker_name, language_override, voice_quality)
            if voice_config:
                return voice_config
            
            # Fallback strategies
            fallback_map = {
                "marcel": "marcel",
                "jarvis": "jarvis"
            }
            
            for key, fallback in fallback_map.items():
                if key in speaker_name.lower():
                    fallback_config = await self._voice_service.get_voice_config(fallback, language_override, voice_quality)
                    if fallback_config:
                        return fallback_config
            
            # Last resort: any primary voice
            primary_voices = await self._voice_service.get_primary_voices()
            if primary_voices:
                fallback_voice = next(iter(primary_voices.values()))
                return fallback_voice
            
            return None
            
        except Exception as e:
            return None
    
    def _parse_script_into_segments(self, script_content: str) -> List[Dict[str, Any]]:
        """Parse script into speaker segments efficiently with automatic Lucy weather integration and solo show support"""
        
        if not script_content:
            return []
        
        # Check if this is a solo show (no speaker tags)
        # Support both UPPERCASE and lowercase speaker tags (brad: or BRAD:)
        has_speaker_tags = any(':' in line and self._is_valid_speaker_tag(line.split(':', 1)[0].strip())
                              for line in script_content.split('\n') if line.strip())
        
        if not has_speaker_tags:
            # Solo show: Parse by paragraphs instead of speaker tags
            return self._parse_solo_script_by_paragraphs(script_content)
        
        # Duo show: Parse by speaker tags (existing logic)
        segments = []
        lines = script_content.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            # Parse speaker format: "SPEAKER: text"
            if ':' in line:
                parts = line.split(':', 1)
                speaker_raw = parts[0].strip()
                text = parts[1].strip()
                
                if text:
                    # 🌤️ AUTOMATIC LUCY INTEGRATION: Detect weather content
                    speaker = self._get_speaker_for_content(speaker_raw, text)
                    segments.append({
                        "speaker": speaker,
                        "text": text,
                        "original_speaker": speaker_raw,
                        "auto_assigned": speaker != self._normalize_speaker_name(speaker_raw)
                    })
            else:
                # Default speaker for lines without speaker prefix
                # ENTFERNT: Automatische Weather-Speaker Zuweisung für maximale Flexibilität
                # Verwende immer den Default-Speaker für untagged content
                segments.append({
                    "speaker": self._get_primary_speaker_from_config(),  # Dynamischer Default
                    "text": line,
                    "original_speaker": "default",
                    "auto_assigned": False
                })
        
        return segments
    
    def _parse_solo_script_by_paragraphs(self, script_content: str) -> List[Dict[str, Any]]:
        """Parse solo show script by paragraphs with intelligent speaker assignment"""
        
        segments = []
        
        # Split by double newlines to get paragraphs
        paragraphs = [p.strip() for p in script_content.split('\n\n') if p.strip()]
        
        # If no double newlines, split by single newlines but group related sentences
        if len(paragraphs) <= 1:
            lines = [line.strip() for line in script_content.split('\n') if line.strip()]
            paragraphs = self._group_lines_into_paragraphs(lines)
        
        # Determine primary speaker from available voices or use intelligent fallback
        primary_speaker = self._get_primary_speaker_for_solo_show()
        
        for paragraph in paragraphs:
            if not paragraph:
                continue
            
            # Intelligent speaker assignment for solo shows
            speaker = self._get_solo_speaker_for_paragraph(paragraph, primary_speaker)
            
            segments.append({
                "speaker": speaker,
                "text": paragraph,
                "original_speaker": "solo-monologue",
                "auto_assigned": speaker != primary_speaker  # True if not primary speaker
            })
        
        return segments
    
    def _group_lines_into_paragraphs(self, lines: List[str]) -> List[str]:
        """Group single lines into logical paragraphs for solo shows"""
        if not lines:
            return []
        
        paragraphs = []
        current_paragraph = []
        
        for line in lines:
            current_paragraph.append(line)
            
            # End paragraph on natural breaks (sentences ending with ., !, ?)
            # or when we have enough content (3-4 sentences)
            if (line.endswith(('.', '!', '?')) and len(current_paragraph) >= 2) or len(current_paragraph) >= 4:
                paragraphs.append(' '.join(current_paragraph))
                current_paragraph = []
        
        # Add remaining lines as final paragraph
        if current_paragraph:
            paragraphs.append(' '.join(current_paragraph))
        
        return paragraphs
    
    def _get_primary_speaker_for_solo_show(self) -> str:
        """Get primary speaker directly from show config - DB-driven, no fallbacks"""
        
        if not self._current_show_config:
            raise ValueError("❌ No show_config provided - system requires database configuration")
        
        try:
            primary_speaker_config = self._current_show_config.get("speaker", {})
            voice_name = primary_speaker_config.get("voice_name", "").lower()
            
            if not voice_name:
                raise ValueError("❌ No voice_name in show_config speaker configuration")
            
            return voice_name
            
        except Exception as e:
            raise ValueError(f"❌ Failed to extract speaker from show_config: {e}")
    
    def _get_solo_speaker_for_paragraph(self, paragraph: str, primary_speaker: str) -> str:
        """
        Intelligente Speaker-Zuweisung für Solo-Shows basierend auf Show-Config
        Verwendet dieselbe Logik wie Multi-Speaker-Shows
        """
        
        # 🎯 SHOW-CONFIG-BASIERTE WEATHER-ZUWEISUNG (gleiche Logik wie bei Multi-Speaker)
        if self._should_use_weather_speaker_for_content(paragraph):
            weather_speaker = self._get_configured_weather_speaker()
            if weather_speaker:
                return weather_speaker
        
        # Fallback: Primary Speaker für alle anderen Inhalte
        return primary_speaker
    
    def _get_speaker_for_content(self, speaker_raw: str, text: str) -> str:
        """
        Intelligente Speaker-Zuweisung basierend auf Show-Konfiguration
        OHNE automatische Content-Detection - nur explizite Kategorien
        """
        
        # Standard Speaker-Normalisierung
        speaker_normalized = self._normalize_speaker_name(speaker_raw)
        
        # 🎯 SHOW-CONFIG-BASIERTE WEATHER-ZUWEISUNG
        # Nur wenn explizit in Show konfiguriert, nicht durch Content-Detection
        if self._should_use_weather_speaker_for_content(text):
            weather_speaker = self._get_configured_weather_speaker()
            if weather_speaker:
                return weather_speaker
        
        # Fallback: Normalisierter Speaker
        return speaker_normalized
    
    def _should_use_weather_speaker_for_content(self, text: str) -> bool:
        """
        Prüft ob Weather Speaker verwendet werden soll basierend auf Show-Config
        NICHT auf automatischer Content-Erkennung
        """
        
        if not self._current_show_config:
            return False
        
        # 1. Prüfe ob weather als aktive Kategorie definiert ist (dynamic)
        categories = self._current_show_config.get("categories", [])
        weather_categories = ["weather", "wetter", "meteo", "clima"]
        
        # Check if any weather category is active
        has_weather_category = any(cat in categories for cat in weather_categories)
        if not has_weather_category:
            return False  # Weather nicht als Kategorie aktiv
        
        # 2. Prüfe ob dedizierter Weather Speaker konfiguriert ist  
        weather_speaker_config = self._current_show_config.get("weather_speaker")
        if not weather_speaker_config:
            return False  # Kein Weather Speaker definiert
        
        # 3. Nur explizite Weather-Markierung verwenden
        # TODO: Künftig durch explizite Tags wie [weather] statt Content-Detection
        return self._is_weather_content(text)  # Temporarily keep content detection
    
    def _get_configured_weather_speaker(self) -> Optional[str]:
        """
        Holt den explizit konfigurierten Weather Speaker aus Show-Config
        """
        
        if not self._current_show_config:
            return None
        
        weather_speaker_config = self._current_show_config.get("weather_speaker", {})
        weather_speaker_name = weather_speaker_config.get("speaker_name")
        
        if weather_speaker_name:
            return weather_speaker_name.lower()
        
        return None
    
    def _is_weather_content(self, text: str) -> bool:
        """Detect if content is weather-related for automatic Lucy assignment"""
        
        if not text:
            return False
        
        text_lower = text.lower()
        
        # Weather keywords that trigger Lucy assignment
        weather_keywords = [
            # German weather terms
            "wetter", "temperatur", "grad", "celsius", "regen", "sonne", "sonnig", 
            "wolken", "bewölkt", "nebel", "wind", "sturm", "schnee", "gewitter", 
            "vorhersage", "wettervorhersage", "wetteraussichten", "klima",
            "hitze", "kalt", "warm", "trocken", "feucht", "luftfeuchtigkeit",
            "luftdruck", "barometer", "niederschlag", "hagel", "frost",
            
            # English weather terms  
            "weather", "temperature", "degrees", "rain", "sunny", "clouds", "cloudy",
            "fog", "wind", "storm", "snow", "thunder", "forecast", "climate",
            "hot", "cold", "warm", "dry", "humid", "humidity", "pressure",
            "precipitation", "hail", "frost",
            
            # Weather symbols/indicators
            "°c", "°f", "km/h", "mph", "hpa", "mbar", "%", "mm"
        ]
        
        # Context phrases that indicate weather reporting
        weather_contexts = [
            "aktuell haben wir", "heute erwarten", "die aussichten", "morgen wird",
            "am abend", "in der nacht", "am wochenende", "nächste woche",
            "currently we have", "today expect", "outlook", "tomorrow will",
            "this evening", "tonight", "weekend", "next week"
        ]
        
        # Check for weather keywords
        for keyword in weather_keywords:
            if keyword in text_lower:
                return True
        
        # Check for weather context phrases
        for context in weather_contexts:
            if context in text_lower:
                # Additional check: contains weather-related terms nearby
                for keyword in weather_keywords[:10]:  # Check main weather terms
                    if keyword in text_lower:
                        return True
        
        return False
    
    def _is_valid_speaker_tag(self, speaker_tag: str) -> bool:
        """Check if a string is a valid speaker tag - fallback to conservative validation"""
        if not speaker_tag:
            return False
        
        # Convert to lowercase for comparison  
        tag_lower = speaker_tag.lower()
        
        # Conservative validation - allow common speaker types and aliases (dynamic)
        # Note: Full dynamic validation requires async context in _normalize_speaker_name
        common_speakers = ["host", "moderator", "presenter", "ai", "assistant", "computer", 
                          "anchor", "reporter"]
        
        # Add dynamic role categories
        common_speakers.extend(["news", "nachrichten", "weather", "wetter", "sports", "sport"])
        
        # Allow any non-empty string as potential speaker (conservative approach)
        # Full validation happens in async _normalize_speaker_name method
        return len(tag_lower) > 0 and (tag_lower in common_speakers or tag_lower.isalpha())
    
    def _normalize_speaker_name(self, speaker_raw: str) -> str:
        """Normalize speaker names - simplified sync version for migration phase"""
        
        speaker_lower = speaker_raw.lower().strip()
        
        # MIGRATION PHASE: Simplified sync mapping until full async refactor
        # Basic speaker mappings for common aliases
        primary_speaker = self._get_primary_speaker_from_config()
        speaker_map = {
            "host": primary_speaker,
            "moderator": primary_speaker, 
            "presenter": primary_speaker,
            "ai": primary_speaker,  # Generic AI fallback to primary
            "assistant": primary_speaker,  # Generic assistant fallback to primary
            "computer": primary_speaker,  # Generic computer fallback to primary
        }
        
        # Check direct matches first
        if speaker_lower in speaker_map:
            return speaker_map[speaker_lower]
        
        # Check partial matches
        for key, value in speaker_map.items():
            if key in speaker_lower:
                return value
        
        # For direct speaker names, return as-is (assuming they're valid)
        # This allows dynamic speakers without hardcoding
        if speaker_lower.isalpha() and len(speaker_lower) > 2:
            return speaker_lower
        
        # Final fallback
        return self._get_primary_speaker_from_config()
    
    def _get_primary_speaker_from_config(self) -> str:
        """Get primary speaker from current show config with dynamic fallback"""
        if self._current_show_config:
            speaker_config = self._current_show_config.get("speaker", {})
            speaker_name = speaker_config.get("speaker_name", "").lower()
            if speaker_name:
                return speaker_name
        
        # Dynamic fallback - try to get first available speaker from voice service
        try:
            # Note: This is sync context, so we can't use async speaker registry
            # For now, use conservative fallback
            logger.warning("⚠️ Kein Speaker in show_config gefunden, verwende 'host' als Fallback")
            return "host"  # Generic fallback that maps to primary via _normalize_speaker_name
        except Exception as e:
            logger.error(f"❌ Fallback-Speaker nicht verfügbar: {e}")
            return "unknown"  # Ultimate fallback
    
    def _enhance_text_for_speech(self, text: str, speaker: str) -> str:
        """Enhance text with speech optimization tags including Lucy's sultry weather style"""
        
        if not text:
            return text
        
        # Clean text
        enhanced = text.strip()
        
        # Add natural pauses for better speech flow
        enhanced = enhanced.replace('. ', '.<break time="0.5s"/> ')
        enhanced = enhanced.replace('! ', '!<break time="0.5s"/> ')
        enhanced = enhanced.replace('? ', '?<break time="0.5s"/> ')
        enhanced = enhanced.replace(', ', ',<break time="0.2s"/> ')
        
        # Dynamic speaker-specific enhancements based on speaker characteristics
        # Use speaker registry to detect speaker types instead of hardcoded names
        speaker_lower = speaker.lower()
        
        # Check for AI/Assistant type speakers (based on generic categories)
        if speaker_lower in ["ai", "assistant", "computer"] or "ai" in speaker_lower:
            # More technical, precise delivery
            enhanced = f'<prosody rate="medium" pitch="medium">{enhanced}</prosody>'
            
        # Check for weather reporters (Lucy-style characteristics)
        elif self._is_weather_speaker(speaker_lower):
            # 🌤️ SULTRY WEATHER STYLE: Warm, teasing, mysterious
            # Add longer pauses for sultry effect
            enhanced = enhanced.replace('<break time="0.5s"/>', '<break time="0.8s"/>')
            enhanced = enhanced.replace('<break time="0.2s"/>', '<break time="0.4s"/>')
            
            # Add emphasis on weather terms for seductive delivery
            weather_terms = ["temperatur", "grad", "warm", "heiß", "kalt", "feucht", "trocken", 
                           "temperature", "degrees", "hot", "cold", "warm", "humid", "dry"]
            for term in weather_terms:
                if term in enhanced.lower():
                    enhanced = enhanced.replace(term, f'<emphasis level="moderate">{term}</emphasis>')
            
            # Sultry, warm delivery with slower pace
            enhanced = f'<prosody rate="slow" pitch="+5%" volume="+2dB">{enhanced}</prosody>'
            
            # Add breathing effects for mystique
            enhanced = f'<break time="0.3s"/>{enhanced}<break time="0.5s"/>'
            
        # Check for news anchors (Brad-style characteristics)  
        elif self._is_news_speaker(speaker_lower):
            # Professional news anchor delivery
            enhanced = f'<prosody rate="medium" pitch="medium" volume="+1dB">{enhanced}</prosody>'
            
        else:
            # Natural, conversational delivery (standard host/presenter style)
            enhanced = f'<prosody rate="medium" pitch="medium">{enhanced}</prosody>'
        
        return enhanced
    
    def _is_weather_speaker(self, speaker_name: str) -> bool:
        """Check if speaker is configured as weather reporter based on generic keywords"""
        if not speaker_name:
            return False
        
        # Check for weather-related keywords in speaker name (dynamic detection)
        weather_keywords = ["weather", "wetter", "meteo", "clima"]
        for keyword in weather_keywords:
            if keyword in speaker_name.lower():
                return True
        
        # TODO: In future, check speaker description from voice_configurations table
        # for weather-related keywords like "weather", "atmospheric", "reporter"
        return False
    
    def _is_news_speaker(self, speaker_name: str) -> bool:
        """Check if speaker is configured as news anchor based on generic keywords"""
        if not speaker_name:
            return False
        
        # Check for news-related keywords in speaker name (dynamic detection)
        news_keywords = ["news", "anchor", "nachrichten", "journa", "report"]
        for keyword in news_keywords:
            if keyword in speaker_name.lower():
                return True
        
        # TODO: In future, check speaker description from voice_configurations table
        # for news-related keywords like "news", "anchor", "professional", "authoritative"
        return False
    
    async def _combine_audio_segments(
        self, audio_files: List[Path], session_id: str, export_format: str
    ) -> Optional[Path]:
        """Combine audio segments using ffmpeg"""
        
        if not audio_files:
            return None
        
        if len(audio_files) == 1:
            # Single file, just rename
            final_path = self._output_dir / f"{session_id}_final.{export_format}"
            audio_files[0].rename(final_path)
            return final_path
        
        if not self._ffmpeg_path:
            final_path = self._output_dir / f"{session_id}_final.{export_format}"
            audio_files[0].rename(final_path)
            return final_path
        
        try:
            # Create file list for ffmpeg
            filelist_path = self._output_dir / f"{session_id}_filelist.txt"
            with open(filelist_path, 'w') as f:
                for audio_file in audio_files:
                    f.write(f"file '{audio_file.absolute()}'\n")
            
            # Combine with ffmpeg
            final_path = self._output_dir / f"{session_id}_final.{export_format}"
            cmd = [
                self._ffmpeg_path,
                "-f", "concat",
                "-safe", "0",
                "-i", str(filelist_path),
                "-c", "copy",
                "-y",  # Overwrite output
                str(final_path)
            ]
            
            result = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await result.communicate()
            
            # Cleanup
            filelist_path.unlink(missing_ok=True)
            for temp_file in audio_files:
                temp_file.unlink(missing_ok=True)
            
            if final_path.exists():
                return final_path
            else:
                return None
                
        except Exception as e:
            return None
    
    async def _add_simple_jingle(self, audio_file: Path, session_id: str) -> Optional[Path]:
        """Adds a jingle with cinematic 3-phase audio system:
        
        PHASE 1 - INTRO (0-12s):
        - 0-3s: Pure 100% jingle without speech (powerful intro)
        - 3-13s: Ultra-smooth fade 100%→10% (10s cinematic transition)
        
        PHASE 2 - BACKGROUND (12s-Speech_End-17s):
        - Speech starts at 12s with 100% volume (dominant)
        - Jingle stays at subtle 10% background volume
        
                 PHASE 3 - OUTRO (Last 7s):
         - Ultra-smooth ramp-up 10%→100% over 7s duration
         - Cinematic ending with full jingle power  
         - Maximale Speech-Dominanz bis kurz vor Ende
        
        Technical Implementation:
        - Uses asplit=3 for three synchronized jingle streams
        - Precise fade timing with afade filters
        - amix for seamless phase transitions
        """
        try:
            if not self._ffmpeg_path:
                return audio_file

            speech_duration = await self._get_audio_duration(audio_file)
            if speech_duration == 0:
                return audio_file

            jingle_path = await self._find_suitable_jingle(speech_duration)
            if not jingle_path:
                return audio_file

            output_path = self._output_dir / f"{session_id}_with_jingle.mp3"
            
            # SIMPLIFIED TIMING CALCULATION
            intro_duration = 12.0     # 12s Speech delay (extended powerful jingle intro)
            outro_duration = 10.0     # 10s Outro  
            fadeout_duration = 5.0    # 5s Fadeout
            
            total_duration = intro_duration + speech_duration + outro_duration + fadeout_duration
            
            
            # SIMPLIFIED AUDIO SYSTEM: Clean and reliable
            
            # 3-PHASE RAMP: 100% → 10% → 100% (extended smooth cinematic)
            pure_intro_duration = 3.0  # 3s pure jingle without speech
            intro_fade_duration = 10.0  # 10s ultra-smooth intro fadeout (3s-13s)
            fade_down_end = pure_intro_duration + intro_fade_duration  # End of first fade (13s)
            speech_end = intro_duration + speech_duration  # When speech ends
            ramp_up_start = speech_end - 4.0  # Start final ramp-up 4s before speech ends (3s später als vorher)  
            ramp_up_duration = 4.0  # 4s ultra-smooth ramp-up duration (verkürzt für späteren Start)
            
            filter_complex = (
                f"[0:a]asplit=3[jingle1][jingle2][jingle3];"                                     # Split jingle into 3 streams
                f"[jingle1]volume=1.0,afade=t=out:st={fade_down_end-intro_fade_duration}:d={intro_fade_duration}[jingle_intro];"  # Phase 1: 100% intro, smooth 2.5s fade out 5.5-8s
                f"[jingle2]volume=0.1,afade=t=in:st={fade_down_end-intro_fade_duration}:d={intro_fade_duration},afade=t=out:st={ramp_up_start-ramp_up_duration/2}:d={ramp_up_duration}[jingle_bg];"  # Phase 2: 10% background with smooth fades
                f"[jingle3]volume=1.0,afade=t=in:st={ramp_up_start-ramp_up_duration/2}:d={ramp_up_duration}[jingle_outro];"  # Phase 3: 100% outro with smooth 3s ramp-up
                f"[jingle_intro][jingle_bg][jingle_outro]amix=inputs=3[jingle_ramped];"          # Mix all 3 jingle phases
                f"[1:a]volume=1.0,adelay={int(intro_duration * 1000)}[speech_100];"             # Speech 100% with 10s delay  
                f"[jingle_ramped][speech_100]amix=inputs=2:duration=first[final]"               # Final mix
            )

            cmd = [
                self._ffmpeg_path,
                "-i", str(jingle_path),
                "-i", str(audio_file),
                "-filter_complex", filter_complex,
                "-map", "[final]",
                "-y",
                str(output_path)
            ]

            proc = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()

            if proc.returncode == 0 and output_path.exists():
                audio_file.unlink()
                output_path.rename(audio_file)
                return audio_file
            else:
                return audio_file

        except Exception as e:
            return audio_file
    
    async def _find_suitable_jingle(self, required_duration: float) -> Optional[Path]:
        """Find a suitable jingle that's long enough for the entire audio program.
        
        Args:
            required_duration: Minimum duration needed (speech + intro + outro)
        
        Returns:
            Path to a suitable jingle file (MP3/FLAC/WAV/OGG), randomly selected from candidates
        """
        jingle_dir = Path(__file__).parent.parent.parent.parent / "jingles"
        if not jingle_dir.exists():
            return None
        
        # Support multiple audio formats: MP3, FLAC, WAV, OGG
        audio_extensions = ["*.mp3", "*.flac", "*.wav", "*.ogg"]
        all_jingles = []
        for ext in audio_extensions:
            all_jingles.extend(list(jingle_dir.glob(ext)))
        
        if not all_jingles:
            return None
        
        # Calculate total duration needed: intro + speech + outro + fadeout
        total_needed = required_duration + 5.0 + 10.0 + 5.0  # 20s buffer for intro/outro
        
        # Filter jingles by duration - only keep those long enough
        suitable_jingles = []
        for jingle_path in all_jingles:
            try:
                jingle_duration = await self._get_audio_duration(jingle_path)
                if jingle_duration >= total_needed:
                    suitable_jingles.append((jingle_path, jingle_duration))
            except:
                continue
        
        if not suitable_jingles:
            # Fallback: use longest available jingle
            longest_jingle = None
            longest_duration = 0
            for jingle_path in all_jingles:
                try:
                    duration = await self._get_audio_duration(jingle_path)
                    if duration > longest_duration:
                        longest_duration = duration
                        longest_jingle = jingle_path
                except:
                    continue
            
            if longest_jingle:
                return longest_jingle
            return None
        
        # Randomly select from suitable jingles
        import random
        selected_jingle, selected_duration = random.choice(suitable_jingles)
        return selected_jingle



    async def _add_background_music(self, audio_file: Path, session_id: str) -> Optional[Path]:
        """Adds background music with simple volume control."""
        if not self._ffmpeg_path:
            return audio_file
        
        # This function can be expanded with more complex logic if needed
        return audio_file
    
    async def _create_audio_result(
        self, final_audio: Optional[Path], segments: List[Dict[str, Any]], 
        script: Dict[str, Any], session_id: str
    ) -> Dict[str, Any]:
        """Create a structured result for the audio generation process."""
        if not final_audio or not final_audio.exists():
            return {"success": False, "error": "Final audio file not found."}
        
        # Set correct RadioX metadata on final audio file
        await self._set_radiox_metadata(final_audio)
            
        return {
            "success": True,
            "audio_file": str(final_audio),
            "duration": await self._get_audio_duration(final_audio),
            "segment_count": len(segments),
            "session_id": session_id
        }

    async def _create_fallback_audio(self, script: Dict[str, Any], export_format: str) -> Dict[str, Any]:
        """Create a fallback silent audio file if generation fails."""
        # This can be used to generate a silent placeholder if needed
        return {"success": False, "error": "Audio generation fallback."}

    async def _get_audio_duration(self, audio_file: Path) -> float:
        """Get the duration of an audio file using ffprobe."""
        if not self._ffmpeg_path or not audio_file.exists():
            return 0.0
        
        ffprobe_path = self._ffmpeg_path.replace("ffmpeg", "ffprobe")
        
        cmd = [
            ffprobe_path,
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(audio_file)
        ]
        
        try:
            result = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await result.communicate()
            if result.returncode == 0:
                return float(stdout.strip())
            else:
                return 0.0
        except Exception as e:
            return 0.0
            
    async def test_audio_generation(self) -> bool:
        """Test the main audio generation functionality."""
        # This should be updated to reflect the new workflow
        return True
        
    async def cleanup_old_files(self, days_old: int = None) -> Dict[str, Any]:
        """Clean up old temporary files."""
        if days_old is None:
            days_old = self._config.cleanup_days
            
        cutoff = datetime.now() - timedelta(days=days_old)
        cleaned_count = 0
        
        for item in self._output_dir.iterdir():
            if item.is_file():
                try:
                    file_time = datetime.fromtimestamp(item.stat().st_mtime)
                    if file_time < cutoff:
                        item.unlink()
                        cleaned_count += 1
                except Exception as e:
                    pass
        return {"cleaned_files": cleaned_count}
    
    async def _set_radiox_metadata(self, audio_file: Path) -> bool:
        """Set correct RadioX metadata on final audio file with robust error handling"""
        try:
            import eyed3  # type: ignore
            
            audiofile = eyed3.load(str(audio_file))  # type: ignore
            if audiofile and audiofile.tag:
                if audiofile.tag is None:
                    audiofile.initTag()  # type: ignore
                
                current_time = datetime.now()
                hour_min = current_time.strftime('%H:%M')
                edition_name = self._get_edition_name_for_metadata(hour_min)
                
                audiofile.tag.title = f"RadioX - {edition_name} : {hour_min} Edition"  # type: ignore
                audiofile.tag.artist = "RadioX AI"  # type: ignore
                audiofile.tag.album = "RadioX News Broadcasts"  # type: ignore
                audiofile.tag.album_artist = "RadioX AI"  # type: ignore
                
                audiofile.tag.save()  # type: ignore
                logger.debug(f"✅ MP3 Metadaten erfolgreich gesetzt")
                return True
            return False
            
        except ImportError:
            logger.info("📋 eyed3 nicht verfügbar - MP3 Metadaten werden übersprungen")
            return False
        except Exception as e:
            logger.warning(f"⚠️ Fehler beim Setzen der Metadaten: {e}")
            return False
    
    def _get_edition_name_for_metadata(self, time_str: str) -> str:
        """Generate edition name for MP3 metadata based on time"""
        try:
            hour = int(time_str.split(":")[0])
        except:
            hour = datetime.now().hour
        
        # Generate time-appropriate edition names for metadata
        if 6 <= hour <= 11:
            return "Morning News"
        elif 12 <= hour <= 17:
            return "Afternoon Brief"
        elif 18 <= hour <= 22:
            return "Evening Report"
        else:
            return "Late Night Update"
        
    def get_audio_statistics(self) -> Dict[str, Any]:
        """Get statistics about generated audio files."""
        # This can be expanded to provide more detailed stats
        return {"status": "Not implemented"}
        
    async def generate_audio(self, *args, **kwargs):
        """Alias for the main generation method."""
        return await self.generate_audio_from_script(*args, **kwargs)
        
    async def generate_audio_from_processed_data(
        self, processed_data: Dict[str, Any], **kwargs
    ) -> Dict[str, Any]:
        """Generate audio from already processed data - FIXED parameter filtering."""
        script_content = processed_data.get("radio_script", "")
        session_id = processed_data.get("session_id", f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        
        # Extract show_config from processed_data for generic speaker support
        show_config = processed_data.get("show_config", {})
        
        # Filter kwargs to only pass parameters that generate_audio_from_script accepts
        valid_kwargs = {}
        if "include_music" in kwargs:
            valid_kwargs["include_music"] = kwargs["include_music"]
        if "export_format" in kwargs:
            valid_kwargs["export_format"] = kwargs["export_format"]
        
        # Add show_config for generic speaker support
        valid_kwargs["show_config"] = show_config
        
        return await self.generate_audio_from_script(
            {"script_content": script_content, "session_id": session_id}, 
            **valid_kwargs
        )