#!/usr/bin/env python3
import sys
sys.path.append('src')
import asyncio
from services.processing.content_processing_service import ContentProcessingService

async def check_config():
    processor = ContentProcessingService()
    config = await processor.get_show_configuration("zurich")
    
    print("🎭 ZURICH SHOW CONFIGURATION:")
    print("=" * 50)
    print(f"Display Name: {config.get('show', {}).get('display_name')}")
    print(f"City Focus: {config.get('show', {}).get('city_focus')}")
    
    # Check RSS Filter Categories
    rss_filter = config.get("content", {}).get("rss_filter", {})
    categories = rss_filter.get("categories", [])
    print(f"RSS Filter Categories: {categories}")
    
    # Check if weather category is present
    has_weather = "weather" in [cat.lower() for cat in categories]
    print(f"Has Weather Category: {has_weather}")
    
    # Full config
    print("\n🔍 FULL CONFIG:")
    import json
    print(json.dumps(config, indent=2))

if __name__ == "__main__":
    asyncio.run(check_config()) 