#!/usr/bin/env python3
"""
Image Generation Service
========================

Separater Service für Cover-Art Generierung:
- DALL-E Integration für AI-generierte Cover
- MP3 Metadata + Cover Embedding  
- Broadcast-spezifische Designs
"""

import asyncio
import aiohttp
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from loguru import logger
from PIL import Image, ImageDraw, ImageFont
import subprocess

# Import centralized settings
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))
from config.settings import get_settings


class ImageGenerationService:
    """Service für AI-generierte Cover-Art"""
    
    def __init__(self):
        # Load settings centrally
        self.settings = get_settings()
        self.openai_api_key = self.settings.openai_api_key
        self.dall_e_base_url = "https://api.openai.com/v1/images/generations"
        
        # Output-Verzeichnis - outplay für HTML Dashboard Zugriff
        self.output_dir = Path(__file__).parent.parent.parent.parent / "outplay"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Cover-Konfiguration
        self.config = {
            "image_size": "1024x1024",
            "image_quality": "hd", 
            "style": "vivid",
            "timeout": 60
        }
    
    async def generate_cover_art(
        self,
        session_id: str,
        broadcast_content: Dict[str, Any],
        target_time: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generiert AI Cover-Art für Broadcast"""
        
        logger.info(f"🎨 Generiere Cover-Art für Session {session_id}")
        
        if not self.openai_api_key:
            return await self._generate_fallback_cover(session_id, broadcast_content)
        
        try:
            # 1. DALL-E Prompt erstellen
            prompt = self._create_dalle_prompt(broadcast_content, target_time)
            
            # 2. DALL-E API Request
            cover_url = await self._request_dalle_image(prompt)
            
            if not cover_url:
                return await self._generate_fallback_cover(session_id, broadcast_content)
            
            # 3. Cover-Image herunterladen
            cover_path = await self._download_cover_image(cover_url, session_id)
            
            if not cover_path:
                return await self._generate_fallback_cover(session_id, broadcast_content)
            
            result = {
                "success": True,
                "session_id": session_id,
                "cover_path": str(cover_path),
                "cover_filename": cover_path.name,
                "dalle_prompt": prompt,
                "generation_timestamp": datetime.now().isoformat(),
                "cover_type": "ai_generated"
            }
            
            logger.info(f"✅ AI Cover-Art generiert: {cover_path.name}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Fehler bei Cover-Generierung: {e}")
            return await self._generate_fallback_cover(session_id, broadcast_content)
    
    async def embed_cover_in_mp3(
        self,
        audio_file: Path,
        cover_file: Path,
        metadata: Dict[str, Any]
    ) -> bool:
        """Bettet Cover-Art in MP3-Datei ein mit ffmpeg"""
        
        logger.info(f"🏷️ Bette Cover in MP3 ein: {audio_file.name}")
        
        try:
            # FFmpeg-Pfad für macOS/Linux (system PATH)
            import subprocess
            
            # Prüfe ob ffmpeg im System verfügbar ist
            try:
                result = subprocess.run(['ffmpeg', '-version'], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    ffmpeg_cmd = 'ffmpeg'
                    logger.debug(f"✅ FFmpeg gefunden im System PATH")
                else:
                    logger.warning("⚠️ ffmpeg nicht verfügbar - Cover-Embedding übersprungen")
                    return False
            except Exception as e:
                logger.warning(f"⚠️ ffmpeg Fehler: {e} - Cover-Embedding übersprungen")
                return False
            
            # Erstelle temporäre Ausgabedatei
            temp_output = audio_file.parent / f"temp_with_cover_{audio_file.stem}.mp3"
            
            # Metadaten für FFmpeg-Embedding im gewünschten Format
            current_time = datetime.now()
            hour_min = current_time.strftime('%H:%M')
            edition_name = self._get_edition_name_for_metadata(hour_min)
            title = f"RadioX - {edition_name} : {hour_min} Edition"
            
            # Verbesserte ffmpeg Kommando für MP3-Cover-Embedding
            ffmpeg_command = [
                ffmpeg_cmd, '-y',  # Überschreibe Ausgabedatei
                '-i', str(audio_file),  # Audio-Input
                '-i', str(cover_file),  # Cover-Input
                '-map', '0:a',  # Audio-Stream (explizit)
                '-map', '1:v',  # Cover-Stream (explizit)
                '-c:a', 'copy',  # Audio ohne Re-Encoding
                '-c:v', 'copy',  # Cover ohne Re-Encoding
                '-id3v2_version', '3',  # ID3v2.3 für Windows Media Player Kompatibilität
                '-metadata:s:v', 'title=Album cover',  # Cover-Titel
                '-metadata:s:v', 'comment=Cover',  # Cover-Kommentar
                '-metadata', f'title={title}',  # Track-Titel im gewünschten Format
                '-metadata', 'artist=RadioX AI',  # Künstler
                '-metadata', 'album=RadioX News Broadcasts',  # Album
                '-metadata', 'genre=News/Talk',  # Genre
                '-disposition:v:0', 'attached_pic',  # Cover als attached picture markieren
                str(temp_output)
            ]
            
            # Führe ffmpeg aus mit detailliertem Logging
            logger.debug(f"🔧 FFmpeg Command: {' '.join(ffmpeg_command)}")
            
            result = subprocess.run(ffmpeg_command, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0 and temp_output.exists():
                # Ersetze Original-Datei mit Cover-Version
                import shutil
                shutil.move(str(temp_output), str(audio_file))
                
                logger.success(f"✅ Cover erfolgreich via FFmpeg in MP3 eingebettet: {audio_file.name}")
                return True
            else:
                logger.warning(f"⚠️ ffmpeg Cover-Embedding fehlgeschlagen: {result.stderr}")
                # Lösche temporäre Datei falls vorhanden
                if temp_output.exists():
                    temp_output.unlink()
                
                # FALLBACK: Versuche eyed3
                logger.info(f"🔄 Versuche Fallback mit eyed3...")
                return await self._embed_cover_with_eyed3(audio_file, cover_file, metadata)
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Cover-Embedding: {e}")
            return False
    
    async def _embed_cover_with_eyed3(self, audio_file: Path, cover_file: Path, metadata: Dict[str, Any]) -> bool:
        """Fallback: Cover-Embedding mit eyed3 (wenn ffmpeg fehlschlägt)"""
        
        try:
            import eyed3
            from PIL import Image
            import io
            
            logger.info(f"🎨 Bette Cover mit eyed3 ein: {audio_file.name}")
            
            # Cover zu JPEG konvertieren für bessere Kompatibilität
            with Image.open(cover_file) as img:
                # Zu RGB konvertieren (PNG könnte RGBA sein)
                if img.mode in ('RGBA', 'LA', 'P'):
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    if img.mode == 'RGBA':
                        background.paste(img, mask=img.split()[-1])
                    else:
                        background.paste(img)
                    img = background
                elif img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Optimale Größe für Cover-Art (500x500)
                img.thumbnail((500, 500), Image.Resampling.LANCZOS)
                
                # Als JPEG in Memory speichern
                jpeg_buffer = io.BytesIO()
                img.save(jpeg_buffer, format='JPEG', quality=90, optimize=True)
                jpeg_data = jpeg_buffer.getvalue()
            
            # MP3 laden
            audiofile = eyed3.load(str(audio_file))
            
            if audiofile is None:
                logger.error("❌ MP3-Datei konnte nicht mit eyed3 geladen werden")
                return False
            
            # Tag initialisieren falls nicht vorhanden
            if audiofile.tag is None:
                audiofile.initTag()
            
            # Alte Cover entfernen
            try:
                for img_type in [eyed3.id3.frames.ImageFrame.FRONT_COVER, 
                               eyed3.id3.frames.ImageFrame.BACK_COVER,
                               eyed3.id3.frames.ImageFrame.OTHER]:
                    try:
                        audiofile.tag.images.remove(img_type)
                    except (ValueError, TypeError):
                        pass
            except:
                pass
            
            # Neues Cover einbetten
            audiofile.tag.images.set(
                eyed3.id3.frames.ImageFrame.FRONT_COVER,
                jpeg_data,
                "image/jpeg",
                description="RadioX Cover Art"
            )
            
            # Metadaten setzen im gewünschten Format
            current_time = datetime.now()
            hour_min = current_time.strftime('%H:%M')
            edition_name = self._get_edition_name_for_metadata(hour_min)
            
            audiofile.tag.title = f"RadioX - {edition_name} : {hour_min} Edition"
            audiofile.tag.artist = "RadioX AI"
            audiofile.tag.album = "RadioX News Broadcasts"
            audiofile.tag.album_artist = "RadioX AI"
            audiofile.tag.genre = "News/Talk"
            audiofile.tag.recording_date = current_time.year
            
            # Mit ID3v2.3 speichern (bessere Kompatibilität)
            audiofile.tag.save(version=eyed3.id3.ID3_V2_3)
            
            logger.success(f"✅ Cover erfolgreich via eyed3 in MP3 eingebettet: {audio_file.name}")
            return True
            
        except ImportError:
            logger.error("❌ eyed3 nicht verfügbar - Cover-Embedding fehlgeschlagen")
            return False
        except Exception as e:
            logger.error(f"❌ eyed3 Cover-Embedding Fehler: {e}")
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
    
    # Private Methods
    
    def _create_dalle_prompt(self, broadcast_content: Dict[str, Any], target_time: Optional[str] = None) -> str:
        """🎨 UNIVERSELLER PROMPT FÜR RADIOX COVER GENERATOR"""
        
        # Extract dynamic values from broadcast content
        edition_name = self._get_edition_name(target_time)
        show_style = self._extract_show_style(broadcast_content)
        speakers = self._extract_speaker_descriptions(broadcast_content)
        time_mood = self._get_time_mood(target_time)
        topic_symbols = self._extract_topic_symbols(broadcast_content)
        
        # Create the new professional prompt
        prompt = f"""Create a cinematic, AI-generated visual cover for the fictional radio show "RADIO X – {edition_name}".

📍 Context:
This is a {show_style}

🎙️ Speakers:
The hosts should be subtly represented in the image:
{speakers}

🕒 Time of Day:
Reflect the visual mood of {time_mood}

🧠 Content:
Represent the following news topics with visual **symbolism only** (no text or direct illustration):
{topic_symbols['symbol_1']}
{topic_symbols['symbol_2']}
{topic_symbols['symbol_3']}

🎨 Art Direction:
– Magazine-style composition or streaming platform key art
– Strong composition, minimal color palette, cinematic contrast
– No headlines, no article text – only RADIO X logo and EDITION title in modern typography
– Style mix: cyberpunk x Swiss brutalism x symbolic realism"""

        logger.debug(f"🎨 Cinematic RadioX Cover Prompt created for {edition_name}")
        return prompt
    
    def _extract_show_style(self, broadcast_content: Dict[str, Any]) -> str:
        """Extract full show style description from DB"""
        
        # Try to get from show configuration
        show_config = broadcast_content.get("show_config", {})
        show_details = show_config.get("show", {})
        
        show_name = show_details.get("name", "Radio Show")
        city_focus = show_details.get("city_focus", "Local")
        description = show_details.get("description", "")
        
        if description:
            return f"{show_name} show with {city_focus} focus: {description}"
        else:
            return f"{show_name} radio show with {city_focus} focus."
    
    def _extract_speaker_descriptions(self, broadcast_content: Dict[str, Any]) -> str:
        """Extract speaker descriptions directly from DB"""
        
        show_config = broadcast_content.get("show_config", {})
        
        # Get primary speaker
        primary_speaker = show_config.get("speaker", {})
        primary_name = primary_speaker.get("voice_name", "Host")
        primary_desc = primary_speaker.get("description", "Radio host")
        
        # Get secondary speaker if duo show
        secondary_speaker = show_config.get("secondary_speaker", {})
        secondary_name = secondary_speaker.get("voice_name", "Co-Host")
        secondary_desc = secondary_speaker.get("description", "AI assistant")
        
        # Build speaker list
        speakers_text = f"– {primary_name}: {self._create_visual_description(primary_name, primary_desc)}"
        
        # Check if duo show
        is_duo_show = show_config.get("show", {}).get("is_duo_show", False)
        if is_duo_show and secondary_speaker:
            speakers_text += f"\n– {secondary_name}: {self._create_visual_description(secondary_name, secondary_desc)}"
        
        # Check for weather speaker (Lucy) if weather category active
        rss_categories = show_config.get("content", {}).get("rss_filter", {}).get("categories", [])
        if "weather" in rss_categories:
            weather_speaker = show_config.get("weather_speaker", {})
            weather_name = weather_speaker.get("voice_name", "Lucy")
            weather_desc = weather_speaker.get("description", "Weather specialist")
            speakers_text += f"\n– {weather_name}: {self._create_visual_description(weather_name, weather_desc)}"
        
        return speakers_text
    
    def _create_visual_description(self, name: str, full_description: str) -> str:
        """Convert full speaker description to short visual description for image prompt"""
        
        # Extract key visual traits from full description
        desc_lower = full_description.lower()
        
        if "marcel" in name.lower():
            return "energetic, expressive human with techwear and sharp posture, Mexican heritage visible in features"
        elif "jarvis" in name.lower():
            return "digital, geometric, floating presence with faint blue glow and surgical precision"
        elif "lucy" in name.lower():
            return "sultry, weather-focused figure with atmospheric elements and flowing presence"
        else:
            # Generate based on description keywords
            visual_traits = []
            
            if any(word in desc_lower for word in ["ai", "digital", "synthetic"]):
                visual_traits.append("digital holographic presence")
            if any(word in desc_lower for word in ["energetic", "dynamic"]):
                visual_traits.append("dynamic posture")
            if any(word in desc_lower for word in ["elegant", "sophisticated"]):
                visual_traits.append("elegant appearance")
            if any(word in desc_lower for word in ["weather", "atmospheric"]):
                visual_traits.append("atmospheric elements")
            
            if visual_traits:
                return ", ".join(visual_traits)
            else:
                return "professional radio host presence"
    
    def _get_time_mood(self, target_time: Optional[str]) -> str:
        """Generate Zürich time-specific mood description"""
        
        if not target_time:
            hour = datetime.now().hour
            minute = datetime.now().minute
            time_str = f"{hour:02d}:{minute:02d}"
        else:
            time_str = target_time
            try:
                hour = int(target_time.split(":")[0])
            except:
                hour = datetime.now().hour
        
        # Generate time-specific mood for Zürich
        if 6 <= hour <= 8:
            return f"{time_str} in Zürich = early morning haze, trams starting, concrete cold, coffee steam in winter air"
        elif 9 <= hour <= 11:
            return f"{time_str} in Zürich = business morning, sharp shadows between buildings, professional energy"
        elif 12 <= hour <= 17:
            return f"{time_str} in Zürich = midday clarity, bright corporate glass, clean urban geometry"
        elif 18 <= hour <= 22:
            return f"{time_str} in Zürich = evening transition, warm office lights, sophisticated urban twilight"
        elif 23 <= hour <= 2:
            return f"{time_str} in Zürich = dark neon, backlit alleys, glitchy reflections in wet streets"
        else:  # 3-5
            return f"{time_str} in Zürich = surreal loneliness, empty roads, faint data pulses in sleeping city"
    
    def _get_edition_name(self, target_time: Optional[str]) -> str:
        """Generate edition name based on time"""
        if not target_time:
            hour = datetime.now().hour
        else:
            try:
                hour = int(target_time.split(":")[0])
            except:
                hour = datetime.now().hour
        
        # Generate time-appropriate edition names
        if 6 <= hour <= 11:
            return f"{hour:02d}:00 MORNING EDITION"
        elif 12 <= hour <= 17:
            return f"{hour:02d}:00 AFTERNOON BRIEF"
        elif 18 <= hour <= 22:
            return f"{hour:02d}:00 EVENING EDITION"
        else:
            return f"{hour:02d}:00 LATE NIGHT SPECIAL"
    
    def _extract_topic_symbols(self, broadcast_content: Dict[str, Any]) -> Dict[str, str]:
        """Extract symbolic representations of news topics"""
        
        selected_news = broadcast_content.get("selected_news", [])
        script_content = broadcast_content.get("script_content", "").lower()
        
        symbols = {
            "symbol_1": "– Breaking news → glowing news ticker strips in neon red",
            "symbol_2": "– Technology → floating digital elements and circuit patterns", 
            "symbol_3": "– Finance → golden coin symbols and market data streams"
        }
        
        # Analyze content for specific symbolic representations
        symbol_list = []
        
        # Extract symbols from news titles and content
        for i, news in enumerate(selected_news[:3]):
            title = news.get("title", "").lower()
            symbol = self._map_topic_to_symbol(title, script_content)
            symbol_list.append(symbol)
        
        # Fill remaining slots with default symbols if needed
        while len(symbol_list) < 3:
            symbol_list.append("– News updates → floating paper fragments with glowing edges")
        
        # Assign to dictionary
        for i, symbol in enumerate(symbol_list[:3]):
            symbols[f"symbol_{i+1}"] = symbol
            
        return symbols
    
    def _map_topic_to_symbol(self, title: str, content: str) -> str:
        """Map news topic to visual symbol"""
        
        title_content = f"{title} {content}".lower()
        
        # Weapons/Crime
        if any(word in title_content for word in ["weapon", "gun", "crime", "theft", "robbery", "einbruch"]):
            return "– Crime story → empty display case with shattered glass and warning lights"
        
        # Weather/Environment
        elif any(word in title_content for word in ["weather", "smoke", "forest", "fire", "dust", "saharastaub"]):
            return "– Environmental event → swirling smoke patterns and red sky over city skyline"
        
        # Politics/Government
        elif any(word in title_content for word in ["politics", "government", "election", "tax", "abgabe", "bürgerliche"]):
            return "– Political tension → scales of justice with glowing parliamentary building silhouette"
        
        # Transport/Traffic
        elif any(word in title_content for word in ["traffic", "transport", "elektroauto", "verkehr"]):
            return "– Transportation → sleek electric car silhouette with charging bolt symbol"
        
        # Entertainment/Culture
        elif any(word in title_content for word in ["culture", "comedy", "expat", "französische", "entertainment"]):
            return "– Cultural event → theater masks with spotlights and French flag elements"
        
        # Technology
        elif any(word in title_content for word in ["tech", "ai", "digital", "cyber"]):
            return "– Technology → floating circuit boards with pulsing blue data streams"
        
        # Bitcoin/Crypto
        elif any(word in title_content for word in ["bitcoin", "crypto", "blockchain"]):
            return "– Cryptocurrency → golden bitcoin symbol with fluctuating price charts"
        
        # Swiss/Local
        elif any(word in title_content for word in ["swiss", "zürich", "switzerland"]):
            return "– Local news → Swiss cross emblem with urban Zürich cityscape reflection"
        
        # Default fallback
        else:
            return "– Breaking news → glowing newspaper fragments floating in digital space"
    

    
    async def _request_dalle_image(self, prompt: str) -> Optional[str]:
        """Sendet Request an DALL-E API"""
        
        try:
            headers = {
                "Authorization": f"Bearer {self.openai_api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": "dall-e-3",
                "prompt": prompt,
                "n": 1,
                "size": self.config["image_size"],
                "quality": self.config["image_quality"],
                "style": self.config["style"]
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.dall_e_base_url,
                    headers=headers,
                    json=data,
                    timeout=aiohttp.ClientTimeout(total=self.config["timeout"])
                ) as response:
                    
                    if response.status == 200:
                        result = await response.json()
                        image_url = result["data"][0]["url"]
                        logger.info("✅ DALL-E Cover-Art generiert")
                        return image_url
                    else:
                        logger.error(f"❌ DALL-E API Fehler {response.status}")
                        return None
        
        except Exception as e:
            logger.error(f"❌ DALL-E Request Fehler: {e}")
            return None
    
    async def _download_cover_image(self, image_url: str, session_id: str) -> Optional[Path]:
        """Lädt Cover-Image herunter"""
        
        try:
            cover_filename = f"radiox_{datetime.now().strftime('%y%m%d_%H%M')}.png"
            cover_path = self.output_dir / cover_filename
            
            async with aiohttp.ClientSession() as session:
                async with session.get(image_url) as response:
                    if response.status == 200:
                        with open(cover_path, 'wb') as f:
                            async for chunk in response.content.iter_chunked(8192):
                                f.write(chunk)
                        
                        logger.info(f"✅ Cover-Image heruntergeladen: {cover_filename}")
                        return cover_path
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Cover-Download Fehler: {e}")
            return None
    
    async def _generate_fallback_cover(self, session_id: str, broadcast_content: Dict[str, Any]) -> Dict[str, Any]:
        """Generiert einfaches Fallback-Cover"""
        
        try:
            # Einfaches Cover mit PIL
            image = Image.new('RGB', (1024, 1024), color='#1a1a2e')
            draw = ImageDraw.Draw(image)
            
            # RadioX Text
            try:
                font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 120)
            except:
                font = ImageFont.load_default()
            
            draw.text((200, 400), "RadioX", fill="white", font=font)
            draw.text((250, 520), "AI News", fill="#00d4ff", font=font)
            
            # Speichern
            fallback_filename = f"radiox_{datetime.now().strftime('%y%m%d_%H%M')}_fallback.png"
            fallback_path = self.output_dir / fallback_filename
            
            image.save(fallback_path, "PNG")
            
            logger.info(f"✅ Fallback Cover erstellt: {fallback_filename}")
            
            return {
                "success": True,
                "session_id": session_id,
                "cover_path": str(fallback_path),
                "cover_filename": fallback_path.name,
                "generation_timestamp": datetime.now().isoformat(),
                "cover_type": "fallback"
            }
            
        except Exception as e:
            logger.error(f"❌ Fallback Cover Fehler: {e}")
            return {
                "success": False,
                "session_id": session_id,
                "error": str(e),
                "generation_timestamp": datetime.now().isoformat()
            } 