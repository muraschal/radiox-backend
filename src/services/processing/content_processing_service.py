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
        show_config: Dict[str, Any] = None, last_show_context: Optional[Dict[str, Any]] = None
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
            prompt = self._create_radio_show_prompt(prepared_data, last_show_context)
            radio_show = await self._generate_radio_show_with_gpt(prompt, prepared_data)
            
            # Create comprehensive result
            result = self._create_processing_result(
                radio_show, raw_data, show_config, prompt, prepared_data, 
                target_news_count, target_time, preset_name
            )
            
            # **NEUE TAILWIND DASHBOARD GENERATION statt alte Show HTML**
            await self._generate_new_tailwind_dashboard(result, raw_data, show_config)
            
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
    
    async def _generate_new_tailwind_dashboard(self, result: Dict[str, Any], raw_data: Dict[str, Any], show_config: Dict[str, Any]) -> None:
        """Generate new Tailwind CSS-based dashboard"""
        try:
            await self._cleanup_old_show_htmls()
            
            # **NEUE INTEGRATION: TailwindDashboardService verwenden**
            from src.services.utilities.tailwind_dashboard_service import TailwindDashboardService
            
            tailwind_service = TailwindDashboardService()
            
            # Generate Show Notes Dashboard mit Processing-Daten
            dashboard_path = await tailwind_service.generate_shownotes_dashboard(
                raw_data=raw_data,
                processed_data=result,
                show_config=show_config
            )
            
            logger.info(f"✅ Neue Tailwind Show Dashboard generiert: {dashboard_path}")
            
            # Update result mit neuem Dashboard-Pfad
            result["tailwind_dashboard"] = dashboard_path
            
        except Exception as e:
            logger.error(f"❌ Tailwind Dashboard Generation Fehler: {e}")
            raise e  # Keine Fallbacks - Fehler durchreichen
    
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
    
    # ALTE HTML-GENERATION ENTFERNT - Ersetzt durch TailwindDashboardService
    # Die _create_new_tailwind_dashboard_content Methode wurde entfernt da jetzt
    # die neue TailwindDashboardService verwendet wird
    
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
        """Prepare data for GPT with PRESET-BASED filtering - COMPLETE OVERHAUL"""
        
        all_news = raw_data.get("news", [])
        logger.info(f"🔍 Starte Preset-basierte Filterung von {len(all_news)} News...")
        
        # Extract preset configuration
        rss_filter = show_config.get("content", {}).get("rss_filter", {})
        if not rss_filter:
            logger.warning("⚠️ Kein RSS-Filter in Show-Config - verwende Fallback")
            # Fallback to old logic if no preset config
            return self._prepare_data_for_gpt_fallback(raw_data, show_config, target_news_count, target_time)
        
        # Step 1: Category Filtering (INCLUDE only allowed categories)
        allowed_categories = rss_filter.get("categories", ["zurich", "schweiz", "weather", "news"])
        excluded_categories = rss_filter.get("exclude_categories", ["crypto", "bitcoin"])
        min_priority = rss_filter.get("min_priority", 6)
        
        category_filtered_news = []
        for news_item in all_news:
            category = news_item.get("category", "").lower()
            priority = news_item.get("priority", 0)
            
            # Apply category filters
            if category in allowed_categories and category not in excluded_categories and priority >= min_priority:
                category_filtered_news.append(news_item)
        
        logger.info(f"📂 Kategorie-Filter: {len(category_filtered_news)} News (von {len(all_news)}) nach Kategorie + Priority-Filter")
        
        # Step 2: Age-based filtering with category-specific rules
        age_preference = rss_filter.get("age_preference", {})
        zurich_max_age = age_preference.get("zurich_max_age", 24)
        schweiz_max_age = age_preference.get("schweiz_max_age", 12) 
        other_max_age = age_preference.get("other_max_age", 6)
        
        age_filtered_news = []
        current_time = datetime.now()
        
        for news_item in category_filtered_news:
            try:
                published = datetime.fromisoformat(news_item.get("published", ""))
                age_hours = (current_time - published).total_seconds() / 3600
                category = news_item.get("category", "").lower()
                
                # Apply category-specific age limits
                max_age_for_category = other_max_age  # default
                if category == "zurich":
                    max_age_for_category = zurich_max_age
                elif category == "schweiz":
                    max_age_for_category = schweiz_max_age
                
                if age_hours <= max_age_for_category:
                    # Store calculated age for later use
                    news_item["age_hours"] = age_hours
                    age_filtered_news.append(news_item)
                    
            except Exception as e:
                # Include if date parsing fails (better safe than sorry)
                logger.warning(f"⚠️ Datum-Parsing Fehler für News: {e}")
                age_filtered_news.append(news_item)
        
        logger.info(f"⏰ Age-Filter: {len(age_filtered_news)} News nach kategorie-spezifischer Altersfilterung")
        
        # Step 3: Apply category weights and priority boost
        category_weights = rss_filter.get("category_weights", {"zurich": 3.0, "schweiz": 1.5, "news": 1.0})
        zurich_priority_boost = rss_filter.get("zurich_priority_boost", 2.0)
        
        for news_item in age_filtered_news:
            category = news_item.get("category", "").lower()
            base_priority = news_item.get("priority", 5)
            
            # Apply category weight
            weight = category_weights.get(category, 1.0)
            news_item["weight"] = weight
            
            # Apply Zurich priority boost
            if category == "zurich":
                news_item["boosted_priority"] = base_priority + zurich_priority_boost
            else:
                news_item["boosted_priority"] = base_priority
        
        # Step 4: Sort by weighted priority and age, then limit
        def sort_key(item):
            boosted_priority = item.get("boosted_priority", item.get("priority", 5))
            weight = item.get("weight", 1.0)
            age_hours = item.get("age_hours", 0)
            # Higher priority + higher weight + lower age = better score
            return -(boosted_priority * weight * (1 / (age_hours + 1)))
        
        age_filtered_news.sort(key=sort_key)
        
        # Step 5: Apply max feeds per category limit
        max_feeds_per_category = rss_filter.get("max_feeds_per_category", 10)
        category_counts = {}
        final_news = []
        
        for news_item in age_filtered_news:
            category = news_item.get("category", "").lower()
            current_count = category_counts.get(category, 0)
            
            if current_count < max_feeds_per_category:
                final_news.append(news_item)
                category_counts[category] = current_count + 1
            
            # Stop when we have enough for GPT
            if len(final_news) >= self._config.max_news_for_gpt:
                break
        
        # Final limit to max_news_for_gpt
        limited_news = final_news[:self._config.max_news_for_gpt]
        
        # Log filtering results
        logger.info(f"🎯 PRESET-FILTER RESULTS:")
        logger.info(f"   📊 Total → Kategorie → Age → Gewichtet → Final: {len(all_news)} → {len(category_filtered_news)} → {len(age_filtered_news)} → {len(final_news)} → {len(limited_news)}")
        logger.info(f"   📂 Erlaubte Kategorien: {', '.join(allowed_categories)}")
        logger.info(f"   🚫 Ausgeschlossen: {', '.join(excluded_categories)}")
        logger.info(f"   ⭐ Min. Priority: {min_priority}")
        logger.info(f"   ⏰ Age Limits: Zürich({zurich_max_age}h), Schweiz({schweiz_max_age}h), Other({other_max_age}h)")
        
        # Category breakdown
        category_breakdown = {}
        for item in limited_news:
            cat = item.get("category", "unknown")
            category_breakdown[cat] = category_breakdown.get(cat, 0) + 1
        logger.info(f"   📂 Final Categories: {dict(category_breakdown)}")
        
        return {
            "news": limited_news,
            "weather": raw_data.get("weather"),
            "crypto": raw_data.get("crypto"),
            "show_config": show_config,
            "target_news_count": target_news_count,
            "target_time": target_time,
            "processing_timestamp": datetime.now().isoformat(),
            "filter_stats": {
                "total_news": len(all_news),
                "category_filtered": len(category_filtered_news),
                "age_filtered": len(age_filtered_news),
                "weighted_filtered": len(final_news),
                "final_for_gpt": len(limited_news),
                "category_breakdown": category_breakdown,
                "applied_filters": {
                    "allowed_categories": allowed_categories,
                    "excluded_categories": excluded_categories,
                    "min_priority": min_priority,
                    "age_limits": {
                        "zurich_max_age": zurich_max_age,
                        "schweiz_max_age": schweiz_max_age,
                        "other_max_age": other_max_age
                    },
                    "category_weights": category_weights,
                    "zurich_priority_boost": zurich_priority_boost
                }
            }
        }
    
    def _prepare_data_for_gpt_fallback(
        self, raw_data: Dict[str, Any], show_config: Dict[str, Any],
        target_news_count: int, target_time: Optional[str]
    ) -> Dict[str, Any]:
        """Fallback to old 48h filter logic if no preset config available"""
        logger.warning("🔄 Verwende Fallback-Filterung (48h + Top 15)")
        
        # Old logic as fallback
        all_news = raw_data.get("news", [])
        cutoff_time = datetime.now() - timedelta(hours=self._config.news_filter_hours)
        
        recent_news = []
        for news_item in all_news:
            try:
                published = datetime.fromisoformat(news_item.get("published", ""))
                if published >= cutoff_time:
                    recent_news.append(news_item)
            except:
                recent_news.append(news_item)
        
        recent_news.sort(key=lambda x: x.get("published", ""), reverse=True)
        limited_news = recent_news[:self._config.max_news_for_gpt]
        
        logger.info(f"📊 Fallback Filter: {len(limited_news)} News (von {len(all_news)} total, {len(recent_news)} recent)")
        
        return {
            "news": limited_news,
            "weather": raw_data.get("weather"),
            "crypto": raw_data.get("crypto"),
            "show_config": show_config,
            "target_news_count": target_news_count,
            "target_time": target_time,
            "processing_timestamp": datetime.now().isoformat()
        }
    
    def _create_radio_show_prompt(self, prepared_data: Dict[str, Any], last_show_context: Optional[Dict[str, Any]] = None) -> str:
        """Create optimized GPT prompt with last show context for diversity"""
        
        show_config = prepared_data["show_config"]
        news = prepared_data["news"]
        weather = prepared_data["weather"]
        crypto = prepared_data["crypto"]
        target_count = prepared_data["target_news_count"]
        
        # Extract show details efficiently
        show_name = show_config["show"]["display_name"]
        city_focus = show_config["show"]["city_focus"]
        show_description = show_config["show"]["description"]
        categories = show_config["content"]["categories"]
        
        # ⭐ Voice-Konfiguration für Duo-Shows
        primary_speaker = show_config["speaker"]
        secondary_speaker = show_config.get("secondary_speaker")
        is_duo_show = show_config["show"].get("is_duo_show", False)
        
        # ⭐ Format erweiterte Daten-Sektionen
        weather_section = weather.get("current_summary", "Wetter nicht verfügbar") if weather else "Wetter nicht verfügbar"  # ⭐ Direkt GPT-Summary!
        crypto_section = crypto.get("bitcoin_summary", "Bitcoin nicht verfügbar") if crypto else "Bitcoin nicht verfügbar"  # ⭐ Direkt GPT-Summary!
        
        # ⭐ Dynamische Voice-Konfiguration basierend auf DB + Show-Settings
        speakers = self._get_dynamic_speakers(show_config, weather, primary_speaker, secondary_speaker)
        voice_setup, script_instruction = self._create_dynamic_voice_prompt(speakers)
        
        # ⭐ SMART: Last Show Context für maximale Diversität
        diversity_instruction = self._create_diversity_instruction(last_show_context)

        # ⭐ CLEAN ENGLISH STRUCTURE: Show parameters first, then data, instructions at the end
        return f"""You are AI producer for "{show_name}" - Radio show focused on {city_focus}.

🎭 SHOW STYLE: {show_description}

{voice_setup}

🌤️ WEATHER (Zurich): {weather_section}
₿ BITCOIN: {crypto_section}

{diversity_instruction}

{script_instruction}

📰 NEWS ({len(news)} available):
{self._format_news_for_prompt(news)}

TASK: Create natural radio script with {target_count} news segments.

QUALITY REQUIREMENTS:
1. Select {target_count} most relevant news for this show
2. Use complete summaries
3. Integrate weather + Bitcoin data if fitting
4. 2-3 minute natural radio script
5. Maintain show character consistently

OUTPUT: Direct radio script for ElevenLabs (NO JSON!)
- Natural, flowing text in English
- Speakers clearly separated: "MARCEL: [Text]", "JARVIS: [Text]"
- Emotions come from text context
- No special formatting or pause markings
- Simple speakable radio content"""
    
    def _format_news_for_prompt(self, news: List[Dict[str, Any]]) -> str:
        """Format news for GPT prompt efficiently - VOLLSTÄNDIG ohne Kürzung"""
        if not news:
            return "KEINE NEWS VERFÜGBAR"
        
        news_text = f"NEWS ({len(news)} verfügbar):\n"
        for i, item in enumerate(news, 1):
            age_hours = round(item.get('age_hours', 0))
            # FIXED: Vollständige Summary ohne Kürzung + Original URL für GPT
            summary = self._clean_html_from_summary(item.get('summary', 'Keine Zusammenfassung'))
            original_url = item.get('link', item.get('url', ''))
            
            news_text += f"{i}. [{item.get('source', 'Unknown')}] {item.get('title', 'Kein Titel')}\n"
            news_text += f"   📝 Volltext: {summary}\n"  # OHNE [:200]... Kürzung!
            news_text += f"   🔗 Original: {original_url}\n"  # Original URL für GPT
            news_text += f"   📂 Kategorie: {item.get('category', 'general')} | ⏰ Alter: {age_hours}h\n\n"
        
        return news_text
    
    def _create_diversity_instruction(self, last_show_context: Optional[Dict[str, Any]]) -> str:
        """Create smart diversity instruction based on last show context"""
        
        if not last_show_context or not last_show_context.get("selected_news"):
            return "🎯 CONTENT DIVERSITY: This is the first show - choose diverse, engaging news."
        
        last_news = last_show_context.get("selected_news", [])
        last_titles = last_show_context.get("last_news_titles", [])
        last_sources = last_show_context.get("last_news_sources", [])
        last_categories = last_show_context.get("last_news_categories", [])
        last_timestamp = last_show_context.get("last_show_timestamp", "")
        
        # Format last show summary for GPT
        last_summary = []
        for i, news in enumerate(last_news[:3], 1):  # Max 3 for brevity
            title = news.get("title", "")[:60] + "..." if len(news.get("title", "")) > 60 else news.get("title", "")
            source = news.get("source", "")
            last_summary.append(f"{i}. [{source}] {title}")
        
        diversity_instruction = f"""🎯 CONTENT DIVERSITY MANDATE:
LAST SHOW ({last_timestamp}):
{chr(10).join(last_summary)}

DIVERSITY REQUIREMENTS:
✨ SELECT COMPLETELY DIFFERENT NEWS - Avoid similar topics, sources, or angles
🔄 PRIORITIZE new sources: Avoid heavy reliance on {', '.join(last_sources[:3])}
📂 VARY categories: Last show focused on {', '.join(last_categories)}, diversify now
🎪 FRESH perspective: Even if covering similar events, use different angle/approach
⚡ ENSURE 100% unique content selection - maximum show-to-show diversity"""
        
        return diversity_instruction
    
    def _clean_html_from_summary(self, summary: str) -> str:
        """Entfernt HTML img tags und andere störende HTML-Elemente"""
        if not summary:
            return 'Keine Zusammenfassung verfügbar'
        
        import re
        
        # Entferne img tags komplett (inkl. style attributes)
        clean_text = re.sub(r'<img[^>]*>', '', summary)
        
        # Entferne style attributes aus allen tags
        clean_text = re.sub(r'style="[^"]*"', '', clean_text)
        
        # Entferne HTML paragraph tags aber behalte Inhalt
        clean_text = re.sub(r'</?p[^>]*>', ' ', clean_text)
        
        # Entferne div tags aber behalte Inhalt
        clean_text = re.sub(r'</?div[^>]*>', ' ', clean_text)
        
        # Bereinige verbleibende HTML tags (aber behalte Text)
        clean_text = re.sub(r'<[^>]+>', '', clean_text)
        
        # Bereinige mehrfache Leerzeichen und Zeilenumbrüche
        clean_text = ' '.join(clean_text.split())
        
        return clean_text.strip()
    
    def _format_weather_for_prompt(self, weather: Dict[str, Any]) -> str:
        """Format weather for GPT prompt - KOMPAKT aber vollständig"""
        if not weather:
            return "Nicht verfügbar"
        
        current = weather.get("current", weather)
        if not current:
            return "Nicht verfügbar"
        
        return f"""{current.get('temperature', 'N/A')}°C (gefühlt {current.get('feels_like', 'N/A')}°C), {current.get('description', 'N/A')}, {current.get('humidity', 'N/A')}% Humidity, Wind {current.get('wind_speed', 'N/A')}km/h, {current.get('pressure', 'N/A')}hPa, Sicht {current.get('visibility', 'N/A')}km, {current.get('clouds', 'N/A')}% Bewölkung"""
    
    def _format_crypto_for_prompt(self, crypto: Dict[str, Any]) -> str:
        """Format crypto for GPT prompt - KOMPAKT mit allen wichtigen Daten"""
        if not crypto or not crypto.get("bitcoin"):
            return "Nicht verfügbar"
        
        bitcoin = crypto["bitcoin"]
        trend = crypto.get("trend", {})
        alerts = crypto.get("alerts", [])
        
        # Kompakte Formatierung mit allen Daten
        crypto_text = f"""${bitcoin.get('price_usd', 0):,.0f} | Trends: 1h({bitcoin.get('change_1h', 0):+.1f}%) 24h({bitcoin.get('change_24h', 0):+.1f}%) 7d({bitcoin.get('change_7d', 0):+.1f}%) 30d({bitcoin.get('change_30d', 0):+.1f}%) 90d({bitcoin.get('change_90d', 0):+.1f}%) | Cap: ${bitcoin.get('market_cap', 0)/1e12:.1f}T | Vol: ${bitcoin.get('volume_24h', 0)/1e9:.1f}B"""

        # Trend-Message kompakt hinzufügen
        if trend and trend.get('message'):
            crypto_text += f""" | {trend['emoji']} {trend['message']}"""

        # Wichtigste Alerts kompakt
        if alerts:
            alert_msg = alerts[0].get('message', '').replace('₿ Bitcoin', 'BTC').replace('Current:', '')
            crypto_text += f""" | Alert: {alert_msg}"""
        
        return crypto_text
    
    async def _generate_radio_show_with_gpt(self, prompt: str, prepared_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate radio show with GPT-4 - Direct radio script output"""
        
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
            logger.info(f"📤 GPT Response (erste 500 Zeichen): {content[:500]}...")
            
            # ⭐ SIMPLE FIX: Die an GPT gesendeten News sind automatisch "selected"
            selected_news = prepared_data.get("news", []) if prepared_data else []
            
            # Return direct radio script with selected news
            result = {
                "radio_script": content.strip(),
                "segments": self._parse_script_segments(content),
                "selected_news": selected_news,  # ⭐ Die bereits gefilterten GPT-News!
                "content_focus": {"focus": "auto-detected", "reasoning": "Natürliches Script ohne JSON"},
                "quality_score": 0.9,
                "script_type": "natural_elevenlabs"
            }
            
            logger.info(f"✅ Radio-Script erfolgreich generiert ({len(content)} Zeichen)")
            return result
                
        except asyncio.TimeoutError:
            logger.error(f"❌ GPT-Timeout nach {self._config.gpt_timeout}s")
            raise Exception(f"GPT request timed out after {self._config.gpt_timeout} seconds")
        except Exception as e:
            logger.error(f"❌ GPT-Fehler: {e}")
            raise Exception(f"GPT processing failed: {str(e)}")
    

    
    def _parse_script_segments(self, script: str) -> List[Dict[str, Any]]:
        """Parse natural radio script into segments for ElevenLabs"""
        segments = []
        lines = script.split('\n')
        
        current_segment = []
        current_speaker = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Check if line starts with speaker name
            speaker_match = None
            for speaker_name in ['MARCEL', 'JARVIS', 'LUCY']:
                if line.startswith(f"{speaker_name}:"):
                    speaker_match = speaker_name.lower()
                    content = line[len(speaker_name)+1:].strip()
                    break
            
            if speaker_match:
                # Save previous segment if exists
                if current_segment and current_speaker:
                    segments.append({
                        "speaker": current_speaker,
                        "text": " ".join(current_segment),
                        "type": "dialogue"
                    })
                
                # Start new segment
                current_speaker = speaker_match
                current_segment = [content] if content else []
            else:
                # Continue current segment
                if current_speaker and line:
                    current_segment.append(line)
        
        # Add final segment
        if current_segment and current_speaker:
            segments.append({
                "speaker": current_speaker,
                "text": " ".join(current_segment),
                "type": "dialogue"
            })
        
        # If no speakers found, treat as single marcel segment
        if not segments and script.strip():
            segments.append({
                "speaker": "marcel",
                "text": script.strip(),
                "type": "monologue"
            })
        
        return segments
    
    def _create_fallback_result(self, content: str) -> Dict[str, Any]:
        """Create fallback result when JSON parsing fails"""
        return {
            "selected_news": [],
            "radio_script": content,
            "segments": [{"type": "content", "content": content}],
            "content_focus": {"focus": "general", "reasoning": "Fallback due to parsing error"},
            "quality_score": 0.5
        }
    
    def _get_dynamic_speakers(self, show_config: Dict[str, Any], weather: Dict[str, Any], 
                             primary_speaker: Dict[str, Any], secondary_speaker: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Dynamisch Sprecher basierend auf Show-Config und Weather-Status bestimmen"""
        speakers = []
        
        # Primary Speaker immer dabei
        if primary_speaker:
            speakers.append(primary_speaker)
        
        # Secondary Speaker wenn Duo-Show
        is_duo_show = show_config["show"].get("is_duo_show", False)
        if is_duo_show and secondary_speaker:
            speakers.append(secondary_speaker)
        
        # Weather Specialist nur wenn "weather" in RSS-Filter-Kategorien definiert ist
        rss_categories = show_config.get("content", {}).get("rss_filter", {}).get("categories", [])
        has_weather_category = "weather" in [cat.lower() for cat in rss_categories]
        
        if has_weather_category:
            # Lucy aus DB holen für Weather
            weather_speaker = self._get_weather_speaker()
            if weather_speaker:
                speakers.append(weather_speaker)
        
        return speakers
    
    def _get_weather_speaker(self) -> Dict[str, Any]:
        """Holt Weather-Sprecher (Lucy) aus Supabase DB"""
        try:
            from database.supabase_client import SupabaseClient
            
            supabase = SupabaseClient()
            result = supabase.client.table('voice_configurations').select('*').eq('voice_name', 'Lucy').execute()
            
            if result.data:
                speaker_data = result.data[0]
                return {
                    "voice_name": speaker_data["voice_name"],
                    "description": speaker_data["description"],
                    "voice_id": speaker_data["voice_id"],
                    "specialty": "weather"  # Markiert als Weather-Specialist
                }
        except Exception as e:
            logger.warning(f"⚠️ Konnte Weather-Sprecher nicht aus DB laden: {e}")
        
        return None
    
    def _create_dynamic_voice_prompt(self, speakers: List[Dict[str, Any]]) -> tuple[str, str]:
        """Creates dynamic voice prompt based on number of speakers - only use DB descriptions"""
        if not speakers:
            return "🎤 NO SPEAKERS CONFIGURED", "Standard radio script format"
        
        num_speakers = len(speakers)
        
        if num_speakers == 1:
            speaker = speakers[0]
            voice_setup = f"""🎤 SINGLE HOST:
- Speaker: {speaker["voice_name"]} - {speaker["description"]}
- Format: Solo presentation"""
            
            script_instruction = f"""SCRIPT FORMAT: 
- Format: "{speaker["voice_name"].upper()}: [Text]"
- Use natural, flowing English"""
            
        elif num_speakers == 2:
            primary, secondary = speakers[0], speakers[1]
            voice_setup = f"""🎤 DUO HOSTS:
- Primary: {primary["voice_name"]} - {primary["description"]}
- Secondary: {secondary["voice_name"]} - {secondary["description"]}
- Format: Natural dialogue between both hosts"""
            
            script_instruction = f"""DIALOGUE FORMAT:
- Format: "{primary["voice_name"].upper()}: [Text]" and "{secondary["voice_name"].upper()}: [Text]"
- Natural transitions and conversations between hosts"""
            
        else:  # 3+ Speakers
            voice_setup = f"""🎤 MULTI-HOST SHOW ({num_speakers} Hosts):"""
            speaker_formats = []
            
            for speaker in speakers:
                voice_setup += f"\n- {speaker['voice_name']}: {speaker['description']}"
                speaker_formats.append(f'"{speaker["voice_name"].upper()}: [Text]"')
            
            voice_setup += f"\n- Format: Natural conversation between all {num_speakers} hosts"
            
            # Special note for weather specialist
            weather_note = ""
            for speaker in speakers:
                if speaker.get("specialty") == "weather":
                    weather_note = f"\n- {speaker['voice_name']} handles ALL weather segments"
                    break
            
            script_instruction = f"""MULTI-HOST DIALOGUE:
- Format: {', '.join(speaker_formats)}
- Natural conversation flow between all hosts{weather_note}
- Smooth transitions and authentic interactions"""
        
        return voice_setup, script_instruction
    

    
    # Fallback-Funktion entfernt - keine Fallbacks mehr! 

 