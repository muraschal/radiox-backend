#!/usr/bin/env python3

"""
Content Processing Service - GPT POWERED
========================================

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
from datetime import datetime
from typing import Dict, Any, List, Optional
from loguru import logger
import openai

from config.settings import get_settings

# Import Show Service für Show-Konfiguration
from .show_service import ShowService, get_show_for_generation


class ContentProcessingService:
    """
    EINFACHER Service für GPT-basierte Content-Verarbeitung
    
    KEINE lokale Intelligenz mehr!
    ALLE Entscheidungen an GPT delegiert!
    """
    
    def __init__(self):
        # OpenAI Client
        settings = get_settings()
        self.openai_client = openai.AsyncOpenAI(
            api_key=settings.openai_api_key
        )
        
        # Show Service für Show-Konfigurationen
        self.show_service = ShowService()
        
        logger.info("🔄 Content Processing Service initialized (GPT-POWERED)")
    
    async def process_content(
        self,
        raw_data: Dict[str, Any],
        target_news_count: int = 4,
        target_time: Optional[str] = None,
        preset_name: Optional[str] = None,
        show_config: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        HAUPTFUNKTION: Erstellt komplette Radioshow mit GPT
        
        Args:
            raw_data: Rohdaten von der Datensammlung
            target_news_count: Gewünschte Anzahl News
            target_time: Zielzeit für Optimierung
            preset_name: Show Preset für Fokus-Bestimmung
            show_config: Show-Konfiguration (optional)
            
        Returns:
            Dict mit GPT-generierter Radioshow
        """
        
        logger.info("🤖 Erstelle Radioshow mit GPT...")
        
        try:
            # 1. Show-Konfiguration laden falls nicht übergeben
            if not show_config:
                show_config = await self.get_show_configuration(preset_name or "zurich")
            
            # 2. Daten für GPT vorbereiten
            prepared_data = self._prepare_data_for_gpt(raw_data, show_config, target_news_count, target_time)
            
            # 3. GPT-Prompt erstellen
            prompt = self._create_radio_show_prompt(prepared_data)
            
            # 4. GPT aufrufen
            radio_show = await self._generate_radio_show_with_gpt(prompt)
            
            # 5. Ergebnis formatieren
            result = {
                "success": True,
                "radio_show": radio_show,
                "selected_news": radio_show.get("selected_news", []),
                "weather_data": raw_data.get("weather"),
                "crypto_data": raw_data.get("crypto"),
                "content_focus": radio_show.get("content_focus", {}),
                "quality_score": radio_show.get("quality_score", 0.8),
                "target_time": target_time,
                "preset_name": preset_name,
                "show_config": show_config,
                "processing_timestamp": datetime.now().isoformat(),
                "generated_by": "GPT-4"
            }
            
            logger.info(f"✅ Radioshow erstellt: {len(radio_show.get('selected_news', []))} News")
            return result
            
        except Exception as e:
            logger.error(f"❌ GPT Content Processing Fehler: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def get_show_configuration(self, preset_name: str) -> Dict[str, Any]:
        """
        Lädt Show-Konfiguration über den integrierten Show Service
        
        Args:
            preset_name: Show Preset (zurich, crypto, tech, etc.)
            
        Returns:
            Dict mit vollständiger Show-Konfiguration
        """
        
        logger.info(f"🎭 Lade Show-Konfiguration für: {preset_name}")
        
        try:
            # Verwende die get_show_for_generation Funktion
            show_config = await get_show_for_generation(preset_name)
            
            if not show_config:
                logger.error(f"❌ Show-Konfiguration für '{preset_name}' nicht gefunden")
                return None
            
            logger.info(f"✅ Show-Konfiguration geladen: {show_config['show']['display_name']}")
            return show_config
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden der Show-Konfiguration: {e}")
            return None
    
    async def test_processing(self) -> bool:
        """Testet die GPT-basierte Content-Processing-Funktionalität"""
        
        # Test mit Dummy-Daten
        test_data = {
            "news": [
            {
                "title": "Test News Zürich",
                    "summary": "Eine Test-Nachricht über Zürich für die GPT-Verarbeitung.",
                "source": "test",
                    "published": datetime.now().isoformat()
                }
            ],
            "weather": {"temperature": 15, "condition": "sunny"},
            "crypto": {"bitcoin": 105000, "change": "+2%"}
        }
        
        try:
            result = await self.process_content(test_data, target_news_count=1)
            return result.get("success", False) and len(result.get("selected_news", [])) > 0
        except Exception as e:
            logger.error(f"GPT Content Processing Test Fehler: {e}")
            return False
    
    # ==================== PRIVATE GPT METHODS ====================
    
    def _prepare_data_for_gpt(
        self, 
        raw_data: Dict[str, Any], 
        show_config: Dict[str, Any],
        target_news_count: int,
        target_time: Optional[str]
    ) -> Dict[str, Any]:
        """Bereitet ALLE Daten für GPT auf - KEINE lokale Filterung!"""
        
        # News aus verschiedenen möglichen Formaten extrahieren
        news_articles = []
        if "news" in raw_data:
            news_articles = raw_data["news"]
        elif "sources" in raw_data and "rss" in raw_data["sources"]:
            news_articles = raw_data["sources"]["rss"].get("items", [])
        
        # EINFACHE FILTERUNG: Nur erste 10 News für Token-Limit
        # GPT-4 hat 8192 Token Limit, Input + Output muss < 8192 sein
        if len(news_articles) > 10:
            news_articles = news_articles[:10]
            logger.info(f"🔧 News auf 10 reduziert für GPT Token-Limit")
        
        # Kürze auch die Summaries um Token zu sparen
        for article in news_articles:
            if "summary" in article and len(article["summary"]) > 150:
                article["summary"] = article["summary"][:150] + "..."
        
        # Weather Daten
        weather_data = raw_data.get("weather") or raw_data.get("sources", {}).get("weather")
        
        # Crypto Daten  
        crypto_data = raw_data.get("crypto") or raw_data.get("sources", {}).get("bitcoin")
        
        prepared = {
            "news_articles": news_articles,  # ALLE News - keine Filterung!
            "weather": weather_data,
            "crypto": crypto_data,
            "target_news_count": target_news_count,
            "target_time": target_time,
            "current_time": datetime.now().strftime("%H:%M"),
            "current_date": datetime.now().strftime("%Y-%m-%d")
        }
        
        # Show-Konfiguration hinzufügen falls verfügbar
        if show_config:
            # Flexible Sprecher-Konfiguration (Solo oder Duo)
            speakers_info = {
                "primary": show_config["speakers"]["primary"]["voice_name"],
                "is_duo_show": show_config["show"]["is_duo_show"],
                "speaker_count": show_config["show"]["speaker_count"]
            }
            
            # Füge Secondary Sprecher hinzu falls vorhanden
            if show_config["speakers"]["secondary"]:
                speakers_info["secondary"] = show_config["speakers"]["secondary"]["voice_name"]
                speakers_info["speaker_configuration"] = show_config["speakers"]["configuration"]
            
            prepared["show_configuration"] = {
                "name": show_config["show"]["display_name"],
                "description": show_config["show"]["description"],
                "speaker": show_config["speaker"]["voice_name"],  # Backward compatibility
                "speakers": speakers_info,  # Neue flexible Sprecher-Info
                "city_focus": show_config["show"]["city_focus"],
                "categories": show_config["content"]["categories"],
                "exclude_categories": show_config["content"]["exclude_categories"],
                "min_priority": show_config["content"]["min_priority"],
                "language": show_config["settings"]["language"],
                "show_behavior": show_config["show"].get("show_behavior", {})
            }
        
        logger.info(f"📊 Daten für GPT vorbereitet: {len(news_articles)} News, Show: {show_config['show']['display_name'] if show_config else 'Default'}")
        
        return prepared
    
    def _create_radio_show_prompt(self, prepared_data: Dict[str, Any]) -> str:
        """Erstellt den GPT-Prompt für Radioshow-Generierung"""
        
        show_config = prepared_data.get("show_configuration", {})
        news_count = len(prepared_data.get("news_articles", []))
        
        # Dynamische Sprecher-Konfiguration
        speakers_info = show_config.get('speakers', {})
        is_duo_show = speakers_info.get('is_duo_show', False)
        primary_speaker = speakers_info.get('primary', 'Host')
        secondary_speaker = speakers_info.get('secondary', None)
        
        if is_duo_show and secondary_speaker:
            show_format = f"DIALOG zwischen {primary_speaker} und {secondary_speaker}"
            characters_section = f"""CHARAKTERE:
- {primary_speaker.upper()}: Enthusiastisch, leidenschaftlich, spontan, menschlich
- {secondary_speaker.upper()}: Analytisch, wittig, sarkastisch, AI-Assistent"""
            script_format = f"Format: \"{primary_speaker.upper()}: [Text]\" und \"{secondary_speaker.upper()}: [Text]\""
            script_example = f"""{primary_speaker.upper()}: Welcome to RadioX! I'm {primary_speaker}, and this is our evening news update.
{secondary_speaker.upper()}: Good evening, {primary_speaker}. I've analyzed today's top stories, and we have some fascinating developments.
{primary_speaker.upper()}: Fantastic! What's caught your attention today?
{secondary_speaker.upper()}: Well, let's start with the most significant story..."""
        else:
            show_format = f"SOLO-SHOW mit {primary_speaker}"
            characters_section = f"""CHARAKTER:
- {primary_speaker.upper()}: Professioneller Moderator, informativ, engagiert, direkt zum Publikum sprechend"""
            script_format = f"Format: \"{primary_speaker.upper()}: [Text]\""
            script_example = f"""{primary_speaker.upper()}: Welcome to RadioX! I'm {primary_speaker} with your evening news update.
{primary_speaker.upper()}: Today we have some fascinating developments to discuss.
{primary_speaker.upper()}: Let's start with our top story..."""

        prompt = f"""Du bist ein professioneller Radio-Produzent und erstellst eine komplette Radioshow als {show_format}.

SHOW KONFIGURATION:
- Show Name: {show_config.get('name', 'RadioX')}
- Beschreibung: {show_config.get('description', 'Allgemeine Radioshow')}
- Format: {show_format}
- Stadt-Fokus: {show_config.get('city_focus', 'Global')}
- Bevorzugte Kategorien: {', '.join(show_config.get('categories', []))}
- Ausgeschlossene Kategorien: {', '.join(show_config.get('exclude_categories', []))}
- Sprache: {show_config.get('language', 'English')}

{characters_section}

VERFÜGBARE DATEN:
- News Artikel: {news_count} verfügbar
- Wetter: {prepared_data.get('weather', 'Nicht verfügbar')}
- Crypto: {prepared_data.get('crypto', 'Nicht verfügbar')}
- Zielzeit: {prepared_data.get('target_time', 'Aktuell')}
- Aktuelle Zeit: {prepared_data.get('current_time')}

NEWS ARTIKEL:
{json.dumps(prepared_data.get('news_articles', []), indent=2, ensure_ascii=False)}

AUFGABE:
Erstelle eine komplette Radioshow mit folgenden Elementen:

1. NEWS SELEKTION:
   - Wähle die {prepared_data.get('target_news_count', 4)} besten News
   - Berücksichtige Show-Fokus und Kategorien
   - Erkläre warum du diese News gewählt hast
   - Sortiere nach Wichtigkeit/Relevanz

2. CONTENT FOKUS:
   - Bestimme den Hauptfokus der Show
   - Bewerte die Confidence (0.0-1.0)
   - Erkläre die Fokus-Entscheidung

3. QUALITÄTSBEWERTUNG:
   - Bewerte die Gesamtqualität der Show (0.0-1.0)
   - Berücksichtige News-Qualität, Relevanz, Diversität

4. KOMPLETTES RADIO-SCRIPT:
   - Erstelle ein VOLLSTÄNDIGES {"DIALOG" if is_duo_show else "MONOLOG"}-Script
   - {script_format}
   - Integriere ALLE ausgewählten News in natürlichem {"Dialog" if is_duo_show else "Monolog"}
   - Füge Wetter- und Crypto-Segmente ein
   - Verwende natürliche Übergänge zwischen den Themen
   - Script soll 3-5 Minuten Sprechzeit haben (750-900 Wörter)
   - {"Erstelle lebendige Diskussionen zwischen den beiden Charakteren" if is_duo_show else "Spreche direkt und engagiert zum Publikum"}
   - Sprache: {show_config.get('language', 'English')}
   - WICHTIG: Jede Zeile muss mit "{primary_speaker.upper()}:" {"oder \"" + secondary_speaker.upper() + ":\"" if is_duo_show else ""} beginnen

ANTWORT FORMAT (JSON):
{{
  "selected_news": [
    {{
      "title": "News Titel",
      "summary": "News Zusammenfassung", 
      "source": "Quelle",
      "category": "Kategorie",
      "relevance_score": 0.9,
      "selection_reason": "Warum diese News gewählt wurde"
    }}
  ],
  "content_focus": {{
    "focus": "local/politics/economy/tech/crypto/etc",
    "confidence": 0.8,
    "explanation": "Warum dieser Fokus"
  }},
  "quality_score": 0.85,
  "weather_segment": "Wetter-Segment Text",
  "crypto_segment": "Crypto-Segment Text",
  "complete_radio_script": "{script_example.replace(chr(10), '\\n')}",
  "show_script": {{
    "intro": "Show Intro Text",
    "transitions": ["Übergang 1", "Übergang 2"],
    "outro": "Show Outro Text"
  }},
  "metadata": {{
    "total_news_analyzed": {news_count},
    "show_length_estimate": "3-5 Minuten",
    "target_audience": "Show Zielgruppe",
    "script_word_count": "Anzahl Wörter im Script"
  }}
}}

WICHTIG: Das 'complete_radio_script' Feld muss ein vollständiges {"DIALOG" if is_duo_show else "MONOLOG"}-Script enthalten!

BEISPIEL FORMAT:
{script_example}

Erstelle jetzt die perfekte {"Dialog-" if is_duo_show else ""}Radioshow!"""

        return prompt
    
    async def _generate_radio_show_with_gpt(self, prompt: str) -> Dict[str, Any]:
        """Ruft GPT auf und generiert die Radioshow"""
        
        logger.info("🤖 Sende Anfrage an GPT-4...")
        
        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system", 
                        "content": "Du bist ein professioneller Radio-Produzent. Antworte immer im JSON-Format."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            # JSON Response parsen
            radio_show = json.loads(response.choices[0].message.content)
            
            logger.info("✅ GPT-4 Radioshow erfolgreich generiert")
            return radio_show
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ GPT Response JSON Parse Fehler: {e}")
            raise Exception(f"GPT Response konnte nicht geparst werden: {e}")
                
        except Exception as e:
            logger.error(f"❌ GPT API Fehler: {e}")
            raise Exception(f"GPT API Aufruf fehlgeschlagen: {e}") 

    def _get_bitcoin_price_instructions(self, show_behavior: Dict[str, Any], crypto_data: Dict[str, Any]) -> str:
        """Erstellt spezielle Bitcoin-Preis-Instruktionen für Jarvis"""
        
        intro_behavior = show_behavior.get("intro_behavior", {})
        
        if intro_behavior.get("jarvis_bitcoin_price_first", False):
            instructions = "🚨 WICHTIGE JARVIS BITCOIN-PREIS-INSTRUKTION:\n"
            instructions += "- Jarvis MUSS als allererstes den aktuellen Bitcoin-Preis nennen\n"
            instructions += "- Verwende einen dramatischen, aufregenden Ton\n"
            instructions += "- Format: 'Bitcoin steht aktuell bei [PREIS] - [TREND-KOMMENTAR]'\n"
            
            if crypto_data:
                price = crypto_data.get('price', 'N/A')
                change = crypto_data.get('change_24h', 'N/A')
                instructions += f"- Aktueller Preis: {price}\n"
                instructions += f"- 24h Änderung: {change}\n"
                
                # Trend-Kontext
                if intro_behavior.get("price_context") == "always_include_trend":
                    instructions += "- IMMER Trend-Kontext hinzufügen (Bullish/Bearish/Seitwärts)\n"
                    instructions += "- Kurze Marktanalyse einbauen\n"
            
            instructions += "- Dann erst mit der normalen Show fortfahren\n"
            return instructions
        
        return "Kein spezielles Bitcoin-Preis-Feature aktiviert" 