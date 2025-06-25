"""
RadioX Audio Service
Handles ElevenLabs TTS integration and audio generation
REAL IMPLEMENTATION with voice configurations and audio processing
ENHANCED: Supabase Storage integration for Show Library
"""

from fastapi import FastAPI, HTTPException
import httpx
import redis.asyncio as redis
import json
import asyncio
import os
import tempfile
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List
from loguru import logger
from pydantic import BaseModel
from supabase import create_client, Client

app = FastAPI(
    title="RadioX Audio Service",
    description="ElevenLabs TTS and Audio Processing Service", 
    version="1.0.0"
)

# Redis Connection
redis_client: Optional[redis.Redis] = None

# Supabase Connections
supabase_client: Optional[Client] = None  # Regular operations (anon key)
supabase_admin: Optional[Client] = None   # Admin operations (service key)

@app.on_event("startup")
async def startup_event():
    global redis_client, supabase_client, supabase_admin
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    redis_client = redis.from_url(redis_url, decode_responses=True)
    
    # Initialize Supabase for regular operations
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    if supabase_url and supabase_key:
        supabase_client = create_client(supabase_url, supabase_key)
        logger.info("✅ Supabase (anon) connected")
    else:
        logger.warning("⚠️ Supabase anon credentials missing")
    
    # Initialize Supabase for admin operations (storage, etc.)
    supabase_service_key = os.getenv("SUPABASE_SERVICE_KEY")
    if supabase_url and supabase_service_key:
        supabase_admin = create_client(supabase_url, supabase_service_key)
        logger.info("✅ Supabase (admin) connected - Storage enabled")
    else:
        logger.warning("⚠️ Supabase service key missing - storage disabled")
    
    logger.info("Audio Service started successfully")

@app.on_event("shutdown")
async def shutdown_event():
    if redis_client:
        await redis_client.close()
    logger.info("Audio Service shutdown complete")

# Pydantic Models
class AudioRequest(BaseModel):
    text: str
    speaker: str = "marcel"
    voice_quality: str = "mid"
    model_id: Optional[str] = None

class ScriptAudioRequest(BaseModel):
    script_content: str
    session_id: Optional[str] = None
    include_music: bool = False
    export_format: str = "mp3"
    voice_quality: str = "mid"

class ElevenLabsService:
    """ElevenLabs TTS Integration Service"""
    
    def __init__(self):
        self.api_key = os.getenv("ELEVENLABS_API_KEY")
        self.base_url = "https://api.elevenlabs.io/v1"
        self.data_service_url = os.getenv("DATA_SERVICE_URL", "http://data-service:8000")
        
        # Audio configuration
        self.config = {
            "max_parallel_segments": 5,
            "request_timeout": 30,
            "supported_formats": ["mp3", "wav", "ogg"]
        }
    
    async def get_voice_config(self, speaker: str, voice_quality: str = "mid") -> Optional[Dict[str, Any]]:
        """Get voice configuration from Data Service"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.data_service_url}/speakers/{speaker}")
                
                if response.status_code == 200:
                    voice_data = response.json()
                    
                    # Get model based on quality
                    model_mapping = {
                        "low": "eleven_turbo_v2_5",
                        "mid": "eleven_multilingual_v2", 
                        "high": "eleven_multilingual_v2",
                        "ultra": "eleven_multilingual_v2"
                    }
                    
                    return {
                        "voice_id": voice_data["voice_id"],
                        "model_id": model_mapping.get(voice_quality, "eleven_multilingual_v2"),
                        "stability": 0.5,
                        "similarity_boost": 0.8,
                        "style": 0.0,
                        "use_speaker_boost": True
                    }
                else:
                    logger.warning(f"⚠️ Voice config not found for {speaker}")
                    return None
                    
        except Exception as e:
            logger.error(f"❌ Voice config lookup failed: {str(e)}")
            return None
    
    async def generate_speech(self, request: AudioRequest) -> Optional[bytes]:
        """Generate speech from text using ElevenLabs"""
        if not self.api_key:
            logger.warning("⚠️ ElevenLabs API key not configured")
            return None
        
        try:
            # Get voice configuration
            voice_config = await self.get_voice_config(request.speaker, request.voice_quality)
            if not voice_config:
                logger.error(f"❌ No voice config for speaker: {request.speaker}")
                return None
            
            # Prepare API request
            voice_id = voice_config["voice_id"]
            url = f"{self.base_url}/text-to-speech/{voice_id}"
            
            payload = {
                "text": self._enhance_text_for_speech(request.text, request.speaker),
                "model_id": request.model_id or voice_config["model_id"],
                "voice_settings": {
                    "stability": voice_config["stability"],
                    "similarity_boost": voice_config["similarity_boost"],
                    "style": voice_config["style"],
                    "use_speaker_boost": voice_config["use_speaker_boost"]
                }
            }
            
            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": self.api_key
            }
            
            logger.info(f"🎤 Generating speech for {request.speaker} with voice ID: {voice_id}")
            
            async with httpx.AsyncClient(timeout=self.config["request_timeout"]) as client:
                response = await client.post(url, json=payload, headers=headers)
                
                if response.status_code == 200:
                    audio_data = response.content
                    logger.info(f"✅ Generated {len(audio_data)} bytes of audio")
                    return audio_data
                else:
                    error_text = response.text
                    logger.error(f"❌ ElevenLabs API error {response.status_code}: {error_text}")
                    return None
                    
        except Exception as e:
            logger.error(f"❌ Speech generation failed: {str(e)}")
            return None
    
    def _enhance_text_for_speech(self, text: str, speaker: str) -> str:
        """Enhance text for better speech synthesis"""
        enhanced_text = text
        
        # Speaker-specific enhancements
        if speaker.lower() == "marcel":
            # Marcel: More emotional, enthusiastic
            enhanced_text = enhanced_text.replace("!", "!!")
            enhanced_text = enhanced_text.replace("Bitcoin", "Bitcoin")  # Emphasis
        elif speaker.lower() == "jarvis":
            # Jarvis: More analytical, precise
            enhanced_text = enhanced_text.replace("...", "... ")
            enhanced_text = enhanced_text.replace(".", ". ")
        
        # General enhancements
        enhanced_text = enhanced_text.replace("RadioX", "Radio X")
        enhanced_text = enhanced_text.replace("AI", "A I")
        enhanced_text = enhanced_text.replace("API", "A P I")
        
        return enhanced_text

class AudioProcessingService:
    """Audio processing and script handling service"""
    
    def __init__(self):
        self.elevenlabs = ElevenLabsService()
        self.temp_dir = Path(tempfile.gettempdir()) / "radiox_audio"
        self.temp_dir.mkdir(exist_ok=True)
        self.ffmpeg_path = self._find_ffmpeg()
        self.storage_bucket = "radio-shows"
    
    def _find_ffmpeg(self) -> Optional[str]:
        """Find available ffmpeg executable"""
        candidates = ["ffmpeg", "/usr/bin/ffmpeg", "/usr/local/bin/ffmpeg"]
        
        for candidate in candidates:
            try:
                result = subprocess.run([candidate, '-version'], 
                                      capture_output=True, timeout=5)
                if result.returncode == 0:
                    logger.info(f"✅ Found ffmpeg: {candidate}")
                    return candidate
            except (FileNotFoundError, subprocess.TimeoutExpired):
                continue
        
        logger.warning("⚠️ ffmpeg not found - audio processing limited")
        return None
    
    def _parse_script_into_segments(self, script_content: str) -> List[Dict[str, Any]]:
        """Parse script into speaker segments"""
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
                # Default to marcel for untagged lines
                segments.append({
                    "speaker": "marcel",
                    "text": line,
                    "original_speaker": "default"
                })
        
        return segments
    
    def _normalize_speaker_name(self, speaker_raw: str) -> str:
        """Normalize speaker names"""
        speaker_lower = speaker_raw.lower().strip()
        
        # Direct mappings
        mappings = {
            "marcel": "marcel",
            "jarvis": "jarvis", 
            "brad": "brad",
            "lucy": "lucy"
        }
        
        # Check exact matches first
        if speaker_lower in mappings:
            return mappings[speaker_lower]
        
        # Fuzzy matching
        for key, value in mappings.items():
            if key in speaker_lower:
                return value
        
        # Default fallback
        return "marcel"
    
    async def generate_audio_from_script(self, request: ScriptAudioRequest) -> Dict[str, Any]:
        """Generate complete audio from script"""
        try:
            session_id = request.session_id or f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            logger.info(f"🎭 Generating audio for session: {session_id}")
            
            # Parse script into segments
            segments = self._parse_script_into_segments(request.script_content)
            
            if not segments:
                raise HTTPException(status_code=400, detail="No segments parsed from script")
            
            logger.info(f"📝 Parsed {len(segments)} segments")
            
            # Generate audio for each segment
            audio_files = await self._generate_segments_parallel(segments, session_id, request.voice_quality)
            
            # Filter valid files
            valid_files = [f for f in audio_files if f and Path(f).exists()]
            
            if not valid_files:
                raise HTTPException(status_code=500, detail="No valid audio segments generated")
            
            logger.info(f"🎵 Generated {len(valid_files)} audio segments")
            
            # Combine audio segments
            combined_audio = await self._combine_audio_segments(valid_files, session_id, request.export_format)
            
            if not combined_audio:
                raise HTTPException(status_code=500, detail="Failed to combine audio segments")
            
            # Add jingle if requested
            final_audio = combined_audio
            if request.include_music:
                final_audio = await self._add_simple_jingle(combined_audio, session_id)
            
            # Get audio info
            duration = await self._get_audio_duration(final_audio) if final_audio else 0
            file_size = final_audio.stat().st_size if final_audio and final_audio.exists() else 0
            
            # Prepare metadata for storage upload
            upload_metadata = {
                "preset_name": getattr(request, 'preset_name', 'default'),
                "speakers": {seg["speaker"] for seg in segments},
                "duration_minutes": getattr(request, 'duration_minutes', 
                                          max(1, int(duration / 60)) if duration > 0 else 1)
            }
            
            # Upload to Supabase Storage
            storage_url = await self.upload_to_storage(final_audio, session_id, upload_metadata) if final_audio else None
            
            # Prepare response data
            result_data = {
                "success": True,
                "session_id": session_id,
                "audio_file": str(final_audio) if final_audio else None,  # Local temp file for backward compatibility
                "audio_url": storage_url,  # New: Permanent storage URL
                "segments_count": len(segments),
                "duration_seconds": duration,
                "file_size_bytes": file_size,
                "format": request.export_format,
                "generated_at": datetime.now().isoformat(),
                "storage_uploaded": storage_url is not None
            }
            
            # Save to database if storage upload succeeded
            if storage_url:
                show_data = {
                    "script_content": request.script_content,
                    "file_size_bytes": file_size,
                    "duration_seconds": duration,
                    "segments_count": len(segments),
                    "format": request.export_format,
                    "generated_at": result_data["generated_at"],
                    "preset_name": getattr(request, 'preset_name', 'default'),
                    "show_title": f"RadioX Show {datetime.now().strftime('%H:%M')}",
                    "show_description": f"AI-generated show with {len(segments)} segments",
                    "speakers": {seg["speaker"] for seg in segments}
                }
                
                await self.save_show_to_database(session_id, show_data, storage_url)
            
            return result_data
            
        except Exception as e:
            logger.error(f"❌ Audio generation failed: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Audio generation failed: {str(e)}")
    
    async def _generate_segments_parallel(
        self, segments: List[Dict[str, Any]], session_id: str, voice_quality: str
    ) -> List[Optional[str]]:
        """Generate audio segments in parallel"""
        
        semaphore = asyncio.Semaphore(self.elevenlabs.config["max_parallel_segments"])
        
        async def limited_generation(segment: Dict[str, Any], index: int) -> Optional[str]:
            async with semaphore:
                return await self._generate_single_segment(segment, session_id, index, voice_quality)
        
        tasks = [
            limited_generation(segment, i) 
            for i, segment in enumerate(segments)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return [r for r in results if isinstance(r, str)]
    
    async def _generate_single_segment(
        self, segment: Dict[str, Any], session_id: str, index: int, voice_quality: str
    ) -> Optional[str]:
        """Generate single audio segment"""
        try:
            speaker = segment.get("speaker", "marcel")
            text = segment.get("text", "").strip()
            
            if not text:
                return None
            
            # Generate speech
            audio_request = AudioRequest(
                text=text,
                speaker=speaker,
                voice_quality=voice_quality
            )
            
            audio_data = await self.elevenlabs.generate_speech(audio_request)
            
            if not audio_data:
                return None
            
            # Save audio file
            filename = f"{session_id}_segment_{index:03d}_{speaker}.mp3"
            filepath = self.temp_dir / filename
            
            with open(filepath, 'wb') as f:
                f.write(audio_data)
            
            logger.info(f"✅ Generated segment {index}: {speaker} ({len(text)} chars)")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"❌ Segment generation failed: {str(e)}")
            return None
    
    async def _combine_audio_segments(
        self, audio_files: List[str], session_id: str, export_format: str
    ) -> Optional[Path]:
        """Combine audio segments using ffmpeg"""
        if not self.ffmpeg_path:
            logger.warning("⚠️ ffmpeg not available - returning first segment only")
            return Path(audio_files[0]) if audio_files else None
        
        try:
            # Create file list for ffmpeg
            filelist_path = self.temp_dir / f"{session_id}_filelist.txt"
            
            with open(filelist_path, 'w') as f:
                for audio_file in audio_files:
                    f.write(f"file '{audio_file}'\n")
            
            # Output file
            output_file = self.temp_dir / f"{session_id}_combined.{export_format}"
            
            # ffmpeg command
            cmd = [
                self.ffmpeg_path,
                "-f", "concat",
                "-safe", "0", 
                "-i", str(filelist_path),
                "-c", "copy",
                "-y",  # Overwrite output file
                str(output_file)
            ]
            
            # Run ffmpeg
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0 and output_file.exists():
                logger.info(f"✅ Combined {len(audio_files)} segments into {output_file}")
                
                # Cleanup temporary files
                filelist_path.unlink(missing_ok=True)
                for audio_file in audio_files:
                    Path(audio_file).unlink(missing_ok=True)
                
                return output_file
            else:
                logger.error(f"❌ ffmpeg failed: {result.stderr}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Audio combination failed: {str(e)}")
            return None
    
    async def _add_simple_jingle(self, audio_file: Path, session_id: str) -> Optional[Path]:
        """Add simple jingle (placeholder - would need actual jingle files)"""
        # For now, just return the original file
        # In real implementation, this would add intro/outro jingles
        logger.info("🎵 Jingle addition skipped (no jingle files configured)")
        return audio_file
    
    async def _get_audio_duration(self, audio_file: Path) -> float:
        """Get audio duration using ffmpeg"""
        if not self.ffmpeg_path or not audio_file.exists():
            return 0.0
        
        try:
            cmd = [
                self.ffmpeg_path,
                "-i", str(audio_file),
                "-f", "null",
                "-"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            # Parse duration from ffmpeg output
            for line in result.stderr.split('\n'):
                if 'Duration:' in line:
                    duration_str = line.split('Duration:')[1].split(',')[0].strip()
                    # Parse HH:MM:SS.mmm format
                    parts = duration_str.split(':')
                    if len(parts) == 3:
                        hours = float(parts[0])
                        minutes = float(parts[1]) 
                        seconds = float(parts[2])
                        return hours * 3600 + minutes * 60 + seconds
            
            return 0.0
            
        except Exception as e:
            logger.warning(f"⚠️ Duration detection failed: {str(e)}")
            return 0.0
    
    async def upload_to_storage(self, audio_file: Path, session_id: str, show_metadata: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """Upload audio file to Supabase Storage with human-readable filename"""
        global supabase_admin
        
        if not supabase_admin:
            logger.warning("⚠️ Supabase admin not available - skipping upload")
            return None
        
        try:
            # Generate human-readable filename
            now = datetime.now()
            date_str = now.strftime("%Y-%m-%d")
            time_str = now.strftime("%H-%M")
            
            # Extract metadata for filename
            preset_name = show_metadata.get("preset_name", "default") if show_metadata else "default"
            speakers = show_metadata.get("speakers", set()) if show_metadata else set()
            duration = show_metadata.get("duration_minutes", 0) if show_metadata else 0
            
            # Create speaker string
            if isinstance(speakers, set):
                speaker_list = sorted(list(speakers))
            elif isinstance(speakers, list):
                speaker_list = sorted(speakers)
            else:
                speaker_list = ["unknown"]
            
            speaker_str = "-".join(speaker_list[:2])  # Max 2 speakers in filename
            
            # Sanitize preset name
            preset_clean = preset_name.lower().replace("_", "-").replace(" ", "-")
            
            # Build filename: YYYY-MM-DD_HH-MM_preset_speakers_duration.mp3
            filename_parts = [
                date_str,
                time_str,
                preset_clean,
                speaker_str,
                f"{duration}min"
            ]
            
            filename_base = "_".join(filename_parts)
            # Remove any unsafe characters
            import re
            filename_base = re.sub(r'[^a-zA-Z0-9_-]', '', filename_base)
            
            filename = f"shows/{filename_base}.mp3"
            
            # Read file data
            with open(audio_file, 'rb') as f:
                file_data = f.read()
            
            # Upload to storage
            result = supabase_admin.storage.from_(self.storage_bucket).upload(
                filename, 
                file_data,
                file_options={
                    "content-type": "audio/mpeg",
                    "cache-control": "3600"
                }
            )
            
            if result:
                # Get public URL
                public_url = supabase_admin.storage.from_(self.storage_bucket).get_public_url(filename)
                logger.info(f"✅ Uploaded to storage: {filename}")
                return public_url
            else:
                logger.error("❌ Storage upload failed")
                return None
                
        except Exception as e:
            logger.error(f"❌ Storage upload error: {str(e)}")
            return None
    
    async def save_show_to_database(self, session_id: str, show_data: Dict[str, Any], audio_url: str) -> bool:
        """Save show metadata to broadcast_logs table"""
        global supabase_client
        
        if not supabase_client:
            logger.warning("⚠️ Supabase not available - skipping database save")
            return False
        
        try:
            # Prepare show record
            show_record = {
                "session_id": session_id,
                "timestamp": datetime.now().isoformat(),
                "script_content": show_data.get("script_content", ""),
                "audio_file_url": audio_url,
                "audio_file_size": show_data.get("file_size_bytes", 0),
                "audio_duration_seconds": show_data.get("duration_seconds", 0),
                "show_title": show_data.get("show_title", f"RadioX Show {session_id}"),
                "show_description": show_data.get("show_description", "AI-generated radio show"),
                "preset_name": show_data.get("preset_name", "default"),
                "duration_minutes": show_data.get("duration_minutes", 0),
                "data": {
                    "segments_count": show_data.get("segments_count", 0),
                    "format": show_data.get("format", "mp3"),
                    "generated_at": show_data.get("generated_at"),
                    "speakers": list(show_data.get("speakers", set())) if isinstance(show_data.get("speakers"), set) else show_data.get("speakers", [])
                }
            }
            
            # Insert into database
            result = supabase_client.table("broadcast_logs").insert(show_record).execute()
            
            if result.data:
                logger.info(f"✅ Show saved to database: {session_id}")
                return True
            else:
                logger.error("❌ Database insert failed")
                return False
                
        except Exception as e:
            logger.error(f"❌ Database save error: {str(e)}")
            return False

audio_service = AudioProcessingService()

# Health Check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "audio-service"}

# Audio Generation
@app.post("/generate")
async def generate_audio(request: AudioRequest):
    """Generate audio from text"""
    audio_data = await audio_service.elevenlabs.generate_speech(request)
    
    if not audio_data:
        raise HTTPException(status_code=500, detail="Audio generation failed")
    
    # Save to temporary file and return info
    filename = f"audio_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{request.speaker}.mp3"
    filepath = audio_service.temp_dir / filename
    
    with open(filepath, 'wb') as f:
        f.write(audio_data)
    
    return {
        "success": True,
        "audio_file": str(filepath),
        "speaker": request.speaker,
        "text_length": len(request.text),
        "file_size_bytes": len(audio_data),
        "generated_at": datetime.now().isoformat()
    }

@app.post("/script")
async def generate_script_audio(request: ScriptAudioRequest):
    """Generate audio from complete script"""
    return await audio_service.generate_audio_from_script(request)

@app.get("/voices")
async def get_available_voices():
    """Get available voice configurations"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{audio_service.elevenlabs.data_service_url}/speakers")
            
            if response.status_code == 200:
                speakers = response.json()
                return [
                    {
                        "id": speaker["voice_id"],
                        "name": speaker["name"],
                        "language": speaker["language"]
                    }
                    for speaker in speakers
                ]
            else:
                return {"error": "Failed to fetch voices"}
                
    except Exception as e:
        return {"error": f"Voice lookup failed: {str(e)}"}

@app.get("/temp-files")
async def list_temp_files():
    """List temporary audio files"""
    try:
        files = []
        for file in audio_service.temp_dir.glob("*.mp3"):
            stat = file.stat()
            files.append({
                "filename": file.name,
                "size_bytes": stat.st_size,
                "created": datetime.fromtimestamp(stat.st_ctime).isoformat()
            })
        
        return {"temp_files": files, "temp_dir": str(audio_service.temp_dir)}
        
    except Exception as e:
        return {"error": f"Failed to list files: {str(e)}"}

@app.get("/temp-files/{filename}")
async def get_temp_file(filename: str):
    """Download a specific temporary audio file"""
    try:
        # Security: Only allow safe filenames
        if not filename.endswith('.mp3') or '/' in filename or '..' in filename:
            raise HTTPException(status_code=400, detail="Invalid filename")
        
        file_path = audio_service.temp_dir / filename
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Audio file not found")
        
        # Read file content
        with open(file_path, 'rb') as f:
            audio_data = f.read()
        
        from fastapi.responses import Response
        
        return Response(
            content=audio_data,
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": f"inline; filename={filename}",
                "Content-Length": str(len(audio_data)),
                "Cache-Control": "public, max-age=3600"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to serve temp file {filename}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to serve audio file")

@app.get("/shows")
async def list_shows(limit: int = 10, offset: int = 0):
    """List shows from database"""
    global supabase_client
    
    if not supabase_client:
        raise HTTPException(status_code=503, detail="Database not available")
    
    try:
        result = supabase_client.table("broadcast_logs")\
            .select("*")\
            .order("created_at", desc=True)\
            .range(offset, offset + limit - 1)\
            .execute()
        
        shows = []
        for record in result.data:
            # Parse data field if it's a string
            data_field = record.get("data", {})
            if isinstance(data_field, str):
                try:
                    import json
                    data_field = json.loads(data_field)
                except:
                    data_field = {}
            
            shows.append({
                "id": record.get("id"),
                "session_id": record.get("session_id"),
                "show_title": record.get("show_title", f"Show {record.get('session_id', 'Unknown')}"),
                "show_description": record.get("show_description", ""),
                "audio_url": record.get("audio_file_url"),
                "duration_seconds": record.get("audio_duration_seconds", 0),
                "file_size_bytes": record.get("audio_file_size", 0),
                "preset_name": record.get("preset_name", "default"),
                "created_at": record.get("created_at"),
                "speakers": data_field.get("speakers", []) if isinstance(data_field, dict) else []
            })
        
        return {
            "success": True,
            "shows": shows,
            "total": len(shows),
            "offset": offset,
            "limit": limit
        }
        
    except Exception as e:
        logger.error(f"❌ Shows listing failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to list shows")

@app.get("/shows/{session_id}")
async def get_show(session_id: str):
    """Get specific show details"""
    global supabase_client
    
    if not supabase_client:
        raise HTTPException(status_code=503, detail="Database not available")
    
    try:
        result = supabase_client.table("broadcast_logs")\
            .select("*")\
            .eq("session_id", session_id)\
            .single()\
            .execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Show not found")
        
        record = result.data
        return {
            "success": True,
            "show": {
                "id": record.get("id"),
                "session_id": record.get("session_id"),
                "show_title": record.get("show_title"),
                "show_description": record.get("show_description"),
                "script_content": record.get("script_content"),
                "audio_url": record.get("audio_file_url"),
                "duration_seconds": record.get("audio_duration_seconds", 0),
                "file_size_bytes": record.get("audio_file_size", 0),
                "preset_name": record.get("preset_name"),
                "created_at": record.get("created_at"),
                "data": record.get("data", {})
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Show retrieval failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get show")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 