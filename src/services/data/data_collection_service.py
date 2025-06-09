#!/usr/bin/env python3

"""
Data Collection Service - DUMM UND EINFACH
==========================================

Sammelt wertefrei ALLE verfügbaren Daten:
- RSS: ALLE aktiven Feeds
- Weather: Standard Location
- Bitcoin: Aktueller Preis

Keine Intelligenz, keine Presets, keine Filterung!
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from loguru import logger
import os

from .rss_service import RSSService
from .weather_service import WeatherService
from .bitcoin_service import BitcoinService


class DataCollectionService:
    """
    DUMMER Data Collection Service
    
    Sammelt einfach ALLE verfügbaren Daten ohne Bewertung:
    - RSS: get_all_recent_news()
    - Weather: get_current_weather()
    - Bitcoin: get_bitcoin_price()
    """
    
    def __init__(self):
        self.rss_service = RSSService()
        self.weather_service = WeatherService()
        self.crypto_service = BitcoinService()
    
    async def collect_all_data(self) -> Dict[str, Any]:
        """
        Sammelt ALLE verfügbaren Daten von allen Services
        Generiert automatisch HTML-Dashboards
        """
        
        logger.info("🚀 Starte vollständige Datensammlung...")
        
        # SEQUENZIELLE Sammlung um Race Conditions zu vermeiden
        logger.info("📰 Sammle News...")
        news = await self._collect_all_news_safe()
        
        # Parallele Sammlung für Weather + Crypto (diese haben keine Konflikte)
        logger.info("🌍 Sammle Kontext-Daten parallel...")
        weather_task = self._collect_weather_safe()
        crypto_task = self._collect_crypto_safe()
        
        weather, crypto = await asyncio.gather(
            weather_task, crypto_task,
            return_exceptions=True
        )
        
        # Ergebnisse zusammenfassen
        result = {
            "collection_timestamp": datetime.now().isoformat(),
            "news": news if not isinstance(news, Exception) else [],
            "weather": weather if not isinstance(weather, Exception) else None,
            "crypto": crypto if not isinstance(crypto, Exception) else None,
            "success": True,
            "errors": []
        }
        
        # Fehler sammeln
        if isinstance(news, Exception):
            result["errors"].append(f"News: {str(news)}")
        if isinstance(weather, Exception):
            result["errors"].append(f"Weather: {str(weather)}")
        if isinstance(crypto, Exception):
            result["errors"].append(f"Crypto: {str(crypto)}")
        
        # Statistiken
        news_count = len(result["news"]) if result["news"] else 0
        logger.info(f"✅ Datensammlung abgeschlossen: {news_count} News, Wetter: {'✓' if result['weather'] else '✗'}, Bitcoin: {'✓' if result['crypto'] else '✗'}")
        
        # 🎨 HTML-Dashboards deaktiviert - nur Tailwind Dashboard wird benötigt
        # try:
        #     await self.generate_html_dashboards(result)
        #     logger.info("🎨 HTML-Dashboards automatisch generiert!")
        # except Exception as e:
        #     logger.error(f"⚠️ HTML-Dashboard-Generierung fehlgeschlagen: {e}")
        #     result["errors"].append(f"HTML-Dashboards: {str(e)}")
        
        return result
    
    async def collect_news_only(self) -> Dict[str, Any]:
        """
        Sammelt nur RSS News - ALLE verfügbaren
        """
        
        logger.info("📰 Sammle ALLE RSS News...")
        
        news = await self._collect_all_news_safe()
        
        return {
            "news": news,
            "collection_timestamp": datetime.now().isoformat(),
            "news_count": len(news) if news else 0
        }
    
    async def collect_context_data(self) -> Dict[str, Any]:
        """Sammelt nur Kontext-Daten (ALLE Weather + Crypto)"""
        
        logger.info("🌍 Sammle ALLE Kontext-Daten...")
        
        # Parallele Sammlung
        weather_task = self._collect_weather_safe()
        crypto_task = self._collect_crypto_safe()
        
        weather, crypto = await asyncio.gather(
            weather_task, crypto_task, return_exceptions=True
        )
        
        return {
            "weather": weather if not isinstance(weather, Exception) else None,
            "crypto": crypto if not isinstance(crypto, Exception) else None,
            "collection_timestamp": datetime.now().isoformat()
        }
    
    async def test_connections(self) -> Dict[str, bool]:
        """Testet alle Datenquellen-Verbindungen"""
        
        logger.info("🔧 Teste alle Datenquellen...")
        
        results = {}
        
        # Test RSS Feeds
        try:
            test_feeds = await self.rss_service.get_all_active_feeds()
            results["rss_service"] = len(test_feeds) > 0
        except Exception as e:
            logger.error(f"RSS Test Fehler: {e}")
            results["rss_service"] = False
        
        # Test Weather Service
        try:
            weather = await self.weather_service.get_complete_weather("zurich")  # ⭐ NEU: Mit Forecast!
            results["weather_service"] = weather is not None
        except Exception as e:
            logger.error(f"Weather Test Fehler: {e}")
            results["weather_service"] = False
        
        # Test Crypto Service
        try:
            crypto = await self.crypto_service.get_bitcoin_price()
            results["crypto_service"] = crypto is not None
        except Exception as e:
            logger.error(f"Crypto Test Fehler: {e}")
            results["crypto_service"] = False
        
        logger.info(f"🔧 Verbindungstests abgeschlossen: {results}")
        return results
    
    async def generate_html_dashboards(self, data: Dict[str, Any]) -> bool:
        """
        Generiert automatisch beide HTML-Dashboards:
        1. RSS Dashboard (rss.html)
        2. Data Collection Dashboard (data_collection.html)
        3. Comprehensive Dashboard (radiox_complete.html) - ALL-IN-ONE
        """
        
        logger.info("🎨 Generiere HTML-Dashboards...")
        
        try:
            # Pfad zum outplay Ordner
            outplay_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..", "outplay")
            os.makedirs(outplay_dir, exist_ok=True)
            
            # 1. RSS Dashboard generieren
            await self._generate_rss_dashboard(data, outplay_dir)
            
            # 2. Data Collection Dashboard generieren  
            await self._generate_data_collection_dashboard(data, outplay_dir)
            
            # 3. **NEW: Comprehensive ALL-IN-ONE Dashboard**
            await self._generate_comprehensive_dashboard(data, outplay_dir)
            
            # 4. JSON-Daten für JavaScript speichern
            await self._save_json_data(data, outplay_dir)
            
            logger.info("✅ HTML-Dashboards erfolgreich generiert")
            return True
            
        except Exception as e:
            logger.error(f"❌ Fehler bei HTML-Dashboard-Generierung: {e}")
            return False
    
    async def _generate_rss_dashboard(self, data: Dict[str, Any], outplay_dir: str):
        """Generiert das RSS-spezifische Dashboard"""
        
        news = data.get('news', [])
        
        # RSS-spezifische Statistiken
        sources = {}
        categories = {}
        total_articles = len(news)
        
        for item in news:
            source = item.get('source', 'unknown')
            category = item.get('category', 'general')
            
            sources[source] = sources.get(source, 0) + 1
            categories[category] = categories.get(category, 0) + 1
        
        # RSS HTML Template
        rss_html = f"""<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>📰 RadioX RSS Dashboard</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh; padding: 20px; color: #2c3e50;
        }}
        .container {{ max-width: 1400px; margin: 0 auto; background: rgba(255,255,255,0.95); border-radius: 20px; box-shadow: 0 20px 40px rgba(0,0,0,0.1); overflow: hidden; }}
        .header {{ background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%); color: white; padding: 30px; text-align: center; }}
        .header h1 {{ font-size: 2.5em; margin-bottom: 10px; text-shadow: 2px 2px 4px rgba(0,0,0,0.3); }}
        .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; padding: 30px; background: #f8f9fa; }}
        .stat-card {{ background: white; padding: 25px; border-radius: 15px; box-shadow: 0 5px 15px rgba(0,0,0,0.1); text-align: center; }}
        .stat-card .icon {{ font-size: 3em; margin-bottom: 15px; }}
        .stat-card .number {{ font-size: 2.5em; font-weight: bold; color: #2c3e50; margin-bottom: 10px; }}
        .stat-card .label {{ font-size: 1.1em; color: #7f8c8d; text-transform: uppercase; letter-spacing: 1px; }}
        .content {{ padding: 30px; }}
        .section {{ background: white; border-radius: 15px; box-shadow: 0 5px 15px rgba(0,0,0,0.1); margin-bottom: 30px; overflow: hidden; }}
        .section-header {{ background: linear-gradient(135deg, #3498db 0%, #2980b9 100%); color: white; padding: 20px; font-size: 1.5em; font-weight: bold; }}
        .news-table {{ width: 100%; border-collapse: collapse; }}
        .news-table th {{ background: #34495e; color: white; padding: 15px; text-align: left; font-weight: 600; }}
        .news-table td {{ padding: 15px; border-bottom: 1px solid #ecf0f1; vertical-align: top; }}
        .news-table tr:hover {{ background: #f8f9fa; }}
        .source-badge {{ padding: 4px 12px; border-radius: 12px; font-weight: bold; text-transform: uppercase; font-size: 0.8em; color: white; }}
        .source-nzz {{ background: #e74c3c; }}
        .source-20min {{ background: #f39c12; }}
        .source-srf {{ background: #27ae60; }}
        .source-tagesanzeiger {{ background: #8e44ad; }}
        .source-cash {{ background: #2ecc71; }}
        .source-heise {{ background: #34495e; }}
        .source-cointelegraph {{ background: #f1c40f; color: black; }}
        .source-techcrunch {{ background: #1abc9c; }}
        .source-theverge {{ background: #9b59b6; }}
        .source-rt {{ background: #e67e22; }}
        .source-bbc {{ background: #c0392b; }}
        .news-link {{ color: #3498db; text-decoration: none; font-weight: bold; }}
        .news-link:hover {{ color: #2980b9; }}
        .timestamp {{ text-align: center; padding: 20px; background: #ecf0f1; color: #7f8c8d; font-style: italic; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📰 RadioX RSS Dashboard</h1>
            <div style="font-size: 1.2em; opacity: 0.9;">Alle RSS-Feeds im Überblick</div>
        </div>

        <div class="stats-grid">
            <div class="stat-card">
                <div class="icon">📰</div>
                <div class="number">{total_articles}</div>
                <div class="label">Artikel Total</div>
            </div>
            <div class="stat-card">
                <div class="icon">📡</div>
                <div class="number">{len(sources)}</div>
                <div class="label">Aktive Quellen</div>
            </div>
            <div class="stat-card">
                <div class="icon">🏷️</div>
                <div class="number">{len(categories)}</div>
                <div class="label">Kategorien</div>
            </div>
        </div>

        <div class="content">
            <div class="section">
                <div class="section-header">📊 Quellen-Verteilung</div>
                <div style="padding: 20px;">
                    {self._generate_source_stats_html(sources)}
                </div>
            </div>

            <div class="section">
                <div class="section-header">📰 Alle RSS-Artikel</div>
                <table class="news-table">
                    <thead>
                        <tr>
                            <th>Quelle</th>
                            <th>Kategorie</th>
                            <th>Titel</th>
                            <th>Zusammenfassung</th>
                            <th>Alter</th>
                            <th>Link</th>
                        </tr>
                    </thead>
                    <tbody>
                        {self._generate_news_table_html(news)}
                    </tbody>
                </table>
            </div>
        </div>

        <div class="timestamp">
            RSS-Dashboard generiert am: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}
        </div>
    </div>
</body>
</html>"""
        
        # RSS HTML speichern
        rss_path = os.path.join(outplay_dir, "rss.html")
        with open(rss_path, 'w', encoding='utf-8') as f:
            f.write(rss_html)
        
        logger.info("✅ RSS Dashboard (rss.html) generiert")
    
    async def _generate_data_collection_dashboard(self, data: Dict[str, Any], outplay_dir: str):
        """Generiert das Data Collection Dashboard mit eingebetteten Daten"""
        
        import json
        
        # JSON-Daten direkt in JavaScript einbetten
        json_data = json.dumps(data, indent=2, ensure_ascii=False, default=str)
        
        # Data Collection HTML Template mit eingebetteten Daten
        data_collection_html = f"""<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RadioX Data Collection Dashboard</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; padding: 20px; }}
        .container {{ max-width: 1400px; margin: 0 auto; background: rgba(255, 255, 255, 0.95); border-radius: 20px; box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1); overflow: hidden; }}
        .header {{ background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%); color: white; padding: 30px; text-align: center; }}
        .header h1 {{ font-size: 2.5em; margin-bottom: 10px; text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3); }}
        .header .subtitle {{ font-size: 1.2em; opacity: 0.9; }}
        .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; padding: 30px; background: #f8f9fa; }}
        .stat-card {{ background: white; padding: 25px; border-radius: 15px; box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1); text-align: center; transition: transform 0.3s ease; }}
        .stat-card:hover {{ transform: translateY(-5px); }}
        .stat-card .icon {{ font-size: 3em; margin-bottom: 15px; }}
        .stat-card .number {{ font-size: 2.5em; font-weight: bold; color: #2c3e50; margin-bottom: 10px; }}
        .stat-card .label {{ font-size: 1.1em; color: #7f8c8d; text-transform: uppercase; letter-spacing: 1px; }}
        .content-grid {{ display: grid; grid-template-columns: 2fr 1fr; gap: 30px; padding: 30px; }}
        .news-section {{ background: white; border-radius: 15px; box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1); overflow: hidden; }}
        .section-header {{ background: linear-gradient(135deg, #3498db 0%, #2980b9 100%); color: white; padding: 20px; font-size: 1.5em; font-weight: bold; }}
        .news-filters {{ padding: 20px; background: #ecf0f1; border-bottom: 1px solid #bdc3c7; }}
        .filter-buttons {{ display: flex; flex-wrap: wrap; gap: 10px; }}
        .filter-btn {{ padding: 8px 16px; border: none; border-radius: 20px; background: #95a5a6; color: white; cursor: pointer; transition: all 0.3s ease; font-size: 0.9em; }}
        .filter-btn.active {{ background: #3498db; transform: scale(1.05); }}
        .filter-btn:hover {{ background: #2980b9; }}
        .news-list {{ max-height: 800px; overflow-y: auto; }}
        .news-item {{ padding: 20px; border-bottom: 1px solid #ecf0f1; transition: background-color 0.3s ease; }}
        .news-item:hover {{ background-color: #f8f9fa; }}
        .news-item:last-child {{ border-bottom: none; }}
        .news-meta {{ display: flex; align-items: center; gap: 15px; margin-bottom: 10px; font-size: 0.9em; }}
        .source-badge {{ padding: 4px 12px; border-radius: 12px; font-weight: bold; text-transform: uppercase; font-size: 0.8em; }}
        .source-nzz {{ background: #e74c3c; color: white; }}
        .source-20min {{ background: #f39c12; color: white; }}
        .source-srf {{ background: #27ae60; color: white; }}
        .source-tagesanzeiger {{ background: #8e44ad; color: white; }}
        .source-cash {{ background: #2ecc71; color: white; }}
        .source-heise {{ background: #34495e; color: white; }}
        .source-cointelegraph {{ background: #f1c40f; color: black; }}
        .source-techcrunch {{ background: #1abc9c; color: white; }}
        .source-theverge {{ background: #9b59b6; color: white; }}
        .source-rt {{ background: #e67e22; color: white; }}
        .source-bbc {{ background: #c0392b; color: white; }}
        .category-badge {{ padding: 4px 12px; border-radius: 12px; background: #ecf0f1; color: #2c3e50; font-size: 0.8em; }}
        .priority-badge {{ padding: 4px 8px; border-radius: 8px; font-weight: bold; font-size: 0.8em; }}
        .priority-10 {{ background: #e74c3c; color: white; }}
        .priority-9 {{ background: #f39c12; color: white; }}
        .priority-8 {{ background: #f1c40f; color: black; }}
        .priority-7 {{ background: #2ecc71; color: white; }}
        .priority-6 {{ background: #3498db; color: white; }}
        .priority-5 {{ background: #95a5a6; color: white; }}
        .age-badge {{ padding: 4px 8px; border-radius: 8px; background: #bdc3c7; color: #2c3e50; font-size: 0.8em; }}
        .news-title {{ font-size: 1.2em; font-weight: bold; color: #2c3e50; margin-bottom: 8px; line-height: 1.4; }}
        .news-summary {{ color: #7f8c8d; line-height: 1.5; margin-bottom: 10px; }}
        .news-summary img {{ max-width: 120px; max-height: 80px; object-fit: cover; border-radius: 8px; margin-right: 10px; margin-bottom: 5px; }}
        .news-link {{ display: inline-flex; align-items: center; gap: 8px; color: #3498db; text-decoration: none; font-weight: bold; transition: color 0.3s ease; }}
        .news-link:hover {{ color: #2980b9; }}
        .sidebar {{ display: flex; flex-direction: column; gap: 20px; }}
        .context-card {{ background: white; border-radius: 15px; box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1); overflow: hidden; }}
        .weather-card .section-header {{ background: linear-gradient(135deg, #f39c12 0%, #e67e22 100%); }}
        .crypto-card .section-header {{ background: linear-gradient(135deg, #f1c40f 0%, #f39c12 100%); color: #2c3e50; }}
        .card-content {{ padding: 25px; text-align: center; }}
        .weather-temp {{ font-size: 3em; font-weight: bold; color: #f39c12; margin-bottom: 10px; }}
        .weather-desc {{ font-size: 1.2em; color: #7f8c8d; margin-bottom: 15px; }}
        .weather-location {{ font-size: 1em; color: #95a5a6; }}
        .crypto-price {{ font-size: 2.5em; font-weight: bold; color: #f1c40f; margin-bottom: 10px; }}
        .crypto-change {{ font-size: 1.3em; font-weight: bold; margin-bottom: 15px; }}
        .crypto-change.positive {{ color: #27ae60; }}
        .crypto-change.negative {{ color: #e74c3c; }}
        .crypto-trend {{ font-size: 1em; color: #7f8c8d; background: #ecf0f1; padding: 10px; border-radius: 8px; }}
        .timestamp {{ text-align: center; padding: 20px; background: #ecf0f1; color: #7f8c8d; font-style: italic; }}
        @media (max-width: 768px) {{ .content-grid {{ grid-template-columns: 1fr; }} .stats-grid {{ grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); }} .filter-buttons {{ justify-content: center; }} }}
        .hidden {{ display: none !important; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 RadioX Data Collection Dashboard</h1>
            <div class="subtitle">Alle gesammelten Daten vor GPT-Priorisierung</div>
        </div>
        <div class="stats-grid">
            <div class="stat-card"><div class="icon">📰</div><div class="number" id="total-news">0</div><div class="label">News Artikel</div></div>
            <div class="stat-card"><div class="icon">🔗</div><div class="number" id="total-links">0</div><div class="label">Mit URLs</div></div>
            <div class="stat-card"><div class="icon">📡</div><div class="number" id="total-sources">0</div><div class="label">Quellen</div></div>
            <div class="stat-card"><div class="icon">🏷️</div><div class="number" id="total-categories">0</div><div class="label">Kategorien</div></div>
        </div>
        <div class="content-grid">
            <div class="news-section">
                <div class="section-header">📰 News Artikel (für GPT-Priorisierung)</div>
                <div class="news-filters">
                    <div class="filter-buttons">
                        <button class="filter-btn active" data-filter="all">Alle</button>
                        <button class="filter-btn" data-filter="zurich">Zürich</button>
                        <button class="filter-btn" data-filter="news">News</button>
                        <button class="filter-btn" data-filter="wirtschaft">Wirtschaft</button>
                        <button class="filter-btn" data-filter="tech">Tech</button>
                        <button class="filter-btn" data-filter="bitcoin">Bitcoin</button>
                        <button class="filter-btn" data-filter="international">International</button>
                        <button class="filter-btn" data-filter="schweiz">Schweiz</button>
                    </div>
                </div>
                <div class="news-list" id="news-list"></div>
            </div>
            <div class="sidebar">
                <div class="context-card weather-card">
                    <div class="section-header">🌤️ Wetter Kontext</div>
                    <div class="card-content" id="weather-content"></div>
                </div>
                <div class="context-card crypto-card">
                    <div class="section-header">₿ Bitcoin Kontext</div>
                    <div class="card-content" id="crypto-content"></div>
                </div>
            </div>
        </div>
        <div class="timestamp" id="timestamp"></div>
    </div>
    <script>
        // Daten direkt eingebettet (kein fetch() nötig)
        const data = {json_data};
        
        function loadData() {{
            try {{
                displayStats(data); 
                displayNews(data.news || []); 
                displayWeather(data.weather); 
                displayCrypto(data.crypto); 
                displayTimestamp(data.collection_timestamp);
            }} catch (error) {{
                console.error('Error loading data:', error);
                document.getElementById('news-list').innerHTML = '<div style="padding: 20px; text-align: center; color: #e74c3c;">Fehler beim Laden der Daten</div>';
            }}
        }}
        
        function displayStats(data) {{
            const news = data.news || []; 
            const newsWithLinks = news.filter(item => item.has_link); 
            const sources = [...new Set(news.map(item => item.source))]; 
            const categories = [...new Set(news.map(item => item.category))];
            document.getElementById('total-news').textContent = news.length; 
            document.getElementById('total-links').textContent = newsWithLinks.length; 
            document.getElementById('total-sources').textContent = sources.length; 
            document.getElementById('total-categories').textContent = categories.length;
        }}
        
        function displayNews(news) {{
            const newsList = document.getElementById('news-list');
            if (!news || news.length === 0) {{ 
                newsList.innerHTML = '<div style="padding: 20px; text-align: center;">Keine News verfügbar</div>'; 
                return; 
            }}
            newsList.innerHTML = news.map(item => `<div class="news-item" data-category="${{item.category}}" data-source="${{item.source}}"><div class="news-meta"><span class="source-badge source-${{item.source}}">${{item.source}}</span><span class="category-badge">${{item.category}}</span><span class="priority-badge priority-${{item.priority}}">P${{item.priority}}</span><span class="age-badge">${{Math.round(item.age_hours)}}h alt</span></div><div class="news-title">${{item.title}}</div><div class="news-summary">${{item.summary}}</div>${{item.has_link ? `<a href="${{item.link}}" target="_blank" class="news-link">🔗 Vollständiger Artikel (für GPT)</a>` : ''}}</div>`).join('');
            setupFilters(news);
        }}
        
        function setupFilters(news) {{
            const filterButtons = document.querySelectorAll('.filter-btn'); 
            const newsItems = document.querySelectorAll('.news-item');
            filterButtons.forEach(button => {{ 
                button.addEventListener('click', () => {{ 
                    filterButtons.forEach(btn => btn.classList.remove('active')); 
                    button.classList.add('active'); 
                    const filter = button.dataset.filter; 
                    newsItems.forEach(item => {{ 
                        if (filter === 'all' || item.dataset.category === filter || item.dataset.source === filter) {{ 
                            item.classList.remove('hidden'); 
                        }} else {{ 
                            item.classList.add('hidden'); 
                        }} 
                    }}); 
                }}); 
            }});
        }}
        
        function displayWeather(weather) {{
            const weatherContent = document.getElementById('weather-content');
            if (!weather || !weather.current) {{ 
                weatherContent.innerHTML = '<div style="color: #e74c3c;">Keine Wetterdaten verfügbar</div>'; 
                return; 
            }}
            
            const current = weather.current;
            const forecast = weather.forecast || [];
            const outlook = weather.outlook || null;
            
            let weatherHtml = `
                <div class="weather-temp">${{current.temperature}}°C</div>
                <div class="weather-desc">${{current.description}}</div>
                <div class="weather-location">📍 ${{weather.location || 'Zürich'}}</div>
                <div style="margin-top: 15px; font-size: 0.9em; color: #7f8c8d;">
                    💨 ${{current.wind_speed}}km/h | 💧 ${{current.humidity}}%
                </div>
            `;
            
            // Outlook (Tomorrow) anzeigen
            if (outlook && outlook.tomorrow) {{
                const tom = outlook.tomorrow;
                weatherHtml += `
                    <div style="margin-top: 15px; padding: 10px; background: #ecf0f1; border-radius: 8px;">
                        <div style="font-weight: bold; margin-bottom: 5px;">🌅 Morgen</div>
                        <div>${{tom.temp_min}}°C - ${{tom.temp_max}}°C</div>
                        <div style="font-size: 0.9em; color: #7f8c8d;">${{tom.description}}</div>
                        ${{tom.precipitation > 0 ? `<div style="font-size: 0.9em;">🌧️ ${{tom.precipitation}}mm</div>` : ''}}
                    </div>
                `;
            }}
            
            // 5-Tage Forecast (kompakt)
            if (forecast.length > 0) {{
                weatherHtml += `
                    <div style="margin-top: 15px; padding: 10px; background: #f8f9fa; border-radius: 8px;">
                        <div style="font-weight: bold; margin-bottom: 8px;">📅 5-Tage Forecast</div>
                        <div style="font-size: 0.8em;">
                `;
                
                forecast.slice(0, 3).forEach(day => {{
                    const date = new Date(day.date).toLocaleDateString('de-DE', {{weekday: 'short'}});
                    weatherHtml += `
                        <div style="display: flex; justify-content: space-between; margin-bottom: 3px;">
                            <span>${{date}}</span>
                            <span>${{Math.round(day.temp_min)}}°-${{Math.round(day.temp_max)}}°</span>
                        </div>
                    `;
                }});
                
                weatherHtml += `</div></div>`;
            }}
            
            weatherContent.innerHTML = weatherHtml;
        }}
        
        function displayCrypto(crypto) {{
            const cryptoContent = document.getElementById('crypto-content');
            if (!crypto || !crypto.bitcoin) {{ 
                cryptoContent.innerHTML = '<div style="color: #e74c3c;">Keine Bitcoin-Daten verfügbar</div>'; 
                return; 
            }}
            
            const bitcoin = crypto.bitcoin; 
            const trend = crypto.trend || null;
            const alerts = crypto.alerts || [];
            
            const change24h = bitcoin.change_24h || 0; 
            const changeClass = change24h >= 0 ? 'positive' : 'negative'; 
            const changeSymbol = change24h >= 0 ? '+' : '';
            
            let cryptoHtml = `
                <div class="crypto-price">$${{bitcoin.price_usd.toLocaleString()}}</div>
                <div class="crypto-change ${{changeClass}}">${{changeSymbol}}${{change24h.toFixed(1)}}% (24h)</div>
            `;
            
            // Trend-Analyse anzeigen
            if (trend && trend.message) {{
                cryptoHtml += `
                    <div style="margin: 15px 0; padding: 10px; background: #ecf0f1; border-radius: 8px; font-size: 0.9em;">
                        <div style="font-weight: bold; margin-bottom: 5px;">${{trend.emoji}} Trend</div>
                        <div>${{trend.message}}</div>
                    </div>
                `;
            }}
            
            // Alle Zeiträume anzeigen (wie im CLI)
            cryptoHtml += `
                <div style="margin-top: 15px; padding: 10px; background: #f8f9fa; border-radius: 8px;">
                    <div style="font-weight: bold; margin-bottom: 8px;">📊 Alle Zeiträume</div>
                    <div style="font-size: 0.85em; line-height: 1.4;">
                        <div>1h: ${{bitcoin.change_1h ? (bitcoin.change_1h >= 0 ? '+' : '') + bitcoin.change_1h.toFixed(2) + '%' : 'N/A'}}</div>
                        <div>24h: ${{changeSymbol}}${{change24h.toFixed(2)}}%</div>
                        <div>7d: ${{bitcoin.change_7d ? (bitcoin.change_7d >= 0 ? '+' : '') + bitcoin.change_7d.toFixed(2) + '%' : 'N/A'}}</div>
                        <div>30d: ${{bitcoin.change_30d ? (bitcoin.change_30d >= 0 ? '+' : '') + bitcoin.change_30d.toFixed(2) + '%' : 'N/A'}}</div>
                        <div>60d: ${{bitcoin.change_60d ? (bitcoin.change_60d >= 0 ? '+' : '') + bitcoin.change_60d.toFixed(2) + '%' : 'N/A'}}</div>
                        <div>90d: ${{bitcoin.change_90d ? (bitcoin.change_90d >= 0 ? '+' : '') + bitcoin.change_90d.toFixed(2) + '%' : 'N/A'}}</div>
                    </div>
                </div>
            `;
            
            // Market Cap und Volume
            if (bitcoin.market_cap) {{
                cryptoHtml += `
                    <div style="margin-top: 15px; padding: 10px; background: #fff3cd; border-radius: 8px; font-size: 0.85em;">
                        <div>💰 Market Cap: $${{(bitcoin.market_cap / 1e12).toFixed(2)}}T</div>
                        ${{bitcoin.volume_24h ? `<div>📊 24h Volume: $${{(bitcoin.volume_24h / 1e9).toFixed(1)}}B</div>` : ''}}
                    </div>
                `;
            }}
            
            // Alerts anzeigen
            if (alerts && alerts.length > 0) {{
                cryptoHtml += `
                    <div style="margin-top: 15px; padding: 10px; background: #f8d7da; border-radius: 8px; font-size: 0.85em;">
                        <div style="font-weight: bold; color: #721c24;">🚨 Alerts</div>
                        ${{alerts.map(alert => `<div>${{alert.message}}</div>`).join('')}}
                    </div>
                `;
            }}
            
            cryptoContent.innerHTML = cryptoHtml;
        }}
        
        function displayTimestamp(timestamp) {{
            const timestampElement = document.getElementById('timestamp');
            if (timestamp) {{ 
                const date = new Date(timestamp); 
                timestampElement.textContent = `Daten gesammelt am: ${{date.toLocaleString('de-DE')}}`; 
            }} else {{ 
                timestampElement.textContent = 'Zeitstempel nicht verfügbar'; 
            }}
        }}
        
        // Daten beim Laden der Seite anzeigen
        document.addEventListener('DOMContentLoaded', loadData);
    </script>
</body>
</html>"""
        
        # Data Collection HTML speichern
        data_collection_path = os.path.join(outplay_dir, "data_collection.html")
        with open(data_collection_path, 'w', encoding='utf-8') as f:
            f.write(data_collection_html)
        
        logger.info("✅ Data Collection Dashboard (data_collection.html) generiert")

    async def _generate_comprehensive_dashboard(self, data: Dict[str, Any], outplay_dir: str):
        """Generiert das comprehensive ALL-IN-ONE Dashboard mit Data Collection, GPT Input/Output und Voice-Infos"""
        
        import json
        from datetime import datetime
        
        # Extract all data
        news = data.get('news', [])
        weather = data.get('weather', {})
        crypto = data.get('crypto', {})
        
        # GPT/Processing data (if available)
        processing_data = data.get('processing_data', {})
        gpt_input = processing_data.get('gpt_prompt', '')
        gpt_output = processing_data.get('radio_script', '')
        voice_config = processing_data.get('voice_config', {})
        show_config = processing_data.get('show_config', {})
        
        # Statistics
        total_articles = len(news)
        sources = {}
        categories = {}
        
        for item in news:
            source = item.get('source', 'unknown')
            category = item.get('category', 'general')
            sources[source] = sources.get(source, 0) + 1
            categories[category] = categories.get(category, 0) + 1
        
        # JSON data for JavaScript
        json_data = json.dumps(data, indent=2, ensure_ascii=False, default=str)
        
        # Comprehensive HTML Template
        comprehensive_html = f"""<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>📻 RadioX Complete Dashboard</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
            color: #ffffff; min-height: 100vh; overflow-x: hidden;
        }}
        
        .main-container {{ 
            max-width: 100vw; min-height: 100vh;
            background: rgba(0,0,0,0.3); backdrop-filter: blur(10px);
        }}
        
        .header {{ 
            background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%);
            color: white; padding: 20px; text-align: center;
            box-shadow: 0 4px 20px rgba(0,0,0,0.3);
        }}
        
        .header h1 {{ 
            font-size: 2.8em; margin-bottom: 5px; 
            text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
            background: linear-gradient(45deg, #fff, #f8f9fa);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        }}
        
        .header .subtitle {{ 
            font-size: 1.3em; opacity: 0.9; font-weight: 300;
        }}
        
        /* Navigation Tabs */
        .nav-tabs {{ 
            display: flex; background: rgba(0,0,0,0.5); 
            justify-content: center; flex-wrap: wrap; padding: 10px;
        }}
        
        .nav-tab {{ 
            padding: 12px 24px; margin: 5px; background: rgba(255,255,255,0.1);
            border: none; color: white; cursor: pointer; border-radius: 25px;
            transition: all 0.3s ease; font-weight: 600; font-size: 14px;
        }}
        
        .nav-tab.active {{ 
            background: linear-gradient(135deg, #3498db 0%, #2980b9 100%);
            transform: translateY(-2px); box-shadow: 0 4px 15px rgba(52, 152, 219, 0.4);
        }}
        
        .nav-tab:hover {{ 
            background: rgba(255,255,255,0.2); transform: translateY(-1px);
        }}
        
        /* Content Sections */
        .content-section {{ 
            display: none; padding: 30px; min-height: calc(100vh - 200px);
        }}
        
        .content-section.active {{ display: block; }}
        
        /* Stats Grid */
        .stats-grid {{ 
            display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px; margin-bottom: 30px;
        }}
        
        .stat-card {{ 
            background: rgba(255,255,255,0.1); backdrop-filter: blur(10px);
            padding: 25px; border-radius: 15px; text-align: center;
            border: 1px solid rgba(255,255,255,0.2); transition: all 0.3s ease;
        }}
        
        .stat-card:hover {{ 
            transform: translateY(-5px); box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            background: rgba(255,255,255,0.15);
        }}
        
        .stat-card .icon {{ font-size: 3em; margin-bottom: 15px; }}
        .stat-card .number {{ 
            font-size: 2.5em; font-weight: bold; margin-bottom: 10px;
            background: linear-gradient(135deg, #4CAF50, #2E7D32);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        }}
        .stat-card .label {{ 
            font-size: 1.1em; opacity: 0.8; text-transform: uppercase; letter-spacing: 1px;
        }}
        
        /* Grid Layouts */
        .two-column {{ display: grid; grid-template-columns: 2fr 1fr; gap: 30px; }}
        .three-column {{ display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 20px; }}
        
        /* Panel Styles */
        .panel {{ 
            background: rgba(255,255,255,0.1); backdrop-filter: blur(10px);
            border-radius: 15px; border: 1px solid rgba(255,255,255,0.2);
            overflow: hidden; margin-bottom: 20px;
        }}
        
        .panel-header {{ 
            background: linear-gradient(135deg, #34495e 0%, #2c3e50 100%);
            color: white; padding: 15px; font-weight: bold; font-size: 1.2em;
        }}
        
        .panel-content {{ padding: 20px; max-height: 400px; overflow-y: auto; }}
        .panel-content::-webkit-scrollbar {{ width: 8px; }}
        .panel-content::-webkit-scrollbar-track {{ background: rgba(255,255,255,0.1); }}
        .panel-content::-webkit-scrollbar-thumb {{ background: rgba(255,255,255,0.3); border-radius: 4px; }}
        
        /* News Items */
        .news-item {{ 
            background: rgba(255,255,255,0.05); margin-bottom: 15px;
            padding: 15px; border-radius: 10px; border-left: 4px solid #3498db;
            transition: all 0.3s ease;
        }}
        
        .news-item:hover {{ 
            background: rgba(255,255,255,0.1); transform: translateX(5px);
        }}
        
        .news-title {{ 
            font-weight: bold; margin-bottom: 8px; color: #fff; font-size: 1.1em;
        }}
        
        .news-meta {{ 
            font-size: 0.9em; opacity: 0.7; margin-bottom: 8px;
        }}
        
        .news-summary {{ 
            font-size: 0.95em; line-height: 1.4; opacity: 0.9;
        }}
        
        /* Source Badges */
        .source-badge {{ 
            padding: 4px 12px; border-radius: 12px; font-size: 0.8em;
            font-weight: bold; text-transform: uppercase; color: white;
            display: inline-block; margin-right: 8px;
        }}
        
        .source-nzz {{ background: #e74c3c; }}
        .source-srf {{ background: #27ae60; }}
        .source-tagesanzeiger {{ background: #8e44ad; }}
        .source-cash {{ background: #2ecc71; }}
        .source-heise {{ background: #34495e; }}
        .source-unknown {{ background: #95a5a6; }}
        
        /* Weather Card */
        .weather-card {{ 
            background: linear-gradient(135deg, #3498db 0%, #2980b9 100%);
            border-radius: 15px; padding: 20px; text-align: center; color: white;
        }}
        
        .weather-temp {{ font-size: 3em; font-weight: bold; margin: 10px 0; }}
        .weather-desc {{ font-size: 1.2em; opacity: 0.9; }}
        .weather-details {{ 
            display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 15px;
        }}
        .weather-detail {{ background: rgba(255,255,255,0.2); padding: 10px; border-radius: 8px; }}
        
        /* Crypto Card */
        .crypto-card {{ 
            background: linear-gradient(135deg, #f39c12 0%, #e67e22 100%);
            border-radius: 15px; padding: 20px; text-align: center; color: white;
        }}
        
        .crypto-price {{ font-size: 2em; font-weight: bold; margin: 10px 0; }}
        .crypto-change {{ font-size: 1.3em; }}
        .crypto-change.positive {{ color: #2ecc71; }}
        .crypto-change.negative {{ color: #e74c3c; }}
        
        /* GPT Section */
        .gpt-section {{ margin-bottom: 30px; }}
        .gpt-panel {{ margin-bottom: 20px; }}
        .gpt-content {{ 
            background: rgba(0,0,0,0.3); padding: 20px; border-radius: 10px;
            font-family: 'Monaco', 'Consolas', monospace; font-size: 13px;
            line-height: 1.5; white-space: pre-wrap; max-height: 300px; overflow-y: auto;
        }}
        
        /* Voice Config */
        .voice-config {{ 
            display: grid; grid-template-columns: 1fr 1fr; gap: 20px;
        }}
        
        .voice-speaker {{ 
            background: rgba(255,255,255,0.05); padding: 15px; border-radius: 10px;
        }}
        
        .voice-speaker h4 {{ margin-bottom: 10px; color: #4CAF50; }}
        .voice-param {{ margin-bottom: 8px; font-size: 0.9em; }}
        .voice-param strong {{ color: #fff; }}
        
        /* Timestamp */
        .timestamp {{ 
            text-align: center; padding: 20px; background: rgba(0,0,0,0.3);
            color: rgba(255,255,255,0.7); font-style: italic; margin-top: 30px;
        }}
        
        /* Responsive */
        @media (max-width: 768px) {{
            .two-column {{ grid-template-columns: 1fr; }}
            .three-column {{ grid-template-columns: 1fr; }}
            .stats-grid {{ grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); }}
            .nav-tabs {{ padding: 5px; }}
            .nav-tab {{ padding: 8px 16px; margin: 2px; font-size: 12px; }}
            .content-section {{ padding: 15px; }}
        }}
    </style>
</head>
<body>
    <div class="main-container">
        <!-- Header -->
        <div class="header">
            <h1>📻 RadioX Complete Dashboard</h1>
            <div class="subtitle">Data Collection • GPT Processing • Voice Configuration</div>
        </div>

        <!-- Navigation -->
        <div class="nav-tabs">
            <button class="nav-tab active" onclick="showSection('overview')">📊 Overview</button>
            <button class="nav-tab" onclick="showSection('data')">📰 Data Collection</button>
            <button class="nav-tab" onclick="showSection('gpt')">🤖 GPT Processing</button>
            <button class="nav-tab" onclick="showSection('voice')">🎤 Voice Config</button>
            <button class="nav-tab" onclick="showSection('raw')">📋 Raw Data</button>
        </div>

        <!-- Overview Section -->
        <div id="overview" class="content-section active">
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="icon">📰</div>
                    <div class="number">{total_articles}</div>
                    <div class="label">Total Articles</div>
                </div>
                <div class="stat-card">
                    <div class="icon">📡</div>
                    <div class="number">{len(sources)}</div>
                    <div class="label">News Sources</div>
                </div>
                <div class="stat-card">
                    <div class="icon">🏷️</div>
                    <div class="number">{len(categories)}</div>
                    <div class="label">Categories</div>
                </div>
                <div class="stat-card">
                    <div class="icon">🌡️</div>
                    <div class="number">{weather.get('temperature', 'N/A')}</div>
                    <div class="label">Temperature</div>
                </div>
                <div class="stat-card">
                    <div class="icon">₿</div>
                    <div class="number">${crypto.get('bitcoin', {}).get('price_usd', 0):,.0f}</div>
                    <div class="label">Bitcoin Price</div>
                </div>
                <div class="stat-card">
                    <div class="icon">📝</div>
                    <div class="number">{len(gpt_output.split()) if gpt_output else 0}</div>
                    <div class="label">GPT Words</div>
                </div>
            </div>

            <div class="three-column">
                <!-- Weather Card -->
                <div class="weather-card">
                    <h3>🌤️ Weather</h3>
                    <div class="weather-temp">{weather.get('temperature', 'N/A')}°</div>
                    <div class="weather-desc">{weather.get('description', 'No data')}</div>
                    <div class="weather-details">
                        <div class="weather-detail">
                            <strong>Humidity</strong><br>
                            {weather.get('humidity', 'N/A')}%
                        </div>
                        <div class="weather-detail">
                            <strong>Pressure</strong><br>
                            {weather.get('pressure', 'N/A')} hPa
                        </div>
                    </div>
                </div>

                <!-- Crypto Card -->
                <div class="crypto-card">
                    <h3>₿ Bitcoin</h3>
                    <div class="crypto-price">${crypto.get('bitcoin', {}).get('price_usd', 0):,.0f}</div>
                    <div class="crypto-change {'positive' if crypto.get('bitcoin', {}).get('change_24h', 0) > 0 else 'negative'}">
                        {crypto.get('bitcoin', {}).get('change_24h', 0):+.2f}%
                    </div>
                </div>

                <!-- Source Distribution -->
                <div class="panel">
                    <div class="panel-header">📊 Source Distribution</div>
                    <div class="panel-content">
                        {self._generate_source_distribution_html(sources)}
                    </div>
                </div>
            </div>
        </div>

        <!-- Data Collection Section -->
        <div id="data" class="content-section">
            <div class="two-column">
                <div class="panel">
                    <div class="panel-header">📰 Latest News ({total_articles} articles)</div>
                    <div class="panel-content">
                        {self._generate_news_items_html(news[:20])}
                    </div>
                </div>
                <div>
                    <div class="panel">
                        <div class="panel-header">📊 Collection Statistics</div>
                        <div class="panel-content">
                            {self._generate_collection_stats_html(sources, categories)}
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- GPT Processing Section -->
        <div id="gpt" class="content-section">
            <div class="gpt-section">
                <div class="panel gpt-panel">
                    <div class="panel-header">📤 GPT Input (Prompt)</div>
                    <div class="gpt-content">{gpt_input or 'No GPT input available'}</div>
                </div>
                
                <div class="panel gpt-panel">
                    <div class="panel-header">📥 GPT Output (Radio Script)</div>
                    <div class="gpt-content">{gpt_output or 'No GPT output available'}</div>
                </div>
            </div>
        </div>

        <!-- Voice Configuration Section -->
        <div id="voice" class="content-section">
            <div class="panel">
                <div class="panel-header">🎤 Voice Configuration</div>
                <div class="panel-content">
                    {self._generate_voice_config_html(voice_config, show_config)}
                </div>
            </div>
        </div>

        <!-- Raw Data Section -->
        <div id="raw" class="content-section">
            <div class="panel">
                <div class="panel-header">📋 Complete Raw Data (JSON)</div>
                <div class="gpt-content">{json_data}</div>
            </div>
        </div>

        <!-- Timestamp -->
        <div class="timestamp">
            Complete Dashboard generated: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}
        </div>
    </div>

    <script>
        function showSection(sectionId) {{
            // Hide all sections
            document.querySelectorAll('.content-section').forEach(section => {{
                section.classList.remove('active');
            }});
            
            // Remove active class from all tabs
            document.querySelectorAll('.nav-tab').forEach(tab => {{
                tab.classList.remove('active');
            }});
            
            // Show selected section
            document.getElementById(sectionId).classList.add('active');
            
            // Add active class to clicked tab
            event.target.classList.add('active');
        }}

        // Store complete data for JavaScript access
        window.radioXData = {json_data};
        
        // Auto-refresh every 5 minutes (if needed)
        // setTimeout(() => location.reload(), 300000);
    </script>
</body>
</html>"""

        # Save comprehensive HTML
        comprehensive_path = os.path.join(outplay_dir, "radiox_complete.html")
        with open(comprehensive_path, 'w', encoding='utf-8') as f:
            f.write(comprehensive_html)
        
        logger.info("✅ Comprehensive Dashboard (radiox_complete.html) generiert")
    
    async def _save_json_data(self, data: Dict[str, Any], outplay_dir: str):
        """Speichert die JSON-Daten für JavaScript"""
        
        import json
        
        # Saubere JSON-Daten speichern
        json_path = os.path.join(outplay_dir, "data_collection_clean.json")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info("✅ JSON-Daten gespeichert (data_collection_clean.json)")
    
    def _generate_source_distribution_html(self, sources: Dict[str, int]) -> str:
        """Generiert Source Distribution HTML"""
        html = ""
        for source, count in sorted(sources.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / sum(sources.values())) * 100 if sources else 0
            html += f"""
            <div style="margin-bottom: 10px; padding: 10px; background: rgba(255,255,255,0.05); border-radius: 8px;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                    <span><span class="source-badge source-{source.lower().replace(' ', '')}">{source}</span></span>
                    <span><strong>{count}</strong> articles</span>
                </div>
                <div style="background: rgba(255,255,255,0.1); height: 8px; border-radius: 4px; overflow: hidden;">
                    <div style="background: #3498db; height: 100%; width: {percentage}%; transition: width 0.3s ease;"></div>
                </div>
                <div style="font-size: 0.8em; opacity: 0.7; margin-top: 3px;">{percentage:.1f}%</div>
            </div>
            """
        return html

    def _generate_news_items_html(self, news: List[Dict[str, Any]]) -> str:
        """Generiert News Items HTML"""
        html = ""
        for item in news:
            source = item.get('source', 'unknown')
            category = item.get('category', 'general')
            title = item.get('title', 'No title')[:100] + '...' if len(item.get('title', '')) > 100 else item.get('title', 'No title')
            summary = item.get('summary', 'No summary')[:200] + '...' if len(item.get('summary', '')) > 200 else item.get('summary', 'No summary')
            age = item.get('age', 'unknown')
            
            html += f"""
            <div class="news-item">
                <div class="news-title">{title}</div>
                <div class="news-meta">
                    <span class="source-badge source-{source.lower().replace(' ', '')}">{source}</span>
                    <span style="opacity: 0.7;">• {category} • {age}</span>
                </div>
                <div class="news-summary">{summary}</div>
            </div>
            """
        return html

    def _generate_collection_stats_html(self, sources: Dict[str, int], categories: Dict[str, int]) -> str:
        """Generiert Collection Statistics HTML"""
        html = f"""
        <div style="margin-bottom: 20px;">
            <h4 style="color: #4CAF50; margin-bottom: 10px;">📊 Sources ({len(sources)})</h4>
            {self._generate_simple_stats_list(sources)}
        </div>
        <div>
            <h4 style="color: #4CAF50; margin-bottom: 10px;">🏷️ Categories ({len(categories)})</h4>
            {self._generate_simple_stats_list(categories)}
        </div>
        """
        return html

    def _generate_simple_stats_list(self, stats_dict: Dict[str, int]) -> str:
        """Generiert simple Stats Liste"""
        html = ""
        for key, value in sorted(stats_dict.items(), key=lambda x: x[1], reverse=True):
            html += f"""
            <div style="display: flex; justify-content: space-between; padding: 5px 0; border-bottom: 1px solid rgba(255,255,255,0.1);">
                <span>{key}</span>
                <span style="color: #4CAF50; font-weight: bold;">{value}</span>
            </div>
            """
        return html

    def _generate_voice_config_html(self, voice_config: Dict[str, Any], show_config: Dict[str, Any]) -> str:
        """Generiert Voice Configuration HTML"""
        primary_speaker = show_config.get('speaker', {}) if show_config else {}
        secondary_speaker = show_config.get('secondary_speaker', {}) if show_config else {}
        
        html = f"""
        <div class="voice-config">
            <div class="voice-speaker">
                <h4>🎤 Primary Speaker</h4>
                <div class="voice-param"><strong>Voice ID:</strong> {primary_speaker.get('voice_id', 'N/A')}</div>
                <div class="voice-param"><strong>Model:</strong> {primary_speaker.get('model', 'N/A')}</div>
                <div class="voice-param"><strong>Stability:</strong> {primary_speaker.get('voice_settings', {}).get('stability', 'N/A')}</div>
                <div class="voice-param"><strong>Clarity:</strong> {primary_speaker.get('voice_settings', {}).get('similarity_boost', 'N/A')}</div>
                <div class="voice-param"><strong>Style:</strong> {primary_speaker.get('voice_settings', {}).get('style', 'N/A')}</div>
            </div>
            <div class="voice-speaker">
                <h4>🎤 Secondary Speaker</h4>
                <div class="voice-param"><strong>Voice ID:</strong> {secondary_speaker.get('voice_id', 'N/A')}</div>
                <div class="voice-param"><strong>Model:</strong> {secondary_speaker.get('model', 'N/A')}</div>
                <div class="voice-param"><strong>Stability:</strong> {secondary_speaker.get('voice_settings', {}).get('stability', 'N/A')}</div>
                <div class="voice-param"><strong>Clarity:</strong> {secondary_speaker.get('voice_settings', {}).get('similarity_boost', 'N/A')}</div>
                <div class="voice-param"><strong>Style:</strong> {secondary_speaker.get('voice_settings', {}).get('style', 'N/A')}</div>
            </div>
        </div>
        
        <div style="margin-top: 20px;">
            <h4 style="color: #4CAF50; margin-bottom: 10px;">🔧 Additional Settings</h4>
            <div class="voice-param"><strong>Audio Format:</strong> {voice_config.get('audio_format', 'N/A')}</div>
            <div class="voice-param"><strong>Optimize Streaming:</strong> {voice_config.get('optimize_streaming_latency', 'N/A')}</div>
            <div class="voice-param"><strong>Output Format:</strong> {voice_config.get('output_format', 'N/A')}</div>
        </div>
        """
        return html

    def _generate_source_stats_html(self, sources: Dict[str, int]) -> str:
        """Generiert HTML für Quellen-Statistiken"""
        
        stats_html = '<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px;">'
        
        for source, count in sorted(sources.items(), key=lambda x: x[1], reverse=True):
            stats_html += f'''
                <div style="background: #ecf0f1; padding: 15px; border-radius: 8px; text-align: center;">
                    <div class="source-badge source-{source}" style="display: inline-block; margin-bottom: 8px;">{source}</div>
                    <div style="font-size: 1.5em; font-weight: bold; color: #2c3e50;">{count}</div>
                    <div style="font-size: 0.9em; color: #7f8c8d;">Artikel</div>
                </div>
            '''
        
        stats_html += '</div>'
        return stats_html
    
    def _generate_news_table_html(self, news: List[Dict[str, Any]]) -> str:
        """Generiert HTML für News-Tabelle"""
        
        table_html = ""
        
        for item in news:
            age_hours = round(item.get('age_hours', 0))
            link_html = f'<a href="{item.get("link", "")}" target="_blank" class="news-link">🔗 Artikel</a>' if item.get('has_link') else 'Kein Link'
            
            table_html += f'''
                <tr>
                    <td><span class="source-badge source-{item.get('source', 'unknown')}">{item.get('source', 'Unknown')}</span></td>
                    <td>{item.get('category', 'general')}</td>
                    <td style="max-width: 400px;"><strong>{item.get('title', 'Kein Titel')}</strong></td>
                    <td style="max-width: 300px;">{item.get('summary', 'Keine Zusammenfassung')[:150]}...</td>
                    <td>{age_hours}h</td>
                    <td>{link_html}</td>
                </tr>
            '''
        
        return table_html
    
    # ==================== PRIVATE HELPER METHODS ====================
    
    async def _collect_all_news_safe(self) -> List[Dict[str, Any]]:
        """
        Sammelt ALLE RSS News - PARALLELISIERT für bessere Performance
        Gibt ALLE verfügbaren Informationen zurück für GPT-Priorisierung
        """
        
        logger.info("📰 Sammle RSS News...")
        
        try:
            # Hole aktive Feeds
            feeds = await self.rss_service.get_all_active_feeds()
            
            if not feeds:
                logger.warning("⚠️ Keine aktiven RSS Feeds")
                return []
            
            logger.info(f"🚀 Sammle von {len(feeds)} Feeds parallel...")
            
            # Verwende die optimierte RSS Service Methode
            news_items = await self.rss_service.get_all_recent_news()
            
            logger.info(f"📊 {len(news_items)} News gesammelt")
            
            if not news_items:
                logger.warning("⚠️ Keine News gefunden")
                return []
            
            # Konvertiere RSSNewsItem Objekte zu vollständigen JSON-Dictionaries
            news_json = []
            for item in news_items:
                news_dict = {
                    "title": item.title,
                    "summary": item.summary,
                    "link": item.link,  # WICHTIG: URL für GPT
                    "published": item.published.isoformat(),
                    "source": item.source,
                    "category": item.category,
                    "priority": item.priority,
                    "weight": item.weight,
                    # Zusätzliche Metadaten für GPT
                    "published_timestamp": item.published.timestamp(),
                    "age_hours": (datetime.now() - item.published).total_seconds() / 3600,
                    "content_length": len(item.summary),
                    "has_link": bool(item.link),
                    "source_category": f"{item.source}_{item.category}"
                }
                news_json.append(news_dict)
            
            logger.info(f"✅ {len(news_json)} News als JSON bereit")
            return news_json
            
        except Exception as e:
            logger.error(f"❌ RSS-Sammlung Fehler: {e}")
            return []
    
    async def _collect_weather_safe(self) -> Dict[str, Any]:
        """Sammelt ALLE Wetter-Daten - Current Weather nur"""
        logger.info("🌤️ Hole ALLE Zürich Wetter-Daten...")
        
        try:
            # Sammle nur verfügbare Wetter-Informationen
            current_summary = await self.weather_service.get_weather_summary_with_gpt("zurich")  # ⭐ NEU: GPT-Summary!
            
            # Zusammenfassen aller Wetter-Daten - GPT-Summary ist ein String!
            weather_data = {
                "current_summary": current_summary,  # ⭐ String GPT-Summary
                "location": "Zürich",
                "timestamp": datetime.now().isoformat()
            }
            
            # ENTFERNT: Alte Rückwärtskompatibilität da GPT-Summary ein String ist
            
            logger.info(f"✅ Zürich Wetter gesammelt: {len(current_summary)} Zeichen")
            return weather_data
            
        except Exception as e:
            logger.error(f"❌ Fehler bei Wetter-Sammlung: {e}")
            return {}
    
    async def _collect_crypto_safe(self) -> Dict[str, Any]:
        """Sammelt ALLE Crypto-Daten - Bitcoin GPT-Summary + Raw Data"""
        logger.info("₿ Hole ALLE Crypto-Daten...")
        
        try:
            # ⭐ NEU: Hole intelligente Bitcoin-GPT-Summary
            bitcoin_summary = await self.crypto_service.get_bitcoin_summary_with_gpt()  # ⭐ GPT-Summary!
            
            # Sammle ALLE verfügbaren Bitcoin-Informationen parallel für Rückwärtskompatibilität
            price_task = self.crypto_service.get_bitcoin_price()
            trend_task = self.crypto_service.get_bitcoin_trend()
            alerts_task = self.crypto_service.get_bitcoin_alerts(price_threshold=100000)
            
            price_data, trend_data, alerts_data = await asyncio.gather(
                price_task, trend_task, alerts_task,
                return_exceptions=True
            )
            
            # Zusammenfassen aller Bitcoin-Daten - GPT-Summary ist ein String!
            crypto_data = {
                "bitcoin_summary": bitcoin_summary,  # ⭐ String GPT-Summary
                "bitcoin": price_data if not isinstance(price_data, Exception) else None,
                "trend": trend_data if not isinstance(trend_data, Exception) else None,
                "alerts": alerts_data if not isinstance(alerts_data, Exception) else [],
                "timestamp": datetime.now().isoformat()
            }
            
            # Radio-formatierte Ausgaben für verschiedene Zeiträume (Rückwärtskompatibilität)
            if crypto_data["bitcoin"]:
                try:
                    radio_24h = self.crypto_service.format_for_radio(crypto_data["bitcoin"], "24h")
                    radio_7d = self.crypto_service.format_for_radio(crypto_data["bitcoin"], "7d")
                    
                    crypto_data["radio_formats"] = {
                        "24h": radio_24h,
                        "7d": radio_7d
                    }
                except Exception as e:
                    logger.warning(f"⚠️ Radio-Format-Generierung fehlgeschlagen: {e}")
            
            price = crypto_data["bitcoin"]["price_usd"] if crypto_data["bitcoin"] else "N/A"
            logger.info(f"✅ Bitcoin: ${price:,.0f} + GPT-Summary ({len(bitcoin_summary)} Zeichen)")
            return crypto_data
            
        except Exception as e:
            logger.error(f"❌ Fehler bei Crypto-Sammlung: {e}")
            return {} 