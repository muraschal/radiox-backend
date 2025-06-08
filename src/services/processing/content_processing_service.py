#!/usr/bin/env python3

"""
Content Processing Service - HIGH PERFORMANCE GPT ENGINE
=======================================================

Google Engineering Best Practices:
- Single Responsibility (GPT-focused processing)
- Dependency Injection (Clean service composition)
- Performance Optimization (Async, caching)
- Error Handling (Graceful degradation)
- Resource Management (Memory efficient)

RADIKAL VEREINFACHT: Alle Intelligenz an GPT externalisiert!

- Keine lokale Kategorisierung
- Keine lokale Filterung  
- Keine lokale Priorisierung
- Keine komplexen Algorithmen

EINFACH: Daten aufbereiten → GPT → Fertige Radioshow

DEPENDENCIES: OpenAI GPT-4
"""

import asyncio
import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from loguru import logger
import openai

from config.settings import get_settings

# Import Show Service für Show-Konfiguration
from .show_service import ShowService, get_show_for_generation


@dataclass(frozen=True)
class ProcessingConfig:
    """Immutable processing configuration"""
    gpt_model: str = "gpt-4"
    gpt_timeout: int = 180
    max_news_for_gpt: int = 15
    news_filter_hours: int = 48
    html_retention_count: int = 2


class ContentProcessingService:
    """High-Performance GPT-Powered Content Processing Engine
    
    Implements Google Engineering Best Practices:
    - Single Responsibility (GPT delegation)
    - Performance First (Async operations)
    - Clean Architecture (Service composition)
    - Resource Management (Memory efficient)
    """
    
    __slots__ = ('_openai_client', '_show_service', '_config')
    
    def __init__(self):
        # OpenAI Client
        settings = get_settings()
        self._openai_client = openai.AsyncOpenAI(
            api_key=settings.openai_api_key
        )
        
        # Show Service für Show-Konfigurationen
        self._show_service = ShowService()
        
        self._config = ProcessingConfig()
        
        logger.info("🔄 Content Processing Service initialized (GPT-POWERED)")
    
    async def process_content_for_show(
        self, raw_data: Dict[str, Any], target_news_count: int = 4,
        target_time: Optional[str] = None, preset_name: Optional[str] = None,
        show_config: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Main processing pipeline with performance optimization"""
        
        logger.info("🤖 Erstelle Radioshow mit GPT...")
        
        try:
            # Pipeline execution with early validation
            show_config = show_config or await self.get_show_configuration(preset_name or "zurich")
            if not show_config:
                raise Exception(f"Show configuration for '{preset_name}' not found")
            
            # Parallel data preparation and GPT processing
            prepared_data = self._prepare_data_for_gpt(raw_data, show_config, target_news_count, target_time)
            prompt = self._create_radio_show_prompt(prepared_data)
            radio_show = await self._generate_radio_show_with_gpt(prompt)
            
            # Create comprehensive result
            result = self._create_processing_result(
                radio_show, raw_data, show_config, prompt, prepared_data, 
                target_news_count, target_time, preset_name
            )
            
            # Generate HTML dashboard asynchronously
            await self._generate_show_html(result)
            
            logger.info(f"✅ Radioshow erstellt: {len(radio_show.get('selected_news', []))} News")
            return result
            
        except Exception as e:
            logger.error(f"❌ GPT Content Processing Fehler: {e}")
            return self._create_error_result(str(e))
    
    def _create_processing_result(
        self, radio_show: Dict[str, Any], raw_data: Dict[str, Any], 
        show_config: Dict[str, Any], prompt: str, prepared_data: Dict[str, Any],
        target_news_count: int, target_time: Optional[str], preset_name: Optional[str]
    ) -> Dict[str, Any]:
        """Create comprehensive processing result"""
        return {
            "success": True,
            "radio_script": radio_show.get("radio_script", ""),
            "segments": radio_show.get("segments", []),
            "selected_news": radio_show.get("selected_news", []),
            "weather_data": raw_data.get("weather"),
            "crypto_data": raw_data.get("crypto"),
            "content_focus": radio_show.get("content_focus", {}),
            "quality_score": radio_show.get("quality_score", 0.8),
            "target_time": target_time,
            "preset_name": preset_name,
            "show_config": show_config,
            "processing_timestamp": datetime.now().isoformat(),
            "generated_by": f"{self._config.gpt_model}",
            "gpt_prompt": prompt,
            "all_news": raw_data.get("news", []),
            "prepared_data": prepared_data,
            "show_details": show_config,
            "html_dashboard": f"radiox_show_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        }
    
    def _create_error_result(self, error_message: str) -> Dict[str, Any]:
        """Create error result"""
        return {
            "success": False,
            "error": error_message,
            "timestamp": datetime.now().isoformat()
        }
    
    async def get_show_configuration(self, preset_name: str) -> Optional[Dict[str, Any]]:
        """Load show configuration with caching"""
        logger.info(f"🎭 Lade Show-Konfiguration für: {preset_name}")
        
        try:
            show_config = await get_show_for_generation(preset_name)
            if show_config:
                logger.info(f"✅ Show-Konfiguration geladen: {show_config['show']['display_name']}")
            return show_config
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden der Show-Konfiguration: {e}")
            return None
    
    async def test_processing(self) -> bool:
        """Test GPT processing functionality"""
        test_data = {
            "news": [{
                "title": "Test News Zürich",
                "summary": "Eine Test-Nachricht über Zürich für die GPT-Verarbeitung.",
                "source": "test",
                "published": datetime.now().isoformat()
            }],
            "weather": {"temperature": 15, "condition": "sunny"},
            "crypto": {"bitcoin": 105000, "change": "+2%"}
        }
        
        try:
            result = await self.process_content_for_show(test_data, target_news_count=1)
            return result.get("success", False) and len(result.get("selected_news", [])) > 0
        except Exception:
            return False
    
    async def _generate_show_html(self, result: Dict[str, Any]) -> None:
        """Generate high-performance HTML dashboard"""
        try:
            await self._cleanup_old_show_htmls()
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"radiox_show_{timestamp}.html"
            html_content = self._create_show_html_content(result, timestamp)
            
            # Ensure outplay directory exists
            os.makedirs("outplay", exist_ok=True)
            
            # Write HTML file
            filepath = os.path.join("outplay", filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            logger.info(f"✅ Show HTML Dashboard generiert: {filename}")
            
        except Exception as e:
            logger.error(f"❌ HTML-Generierung fehlgeschlagen: {e}")
    
    async def _cleanup_old_show_htmls(self) -> None:
        """Clean up old HTML files efficiently"""
        try:
            outplay_dir = "outplay"
            if not os.path.exists(outplay_dir):
                return
            
            # Get all radiox_show_*.html files
            show_files = [
                f for f in os.listdir(outplay_dir) 
                if f.startswith("radiox_show_") and f.endswith(".html")
            ]
            
            # Sort by modification time (newest first)
            show_files.sort(
                key=lambda f: os.path.getmtime(os.path.join(outplay_dir, f)), 
                reverse=True
            )
            
            # Delete old files (keep only retention_count)
            for old_file in show_files[self._config.html_retention_count:]:
                os.remove(os.path.join(outplay_dir, old_file))
                logger.debug(f"🗑️ Alte HTML-Datei gelöscht: {old_file}")
                
        except Exception as e:
            logger.warning(f"⚠️ HTML-Cleanup Fehler: {e}")
    
    def _create_show_html_content(self, result: Dict[str, Any], timestamp: str) -> str:
        """Create optimized HTML content with full-width dashboard"""
        
        # Extract data efficiently
        show_config = result.get("show_details", {})
        all_news = result.get("all_news", [])
        selected_news = result.get("selected_news", [])
        weather = result.get("weather_data", {})
        crypto = result.get("crypto_data", {})
        gpt_prompt = result.get("gpt_prompt", "")
        radio_script = result.get("radio_script", "")
        
        # Calculate metrics
        total_news = len(all_news)
        filtered_news = len([n for n in all_news if self._is_recent_news(n)])
        bitcoin_price = crypto.get("bitcoin", {}).get("price_usd", 0) if crypto.get("bitcoin") else 0
        bitcoin_change = crypto.get("bitcoin", {}).get("change_24h", 0) if crypto.get("bitcoin") else 0
        
        # Voice configuration
        voice_config_html = self._format_voice_config_dashboard(
            show_config.get("speaker", {}), 
            show_config.get("secondary_speaker", {})
        )
        
        return f"""<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RadioX Show Dashboard - {timestamp}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #1a1a1a;
            color: #ffffff;
            width: 100vw;
            height: 100vh;
            overflow-x: hidden;
        }}
        
        .dashboard-header {{
            background: #2a2a2a;
            padding: 15px 20px;
            border-bottom: 2px solid #4CAF50;
            display: flex;
            justify-content: space-between;
            align-items: center;
            height: 10vh;
        }}
        
        .dashboard-title {{
            font-size: 24px;
            font-weight: bold;
            color: #4CAF50;
        }}
        
        .dashboard-timestamp {{
            font-size: 14px;
            color: #888;
        }}
        
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(6, 1fr);
            gap: 15px;
            padding: 15px 20px;
            height: 10vh;
        }}
        
        .metric-card {{
            background: #2a2a2a;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
            border: 1px solid #333;
        }}
        
        .metric-value {{
            font-size: 20px;
            font-weight: bold;
            color: #4CAF50;
        }}
        
        .metric-label {{
            font-size: 12px;
            color: #888;
            margin-top: 5px;
        }}
        
        .content-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            gap: 20px;
            padding: 20px;
            height: 80vh;
        }}
        
        .content-panel {{
            background: #2a2a2a;
            border-radius: 8px;
            border: 1px solid #333;
            overflow: hidden;
            display: flex;
            flex-direction: column;
        }}
        
        .panel-header {{
            background: #333;
            padding: 15px;
            font-weight: bold;
            color: #4CAF50;
            border-bottom: 1px solid #444;
        }}
        
        .panel-content {{
            flex: 1;
            padding: 15px;
            overflow-y: auto;
            font-size: 13px;
            line-height: 1.4;
        }}
        
        .news-item {{
            background: #333;
            margin-bottom: 10px;
            padding: 10px;
            border-radius: 6px;
            border-left: 3px solid #4CAF50;
        }}
        
        .news-title {{
            font-weight: bold;
            color: #fff;
            margin-bottom: 5px;
        }}
        
        .news-meta {{
            color: #888;
            font-size: 11px;
            margin-bottom: 5px;
        }}
        
        .news-summary {{
            color: #ccc;
            font-size: 12px;
        }}
        
        .voice-config {{
            background: #333;
            padding: 10px;
            border-radius: 6px;
            margin-bottom: 15px;
        }}
        
        .voice-speaker {{
            margin-bottom: 8px;
        }}
        
        .voice-name {{
            font-weight: bold;
            color: #4CAF50;
        }}
        
        .voice-details {{
            color: #888;
            font-size: 11px;
        }}
        
        .weather-crypto {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
            margin-bottom: 15px;
        }}
        
        .weather-card, .crypto-card {{
            background: #333;
            padding: 10px;
            border-radius: 6px;
        }}
        
        .card-title {{
            font-weight: bold;
            color: #4CAF50;
            margin-bottom: 5px;
        }}
        
        .card-value {{
            color: #fff;
            font-size: 14px;
        }}
        
        .positive {{ color: #4CAF50; }}
        .negative {{ color: #f44336; }}
        
        pre {{
            background: #1a1a1a;
            padding: 10px;
            border-radius: 6px;
            font-size: 11px;
            line-height: 1.3;
            white-space: pre-wrap;
            word-wrap: break-word;
            color: #ccc;
        }}
        
        ::-webkit-scrollbar {{
            width: 8px;
        }}
        
        ::-webkit-scrollbar-track {{
            background: #1a1a1a;
        }}
        
        ::-webkit-scrollbar-thumb {{
            background: #4CAF50;
            border-radius: 4px;
        }}
    </style>
</head>
<body>
    <div class="dashboard-header">
        <div class="dashboard-title">📻 RadioX Show Dashboard</div>
        <div class="dashboard-timestamp">Generated: {timestamp}</div>
    </div>
    
    <div class="metrics-grid">
        <div class="metric-card">
            <div class="metric-value">{total_news}</div>
            <div class="metric-label">Total News</div>
        </div>
        <div class="metric-card">
            <div class="metric-value">{filtered_news}</div>
            <div class="metric-label">Filtered (48h)</div>
        </div>
        <div class="metric-card">
            <div class="metric-value">{len(selected_news)}</div>
            <div class="metric-label">Selected News</div>
        </div>
        <div class="metric-card">
            <div class="metric-value">{weather.get('current', {}).get('temperature', 'N/A')}°C</div>
            <div class="metric-label">Temperature</div>
        </div>
        <div class="metric-card">
            <div class="metric-value">${bitcoin_price:,.0f}</div>
            <div class="metric-label">Bitcoin Price</div>
        </div>
        <div class="metric-card">
            <div class="metric-value {'positive' if bitcoin_change > 0 else 'negative'}">{bitcoin_change:+.1f}%</div>
            <div class="metric-label">BTC Change 24h</div>
        </div>
    </div>
    
    <div class="content-grid">
        <div class="content-panel">
            <div class="panel-header">📰 Complete Data Feed</div>
            <div class="panel-content">
                {voice_config_html}
                
                <div class="weather-crypto">
                    <div class="weather-card">
                        <div class="card-title">🌤️ Weather</div>
                        <div class="card-value">{weather.get('current', {}).get('temperature', 'N/A')}°C</div>
                        <div style="color: #888; font-size: 11px;">{weather.get('current', {}).get('description', 'N/A')}</div>
                    </div>
                    <div class="crypto-card">
                        <div class="card-title">₿ Bitcoin</div>
                        <div class="card-value">${bitcoin_price:,.0f}</div>
                        <div style="color: {'#4CAF50' if bitcoin_change > 0 else '#f44336'}; font-size: 11px;">{bitcoin_change:+.1f}% (24h)</div>
                    </div>
                </div>
                
                <div style="margin-bottom: 10px; font-weight: bold; color: #4CAF50;">📊 All News ({total_news} total)</div>
                {self._format_news_feed_dashboard(all_news[:50])}
            </div>
        </div>
        
        <div class="content-panel">
            <div class="panel-header">🤖 GPT Prompt</div>
            <div class="panel-content">
                <pre>{gpt_prompt}</pre>
            </div>
        </div>
        
        <div class="content-panel">
            <div class="panel-header">📻 Radio Script</div>
            <div class="panel-content">
                <pre>{radio_script}</pre>
            </div>
        </div>
    </div>
</body>
</html>"""
    
    def _is_recent_news(self, news_item: Dict[str, Any]) -> bool:
        """Check if news is within filter timeframe"""
        try:
            published = datetime.fromisoformat(news_item.get("published", ""))
            cutoff = datetime.now() - timedelta(hours=self._config.news_filter_hours)
            return published >= cutoff
        except:
            return True
    
    def _format_voice_config_dashboard(self, primary_speaker: Dict[str, Any], secondary_speaker: Dict[str, Any]) -> str:
        """Format voice configuration for dashboard"""
        html = '<div class="voice-config">'
        html += '<div style="font-weight: bold; color: #4CAF50; margin-bottom: 10px;">🎤 Voice Configuration</div>'
        
        if primary_speaker:
            html += f'''
            <div class="voice-speaker">
                <div class="voice-name">Primary: {primary_speaker.get("voice_name", "Unknown")}</div>
                <div class="voice-details">
                    ID: {primary_speaker.get("voice_id", "N/A")} | 
                    Lang: {primary_speaker.get("language", "N/A")} | 
                    Style: {primary_speaker.get("style", "N/A")} | 
                    Stability: {primary_speaker.get("stability", "N/A")} | 
                    Model: {primary_speaker.get("model_id", "N/A")}
                </div>
            </div>
            '''
        
        if secondary_speaker:
            html += f'''
            <div class="voice-speaker">
                <div class="voice-name">Secondary: {secondary_speaker.get("voice_name", "Unknown")}</div>
                <div class="voice-details">
                    ID: {secondary_speaker.get("voice_id", "N/A")} | 
                    Lang: {secondary_speaker.get("language", "N/A")} | 
                    Style: {secondary_speaker.get("style", "N/A")} | 
                    Stability: {secondary_speaker.get("stability", "N/A")} | 
                    Model: {secondary_speaker.get("model_id", "N/A")}
                </div>
            </div>
            '''
        
        html += '</div>'
        return html
    
    def _format_news_feed_dashboard(self, news: List[Dict[str, Any]]) -> str:
        """Format news feed for dashboard"""
        html = ""
        for item in news[:30]:  # Limit for performance
            age_hours = round(item.get('age_hours', 0))
            html += f'''
            <div class="news-item">
                <div class="news-title">{item.get('title', 'Kein Titel')}</div>
                <div class="news-meta">{item.get('source', 'Unknown')} • {age_hours}h ago • {item.get('category', 'general')}</div>
                <div class="news-summary">{item.get('summary', 'Keine Zusammenfassung')[:200]}...</div>
            </div>
            '''
        return html
    
    def _prepare_data_for_gpt(
        self, raw_data: Dict[str, Any], show_config: Dict[str, Any],
        target_news_count: int, target_time: Optional[str]
    ) -> Dict[str, Any]:
        """Prepare data for GPT with 48h filter and performance optimization"""
        
        # Filter news to last 48 hours for GPT processing
        all_news = raw_data.get("news", [])
        cutoff_time = datetime.now() - timedelta(hours=self._config.news_filter_hours)
        
        recent_news = []
        for news_item in all_news:
            try:
                published = datetime.fromisoformat(news_item.get("published", ""))
                if published >= cutoff_time:
                    recent_news.append(news_item)
            except:
                recent_news.append(news_item)  # Include if date parsing fails
        
        # Sort by publication date (newest first) and limit for GPT
        recent_news.sort(key=lambda x: x.get("published", ""), reverse=True)
        limited_news = recent_news[:self._config.max_news_for_gpt]
        
        logger.info(f"📊 GPT Input: {len(limited_news)} News (von {len(all_news)} total, {len(recent_news)} recent)")
        
        return {
            "news": limited_news,
            "weather": raw_data.get("weather"),
            "crypto": raw_data.get("crypto"),
            "show_config": show_config,
            "target_news_count": target_news_count,
            "target_time": target_time,
            "processing_timestamp": datetime.now().isoformat()
        }
    
    def _create_radio_show_prompt(self, prepared_data: Dict[str, Any]) -> str:
        """Create optimized GPT prompt"""
        
        show_config = prepared_data["show_config"]
        news = prepared_data["news"]
        weather = prepared_data["weather"]
        crypto = prepared_data["crypto"]
        target_count = prepared_data["target_news_count"]
        
        # Extract show details efficiently
        show_name = show_config["show"]["display_name"]
        city_focus = show_config["show"]["city_focus"]
        categories = show_config["content"]["categories"]
        speaker_name = show_config["speaker"]["voice_name"]
        
        # Format data sections
        news_section = self._format_news_for_prompt(news)
        weather_section = self._format_weather_for_prompt(weather)
        crypto_section = self._format_crypto_for_prompt(crypto)
        
        return f"""Du bist der AI-Produzent für "{show_name}" - eine Radioshow mit Fokus auf {city_focus}.

AUFGABE: Erstelle ein komplettes Radio-Skript mit genau {target_count} News-Segmenten.

VERFÜGBARE DATEN:
{news_section}

{weather_section}

{crypto_section}

SHOW-KONFIGURATION:
- Sprecher: {speaker_name}
- Stadt-Fokus: {city_focus}
- Kategorien: {', '.join(categories)}

ANFORDERUNGEN:
1. Wähle die {target_count} relevantesten News für {city_focus}
2. Erstelle ein natürliches Radio-Skript (2-3 Minuten)
3. Integriere Wetter und Bitcoin-Preis
4. Verwende einen lockeren, informativen Ton

ANTWORT-FORMAT (JSON):
{{
    "selected_news": [
        {{"title": "...", "summary": "...", "source": "...", "relevance_reason": "..."}}
    ],
    "radio_script": "Vollständiges Radio-Skript hier...",
    "segments": [
        {{"type": "intro", "content": "..."}},
        {{"type": "news", "content": "...", "news_title": "..."}},
        {{"type": "weather", "content": "..."}},
        {{"type": "crypto", "content": "..."}},
        {{"type": "outro", "content": "..."}}
    ],
    "content_focus": {{"focus": "{city_focus}", "reasoning": "..."}},
    "quality_score": 0.9
}}"""
    
    def _format_news_for_prompt(self, news: List[Dict[str, Any]]) -> str:
        """Format news for GPT prompt efficiently"""
        if not news:
            return "KEINE NEWS VERFÜGBAR"
        
        news_text = f"NEWS ({len(news)} verfügbar):\n"
        for i, item in enumerate(news, 1):
            age_hours = round(item.get('age_hours', 0))
            news_text += f"{i}. [{item.get('source', 'Unknown')}] {item.get('title', 'Kein Titel')}\n"
            news_text += f"   Zusammenfassung: {item.get('summary', 'Keine Zusammenfassung')[:200]}...\n"
            news_text += f"   Kategorie: {item.get('category', 'general')} | Alter: {age_hours}h\n\n"
        
        return news_text
    
    def _format_weather_for_prompt(self, weather: Dict[str, Any]) -> str:
        """Format weather for GPT prompt"""
        if not weather or not weather.get("current"):
            return "WETTER: Nicht verfügbar"
        
        current = weather["current"]
        return f"""WETTER (Zürich):
- Temperatur: {current.get('temperature', 'N/A')}°C
- Bedingungen: {current.get('description', 'N/A')}
- Gefühlte Temperatur: {current.get('feels_like', 'N/A')}°C
- Luftfeuchtigkeit: {current.get('humidity', 'N/A')}%"""
    
    def _format_crypto_for_prompt(self, crypto: Dict[str, Any]) -> str:
        """Format crypto for GPT prompt"""
        if not crypto or not crypto.get("bitcoin"):
            return "BITCOIN: Nicht verfügbar"
        
        bitcoin = crypto["bitcoin"]
        return f"""BITCOIN:
- Aktueller Preis: ${bitcoin.get('price_usd', 0):,.0f}
- 24h Änderung: {bitcoin.get('change_24h', 0):+.2f}%
- 7d Änderung: {bitcoin.get('change_7d', 0):+.2f}%
- Marktkapitalisierung: ${bitcoin.get('market_cap', 0):,.0f}"""
    
    async def _generate_radio_show_with_gpt(self, prompt: str) -> Dict[str, Any]:
        """Generate radio show with GPT-4 and performance optimization"""
        
        try:
            logger.info(f"🤖 Sende Anfrage an {self._config.gpt_model}...")
            
            response = await asyncio.wait_for(
                self._openai_client.chat.completions.create(
                    model=self._config.gpt_model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7,
                    max_tokens=4000
                ),
                timeout=self._config.gpt_timeout
            )
            
            content = response.choices[0].message.content
            
            # Parse JSON response
            try:
                result = json.loads(content)
                logger.info(f"✅ GPT-Antwort erfolgreich geparst")
                return result
            except json.JSONDecodeError:
                logger.warning("⚠️ GPT-Antwort ist kein gültiges JSON, verwende Fallback")
                return self._create_fallback_result(content)
                
        except asyncio.TimeoutError:
            logger.error(f"❌ GPT-Timeout nach {self._config.gpt_timeout}s")
            raise Exception(f"GPT request timed out after {self._config.gpt_timeout} seconds")
        except Exception as e:
            logger.error(f"❌ GPT-Fehler: {e}")
            raise Exception(f"GPT processing failed: {str(e)}")
    
    def _create_fallback_result(self, content: str) -> Dict[str, Any]:
        """Create fallback result when JSON parsing fails"""
        return {
            "selected_news": [],
            "radio_script": content,
            "segments": [{"type": "content", "content": content}],
            "content_focus": {"focus": "general", "reasoning": "Fallback due to parsing error"},
            "quality_score": 0.5
        } 