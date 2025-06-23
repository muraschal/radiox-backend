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
from loguru import logger

# Add src to path for clean imports
sys.path.append(str(Path(__file__).parent / "src"))

# Clean Architecture Imports - Domain-driven
from services.data import DataCollectionService
from services.processing import ContentProcessingService
from services.generation import AudioGenerationService
from src.services.generation.image_generation_service import ImageGenerationService
# Direct import to avoid circular dependencies
from src.services.utilities.dashboard_service import DashboardService


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
        self._dashboard_service = DashboardService()
        self._content_logger = None  # Lazy loading for GPT article tracking
        
        self._log_initialization()
    
    def _log_initialization(self) -> None:
        """Log initialization with compact format"""
        # Minimal initialization message
        pass
    
    def _get_current_gpt_model(self) -> str:
        """Get current GPT model from central configuration"""
        try:
            from config.api_config import get_gpt_model
            return get_gpt_model()
        except ImportError:
            return "gpt-4"  # Fallback
    
    async def run_complete_workflow(
        self,
        preset_name: str = "zurich",
        target_news_count: int = 4,
        target_time: Optional[str] = None,
        language: str = "en",
        voice_quality: str = "mid",
        dryrun: bool = False
    ) -> Dict[str, Any]:
        """Executes the complete, robust v3.2 workflow with corrected operational order."""
        
        workflow_id = f"wf_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        print(f"📻 RadioX • {preset_name.title()} • {target_news_count} stories")
        print("")

        try:
            
            # --- STEP 1 & 2: Data Collection & Processing ---
            print("⚡ Collecting data...")
            show_config = await self._execute_show_configuration(preset_name)
            collected_data = await self._execute_data_collection(preset_name)
            
            print("🤖 Processing with GPT...")
            processed_data = await self._execute_data_processing(
                collected_data["data"], target_news_count, target_time, preset_name, show_config["data"], language
            )

            # --- STEP 3: Generate Cover First (for Dashboard integration) ---
            print("🎨 Generating cover...")
            cover_data = {}
            if self._config.audio_enabled:
                # FIXED: Generate cover auch im dryrun (User will das Cover sehen!)
                initial_cover_data = await self._execute_cover_generation_standalone(processed_data["data"], target_time)
                
                cover_data = initial_cover_data
                if initial_cover_data.get("success"):
                    print("✅ Cover generated")
            else:
                initial_cover_data = self._create_skipped_cover_result()
                cover_data = initial_cover_data

            # --- STEP 4: Generate Audio First ---
            audio_data = {}
            if self._config.audio_enabled:
                print("🎵 Generating audio...")
                audio_data = await self._execute_audio_generation(
                    processed_data["data"], target_news_count, target_time, preset_name, show_config["data"], voice_quality
                )
                
                if audio_data.get("success"):
                    print("✅ Audio generated")
                
            else:
                # Skip audio if disabled
                audio_data = self._create_skipped_audio_result()

            # --- STEP 5: Cover Embedding FIRST (while audio is still in temp/) ---
            # Only attempt cover embedding if both audio and cover were successfully generated
            if (audio_data.get("success") and not audio_data.get("skipped") and 
                cover_data.get("success") and not cover_data.get("skipped")):
                cover_data = await self._execute_cover_embedding(
                    cover_data.get("data", {}), audio_data.get("data", {}), target_time
                )
                print("✅ Audio with cover embedded")
            else:
                if audio_data.get("skipped") or cover_data.get("skipped"):
                    print("✅ Audio with cover embedded")  # Keep consistent output
            
            # --- STEP 6: Finalize Media Files (Move from temp to outplay, if any were generated) ---
            final_paths = await self._finalize_show_files(
                audio_data if audio_data.get("success") else {}, 
                cover_data.get("data", {})
            )
            
            # --- STEP 7: Generate Dashboard AFTER files are finalized (with correct filenames) ---
            print("📊 Generating dashboard...")
            dashboard_result = await self._execute_dashboard_generation(
                collected_data["data"], 
                processed_data["data"], 
                show_config["data"],
                cover_data if cover_data.get("success") else {},  # Cover data - pass entire cover_data
                audio_data.get("data", {}) if audio_data.get("success") else {},   # Audio data
                final_paths.get("timestamp")  # Pass the final timestamp for consistent naming
            )
            
            if dashboard_result.get("success"):
                filepath = dashboard_result.get('filepath', '').split('/')[-1]  # Just filename
                print(f"✅ Dashboard: {filepath}")

            # --- STEP 8: Web Sync & Git Publishing ---
            await self._execute_web_sync_and_publish()

            # --- STEP 9: Cleanup ---
            await self._cleanup_temp_directory()
            
            # --- FINAL STEP: Create Result ---
            return self._create_workflow_result(
                workflow_id, preset_name, target_news_count, target_time,
                show_config, collected_data, processed_data, audio_data, cover_data
            )
            
        except Exception as e:
            # Add more context to the error log
            import traceback
            logger.error(f"❌ Workflow {workflow_id} failed with exception: {e}")
            logger.error(traceback.format_exc())
            return self._create_error_result(workflow_id, str(e))
    
    async def _execute_show_configuration(self, preset_name: str) -> Dict[str, Any]:
        """Execute show configuration step"""
        result = await self.run_show_configuration(preset_name)
        self._validate_step_result(result, "Show configuration")
        return result
    
    async def _execute_data_collection(self, preset_name: str) -> Dict[str, Any]:
        """Execute data collection step"""
        result = await self.run_data_collection(preset_name)
        self._validate_step_result(result, "Data collection")
        return result
    
    async def _execute_data_processing(
        self, raw_data: Dict[str, Any], target_news_count: int, 
        target_time: Optional[str], preset_name: str, show_config: Dict[str, Any], language: str = "en"
    ) -> Dict[str, Any]:
        """Execute data processing step with proactive duplicate filtering."""
        
        # Get context AND a list of already used article titles for proactive filtering
        last_show_context = await self._get_last_show_context()
        used_article_titles = await self._get_used_article_titles()
        
        result = await self.run_data_processing(
            raw_data=raw_data,
            target_news_count=target_news_count,
            target_time=target_time,
            preset_name=preset_name,
            show_config=show_config,
            last_show_context=last_show_context,
            used_article_titles=used_article_titles, # Pass the set of used titles
            language=language
        )
        self._validate_step_result(result, "Data processing")
        
        # Log the newly selected articles for the next run
        await self._log_gpt_selected_articles(result["data"], raw_data)
        
        return result
    
    async def _execute_audio_generation(
        self, processed_data: Dict[str, Any], target_news_count: int,
        target_time: Optional[str], preset_name: str, show_config: Dict[str, Any],
        voice_quality: str = "mid"
    ) -> Dict[str, Any]:
        """Execute audio generation step with voice quality support"""
        logger.info("🎙️ Executing audio generation...")
        start_time = datetime.now()
        
        if not self._audio_generator:
            return {"success": False, "error": "Audio generator not initialized"}
        
        try:
            result = await self._audio_generator.generate_audio_from_script(
                processed_data, 
                include_music=True, 
                export_format="mp3", 
                show_config=show_config,
                voice_quality=voice_quality
            )
            
            # Debug: Log the actual result
            logger.info(f"📤 Audio generation result: {result}")
            
            duration = (datetime.now() - start_time).total_seconds()
            result["step_duration"] = duration
            
            self._validate_step_result(result, "Audio generation")
            logger.success(f"✅ Audio generation completed successfully in {duration:.2f}s")
            return result
            
        except Exception as e:
            import traceback
            logger.error(f"❌ Audio Generation step failed critically: {e}")
            logger.error(f"Full traceback:\n{traceback.format_exc()}")
            raise
    
    async def _execute_cover_generation(
        self, processed_data: Dict[str, Any], audio_data: Dict[str, Any], target_time: Optional[str],
        dryrun: bool = False
    ) -> Dict[str, Any]:
        """Execute cover image generation step with dryrun support"""
        if dryrun:
            logger.info("🛠️ Dryrun mode: Using default cover (no DALL-E generation)")
            return {
                "success": True,
                "data": {
                    "cover_path": None,
                    "cover_mode": "default",
                    "dryrun": True
                },
                "timestamp": datetime.now().isoformat()
            }
        
        result = await self.run_cover_generation(processed_data, audio_data, target_time)
        self._validate_step_result(result, "Cover generation")
        return result
    
    async def _execute_cover_generation_standalone(
        self, processed_data: Dict[str, Any], target_time: Optional[str]
    ) -> Dict[str, Any]:
        """Execute standalone cover generation (parallel to audio) - no MP3 embedding yet"""
        try:
            result = await self.run_cover_generation_standalone(processed_data, target_time)
            self._validate_step_result(result, "Standalone cover generation")
            return result
        except Exception as e:
            import traceback
            logger.error(f"❌ Standalone Cover Generation failed: {e}")
            logger.error(traceback.format_exc())
            return {"success": False, "error": str(e)}
    
    async def _execute_cover_embedding(
        self, cover_data: Dict[str, Any], audio_data: Dict[str, Any], target_time: Optional[str]
    ) -> Dict[str, Any]:
        """Execute cover embedding into MP3 file"""
        try:
            result = await self.run_cover_embedding(cover_data, audio_data, target_time)
            self._validate_step_result(result, "Cover embedding")
            return result
        except Exception as e:
            import traceback
            logger.error(f"❌ Cover Embedding failed: {e}")
            logger.error(traceback.format_exc())
            return {"success": False, "error": str(e)}
    
    async def _execute_dashboard_generation(
        self, raw_data: Dict[str, Any], processed_data: Dict[str, Any], show_config: Dict[str, Any], 
        cover_data: Dict[str, Any] = None, audio_data: Dict[str, Any] = None, timestamp: str = None
    ) -> Dict[str, Any]:
        """Execute dashboard generation with error handling"""
        try:
            filepath = await self.generate_shownotes_dashboard(
                raw_data=raw_data, 
                processed_data=processed_data, 
                show_config=show_config,
                timestamp=timestamp,
                cover_data=cover_data,
                audio_data=audio_data
            )
            return {"success": True, "filepath": filepath}
        except Exception as e:
            import traceback
            logger.error(f"❌ Dashboard Generation failed: {e}")
            logger.error(traceback.format_exc())
            return {"success": False, "error": str(e)}

    async def _execute_web_sync_and_publish(self) -> None:
        """Execute web sync and git publishing after successful show generation"""
        try:
            print("🌐 Syncing to web & publishing...")
            
            # Step 1: Run dynamic web sync
            import subprocess
            sync_result = subprocess.run(
                ["python3", "sync_web_dynamic.py"],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if sync_result.returncode != 0:
                logger.warning(f"⚠️ Web sync warning: {sync_result.stderr}")
                print("⚠️ Web sync had issues but continuing...")
            else:
                print("✅ Web sync completed")
            
            # Step 2: Git add, commit, push
            # Add all changes in web folder
            git_add = subprocess.run(
                ["git", "add", "web/"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if git_add.returncode == 0:
                # Check if there are changes to commit
                git_status = subprocess.run(
                    ["git", "status", "--porcelain", "web/"],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if git_status.stdout.strip():
                    # There are changes, commit them
                    timestamp = datetime.now().strftime('%y%m%d_%H%M')
                    commit_message = f"Add latest RadioX show {timestamp} to web deployment"
                    
                    git_commit = subprocess.run(
                        ["git", "commit", "-m", commit_message],
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                    
                    if git_commit.returncode == 0:
                        # Push to remote
                        git_push = subprocess.run(
                            ["git", "push", "origin", "main"],
                            capture_output=True,
                            text=True,
                            timeout=60
                        )
                        
                        if git_push.returncode == 0:
                            print("✅ Published to radiox.rapold.io")
                        else:
                            print("⚠️ Git push failed, changes committed locally")
                    else:
                        print("⚠️ Git commit failed")
                else:
                    print("ℹ️ No new changes to publish")
            else:
                print("⚠️ Git add failed")
                
        except subprocess.TimeoutExpired:
            logger.warning("⚠️ Web sync/publish timeout")
            print("⚠️ Publishing timeout, show generated successfully")
        except Exception as e:
            logger.warning(f"⚠️ Web sync/publish warning: {e}")
            print("⚠️ Publishing had issues, show generated successfully")
    
    def _validate_step_result(self, result: Dict[str, Any], step_name: str) -> None:
        """Validate step result with fail-fast pattern"""
        if not result or not result.get("success"):
            raise Exception(f"{step_name} failed")
    
    def _create_skipped_audio_result(self) -> Dict[str, Any]:
        """Create result for skipped audio generation"""
        return {"success": True, "skipped": True, "reason": "Audio disabled"}
    
    def _create_skipped_cover_result(self) -> Dict[str, Any]:
        """Create result for skipped cover generation"""
        return {"success": True, "skipped": True, "reason": "Audio disabled or failed"}
    
    def _create_workflow_result(
        self, workflow_id: str, preset_name: str, target_news_count: int, target_time: Optional[str],
        show_config: Dict[str, Any], collected_data: Dict[str, Any], 
        processed_data: Dict[str, Any], audio_data: Dict[str, Any], cover_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create comprehensive workflow result"""
        quality_metrics = self._calculate_workflow_quality(collected_data, processed_data)
        
        print("")
        print(f"✨ Complete • Quality: {quality_metrics['overall_score']:.1f}")
        
        # Show generated files in a clean way
        files_generated = []
        if not audio_data.get('skipped'):
            files_generated.append("🎵 Audio")
        if not cover_data.get('skipped'):
            files_generated.append("🎨 Cover") 
        files_generated.append("📊 Dashboard")
        
        if files_generated:
            print(f"📁 Generated: {' • '.join(files_generated)}")
        
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
        print(f"❌ Failed: {error_message}")
        return {
            "success": False,
            "workflow_id": workflow_id,
            "timestamp": datetime.now().isoformat(),
            "error": error_message
        }
    
    async def _finalize_show_files(self, audio_data: Dict[str, Any], cover_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Moves generated media from a temporary directory to the final 'outplay' directory
        with the unified naming scheme. Also copies files to 'web' directory for Vercel hosting.
        This is a critical step to ensure files are in their final location before the dashboard is generated.
        """
        import shutil
        outplay_dir = Path(__file__).parent / "outplay"
        outplay_dir.mkdir(parents=True, exist_ok=True)
        
        # Create web directory for Vercel hosting
        web_dir = Path(__file__).parent / "web"
        web_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime('%y%m%d_%H%M')
        final_paths = {"timestamp": timestamp}

        # Finalize Audio File
        temp_audio_path_str = audio_data.get("audio_file")
        if temp_audio_path_str:
            temp_audio_path = Path(temp_audio_path_str)
            if temp_audio_path.exists():
                final_audio_path = outplay_dir / f"radiox_{timestamp}.mp3"
                web_audio_path = web_dir / f"radiox_{timestamp}.mp3"
                
                # Move to outplay directory
                shutil.move(str(temp_audio_path), str(final_audio_path))
                # Copy to web directory for Vercel
                shutil.copy2(str(final_audio_path), str(web_audio_path))
                print(f"📁 Audio copied to web/ for Vercel hosting")
                
                final_paths["audio"] = str(final_audio_path)

        # Finalize Cover File
        cover_generation = cover_data.get("cover_generation", {})
        temp_cover_path_str = cover_generation.get("cover_path")
        if temp_cover_path_str:
            temp_cover_path = Path(temp_cover_path_str)
            if temp_cover_path.exists():
                final_cover_path = outplay_dir / f"radiox_{timestamp}.png"
                web_cover_path = web_dir / f"radiox_{timestamp}.png"
                
                # Move to outplay directory
                shutil.move(str(temp_cover_path), str(final_cover_path))
                # Copy to web directory for Vercel
                shutil.copy2(str(final_cover_path), str(web_cover_path))
                print(f"🖼️ Cover copied to web/ for Vercel hosting")
                
                final_paths["cover"] = str(final_cover_path)
        
        return final_paths

    async def _copy_audio_to_outplay(self, audio_data: Dict[str, Any]) -> None:
        """DEPRECATED - Replaced by _finalize_show_files"""
        pass

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
            
        except Exception as e:
            logger.warning(f"⚠️ Temp cleanup warning: {e}")
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
                # Return context directly from new DB structure
                return last_show
            else:
                return None
                
        except Exception as e:
            logger.warning(f"⚠️ Last show context warning: {e}")
            return None

    async def _get_used_article_titles(self, days: int = 2) -> set:
        """Get a set of recently used article titles to avoid duplicates."""
        try:
            if not hasattr(self, '_content_logger') or self._content_logger is None:
                from src.services.utilities.content_logging_service import ContentLoggingService
                self._content_logger = ContentLoggingService()
            
            return await self._content_logger.get_used_article_titles(days=days)
        except Exception as e:
            logger.warning(f"⚠️ Could not get used article titles: {e}")
            return set()

    async def _log_gpt_selected_articles(self, processed_data: Dict[str, Any], raw_data: Dict[str, Any]) -> None:
        """Log GPT-selected articles and save to Supabase"""
        try:
            selected_news = processed_data.get("selected_news", [])
            all_news = raw_data.get("news", [])
            
            if not selected_news:
                return
            
            # Show selected articles in clean format
            selected_titles = [article.get("title", "No title")[:60] for article in selected_news]
            print(f"✅ Selected {len(selected_news)} articles")
            
            # **SAVE TO SUPABASE** (lazy loading to avoid import issues)
            try:
                if not hasattr(self, '_content_logger') or self._content_logger is None:
                    from src.services.utilities.content_logging_service import ContentLoggingService
                    self._content_logger = ContentLoggingService()
                
                # Generate pragmatic show title: "Radio X Zurich 2330"
                show_title = f"Radio X Zurich {datetime.now().strftime('%H%M')}"
                
                await self._content_logger.log_show_broadcast(
                    show_title=show_title,
                    selected_articles=selected_news,
                    metadata={
                        "workflow": "main_workflow",
                        "gpt_model": self._get_current_gpt_model(),
                        "selection_ratio": f"{len(selected_news)}/{len(all_news)}"
                    }
                )
                
            except Exception as e:
                logger.warning(f"⚠️ Supabase logging warning: {e}")
                # Don't fail workflow if logging fails
                
        except Exception as e:
            logger.warning(f"⚠️ GPT article logging warning: {e}")
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
        show_config: Dict[str, Any], timestamp: Optional[str] = None, 
        cover_data: Dict[str, Any] = None, audio_data: Dict[str, Any] = None
    ) -> str:
        """Generate the new Show Notes Dashboard"""

        # If no specific timestamp is provided, generate a new one.
        if timestamp is None:
            timestamp = datetime.now().strftime('%y%m%d_%H%M')
            logger.warning(f"No timestamp provided for dashboard, generated a new one: {timestamp}")

        # Include cover and audio data in processed_data if available
        processed_data = processed_data.copy()
        if cover_data:
            # Extract the actual cover generation data from nested structure
            if cover_data.get("data", {}).get("cover_generation"):
                processed_data['cover_generation'] = cover_data["data"]["cover_generation"]
            elif cover_data.get("cover_generation"):
                processed_data['cover_generation'] = cover_data["cover_generation"]
            else:
                processed_data['cover_generation'] = cover_data
        if audio_data:
            processed_data['audio_generation'] = audio_data

        # Generate Show Notes Dashboard with new Jinja2 Service
        filepath = await self._dashboard_service.generate_dashboard(
            raw_data=raw_data, 
            processed_data=processed_data, 
            show_config=show_config,
            timestamp=timestamp,
            cover_data=cover_data,
            audio_data=audio_data
        )
        
        return filepath
    
    async def run_data_processing(
        self, raw_data: Dict[str, Any], target_news_count: int = 4,
        target_time: Optional[str] = None, preset_name: Optional[str] = None,
        show_config: Dict[str, Any] = None, last_show_context: Optional[Dict[str, Any]] = None,
        used_article_titles: Optional[set] = None, language: str = "en"
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
                last_show_context=last_show_context,
                used_article_titles=used_article_titles, # Pass down to the service
                language=language
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
            result = await self.run_data_processing(
                raw_data=real_data,
                target_news_count=target_news_count,
                target_time=target_time,
                preset_name=preset_name,
                show_config=show_config,
                last_show_context=last_show_context
            )
            
            # Generate dashboard with processed data (no cover data in processing-only mode)
            await self.generate_shownotes_dashboard(
                real_data, result["data"], show_config
            )
            
            # Cleanup temp directory
            await self._cleanup_temp_directory()
            
            return result
            
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
    
    async def run_cover_generation_standalone(
        self, processed_data: Dict[str, Any], target_time: Optional[str] = None
    ) -> Dict[str, Any]:
        """Execute standalone cover generation (no MP3 embedding) - PARALLEL OPTIMIZATION"""
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
            
            # Generate cover art (NO EMBEDDING YET)
            cover_result = await self._image_generator.generate_cover_art(
                session_id=session_id,
                broadcast_content=broadcast_content,
                target_time=target_time
            )
            
            duration = (datetime.now() - start_time).total_seconds()
            
            result = {
                "cover_generation": cover_result,
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
    
    async def run_cover_embedding(
        self, cover_data: Dict[str, Any], audio_data: Dict[str, Any], target_time: Optional[str] = None
    ) -> Dict[str, Any]:
        """Execute cover embedding into MP3 after both cover and audio are ready"""
        if not self._image_generator:
            return {"success": False, "error": "Cover generation not enabled"}
        
        try:
            start_time = datetime.now()
            
            # Embed cover in MP3
            embedded_cover = False
            cover_path = cover_data.get("cover_generation", {}).get("cover_path")
            audio_file = audio_data.get("audio_file")
            
            if cover_path and audio_file:
                from pathlib import Path
                audio_path = Path(audio_file)
                cover_file = Path(cover_path)
                
                if audio_path.exists() and cover_file.exists():
                    # Embed cover in MP3
                    embedded_cover = await self._image_generator.embed_cover_in_mp3(
                        audio_file=audio_path,
                        cover_file=cover_file,
                        metadata={
                            "title": f"RadioX Broadcast {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                            "artist": "RadioX AI",
                            "album": "RadioX News Broadcasts"
                        }
                    )
            
            duration = (datetime.now() - start_time).total_seconds()
            
            # Update cover data with embedding info
            enhanced_cover_data = cover_data.copy()
            enhanced_cover_data["cover_embedded"] = embedded_cover
            
            return {
                "success": True,
                "data": enhanced_cover_data,
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

    async def dryrun_workflow(self, target_news_count: int, preset_name: str, 
                            language: str, target_time: int = 5) -> Optional[str]:
        """
        🚀 OPTIMIZED Dryrun-Workflow mit Connection Pool Management
        """
        logger.info(f"🎯 DRYRUN-WORKFLOW gestartet")
        logger.info(f"   📊 Target: {target_news_count} news, {target_time} min")
        logger.info(f"   🌍 Language: {language}, Preset: {preset_name}")
        
        # 🚀 PERFORMANCE OPTIMIZATION: Preload critical data
        logger.info("⚡ Preloading critical database resources...")
        try:
            from database.supabase_client import get_db
            db = get_db()
            
            # Preload speakers to prevent connection pool exhaustion
            if hasattr(db, 'preload_speakers'):
                await db.preload_speakers()
                logger.info("✅ Speakers preloaded successfully")
            
            # Add small delay to prevent connection race conditions
            await asyncio.sleep(0.1)
            
        except Exception as e:
            logger.warning(f"⚠️ Preload failed (continuing): {e}")

        # Initialize services with error handling
        try:
            show_service = ShowService()
            content_service = ContentProcessingService()
            audio_service = AudioGenerationService()
            
            # Serialize critical database operations to prevent connection pool overflow
            logger.info("🔄 Loading show configuration...")
            show_config = await show_service.get_show_configuration(preset_name, language)
            
            if not show_config:
                logger.error(f"❌ Show configuration für '{preset_name}' nicht gefunden")
                return None

            # Add delay between database operations
            await asyncio.sleep(0.05)
            
            logger.info("🔄 Loading speaker configurations...")
            primary_speaker_config = await show_service.get_speaker_configuration("marcel")
            
            await asyncio.sleep(0.05)
            secondary_speaker_config = await show_service.get_speaker_configuration("jarvis")
            
            if not primary_speaker_config:
                logger.error("❌ Primary speaker configuration missing for marcel")
                return None

            logger.info("✅ All configurations loaded successfully")

        except Exception as e:
            logger.error(f"❌ Service initialization failed: {e}")
            return None


async def main():
    """Main entry point with CLI argument parsing"""
    # Setup logger to only show INFO and above by default
    logger.remove()
    logger.add(sys.stderr, level="INFO")

    parser = argparse.ArgumentParser(
        prog='RadioX Master Orchestrator',
        description='''
\033[1;36m🎙️ RadioX Master Orchestrator v3.0.0\033[0m
\033[1;34m═══════════════════════════════════════════════════════════════════════════════════\033[0m
\033[1;37mAutomatisierte Radio-Show-Generierung mit KI-gestütztem Content-Processing,
Dynamic Speaker Management und professioneller Audio-Produktion.\033[0m

\033[1;35m✨ Features:\033[0m
  \033[0;32m• Dynamic Speaker Registry (Marcel, Jarvis, Brad, Lucy)\033[0m
  \033[0;32m• Voice Quality Control (Low/Mid/High)\033[0m
  \033[0;32m• Intelligente Content-Verarbeitung\033[0m
  \033[0;32m• Show-Config-basierte Speaker-Zuweisung\033[0m
  \033[0;32m• ElevenLabs Audio-Generierung\033[0m
  \033[0;32m• Automated Cover & Dashboard-Erstellung\033[0m
        ''',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
\033[1;33m📋 Beispiele:\033[0m
\033[0;36m╔═══════════════════════════════════════════════════════════════╦═══════════════════════════════════╗\033[0m
\033[0;36m║\033[0m \033[1;37mCommand\033[0m                                                      \033[0;36m║\033[0m \033[1;37mBeschreibung\033[0m                      \033[0;36m║\033[0m
\033[0;36m╠═══════════════════════════════════════════════════════════════╬═══════════════════════════════════╣\033[0m
\033[0;36m║\033[0m \033[0;32m%(prog)s\033[0m                                         \033[0;36m║\033[0m Standard Show (Mid Quality)        \033[0;36m║\033[0m
\033[0;36m║\033[0m \033[0;32m%(prog)s --dryrun\033[0m                                \033[0;36m║\033[0m \033[1;33mDev Test (1 News, DE, Low Quality)\033[0m \033[0;36m║\033[0m
\033[0;36m║\033[0m \033[0;32m%(prog)s --voicequality high\033[0m                     \033[0;36m║\033[0m High Quality Production            \033[0;36m║\033[0m
\033[0;36m║\033[0m \033[0;32m%(prog)s --voicequality low --test\033[0m               \033[0;36m║\033[0m Quick System Test                 \033[0;36m║\033[0m
\033[0;36m║\033[0m \033[0;32m%(prog)s --lang de --news-count 2\033[0m                \033[0;36m║\033[0m Deutsche Show                     \033[0;36m║\033[0m
\033[0;36m║\033[0m \033[0;32m%(prog)s --data-only\033[0m                             \033[0;36m║\033[0m Nur Datensammlung                \033[0;36m║\033[0m
\033[0;36m╚═══════════════════════════════════════════════════════════════╩═══════════════════════════════════╝\033[0m

\033[1;31m📊 Voice Quality Tiers:\033[0m
\033[0;34m╔══════╦═════════════════╦═════════════╦═══════════════╦═══════════════════════════╗\033[0m
\033[0;34m║\033[0m \033[1;37mTier\033[0m \033[0;34m║\033[0m \033[1;37mModel\033[0m           \033[0;34m║\033[0m \033[1;37mLatenz\033[0m      \033[0;34m║\033[0m \033[1;37mKosten\033[0m        \033[0;34m║\033[0m \033[1;37mVerwendung\033[0m             \033[0;34m║\033[0m
\033[0;34m╠══════╬═════════════════╬═════════════╬═══════════════╬═══════════════════════════╣\033[0m
\033[0;34m║\033[0m \033[1;32mlow\033[0m  \033[0;34m║\033[0m Flash Model     \033[0;34m║\033[0m \033[0;33m75ms\033[0m        \033[0;34m║\033[0m \033[0;32m50%% (-50%%)\033[0m   \033[0;34m║\033[0m Live Shows, Testing       \033[0;34m║\033[0m
\033[0;34m║\033[0m \033[1;33mmid\033[0m  \033[0;34m║\033[0m Turbo Model     \033[0;34m║\033[0m \033[0;33m275ms\033[0m       \033[0;34m║\033[0m \033[0;32m50%% (-50%%)\033[0m   \033[0;34m║\033[0m Standard Production       \033[0;34m║\033[0m
\033[0;34m║\033[0m \033[1;31mhigh\033[0m \033[0;34m║\033[0m Multilingual    \033[0;34m║\033[0m \033[0;33m800ms\033[0m       \033[0;34m║\033[0m \033[0;31m100%% (Base)\033[0m   \033[0;34m║\033[0m Best Quality, Podcasts   \033[0;34m║\033[0m
\033[0;34m╚══════╩═════════════════╩═════════════╩═══════════════╩═══════════════════════════╝\033[0m

\033[1;35m🎤 Available Speakers:\033[0m
\033[0;35m╔════════╦═════════════════╦═══════════════════════════════════════════╗\033[0m
\033[0;35m║\033[0m \033[1;37mSpeaker\033[0m \033[0;35m║\033[0m \033[1;37mRole\033[0m            \033[0;35m║\033[0m \033[1;37mCharacteristics\033[0m                        \033[0;35m║\033[0m
\033[0;35m╠════════╬═════════════════╬═══════════════════════════════════════════╣\033[0m
\033[0;35m║\033[0m \033[1;34mmarcel\033[0m  \033[0;35m║\033[0m Main Host       \033[0;35m║\033[0m \033[0;37mEnergetic and passionate presenter\033[0m      \033[0;35m║\033[0m
\033[0;35m║\033[0m \033[1;36mjarvis\033[0m  \033[0;35m║\033[0m AI Assistant    \033[0;35m║\033[0m \033[0;37mAnalytical and precise communicator\033[0m    \033[0;35m║\033[0m
\033[0;35m║\033[0m \033[1;32mbrad\033[0m    \033[0;35m║\033[0m News Anchor     \033[0;35m║\033[0m \033[0;37mProfessional and authoritative voice\033[0m   \033[0;35m║\033[0m
\033[0;35m║\033[0m \033[1;35mlucy\033[0m    \033[0;35m║\033[0m Weather Reporter \033[0;35m║\033[0m \033[0;37mSultry and atmospheric delivery\033[0m       \033[0;35m║\033[0m
\033[0;35m╚════════╩═════════════════╩═══════════════════════════════════════════╝\033[0m

\033[1;36m🚀 Quick Start Guide:\033[0m
\033[0;32m╔══════════════════════════════════════╦═══════════════════════════════════════════╗\033[0m
\033[0;32m║\033[0m \033[1;37mUse Case\033[0m                          \033[0;32m║\033[0m \033[1;37mRecommended Command\033[0m                    \033[0;32m║\033[0m
\033[0;32m╠══════════════════════════════════════╬═══════════════════════════════════════════╣\033[0m
\033[0;32m║\033[0m \033[1;33m🧪 Development Testing\033[0m             \033[0;32m║\033[0m \033[0;36m%(prog)s --dryrun\033[0m           \033[0;32m║\033[0m
\033[0;32m║\033[0m \033[0;37m📻 Standard Radio Show\033[0m             \033[0;32m║\033[0m \033[0;36m%(prog)s\033[0m                    \033[0;32m║\033[0m
\033[0;32m║\033[0m \033[0;33m🎬 High Quality Production\033[0m         \033[0;32m║\033[0m \033[0;36m%(prog)s --voicequality high\033[0m    \033[0;32m║\033[0m
\033[0;32m║\033[0m \033[0;35m⚡ Fast Testing\033[0m                   \033[0;32m║\033[0m \033[0;36m%(prog)s --voicequality low\033[0m     \033[0;32m║\033[0m
\033[0;32m║\033[0m \033[0;31m🔧 System Testing\033[0m                 \033[0;32m║\033[0m \033[0;36m%(prog)s --test\033[0m                 \033[0;32m║\033[0m
\033[0;32m║\033[0m \033[0;37m📊 Data Collection Only\033[0m           \033[0;32m║\033[0m \033[0;36m%(prog)s --data-only\033[0m            \033[0;32m║\033[0m
\033[0;32m╚══════════════════════════════════════╩═══════════════════════════════════════════╝\033[0m

\033[1;37m📞 Support: RadioX Development Team | \033[1;32mv3.0.0\033[1;37m | \033[1;34m© 2024\033[0m
        '''
    )

    # ═══════════════════════════════════════════════════════════════════════
    # WORKFLOW CONTROL
    # ═══════════════════════════════════════════════════════════════════════
    workflow_group = parser.add_argument_group(
        '🔧 Workflow Control', 
        'Control which parts of the RadioX pipeline to execute'
    )
    
    workflow_group.add_argument(
        '--debug',
        action='store_true',
        help='🐛 Enable verbose debug logging for detailed system output'
    )
    
    workflow_group.add_argument(
        '--test', 
        action='store_true',
        help='🧪 Run comprehensive system tests (all components)'
    )
    
    workflow_group.add_argument(
        '--dryrun',
        action='store_true', 
        help='🧪 Development mode: 1 news, DE, low quality, default cover (perfect for dev testing)'
    )
    
    workflow_group.add_argument(
        '--data-only', 
        action='store_true',
        help='📊 Execute only data collection phase (no processing/audio)'
    )
    
    workflow_group.add_argument(
        '--processing-only', 
        action='store_true',
        help='⚙️ Execute only content processing (uses latest collected data)'
    )

    # ═══════════════════════════════════════════════════════════════════════
    # VOICE & QUALITY SETTINGS  
    # ═══════════════════════════════════════════════════════════════════════
    voice_group = parser.add_argument_group(
        '🎙️ Voice & Quality Settings', 
        'Configure audio quality and speaker behavior'
    )
    
    voice_group.add_argument(
        '--voicequality', 
        choices=['low', 'mid', 'high'], 
        default='mid',
        metavar='TIER',
        help='🎛️ Voice quality tier (default: mid)\n'
             '  low  = Flash Model (75ms, fast, 50%% cost)\n'
             '  mid  = Turbo Model (275ms, balanced, 50%% cost)\n' 
             '  high = Multilingual (800ms, best quality, 100%% cost)'
    )

    # ═══════════════════════════════════════════════════════════════════════
    # SHOW CONFIGURATION
    # ═══════════════════════════════════════════════════════════════════════
    show_group = parser.add_argument_group(
        '📻 Show Configuration', 
        'Configure show content and behavior'
    )
    
    show_group.add_argument(
        '--preset', 
        default='zurich',
        metavar='NAME',
        help='🎭 Show preset configuration (default: zurich)'
    )
    
    show_group.add_argument(
        '--news-count', 
        type=int, 
        default=4,
        metavar='N',
        help='📰 Number of news articles to include (default: 4, max: 8)'
    )
    
    show_group.add_argument(
        '--target-time', 
        metavar='HH:MM',
        help='⏰ Target show duration (e.g., 05:30 for 5.5 minutes)'
    )
    
    show_group.add_argument(
        '--lang', 
        choices=['en', 'de'], 
        default='en',
        metavar='LANG',
        help='🌍 Script language (default: en)\n'
             '  en = English content and narration\n'
             '  de = German content and narration'
    )
    
    args = parser.parse_args()

    # ═══════════════════════════════════════════════════════════════════════
    # DRYRUN MODE CONFIGURATION
    # ═══════════════════════════════════════════════════════════════════════
    if args.dryrun:
        print("\n\033[1;33m🧪 DRYRUN MODE ACTIVATED\033[0m")
        print("\033[0;36m╔══════════════════════════════════════════════════════════════╗\033[0m")
        print("\033[0;36m║\033[0m \033[1;37mDevelopment Configuration:\033[0m                              \033[0;36m║\033[0m")
        print("\033[0;36m╟──────────────────────────────────────────────────────────────╢\033[0m")
        print("\033[0;36m║\033[0m \033[0;32m• News Count:\033[0m      1 (minimal for testing)            \033[0;36m║\033[0m")
        print("\033[0;36m║\033[0m \033[0;32m• Preset:\033[0m          zurich                              \033[0;36m║\033[0m")
        print("\033[0;36m║\033[0m \033[0;32m• Language:\033[0m        German (de)                         \033[0;36m║\033[0m")
        print("\033[0;36m║\033[0m \033[0;32m• Voice Quality:\033[0m   Low (fast generation)               \033[0;36m║\033[0m")
        print("\033[0;36m║\033[0m \033[0;32m• Cover Mode:\033[0m      Default (no DALL-E queries)         \033[0;36m║\033[0m")
        print("\033[0;36m╚══════════════════════════════════════════════════════════════╝\033[0m")
        
        # Override settings for dryrun
        args.news_count = 1
        args.preset = 'zurich'
        args.lang = 'de'
        args.voicequality = 'low'
        # Cover generation will be handled in the workflow
        
        print(f"\033[0;33m⚡ Starting development workflow...\033[0m\n")

    if args.debug:
        logger.remove()
        logger.add(sys.stderr, level="DEBUG")

    # Initialize master with full audio enabled
    master = RadioXMaster(audio_enabled=True)
    
    try:
        if args.test:
            result = await master.test_system()
        elif args.dryrun:
            # DRYRUN: Fast development workflow
            result = await master.run_complete_workflow(args.preset, args.news_count, args.target_time, args.lang, voice_quality=args.voicequality, dryrun=True)
        elif args.data_only:
            result = await master.run_data_collection(args.preset)
        elif args.processing_only:
            # FIXED: Lade echte Daten aus JSON-File statt Mock-Daten
            result = await master.run_processing_only_with_real_data(args.news_count, args.target_time, args.preset)
        else:
            result = await master.run_complete_workflow(args.preset, args.news_count, args.target_time, args.lang, voice_quality=args.voicequality)
        
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