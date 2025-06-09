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
from src.services.generation.image_generation_service import ImageGenerationService
# Direct import to avoid circular dependencies
from src.services.utilities.tailwind_dashboard_service import TailwindDashboardService


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
    
    __slots__ = ('_data_collector', '_content_processor', '_audio_generator', '_image_generator', '_dashboard_service', '_config', '_content_logger')
    
    def __init__(self, audio_enabled: bool = True) -> None:
        self._config = WorkflowConfig(audio_enabled=audio_enabled)
        
        # Dependency injection with lazy loading
        self._data_collector = DataCollectionService()
        self._content_processor = ContentProcessingService()
        self._audio_generator = AudioGenerationService() if audio_enabled else None
        self._image_generator = ImageGenerationService() if audio_enabled else None
        self._dashboard_service = TailwindDashboardService()
        self._content_logger = None  # Lazy loading for GPT article tracking
        
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
            
            # **NEW: Archive old shows before generating new ones**
            await self._archive_old_shows()
            
            # **NEW: Generate Cover Art & Embed in MP3**
            cover_data = await self._execute_cover_generation(
                processed_data["data"], audio_data["data"] if audio_data.get("success") else {}, target_time
            ) if self._config.audio_enabled and audio_data.get("success") else self._create_skipped_cover_result()
            
            # **NEW: Generate Show Notes Dashboard**
            await self.generate_shownotes_dashboard(
                collected_data["data"], processed_data["data"], show_config["data"]
            )
            
            # **NEW: Integrate processing data into comprehensive dashboard**
            await self.integrate_processing_data_into_dashboard(
                collected_data["data"], processed_data["data"], show_config["data"]
            )
            
            # **NEW: Copy MP3 from temp to outplay before cleanup**
            await self._copy_audio_to_outplay(audio_data["data"] if audio_data.get("success") else {})
            
            # **NEW: Cleanup temp directory after successful workflow**
            await self._cleanup_temp_directory()
            
            return self._create_workflow_result(
                workflow_id, preset_name, target_news_count, target_time,
                show_config, collected_data, processed_data, audio_data, cover_data
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
        
        # **NEW: Get last show context from Supabase for GPT**
        last_show_context = await self._get_last_show_context()
        
        result = await self.run_data_processing(
            raw_data, target_news_count, target_time, preset_name, show_config, last_show_context
        )
        self._validate_step_result(result, "Data processing")
        
        # **NEW: Log GPT-selected articles**
        await self._log_gpt_selected_articles(result["data"], raw_data)
        
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
    
    async def _execute_cover_generation(
        self, processed_data: Dict[str, Any], audio_data: Dict[str, Any], target_time: Optional[str]
    ) -> Dict[str, Any]:
        """Execute cover image generation step"""
        print("🎨 COVER GENERATION")
        result = await self.run_cover_generation(processed_data, audio_data, target_time)
        self._validate_step_result(result, "Cover generation")
        print("✅ Cover Generation completed")
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
    
    def _create_skipped_cover_result(self) -> Dict[str, Any]:
        """Create result for skipped cover generation"""
        print("🎨 COVER GENERATION SKIPPED")
        print("✅ Cover skipped (audio disabled or audio failed)")
        return {"success": True, "skipped": True, "reason": "Audio disabled or failed"}
    
    def _create_workflow_result(
        self, workflow_id: str, preset_name: str, target_news_count: int, target_time: Optional[str],
        show_config: Dict[str, Any], collected_data: Dict[str, Any], 
        processed_data: Dict[str, Any], audio_data: Dict[str, Any], cover_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create comprehensive workflow result"""
        quality_metrics = self._calculate_workflow_quality(collected_data, processed_data)
        
        print("🎯 WORKFLOW COMPLETED SUCCESSFULLY")
        print(f"📊 Quality Score: {quality_metrics['overall_score']:.2f}")
        print(f"📰 News Processed: {quality_metrics['news_count']}")
        print(f"🎵 Audio: {'Generated' if not audio_data.get('skipped') else 'Skipped'}")
        print(f"🎨 Cover: {'Generated' if not cover_data.get('skipped') else 'Skipped'}")
        
        return {
                "success": True,
                "workflow_id": workflow_id,
                "timestamp": datetime.now().isoformat(),
            "config": {"preset_name": preset_name, "target_news_count": target_news_count, "target_time": target_time},
                "show_configuration": show_config,
                "data_collection": collected_data,
                "data_processing": processed_data,
                "audio_generation": audio_data,
                "cover_generation": cover_data,
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
    
    async def _archive_old_shows(self) -> None:
        """Archive old show files before creating new ones"""
        try:
            import shutil
            from pathlib import Path
            
            outplay_dir = Path(__file__).parent / "outplay"
            archive_dir = outplay_dir / "archive"
            
            # Create archive directory if it doesn't exist
            archive_dir.mkdir(parents=True, exist_ok=True)
            
            # Find all radiox files in outplay (not in archive subdirectory)
            radiox_files = []
            for pattern in ["radiox_*.mp3", "radiox_*.html", "radiox_*.png"]:
                radiox_files.extend([f for f in outplay_dir.glob(pattern) if f.parent == outplay_dir])
            
            if radiox_files:
                # Create timestamped archive subdirectory
                archive_timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                session_archive_dir = archive_dir / f"show_{archive_timestamp}"
                session_archive_dir.mkdir(exist_ok=True)
                
                archived_count = 0
                for file in radiox_files:
                    try:
                        shutil.move(str(file), str(session_archive_dir / file.name))
                        archived_count += 1
                    except Exception as e:
                        print(f"⚠️ Failed to archive {file.name}: {e}")
                
                print(f"📦 Archived {archived_count} old files to: archive/show_{archive_timestamp}/")
            
        except Exception as e:
            print(f"⚠️ Archive warning: {e}")
            # Don't fail the workflow if archiving fails

    async def _copy_audio_to_outplay(self, audio_data: Dict[str, Any]) -> None:
        """Copy MP3 from temp to outplay before cleanup"""
        try:
            import shutil
            from pathlib import Path
            
            if not audio_data.get("audio_file"):
                return
            
            temp_audio = Path(audio_data["audio_file"])
            if not temp_audio.exists():
                return
            
            # Create outplay directory if it doesn't exist
            outplay_dir = Path(__file__).parent / "outplay"
            outplay_dir.mkdir(parents=True, exist_ok=True)
            
            # Copy MP3 to outplay with unified naming
            timestamp = datetime.now().strftime('%y%m%d_%H%M')
            final_audio = outplay_dir / f"radiox_{timestamp}.mp3"
            
            shutil.copy2(temp_audio, final_audio)
            print(f"🎵 Audio copied to: {final_audio.name}")
            
        except Exception as e:
            print(f"⚠️ Audio copy warning: {e}")
            # Don't fail the workflow if copy fails

    async def _cleanup_temp_directory(self) -> None:
        """Cleanup temp directory after successful workflow"""
        try:
            import shutil
            temp_dir = Path(__file__).parent / "temp"
            
            if temp_dir.exists():
                # Remove all files and subdirectories
                for item in temp_dir.iterdir():
                    if item.is_file():
                        item.unlink()
                    elif item.is_dir():
                        shutil.rmtree(item)
                
                print("🧹 Temp directory cleaned up")
            
        except Exception as e:
            print(f"⚠️ Temp cleanup warning: {e}")
            # Don't fail the workflow if cleanup fails

    async def _get_last_show_context(self) -> Optional[Dict[str, Any]]:
        """Get last show context from Supabase for GPT diversity"""
        try:
            if not hasattr(self, '_content_logger') or self._content_logger is None:
                from src.services.utilities.content_logging_service import ContentLoggingService
                self._content_logger = ContentLoggingService()
            
            # Get the most recent show from Supabase
            last_show = await self._content_logger.get_last_show_context()
            
            if last_show:
                # Extract key information for GPT
                context = {
                    "last_show_timestamp": last_show.get("created_at"),
                    "last_selected_news": last_show.get("selected_news", []),
                    "last_news_titles": [news.get("title", "") for news in last_show.get("selected_news", [])],
                    "last_news_sources": list(set([news.get("source", "") for news in last_show.get("selected_news", [])])),
                    "last_news_categories": list(set([news.get("category", "") for news in last_show.get("selected_news", [])])),
                    "show_count": last_show.get("show_count", 1)
                }
                
                print(f"📚 Last Show Context: {len(context['last_news_titles'])} news from {', '.join(context['last_news_sources'][:3])}")
                return context
            else:
                print("📚 No previous show found - first show generation")
                return None
                
        except Exception as e:
            print(f"⚠️ Last show context warning: {e}")
            return None

    async def _log_gpt_selected_articles(self, processed_data: Dict[str, Any], raw_data: Dict[str, Any]) -> None:
        """Log GPT-selected articles and save to Supabase"""
        try:
            selected_news = processed_data.get("selected_news", [])
            all_news = raw_data.get("news", [])
            
            if not selected_news:
                print("📰 GPT: Keine Artikel ausgewählt")
                return
            
            # **COMMUNICATE GPT SELECTIONS IN LOG**
            print(f"🤖 GPT ARTICLE SELECTION: {len(selected_news)}/{len(all_news)} ausgewählt")
            print("=" * 50)
            for i, article in enumerate(selected_news, 1):
                title = article.get("title", "No title")[:80]
                source = article.get("source", "Unknown").upper()
                relevance = article.get("relevance_reason", "No reason")[:100]
                print(f"{i:2d}. [{source}] {title}")
                print(f"    📝 {relevance}")
            print("=" * 50)
            
            # **SAVE TO SUPABASE** (lazy loading to avoid import issues)
            try:
                if not hasattr(self, '_content_logger') or self._content_logger is None:
                    from src.services.utilities.content_logging_service import ContentLoggingService
                    self._content_logger = ContentLoggingService()
                
                session_id = f"workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                await self._content_logger.log_collected_news(
                    session_id=session_id,
                    collected_news=all_news,
                    selected_news=selected_news,
                    collection_metadata={
                        "workflow": "main_workflow",
                        "gpt_model": "gpt-4",
                        "selection_ratio": f"{len(selected_news)}/{len(all_news)}"
                    }
                )
                print(f"💾 GPT selections saved to Supabase: {session_id}")
                
            except Exception as e:
                print(f"⚠️ Supabase logging warning: {e}")
                # Don't fail workflow if logging fails
                
        except Exception as e:
            print(f"⚠️ GPT article logging warning: {e}")
            # Don't fail workflow if logging fails
    
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

    async def integrate_processing_data_into_dashboard(
        self, raw_data: Dict[str, Any], processed_data: Dict[str, Any], 
        show_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Integrate processing data into comprehensive dashboard"""
        
        # Extract processing information
        processing_info = {
            'gpt_prompt': processed_data.get('gpt_prompt', ''),
            'radio_script': processed_data.get('radio_script', ''),
            'voice_config': processed_data.get('voice_configuration', {}),
            'show_config': show_config
        }
        
        # Merge with raw data for comprehensive dashboard
        enhanced_data = raw_data.copy()
        enhanced_data['processing_data'] = processing_info
        
        # Generate comprehensive dashboard - DEAKTIVIERT (nur Tailwind Dashboard benötigt)
        # await self._data_collector.generate_html_dashboards(enhanced_data)
        
        return enhanced_data
    
    async def generate_shownotes_dashboard(
        self, raw_data: Dict[str, Any], processed_data: Dict[str, Any], 
        show_config: Dict[str, Any]
    ) -> str:
        """Generate the new Show Notes Dashboard"""
        
        # Generate Show Notes Dashboard with DashboardService
        filepath = await self._dashboard_service.generate_shownotes_dashboard(
            raw_data, processed_data, show_config
        )
        
        print(f"📊 Show Notes Dashboard: {filepath}")
        return filepath
    
    async def run_data_processing(
        self, raw_data: Dict[str, Any], target_news_count: int = 4,
        target_time: Optional[str] = None, preset_name: Optional[str] = None,
        show_config: Dict[str, Any] = None, last_show_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute data processing with performance optimization"""
        try:
            start_time = datetime.now()
            
            processed_data = await self._content_processor.process_content_for_show(
                raw_data=raw_data,
                target_news_count=target_news_count,
                target_time=target_time,
                preset_name=preset_name,
                show_config=show_config,
                last_show_context=last_show_context
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
    
    async def run_processing_only_with_real_data(
        self, target_news_count: int = 4, target_time: Optional[str] = None, 
        preset_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Execute processing-only mode with real data from JSON file"""
        try:
            print("📂 LADE ECHTE DATEN FÜR PROCESSING...")
            
            # Lade echte Daten aus dem neuesten JSON-File
            real_data = await self._load_latest_collected_data()
            
            if not real_data:
                raise Exception("Keine gesammelten Daten gefunden. Führe zuerst --data-only aus.")
            
            print(f"✅ {len(real_data.get('news', []))} News aus JSON geladen")
            
            # Lade Show-Konfiguration
            show_config_result = await self.run_show_configuration(preset_name)
            if not show_config_result.get("success"):
                raise Exception(f"Show-Konfiguration konnte nicht geladen werden: {show_config_result.get('error')}")
            
            show_config = show_config_result["data"]
            
            # Get last show context
            last_show_context = await self._get_last_show_context()
            
            # Führe Processing mit echten Daten aus
            return await self.run_data_processing(
                raw_data=real_data,
                target_news_count=target_news_count,
                target_time=target_time,
                preset_name=preset_name,
                show_config=show_config,
                last_show_context=last_show_context
            )
            
        except Exception as e:
            return {"success": False, "error": str(e), "timestamp": datetime.now().isoformat()}
    
    async def _load_latest_collected_data(self) -> Dict[str, Any]:
        """Lädt die neuesten gesammelten Daten aus dem JSON-File"""
        import json
        from pathlib import Path
        
        # Suche nach dem neuesten data_collection_clean.json File
        outplay_dir = Path("outplay")
        json_file = outplay_dir / "data_collection_clean.json"
        
        if not json_file.exists():
            raise Exception(f"JSON-Datei nicht gefunden: {json_file}")
        
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            print(f"📊 Daten geladen: {len(data.get('news', []))} News, Wetter: {'✓' if data.get('weather') else '✗'}, Crypto: {'✓' if data.get('crypto') else '✗'}")
            return data
            
        except Exception as e:
            raise Exception(f"Fehler beim Laden der JSON-Datei: {e}")
    
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
            
            audio_result = await self._audio_generator.generate_audio_from_processed_data(
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
    
    async def run_cover_generation(
        self, processed_data: Dict[str, Any], audio_data: Dict[str, Any], target_time: Optional[str] = None
    ) -> Dict[str, Any]:
        """Execute cover generation and embed in MP3 with performance optimization"""
        if not self._image_generator:
            return {"success": False, "error": "Cover generation not enabled"}
        
        try:
            start_time = datetime.now()
            
            # Generate session ID
            session_id = f"cover_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Extract broadcast content for cover generation
            broadcast_content = {
                "radio_script": processed_data.get("radio_script", ""),
                "selected_news": processed_data.get("selected_news", []),
                "segments": processed_data.get("segments", [])
            }
            
            # Generate cover art
            cover_result = await self._image_generator.generate_cover_art(
                session_id=session_id,
                broadcast_content=broadcast_content,
                target_time=target_time
            )
            
            # If cover generated successfully and audio file exists, embed cover
            embedded_cover = False
            if (cover_result.get("success") and 
                audio_data.get("audio_path") and 
                cover_result.get("cover_path")):
                
                from pathlib import Path
                audio_path = Path(audio_data["audio_path"])
                cover_path = Path(cover_result["cover_path"])
                
                if audio_path.exists() and cover_path.exists():
                    # Embed cover in MP3
                    embedded_cover = await self._image_generator.embed_cover_in_mp3(
                        audio_file=audio_path,
                        cover_file=cover_path,
                        metadata={
                            "title": f"RadioX Broadcast {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                            "artist": "RadioX AI",
                            "album": "RadioX News Broadcasts"
                        }
                    )
            
            duration = (datetime.now() - start_time).total_seconds()
            
            result = {
                "cover_generation": cover_result,
                "cover_embedded": embedded_cover,
                "session_id": session_id
            }
            
            validation_result = self._validate_cover_data(result)
            
            return {
                "success": True,
                "data": result,
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
    
    def _validate_cover_data(self, cover_result: Dict[str, Any]) -> Dict[str, Any]:
        """Validate cover generation result"""
        cover_generated = cover_result.get("cover_generation", {}).get("success", False)
        cover_embedded = bool(cover_result.get("cover_embedded", False))
        has_session_id = bool(cover_result.get("session_id"))
        
        quality_score = (
            (1.0 if cover_generated else 0.0) * 0.6 +
            (1.0 if cover_embedded else 0.0) * 0.3 +
            (1.0 if has_session_id else 0.0) * 0.1
        )
        
        return {
            "cover_generated": cover_generated,
            "cover_embedded": cover_embedded,
            "has_session_id": has_session_id,
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
            # FIXED: Lade echte Daten aus JSON-File statt Mock-Daten
            result = await master.run_processing_only_with_real_data(args.news_count, args.target_time, args.preset)
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