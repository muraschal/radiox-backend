#!/usr/bin/env python3

"""
CLI Data Collection - OPTIMIERTE DATENSAMMLUNG
==============================================

Direkter Zugriff auf den optimierten Data Collection Service:
- RSS Service: Professional Dashboard Integration (100+ articles)
- Bitcoin Service: Multi-timeframe Analysis (1h, 24h, 7d, 30d, 60d, 90d)
- Weather Service: Smart Time-based Logic (Swiss cities)
- Parallel Processing: Optimierte Performance
- Quality Metrics: Detaillierte Statistiken

USAGE:
python cli_data_collection.py                    # Vollständige Datensammlung
python cli_data_collection.py --test             # Service Tests
python cli_data_collection.py --news-only        # Nur RSS News
python cli_data_collection.py --preset bitcoin   # Preset-basierte Sammlung
python cli_data_collection.py --stats            # Nur Statistiken
"""

import asyncio
import sys
import argparse
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

# Import fix: use correct path
from src.services.data.data_collection_service import DataCollectionService
from loguru import logger

# Configure logger
logger.remove()
logger.add(sys.stdout, format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | {message}", level="INFO")


class DataCollectionCLI:
    """CLI Interface für den optimierten Data Collection Service"""
    
    def __init__(self):
        self.service = DataCollectionService()
        
    async def run_full_collection(self, preset: str = None, max_age_hours: int = 24):
        """Führt vollständige Datensammlung durch"""
        
        print("📊 DATA COLLECTION SERVICE")
        print("==============================")
        
        try:
            # Vollständige Datensammlung
            logger.info(f"🔄 Starte optimierte Datensammlung (Preset: {preset or 'default'})")
            
            # Use the available method from DataCollectionService
            data = await self.service.collect_all_data()
            
            # Ergebnisse anzeigen
            self._display_collection_results(data)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Fehler bei Datensammlung: {e}")
            return False
    
    async def run_news_only(self, limit: int = 25, max_age_hours: int = 24):
        """Sammelt nur RSS News"""
        
        print("📰 RSS NEWS COLLECTION")
        print("==============================")
        
        try:
            logger.info(f"📰 Sammle RSS News (Limit: {limit}, Max Age: {max_age_hours}h)")
            
            # Use the available method from DataCollectionService  
            news_data = await self.service.collect_news_only()
            news = news_data.get("news", [])
            
            # News anzeigen
            self._display_news_results(news)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Fehler bei News-Sammlung: {e}")
            return False
    
    async def run_service_tests(self):
        """Testet alle optimierten Services"""
        
        print("🧪 SERVICE TESTS")
        print("==============================")
        
        try:
            logger.info("🧪 Teste alle optimierten Data Collection Services")
            
            # Use the available method from DataCollectionService
            results = await self.service.test_connections()
            
            # Test-Ergebnisse anzeigen
            self._display_test_results(results)
            
            return all(results.values())
            
        except Exception as e:
            logger.error(f"❌ Fehler bei Service-Tests: {e}")
            return False
    
    async def show_statistics(self):
        """Zeigt Service-Statistiken"""
        
        print("📊 DATA COLLECTION STATISTICS")
        print("==============================")
        
        try:
            # Sammle minimale Daten für Statistiken
            data = await self.service.collect_all_data()
            
            # Simple statistics from the basic data structure
            news_count = len(data.get("news", []))
            has_weather = bool(data.get("weather"))
            has_crypto = bool(data.get("crypto"))
            
            print(f"\n📊 BASIC STATISTICS:")
            print(f"   📰 News Articles: {news_count}")
            print(f"   🌤️ Weather Data: {'✅' if has_weather else '❌'}")
            print(f"   ₿ Crypto Data: {'✅' if has_crypto else '❌'}")
            print(f"   ⏰ Timestamp: {data.get('collection_timestamp', 'unknown')}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Fehler bei Statistik-Sammlung: {e}")
            return False
    
    def _display_collection_results(self, data: dict):
        """Zeigt Ergebnisse der vollständigen Datensammlung"""
        
        if not data:
            print("❌ Keine Daten gesammelt")
            return
        
        print(f"\n🎯 SAMMLUNG ABGESCHLOSSEN:")
        print(f"   ⏰ Timestamp: {data.get('collection_timestamp', 'unknown')}")
        print(f"   ✅ Success: {data.get('success', False)}")
        
        # News Daten
        news = data.get("news", [])
        if news:
            print(f"\n📰 RSS NEWS:")
            print(f"   📄 Articles: {len(news)}")
            
            # Top 5 News anzeigen
            for i, news_item in enumerate(news[:5], 1):
                title = news_item.get("title", "No title")[:60]
                source = news_item.get("source", "Unknown")
                category = news_item.get("category", "general")
                print(f"   {i}. [{category}] {title}... ({source})")
        
        # Weather Daten
        weather = data.get("weather")
        if weather:
            print(f"\n🌤️ WEATHER DATA:")
            temp = weather.get("temperature", "?")
            desc = weather.get("description", "unknown")
            location = weather.get("location", "Zürich")
            print(f"   📍 {location}: {temp}°C, {desc}")
        
        # Crypto Daten
        crypto = data.get("crypto")
        if crypto:
            print(f"\n₿ CRYPTO DATA:")
            if "bitcoin" in crypto:
                btc = crypto["bitcoin"]
                price = btc.get("price_usd", "N/A")
                change = btc.get("change_24h", 0)
                print(f"   💰 Bitcoin: ${price:,.0f} ({change:+.1f}%)")
        
        # Fehler anzeigen
        errors = data.get("errors", [])
        if errors:
            print(f"\n⚠️ ERRORS:")
            for error in errors:
                print(f"   ❌ {error}")
    
    def _display_news_results(self, news: list):
        """Zeigt RSS News Ergebnisse"""
        
        if not news:
            print("❌ Keine News gesammelt")
            return
        
        print(f"\n📰 NEWS GESAMMELT: {len(news)}")
        
        # Kategorien zählen
        categories = {}
        sources = {}
        
        for item in news:
            cat = item.get("category", "general") 
            src = item.get("source", "unknown")
            categories[cat] = categories.get(cat, 0) + 1
            sources[src] = sources.get(src, 0) + 1
        
        print(f"\n📂 KATEGORIEN:")
        for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
            print(f"   📂 {cat}: {count} articles")
        
        print(f"\n📰 QUELLEN:")
        for src, count in sorted(sources.items(), key=lambda x: x[1], reverse=True):
            print(f"   📰 {src}: {count} articles")
        
        print(f"\n🎯 TOP 10 NEWS:")
        for i, news_item in enumerate(news[:10], 1):
            title = news_item.get("title", "No title")[:70]
            source = news_item.get("source", "Unknown")
            category = news_item.get("category", "general")
            print(f"   {i:2d}. [{category}] {title}...")
            print(f"       📰 {source}")
    
    def _display_test_results(self, results: dict):
        """Zeigt Service-Test Ergebnisse"""
        
        print(f"\n🧪 TEST RESULTS:")
        
        for service, passed in results.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            service_name = service.replace("_", " ").title()
            print(f"   {status} {service_name}")
        
        total_tests = len(results)
        passed_tests = sum(1 for r in results.values() if r)
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        print(f"\n📊 SUMMARY:")
        print(f"   🎯 Success Rate: {success_rate:.1f}% ({passed_tests}/{total_tests})")
        
        if success_rate >= 75:
            print("   🎉 EXCELLENT - Services are optimized!")
        elif success_rate >= 50:
            print("   ⚠️ GOOD - Minor issues detected")
        else:
            print("   ❌ POOR - Major issues need attention")
    
    def _display_statistics(self, stats: dict, sources: dict):
        """Zeigt detaillierte Statistiken"""
        
        print(f"\n📊 DETAILED STATISTICS:")
        print(f"   📊 Total Sources: {stats.get('total_sources', 0)}")
        print(f"   ✅ Successful: {stats.get('successful_sources', 0)}")
        print(f"   ❌ Failed: {stats.get('failed_sources', 0)}")
        print(f"   📄 Total Items: {stats.get('total_items', 0)}")
        
        # Optimization Metrics
        opt_metrics = stats.get("optimization_metrics", {})
        if opt_metrics:
            print(f"\n🔧 OPTIMIZATION METRICS:")
            print(f"   📰 RSS Articles: {opt_metrics.get('rss_articles', 0)}")
            print(f"   ₿ Bitcoin Timeframes: {opt_metrics.get('bitcoin_timeframes', 0)}")
            print(f"   🌤️ Weather Cities: {opt_metrics.get('weather_cities', 0)}")
        
        # Optimization Score
        opt_score = stats.get("optimization_score", 0)
        print(f"\n🎯 OPTIMIZATION SCORE: {opt_score}/100")
        
        if opt_score >= 80:
            print("   🎉 EXCELLENT - Highly optimized!")
        elif opt_score >= 60:
            print("   ✅ GOOD - Well optimized")
        elif opt_score >= 40:
            print("   ⚠️ FAIR - Room for improvement")
        else:
            print("   ❌ POOR - Needs optimization")


async def main():
    """Main CLI function"""
    
    parser = argparse.ArgumentParser(
        description="CLI Data Collection - Optimierte Datensammlung",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
EXAMPLES:
  python cli_data_collection.py                    # Vollständige Sammlung
  python cli_data_collection.py --test             # Service Tests
  python cli_data_collection.py --news-only        # Nur RSS News
  python cli_data_collection.py --preset bitcoin   # Bitcoin-fokussierte Sammlung
  python cli_data_collection.py --stats            # Nur Statistiken
  python cli_data_collection.py --news-only --limit 50  # 50 News sammeln
        """
    )
    
    parser.add_argument("--test", action="store_true", help="Teste alle Services")
    parser.add_argument("--news-only", action="store_true", help="Sammle nur RSS News")
    parser.add_argument("--stats", action="store_true", help="Zeige nur Statistiken")
    parser.add_argument("--preset", type=str, help="Show Preset (z.B. bitcoin, tech, news)")
    parser.add_argument("--limit", type=int, default=25, help="News Limit (default: 25)")
    parser.add_argument("--max-age", type=int, default=1, help="Max Age in Stunden (default: 1)")
    
    args = parser.parse_args()
    
    cli = DataCollectionCLI()
    success = False
    
    try:
        if args.test:
            success = await cli.run_service_tests()
        elif args.news_only:
            success = await cli.run_news_only(args.limit, args.max_age)
        elif args.stats:
            success = await cli.show_statistics()
        else:
            success = await cli.run_full_collection(args.preset, args.max_age)
        
        if success:
            print(f"\n✅ Data Collection erfolgreich abgeschlossen!")
        else:
            print(f"\n❌ Data Collection fehlgeschlagen!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print(f"\n⚠️ Data Collection abgebrochen!")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Unerwarteter Fehler: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main()) 