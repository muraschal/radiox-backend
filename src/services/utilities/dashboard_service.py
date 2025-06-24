"""
📻 RadioX Dashboard Service
High-Performance HTML Dashboard Generator

Generates beautiful radiox_shownotes_yymmdd_hhmm.html based on data_collection.html
but with smaller boxes and additional Voice/GPT processing data.
"""

import os
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
from loguru import logger

from jinja2 import Environment, FileSystemLoader, Template


class DashboardService:
    """
    🎨 Dashboard Service für RadioX Show Notes
    TAILWIND CSS ÜBER CDN - EINFACH & FUNKTIONAL
    """
    
    def __init__(self):
        """Initialisiert den Dashboard Service mit Jinja2"""
        self.output_dir = Path("web")
        self.templates_dir = Path("templates/dashboard")
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Jinja2 Environment Setup
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            autoescape=True,
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        logger.info("✨ Clean Dashboard Service initialisiert (Jinja2)")
    
    async def generate_dashboard(
        self, 
        raw_data: Dict[str, Any], 
        processed_data: Dict[str, Any], 
        show_config: Dict[str, Any],
        timestamp: Optional[str] = None,
        cover_data: Optional[Dict[str, Any]] = None,
        audio_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generiert das Dashboard mit Jinja2 Templates"""
        try:
            logger.info("🎨 Generiere Dashboard mit Jinja2...")
            
            # Generate timestamp if not provided
            if not timestamp:
                timestamp = datetime.now().strftime('%y%m%d_%H%M')
            
            # Extract and prepare data
            processed_info = self._extract_processing_data(processed_data)
            stats = self._calculate_dashboard_stats(raw_data, processed_info)
            
            # Prepare template context
            context = self._prepare_template_context(
                raw_data=raw_data,
                processed_info=processed_info,
                show_config=show_config,
                stats=stats,
                timestamp=timestamp,
                cover_data=cover_data,
                audio_data=audio_data
            )
            
            # Load and render template
            template = self.jinja_env.get_template('dashboard.html')
            html_content = template.render(**context)
            
            # Save to file
            filename = f"radiox_{timestamp}.html"
            filepath = os.path.join(self.output_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            # Copy CSS to web directory for serving
            await self._copy_css_to_web()
            
            logger.success(f"✅ Dashboard generiert: {filename}")
            return filepath
            
        except Exception as e:
            logger.error(f"❌ Dashboard Generation failed: {e}")
            raise
    
    def _prepare_template_context(
        self,
        raw_data: Dict[str, Any],
        processed_info: Dict[str, Any],
        show_config: Dict[str, Any],
        stats: Dict[str, Any],
        timestamp: str,
        cover_data: Optional[Dict[str, Any]] = None,
        audio_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Bereitet den Kontext für das Jinja2 Template vor"""
        
        # Format timestamp for display
        time_part = timestamp.split('_')[1] if '_' in timestamp else timestamp[-4:]
        formatted_timestamp = f"{time_part[:2]}:{time_part[2:]}"
        
        # Show title and description
        show_display_name = show_config.get('show', {}).get('display_name', 'RadioX AI')
        show_description_db = show_config.get('show', {}).get('description', '')
        base_description = show_description_db if show_description_db else '🎙️ AI-generierte Radio-Show'
        
        # Speaker info
        speaker_info = self._generate_speaker_info(show_config)
        show_description = f"{base_description} {speaker_info}"
        show_title = f"{show_display_name} | {formatted_timestamp} Edition"
        
        # File references - check for actual files instead of data parameters
        cover_filename = f"radiox_{timestamp}.png"
        audio_filename = f"radiox_{timestamp}.mp3"
        
        # Verify files actually exist
        cover_path = self.output_dir / cover_filename
        audio_path = self.output_dir / audio_filename
        
        if not cover_path.exists():
            cover_filename = None
        if not audio_path.exists():
            audio_filename = None
        
        return {
            # Basic info
            'show_title': show_title,
            'show_description': show_description,
            'timestamp': timestamp,
            'formatted_timestamp': formatted_timestamp,
            
            # File references
            'cover_filename': cover_filename,
            'audio_filename': audio_filename,
            'css_file': 'style.css',  # Relative path
            
            # Data
            'stats': stats,
            'selected_news': processed_info.get('selected_news', []),
            'radio_script': processed_info.get('radio_script', ''),
            'show_config': show_config,
            
            # GPT Prompts (NEW)
            'gpt_prompts': self._extract_gpt_prompts(processed_info, raw_data),
            
            # Raw data for debugging
            'raw_data': raw_data,
            'processed_info': processed_info
        }
    
    def _extract_processing_data(self, processed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extrahiert die verarbeiteten Daten aus verschiedenen Formaten"""
        # Handle nested data structure
        if 'data' in processed_data:
            data = processed_data['data']
        else:
            data = processed_data
        
        return {
            'gpt_prompt': data.get('gpt_prompt', ''),
            'radio_script': data.get('radio_script', data.get('script_content', '')),
            'selected_news': data.get('selected_news', []),
            'processing_info': data.get('processing_info', {}),
            'voice_config': data.get('voice_config', {}),
            'cover_generation': data.get('cover_generation', {})
        }
    
    def _calculate_dashboard_stats(self, raw_data: Dict[str, Any], processed_info: Dict[str, Any]) -> Dict[str, Any]:
        """Berechnet Dashboard-Statistiken"""
        news = raw_data.get('news', [])
        weather = raw_data.get('weather', {})
        crypto = raw_data.get('crypto', {})
        
        # Weather & Bitcoin intelligent summaries
        weather_summary = weather.get('current_summary', weather.get('description', ''))
        bitcoin_summary = crypto.get('bitcoin_summary', '')
        
        # Extract temperature from weather summary
        weather_temp = self._extract_temperature_from_summary(weather_summary)
        
        return {
            'total_news': len(news),
            'selected_news': len(processed_info.get('selected_news', [])),
            'total_sources': len(set(item.get('source', 'unknown') for item in news)),
            'gpt_words': len(processed_info.get('radio_script', '').split()),
            'weather_temp': weather_temp,
            'bitcoin_price': crypto.get('bitcoin', {}).get('price_usd', 0),
            'bitcoin_change': crypto.get('bitcoin', {}).get('change_24h', 0),
            'weather_desc': weather.get('description', 'No data'),
            'weather_summary': weather_summary,
            'bitcoin_summary': bitcoin_summary,
            'weather_location': weather.get('location', 'Zürich'),
            'sources': self._group_by_source(news)
        }
    
    def _extract_temperature_from_summary(self, weather_summary: str) -> str:
        """Extrahiert Temperatur aus Weather Summary"""
        if not weather_summary:
            return 'N/A'
        
        import re
        celsius_match = re.search(r'(\d+\.?\d*)\s?°C', weather_summary, re.IGNORECASE)
        if celsius_match:
            return f"{celsius_match.group(1)}°C"
        
        return 'N/A'
    
    def _group_by_source(self, news: List[Dict[str, Any]]) -> Dict[str, int]:
        """Gruppiert News nach Quellen"""
        sources = {}
        for item in news:
            source = item.get('source', 'Unknown')
            sources[source] = sources.get(source, 0) + 1
        return sources
    
    def _generate_speaker_info(self, show_config: Dict[str, Any]) -> str:
        """Generiert Speaker Info Text"""
        try:
            speaker = show_config.get('speaker', {})
            voice_name = speaker.get('voice_name', '')
            
            if voice_name:
                return f"mit {voice_name.title()}"
            return ""
        except Exception:
            return ""
    
    async def _copy_css_to_web(self) -> None:
        """Kopiert CSS-Datei ins web-Verzeichnis für Serving"""
        try:
            import shutil
            css_source = self.templates_dir / "style.css"
            css_dest = self.output_dir / "style.css"
            
            if css_source.exists():
                shutil.copy2(css_source, css_dest)
                logger.debug("📄 CSS copied to web directory")
        except Exception as e:
            logger.warning(f"⚠️ CSS copy warning: {e}")
    
    def _extract_gpt_prompts(self, processed_info: Dict[str, Any], raw_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extrahiert und formatiert GPT Prompts aus den verarbeiteten Daten"""
        prompts = []
        
        try:
            # Extract GPT prompt from processed data
            gpt_prompt = processed_info.get('gpt_prompt', '')
            
            if gpt_prompt:
                # Stage 1: Article Selection Prompt
                if 'STAGE 1' in gpt_prompt or 'Select' in gpt_prompt:
                    prompts.append({
                        'stage': 'Stage 1: Article Selection',
                        'model': 'gpt-4',
                        'purpose': 'Intelligente Auswahl relevanter News-Artikel basierend auf Show-Preset und Zielgruppe',
                        'prompt': self._clean_prompt_for_display(gpt_prompt),
                        'response_summary': f"{len(processed_info.get('selected_news', []))} Artikel ausgewählt"
                    })
                
                # Stage 2: Script Generation Prompt (if different)
                script_prompt = processed_info.get('script_prompt', '')
                if script_prompt and script_prompt != gpt_prompt:
                    prompts.append({
                        'stage': 'Stage 2: Script Generation',
                        'model': 'gpt-4',
                        'purpose': 'Generierung des finalen Radio-Scripts mit natürlichen Dialogen und Moderationen',
                        'prompt': self._clean_prompt_for_display(script_prompt),
                        'response_summary': f"{len(processed_info.get('radio_script', '').split())} Wörter generiert"
                    })
                elif not script_prompt:
                    # Single-stage prompt (both selection and script generation)
                    prompts.append({
                        'stage': 'Combined: Selection + Script',
                        'model': 'gpt-4',
                        'purpose': 'Artikel-Auswahl und Script-Generierung in einem Schritt',
                        'prompt': self._clean_prompt_for_display(gpt_prompt),
                        'response_summary': f"{len(processed_info.get('selected_news', []))} Artikel → {len(processed_info.get('radio_script', '').split())} Wörter"
                    })
            
            # Add Bitcoin GPT prompt if available
            bitcoin_data = raw_data.get('crypto', {})
            if bitcoin_data.get('bitcoin_summary'):
                prompts.append({
                    'stage': 'Bitcoin Analysis',
                    'model': 'gpt-4',
                    'purpose': 'Intelligente Analyse der Bitcoin-Marktdaten für Radio-Integration',
                    'prompt': 'Analysiere die aktuellen Bitcoin-Daten und erstelle eine prägnante, radio-taugliche Zusammenfassung...',
                    'response_summary': f"Bitcoin Summary: {len(bitcoin_data.get('bitcoin_summary', '').split())} Wörter"
                })
            
        except Exception as e:
            logger.warning(f"⚠️ GPT Prompts extraction warning: {e}")
        
        return prompts
    
    def _clean_prompt_for_display(self, prompt: str) -> str:
        """Bereinigt GPT Prompts für bessere Lesbarkeit"""
        if not prompt:
            return "Kein Prompt verfügbar"
        
        # Remove excessive whitespace and normalize line breaks
        cleaned = '\n'.join(line.strip() for line in prompt.split('\n') if line.strip())
        
        # Limit length for display (but keep it readable)
        if len(cleaned) > 2000:
            cleaned = cleaned[:2000] + "\n\n... (gekürzt für Anzeige)"
        
        return cleaned




# Backward compatibility wrapper
class DashboardFancyService(DashboardService):
    """Wrapper für Backward Compatibility"""
    
    async def generate_fancy_dashboard(self, *args, **kwargs):
        """Delegiert an neue generate_dashboard Methode"""
        return await self.generate_dashboard(*args, **kwargs) 