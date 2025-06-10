#!/usr/bin/env python3
"""
Content Logging Service - OPTIMIZED & PRAGMATIC
================================================

Vereinfachte Protokollierung für RadioX:
- Show-Titel (z.B. "Radio X Zurich 2300")
- Artikel-Titel als Array
- Minimale, effiziente Struktur

PRAGMATISCHES DESIGN:
- Keine komplexen Dataclasses
- Direkte Supabase-Speicherung  
- Einfache Duplikat-Vermeidung
"""

import asyncio
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional
from loguru import logger

# Supabase für einfache Speicherung
from ..infrastructure.supabase_service import SupabaseService


class ContentLoggingService:
    """
    PRAGMATISCHER Content Logger
    
    Speichert nur das Nötigste:
    - Show-Titel 
    - Verwendete Artikel-Titel
    - Timestamp
    """
    
    def __init__(self):
        """Initialize simplified content logging"""
        self.supabase = SupabaseService()
        
        # Minimale Konfiguration
        self.config = {
            "enable_json_backup": True,  # Lokale JSON-Backups
            "max_show_history": 50      # Letzte 50 Shows behalten
        }
        
        # Logs-Verzeichnis für JSON-Backups
        self.logs_dir = Path(__file__).parent.parent.parent.parent / "logs"
        self.logs_dir.mkdir(exist_ok=True)
        
        logger.info("📋 Pragmatic Content Logging Service initialized")

    async def log_show_broadcast(
        self,
        show_title: str,
        selected_articles: List[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Pragmatische Show-Protokollierung
        
        Args:
            show_title: Titel der Show (z.B. "Radio X Zurich 2300")
            selected_articles: Liste der verwendeten Artikel
            metadata: Optionale Metadaten
            
        Returns:
            Logging-Ergebnis
        """
        
        # Extrahiere nur die Artikel-Titel
        article_titles = [
            article.get("title", "Unknown Article") 
            for article in selected_articles
        ]
        
        logger.info(f"📋 Protokolliere Show: {show_title} mit {len(article_titles)} Artikeln")
        
        try:
            # 1. Supabase-Eintrag (Hauptspeicherung) - minimal schema compatibility  
            log_entry = {
                "session_id": f"show_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "data": {
                    "event_type": "show_broadcast",  # Store in data instead
                    "show_title": show_title,
                    "article_titles": article_titles,
                    "article_count": len(article_titles),
                    "metadata": metadata or {}
                },
                "timestamp": datetime.now().isoformat()
            }
            
            response = self.supabase.client.table('broadcast_logs').insert(log_entry).execute()
            
            if response.data:
                logger.success(f"✅ Show protokolliert: {show_title}")
            else:
                logger.error(f"❌ Supabase-Fehler beim Protokollieren")
                return {"success": False, "error": "Supabase insert failed"}
            
            # 2. Optional: JSON-Backup
            if self.config["enable_json_backup"]:
                await self._create_json_backup(show_title, article_titles, metadata)
            
            # 3. Cleanup alter Einträge
            await self._cleanup_old_shows()
            
            return {
                "success": True,
                "show_title": show_title,
                "articles_logged": len(article_titles),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Fehler bei Show-Protokollierung: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    async def get_last_show_context(self) -> Optional[Dict[str, Any]]:
        """Holt den Kontext der letzten Show für Duplikat-Vermeidung - ROBUST & DEBUG"""
        try:
            # Hole die letzten 10 Einträge für debugging
            response = self.supabase.client.table('broadcast_logs') \
                .select('data, timestamp') \
                .order('timestamp', desc=True) \
                .limit(10) \
                .execute()
            
            logger.info(f"🔍 DB Query: {len(response.data) if response.data else 0} total records found")
            
            # Debug: Print first few entries to understand data structure
            if response.data:
                for i, record in enumerate(response.data[:3]):
                    logger.debug(f"🔍 Record {i+1} type: {type(record)}, value: {record}")
                    
                    # Safe record access
                    if isinstance(record, dict):
                        data = record.get('data', {})
                        if isinstance(data, dict):
                            logger.debug(f"🔍 Record {i+1}: event_type='{data.get('event_type')}', show_title='{data.get('show_title')}', timestamp='{record.get('timestamp')}'")
                        else:
                            logger.debug(f"🔍 Record {i+1}: data is {type(data)}: {data}")
                    else:
                        logger.debug(f"🔍 Record {i+1}: record is {type(record)}: {record}")
            
            # Filter for show_broadcast entries in the data - ROBUST MATCHING
            show_broadcasts = []
            if response.data:
                for record in response.data:
                    # Safe record handling
                    if not isinstance(record, dict):
                        logger.warning(f"⚠️ Unexpected record type: {type(record)}")
                        continue
                        
                    raw_data = record.get('data', {})
                    
                    # Parse JSON string if needed (Supabase returns JSONB as string)
                    if isinstance(raw_data, str):
                        try:
                            import json
                            data = json.loads(raw_data)
                        except json.JSONDecodeError:
                            logger.warning(f"⚠️ Invalid JSON in data field: {raw_data[:100]}...")
                            continue
                    else:
                        data = raw_data
                    
                    # Now data should be a dict
                    if not isinstance(data, dict):
                        logger.warning(f"⚠️ Data is not a dict after parsing: {type(data)}")
                        continue
                    
                    event_type = data.get('event_type', '')
                    
                    # Robustere Filterung: verschiedene event_type Varianten akzeptieren
                    if (event_type == 'show_broadcast' or 
                        'show' in event_type.lower() or 
                        'broadcast' in event_type.lower() or
                        data.get('show_title') or  # Fallback: wenn show_title vorhanden
                        data.get('article_titles')):  # Fallback: wenn article_titles vorhanden
                        show_broadcasts.append(record)
                        logger.debug(f"✅ Found suitable show entry: {data.get('show_title', 'No title')}")
            
            if show_broadcasts:
                last_show = show_broadcasts[0]
                raw_show_data = last_show.get('data', {})
                
                # Parse JSON string if needed (Supabase returns JSONB as string)
                if isinstance(raw_show_data, str):
                    try:
                        import json
                        show_data = json.loads(raw_show_data)
                    except json.JSONDecodeError:
                        logger.error(f"❌ Invalid JSON in show data: {raw_show_data[:100]}...")
                        return None
                else:
                    show_data = raw_show_data
                
                # Extract article titles robustly
                article_titles = show_data.get('article_titles', [])
                show_title = show_data.get('show_title', 'Unknown Show')
                
                context = {
                    'show_title': show_title,
                    'created_at': last_show.get('timestamp'),
                    'selected_news': [],  # Legacy-Kompatibilität
                    'last_news_titles': article_titles,
                    'last_news_sources': [],  # Nicht mehr relevant
                    'last_news_categories': [],  # Nicht mehr relevant
                    'show_count': 1
                }
                
                logger.success(f"📚 Show-Kontext gefunden: '{show_title}' mit {len(article_titles)} Artikeln")
                return context
            
            logger.warning("📚 Keine vorherige Show gefunden - alle Themen verfügbar")
            return None
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Abrufen des letzten Show-Kontexts: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None

    async def get_used_article_titles(self, days: int = 2) -> set:
        """
        Holt verwendete Artikel-Titel der letzten Tage
        
        Args:
            days: Anzahl Tage zurück
            
        Returns:
            Set von bereits verwendeten Artikel-Titeln
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            response = self.supabase.client.table('broadcast_logs') \
                .select('data') \
                .gte('timestamp', cutoff_date.isoformat()) \
                .execute()

            used_titles = set()
            if response.data:
                for record in response.data:
                    raw_data = record.get('data', {})
                    
                    # Parse JSON string if needed (Supabase returns JSONB as string)
                    if isinstance(raw_data, str):
                        try:
                            import json
                            show_data = json.loads(raw_data)
                        except json.JSONDecodeError:
                            continue
                    else:
                        show_data = raw_data
                    
                    # Only process show_broadcast entries
                    if isinstance(show_data, dict) and show_data.get('event_type') == 'show_broadcast':
                        article_titles = show_data.get('article_titles', [])
                        if isinstance(article_titles, list):
                            used_titles.update(article_titles)
            
            logger.info(f"🔎 {len(used_titles)} bereits verwendete Artikel-Titel gefunden")
            return used_titles
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Abrufen verwendeter Titel: {e}")
            return set()

    async def get_used_article_urls(self, days: int = 2) -> set:
        """Legacy-Kompatibilität für URL-basierte Duplikat-Erkennung"""
        # Da wir jetzt titel-basiert arbeiten, geben wir leeres Set zurück
        logger.info("🔄 URL-basierte Duplikat-Erkennung deaktiviert (verwende Titel)")
        return set()

    async def _create_json_backup(
        self, 
        show_title: str, 
        article_titles: List[str], 
        metadata: Optional[Dict[str, Any]]
    ) -> None:
        """Erstellt lokales JSON-Backup"""
        try:
            backup_data = {
                "show_title": show_title,
                "article_titles": article_titles,
                "article_count": len(article_titles),
                "metadata": metadata or {},
                "timestamp": datetime.now().isoformat()
            }
            
            timestamp_str = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = self.logs_dir / f"show_backup_{timestamp_str}.json"
            
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, indent=2, ensure_ascii=False)
            
            logger.debug(f"💾 JSON-Backup erstellt: {backup_file.name}")
            
        except Exception as e:
            logger.warning(f"⚠️ JSON-Backup Fehler: {e}")

    async def _cleanup_old_shows(self) -> None:
        """Bereinigt alte Show-Einträge"""
        try:
            # Behalte nur die letzten max_show_history Shows
            response = self.supabase.client.table('broadcast_logs') \
                .select('id') \
                .order('timestamp', desc=True) \
                .offset(self.config["max_show_history"]) \
                .execute()
            
            if response.data:
                old_ids = [record['id'] for record in response.data]
                
                # Lösche alte Einträge
                for old_id in old_ids:
                    self.supabase.client.table('broadcast_logs') \
                        .delete() \
                        .eq('id', old_id) \
                        .execute()
                
                logger.info(f"🗑️ {len(old_ids)} alte Show-Einträge bereinigt")
                
        except Exception as e:
            logger.warning(f"⚠️ Cleanup Fehler: {e}")

    async def test_content_logging(self) -> bool:
        """Testet das vereinfachte Content Logging"""
        
        # Mock-Daten
        mock_show_title = "Radio X Test 1234"
        mock_articles = [
            {"title": "Test Artikel 1", "source": "Test Source"},
            {"title": "Test Artikel 2", "source": "Test Source"}
        ]
        mock_metadata = {"test": True, "mode": "simplified"}
        
        try:
            result = await self.log_show_broadcast(
                mock_show_title, 
                mock_articles, 
                mock_metadata
            )
            
            logger.info(f"Content Logging Test: {result['success']}")
            return result["success"]
            
        except Exception as e:
            logger.error(f"Content Logging Test Fehler: {e}")
            return False

    # LEGACY METHODS (für Rückwärts-Kompatibilität)
    
    async def log_collected_news(
        self,
        session_id: str,
        collected_news: List[Dict[str, Any]],
        selected_news: List[Dict[str, Any]],
        collection_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Legacy-Wrapper für neue log_show_broadcast Methode"""
        
        # Erstelle Show-Titel aus Session-ID und Zeit
        timestamp = datetime.now().strftime('%H%M')
        show_title = f"Radio X Show {timestamp}"
        
        # Verwende neue vereinfachte Methode
        return await self.log_show_broadcast(
            show_title, 
            selected_news, 
            collection_metadata
        )

    async def log_final_script(
        self,
        session_id: str,
        script_content: str,
        script_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Legacy-Kompatibilität - Scripts werden nicht mehr separat geloggt"""
        logger.info("📝 Script-Logging übersprungen (vereinfachtes System)")
        return {
            "success": True,
            "session_id": session_id,
            "note": "Script logging simplified - not stored separately",
            "timestamp": datetime.now().isoformat()
        } 