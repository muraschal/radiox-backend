#!/usr/bin/env python3

"""
RadioX Performance CLI
======================

CLI-Tool für Performance-Monitoring und -Optimierung:
- Zeigt aktuelle Performance-Bottlenecks
- Testet API-Response-Zeiten
- Optimiert Konfigurationen
- Überwacht Ressourcenverbrauch
"""

import asyncio
import time
import argparse
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
from loguru import logger

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from src.services.data.data_collection_service import DataCollectionService
from src.services.generation.broadcast_generation_service import BroadcastGenerationService
from src.services.generation.audio_generation_service import AudioGenerationService
from config.settings import get_settings


class PerformanceMonitor:
    """Performance-Monitoring und -Optimierung für RadioX"""
    
    def __init__(self):
        self.settings = get_settings()
        self.data_service = DataCollectionService()
        self.broadcast_service = BroadcastGenerationService()
        self.audio_service = AudioGenerationService()
        
    async def run_performance_test(self) -> Dict[str, Any]:
        """Führt kompletten Performance-Test durch"""
        
        logger.info("🚀 Starte RadioX Performance-Test...")
        
        results = {
            "test_timestamp": datetime.now().isoformat(),
            "rss_collection": await self._test_rss_performance(),
            "gpt_generation": await self._test_gpt_performance(),
            "audio_generation": await self._test_audio_performance(),
            "total_workflow": await self._test_complete_workflow()
        }
        
        # Performance-Report generieren
        await self._generate_performance_report(results)
        
        return results
    
    async def _test_rss_performance(self) -> Dict[str, Any]:
        """Testet RSS-Collection Performance"""
        
        logger.info("📰 Teste RSS-Collection Performance...")
        
        start_time = time.time()
        
        try:
            # Teste parallele RSS-Sammlung
            news_data = await self.data_service.collect_news_only()
            
            end_time = time.time()
            duration = end_time - start_time
            
            news_count = len(news_data.get("news", []))
            
            return {
                "success": True,
                "duration_seconds": round(duration, 2),
                "news_collected": news_count,
                "news_per_second": round(news_count / duration, 2) if duration > 0 else 0,
                "performance_rating": self._rate_performance(duration, "rss")
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "duration_seconds": time.time() - start_time
            }
    
    async def _test_gpt_performance(self) -> Dict[str, Any]:
        """Testet GPT-Generation Performance"""
        
        logger.info("🤖 Teste GPT-Generation Performance...")
        
        start_time = time.time()
        
        try:
            # Teste mit minimalen Daten
            test_content = {
                "selected_news": [
                    {
                        "title": "Performance Test News",
                        "summary": "Test-Nachricht für Performance-Messung.",
                        "primary_category": "test",
                        "source_name": "Test",
                        "hours_old": 1
                    }
                ],
                "context_data": {
                    "weather": {"formatted": "20°C, sonnig"},
                    "crypto": {"formatted": "$100,000 (+2.5%)"}
                }
            }
            
            result = await self.broadcast_service.generate_broadcast(test_content)
            
            end_time = time.time()
            duration = end_time - start_time
            
            script_length = len(result.get("script_content", ""))
            
            return {
                "success": True,
                "duration_seconds": round(duration, 2),
                "script_length": script_length,
                "chars_per_second": round(script_length / duration, 2) if duration > 0 else 0,
                "performance_rating": self._rate_performance(duration, "gpt")
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "duration_seconds": time.time() - start_time
            }
    
    async def _test_audio_performance(self) -> Dict[str, Any]:
        """Testet Audio-Generation Performance"""
        
        logger.info("🎵 Teste Audio-Generation Performance...")
        
        start_time = time.time()
        
        try:
            # Teste mit kurzem Skript
            test_script = {
                "session_id": "perf_test",
                "script_content": "MARCEL: Hallo! JARVIS: Hallo zurück! MARCEL: Das war ein Test."
            }
            
            result = await self.audio_service.generate_audio(test_script, include_music=False)
            
            end_time = time.time()
            duration = end_time - start_time
            
            return {
                "success": result.get("success", False),
                "duration_seconds": round(duration, 2),
                "audio_generated": result.get("final_audio_file") is not None,
                "performance_rating": self._rate_performance(duration, "audio")
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "duration_seconds": time.time() - start_time
            }
    
    async def _test_complete_workflow(self) -> Dict[str, Any]:
        """Testet kompletten Workflow"""
        
        logger.info("🔄 Teste kompletten RadioX Workflow...")
        
        start_time = time.time()
        
        try:
            # 1. Daten sammeln
            data = await self.data_service.collect_all_data()
            
            # 2. Broadcast generieren
            broadcast = await self.broadcast_service.generate_broadcast(data)
            
            # 3. Audio generieren (optional)
            # audio = await self.audio_service.generate_audio(broadcast, include_music=False)
            
            end_time = time.time()
            duration = end_time - start_time
            
            return {
                "success": True,
                "duration_seconds": round(duration, 2),
                "news_collected": len(data.get("news", [])),
                "script_generated": len(broadcast.get("script_content", "")),
                "performance_rating": self._rate_performance(duration, "workflow")
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "duration_seconds": time.time() - start_time
            }
    
    def _rate_performance(self, duration: float, test_type: str) -> str:
        """Bewertet Performance basierend auf Dauer"""
        
        thresholds = {
            "rss": {"excellent": 10, "good": 30, "fair": 60},
            "gpt": {"excellent": 30, "good": 90, "fair": 180},
            "audio": {"excellent": 60, "good": 180, "fair": 300},
            "workflow": {"excellent": 120, "good": 300, "fair": 600}
        }
        
        threshold = thresholds.get(test_type, thresholds["workflow"])
        
        if duration <= threshold["excellent"]:
            return "🟢 EXCELLENT"
        elif duration <= threshold["good"]:
            return "🟡 GOOD"
        elif duration <= threshold["fair"]:
            return "🟠 FAIR"
        else:
            return "🔴 SLOW"
    
    async def _generate_performance_report(self, results: Dict[str, Any]):
        """Generiert Performance-Report"""
        
        # Speichere in outplay Ordner
        outplay_dir = Path(__file__).parent.parent / "outplay"
        outplay_dir.mkdir(exist_ok=True)
        
        report_path = outplay_dir / f"performance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        
        html_content = f"""<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🚀 RadioX Performance Report</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #1a1a1a; color: #ffffff; padding: 20px; min-height: 100vh;
        }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .header {{ text-align: center; margin-bottom: 40px; }}
        .header h1 {{ font-size: 3em; margin-bottom: 10px; }}
        .metrics-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-bottom: 40px; }}
        .metric-card {{ background: #2a2a2a; padding: 25px; border-radius: 15px; border-left: 5px solid #4CAF50; }}
        .metric-card.warning {{ border-left-color: #ff9800; }}
        .metric-card.error {{ border-left-color: #f44336; }}
        .metric-title {{ font-size: 1.2em; font-weight: bold; margin-bottom: 15px; }}
        .metric-value {{ font-size: 2em; font-weight: bold; margin-bottom: 10px; }}
        .metric-details {{ color: #cccccc; }}
        .recommendations {{ background: #2a2a2a; padding: 25px; border-radius: 15px; }}
        .recommendations h2 {{ margin-bottom: 20px; color: #4CAF50; }}
        .recommendations ul {{ list-style: none; }}
        .recommendations li {{ margin-bottom: 10px; padding-left: 20px; position: relative; }}
        .recommendations li:before {{ content: "💡"; position: absolute; left: 0; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 RadioX Performance Report</h1>
            <p>Generiert am: {results['test_timestamp']}</p>
        </div>
        
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-title">📰 RSS Collection</div>
                <div class="metric-value">{results['rss_collection'].get('duration_seconds', 'N/A')}s</div>
                <div class="metric-details">
                    {results['rss_collection'].get('news_collected', 0)} News gesammelt<br>
                    {results['rss_collection'].get('performance_rating', 'N/A')}
                </div>
            </div>
            
            <div class="metric-card">
                <div class="metric-title">🤖 GPT Generation</div>
                <div class="metric-value">{results['gpt_generation'].get('duration_seconds', 'N/A')}s</div>
                <div class="metric-details">
                    {results['gpt_generation'].get('script_length', 0)} Zeichen generiert<br>
                    {results['gpt_generation'].get('performance_rating', 'N/A')}
                </div>
            </div>
            
            <div class="metric-card">
                <div class="metric-title">🎵 Audio Generation</div>
                <div class="metric-value">{results['audio_generation'].get('duration_seconds', 'N/A')}s</div>
                <div class="metric-details">
                    Audio: {'✅' if results['audio_generation'].get('audio_generated') else '❌'}<br>
                    {results['audio_generation'].get('performance_rating', 'N/A')}
                </div>
            </div>
            
            <div class="metric-card">
                <div class="metric-title">🔄 Complete Workflow</div>
                <div class="metric-value">{results['total_workflow'].get('duration_seconds', 'N/A')}s</div>
                <div class="metric-details">
                    End-to-End Performance<br>
                    {results['total_workflow'].get('performance_rating', 'N/A')}
                </div>
            </div>
        </div>
        
        <div class="recommendations">
            <h2>💡 Performance-Optimierungen</h2>
            <ul>
                <li>RSS-Feeds parallel sammeln (aktuell: 8 parallel)</li>
                <li>Audio-Segmente parallel generieren (aktuell: 5 parallel)</li>
                <li>GPT-Timeout optimiert auf 180s</li>
                <li>RSS-Timeout optimiert auf 15s</li>
                <li>Caching für häufige API-Calls implementieren</li>
                <li>Datenbank-Queries optimieren</li>
            </ul>
        </div>
    </div>
</body>
</html>"""
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info(f"📊 Performance-Report gespeichert: {report_path}")


async def main():
    """Hauptfunktion für Performance CLI"""
    
    parser = argparse.ArgumentParser(description="RadioX Performance Monitor")
    parser.add_argument("--action", choices=["test", "monitor", "optimize"], default="test",
                       help="Aktion: test (einmaliger Test), monitor (kontinuierlich), optimize (Optimierungen anwenden)")
    
    args = parser.parse_args()
    
    monitor = PerformanceMonitor()
    
    if args.action == "test":
        logger.info("🚀 Starte Performance-Test...")
        results = await monitor.run_performance_test()
        
        print("\n" + "="*60)
        print("🚀 RADIOX PERFORMANCE RESULTS")
        print("="*60)
        
        for test_name, test_result in results.items():
            if test_name == "test_timestamp":
                continue
                
            print(f"\n📊 {test_name.upper()}:")
            if test_result.get("success"):
                print(f"   ⏱️  Dauer: {test_result.get('duration_seconds')}s")
                print(f"   📈 Rating: {test_result.get('performance_rating')}")
            else:
                print(f"   ❌ Fehler: {test_result.get('error')}")
        
        print("\n" + "="*60)
        
    elif args.action == "monitor":
        logger.info("📊 Starte kontinuierliches Performance-Monitoring...")
        # TODO: Implementiere kontinuierliches Monitoring
        
    elif args.action == "optimize":
        logger.info("⚡ Wende Performance-Optimierungen an...")
        # TODO: Implementiere automatische Optimierungen


if __name__ == "__main__":
    asyncio.run(main()) 