#!/usr/bin/env python3

"""
RadioX CLI - Microservices Client
=================================

Clean Architecture Implementation:
- Single Responsibility: CLI interface only
- Microservices Communication: HTTP API calls
- Separation of Concerns: No business logic
- Fail Fast: Early validation

MICROSERVICES ARCHITECTURE:
- API Gateway: 8000 (Central routing)
- Show Service: 8001 (Show generation)
- Content Service: 8002 (News collection)
- Audio Service: 8003 (TTS + ffmpeg)
- Media Service: 8004 (File management)
- Speaker Service: 8005 (Voice configuration)
- Data Service: 8006 (Database access)
- Analytics Service: 8007 (Metrics)

USAGE:
python main.py --news-count 3 --preset zurich
python main.py --data-only
python main.py --health-check
"""

import asyncio
import argparse
import aiohttp
import sys
from datetime import datetime
from typing import Dict, Any, Optional
from loguru import logger

# Configure logger
logger.remove()
logger.add(sys.stdout, format="{time:HH:mm:ss} | {level} | {message}", level="INFO")


class RadioXClient:
    """
    Clean CLI Client for RadioX Microservices
    
    Single Responsibility: Communicate with microservices via HTTP API
    """
    
    def __init__(self, api_gateway_url: str = "http://localhost:8000"):
        self.api_gateway_url = api_gateway_url
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def health_check(self) -> Dict[str, Any]:
        """Check health of all microservices"""
        try:
            async with self.session.get(f"{self.api_gateway_url}/health") as response:
                if response.status == 200:
                    result = await response.json()
                    print("🟢 All services healthy")
                    return result
                else:
                    print("🔴 Service health issues detected")
                    return {"healthy": False}
        except Exception as e:
            print(f"❌ Cannot connect to API Gateway: {e}")
            return {"error": str(e)}
    
    async def generate_show(
        self, 
        preset: str = "zurich", 
        news_count: int = 3,
        language: str = "en",
        voice_quality: str = "mid"
    ) -> Dict[str, Any]:
        """Generate complete radio show via microservices"""
        
        print(f"🎙️ RadioX • {preset.title()} • {news_count} stories")
        print("")
        
        try:
            # Call show generation endpoint
            payload = {
                "preset": preset,
                "news_count": news_count,
                "language": language,
                "voice_quality": voice_quality
            }
            
            print("🚀 Generating show via microservices...")
            
            async with self.session.post(
                f"{self.api_gateway_url}/generate",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=300)  # 5 minute timeout
            ) as response:
                
                if response.status == 200:
                    result = await response.json()
                    
                    if result.get("success"):
                        print("✅ Show generated successfully")
                        print(f"📁 Files: {result.get('files', {})}")
                        return result
                    else:
                        print(f"❌ Generation failed: {result.get('error')}")
                        return result
                else:
                    error_text = await response.text()
                    print(f"❌ API Error ({response.status}): {error_text}")
                    return {"success": False, "error": f"HTTP {response.status}"}
                    
        except asyncio.TimeoutError:
            print("⏰ Generation timeout - show may still be processing")
            return {"success": False, "error": "Timeout"}
        except Exception as e:
            print(f"❌ Connection error: {e}")
            return {"success": False, "error": str(e)}
    
    async def collect_data_only(self, preset: str = "zurich") -> Dict[str, Any]:
        """Collect data only (no processing)"""
        try:
            async with self.session.post(
                f"{self.api_gateway_url}/data/collect",
                json={"preset": preset}
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    print("✅ Data collection complete")
                    return result
                else:
                    print(f"❌ Data collection failed ({response.status})")
                    return {"success": False}
        except Exception as e:
            print(f"❌ Data collection error: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_service_status(self) -> Dict[str, Any]:
        """Get detailed service status"""
        try:
            async with self.session.get(f"{self.api_gateway_url}/services/status") as response:
                if response.status == 200:
                    result = await response.json()
                    
                    print("📊 Service Status:")
                    for service, status in result.get("services", {}).items():
                        status_icon = "🟢" if status.get("healthy") else "🔴"
                        print(f"  {status_icon} {service}: {status.get('status', 'unknown')}")
                    
                    return result
                else:
                    print("❌ Cannot get service status")
                    return {"error": "Status unavailable"}
        except Exception as e:
            print(f"❌ Status check error: {e}")
            return {"error": str(e)}


async def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        prog="RadioX CLI",
        description="AI Radio Show Generator - Microservices Client"
    )
    
    # Commands
    parser.add_argument("--news-count", type=int, default=3, help="Number of news articles")
    parser.add_argument("--preset", default="zurich", help="Show preset (zurich, basel, etc.)")
    parser.add_argument("--language", default="en", choices=["en", "de"], help="Language")
    parser.add_argument("--voice-quality", default="mid", choices=["low", "mid", "high"], help="Voice quality")
    
    # Modes
    parser.add_argument("--data-only", action="store_true", help="Collect data only")
    parser.add_argument("--health-check", action="store_true", help="Check service health")
    parser.add_argument("--status", action="store_true", help="Show service status")
    
    # API Gateway
    parser.add_argument("--api-url", default="http://localhost:8000", help="API Gateway URL")
    
    args = parser.parse_args()
    
    # Create client
    async with RadioXClient(args.api_url) as client:
        
        if args.health_check:
            await client.health_check()
            
        elif args.status:
            await client.get_service_status()
            
        elif args.data_only:
            await client.collect_data_only(args.preset)
            
        else:
            # Generate complete show
            result = await client.generate_show(
                preset=args.preset,
                news_count=args.news_count,
                language=args.language,
                voice_quality=args.voice_quality
            )
            
            if result.get("success"):
                print("")
                print(f"🎉 RadioX show generated successfully!")
            else:
                print("")
                print(f"💥 Show generation failed")
                sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main()) 