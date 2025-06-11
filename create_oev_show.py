#!/usr/bin/env python3
"""
ÖV RadioShow Generator
======================

Erstellt eine deutsche RadioShow mit Fokus auf öffentlichen Verkehr.
Filtert gesammelte Daten nach ÖV-relevanten News (SBB, VBZ, ZVV).
"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.append('src')

from services.generation.audio_generation_service import AudioGenerationService
from services.processing.content_processing_service import ContentProcessingService

async def create_oev_show():
    """Erstellt eine ÖV-fokussierte deutsche RadioShow"""
    
    print("🚇 ÖV RADIOSHOW GENERATOR")
    print("=" * 50)
    
    # 1. Lade gesammelte Daten
    print("📊 Lade gesammelte Daten...")
    outplay_dir = Path("outplay")
    data_file = outplay_dir / "data_collection_clean.json"
    
    if not data_file.exists():
        print("❌ Keine Daten gefunden. Führe erst 'python3 main.py --data-only' aus.")
        return False
    
    with open(data_file, 'r', encoding='utf-8') as f:
        all_data = json.load(f)
    
    # 2. Filtere ÖV-relevante News
    print("🚇 Filtere ÖV-relevante News...")
    all_news = all_data.get("news", [])
    oev_news = []
    
    for news in all_news:
        # Filter nach ÖV-Kategorien und Quellen
        source = news.get("source", "").lower()
        category = news.get("category", "").lower()
        title = news.get("title", "").lower()
        
        # ÖV-relevante Kriterien
        is_oev_source = source in ["sbb", "vbz", "zvv"]
        is_oev_category = category in ["oev"]
        is_oev_keywords = any(keyword in title for keyword in [
            "bahn", "zug", "öv", "verkehr", "tram", "bus", "sbb", "vbz", "zvv",
            "station", "gleis", "fahrplan", "störung", "verspätung", "ersatzbus"
        ])
        
        if is_oev_source or is_oev_category or is_oev_keywords:
            oev_news.append(news)
    
    print(f"✅ {len(oev_news)} ÖV-relevante News gefunden von {len(all_news)} total")
    
    if len(oev_news) == 0:
        print("❌ Keine ÖV-News gefunden!")
        return False
    
    # 3. Erstelle ÖV-fokussierte Daten-Struktur
    print("🎭 Bereite ÖV-Show-Daten vor...")
    oev_data = {
        "news": oev_news[:5],  # Top 5 ÖV News
        "weather": all_data.get("weather"),
        "crypto": all_data.get("crypto"),
        "timestamp": datetime.now().isoformat()
    }
    
    # 4. Erstelle ÖV-Show-Konfiguration
    show_config = {
        "show": {
            "preset_name": "oev",
            "display_name": "ÖV News Zürich",
            "description": "Öffentlicher Verkehr - Aktuelle News, Störungen und Updates",
            "city_focus": "zurich"
        },
        "content": {
            "focus": "öffentlicher_verkehr",
            "categories": ["oev", "verkehr", "transport"]
        }
    }
    
    # 5. Verarbeite mit GPT
    print("🤖 Verarbeite mit GPT...")
    try:
        content_processor = ContentProcessingService()
        
        # Manuell einen deutschen ÖV-Prompt erstellen
        result = await content_processor.process_content_for_show(
            oev_data, 
            target_news_count=3,
            target_time="05:00",
            preset_name="oev_manual",
            show_config=show_config,
            language="de"
        )
        
        if result.get("success"):
            print("✅ GPT-Verarbeitung erfolgreich!")
            print(f"📝 Script: {len(result.get('radio_script', ''))} Zeichen")
            
            # 6. Speichere Ergebnis
            output_file = outplay_dir / f"oev_show_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            
            print(f"💾 Show gespeichert: {output_file}")
            
            # 7. Zeige Script-Preview
            script = result.get("radio_script", "")
            if script:
                print("\n📻 RADIO SCRIPT PREVIEW:")
                print("-" * 50)
                print(script[:500] + "..." if len(script) > 500 else script)
                print("-" * 50)
            
            return True
        else:
            print("❌ GPT-Verarbeitung fehlgeschlagen")
            return False
            
    except Exception as e:
        print(f"❌ Fehler bei GPT-Verarbeitung: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(create_oev_show()) 