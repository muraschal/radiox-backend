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
        
        # Initialize image service with error handling
        try:
            self._image_service = ImageGenerationService()
            logger.debug("✅ ImageGenerationService initialized")
        except Exception as e:
            logger.warning(f"⚠️ ImageGenerationService failed: {e}")
            self._image_service = None
        
        # Setup paths
        self._output_dir = Path(__file__).parent.parent.parent.parent / "outplay"
        self._output_dir.mkdir(parents=True, exist_ok=True)
        self._ffmpeg_path = self._find_ffmpeg()
    
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
        """Parse script into speaker segments efficiently"""
        
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
                    speaker = self._normalize_speaker_name(speaker_raw)
                    segments.append({
                        "speaker": speaker,
                        "text": text,
                        "original_speaker": speaker_raw
                    })
            else:
                # Default speaker for lines without speaker prefix
                segments.append({
                    "speaker": "marcel",
                    "text": line,
                    "original_speaker": "default"
                })
        
        return segments
    
    def _normalize_speaker_name(self, speaker_raw: str) -> str:
        """Normalize speaker names to known voices"""
        
        speaker_lower = speaker_raw.lower().strip()
        
        # Direct mappings
        speaker_map = {
            "marcel": "marcel",
            "jarvis": "jarvis",
            "host": "marcel",
            "moderator": "marcel",
            "anchor": "marcel",
            "ai": "jarvis",
            "assistant": "jarvis",
            "computer": "jarvis"
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
        """Enhance text with speech optimization tags"""
        
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
        else:
            # Natural, conversational delivery
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
    
    async def _add_background_music(self, audio_file: Path, session_id: str) -> Optional[Path]:
        """Add background music to audio file"""
        
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
        
        return await self.generate_audio_from_script(script, **kwargs)