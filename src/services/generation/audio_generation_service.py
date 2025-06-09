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
    """Immutable audio configuration"""
    api_base_url: str = "https://api.elevenlabs.io/v1"
    max_parallel_segments: int = 5
    request_timeout: int = 30
    cleanup_days: int = 7
    supported_formats: tuple = ("mp3", "wav", "ogg")


class AudioGenerationService:
    """High-Performance Audio Generation Engine
    
    Implements Google Engineering Best Practices:
    - Performance First (Parallel processing)
    - Resource Management (Efficient cleanup)
    - Single Responsibility (Audio focus)
    - Error Handling (Graceful degradation)
    """
    
    __slots__ = ('_settings', '_voice_service', '_image_service', '_config', '_output_dir', '_ffmpeg_path')
    
    def __init__(self):
        self._settings = get_settings()
        self._voice_service = get_voice_config_service()
        self._config = AudioConfig()
        
        # Lazy loading für ImageGenerationService - nicht im __init__!
        self._image_service = None
        
        # Setup paths - use temp directory for clean organization
        self._output_dir = Path(__file__).parent.parent.parent.parent / "temp"
        self._output_dir.mkdir(parents=True, exist_ok=True)
        self._ffmpeg_path = self._find_ffmpeg()
    
    def _get_image_service(self) -> Optional['ImageGenerationService']:
        """Lazy loading für ImageGenerationService"""
        if self._image_service is None:
            try:
                self._image_service = ImageGenerationService()
                logger.debug("✅ ImageGenerationService lazy-loaded")
            except Exception as e:
                logger.warning(f"⚠️ ImageGenerationService lazy loading failed: {e}")
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
                    logger.info(f"✅ ffmpeg found: {candidate}")
                    return candidate
            except (FileNotFoundError, subprocess.TimeoutExpired):
                continue
        
        logger.warning("⚠️ ffmpeg not found - fallback mode")
        return None
    
    async def generate_audio_from_script(
        self, script: Dict[str, Any], include_music: bool = False,
        export_format: str = "mp3"
    ) -> Dict[str, Any]:
        """Main audio generation pipeline with performance optimization"""
        
        session_id = script.get("session_id", f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        script_content = script.get("script_content", "")
        
        logger.info(f"🔊 Generate audio for session {session_id}")
        
        if not self._settings.elevenlabs_api_key:
            logger.warning("⚠️ ElevenLabs API key missing - fallback mode")
            return await self._create_fallback_audio(script, export_format)
        
        try:
            # Pipeline execution
            segments = self._parse_script_into_segments(script_content)
            logger.info(f"📝 Parsed {len(segments)} segments")
            
            # Parallel audio generation
            audio_files = await self._generate_segments_parallel(segments, session_id)
            valid_files = [f for f in audio_files if isinstance(f, Path) and f.exists()]
            
            if not valid_files:
                raise Exception("No valid audio segments generated")
            
            # Combine segments
            final_audio = await self._combine_audio_segments(valid_files, session_id, export_format)
            
            # Add jingle with intelligent ramping
            if final_audio:
                final_audio = await self._add_jingle_with_intelligent_ramping(final_audio, session_id)
            
            # Add music if requested
            if include_music and final_audio:
                final_audio = await self._add_background_music(final_audio, session_id)
            
            # Create result
            return await self._create_audio_result(final_audio, segments, script, session_id)
            
        except Exception as e:
            logger.error(f"❌ Audio generation failed: {e}")
            return await self._create_fallback_audio(script, export_format)
    
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
            
            # Get voice configuration
            voice_config = await self._get_voice_with_fallback(speaker)
            if not voice_config:
                logger.error(f"❌ No voice config for {speaker}")
                return None
            
            # Prepare API request
            voice_id = voice_config["voice_id"]
            url = f"{self._config.api_base_url}/text-to-speech/{voice_id}"
            
            payload = {
                "text": self._enhance_text_for_speech(text, speaker),
                "model_id": voice_config.get("model_id", "eleven_turbo_v2"),
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
                        
                        logger.debug(f"✅ Generated segment {index}: {speaker}")
                        return filepath
                    else:
                        error_text = await response.text()
                        logger.error(f"❌ ElevenLabs API error {response.status}: {error_text}")
                        return None
                        
        except Exception as e:
            logger.error(f"❌ Segment generation failed: {e}")
            return None
    
    async def _get_voice_with_fallback(self, speaker_name: str) -> Optional[Dict[str, Any]]:
        """Get voice configuration with intelligent fallback"""
        
        try:
            # Try specific voice
            voice_config = await self._voice_service.get_voice_config(speaker_name)
            if voice_config:
                return voice_config
            
            # Fallback strategies
            fallback_map = {
                "marcel": "marcel",
                "jarvis": "jarvis"
            }
            
            for key, fallback in fallback_map.items():
                if key in speaker_name.lower():
                    fallback_config = await self._voice_service.get_voice_config(fallback)
                    if fallback_config:
                        logger.info(f"🔄 Fallback {speaker_name} → {fallback}")
                        return fallback_config
            
            # Last resort: any primary voice
            primary_voices = await self._voice_service.get_primary_voices()
            if primary_voices:
                fallback_voice = next(iter(primary_voices.values()))
                fallback_name = next(iter(primary_voices.keys()))
                logger.warning(f"⚠️ Emergency fallback {speaker_name} → {fallback_name}")
                return fallback_voice
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Voice config error for {speaker_name}: {e}")
            return None
    
    def _parse_script_into_segments(self, script_content: str) -> List[Dict[str, Any]]:
        """Parse script into speaker segments efficiently with automatic Lucy weather integration"""
        
        if not script_content:
            return []
        
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
                # 🌤️ Check if content is weather-related
                if self._is_weather_content(line):
                    segments.append({
                        "speaker": "lucy",
                        "text": line,
                        "original_speaker": "auto-weather",
                        "auto_assigned": True
                    })
                else:
                    segments.append({
                        "speaker": "marcel",
                        "text": line,
                        "original_speaker": "default",
                        "auto_assigned": False
                    })
        
        return segments
    
    def _get_speaker_for_content(self, speaker_raw: str, text: str) -> str:
        """Determine the best speaker for given content with automatic Lucy weather assignment"""
        
        # 🌤️ LUCY AUTO-ASSIGNMENT: Only for LUCY speaker + weather content, NOT for other speakers
        # Marcel und Jarvis können über Wetter sprechen ohne automatisch zu Lucy zu werden
        speaker_normalized = self._normalize_speaker_name(speaker_raw)
        
        if speaker_normalized == "lucy" and self._is_weather_content(text):
            logger.info(f"🌤️ Weather content detected for Lucy: {text[:50]}...")
            return "lucy"
        
        # Otherwise use normal speaker normalization (Marcel bleibt Marcel!)
        return speaker_normalized
    
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
    
    def _normalize_speaker_name(self, speaker_raw: str) -> str:
        """Normalize speaker names to known voices with Lucy integration"""
        
        speaker_lower = speaker_raw.lower().strip()
        
        # Direct mappings including Lucy
        speaker_map = {
            "marcel": "marcel",
            "jarvis": "jarvis",
            "lucy": "lucy",
            "brad": "brad",
            "host": "marcel",
            "moderator": "marcel", 
            "anchor": "brad",
            "news": "brad",
            "ai": "jarvis",
            "assistant": "jarvis",
            "computer": "jarvis",
            "weather": "lucy",
            "wetter": "lucy",
            "wetterfee": "lucy",
            "meteorology": "lucy"
        }
        
        # Check direct matches
        if speaker_lower in speaker_map:
            return speaker_map[speaker_lower]
        
        # Check partial matches
        for key, value in speaker_map.items():
            if key in speaker_lower:
                return value
        
        # Default fallback
        return "marcel"
    
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
        
        # Speaker-specific enhancements
        if speaker == "jarvis":
            # More technical, precise delivery
            enhanced = f'<prosody rate="medium" pitch="medium">{enhanced}</prosody>'
        elif speaker == "lucy":
            # 🌤️ LUCY'S SULTRY WEATHER STYLE: Warm, teasing, mysterious
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
        elif speaker == "brad":
            # Professional news anchor delivery
            enhanced = f'<prosody rate="medium" pitch="medium" volume="+1dB">{enhanced}</prosody>'
        else:
            # Natural, conversational delivery (Marcel default)
            enhanced = f'<prosody rate="medium" pitch="medium">{enhanced}</prosody>'
        
        return enhanced
    
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
            logger.warning("⚠️ ffmpeg not available - using first segment only")
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
            await result.communicate()
            
            # Cleanup
            filelist_path.unlink(missing_ok=True)
            for temp_file in audio_files:
                temp_file.unlink(missing_ok=True)
            
            if final_path.exists():
                logger.info(f"✅ Combined {len(audio_files)} segments")
                return final_path
            else:
                logger.error("❌ ffmpeg combination failed")
                return None
                
        except Exception as e:
            logger.error(f"❌ Audio combination error: {e}")
            return None
    
    async def _add_jingle_with_intelligent_ramping(self, audio_file: Path, session_id: str) -> Optional[Path]:
        """Add jingle with intelligent audio ramping for professional radio sound"""
        
        if not self._ffmpeg_path:
            logger.warning("⚠️ ffmpeg not available - skipping jingle")
            return audio_file
            
        try:
            # Find available jingle
            jingle_path = await self._find_jingle()
            if not jingle_path:
                logger.warning("⚠️ No jingle found - skipping jingle mixing")
                return audio_file
            
            # Get audio duration for timing calculations
            speech_duration = await self._get_audio_duration(audio_file)
            if speech_duration <= 0:
                return audio_file
            
            logger.info(f"🎵 Adding jingle with intelligent ramping (Speech: {speech_duration:.1f}s)")
            
            # Create intelligent audio ramping filter
            ramping_filter = await self._create_intelligent_ramping_filter(speech_duration)
            
            # Create output path
            output_path = self._output_dir / f"{session_id}_with_jingle.mp3"
            
            # ffmpeg command for EPIC jingle mixing with extended timeline
            total_duration = speech_duration + 23  # 8s intro + speech + 15s outro = EPIC!
            cmd = [
                self._ffmpeg_path,
                "-i", str(jingle_path),      # Input 0: Jingle (background)
                "-i", str(audio_file),       # Input 1: Speech (foreground)
                "-filter_complex", ramping_filter,
                "-map", "[final_mix]",       # Map the mixed output
                "-t", str(total_duration),   # Total duration: 10s intro + speech + 15s outro
                "-c:a", "libmp3lame",
                "-b:a", "128k",
                "-y",  # Overwrite output
                str(output_path)
            ]
            
            # Execute ffmpeg
            result = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await result.communicate()
            
            if result.returncode == 0:
                logger.success(f"✅ Jingle mixed successfully: {output_path.name}")
                
                # Cleanup original file
                audio_file.unlink(missing_ok=True)
                return output_path
            else:
                logger.error(f"❌ Jingle mixing failed: {stderr.decode()}")
                return audio_file
                
        except Exception as e:
            logger.error(f"❌ Jingle mixing error: {e}")
            return audio_file
    
    async def _find_jingle(self) -> Optional[Path]:
        """Find available jingle file with randomized selection"""
        import random
        
        jingles_dir = Path(__file__).parent.parent.parent.parent / "jingles"
        
        if not jingles_dir.exists():
            return None
        
        # Look for audio files in jingles directory
        audio_extensions = [".mp3", ".wav", ".m4a", ".ogg"]
        
        jingle_files = []
        for file in jingles_dir.iterdir():
            if file.is_file() and file.suffix.lower() in audio_extensions:
                if not file.name.startswith('.'):  # Skip hidden files like .DS_Store
                    jingle_files.append(file)
        
        if not jingle_files:
            return None
        
        # Randomisierte Auswahl
        selected_jingle = random.choice(jingle_files)
        logger.info(f"🎵 Randomisiert gewählter Jingle: {selected_jingle.name}")
        return selected_jingle
    
    async def _create_intelligent_ramping_filter(self, speech_duration: float) -> str:
        """Creates a robust FFmpeg volume filter for professional 6-stage audio ramping.
        
        Handles different speech durations gracefully with adaptive logic.

        Args:
            speech_duration: The duration of the speech audio in seconds.

        Returns:
            A string containing the FFmpeg volume filter graph.
        """
        D = speech_duration
        logger.info(f"🎤 Creating intelligent ramping filter for speech duration: {D:.2f}s")

        # --- Adaptive Ramping Logic ---
        # For very short news, a full 6-stage ramp is not feasible and can cause errors.
        # Use a simplified 3-stage ramp for content shorter than 60 seconds.
        if D < 60:
            logger.warning(f"⚠️ Speech duration ({D:.2f}s) is less than 60s. Using simplified 3-stage ramping.")
            # Simplified timeline: 100% intro -> 6% backing -> 100% outro
            # Ramp down from 5s-8s, stay at 6%, ramp up in last 5s
            ramp_down_end = 8.0
            ramp_up_start = max(ramp_down_end, D - 5.0) # Ensure ramp up doesn't overlap ramp down

            volume_expression = (
                f"if(lt(t,5),1,"                                                              # 1. Intro: 0-5s at 100%
                f"if(lt(t,{ramp_down_end}),1-0.94*(t-5)/3,"                                    # 2. Ramp Down: 5s-8s to 6%
                f"if(lt(t,{ramp_up_start}),0.06,"                                             # 3. Backing: 8s to (D-5s) at 6%
                f"if(lt(t,{D}),0.06+0.94*(t-{ramp_up_start})/5,1)"                             # 4. Ramp Up: Last 5s to 100%
                f"))))"
            )
        else:
            # --- Standard 6-Stage Professional Ramping ---
            # Timeline: 100% intro -> fade to 6% -> 6% backing -> ramp to 100% -> 100% outro -> fadeout
            logger.info("🎬 Using standard 6-stage professional audio ramping.")
            
            # Define timestamps for clarity
            intro_end = 5.0
            ramp_down_end = 8.0
            ramp_up_start = D - 5.0
            speech_end = D
            outro_end = D + 10.0
            fadeout_duration = 4.0 # A slightly longer fadeout feels more professional
            final_end = outro_end + fadeout_duration

            # Using chained if() statements for FFmpeg filtergraph
            # This is more robust than deeply nested ifs.
            volume_expression = (
                f"if(lt(t,{intro_end}),1,"                                                     # 1. Intro: 0-5s at 100%
                f"if(lt(t,{ramp_down_end}),1-0.94*(t-{intro_end})/3,"                          # 2. Ramp Down: 5-8s, from 100% to 6% over 3s
                f"if(lt(t,{ramp_up_start}),0.06,"                                             # 3. Backing: 8s to (D-5s) at 6%
                f"if(lt(t,{speech_end}),0.06+0.94*(t-{ramp_up_start})/5,"                      # 4. Ramp Up: Last 5s of speech, from 6% to 100%
                f"if(lt(t,{outro_end}),1,"                                                     # 5. Outro: D to D+10s at 100%
                f"if(lt(t,{final_end}),1-(t-{outro_end})/{fadeout_duration},0)"                # 6. Fadeout: D+10s to D+14s, from 100% to 0%
                f"))))))"
            )

        # Final filter string for FFmpeg
        # Remove whitespace for compatibility
        final_filter = f"volume='{volume_expression.replace(' ', '')}'"
        logger.debug(f"✅ Generated FFmpeg volume filter: {final_filter}")
        return final_filter

    async def _add_background_music(self, audio_file: Path, session_id: str) -> Optional[Path]:
        """Adds background music with simple volume control."""
        
        if not self._ffmpeg_path:
            logger.warning("⚠️ ffmpeg not available - skipping background music")
            return audio_file
        
        # TODO: Implement background music mixing
        logger.info("🎵 Background music feature not implemented yet")
        return audio_file
    
    async def _create_audio_result(
        self, final_audio: Optional[Path], segments: List[Dict[str, Any]], 
        script: Dict[str, Any], session_id: str
    ) -> Dict[str, Any]:
        """Create comprehensive audio generation result"""
        
        if final_audio and final_audio.exists():
            return {
                "success": True,
                "audio_file": str(final_audio),
                "audio_path": str(final_audio),  # For cover generation compatibility
                "session_id": session_id,
                "segments_count": len(segments),
                "file_size": final_audio.stat().st_size,
                "duration": await self._get_audio_duration(final_audio),
                "format": final_audio.suffix[1:],
                "generated_at": datetime.now().isoformat(),
                "speakers_used": list(set(s.get("speaker", "unknown") for s in segments))
            }
        else:
            return {
                "success": False,
                "error": "Audio generation failed",
                "session_id": session_id,
                "generated_at": datetime.now().isoformat()
            }
    
    async def _create_fallback_audio(self, script: Dict[str, Any], export_format: str) -> Dict[str, Any]:
        """Create fallback result when audio generation fails"""
        
        session_id = script.get("session_id", "fallback")
        
        return {
            "success": False,
            "error": "ElevenLabs API not available",
            "session_id": session_id,
            "fallback_mode": True,
            "script_content": script.get("script_content", ""),
            "generated_at": datetime.now().isoformat()
        }
    
    async def _get_audio_duration(self, audio_file: Path) -> float:
        """Get audio file duration using ffprobe"""
        
        if not self._ffmpeg_path:
            return 0.0
        
        try:
            ffprobe_path = self._ffmpeg_path.replace("ffmpeg", "ffprobe")
            cmd = [
                ffprobe_path,
                "-v", "quiet",
                "-show_entries", "format=duration",
                "-of", "csv=p=0",
                str(audio_file)
            ]
            
            result = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await result.communicate()
            
            return float(stdout.decode().strip())
            
        except Exception:
            return 0.0
    
    async def test_audio_generation(self) -> bool:
        """Test audio generation functionality"""
        
        test_script = {
            "session_id": "test",
            "script_content": "MARCEL: Dies ist ein Test der Audio-Generierung."
        }
        
        try:
            result = await self.generate_audio_from_script(test_script)
            return result.get("success", False)
        except Exception:
            return False
    
    async def cleanup_old_files(self, days_old: int = None) -> Dict[str, Any]:
        """Clean up old audio files efficiently"""
        
        days_old = days_old or self._config.cleanup_days
        cutoff_date = datetime.now() - timedelta(days=days_old)
        
        deleted_count = 0
        total_size = 0
        
        try:
            for file_path in self._output_dir.glob("*.mp3"):
                if file_path.stat().st_mtime < cutoff_date.timestamp():
                    total_size += file_path.stat().st_size
                    file_path.unlink()
                    deleted_count += 1
            
            logger.info(f"🗑️ Cleaned up {deleted_count} old files ({total_size / 1024 / 1024:.1f} MB)")
            
            return {
                "success": True,
                "deleted_files": deleted_count,
                "freed_space_mb": total_size / 1024 / 1024
            }
            
        except Exception as e:
            logger.error(f"❌ Cleanup failed: {e}")
            return {"success": False, "error": str(e)}
    
    def get_audio_statistics(self) -> Dict[str, Any]:
        """Get audio generation statistics"""
        
        try:
            audio_files = list(self._output_dir.glob("*.mp3"))
            total_size = sum(f.stat().st_size for f in audio_files)
            
            return {
                "total_files": len(audio_files),
                "total_size_mb": total_size / 1024 / 1024,
                "output_directory": str(self._output_dir),
                "ffmpeg_available": self._ffmpeg_path is not None,
                "elevenlabs_configured": bool(self._settings.elevenlabs_api_key)
            }
            
        except Exception as e:
            return {"error": str(e)}

# Legacy compatibility methods
    async def generate_audio(self, *args, **kwargs):
        """Legacy method for backward compatibility"""
        return await self.generate_audio_from_script(*args, **kwargs)
    
    async def generate_audio_from_processed_data(
        self, processed_data: Dict[str, Any], **kwargs
    ) -> Dict[str, Any]:
        """Generate audio from processed content data"""
        
        # Extract radio script from processed data
        radio_script = processed_data.get("radio_script", "")
        session_id = f"show_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        script = {
            "session_id": session_id,
            "script_content": radio_script
        }
        
        # Filter nur unterstützte Parameter für generate_audio_from_script
        audio_kwargs = {
            k: v for k, v in kwargs.items() 
            if k in ["include_music", "export_format"]
        }
        
        return await self.generate_audio_from_script(script, **audio_kwargs)