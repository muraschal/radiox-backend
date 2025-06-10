import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
from loguru import logger

class TailwindDashboardService:
    """
    🎨 CLEAN Tailwind CSS Dashboard für RadioX Show Notes
    CDN-BASED - EINFACH & FUNKTIONAL
    """
    
    def __init__(self):
        """Initialisiert den Dashboard Service"""
        self.output_dir = "outplay"  # Keep outplay for dashboard - temp for assets
        os.makedirs(self.output_dir, exist_ok=True)
        logger.info("📊 Tailwind Dashboard Service initialisiert")
        self._rss_feeds_cache = None  # Cache for RSS feeds from DB
    
    async def generate_shownotes_dashboard(
        self, 
        raw_data: Dict[str, Any], 
        processed_data: Dict[str, Any], 
        show_config: Dict[str, Any],
        timestamp: Optional[str] = None
    ) -> str:
        """Generiert das Show Notes Dashboard"""
        try:
            logger.info("🎨 Generiere Tailwind Show Notes Dashboard...")
            
            # SAFETY: Null-Prüfungen für robuste Dashboard-Generation
            if raw_data is None:
                raw_data = {'news': [], 'weather': {}, 'crypto': {}}
                logger.warning("⚠️ raw_data war None - verwende leere Defaults")
            
            if processed_data is None:
                processed_data = {'radio_script': '', 'selected_news': [], 'quality_score': 0.0}
                logger.warning("⚠️ processed_data war None - verwende leere Defaults")
            
            if show_config is None:
                show_config = {'hosts': [], 'target_time': '4 minutes'}
                logger.warning("⚠️ show_config war None - verwende leere Defaults")
            
            # Load RSS feeds from DB for correct links
            rss_feeds_mapping = await self._get_rss_feeds_from_db()
            
            # Extract processing data
            processed_info = self._extract_processing_data(processed_data)
            
            # Calculate stats
            stats = self._calculate_dashboard_stats(raw_data, processed_info)
            
            # Use provided timestamp or generate a new one (unified format)
            if timestamp is None:
                timestamp = datetime.now().strftime('%y%m%d_%H%M')
            
            # Generate HTML
            html_content = self._generate_tailwind_html(
                raw_data, processed_info, show_config, stats, timestamp, rss_feeds_mapping
            )
            
            # Save to file (unified naming)
            filename = f"radiox_{timestamp}.html"
            filepath = os.path.join(self.output_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            logger.info(f"✅ Tailwind Dashboard generiert: {filename}")
            return filepath
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Generieren des Dashboards: {e}")
            raise
    
    def _extract_processing_data(self, processed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extrahiert die verarbeiteten Daten - VOLLSTÄNDIG für GPT Stream-Erstellung"""
        # SAFETY: Handle None case
        if processed_data is None:
            processed_data = {}
        
        extracted = {
            'gpt_prompt': processed_data.get('gpt_prompt', ''),
            'radio_script': processed_data.get('radio_script', ''),
            'selected_news': processed_data.get('selected_news', []),
            'segments': processed_data.get('segments', []),
            'processing_info': processed_data.get('processing_info', {}),
            'prepared_data': processed_data.get('prepared_data', {}),
            'all_news': processed_data.get('all_news', []),
            'show_details': processed_data.get('show_details', {}),
            'content_focus': processed_data.get('content_focus', {}),
            'quality_score': processed_data.get('quality_score', 0.0),
            'target_time': processed_data.get('target_time', ''),
            'preset_name': processed_data.get('preset_name', ''),
            'processing_timestamp': processed_data.get('processing_timestamp', ''),
            'generated_by': processed_data.get('generated_by', ''),
            'weather_data': processed_data.get('weather_data', {}),
            'crypto_data': processed_data.get('crypto_data', {})
        }
        
        # Extract ALL fields that might contain image/cover generation data
        for key, value in processed_data.items():
            if any(keyword in key.lower() for keyword in ['image', 'cover', 'dalle', 'generation']):
                extracted[key] = value
        
        return extracted
    
    def _calculate_dashboard_stats(self, raw_data: Dict[str, Any], processed_info: Dict[str, Any]) -> Dict[str, Any]:
        """Berechnet Dashboard-Statistiken"""
        # SAFETY: Handle None cases
        if raw_data is None:
            raw_data = {}
        if processed_info is None:
            processed_info = {}
            
        news = raw_data.get('news', [])
        weather = raw_data.get('weather', {})
        crypto = raw_data.get('crypto', {})
        
        return {
            'total_news': len(news),
            'selected_news': len(processed_info.get('selected_news', [])),
            'total_sources': len(set(item.get('source', 'unknown') for item in news)),
            'gpt_words': len(processed_info.get('radio_script', '').split()),
            'weather_temp': self._get_weather_value(weather, 'temperature'),
            'bitcoin_price': crypto.get('bitcoin', {}).get('price_usd', 0)
        }
    
    def _generate_tailwind_html(
        self, 
        raw_data: Dict[str, Any], 
        processed_info: Dict[str, Any], 
        show_config: Dict[str, Any], 
        stats: Dict[str, Any],
        timestamp: str,
        rss_feeds_mapping: Dict[str, str]
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
            <p class="text-blue-200 mt-2">Tailwind Dashboard • {timestamp}</p>
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

    <!-- GPT Selected Articles - PROMINENT HEADER SECTION -->
    <div class="bg-green-600 text-white py-6">
        <div class="max-w-7xl mx-auto px-4">
            <h2 class="text-2xl font-bold mb-4">🤖 GPT Selected Articles ({len(processed_info.get('selected_news', []))} stories)</h2>
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {self._generate_selected_news_header_cards(processed_info.get('selected_news', []))}
            </div>
        </div>
    </div>

    <!-- Audio Player Section -->
    {self._generate_audio_player_html(timestamp)}

    <!-- Main Content -->
    <div class="max-w-7xl mx-auto px-4 py-8">
        <div class="grid grid-cols-12 gap-6">
            
            <!-- NEWS COLUMN (8/12) -->
            <div class="col-span-8">
                <div class="bg-white rounded-lg shadow-sm">
                    <div class="bg-blue-600 text-white px-6 py-4 rounded-t-lg">
                        <h2 class="text-xl font-bold">📰 All Available News ({stats['total_news']} articles)</h2>
                        <p class="text-blue-200 text-sm mt-1">Complete news feed • Selected articles shown above</p>
                    </div>
                    
                    <!-- Filter Buttons -->
                    <div class="p-4 bg-gray-50 border-b">
                        <div class="flex flex-wrap gap-2">
                            <button class="filter-btn px-3 py-1 text-sm rounded-full bg-blue-600 text-white" data-filter="all">Alle</button>
                            <button class="filter-btn px-3 py-1 text-sm rounded-full bg-gray-200 hover:bg-gray-300" data-filter="zurich">Zürich</button>
                            <button class="filter-btn px-3 py-1 text-sm rounded-full bg-gray-200 hover:bg-gray-300" data-filter="tech">Tech</button>
                            <button class="filter-btn px-3 py-1 text-sm rounded-full bg-gray-200 hover:bg-gray-300" data-filter="bitcoin">Bitcoin</button>
                        </div>
                    </div>
                    
                    <!-- All News List -->
                    <div class="p-4 max-h-96 overflow-y-auto space-y-3" id="news-container">
                        {self._generate_news_html(news, rss_feeds_mapping)}
                    </div>
                </div>
            </div>

            <!-- SIDEBAR (4/12) -->
            <div class="col-span-4 space-y-6">

                <!-- Voice Config -->
                <div class="bg-white rounded-lg shadow-sm">
                    <div class="bg-teal-600 text-white px-4 py-3 rounded-t-lg">
                        <h3 class="font-bold">🎤 Voice Configuration</h3>
                    </div>
                    <div class="p-4 text-sm space-y-3">
                        {self._generate_voice_html(show_config)}
                    </div>
                </div>

                <!-- Weather Card - INTELLIGENT GPT SUMMARY -->
                <div class="bg-white rounded-lg shadow-sm">
                    <div class="bg-orange-500 text-white px-4 py-3 rounded-t-lg">
                        <h3 class="font-bold">🌤️ Weather Intelligence</h3>
                        <div class="text-xs text-orange-200">GPT-powered time-aware analysis</div>
                    </div>
                    <div class="p-4">
                        <div class="bg-orange-50 border border-orange-200 p-3 rounded">
                            <div class="text-sm text-orange-800 leading-relaxed">
                                {weather.get('current_summary', 'Weather intelligence not available')}
                            </div>
                        </div>
                        <div class="mt-3 text-xs text-gray-600 flex justify-between">
                            <span>Zürich</span>
                            <span>Live Analysis</span>
                        </div>
                    </div>
                </div>
                
                <!-- Bitcoin Card - INTELLIGENT GPT SUMMARY -->
                <div class="bg-white rounded-lg shadow-sm">
                    <div class="bg-yellow-500 text-white px-4 py-3 rounded-t-lg">
                        <h3 class="font-bold">₿ Bitcoin Intelligence</h3>
                        <div class="text-xs text-yellow-200">GPT-powered market analysis with delta relevance</div>
                    </div>
                    <div class="p-4">
                        <div class="bg-yellow-50 border border-yellow-200 p-3 rounded">
                            <div class="text-sm text-yellow-800 leading-relaxed">
                                {crypto.get('bitcoin_summary', 'Bitcoin intelligence not available')}
                            </div>
                        </div>
                        <div class="mt-3 text-xs text-gray-600 flex justify-between">
                            <span>Market Analysis</span>
                            <span>Live Intelligence</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- GPT Stream Information Section (VOLLSTÄNDIG für Stream-Erstellung) -->
        <div class="mt-8">
            <div class="bg-white rounded-lg shadow-sm">
                <div class="bg-purple-600 text-white px-6 py-4 rounded-t-lg">
                    <h2 class="text-xl font-bold">🤖 GPT Stream Information - ALLE DATEN FÜR STREAM</h2>
                    <p class="text-purple-200 text-sm mt-1">Vollständige Informationen für GPT Stream-Erstellung • Quality: {processed_info.get('quality_score', 0.0)} • Model: {processed_info.get('generated_by', 'GPT-4')}</p>
                </div>
                
                <!-- Main GPT Content Grid -->
                <div class="p-6">
                    <h3 class="text-lg font-medium text-gray-800 mb-4">🤖 Complete GPT Workflow Debug</h3>
                    
                    <!-- 2x3 GPT WORKFLOW GRID: INPUT LEFT, OUTPUT RIGHT -->
                    <div class="grid grid-cols-2 gap-6 mb-6">
                        <!-- LEFT COLUMN: INPUTS -->
                        <div class="space-y-6">
                            <!-- Stage 1: Article Selection Prompt -->
                            <div>
                                <div class="flex justify-between items-center mb-3">
                                    <h4 class="font-medium text-gray-700">📋 Stage 1: Article Selection Prompt</h4>
                                    <button onclick="copyToClipboard('stage1-prompt')" class="px-2 py-1 text-xs bg-purple-100 hover:bg-purple-200 text-purple-800 rounded">📋 Copy</button>
                                </div>
                                <div class="text-xs text-gray-500 mb-2">INPUT: Expects JSON response with selected article IDs</div>
                                <div id="stage1-prompt" class="bg-gray-900 text-purple-400 p-4 rounded text-sm font-mono max-h-80 overflow-y-auto whitespace-pre-wrap">{self._safe_text_full(self._get_stage1_prompt(processed_info))}</div>
                            </div>
                            
                            <!-- Stage 2: Script Writing Prompt -->
                            <div>
                                <div class="flex justify-between items-center mb-3">
                                    <h4 class="font-medium text-gray-700">📝 Stage 2: Script Writing Prompt</h4>
                                    <button onclick="copyToClipboard('stage2-prompt')" class="px-2 py-1 text-xs bg-green-100 hover:bg-green-200 text-green-800 rounded">📋 Copy</button>
                                </div>
                                <div class="text-xs text-gray-500 mb-2">INPUT: Expects plain text radio script response</div>
                                <div id="stage2-prompt" class="bg-gray-900 text-green-400 p-4 rounded text-sm font-mono max-h-80 overflow-y-auto whitespace-pre-wrap">{self._safe_text_full(self._get_stage2_prompt(processed_info))}</div>
                            </div>
                            
                            <!-- Image Generation Prompt -->
                            <div>
                                <div class="flex justify-between items-center mb-3">
                                    <h4 class="font-medium text-gray-700">🎨 Image Generation Prompt</h4>
                                    <button onclick="copyToClipboard('image-prompt')" class="px-2 py-1 text-xs bg-pink-100 hover:bg-pink-200 text-pink-800 rounded">📋 Copy</button>
                                </div>
                                <div class="text-xs text-gray-500 mb-2">INPUT: DALL-E prompt for cover generation</div>
                                <div id="image-prompt" class="bg-gray-900 text-pink-400 p-4 rounded text-sm font-mono max-h-80 overflow-y-auto whitespace-pre-wrap">{self._safe_text_full(self._get_image_prompt(processed_info))}</div>
                            </div>
                        </div>
                        
                        <!-- RIGHT COLUMN: OUTPUTS -->
                        <div class="space-y-6">
                            <!-- Stage 1: GPT Response -->
                            <div>
                                <div class="flex justify-between items-center mb-3">
                                    <h4 class="font-medium text-gray-700">🤖 Stage 1: GPT Response</h4>
                                    <button onclick="copyToClipboard('stage1-response')" class="px-2 py-1 text-xs bg-cyan-100 hover:bg-cyan-200 text-cyan-800 rounded">📋 Copy</button>
                                </div>
                                <div class="text-xs text-gray-500 mb-2">OUTPUT: Selected articles + reasons</div>
                                <div id="stage1-response" class="bg-gray-900 text-cyan-400 p-4 rounded text-sm font-mono max-h-80 overflow-y-auto whitespace-pre-wrap">{self._safe_text_full(self._get_stage1_response(processed_info))}</div>
                            </div>
                            
                            <!-- Stage 2: Generated Radio Script -->
                            <div>
                                <div class="flex justify-between items-center mb-3">
                                    <h4 class="font-medium text-gray-700">🎭 Stage 2: Generated Radio Script</h4>
                                    <button onclick="copyToClipboard('radio-script')" class="px-2 py-1 text-xs bg-blue-100 hover:bg-blue-200 text-blue-800 rounded">📋 Copy</button>
                                </div>
                                <div class="text-xs text-gray-500 mb-2">OUTPUT: GPT's final radio script response</div>
                                <div id="radio-script" class="bg-gray-900 text-blue-400 p-4 rounded text-sm font-mono max-h-80 overflow-y-auto whitespace-pre-wrap">{self._safe_text_full(processed_info.get('radio_script', 'No radio script'))}</div>
                            </div>
                            
                            <!-- Returned Image Prompt -->
                            <div>
                                <div class="flex justify-between items-center mb-3">
                                    <h4 class="font-medium text-gray-700">🖼️ Returned Image Prompt</h4>
                                    <button onclick="copyToClipboard('returned-image-prompt')" class="px-2 py-1 text-xs bg-orange-100 hover:bg-orange-200 text-orange-800 rounded">📋 Copy</button>
                                </div>
                                <div class="text-xs text-gray-500 mb-2">OUTPUT: Final prompt used by DALL-E</div>
                                <div id="returned-image-prompt" class="bg-gray-900 text-orange-400 p-4 rounded text-sm font-mono max-h-80 overflow-y-auto whitespace-pre-wrap">{self._safe_text_full(self._get_returned_image_prompt(processed_info))}</div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Selected News & Segments -->
                <div class="border-t border-gray-200 p-6 grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <div>
                        <div class="flex justify-between items-center mb-3">
                            <h3 class="font-medium text-gray-700">✅ Selected News ({len(processed_info.get('selected_news', []))} articles)</h3>
                            <button onclick="copyToClipboard('selected-news')" class="px-2 py-1 text-xs bg-green-100 hover:bg-green-200 text-green-800 rounded">📋 Copy</button>
                        </div>
                        <div id="selected-news" class="bg-green-50 border border-green-200 p-4 rounded text-sm max-h-80 overflow-y-auto">{self._format_selected_news_for_display(processed_info.get('selected_news', []))}</div>
                    </div>
                    <div>
                        <div class="flex justify-between items-center mb-3">
                            <h3 class="font-medium text-gray-700">🎯 Radio Segments ({len(processed_info.get('segments', []))} segments)</h3>
                            <button onclick="copyToClipboard('radio-segments')" class="px-2 py-1 text-xs bg-indigo-100 hover:bg-indigo-200 text-indigo-800 rounded">📋 Copy</button>
                        </div>
                        <div id="radio-segments" class="bg-indigo-50 border border-indigo-200 p-4 rounded text-sm max-h-80 overflow-y-auto">{self._format_segments_for_display(processed_info.get('segments', []))}</div>
                    </div>
                </div>
                
                <!-- Context Data for Stream -->
                <div class="border-t border-gray-200 p-6 grid grid-cols-1 lg:grid-cols-3 gap-6">
                    <div>
                        <div class="flex justify-between items-center mb-3">
                            <h3 class="font-medium text-gray-700">🎪 Show Context</h3>
                            <button onclick="copyToClipboard('show-context')" class="px-2 py-1 text-xs bg-teal-100 hover:bg-teal-200 text-teal-800 rounded">📋 Copy</button>
                        </div>
                        <div id="show-context" class="bg-teal-50 border border-teal-200 p-4 rounded text-sm max-h-80 overflow-y-auto font-mono whitespace-pre-wrap">{self._format_show_context_for_display(processed_info)}</div>
                    </div>
                    <div>
                        <div class="flex justify-between items-center mb-3">
                            <h3 class="font-medium text-gray-700">🌦️ Live Data Context</h3>
                            <button onclick="copyToClipboard('live-context')" class="px-2 py-1 text-xs bg-orange-100 hover:bg-orange-200 text-orange-800 rounded">📋 Copy</button>
                        </div>
                        <div id="live-context" class="bg-orange-50 border border-orange-200 p-4 rounded text-sm max-h-80 overflow-y-auto font-mono whitespace-pre-wrap">{self._format_live_context_for_display(raw_data, processed_info)}</div>
                    </div>
                    <div>
                        <div class="flex justify-between items-center mb-3">
                            <h3 class="font-medium text-gray-700">⚡ Processing Meta</h3>
                            <button onclick="copyToClipboard('processing-meta')" class="px-2 py-1 text-xs bg-gray-100 hover:bg-gray-200 text-gray-800 rounded">📋 Copy</button>
                        </div>
                        <div id="processing-meta" class="bg-gray-50 border border-gray-200 p-4 rounded text-sm max-h-80 overflow-y-auto font-mono whitespace-pre-wrap">{self._format_processing_meta_for_display(processed_info)}</div>
                    </div>
                </div>
                
                <!-- GPT Filter Logic Section (WICHTIG für Stream-Verständnis) -->
                <div class="border-t border-gray-200 p-6">
                    <div class="mb-4">
                        <h3 class="text-lg font-medium text-gray-800 mb-2">📊 GPT Input Filter Logic</h3>
                        <p class="text-sm text-gray-600">So werden die News für GPT gefiltert und ausgewählt (keine Supabase, nur zeitbasiert!)</p>
                    </div>
                    
                    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                        <div>
                            <div class="flex justify-between items-center mb-3">
                                <h4 class="font-medium text-gray-700">🔍 Filter-Regeln & Statistiken</h4>
                                <button onclick="copyToClipboard('filter-rules')" class="px-2 py-1 text-xs bg-blue-100 hover:bg-blue-200 text-blue-800 rounded">📋 Copy</button>
                            </div>
                            <div id="filter-rules" class="bg-blue-50 border border-blue-200 p-4 rounded text-sm font-mono whitespace-pre-wrap">{self._format_gpt_filter_rules_for_display(raw_data, processed_info)}</div>
                        </div>
                        <div>
                            <div class="flex justify-between items-center mb-3">
                                <h4 class="font-medium text-gray-700">📰 Gesendete News an GPT (Top 15)</h4>
                                <button onclick="copyToClipboard('gpt-input-news')" class="px-2 py-1 text-xs bg-purple-100 hover:bg-purple-200 text-purple-800 rounded">📋 Copy</button>
                            </div>
                            <div id="gpt-input-news" class="bg-purple-50 border border-purple-200 p-4 rounded text-sm max-h-80 overflow-y-auto">{self._format_gpt_input_news_for_display(processed_info)}</div>
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
        
        // Copy to clipboard functionality
        function copyToClipboard(elementId) {{
            const element = document.getElementById(elementId);
            const text = element.textContent;
            
            // Use modern clipboard API if available
            if (navigator.clipboard) {{
                navigator.clipboard.writeText(text).then(() => {{
                    showCopyNotification(`Copied ${{elementId}} to clipboard!`);
                }}).catch(err => {{
                    console.error('Failed to copy: ', err);
                    fallbackCopyToClipboard(text);
                }});
            }} else {{
                fallbackCopyToClipboard(text);
            }}
        }}
        
        // Fallback for older browsers
        function fallbackCopyToClipboard(text) {{
            const textArea = document.createElement('textarea');
            textArea.value = text;
            textArea.style.position = 'fixed';
            textArea.style.left = '-999999px';
            textArea.style.top = '-999999px';
            document.body.appendChild(textArea);
            textArea.focus();
            textArea.select();
            
            try {{
                document.execCommand('copy');
                showCopyNotification('Copied to clipboard!');
            }} catch (err) {{
                console.error('Fallback: Unable to copy', err);
                showCopyNotification('Copy failed - try selecting and copying manually');
            }}
            
            document.body.removeChild(textArea);
        }}
        
        // Show copy notification
        function showCopyNotification(message) {{
            const notification = document.createElement('div');
            notification.textContent = message;
            notification.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                background: #22c55e;
                color: white;
                padding: 12px 20px;
                border-radius: 8px;
                z-index: 10000;
                font-size: 14px;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            `;
            
            document.body.appendChild(notification);
            
            setTimeout(() => {{
                notification.style.opacity = '0';
                notification.style.transition = 'opacity 0.3s ease';
                setTimeout(() => {{
                    document.body.removeChild(notification);
                }}, 300);
            }}, 2000);
        }}
        
        // Make functions globally available
        window.copyToClipboard = copyToClipboard;
    </script>
</body>
</html>"""

    def _generate_news_html(self, news: List[Dict[str, Any]], rss_feeds_mapping: Dict[str, str] = None) -> str:
        """Generiert News HTML mit korrekten Links"""
        html = ""
        for item in news:
            title = item.get('title', 'No title')
            summary = item.get('summary', '')
            source = item.get('source', 'Unknown')
            category = item.get('category', 'general')
            age = item.get('age_hours', 0)
            url = item.get('link', item.get('url', '#'))  # Verwende 'link' falls 'url' nicht verfügbar
            
            # Clean summary and fix images
            clean_summary = self._clean_summary_with_fixed_images(summary)
            short_summary = clean_summary
            
            # Generate RSS link based on source
            # RSS Link (echte URL aus DB)
            rss_link = self._generate_rss_link_sync(source, category, rss_feeds_mapping or {})
            
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
                <div class="flex gap-3">
                    <a href="{url}" target="_blank" class="text-blue-600 hover:text-blue-800 text-sm">🔗 Read article</a>
                    {f'<a href="{rss_link}" target="_blank" class="text-orange-600 hover:text-orange-800 text-sm">📡 RSS Feed</a>' if rss_link else ''}
                </div>
            </div>
            """
        return html
    
    def _generate_selected_news_header_cards(self, selected_news: List[Dict[str, Any]]) -> str:
        """Generates compact header cards for selected news"""
        if not selected_news:
            return '<div class="col-span-4 text-center text-green-200">No articles selected</div>'
        
        cards_html = ""
        for i, news in enumerate(selected_news, 1):
            title = news.get('title', 'No title')
            source = news.get('source', 'Unknown').upper()
            reason = news.get('relevance_reason', news.get('selection_reason', 'Selected by GPT'))
            
            # Truncate for header display
            short_title = title[:60] + "..." if len(title) > 60 else title
            short_reason = reason[:80] + "..." if len(reason) > 80 else reason
            
            cards_html += f"""
            <div class="bg-green-700 rounded-lg p-4 border border-green-500">
                <div class="flex items-center justify-between mb-2">
                    <span class="bg-green-800 text-green-100 px-2 py-1 rounded text-xs font-bold">#{i}</span>
                    <span class="bg-white text-green-700 px-2 py-1 rounded text-xs font-bold">{source}</span>
                </div>
                <h3 class="text-white font-semibold text-sm mb-2 leading-tight">{short_title}</h3>
                <p class="text-green-200 text-xs leading-relaxed">{short_reason}</p>
            </div>
            """
        
        return cards_html
    
    def _generate_selected_news_section(self, selected_news: List[Dict[str, Any]], rss_feeds_mapping: Dict[str, str] = None) -> str:
        """Generiert prominente Sektion für GPT-selected News"""
        if not selected_news:
            return ""
        
        html = f"""
                    <!-- GPT SELECTED NEWS - PROMINENT SECTION -->
                    <div class="p-4 bg-green-50 border-b-2 border-green-200">
                        <div class="flex items-center gap-2 mb-3">
                            <span class="text-green-600 text-lg">🤖</span>
                            <h3 class="font-bold text-green-800">GPT Selected News ({len(selected_news)} articles)</h3>
                            <span class="px-2 py-1 text-xs bg-green-200 text-green-700 rounded-full">FEATURED</span>
                        </div>
                        <div class="space-y-3">
        """
        
        for i, item in enumerate(selected_news, 1):
            title = item.get('title', 'No title')
            summary = item.get('summary', '')
            source = item.get('source', 'Unknown')
            category = item.get('category', 'general')
            age = item.get('age_hours', 0)
            url = item.get('link', item.get('url', '#'))
            reason = item.get('relevance_reason', item.get('selection_reason', 'Selected by GPT'))
            
            # Clean summary
            clean_summary = self._clean_summary_with_fixed_images(summary)
            short_summary = clean_summary[:200] + '...' if len(clean_summary) > 200 else clean_summary
            
            # Generate RSS link
            rss_link = self._generate_rss_link_sync(source, category, rss_feeds_mapping or {})
            
            html += f"""
                            <div class="bg-white p-4 border-2 border-green-300 rounded-lg shadow-sm">
                                <div class="flex items-start justify-between mb-2">
                                    <div class="flex flex-wrap gap-2">
                                        <span class="px-2 py-1 text-xs font-bold rounded bg-green-100 text-green-800">#{i}</span>
                                        <span class="px-2 py-1 text-xs font-medium rounded bg-blue-100 text-blue-800">{source}</span>
                                        <span class="px-2 py-1 text-xs rounded bg-gray-100 text-gray-700">{category}</span>
                                        <span class="px-2 py-1 text-xs rounded bg-gray-100 text-gray-600">{age:.1f}h ago</span>
                                    </div>
                                </div>
                                <h4 class="font-bold text-gray-900 mb-2 text-lg">{title}</h4>
                                <p class="text-gray-600 text-sm mb-2">{short_summary}</p>
                                <div class="bg-green-100 border border-green-300 p-2 rounded mb-3">
                                    <span class="text-xs font-medium text-green-700">GPT Selection Reason:</span>
                                    <p class="text-sm text-green-800 mt-1">{reason}</p>
                                </div>
                                <div class="flex gap-3">
                                    <a href="{url}" target="_blank" class="text-blue-600 hover:text-blue-800 text-sm font-medium">🔗 Read article</a>
                                    {f'<a href="{rss_link}" target="_blank" class="text-orange-600 hover:text-orange-800 text-sm">📡 RSS Feed</a>' if rss_link else ''}
                                </div>
                            </div>
            """
        
        html += """
                        </div>
                    </div>
        """
        
        return html
    
    async def _get_rss_feeds_from_db(self) -> Dict[str, str]:
        """Lädt echte RSS Feed URLs aus der Supabase Datenbank"""
        if self._rss_feeds_cache is not None:
            return self._rss_feeds_cache
        
        try:
            from database.supabase_client import get_db
            db = get_db()
            
            # FIXED: Lade auch feed_category um richtige Zuordnung zu ermöglichen
            response = db.client.table('rss_feed_preferences').select('source_name, feed_url, feed_category').eq('is_active', True).execute()
            
            # Create mapping: "source_category" -> feed_url (z.B. "20min_zurich" -> URL)
            feeds_mapping = {}
            for feed in response.data or []:
                source_name = feed.get('source_name', '').lower()
                feed_category = feed.get('feed_category', '').lower()
                feed_url = feed.get('feed_url', '')
                
                if source_name and feed_category and feed_url:
                    # Kombiniere source + category für eindeutige Zuordnung
                    key = f"{source_name}_{feed_category}"
                    feeds_mapping[key] = feed_url
                    
                    # Zusätzlich: Fallback mit nur source_name (für Kompatibilität)
                    if source_name not in feeds_mapping:
                        feeds_mapping[source_name] = feed_url
            
            self._rss_feeds_cache = feeds_mapping
            logger.debug(f"📡 {len(feeds_mapping)} RSS Feeds aus DB geladen (inkl. category-spezifische)")
            return feeds_mapping
            
        except Exception as e:
            logger.error(f"❌ RSS Feeds aus DB laden fehlgeschlagen: {e}")
            return {}

    def _generate_rss_link_sync(self, source: str, category: str, feeds_mapping: Dict[str, str]) -> str:
        """Sucht die passende RSS-Feed-URL aus dem Mapping."""
        # Kombinierter Schlüssel für präzisere Übereinstimmung
        combined_key = f"{source.lower()}+{category.lower()}"
        
        url = feeds_mapping.get(combined_key, "#")
        # logger.debug(f"✅ RSS Feed gefunden: {source}+{category} -> {feeds_mapping.get(combined_key, 'Nicht gefunden')}")
        return url
    
    def _generate_voice_html(self, show_config: Dict[str, Any]) -> str:
        """Generiert HTML für die Stimmen-Konfiguration mit korrekten Daten."""
        # Correctly access speaker data from the show_config structure
        primary_speaker = show_config.get('speaker', {})
        secondary_speaker = show_config.get('secondary_speaker', {})
        
        html = ""

        def create_speaker_block(speaker_data, role):
            if not speaker_data:
                return ""
            name = speaker_data.get('voice_name', 'N/A')
            description = speaker_data.get('description', 'No description available.')
            return f"""
            <div>
                <span class="font-semibold text-gray-700">{role}: {name}</span>
                <p class="text-xs text-gray-500 mt-1">{description}</p>
            </div>
            """

        html += create_speaker_block(primary_speaker, "Primary Host")
        if secondary_speaker:
            html += create_speaker_block(secondary_speaker, "Secondary Host")

        if not html:
            return "<p>Voice configuration not available.</p>"

        return html
    
    def _generate_alerts_html(self, crypto: Dict[str, Any], weather: Dict[str, Any]) -> str:
        """Generiert Alerts und Empfehlungen HTML"""
        html = ""
        
        # Bitcoin Alerts
        bitcoin_alerts = crypto.get('alerts', [])
        if bitcoin_alerts:
            for alert in bitcoin_alerts:
                alert_type = alert.get('type', 'info')
                message = alert.get('message', 'No message')
                
                if alert_type == 'price_threshold':
                    icon = '💰'
                    bg_color = 'bg-yellow-50'
                    text_color = 'text-yellow-800'
                else:
                    icon = '🔔'
                    bg_color = 'bg-blue-50'
                    text_color = 'text-blue-800'
                
                html += f"""
                <div class="{bg_color} p-3 rounded border-l-4 border-yellow-500">
                    <div class="flex items-start space-x-2">
                        <span class="text-lg">{icon}</span>
                        <div class="text-sm {text_color}">{message}</div>
                    </div>
                </div>
                """
        
        # Bitcoin Trend
        trend_data = crypto.get('trend', {})
        if trend_data:
            trend_emoji = trend_data.get('emoji', '📈')
            trend_message = trend_data.get('message', 'No trend data')
            
            html += f"""
            <div class="bg-green-50 p-3 rounded border-l-4 border-green-500">
                <div class="flex items-start space-x-2">
                    <span class="text-lg">{trend_emoji}</span>
                    <div class="text-sm text-green-800">{trend_message}</div>
                </div>
            </div>
            """
        
        # Weather Recommendations (basierend auf aktuellen Daten)
        temp = weather.get('temperature', 0)
        humidity = weather.get('humidity', 0)
        description = weather.get('description', '').lower()
        
        weather_tip = self._generate_weather_tip(temp, humidity, description)
        if weather_tip:
            html += f"""
            <div class="bg-blue-50 p-3 rounded border-l-4 border-blue-500">
                <div class="flex items-start space-x-2">
                    <span class="text-lg">🌤️</span>
                    <div class="text-sm text-blue-800">{weather_tip}</div>
                </div>
            </div>
            """
        
        return html or "<div class='text-gray-500 text-sm'>No alerts available</div>"
    
    def _generate_weather_tip(self, temp: float, humidity: int, description: str) -> str:
        """Generiert Wetter-Empfehlungen basierend auf aktuellen Bedingungen"""
        
        if temp < 10:
            return "🧥 Cold weather! Don't forget your jacket and warm clothes."
        elif temp > 25:
            return "☀️ Perfect weather for outdoor activities! Stay hydrated."
        elif 'rain' in description or 'shower' in description:
            return "☔ Rain expected. Don't forget your umbrella!"
        elif humidity > 80:
            return "💧 High humidity today. Stay cool and drink plenty of water."
        elif 'clear' in description or 'sun' in description:
            return "🌞 Beautiful clear skies! Great day for a walk in the city."
        elif 'cloud' in description:
            return "☁️ Partly cloudy - comfortable weather for outdoor activities."
        else:
            return f"🌡️ Current conditions: {description}. Enjoy your day in Zürich!"
    
    def _clean_summary_with_fixed_images(self, summary: str) -> str:
        """Reinigt Summary Text und entfernt ALLE HTML-Elemente inkl. Bilder"""
        if not summary:
            return 'No summary available'
        
        import re
        
        # FIXED: Vollständige HTML-Bereinigung
        # 1. Entferne img tags komplett (inkl. alle Attribute)
        clean_text = re.sub(r'<img[^>]*?>', '', summary, flags=re.IGNORECASE | re.DOTALL)
        
        # 2. Entferne style attributes und float-Definitionen
        clean_text = re.sub(r'style\s*=\s*"[^"]*?"', '', clean_text, flags=re.IGNORECASE)
        clean_text = re.sub(r'float\s*:\s*[^;]*?;?', '', clean_text, flags=re.IGNORECASE)
        
        # 3. Entferne problematische HTML paragraph/div tags aber behalte Inhalt
        clean_text = re.sub(r'</?p[^>]*?>', ' ', clean_text, flags=re.IGNORECASE)
        clean_text = re.sub(r'</?div[^>]*?>', ' ', clean_text, flags=re.IGNORECASE)
        
        # 4. Entferne ALLE verbleibenden HTML tags
        clean_text = re.sub(r'<[^>]+>', '', clean_text)
        
        # 5. Bereinige HTML-Entities
        import html
        clean_text = html.unescape(clean_text)
        
        # 6. Bereinige Whitespace und Zeilenumbrüche
        clean_text = ' '.join(clean_text.split())
        
        return clean_text.strip()
    
    def _safe_text(self, text: str, max_length: int = 10000) -> str:
        """Sichere Text-Verarbeitung - KEIN LIMIT FÜR RADIO SCRIPT"""
        if not text:
            return 'No data available'
        
        # HTML escape
        import html
        escaped = html.escape(str(text))
        
        # Für Radio Script: Kein Truncate!
        # Nur für andere Texte beschränken
        if 'MARCEL:' in escaped or 'JARVIS:' in escaped or 'LUCY:' in escaped:
            return escaped  # Radio Script - VOLLSTÄNDIG anzeigen
        
        # Für andere Texte normal kürzen
        if len(escaped) > max_length:
            return escaped[:max_length] + '...'
        
        return escaped
    
    def _safe_text_full(self, text: str) -> str:
        """Sichere Text-Verarbeitung ohne Kürzung"""
        if not text:
            return 'No data available'
        
        # HTML escape
        import html
        escaped = html.escape(str(text))
        
        return escaped
    
    def _generate_weather_alerts_html(self, weather: Dict[str, Any]) -> str:
        """Generiert Weather-spezifische Alerts"""
        temp = weather.get('temperature', 0)
        humidity = weather.get('humidity', 0)
        description = weather.get('description', '').lower()
        
        weather_tip = self._generate_weather_tip(temp, humidity, description)
        if weather_tip:
            return f"""
            <div class="bg-blue-50 p-2 rounded border-l-4 border-blue-500">
                <div class="text-sm text-blue-800">{weather_tip}</div>
            </div>
            """
        return ""
    
    def _generate_bitcoin_alerts_html(self, crypto: Dict[str, Any]) -> str:
        """Generiert Bitcoin-spezifische Alerts"""
        bitcoin = crypto.get('bitcoin', {})
        if not bitcoin:
            return '<div class="text-gray-500 text-xs">No Bitcoin data</div>'
            
        alerts = []
        price_change = bitcoin.get('change_24h', 0)
        week_change = bitcoin.get('change_7d', 0)
        
        if abs(price_change) > 5:
            icon = "🚀" if price_change > 0 else "📉"
            alerts.append(f'{icon} {price_change:+.1f}% (24h)')
        
        if abs(week_change) > 10:
            icon = "📈" if week_change > 0 else "⚠️"
            alerts.append(f'{icon} {week_change:+.1f}% (7d)')
            
        if alerts:
            return f'<div class="space-y-1 text-xs">{"<br>".join(alerts)}</div>'
        else:
            return '<div class="text-yellow-600 text-xs">📊 Stable</div>'

    def _format_selected_news_for_display(self, selected_news: List[Dict[str, Any]]) -> str:
        """Formatiert ausgewählte News für Anzeige"""
        if not selected_news:
            return "Keine News ausgewählt"
        
        formatted = []
        for i, news in enumerate(selected_news, 1):
            title = news.get('title', 'No title')
            source = news.get('source', 'Unknown')
            reason = news.get('relevance_reason', 'No reason given')
            
            formatted.append(f"{i}. [{source}] {title}\n   Grund: {reason}\n")
        
        return "\n".join(formatted)

    def _format_segments_for_display(self, segments: List[Dict[str, Any]]) -> str:
        """Formatiert Radio-Segmente für Anzeige"""
        if not segments:
            return "Keine Segmente vorhanden"
        
        formatted = []
        for i, segment in enumerate(segments, 1):
            seg_type = segment.get('type', 'unknown').upper()
            content = segment.get('content', 'No content')[:200] + '...' if len(segment.get('content', '')) > 200 else segment.get('content', 'No content')
            news_title = segment.get('news_title', '')
            
            if news_title:
                formatted.append(f"{i}. {seg_type} - {news_title}\n   {content}\n")
            else:
                formatted.append(f"{i}. {seg_type}\n   {content}\n")
        
        return "\n".join(formatted)

    def _format_show_context_for_display(self, processed_info: Dict[str, Any]) -> str:
        """Formatiert Show-Kontext für Anzeige"""
        context_parts = []
        
        # Show Details
        show_details = processed_info.get('show_details', {})
        if show_details:
            context_parts.append("=== SHOW CONFIG ===")
            context_parts.append(f"Preset: {processed_info.get('preset_name', 'N/A')}")
            context_parts.append(f"Target Time: {processed_info.get('target_time', 'N/A')}")
            
        # Content Focus
        content_focus = processed_info.get('content_focus', {})
        if content_focus:
            context_parts.append("\n=== CONTENT FOCUS ===")
            focus = content_focus.get('focus', 'N/A')
            reasoning = content_focus.get('reasoning', 'N/A')
            context_parts.append(f"Focus: {focus}")
            context_parts.append(f"Reasoning: {reasoning}")
            
        # Processing Info
        context_parts.append(f"\n=== PROCESSING ===")
        context_parts.append(f"Quality Score: {processed_info.get('quality_score', 0.0)}")
        context_parts.append(f"Generated By: {processed_info.get('generated_by', 'N/A')}")
        context_parts.append(f"Timestamp: {processed_info.get('processing_timestamp', 'N/A')}")
        
        return "\n".join(context_parts) if context_parts else "Kein Show-Kontext verfügbar"

    def _format_live_context_for_display(self, raw_data: Dict[str, Any], processed_info: Dict[str, Any]) -> str:
        """Formatiert Live-Daten-Kontext für Anzeige mit intelligenten GPT-Summaries"""
        context_parts = []
        
        # Weather Context - INTELLIGENT GPT SUMMARY
        weather = raw_data.get('weather', {})
        if weather:
            context_parts.append("=== WEATHER INTELLIGENCE ===")
            weather_summary = weather.get('current_summary', 'Weather intelligence not available')
            context_parts.append(f"GPT Summary: {weather_summary}")
            context_parts.append(f"Location: {weather.get('location', 'Zürich')}")
            context_parts.append(f"Generated: {weather.get('timestamp', 'N/A')}")
            
        # Crypto Context - INTELLIGENT GPT SUMMARY  
        crypto = raw_data.get('crypto', {})
        if crypto:
            context_parts.append("\n=== BITCOIN INTELLIGENCE ===")
            bitcoin_summary = crypto.get('bitcoin_summary', 'Bitcoin intelligence not available')
            context_parts.append(f"GPT Summary: {bitcoin_summary}")
            
            # Raw Bitcoin data for reference
            bitcoin = crypto.get('bitcoin', {})
            if bitcoin:
                context_parts.append(f"Raw Price: ${bitcoin.get('price_usd', 0):,.0f}")
                context_parts.append(f"Raw 24h: {bitcoin.get('change_24h', 0):+.2f}%")
                context_parts.append(f"Raw 7d: {bitcoin.get('change_7d', 0):+.2f}%")
            
        # News Statistics
        all_news = processed_info.get('all_news', [])
        context_parts.append(f"\n=== NEWS STATS ===")
        context_parts.append(f"Total Articles: {len(all_news)}")
        context_parts.append(f"Selected: {len(processed_info.get('selected_news', []))}")
        
        context_parts.append(f"\n=== INTELLIGENCE STATUS ===")
        context_parts.append(f"Weather GPT: {'✅ Active' if weather.get('current_summary') else '❌ Inactive'}")
        context_parts.append(f"Bitcoin GPT: {'✅ Active' if crypto.get('bitcoin_summary') else '❌ Inactive'}")
        
        return "\n".join(context_parts) if context_parts else "Keine Live-Daten verfügbar"

    def _format_processing_meta_for_display(self, processed_info: Dict[str, Any]) -> str:
        """Formatiert Processing-Metadaten für Anzeige"""
        context_parts = []
        
        context_parts.append("=== PROCESSING META ===")
        context_parts.append(f"Success: {processed_info.get('success', 'N/A')}")
        context_parts.append(f"Target News Count: {len(processed_info.get('selected_news', []))}")
        context_parts.append(f"Total Segments: {len(processed_info.get('segments', []))}")
        
        # Prepared Data Info
        prepared_data = processed_info.get('prepared_data', {})
        if prepared_data:
            context_parts.append(f"\n=== PREPARED DATA ===")
            context_parts.append(f"News for GPT: {len(prepared_data.get('news', []))}")
            context_parts.append(f"Target Count: {prepared_data.get('target_news_count', 'N/A')}")
            context_parts.append(f"Target Time: {prepared_data.get('target_time', 'N/A')}")
            
        # Quality Metrics
        quality_score = processed_info.get('quality_score', 0.0)
        context_parts.append(f"\n=== QUALITY ===")
        context_parts.append(f"Score: {quality_score}")
        context_parts.append(f"Grade: {'A' if quality_score >= 0.9 else 'B' if quality_score >= 0.7 else 'C'}")
        
        return "\n".join(context_parts)

    def _format_gpt_filter_rules_for_display(self, raw_data: Dict[str, Any], processed_info: Dict[str, Any]) -> str:
        """Formatiert GPT Filter-Regeln für Anzeige - NEUE PRESET-BASIERTE FILTERUNG"""
        
        # Get filter statistics from new processing
        prepared_data = processed_info.get('prepared_data', {})
        filter_stats = prepared_data.get('filter_stats', {})
        
        if filter_stats:
            # New preset-based filtering
            applied_filters = filter_stats.get('applied_filters', {})
            
            filter_info = f"""=== PRESET-BASIERTE FILTERUNG (NEU!) ===

🎯 ZÜRICH-PRESET KONFIGURATION:
• Erlaubte Kategorien: {', '.join(applied_filters.get('allowed_categories', []))}
• Ausgeschlossene Kategorien: {', '.join(applied_filters.get('excluded_categories', []))}
• Min. Priority: {applied_filters.get('min_priority', 'N/A')}
• Max. Feeds pro Kategorie: {applied_filters.get('max_feeds_per_category', 'N/A')}

⏰ KATEGORIE-SPEZIFISCHE ALTER-LIMITS:
• Zürich News: max. {applied_filters.get('age_limits', {}).get('zurich_max_age', 'N/A')}h alt
• Schweiz News: max. {applied_filters.get('age_limits', {}).get('schweiz_max_age', 'N/A')}h alt  
• Andere News: max. {applied_filters.get('age_limits', {}).get('other_max_age', 'N/A')}h alt

⚖️ KATEGORIE-GEWICHTUNG:
• Zürich: {applied_filters.get('category_weights', {}).get('zurich', 'N/A')}x Gewichtung
• Schweiz: {applied_filters.get('category_weights', {}).get('schweiz', 'N/A')}x Gewichtung
• News: {applied_filters.get('category_weights', {}).get('news', 'N/A')}x Gewichtung
• Zürich Priority Boost: +{applied_filters.get('zurich_priority_boost', 'N/A')}

📊 FILTER-PIPELINE STATISTIKEN:
• 📰 Total News gesammelt: {filter_stats.get('total_news', 'N/A')}
• 📂 Nach Kategorie-Filter: {filter_stats.get('category_filtered', 'N/A')}
• ⏰ Nach Age-Filter: {filter_stats.get('age_filtered', 'N/A')}
• ⚖️ Nach Gewichtung: {filter_stats.get('weighted_filtered', 'N/A')}
• 🎯 Final an GPT: {filter_stats.get('final_for_gpt', 'N/A')}

📂 FINAL KATEGORIE-BREAKDOWN:"""
            
            category_breakdown = filter_stats.get('category_breakdown', {})
            for category, count in category_breakdown.items():
                filter_info += f"\n• {category}: {count} News"
            
            filter_info += f"""

✨ INTELLIGENTE PRESET-FILTERUNG AKTIV!
• Crypto/Bitcoin News automatisch ausgeschlossen
• Zürich News bevorzugt (3x Gewichtung + Priority Boost)
• Kategorie-spezifische Altersfilterung
• Qualitäts-basierte Sortierung"""

        else:
            # Fallback to old display
            all_news = raw_data.get('news', [])
            gpt_news = prepared_data.get('news', [])
            
            filter_info = f"""=== FALLBACK FILTERUNG (ALT) ===

🔧 EINFACHE FILTER-KONFIGURATION:
• Zeitfilter: 48h (nur neue News)
• Max News für GPT: 15 Artikel
• Sortierung: Neueste zuerst (published)
• Stadt-Filter: NEIN (GPT entscheidet!)

📊 FILTER-STATISTIKEN:
• Total News gesammelt: {len(all_news)}
• An GPT gesendet: {len(gpt_news)}
• Von GPT ausgewählt: {len(processed_info.get('selected_news', []))}

⚠️ KEIN PRESET-FILTER AKTIV!
• Alle Kategorien durchgelassen (auch Crypto/Bitcoin)
• Keine Zürich-Priorisierung
• Keine kategorie-spezifische Altersfilterung"""

        return filter_info

    def _get_weather_value(self, weather: Dict[str, Any], key: str) -> str:
        """Extract weather value from either old format (direct) or new format (weather['current'])"""
        if not weather:
            return 'N/A' if key != 'description' else 'No data'
        
        # Try new format first (raw weather data with 'current' section)
        if 'current' in weather and isinstance(weather['current'], dict):
            value = weather['current'].get(key)
            if value is not None:
                return str(value) if key != 'temperature' else str(round(float(value), 1))
        
        # Fallback to old format (direct access)
        value = weather.get(key)
        if value is not None:
            return str(value) if key != 'temperature' else str(round(float(value), 1))
        
        # Default values
        return 'N/A' if key != 'description' else 'No data'

    def _generate_audio_player_html(self, timestamp: str) -> str:
        """Generiert den HTML-Code für den Audio-Player und das Cover.
        
        Sucht nach Audio- und Cover-Dateien, die exakt zum übergebenen Timestamp passen.
        Falls keine exakte Übereinstimmung gefunden wird, wird eine robuste Fallback-Logik
        angewendet, um die absolut neueste Show anzuzeigen.
        """
        logger.info(f"🎤 Generating audio player for timestamp: {timestamp}")
        
        # --- 1. Exaktes Matching (primäre Methode) ---
        exact_audio_path = os.path.join(self.output_dir, f"radiox_{timestamp}.mp3")
        exact_cover_path = os.path.join(self.output_dir, f"radiox_{timestamp}.png")
        
        audio_path = None
        cover_path = None
        
        if os.path.exists(exact_audio_path):
            audio_path = f"radiox_{timestamp}.mp3"
            logger.info(f"✅ Found exact audio match: {audio_path}")
        
        if os.path.exists(exact_cover_path):
            cover_path = f"radiox_{timestamp}.png"
            logger.info(f"✅ Found exact cover match: {cover_path}")
        
        # --- 2. Fallback-Logik (wenn exaktes Matching fehlschlägt) ---
        if audio_path is None or cover_path is None:
            missing_files = []
            if audio_path is None:
                missing_files.append("audio (.mp3)")
            if cover_path is None:
                missing_files.append("cover (.png)")
            
            logger.warning(f"⚠️ Missing {', '.join(missing_files)} for timestamp '{timestamp}'. Initiating fallback to newest files.")
            try:
                files = os.listdir(self.output_dir)
                
                # Finde die neueste MP3-Datei (nur wenn Audio fehlt)
                if audio_path is None:
                    mp3_files = [f for f in files if f.startswith('radiox_') and f.endswith('.mp3')]
                    if mp3_files:
                        latest_mp3 = max(mp3_files, key=lambda f: os.path.getmtime(os.path.join(self.output_dir, f)))
                        audio_path = latest_mp3
                        logger.info(f"🔄 Fallback found newest audio: {audio_path}")
                    else:
                        logger.error(f"❌ No MP3 files found in {self.output_dir}")

                # Finde die neueste PNG-Datei (nur wenn Cover fehlt)
                if cover_path is None:
                    png_files = [f for f in files if f.startswith('radiox_') and f.endswith('.png')]
                    if png_files:
                        latest_png = max(png_files, key=lambda f: os.path.getmtime(os.path.join(self.output_dir, f)))
                        cover_path = latest_png
                        logger.info(f"🔄 Fallback found newest cover: {cover_path}")
                    else:
                        logger.error(f"❌ No PNG files found in {self.output_dir}")
            
            except Exception as e:
                logger.error(f"❌ Error during fallback file search: {e}")

        # --- 3. HTML-Generierung ---
        if audio_path and cover_path:
            player_html = f"""
            <div class="bg-gray-800 text-white rounded-lg shadow-lg overflow-hidden">
                <div class="md:flex">
                    <div class="md:flex-shrink-0">
                        <img class="h-32 w-full object-cover md:w-32" src="{cover_path}" alt="RadioX Show Cover">
                    </div>
                    <div class="p-6 flex flex-col justify-between flex-1">
                        <div>
                            <div class="uppercase tracking-wide text-sm text-indigo-400 font-semibold">RadioX Live</div>
                            <h2 class="block mt-1 text-lg leading-tight font-medium text-white">Latest Broadcast</h2>
                            <p class="mt-2 text-gray-400">Timestamp: {timestamp}</p>
                        </div>
                    </div>
                </div>
                <!-- Full-Width Audio Player with Large Timeline -->
                <div class="bg-gray-900 p-6">
                    <audio controls class="w-full" style="width: 100%; height: 80px; min-height: 80px;" src="{audio_path}">
                        Your browser does not support the audio element.
                    </audio>
                </div>
            </div>"""
        else:
            logger.warning("⚠️ Audio or cover file not found, displaying fallback message.")
            player_html = f"""
            <div class="bg-red-100 border-l-4 border-red-500 text-red-700 p-4 rounded-lg" role="alert">
                <p class="font-bold">Audio Not Available</p>
                <p>Could not find the audio or cover file for timestamp {timestamp}. Please check the 'outplay' directory.</p>
                <p class="text-sm mt-2">Expected audio: <code>radiox_{timestamp}.mp3</code></p>
                <p class="text-sm">Expected cover: <code>radiox_{timestamp}.png</code></p>
            </div>"""

        return f"""
        <!-- Audio Player Section -->
        <div class="max-w-7xl mx-auto px-4 py-6">
            {player_html}
        </div>
        """

    def _format_gpt_input_news_for_display(self, processed_info: Dict[str, Any]) -> str:
        """Formatiert die an GPT gesendeten Nachrichten für die Anzeige"""
        prepared_data = processed_info.get('prepared_data', {})
        gpt_news = prepared_data.get('news', [])
        
        if not gpt_news:
            return "Keine News an GPT gesendet"
        
        formatted = []
        formatted.append(f"=== {len(gpt_news)} NEWS AN GPT GESENDET ===\n")
        
        for i, news in enumerate(gpt_news, 1):
            title = news.get('title', 'No title')
            source = news.get('source', 'Unknown').upper()
            category = news.get('category', 'general')
            age_hours = round(news.get('age_hours', 0))
            summary = news.get('summary', 'No summary')
            
            formatted.append(f"{i:2d}. [{source}] {title}")
            formatted.append(f"    📂 {category} | ⏰ {age_hours}h ago")
            formatted.append(f"    💬 {summary}")
            formatted.append("")  # Empty line
        
        # Add selection info
        selected_news = processed_info.get('selected_news', [])
        if selected_news:
            formatted.append(f"🎯 GPT AUSGEWÄHLT ({len(selected_news)} von {len(gpt_news)}):")
            for i, selected in enumerate(selected_news, 1):
                title = selected.get('title', 'No title')
                reason = selected.get('relevance_reason', 'No reason')
                formatted.append(f"  {i}. {title}")
                formatted.append(f"     Grund: {reason}")
            
        return "\n".join(formatted)

    def _get_stage1_prompt(self, processed_info: Dict[str, Any]) -> str:
        """Extract Stage 1 (Article Selection) prompt"""
        gpt_prompt = processed_info.get('gpt_prompt', {})
        
        if isinstance(gpt_prompt, dict):
            return gpt_prompt.get('stage1_selection_prompt', 'No Stage 1 prompt available')
        else:
            # Fallback for old single-prompt format
            return 'Stage 1 prompt not available (old format)'

    def _get_stage2_prompt(self, processed_info: Dict[str, Any]) -> str:
        """Extract Stage 2 (Script Writing) prompt"""
        gpt_prompt = processed_info.get('gpt_prompt', {})
        
        if isinstance(gpt_prompt, dict):
            return gpt_prompt.get('stage2_scripting_prompt', 'No Stage 2 prompt available')
        else:
            # Fallback for old single-prompt format (probably the scripting prompt)
            return str(gpt_prompt) if gpt_prompt else 'No Stage 2 prompt available'
    
    def _get_stage1_response(self, processed_info: Dict[str, Any]) -> str:
        """Extract Stage 1 GPT Response as readable text"""
        gpt_response = processed_info.get('gpt_response', {})
        
        if isinstance(gpt_response, dict):
            stage1_response = gpt_response.get('stage1_selection_response', '')
            if stage1_response:
                return stage1_response
        
        # Try alternative locations
        selection_data = processed_info.get('article_selection_data', {})
        if selection_data:
            return str(selection_data)
        
        # Try selected_news with reasons as fallback - format as readable text
        selected_news = processed_info.get('selected_news', [])
        if selected_news:
            response_lines = ["SELECTED ARTICLES:"]
            for i, news in enumerate(selected_news, 1):
                title = news.get('title', 'No title')
                reason = news.get('relevance_reason', news.get('selection_reason', 'No reason given'))
                response_lines.append(f"{i}. {title}")
                response_lines.append(f"   Reason: {reason}")
                response_lines.append("")  # Empty line between articles
            
            return "\n".join(response_lines)
        
        return 'No Stage 1 GPT response available'
    
    def _get_image_prompt(self, processed_info: Dict[str, Any]) -> str:
        """Extract Image Generation Prompt sent to DALL-E"""
        
        # NEW: Try cover_generation section first (now available!)
        cover_data = processed_info.get('cover_generation', {})
        if isinstance(cover_data, dict):
            dalle_prompt = cover_data.get('dalle_prompt', '')
            if dalle_prompt:
                return dalle_prompt
        
        # Try image_generation section
        image_data = processed_info.get('image_generation', {})
        if isinstance(image_data, dict):
            dalle_prompt = image_data.get('dalle_prompt', image_data.get('prompt', ''))
            if dalle_prompt:
                return dalle_prompt
        
        # Try direct dalle_prompt field
        dalle_prompt = processed_info.get('dalle_prompt', '')
        if dalle_prompt:
            return dalle_prompt
        
        # Try in workflow results structure
        workflow_result = processed_info.get('workflow_result', {})
        if isinstance(workflow_result, dict):
            cover_gen = workflow_result.get('cover_generation', {})
            if isinstance(cover_gen, dict):
                dalle_prompt = cover_gen.get('dalle_prompt', cover_gen.get('prompt', ''))
                if dalle_prompt:
                    return dalle_prompt
        
        # Try in any nested data structures
        for key, value in processed_info.items():
            if isinstance(value, dict):
                if 'dalle_prompt' in value:
                    return value['dalle_prompt']
                if 'prompt' in value and 'dall' in key.lower():
                    return value['prompt']
                if 'image_prompt' in value:
                    return value['image_prompt']
        
        # Search for any field containing "prompt" and "image" or "dall"
        for key, value in processed_info.items():
            if isinstance(value, str) and 'prompt' in key.lower():
                if 'image' in key.lower() or 'dall' in key.lower() or 'cover' in key.lower():
                    if len(value) > 50:  # Likely a real prompt, not just metadata
                        return value
        
        # Return helpful message if no prompt found
        return """🎨 DALL-E Prompt not available yet.

Note: The DALL-E prompt is now passed to the dashboard, but this might be an older generation.
The prompt should be visible in newer dashboard generations."""
    
    def _get_returned_image_prompt(self, processed_info: Dict[str, Any]) -> str:
        """Extract the final/returned image prompt used by DALL-E"""
        # This would be the prompt that DALL-E actually used (sometimes modified)
        # In most cases this is the same as the sent prompt, but DALL-E might modify it
        
        image_data = processed_info.get('image_generation', {})
        if isinstance(image_data, dict):
            returned_prompt = image_data.get('final_prompt', image_data.get('used_prompt', ''))
            if returned_prompt:
                return returned_prompt
        
        cover_data = processed_info.get('cover_generation', {})
        if isinstance(cover_data, dict):
            returned_prompt = cover_data.get('final_prompt', cover_data.get('used_prompt', ''))
            if returned_prompt:
                return returned_prompt
        
        # Explain that this data isn't available at dashboard generation time
        return """No returned image prompt available - Cover generation runs after dashboard.

Note: Cover generation happens AFTER dashboard creation, so the DALL-E response prompt won't be available here.
The returned prompt is typically the same as the sent prompt unless DALL-E modifies it.
You can find both prompts in the console logs when cover generation runs."""
