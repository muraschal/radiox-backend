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

RADICALLY SIMPLIFIED: All intelligence externalized to GPT!

- No local categorization
- No local filtering  
- No local prioritization
- No complex algorithms

SIMPLE: Prepare data → GPT → Finished radio show

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
    max_news_for_gpt: int = 10
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
        show_config: Dict[str, Any] = None, last_show_context: Optional[Dict[str, Any]] = None,
        used_article_titles: Optional[set] = None, language: str = "en"
    ) -> Dict[str, Any]:
        """Main processing pipeline with a new two-stage GPT process (Text-based final output)."""
        
        logger.info("🤖 Starting two-stage radio show creation (Stage 2: Plain Text)...")
        
        try:
            show_config = show_config or await self.get_show_configuration(preset_name or "zurich")
            if not show_config:
                raise Exception(f"Show configuration for '{preset_name}' not found")
            
            # --- STAGE 1: Article Selection based on Titles (JSON based) ---
            logger.info("🔬 Stage 1: Selecting relevant article IDs and reasons...")
            prepared_titles = self._prepare_titles_for_gpt(raw_data, show_config, used_article_titles)
            
            if not prepared_titles:
                raise Exception("No fresh, relevant articles found after filtering. Cannot proceed.")

            selection_prompt = self._create_article_selection_prompt(prepared_titles, last_show_context, target_news_count, show_config)
            selection_result = await self._select_articles_with_gpt(selection_prompt)
            
            selected_ids = [item.get("id") for item in selection_result.get("selected_items", [])]
            if not selected_ids:
                raise Exception("GPT failed to select any article IDs in Stage 1.")
            
            logger.info(f"✅ Stage 1 complete. GPT selected {len(selected_ids)} articles with reasons.")

            # --- STAGE 2: Script Generation based on Full Content (Text based) ---
            logger.info("✍️ Stage 2: Generating plain text script from full content of selected articles...")
            full_content_for_scripting = self._get_full_content_for_selected_articles(selected_ids, prepared_titles)
            
            scripting_prompt_data = {
                "news": full_content_for_scripting, "weather": raw_data.get("weather", {}),
                "crypto": raw_data.get("crypto", {}), "show_config": show_config,
                "target_news_count": len(full_content_for_scripting), "target_time": target_time,
                "language": language
            }
            scripting_prompt = self._create_scripting_prompt(scripting_prompt_data)
            radio_script_text = await self._generate_script_text_with_gpt(scripting_prompt)

            # Manually construct the final object
            final_selected_articles = self._map_reasons_to_selected_articles(
                selection_result.get("selected_items", []), full_content_for_scripting, prepared_titles
            )

            radio_show = {
                "radio_script": radio_script_text,
                "selected_news": final_selected_articles,
                "segments": self._parse_script_segments(radio_script_text),
            }

            logger.info("✅ Stage 2 complete. Plain text radio script generated.")
            
            result = self._create_processing_result(
                radio_show, raw_data, show_config, 
                {
                    "stage1_selection_prompt": selection_prompt,  # Article selection (JSON)
                    "stage2_scripting_prompt": scripting_prompt   # Script writing (Text)
                },
                scripting_prompt_data, target_news_count, target_time, preset_name
            )
            
            # DASHBOARD GENERATION MOVED TO MAIN WORKFLOW - Don't generate here anymore!
            # await self._generate_new_tailwind_dashboard(result, raw_data, show_config)
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Two-stage GPT Content Processing failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return self._create_error_result(str(e))

    def _map_reasons_to_selected_articles(self, selection_data: List[Dict], all_selected_articles: List[Dict], prepared_titles: List[Dict]) -> List[Dict]:
        """Maps the relevance reasons from GPT's Stage 1 output to the final selected articles."""
        # Create a map of ID to reason
        reason_map = {item.get("id"): item.get("reason") for item in selection_data}
        
        # Create a map of article title to the full article data
        title_to_article_map = {article.get('title'): article for article in all_selected_articles}

        # Create a map of ID to title from the list that was sent to GPT
        id_to_title_map = {item.get('id'): item.get('title') for item in prepared_titles}

        final_articles_with_reason = []
        for selected_id, reason in reason_map.items():
            title = id_to_title_map.get(selected_id)
            if title:
                article = title_to_article_map.get(title)
                if article:
                    article_copy = article.copy()
                    article_copy['relevance_reason'] = reason
                    final_articles_with_reason.append(article_copy)
        
        return final_articles_with_reason

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
        """SIMPLE CATEGORY-BASED FILTERING - 20 latest from allowed categories to GPT"""
        
        all_news = raw_data.get("news", [])
        # Extract allowed categories from DB (silent processing)
        rss_filter = show_config.get("content", {}).get("rss_filter", {})
        allowed_categories = rss_filter.get("categories", [])
        
        if not allowed_categories:
            allowed_categories = ["zurich"]
        
        # Step 1: Filter by allowed categories only
        category_filtered_news = []
        for news_item in all_news:
            category = news_item.get("category", "").lower()
            if category in allowed_categories:
                category_filtered_news.append(news_item)
        
        # Step 2: Sort by publication date (newest first)
        category_filtered_news.sort(key=lambda x: x.get("published", ""), reverse=True)
        
        # Step 3: Take the 20 most recent
        top_20_news = category_filtered_news[:20]
        for i, item in enumerate(top_20_news, 1):
            title = item.get('title', 'No Title')[:60]
            source = item.get('source', 'Unknown')
            category = item.get('category', 'unknown')
            logger.info(f"   {i:2d}. [{source.upper()}] {title}... ({category})")
        
        return {
            "news": top_20_news,
            "weather": raw_data.get("weather"),
            "crypto": raw_data.get("crypto"),
            "show_config": show_config,
            "target_news_count": target_news_count,
            "target_time": target_time,
            "processing_timestamp": datetime.now().isoformat(),
            "filter_stats": {
                "total_news": len(all_news),
                "category_filtered": len(category_filtered_news),
                "final_for_gpt": len(top_20_news),
                "allowed_categories": allowed_categories
            }
        }
    
    def _prepare_data_for_gpt_fallback(
        self, raw_data: Dict[str, Any], show_config: Dict[str, Any],
        target_news_count: int, target_time: Optional[str]
    ) -> Dict[str, Any]:
        """Fallback to old 48h filter logic if no preset config available"""
        logger.warning("🔄 Using fallback filtering (48h + Top 15)")
        
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
        

        
        return {
            "news": limited_news,
            "weather": raw_data.get("weather"),
            "crypto": raw_data.get("crypto"),
            "show_config": show_config,
            "target_news_count": target_news_count,
            "target_time": target_time,
            "processing_timestamp": datetime.now().isoformat()
        }
    
    def _create_scripting_prompt(self, prepared_data: Dict[str, Any]) -> str:
        """Creates a simplified, text-based prompt for GPT to write the radio script."""
        show_config = prepared_data.get("show_config", {})
        news = prepared_data.get("news", [])
        weather = prepared_data.get("weather", {})
        crypto = prepared_data.get("crypto", {})
        target_time = prepared_data.get('target_time', 'a few minutes')
        language = prepared_data.get('language', 'en')

        show_details = show_config.get("show", {})
        show_name = show_details.get("display_name", "RadioX")
        
        primary_speaker_config = show_config.get("speaker", {"voice_name": "Marcel", "description": "Host"})
        secondary_speaker_config = show_config.get("secondary_speaker", {"voice_name": "Jarvis", "description": "AI Assistant"})
        
        all_speakers = self._get_dynamic_speakers(
            show_config, weather, primary_speaker_config, secondary_speaker_config
        )
        
        # Check if this is a solo show
        is_duo_show = show_details.get("is_duo_show", False)
        
        # Build show style from database configuration
        show_style = self._create_show_style_description(show_details)
        
        # Build speaker descriptions
        speaker_descriptions = self._create_speaker_descriptions(all_speakers)
        
        # Build content blocks
        content_blocks = self._create_content_blocks(news, weather, crypto)
        
        # Get current time for time-appropriate greeting
        from datetime import datetime
        current_hour = datetime.now().hour
        if 5 <= current_hour < 12:
            time_of_day = "morning"
            greeting_guidance = "Good morning greetings appropriate"
        elif 12 <= current_hour < 17:
            time_of_day = "afternoon" 
            greeting_guidance = "Good afternoon greetings appropriate"
        elif 17 <= current_hour < 22:
            time_of_day = "evening"
            greeting_guidance = "Good evening greetings appropriate"
        else:
            time_of_day = "late night"
            greeting_guidance = "Late night/good evening greetings appropriate"
            
        # Language configuration
        if language == "de":
            lang_instruction = """🌍 SPRACHE: NUR DEUTSCH
Schreibe den kompletten Dialog auf DEUTSCH. Alle Sprecher-Dialoge müssen auf Deutsch sein."""
            lang_name = "DEUTSCH"
        else:
            lang_instruction = """🌍 LANGUAGE: ENGLISH ONLY
Write the entire dialogue in ENGLISH. All speaker dialogue must be in English language."""
            lang_name = "ENGLISH"

        return f"""🎙️ FINAL RADIOX PROMPT
Create a realistic radio script with defined speakers for a {target_time or "5-7 minute"} show.

{lang_instruction}

⏰ TIME CONTEXT: {time_of_day.upper()} ({current_hour:02d}:xx)
Current time guidance: {greeting_guidance}

📋 FORMAT:
{self._get_format_instructions(is_duo_show, primary_speaker_config.get("voice_name", "speaker"))}

No explanations. No narrative text. No names in dialogue unless naturally occurring.

🎯 GOAL:
Speakers discuss content with strong positions, not generic phrases. Each statement should reflect the speaker's personality, stance, and mindset.

Create a thematic back-and-forth - a ping-pong of opinion, contrast, friction, or surprising agreement.

💥 INTRO:
The first speaker opens with a distinctive, striking introduction - appropriate for the current {time_of_day}, can be over-the-top, cheeky, dark, poetic, or ironic.

🎭 STYLE & TONE:
{show_style}

No neutrality - the show lives on attitude and interpretation.

❌ AVOID:
• Explanatory moderation
• Filler phrases like "That's right", "Interesting", "Good question"
• Meaningless filler sentences
• Radio jargon or meta-commentary
• Overusing speaker names in dialogue - let conversation flow naturally

✅ USE INSTEAD:
• Direct opinions and clear statements
• Cynicism, sarcasm, thoughtfulness
• Humor, contrast, friction between speakers
• Surprising turns and perspectives

📥 INPUT:

SPEAKER_DESCRIPTIONS:
{speaker_descriptions}

CONTENT_BLOCKS:
{content_blocks}

📤 OUTPUT:
Only the dialogue text - directly usable as radio script."""

    def _format_articles_for_prompt(self, news: List[Dict[str, Any]]) -> str:
        """Helper function to format a list of articles for the GPT prompt."""
        formatted_news = []
        for i, item in enumerate(news):
            clean_summary = self._clean_html_from_summary(item.get("summary", ""))
            formatted_news.append(
                f"ID: {i+1}\\n"
                f"Title: {item.get('title', 'No Title')}\\n"
                f"Source: {item.get('source', 'Unknown')}\\n"
                f"Published: {item.get('published', 'N/A')}\\n"
                f"Summary: {clean_summary}"
            )
        return "\\n---\\n".join(formatted_news)

    def _create_diversity_instruction(self, last_show_context: Optional[Dict[str, Any]]) -> str:
        """Simple diversity instruction with direct DB data."""
        if not last_show_context:
            return "**DIVERSITY:** This is the first show - all topics are available."

        try:
            show_title = last_show_context.get("show_title", "Previous Show")
            used_titles = last_show_context.get("last_news_titles", [])
            
            if not used_titles:
                return "**DIVERSITY:** Previous show had no articles - all topics are available."

            # Keep it simple - just show the titles from last show
            instruction = f"**DIVERSITY:** {show_title} covered these topics. Avoid repeating them:\n"
            for title in used_titles[:10]:  # Max 10 to keep prompt clean
                instruction += f"• {title}\n"
            
            instruction += "\nSelect different topics to keep content fresh."
            return instruction

        except Exception as e:
            logger.warning(f"⚠️ Could not create diversity instruction: {e}")
            return "**DIVERSITY:** Select freely - no previous show data available."

    async def _generate_script_text_with_gpt(self, prompt: str) -> str:
        """Generates the raw radio script text from GPT."""
        logger.info("🤖 Sending request to gpt-4 for script generation...")
        try:
            response = await self._openai_client.chat.completions.create(
                model=self._config.gpt_model,
                messages=[{"role": "system", "content": prompt}],
                temperature=0.7,
                timeout=self._config.gpt_timeout,
            )
            content = response.choices[0].message.content
            return content.strip() if content else "Error: GPT returned empty content."
        except Exception as e:
            logger.error(f"❌ GPT script generation (Stage 2) failed: {e}")
            return f"Error: Could not generate script. {e}"

    def _clean_html_from_summary(self, summary: str) -> str:
        """Clean HTML tags and entities from news summary"""
        if not summary:
            return 'No summary available'
        
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
        """Use GPT-optimized weather summary directly from Weather Service"""
        if not weather:
            return "Weather data unavailable"
        
        # Use the GPT-optimized summary directly
        current_summary = weather.get('current_summary')
        if current_summary:
            return current_summary
        
        # Fallback to basic data if GPT summary not available
        current = weather.get("current", weather)
        if current and current.get('temperature'):
            temp = current.get('temperature')
            description = current.get('description', '')
            return f"{temp}°C, {description}".strip(', ')
        
        return "Weather data unavailable"
    
    def _format_crypto_for_prompt(self, crypto: Dict[str, Any]) -> str:
        """Use GPT-optimized bitcoin summary directly from Bitcoin Service"""
        if not crypto:
            return "Crypto data unavailable"
        
        # Use the GPT-optimized summary directly
        bitcoin_summary = crypto.get('bitcoin_summary')
        if bitcoin_summary:
            return bitcoin_summary
        
        # Fallback to basic data if GPT summary not available
        bitcoin = crypto.get("bitcoin", {})
        if bitcoin and bitcoin.get('price_usd'):
            price = bitcoin.get('price_usd')
            change_24h = bitcoin.get('change_24h', 0)
            try:
                return f"Bitcoin ${float(price):,.0f} ({float(change_24h):+.1f}% 24h)"
            except (ValueError, TypeError):
                return f"Bitcoin ${price} ({change_24h}% 24h)"
        
        return "Bitcoin data unavailable"
    
    def _get_dynamic_speakers(self, show_config: Dict[str, Any], weather: Dict[str, Any], 
                             primary_speaker: Dict[str, Any], secondary_speaker: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Dynamically determine speakers based on show config and weather status"""
        speakers = []
        
        # Primary Speaker always included
        if primary_speaker:
            speakers.append(primary_speaker)
        
        # Secondary Speaker if duo show
        is_duo_show = show_config["show"].get("is_duo_show", False)
        if is_duo_show and secondary_speaker:
            speakers.append(secondary_speaker)
        
        # **SIMPLE RULE**: Weather Speaker nur wenn "weather" in RSS-Kategorien
        rss_filter = show_config.get("content", {}).get("rss_filter", "")
        if isinstance(rss_filter, str):
            rss_categories = [cat.strip().lower() for cat in rss_filter.split(",") if cat.strip()]
        else:
            rss_categories = rss_filter.get("categories", []) if isinstance(rss_filter, dict) else []
        has_weather_category = "weather" in rss_categories
        
        if has_weather_category:
            weather_speaker_config = show_config.get("weather_speaker")
            if weather_speaker_config:
                speakers.append(weather_speaker_config)
        
        return speakers
    
    def _get_weather_speaker(self) -> Dict[str, Any]:
        """Returns a default weather speaker configuration."""
        return {
            "voice_name": "lucy",
            "description": "Provides sultry, engaging weather reports.",
            "type": "weather"
        }
    
    def _create_dynamic_voice_prompt(self, speakers: List[Dict[str, Any]]) -> tuple[str, str]:
        """Creates clean, readable voice prompt from database speaker configs."""
        if not speakers:
            return "", "Marcel and Jarvis"

        try:
            voice_prompts = []
            speaker_names = []
            for speaker in speakers:
                # Get real data from database
                name = speaker.get("voice_name", "Unknown Speaker")
                description = speaker.get("description", "A speaker for the show.")
                speaker_names.append(name)
                
                # Clean description: normalize whitespace and remove extra newlines
                clean_description = " ".join(description.split())
                
                # Clean, readable format with consistent formatting
                voice_prompts.append(f"{name}: {clean_description}")
            
            # Clean join with empty lines between speakers for better readability
            prompt_str = "\n\n".join(voice_prompts)
            names_str = " and ".join(speaker_names)
            return prompt_str, names_str
        except Exception as e:
            logger.error(f"Failed to create dynamic voice prompt: {e}")
            return "Marcel: Host\nJarvis: Co-Host", "Marcel and Jarvis"
    
    def _create_dynamic_example(self, speakers: List[Dict[str, Any]], show_config: Dict[str, Any]) -> str:
        """Creates a dynamic conversation example based on the actual speakers for this show."""
        if not speakers:
            return "Example:\nMarcel: There's this fascinating story about a tech breakthrough in Zurich.\nJarvis: Indeed, though I question whether the market implications are being overstated."
        
        try:
            # Get speaker names
            speaker_names = [speaker.get("voice_name", "Speaker") for speaker in speakers]
            primary_speaker = speaker_names[0] if speaker_names else "Marcel"
            
            # Check if we have weather categories to include weather content
            rss_filter = show_config.get("content", {}).get("rss_filter", "")
            if isinstance(rss_filter, str):
                rss_categories = [cat.strip().lower() for cat in rss_filter.split(",") if cat.strip()]
            else:
                rss_categories = rss_filter.get("categories", []) if isinstance(rss_filter, dict) else []
            has_weather_category = "weather" in rss_categories
            
            # Start building example
            example_lines = ["Example:"]
            example_lines.append(f"{primary_speaker}: There's this fascinating story about a tech breakthrough in Zurich.")
            
            # Add second speaker if available
            if len(speaker_names) >= 2:
                secondary_speaker = speaker_names[1]
                example_lines.append(f"{secondary_speaker}: Indeed, though I question whether the market implications are being overstated.")
            
            # Add weather speaker if weather category is enabled and weather speaker exists
            if has_weather_category and len(speaker_names) >= 3:
                weather_speaker = speaker_names[2]
                example_lines.append(f"{weather_speaker}: Speaking of the market, Bitcoin is up 2% today, and the weather's perfect for outdoor celebrations at 18 degrees.")
            elif has_weather_category and len(speaker_names) >= 2:
                # Use secondary speaker for weather if no dedicated weather speaker
                secondary_speaker = speaker_names[1]
                example_lines.append(f"{secondary_speaker}: Speaking of the market, Bitcoin is up 2% today, and the weather's perfect for outdoor celebrations at 18 degrees.")
            elif has_weather_category:
                # Use primary speaker for weather if only one speaker
                example_lines.append(f"{primary_speaker}: Looking at crypto today, Bitcoin is up 2% and with this beautiful 18-degree weather, it's perfect for outdoor celebrations.")
            
            return "\n".join(example_lines)
            
        except Exception as e:
            logger.error(f"Failed to create dynamic example: {e}")
            return "Example:\nMarcel: There's this fascinating story about a tech breakthrough in Zurich.\nJarvis: Indeed, though I question whether the market implications are being overstated."
    
    def _create_show_style_description(self, show_details: Dict[str, Any]) -> str:
        """Creates show style description from database configuration"""
        try:
            show_description = show_details.get("description", "")
            show_name = show_details.get("display_name", "RadioX")
            city_focus = show_details.get("city_focus", "")
            
            # Extract style elements from show description
            style_description = f"Show: {show_name}"
            if city_focus:
                style_description += f" | Focus: {city_focus}"
            if show_description:
                style_description += f"\nStyle: {show_description}"
            
            return style_description
            
        except Exception as e:
            logger.error(f"Failed to create show style description: {e}")
            return "Style: Authentic, direct discussion with clear positions"
    
    def _create_speaker_descriptions(self, speakers: List[Dict[str, Any]]) -> str:
        """Creates optimized speaker descriptions for the new prompt format"""
        try:
            if not speakers:
                return "Marcel: Energetic host with analytical mind\nJarvis: AI voice with surgical precision and dry wit"
            
            speaker_descriptions = []
            for speaker in speakers:
                name = speaker.get("voice_name", "Unknown")
                description = speaker.get("description", "A speaker for the show.")
                
                # Clean and format description
                clean_description = " ".join(description.split())
                speaker_descriptions.append(f"{name}: {clean_description}")
            
            return "\n".join(speaker_descriptions)
            
        except Exception as e:
            logger.error(f"Failed to create speaker descriptions: {e}")
            return "Marcel: Host\nJarvis: Co-Host"
    
    def _create_content_blocks(self, news: List[Dict[str, Any]], weather: Dict[str, Any], crypto: Dict[str, Any]) -> str:
        """Creates structured content blocks for the new prompt format"""
        try:
            content_blocks = []
            
            # News Block
            if news:
                content_blocks.append("📰 NEWS:")
                for i, article in enumerate(news, 1):
                    title = article.get('title', 'No Title')
                    source = article.get('source', 'Unknown')
                    summary = self._clean_html_from_summary(article.get('summary', ''))
                    
                    # Keep full summary for better GPT understanding
                    # GPT-4 can handle much longer contexts, so we preserve complete information
                    if len(summary) > 1000:
                        summary = summary[:1000] + "..."
                    
                    content_blocks.append(f"{i}. [{source}] {title}")
                    content_blocks.append(f"   {summary}")
            
            # Weather Block (if available)
            weather_formatted = self._format_weather_for_prompt(weather)
            if weather_formatted and weather_formatted != "Weather data unavailable":
                content_blocks.append("\n🌤️ WEATHER:")
                content_blocks.append(weather_formatted)
            
            # Crypto Block (if available)
            crypto_formatted = self._format_crypto_for_prompt(crypto)
            if crypto_formatted and crypto_formatted != "Crypto data unavailable":
                content_blocks.append("\n₿ BITCOIN:")
                content_blocks.append(crypto_formatted)
            
            return "\n".join(content_blocks)
            
        except Exception as e:
            logger.error(f"Failed to create content blocks: {e}")
            return "Content blocks unavailable"

    def _get_format_instructions(self, is_duo_show: bool, primary_speaker_name: str = "speaker") -> str:
        """Returns format instructions based on whether it's a solo or duo show - FULLY GENERIC"""
        if is_duo_show:
            # Traditional dialogue format for duo shows
            return """Output only the speakable text in this format:
SPEAKER: ...
SPEAKER2: ..."""
        else:
            # **NATURAL SOLO SHOW:** Continuous monologue with minimal speaker tags
            speaker_lower = primary_speaker_name.lower()
            return f"""Output only the speakable text as a natural continuous monologue:

{speaker_lower}: Introduction with self-identification and welcome...

Continue with flowing paragraphs without repeating the speaker name. Only use '{speaker_lower}:' again if there's a natural break or topic change that would require a pause in real radio.

CRITICAL: This is a SOLO SHOW - avoid repetitive '{speaker_lower}:' tags. Let the content flow naturally as one person speaking."""
    

    
    # Fallback-Funktion entfernt - keine Fallbacks mehr! 

    def _create_article_selection_prompt(self, news_titles: List[Dict[str, Any]], last_show_context: Optional[Dict[str, Any]], target_count: int, show_config: Dict[str, Any]) -> str:
        """Creates a show-aware prompt for GPT to select the best article IDs and provide reasons."""
        
        diversity_instruction = self._create_diversity_instruction(last_show_context)
        
        # IMPROVED: One-line format per news article for better readability
        formatted_titles = []
        for item in news_titles:
            age = item.get('age_hours', 'N/A')
            formatted_titles.append(
                f"ID: {item['id']} | {item['title']} | [{item['source']}] | {item['category']} | {age}h ago"
            )
        
        titles_str = "\n".join(formatted_titles)
        
        # Extract show context for intelligent selection - 1:1 FROM DATABASE
        show_details = show_config.get("show", {})
        
        # Direct 1:1 values from database without any modification
        show_name = show_details.get("display_name", "RadioX")
        city_focus = show_details.get("city_focus", "Zürich")
        show_description = show_details.get("description", "")
        
        # Build show style with full DB values
        show_style = f"Show: {show_name} | Focus: {city_focus}\nStyle: {show_description}"
        
        # Get speaker descriptions 1:1 from database
        primary_speaker_config = show_config.get("speaker", {"voice_name": "Marcel", "description": "Host"})
        secondary_speaker_config = show_config.get("secondary_speaker", {"voice_name": "Jarvis", "description": "AI Assistant"})
        all_speakers = self._get_dynamic_speakers(show_config, {}, primary_speaker_config, secondary_speaker_config)
        
        # Build speaker descriptions with full DB values (no truncation)
        speaker_descriptions_list = []
        for speaker in all_speakers:
            name = speaker.get("voice_name", "Unknown")
            description = speaker.get("description", "No description available.")
            # Use full description from DB without any modification
            speaker_descriptions_list.append(f"{name}: {description}")
        
        speaker_descriptions = "\n".join(speaker_descriptions_list)
        
        # Determine content scope
        city_focus = show_details.get("city_focus", "Zürich")
        content_scope = f"Local focus: {city_focus}, with selective international/tech coverage"

        return f"""
# SYSTEM PROMPT – RADIOX ARTICLE SELECTOR

## MISSION
You are an expert content strategist and radio news curator. Your task is to select exactly {target_count} articles from the provided list that best fit the upcoming show – based on its unique tone, scope, and speaker style.

## SHOW CONTEXT
**Show Style:** 
{show_style}

**Speaker Descriptions:**
{speaker_descriptions}

**Content Scope:** 
{content_scope}

## FILTER LOGIC
Select {target_count} articles that best match:
1. **Stylistic fit:** Articles that invite commentary in the voice of the show (e.g. irony, critique, emotional depth, insider analysis).
2. **Scope fit:** Articles that match the show's geographic or topical focus.
3. **Narrative potential:** Prefer stories with tension, contradiction, surprise or absurdity – content that allows speakers to *react*, not just read.
4. **Recency:** Strongly prioritize articles <6h old unless older stories are a better stylistic fit.
5. **Thematic diversity:** Avoid selecting 2 stories on the same topic unless they clearly contrast each other.

{diversity_instruction}

## AVAILABLE ARTICLES (One per line)
{titles_str}

## OUTPUT FORMAT (TEXT ONLY)
Use the following format:

SELECTED ARTICLES:
ID: 1
REASON: One-sentence reason focused on why the story fits the show – tone-aware, not generic.

ID: 15
REASON: One-sentence reason focused on why the story fits the show – tone-aware, not generic.

ID: 23
REASON: One-sentence reason focused on why the story fits the show – tone-aware, not generic.

ID: 42
REASON: One-sentence reason focused on why the story fits the show – tone-aware, not generic.
"""

    async def _select_articles_with_gpt(self, prompt: str) -> Dict[str, List]:
        """Calls GPT to get a list of selected article IDs and reasons."""
        try:
            response = await self._openai_client.chat.completions.create(
                model=self._config.gpt_model,
                messages=[{"role": "system", "content": prompt}],
                temperature=0.2,
                timeout=self._config.gpt_timeout,
            )
            content = response.choices[0].message.content
            if not content:
                return {}
            
            # Parse simple text format instead of JSON
            selected_items = []
            lines = content.strip().split('\n')
            current_id = None
            current_reason = None
            
            for line in lines:
                line = line.strip()
                if line.startswith('ID:'):
                    # Save previous item if we have one
                    if current_id is not None and current_reason is not None:
                        selected_items.append({
                            "id": current_id,
                            "reason": current_reason
                        })
                    
                    # Start new item
                    try:
                        current_id = int(line.replace('ID:', '').strip())
                        current_reason = None
                    except ValueError:
                        logger.warning(f"Could not parse ID from line: {line}")
                        current_id = None
                        
                elif line.startswith('REASON:'):
                    if current_id is not None:
                        current_reason = line.replace('REASON:', '').strip()
            
            # Don't forget the last item
            if current_id is not None and current_reason is not None:
                selected_items.append({
                    "id": current_id,
                    "reason": current_reason
                })
            
            logger.info(f"✅ Parsed {len(selected_items)} article selections from GPT")
            return {"selected_items": selected_items}
            
        except Exception as e:
            logger.error(f"❌ GPT article selection (Stage 1) failed: {e}")
            return {}

    def _prepare_titles_for_gpt(self, raw_data: Dict[str, Any], show_config: Dict[str, Any], used_titles: Optional[set] = None) -> List[Dict[str, Any]]:
        """
        Prepares a list of the top 50 most relevant news titles for GPT,
        after applying proactive and preset-based filtering.
        """
        all_news = raw_data.get("news", [])
        used_titles = used_titles or set()

        # 1. Proactive filtering: Remove already used articles (title-based)
        fresh_news = [item for item in all_news if item.get("title") not in used_titles]
        logger.info(f"📰 Proactive Filter: Removed {len(all_news) - len(fresh_news)} already used articles. {len(fresh_news)} remain.")

        # 2. Preset-based filtering - now supports TEXT format RSS filter
        rss_filter = show_config.get("content", {}).get("rss_filter", "")
        if not rss_filter:
            logger.warning("⚠️ No RSS filter in show_config, using all fresh news.")
            preset_filtered_news = fresh_news
        else:
            # Parse text-based RSS filter (e.g., "news, international, wirtschaft")
            if isinstance(rss_filter, str):
                allowed_categories = [cat.strip().lower() for cat in rss_filter.split(",") if cat.strip()]
            else:
                # Fallback for old JSON format 
                allowed_categories = rss_filter.get("categories", []) if isinstance(rss_filter, dict) else []
            
            preset_filtered_news = [
                item for item in fresh_news 
                if item.get("category", "").lower() in allowed_categories
            ]
            logger.info(f"📂 Preset Category Filter: {len(preset_filtered_news)} articles remain after keeping only {allowed_categories}.")

        # 3. Sort the relevant news by publication date
        preset_filtered_news.sort(key=lambda x: x.get("published", ""), reverse=True)
        
        # 4. Limit to the top 50 for GPT selection
        top_50_news = preset_filtered_news[:50]


        # Show clean article overview for GPT selection
        logger.info(f"📋 ARTICLE CANDIDATES FOR GPT SELECTION ({len(top_50_news)} total):")
        logger.info("=" * 65)
        for i, item in enumerate(top_50_news[:20], 1):
            title = item.get('title', 'No Title')
            source = item.get('source', 'Unknown')
            category = item.get('category', 'unknown')
            age_hours = 0
            try:
                published = datetime.fromisoformat(item.get("published", ""))
                age_hours = round((datetime.now() - published).total_seconds() / 3600)
            except:
                pass
            
            # Truncate title for clean display
            display_title = title[:50] + "..." if len(title) > 50 else title
            logger.info(f" {i:2d}. [{source.upper()}] {display_title} ({age_hours}h)")
        
        if len(top_50_news) > 20:
            logger.info(f"    ... and {len(top_50_news) - 20} more articles")
        logger.info("=" * 65)

        # 5. Format for GPT
        titles_for_gpt = []
        for i, item in enumerate(top_50_news):
            # Calculate age for the prompt
            age_hours = 0
            try:
                published = datetime.fromisoformat(item.get("published", ""))
                age_hours = round((datetime.now() - published).total_seconds() / 3600)
            except:
                pass # age_hours remains 0 if parsing fails

            titles_for_gpt.append({
                "id": i + 1,
                "original_id": item.get('id', i + 1),
                "title": item.get("title", "No Title"),
                "source": item.get("source", "Unknown"),
                "category": item.get("category", "general"),
                "age_hours": age_hours, # Add age here
                "full_data": item 
            })
        return titles_for_gpt

    def _get_full_content_for_selected_articles(self, selected_ids: List[int], prepared_titles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Retrieves the full news data for the IDs selected by GPT
        using the already prepared list of titles.
        """
        selected_articles = []
        for item in prepared_titles:
            if item["id"] in selected_ids:
                selected_articles.append(item["full_data"])
        
        return selected_articles

    def _parse_script_segments(self, radio_script_text: str) -> List[Dict[str, Any]]:
        """Parse radio script into segments for audio generation"""
        try:
            # Split script into logical segments based on speaker changes or natural breaks
            segments = []
            
            # Simple parser - split by double newlines and identify speakers
            paragraphs = [p.strip() for p in radio_script_text.split('\n\n') if p.strip()]
            
            current_segment = {
                "speaker": "Marcel",  # Default speaker
                "text": "",
                "type": "intro"
            }
            
            for i, paragraph in enumerate(paragraphs):
                # Detect speaker changes (look for names at start of paragraph)
                speakers = ["Marcel", "Jarvis", "Lucy", "Brad"]
                found_speaker = None
                
                for speaker in speakers:
                    if paragraph.lower().startswith(speaker.lower() + ":") or paragraph.lower().startswith(speaker.lower() + " "):
                        found_speaker = speaker
                        # Remove speaker name from text
                        paragraph = paragraph[len(speaker):].lstrip(": ").strip()
                        break
                
                # If new speaker or significant break, start new segment
                if found_speaker and found_speaker != current_segment["speaker"]:
                    if current_segment["text"]:
                        segments.append(current_segment.copy())
                    
                    current_segment = {
                        "speaker": found_speaker,
                        "text": paragraph,
                        "type": "content" if i > 0 and i < len(paragraphs) - 1 else ("intro" if i == 0 else "outro")
                    }
                else:
                    # Continue current segment
                    if current_segment["text"]:
                        current_segment["text"] += " " + paragraph
                    else:
                        current_segment["text"] = paragraph
                        
                    # Update speaker if found one
                    if found_speaker:
                        current_segment["speaker"] = found_speaker
            
            # Add final segment
            if current_segment["text"]:
                segments.append(current_segment)
            
            # If no segments created, create a single segment with all text
            if not segments:
                segments = [{
                    "speaker": "Marcel",
                    "text": radio_script_text,
                    "type": "content"
                }]
            
            logger.debug(f"📝 Parsed {len(segments)} script segments")
            return segments
            
        except Exception as e:
            logger.error(f"❌ Script parsing failed: {e}")
            # Fallback: return entire script as single segment
            return [{
                "speaker": "Marcel",
                "text": radio_script_text,
                "type": "content"
            }]

 