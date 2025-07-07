#!/usr/bin/env python3
"""
🎙️ RADIOX SHOW SCRIPT GENERATOR
DATABASE-DRIVEN CONFIGURATION (Google Design Principles)
Uses hierarchical configuration from Database Service
80/20 BEST PRACTICE: Environment config + Content Extraction
"""

import asyncio
import argparse
import httpx
import json
import os
from datetime import datetime
import sys
from bs4 import BeautifulSoup
import re

# Import service configuration
from config.service_config import config

# Service URLs - Environment based
SERVICES = {
    "database": config.DATABASE_URL,
    "key": config.KEY_SERVICE_URL, 
    "data_collector": config.DATA_COLLECTOR_URL
}

async def get_hierarchical_config(category: str, key: str = None) -> str:
    """Get configuration from Database Service hierarchical config"""
    
    # 1. Environment Override (highest priority)
    if key:
        env_value = os.getenv(f"DEFAULT_{key.upper()}")
        if env_value:
            print(f"📦 Config '{category}.{key}' from ENVIRONMENT: {env_value}")
            return env_value
    
    # 2. Database Service hierarchical config
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            if key:
                # Get specific config value
                response = await client.get(f"{SERVICES['database']}/config/{category}/{key}")
                if response.status_code == 200:
                    data = response.json()
                    value = data.get('value', '')
                    print(f"📦 Config '{category}.{key}' from DATABASE: {value}")
                    return value
            else:
                # Get entire category
                response = await client.get(f"{SERVICES['database']}/config/{category}")
                if response.status_code == 200:
                    data = response.json()
                    print(f"📦 Config category '{category}' from DATABASE: {len(data)} items")
                    return data
    except Exception as e:
        print(f"⚠️ Database config failed for '{category}.{key}': {e}")
    
    # 3. Service Technical Fallback (lowest priority)
    fallbacks = {
        "defaults": {
            "default_channel": "zurich",
            "default_news_count": "3",
            "default_language": "de",
            "default_primary_speaker": "marcel",
            "default_secondary_speaker": "jarvis"
        },
        "system": {
            "default_timezone": "Europe/Zurich"
        }
    }
    
    if category in fallbacks and key in fallbacks[category]:
        fallback_value = fallbacks[category][key]
        print(f"📦 Config '{category}.{key}' from FALLBACK: {fallback_value}")
        return fallback_value
    
    return ""

async def test_service_health():
    """Test if all required services are running"""
    print("🏥 Testing service health...")
    
    for service_name, url in SERVICES.items():
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{url}/health")
                if response.status_code == 200:
                    print(f"✅ {service_name.title()} Service: Healthy")
                else:
                    print(f"❌ {service_name.title()} Service: Unhealthy ({response.status_code})")
                    return False
        except Exception as e:
            print(f"❌ {service_name.title()} Service: Connection failed ({e})")
            return False
    
    return True

async def get_available_presets():
    """Get available show presets from Database Service"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{SERVICES['database']}/show-presets")
            if response.status_code == 200:
                presets = response.json()
                return [preset['preset_name'] for preset in presets]
    except Exception as e:
        print(f"❌ Failed to fetch presets: {e}")
    
    return ["zurich", "news", "oev"]  # fallback

async def get_show_preset(preset_name: str):
    """Get show preset configuration from Database Service"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{SERVICES['database']}/show-presets")
            if response.status_code == 200:
                presets = response.json()
                for preset in presets:
                    if preset['preset_name'] == preset_name:
                        return preset
    except Exception as e:
        print(f"❌ Failed to fetch preset '{preset_name}': {e}")
    
    # Fallback preset
    return {
        "preset_name": preset_name,
        "display_name": f"{preset_name.title()} Show",
        "primary_speaker": await get_hierarchical_config("defaults", "default_primary_speaker"),
        "secondary_speaker": await get_hierarchical_config("defaults", "default_secondary_speaker"),
    }

async def extract_full_article_content(news_articles):
    """Extract full article content from URLs for better GPT prompts"""
    print(f"📰 Extracting full content from {len(news_articles)} articles...")
    
    enriched_articles = []
    
    for i, article in enumerate(news_articles[:3]):  # Limit to 3 for performance
        try:
            url = article.get('link', '')
            if not url:
                continue
                
            print(f"🔍 Extracting article {i+1}/3: {article.get('title', 'Unknown')}...")
            
            async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
                response = await client.get(url, headers={
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                })
                
                if response.status_code == 200:
                    # Parse HTML and extract text content
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Remove script, style, and other non-content elements
                    for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'advertisement']):
                        element.decompose()
                    
                    # Try to find article content - common patterns
                    content_selectors = [
                        'article', 
                        '.article-content',
                        '.article-body', 
                        '.content',
                        '.entry-content',
                        '.post-content',
                        '[data-testid="article-content"]',
                        '.article-text'
                    ]
                    
                    article_text = ""
                    for selector in content_selectors:
                        content_div = soup.select_one(selector)
                        if content_div:
                            article_text = content_div.get_text()
                            break
                    
                    # Fallback: get all paragraph text
                    if not article_text:
                        paragraphs = soup.find_all('p')
                        article_text = ' '.join([p.get_text() for p in paragraphs])
                    
                    # Clean up text
                    article_text = re.sub(r'\s+', ' ', article_text).strip()
                    
                    # Limit text length (GPT token limits)
                    if len(article_text) > 2000:
                        article_text = article_text[:2000] + "..."
                    
                    if article_text and len(article_text) > 100:  # Minimum content check
                        enriched_article = {
                            'title': article.get('title', ''),
                            'summary': article.get('summary', ''),
                            'link': url,
                            'source': article.get('source', ''),
                            'timestamp': article.get('timestamp', ''),
                            'full_content': article_text,
                            'content_length': len(article_text),
                            'extraction_status': 'success'
                        }
                        enriched_articles.append(enriched_article)
                        print(f"✅ Extracted {len(article_text)} characters from {article.get('source', 'unknown')}")
                    else:
                        print(f"⚠️ No substantial content found for {article.get('title', 'unknown')}")
                        # Keep original article if extraction fails
                        enriched_articles.append({**article, 'extraction_status': 'failed'})
                else:
                    print(f"❌ HTTP {response.status_code} for {url}")
                    enriched_articles.append({**article, 'extraction_status': 'http_error'})
                    
        except Exception as e:
            print(f"❌ Content extraction error for {article.get('title', 'unknown')}: {str(e)}")
            enriched_articles.append({**article, 'extraction_status': 'exception'})
            continue
    
    successful_extractions = [a for a in enriched_articles if a.get('extraction_status') == 'success']
    print(f"📄 Content extraction complete: {len(successful_extractions)}/{len(news_articles)} successful")
    
    return enriched_articles

async def get_curated_content():
    """Get curated content from Data Collector Service with full article extraction"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{SERVICES['data_collector']}/content?feed_categories=zuerich&news_count=3&location=Zurich")
            if response.status_code == 200:
                content = response.json()
                
                # Extract full article content for better GPT prompts
                if content.get('news'):
                    print("🔍 Starting full article content extraction...")
                    enriched_news = await extract_full_article_content(content['news'])
                    content['news'] = enriched_news
                    print("✅ Article content extraction complete")
                
                return content
    except Exception as e:
        print(f"❌ Failed to fetch content from Data Collector: {e}")
    
    return {"news": [], "weather": {}, "bitcoin": {}}

async def generate_script_with_gpt(preset, content, target_time, language):
    """Generate show script using REAL GPT-4 with full article content"""
    
    print("🤖 INITIATING REAL GPT-4 COMMUNICATION WITH FULL ARTICLE CONTENT...")
    
    # Get OpenAI API key from database
    openai_api_key = None
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{SERVICES['key']}/keys/openai_api_key")
            if response.status_code == 200:
                data = response.json()
                openai_api_key = data.get('key_value')
                print("✅ OpenAI API key loaded from Key Service")
    except Exception as e:
        print(f"❌ Failed to get OpenAI API key: {e}")
        return "Error: Could not load OpenAI API key"
    
    if not openai_api_key:
        print("❌ No OpenAI API key available")
        return "Error: No OpenAI API key"
    
    news = content.get('news', [])
    weather = content.get('weather', {})
    bitcoin = content.get('bitcoin', {})
    
    # Get speakers from preset
    primary_speaker = preset.get('primary_speaker', 'marcel')
    secondary_speaker = preset.get('secondary_speaker', 'jarvis')
    preset_name = preset.get('preset_name', 'unknown')
    
    # Build the GPT prompt
    system_prompt = f"""Du bist ein Radio-Script-Autor für RadioX.

AUFGABE: Schreibe ein Radio-Script für eine {target_time} Uhr Show.

SPRECHER:
- {primary_speaker.title()}: Hauptmoderator
- {secondary_speaker.title()}: Co-Moderator

FORMAT: [SPRECHER] Text

INHALT: Nutze die bereitgestellten Artikel-Inhalte"""

    # Build detailed news section with full content
    news_section = "=== VOLLSTÄNDIGE ARTIKEL-INHALTE ===\n\n"
    for i, article in enumerate(news[:3]):
        news_section += f"ARTIKEL {i+1}:\n"
        news_section += f"Titel: {article.get('title', 'Unbekannt')}\n"
        news_section += f"Quelle: {article.get('source', 'Unbekannt')}\n"
        news_section += f"URL: {article.get('link', '')}\n"
        
        # Include full content if available
        if article.get('full_content'):
            news_section += f"VOLLSTÄNDIGER INHALT:\n{article['full_content']}\n"
            news_section += f"(Extrahiert: {article.get('content_length', 0)} Zeichen)\n"
        else:
            news_section += f"ZUSAMMENFASSUNG: {article.get('summary', 'Keine Zusammenfassung verfügbar')}\n"
            news_section += f"(Vollständiger Inhalt nicht verfügbar: {article.get('extraction_status', 'unknown')})\n"
        
        news_section += "\n" + "-"*80 + "\n\n"

    # Build user prompt with full article content
    user_prompt = f"""SHOW PRESET: {preset_name}
TARGET TIME: {target_time} Uhr
LANGUAGE: {language}

=== AKTUELLE DATEN ===

WETTER ZÜRICH:
{json.dumps(weather, indent=2, ensure_ascii=False) if weather else "Keine Wetter-Daten verfügbar"}

BITCOIN:
{json.dumps(bitcoin, indent=2, ensure_ascii=False) if bitcoin else "Keine Bitcoin-Daten verfügbar"}

{news_section}

=== ANWEISUNGEN ===
1. Schreibe ein 3-5 Minuten Radio-Script
2. Beginne mit Begrüssung und Zeit
3. Nutze die VOLLSTÄNDIGEN Artikel-Inhalte für informative und detaillierte Berichterstattung
4. Integriere Wetter und Bitcoin natürlich
5. Verwende konkrete Details aus den Artikeln, nicht nur Titel/Zusammenfassungen
6. Beende mit Verabschiedung
7. Verwende authentische Zürich-Referenzen wenn möglich"""

    print("\n" + "="*80)
    print("📤 SENDING TO GPT-4 WITH FULL ARTICLE CONTENT:")
    print("="*80)
    print("🧠 SYSTEM PROMPT:")
    print(system_prompt)
    print(f"\n🎯 USER PROMPT: ({len(user_prompt)} characters)")
    print("📰 Article content included:", len([a for a in news if a.get('full_content')]), "full articles")
    print("="*80)
    
    # Make real OpenAI API call
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            openai_request = {
                "model": "gpt-4o",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "max_tokens": 2000,
                "temperature": 0.7
            }
            
            print("🚀 MAKING OPENAI API CALL WITH ENRICHED CONTENT...")
            print(f"📊 Request: model={openai_request['model']}, tokens={openai_request['max_tokens']}, temp={openai_request['temperature']}")
            
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {openai_api_key}",
                    "Content-Type": "application/json"
                },
                json=openai_request
            )
            
            if response.status_code == 200:
                response_data = response.json()
                
                print("\n" + "="*80)
                print("📥 GPT-4 RESPONSE RECEIVED:")
                print("="*80)
                print(f"📊 Response stats:")
                usage = response_data.get('usage', {})
                print(f"   🎯 Prompt tokens: {usage.get('prompt_tokens', 'N/A')}")
                print(f"   📝 Completion tokens: {usage.get('completion_tokens', 'N/A')}")
                print(f"   📦 Total tokens: {usage.get('total_tokens', 'N/A')}")
                print(f"   🧠 Model: {response_data.get('model', 'N/A')}")
                
                script_content = response_data['choices'][0]['message']['content']
                
                print(f"\n🎭 GENERATED SCRIPT:")
                print("-" * 80)
                print(script_content)
                print("-" * 80)
                print("="*80)
                
                return script_content
                
            else:
                error_text = response.text
                print(f"\n❌ OpenAI API ERROR:")
                print(f"Status: {response.status_code}")
                print(f"Response: {error_text}")
                return f"Error: OpenAI API returned {response.status_code}: {error_text}"
                
    except Exception as e:
        print(f"\n❌ EXCEPTION during GPT call: {e}")
        return f"Error: Exception during GPT call: {e}"

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="RadioX Show Script Generator (Database-Driven)")
    parser.add_argument("--preset", help="Show preset name")
    parser.add_argument("--time", help="Target time (e.g., 09:30)")
    parser.add_argument("--news-count", type=int, help="Number of news articles")
    parser.add_argument("--language", help="Show language")
    parser.add_argument("--check-services", action="store_true", help="Only check service health")
    parser.add_argument("--list-presets", action="store_true", help="List available presets")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    
    return parser.parse_args()

async def main():
    """Main show generation function with database-driven configuration"""
    
    args = parse_args()
    
    # 1. Health check
    if not await test_service_health():
        print("❌ Service health check failed!")
        return
    
    # 2. List presets mode
    if args.list_presets:
        print("📋 Available presets:")
        presets = await get_available_presets()
        for preset in presets:
            print(f"  • {preset}")
        return
    
    # 3. Service check only mode
    if args.check_services:
        print("✅ All services are healthy!")
        return
    
    # 4. Load hierarchical configuration from Database Service
    print("🔧 Loading hierarchical configuration...")
    
    default_preset = args.preset if args.preset else await get_hierarchical_config("defaults", "default_channel")
    default_time = args.time if args.time else "09:30"
    default_news_count = args.news_count if args.news_count else int(await get_hierarchical_config("defaults", "default_news_count") or "3")
    default_language = args.language if args.language else await get_hierarchical_config("defaults", "default_language")
    
    if args.verbose:
        print(f"📦 Final config: preset={default_preset}, time={default_time}, news_count={default_news_count}, language={default_language}")
    
    # 5. Generate show
    print(f"🎭 Generating {default_preset} show for {default_time}...")
    
    # Get preset configuration
    preset = await get_show_preset(default_preset)
    
    # Get curated content
    print("📡 Fetching curated content...")
    content = await get_curated_content()
    
    # Generate script
    print("✍️ Generating script...")
    script = await generate_script_with_gpt(preset, content, default_time, default_language)
    
    # Save to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    filename = f"{default_preset}-{timestamp}-show.txt"
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(script)
    
    print(f"📄 Script saved to: {filename}")
    print(f"📊 Script stats:")
    script_lines = script.split('\\n')
    print(f"   📝 Lines: {len(script_lines)}")
    print(f"   📦 Words: {len(script.split())}")
    print(f"   📰 News articles: {len(content.get('news', []))}")
    
    print("✅ Show generation complete!")

if __name__ == "__main__":
    asyncio.run(main()) 