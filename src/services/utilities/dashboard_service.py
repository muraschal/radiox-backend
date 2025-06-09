"""
📻 RadioX Dashboard Service
High-Performance HTML Dashboard Generator

Generates beautiful radiox_shownotes_yymmdd_hhmm.html based on data_collection.html
but with smaller boxes and additional Voice/GPT processing data.
"""

import os
import json
from datetime import datetime
from typing import Dict, Any, List
from loguru import logger


class DashboardService:
    """
    🎨 Dashboard Service für RadioX Show Notes
    TAILWIND CSS ÜBER CDN - EINFACH & FUNKTIONAL
    """
    
    def __init__(self):
        """Initialisiert den Dashboard Service"""
        self.output_dir = "outplay"
        os.makedirs(self.output_dir, exist_ok=True)
        logger.info("📊 Dashboard Service initialisiert")
    
    async def generate_shownotes_dashboard(
        self, 
        raw_data: Dict[str, Any], 
        processed_data: Dict[str, Any], 
        show_config: Dict[str, Any]
    ) -> str:
        """Generiert das Show Notes Dashboard"""
        try:
            logger.info("🎨 Generiere RadioX Show Notes Dashboard...")
            
            # Extract processing data
            processed_info = self._extract_processing_data(processed_data)
            
            # Calculate stats
            stats = self._calculate_dashboard_stats(raw_data, processed_info)
            
            # Generate timestamp
            timestamp = datetime.now().strftime('%y%m%d_%H%M')
            
            # Generate HTML
            html_content = self._generate_tailwind_html(
                raw_data, processed_info, show_config, stats, timestamp
            )
            
            # Save to file
            filename = f"radiox_shownotes_{timestamp}.html"
            filepath = os.path.join(self.output_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            logger.info(f"✅ Show Notes Dashboard generiert: {filename}")
            return filepath
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Generieren des Dashboards: {e}")
            raise
    
    def _extract_processing_data(self, processed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extrahiert die verarbeiteten Daten"""
        return {
            'gpt_prompt': processed_data.get('gpt_prompt', ''),
            'radio_script': processed_data.get('radio_script', ''),
            'selected_news': processed_data.get('selected_news', []),
            'processing_info': processed_data.get('processing_info', {})
        }
    
    def _calculate_dashboard_stats(self, raw_data: Dict[str, Any], processed_info: Dict[str, Any]) -> Dict[str, Any]:
        """Berechnet Dashboard-Statistiken"""
        news = raw_data.get('news', [])
        weather = raw_data.get('weather', {})
        crypto = raw_data.get('crypto', {})
        
        return {
            'total_news': len(news),
            'selected_news': len(processed_info.get('selected_news', [])),
            'total_sources': len(set(item.get('source', 'unknown') for item in news)),
            'gpt_words': len(processed_info.get('radio_script', '').split()),
            'weather_temp': weather.get('temperature', 'N/A'),
            'bitcoin_price': crypto.get('bitcoin', {}).get('price_usd', 0),
            'sources': {}
        }
    
    def _generate_tailwind_html(
        self, 
        raw_data: Dict[str, Any], 
        processed_info: Dict[str, Any], 
        show_config: Dict[str, Any], 
        stats: Dict[str, Any],
        timestamp: str
    ) -> str:
        """Generiert sauberes Tailwind CSS Dashboard"""
        
        news = raw_data.get('news', [])
        weather = raw_data.get('weather', {})
        crypto = raw_data.get('crypto', {})
        
        return f"""<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>📻 RadioX Show Notes - {timestamp}</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-100 min-h-screen">
    
    <!-- Header -->
    <div class="bg-blue-600 text-white py-6">
        <div class="max-w-7xl mx-auto px-4">
            <h1 class="text-3xl font-bold">📻 RadioX Show Notes</h1>
            <p class="text-blue-200 mt-2">Dashboard • {timestamp}</p>
        </div>
    </div>

    <!-- Stats -->
    <div class="bg-white shadow-sm py-6">
        <div class="max-w-7xl mx-auto px-4">
            <div class="grid grid-cols-6 gap-4 text-center">
                <div class="bg-blue-50 p-4 rounded-lg">
                    <div class="text-2xl mb-2">📰</div>
                    <div class="text-xl font-bold text-gray-800">{stats['total_news']}</div>
                    <div class="text-sm text-gray-500">News Total</div>
                </div>
                <div class="bg-green-50 p-4 rounded-lg">
                    <div class="text-2xl mb-2">✅</div>
                    <div class="text-xl font-bold text-gray-800">{stats['selected_news']}</div>
                    <div class="text-sm text-gray-500">Selected</div>
                </div>
                <div class="bg-purple-50 p-4 rounded-lg">
                    <div class="text-2xl mb-2">📡</div>
                    <div class="text-xl font-bold text-gray-800">{stats['total_sources']}</div>
                    <div class="text-sm text-gray-500">Sources</div>
                </div>
                <div class="bg-indigo-50 p-4 rounded-lg">
                    <div class="text-2xl mb-2">🤖</div>
                    <div class="text-xl font-bold text-gray-800">{stats['gpt_words']}</div>
                    <div class="text-sm text-gray-500">GPT Words</div>
                </div>
                <div class="bg-orange-50 p-4 rounded-lg">
                    <div class="text-2xl mb-2">🌡️</div>
                    <div class="text-xl font-bold text-gray-800">{stats['weather_temp']}</div>
                    <div class="text-sm text-gray-500">Temperature</div>
                </div>
                <div class="bg-yellow-50 p-4 rounded-lg">
                    <div class="text-2xl mb-2">₿</div>
                    <div class="text-xl font-bold text-gray-800">${stats['bitcoin_price']:,.0f}</div>
                    <div class="text-sm text-gray-500">Bitcoin</div>
                </div>
            </div>
        </div>
    </div>

    <!-- Main Content -->
    <div class="max-w-7xl mx-auto px-4 py-8">
        <div class="grid grid-cols-12 gap-6">
            
            <!-- NEWS COLUMN (8/12) -->
            <div class="col-span-8">
                <div class="bg-white rounded-lg shadow-sm">
                    <div class="bg-blue-600 text-white px-6 py-4 rounded-t-lg">
                        <h2 class="text-xl font-bold">📰 News Feed ({stats['total_news']} articles)</h2>
                    </div>
                    
                    <!-- Filter Buttons -->
                    <div class="p-4 bg-gray-50 border-b">
                        <div class="flex flex-wrap gap-2">
                            <button class="filter-btn px-3 py-1 text-sm rounded-full bg-blue-600 text-white" data-filter="all">Alle</button>
                            <button class="filter-btn px-3 py-1 text-sm rounded-full bg-gray-200 hover:bg-gray-300" data-filter="zurich">Zürich</button>
                            <button class="filter-btn px-3 py-1 text-sm rounded-full bg-gray-200 hover:bg-gray-300" data-filter="tech">Tech</button>
                            <button class="filter-btn px-3 py-1 text-sm rounded-full bg-gray-200 hover:bg-gray-300" data-filter="bitcoin">Bitcoin</button>
                            <button class="filter-btn px-3 py-1 text-sm rounded-full bg-gray-200 hover:bg-gray-300" data-filter="international">International</button>
                        </div>
                    </div>
                    
                    <!-- News List -->
                    <div class="p-4 max-h-96 overflow-y-auto space-y-3" id="news-container">
                        {self._generate_news_html(news)}
                    </div>
                </div>
            </div>

            <!-- SIDEBAR (4/12) -->
            <div class="col-span-4 space-y-6">
                
                <!-- GPT Processing -->
                <div class="bg-white rounded-lg shadow-sm">
                    <div class="bg-purple-600 text-white px-4 py-3 rounded-t-lg">
                        <h3 class="font-bold">🤖 GPT Processing</h3>
                    </div>
                    <div class="p-4 space-y-4">
                        <div>
                            <h4 class="font-medium text-gray-700 mb-2">📤 Input Prompt</h4>
                            <div class="bg-gray-900 text-green-400 p-3 rounded text-xs font-mono max-h-32 overflow-y-auto whitespace-pre-wrap">
{self._safe_text(processed_info.get('gpt_prompt', 'No GPT input'), 800)}
                            </div>
                        </div>
                        <div>
                            <h4 class="font-medium text-gray-700 mb-2">📥 Radio Script</h4>
                            <div class="bg-gray-900 text-green-400 p-3 rounded text-xs font-mono max-h-32 overflow-y-auto whitespace-pre-wrap">
{self._safe_text(processed_info.get('radio_script', 'No radio script'), 800)}
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Voice Config -->
                <div class="bg-white rounded-lg shadow-sm">
                    <div class="bg-teal-600 text-white px-4 py-3 rounded-t-lg">
                        <h3 class="font-bold">🎤 Voice Configuration</h3>
                    </div>
                    <div class="p-4 text-sm space-y-3">
                        {self._generate_voice_html(show_config)}
                    </div>
                </div>

                <!-- Context Data -->
                <div class="bg-white rounded-lg shadow-sm">
                    <div class="bg-orange-500 text-white px-4 py-3 rounded-t-lg">
                        <h3 class="font-bold">🌍 Context Data</h3>
                    </div>
                    <div class="p-4 space-y-4">
                        <!-- Weather -->
                        <div class="text-center">
                            <div class="text-sm font-medium text-gray-700">🌤️ Weather</div>
                            <div class="text-2xl font-bold text-orange-600">{weather.get('temperature', 'N/A')}°</div>
                            <div class="text-gray-600">{weather.get('description', 'No data')}</div>
                        </div>
                        
                        <!-- Bitcoin -->
                        <div class="text-center border-t pt-4">
                            <div class="text-sm font-medium text-gray-700">₿ Bitcoin</div>
                            <div class="text-xl font-bold text-yellow-600">${crypto.get('bitcoin', {}).get('price_usd', 0):,.0f}</div>
                            <div class="text-lg font-medium {'text-green-600' if crypto.get('bitcoin', {}).get('change_24h', 0) > 0 else 'text-red-600'}">
                                {crypto.get('bitcoin', {}).get('change_24h', 0):+.2f}%
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        // Filter functionality
        document.addEventListener('DOMContentLoaded', function() {{
            const filterButtons = document.querySelectorAll('.filter-btn');
            const newsItems = document.querySelectorAll('.news-item');

            filterButtons.forEach(button => {{
                button.addEventListener('click', function() {{
                    // Update button styles
                    filterButtons.forEach(btn => {{
                        btn.classList.remove('bg-blue-600', 'text-white');
                        btn.classList.add('bg-gray-200');
                    }});
                    this.classList.remove('bg-gray-200');
                    this.classList.add('bg-blue-600', 'text-white');

                    const filter = this.getAttribute('data-filter');

                    newsItems.forEach(item => {{
                        const category = item.getAttribute('data-category') || '';
                        const title = item.getAttribute('data-title').toLowerCase();
                        
                        if (filter === 'all') {{
                            item.classList.remove('hidden');
                        }} else {{
                            const matches = category.includes(filter) || title.includes(filter);
                            item.classList.toggle('hidden', !matches);
                        }}
                    }});
                }});
            }});
        }});
        
        console.log('📻 RadioX Tailwind Dashboard loaded!');
    </script>
</body>
</html>"""

    def _generate_news_html(self, news: List[Dict[str, Any]]) -> str:
        """Generiert News HTML"""
        html = ""
        for item in news:
            title = item.get('title', 'No title')
            summary = item.get('summary', '')
            source = item.get('source', 'Unknown')
            category = item.get('category', 'general')
            age = item.get('age_hours', 0)
            url = item.get('url', '#')
            
            # Truncate summary
            short_summary = summary[:150] + '...' if len(summary) > 150 else summary
            
            html += f"""
            <div class="news-item p-4 border rounded-lg hover:bg-gray-50 transition-colors" 
                 data-category="{category}" data-title="{title}">
                <div class="flex flex-wrap gap-2 mb-2">
                    <span class="px-2 py-1 text-xs font-medium rounded bg-blue-100 text-blue-800">{source}</span>
                    <span class="px-2 py-1 text-xs rounded bg-gray-100 text-gray-700">{category}</span>
                    <span class="px-2 py-1 text-xs rounded bg-gray-100 text-gray-600">{age:.1f}h ago</span>
                </div>
                <h4 class="font-semibold text-gray-900 mb-2">{title}</h4>
                <p class="text-gray-600 text-sm mb-3">{short_summary}</p>
                <a href="{url}" target="_blank" class="text-blue-600 hover:text-blue-800 text-sm">🔗 Read article</a>
            </div>
            """
        return html
    
    def _generate_voice_html(self, show_config: Dict[str, Any]) -> str:
        """Generiert Voice HTML"""
        primary = show_config.get('speaker', {})
        secondary = show_config.get('secondary_speaker', {})
        
        return f"""
        <div class="bg-gray-50 p-3 rounded border-l-4 border-teal-500">
            <div class="font-medium">🎤 Primary: {primary.get('name', 'N/A')}</div>
            <div class="text-xs text-gray-600 mt-1">ID: {primary.get('voice_id', 'N/A')}</div>
        </div>
        <div class="bg-gray-50 p-3 rounded border-l-4 border-teal-500">
            <div class="font-medium">🎤 Secondary: {secondary.get('name', 'N/A')}</div>
            <div class="text-xs text-gray-600 mt-1">ID: {secondary.get('voice_id', 'N/A')}</div>
        </div>
        """
    
    def _safe_text(self, text: str, max_length: int = 1000) -> str:
        """Sichere Text-Verarbeitung"""
        if not text:
            return 'No data available'
        
        # HTML escape
        import html
        escaped = html.escape(str(text))
        
        # Truncate
        if len(escaped) > max_length:
            return escaped[:max_length] + '...'
        
        return escaped 