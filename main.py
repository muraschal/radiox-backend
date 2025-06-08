#!/usr/bin/env python3

"""
RadioX Master - HIGH PERFORMANCE ORCHESTRATOR
===========================================

Google Engineering Best Practices Implementation:
- SOLID Principles (Single Responsibility, Open/Closed, etc.)
- DRY (Don't Repeat Yourself)
- Clean Code (Readable, Maintainable)
- Performance First (Async, Memory Efficient)
- Fail Fast (Early Validation)

DESIGN PRINCIPLES:
- Clean Architecture (Layered Design)
- Domain-Driven Design (Service Organization)
- Single Responsibility (Each function has one job)
- Separation of Concerns (Clear boundaries)

USAGE:
python main.py                    # Vollständiger Workflow
python main.py --data-only        # Nur Datensammlung
python main.py --processing-only  # Nur Verarbeitung
python main.py --test             # System Tests
"""

import asyncio
import argparse
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass

# Add src to path for clean imports
sys.path.append(str(Path(__file__).parent / "src"))

# Clean Architecture Imports - Domain-driven
from services.data import DataCollectionService
from services.processing import ContentProcessingService
from services.generation import AudioGenerationService


@dataclass(frozen=True)
class WorkflowConfig:
    """Immutable workflow configuration"""
    version: str = "3.0.0"
    architecture: str = "high_performance_clean"
    max_news_count: int = 4
    quality_threshold: float = 0.7
    audio_enabled: bool = True


class RadioXMaster:
    """High-Performance RadioX Orchestrator
    
    Implements Google Engineering Best Practices:
    - Dependency Injection
    - Single Responsibility
    - Fail Fast Pattern
    - Resource Management
    """
    
    __slots__ = ('_data_collector', '_content_processor', '_audio_generator', '_config')
    
    def __init__(self, audio_enabled: bool = True) -> None:
        self._config = WorkflowConfig(audio_enabled=audio_enabled)
        
        # Dependency injection with lazy loading
        self._data_collector = DataCollectionService()
        self._content_processor = ContentProcessingService()
        self._audio_generator = AudioGenerationService() if audio_enabled else None
        
        self._log_initialization()
    
    def _log_initialization(self) -> None:
        """Log initialization with compact format"""
        print(f"🚀 RadioX v{self._config.version} | Audio: {'ON' if self._config.audio_enabled else 'OFF'}")
    
    async def run_complete_workflow(
        self,
        preset_name: str = "zurich",
        target_news_count: int = 4,
        target_time: Optional[str] = None
    ) -> Dict[str, Any]:
        """Execute complete workflow with fail-fast pattern"""
        
        workflow_id = f"wf_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        print(f"🎙️ WORKFLOW {workflow_id} | Preset: {preset_name} | News: {target_news_count}")
        print("=" * 60)
        
        try:
            # Pipeline execution with early validation
            show_config = await self._execute_show_configuration(preset_name)
            collected_data = await self._execute_data_collection(preset_name)
            processed_data = await self._execute_data_processing(
                collected_data["data"], target_news_count, target_time, preset_name, show_config["data"]
            )
            audio_data = await self._execute_audio_generation(
                processed_data["data"], target_news_count, target_time, preset_name, show_config["data"]
            ) if self._config.audio_enabled else self._create_skipped_audio_result()
            
            return self._create_workflow_result(
                workflow_id, preset_name, target_news_count, target_time,
                show_config, collected_data, processed_data, audio_data
            )
            
        except Exception as e:
            return self._create_error_result(workflow_id, str(e))
    
    async def _execute_show_configuration(self, preset_name: str) -> Dict[str, Any]:
        """Execute show configuration step"""
        print("🎭 SHOW CONFIGURATION")
        result = await self.run_show_configuration(preset_name)
        self._validate_step_result(result, "Show configuration")
        print("✅ Show Configuration completed")
        return result
    
    async def _execute_data_collection(self, preset_name: str) -> Dict[str, Any]:
        """Execute data collection step"""
        print("📊 DATA COLLECTION")
        result = await self.run_data_collection(preset_name)
        self._validate_step_result(result, "Data collection")
        print("✅ Data Collection completed")
        return result
    
    async def _execute_data_processing(
        self, raw_data: Dict[str, Any], target_news_count: int, 
        target_time: Optional[str], preset_name: str, show_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute data processing step"""
        print("🔄 DATA PROCESSING")
        result = await self.run_data_processing(raw_data, target_news_count, target_time, preset_name, show_config)
        self._validate_step_result(result, "Data processing")
        print("✅ Data Processing completed")
        return result
    
    async def _execute_audio_generation(
        self, processed_data: Dict[str, Any], target_news_count: int,
        target_time: Optional[str], preset_name: str, show_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute audio generation step"""
        print("🎤 AUDIO GENERATION")
        result = await self.run_audio_generation(processed_data, target_news_count, target_time, preset_name, show_config)
        self._validate_step_result(result, "Audio generation")
        print("✅ Audio Generation completed")
        return result
    
    def _validate_step_result(self, result: Dict[str, Any], step_name: str) -> None:
        """Validate step result with fail-fast pattern"""
        if not result or not result.get("success"):
            raise Exception(f"{step_name} failed")
    
    def _create_skipped_audio_result(self) -> Dict[str, Any]:
        """Create result for skipped audio generation"""
        print("🔇 AUDIO GENERATION SKIPPED")
        print("✅ Audio skipped (--no-audio mode)")
        return {"success": True, "skipped": True, "reason": "Audio disabled"}
    
    def _create_workflow_result(
        self, workflow_id: str, preset_name: str, target_news_count: int, target_time: Optional[str],
        show_config: Dict[str, Any], collected_data: Dict[str, Any], 
        processed_data: Dict[str, Any], audio_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create comprehensive workflow result"""
        quality_metrics = self._calculate_workflow_quality(collected_data, processed_data)
        
        print("🎯 WORKFLOW COMPLETED SUCCESSFULLY")
        print(f"📊 Quality Score: {quality_metrics['overall_score']:.2f}")
        print(f"📰 News Processed: {quality_metrics['news_count']}")
        print(f"🎵 Audio: {'Generated' if not audio_data.get('skipped') else 'Skipped'}")
        
        return {
                "success": True,
                "workflow_id": workflow_id,
                "timestamp": datetime.now().isoformat(),
            "config": {"preset_name": preset_name, "target_news_count": target_news_count, "target_time": target_time},
                "show_configuration": show_config,
                "data_collection": collected_data,
                "data_processing": processed_data,
                "audio_generation": audio_data,
            "quality_metrics": quality_metrics
        }
    
    def _create_error_result(self, workflow_id: str, error_message: str) -> Dict[str, Any]:
        """Create error result"""
        print(f"❌ WORKFLOW FAILED: {error_message}")
        return {
            "success": False,
            "workflow_id": workflow_id,
            "timestamp": datetime.now().isoformat(),
            "error": error_message
        }
    
    async def run_data_collection(self, preset_name: Optional[str] = None) -> Dict[str, Any]:
        """Execute data collection with performance optimization"""
        try:
            start_time = datetime.now()
            collected_data = await self._data_collector.collect_all_data()
            duration = (datetime.now() - start_time).total_seconds()
            
            validation_result = self._validate_collected_data(collected_data)
            
            return {
                "success": True,
                "data": collected_data,
                "validation": validation_result,
                "performance": {"duration_seconds": duration},
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {"success": False, "error": str(e), "timestamp": datetime.now().isoformat()}
    
    async def run_data_processing(
        self, raw_data: Dict[str, Any], target_news_count: int = 4,
        target_time: Optional[str] = None, preset_name: Optional[str] = None,
        show_config: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Execute data processing with performance optimization"""
        try:
            start_time = datetime.now()
            
            processed_data = await self._content_processor.process_content_for_show(
                raw_data=raw_data,
                target_news_count=target_news_count,
                target_time=target_time,
                preset_name=preset_name,
                show_config=show_config
            )
            
            duration = (datetime.now() - start_time).total_seconds()
            validation_result = self._validate_processed_data(processed_data)
            
            return {
                "success": True,
                "data": processed_data,
                "validation": validation_result,
                "performance": {"duration_seconds": duration},
                "timestamp": datetime.now().isoformat()
            }
    
        except Exception as e:
            return {"success": False, "error": str(e), "timestamp": datetime.now().isoformat()}
    
    async def run_show_configuration(self, preset_name: Optional[str] = None) -> Dict[str, Any]:
        """Load show configuration with validation"""
        try:
            show_config = await self._content_processor.get_show_configuration(preset_name or "zurich")
            
            if not show_config:
                raise Exception(f"Show preset '{preset_name}' not found")
            
            return {
                "success": True,
                "data": show_config,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {"success": False, "error": str(e), "timestamp": datetime.now().isoformat()}
    
    async def run_audio_generation(
        self, processed_data: Dict[str, Any], target_news_count: int = 4,
        target_time: Optional[str] = None, preset_name: Optional[str] = None,
        show_config: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Execute audio generation with performance optimization"""
        if not self._audio_generator:
            return {"success": False, "error": "Audio generation not enabled"}
        
        try:
            start_time = datetime.now()
            
            audio_result = await self._audio_generator.generate_show_audio(
                processed_data=processed_data,
                target_news_count=target_news_count,
                target_time=target_time,
                preset_name=preset_name,
                show_config=show_config
            )
            
            duration = (datetime.now() - start_time).total_seconds()
            validation_result = self._validate_audio_data(audio_result)
            
            return {
                "success": True,
                "data": audio_result,
                "validation": validation_result,
                "performance": {"duration_seconds": duration},
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {"success": False, "error": str(e), "timestamp": datetime.now().isoformat()}
    
    async def test_system(self) -> Dict[str, Any]:
        """High-performance system test"""
        print("🧪 SYSTEM TEST")
        print("-" * 40)
        
        tests = [
            ("Data Collection", self._test_data_collection),
            ("Content Processing", self._test_content_processing),
            ("Audio Generation", self._test_audio_generation)
        ]
        
        results = {}
        overall_success = True
        
        for test_name, test_func in tests:
            try:
                start_time = datetime.now()
                result = await test_func()
                duration = (datetime.now() - start_time).total_seconds()
                
                results[test_name] = {
                    "success": result,
                    "duration": duration,
                    "status": "✅ PASS" if result else "❌ FAIL"
                }
                
                print(f"{results[test_name]['status']} {test_name} ({duration:.2f}s)")
                
                if not result:
                    overall_success = False
                    
            except Exception as e:
                results[test_name] = {"success": False, "error": str(e), "status": "❌ ERROR"}
                print(f"❌ ERROR {test_name}: {e}")
                overall_success = False
        
        print(f"\n{'✅ ALL TESTS PASSED' if overall_success else '❌ SOME TESTS FAILED'}")
        
        return {
            "success": overall_success,
            "results": results,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _test_data_collection(self) -> bool:
        """Test data collection service"""
        result = await self.run_data_collection()
        return result.get("success", False)
    
    async def _test_content_processing(self) -> bool:
        """Test content processing service"""
        mock_data = {"news": [], "weather": {}, "crypto": {}}
        result = await self.run_data_processing(mock_data)
        return result.get("success", False)
    
    async def _test_audio_generation(self) -> bool:
        """Test audio generation service"""
        if not self._config.audio_enabled:
            return True  # Skip test if audio disabled
        
        mock_data = {"radio_script": "Test script", "segments": []}
        result = await self.run_audio_generation(mock_data)
        return result.get("success", False)
    
    def _validate_collected_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate collected data quality"""
        news_count = len(raw_data.get("news", []))
        has_weather = bool(raw_data.get("weather"))
        has_crypto = bool(raw_data.get("crypto"))
        
        quality_score = (
            (1.0 if news_count > 0 else 0.0) * 0.7 +
            (1.0 if has_weather else 0.0) * 0.15 +
            (1.0 if has_crypto else 0.0) * 0.15
        )
        
        return {
            "news_count": news_count,
            "has_weather": has_weather,
            "has_crypto": has_crypto,
            "quality_score": quality_score,
            "is_valid": quality_score >= self._config.quality_threshold
        }
    
    def _validate_processed_data(self, processed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate processed data quality"""
        has_script = bool(processed_data.get("radio_script"))
        has_segments = bool(processed_data.get("segments"))
        has_html = bool(processed_data.get("html_dashboard"))
        
        quality_score = (
            (1.0 if has_script else 0.0) * 0.5 +
            (1.0 if has_segments else 0.0) * 0.3 +
            (1.0 if has_html else 0.0) * 0.2
        )
        
        return {
            "has_script": has_script,
            "has_segments": has_segments,
            "has_html": has_html,
            "quality_score": quality_score,
            "is_valid": quality_score >= self._config.quality_threshold
        }
    
    def _calculate_workflow_quality(
        self, collection_result: Dict[str, Any], processing_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate overall workflow quality metrics"""
        collection_quality = collection_result.get("validation", {}).get("quality_score", 0.0)
        processing_quality = processing_result.get("validation", {}).get("quality_score", 0.0)
        
        overall_score = (collection_quality * 0.4) + (processing_quality * 0.6)
        news_count = collection_result.get("validation", {}).get("news_count", 0)
        
        return {
            "overall_score": overall_score,
            "collection_quality": collection_quality,
            "processing_quality": processing_quality,
            "news_count": news_count,
            "grade": "A" if overall_score >= 0.9 else "B" if overall_score >= 0.7 else "C"
        }
    
    def _validate_audio_data(self, audio_result: Dict[str, Any]) -> Dict[str, Any]:
        """Validate audio generation result"""
        has_audio_files = bool(audio_result.get("audio_files"))
        has_metadata = bool(audio_result.get("metadata"))
        
        quality_score = (
            (1.0 if has_audio_files else 0.0) * 0.8 +
            (1.0 if has_metadata else 0.0) * 0.2
        )
        
        return {
            "has_audio_files": has_audio_files,
            "has_metadata": has_metadata,
            "quality_score": quality_score,
            "is_valid": quality_score >= self._config.quality_threshold
        }


async def main():
    """High-performance main function with argument parsing"""
    parser = argparse.ArgumentParser(
        description="RadioX Master - High Performance Radio Show Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                           # Full workflow with audio
  python main.py --no-audio               # HTML dashboard only
  python main.py --data-only              # Data collection only
  python main.py --processing-only        # Processing only
  python main.py --test                   # System tests
        """
    )
    
    # Workflow control
    parser.add_argument("--data-only", action="store_true", help="Nur Datensammlung ausführen")
    parser.add_argument("--processing-only", action="store_true", help="Nur Verarbeitung ausführen")
    parser.add_argument("--test", action="store_true", help="System Tests ausführen")
    parser.add_argument("--no-audio", action="store_true", help="Generiere nur HTML Dashboard ohne Audio (spart ElevenLabs Kosten)")
    
    # Configuration
    parser.add_argument("--preset", default="zurich", help="Show Preset (default: zurich)")
    parser.add_argument("--news-count", type=int, default=4, help="Anzahl News (default: 4)")
    parser.add_argument("--target-time", help="Zielzeit für Show (HH:MM)")
    
    args = parser.parse_args()
    
    # Initialize master with audio setting
    master = RadioXMaster(audio_enabled=not args.no_audio)
    
    try:
        if args.test:
            result = await master.test_system()
        elif args.data_only:
            result = await master.run_data_collection(args.preset)
        elif args.processing_only:
            # Mock data for processing-only mode
            mock_data = {"news": [], "weather": {}, "crypto": {}}
            result = await master.run_data_processing(mock_data, args.news_count, args.target_time, args.preset)
        else:
            result = await master.run_complete_workflow(args.preset, args.news_count, args.target_time)
        
        # Exit with appropriate code
        sys.exit(0 if result.get("success") else 1)
            
    except KeyboardInterrupt:
        print("\n🛑 Workflow interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"💥 Critical error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main()) 