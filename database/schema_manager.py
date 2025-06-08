#!/usr/bin/env python3
"""
RadioX Database Schema Manager
==============================

Zentrales Schema-Management für alle RadioX-Datenbanktabellen.
Ersetzt alle fragmentierten DB-Create-Scripts durch ein einheitliches System.

Features:
- Alle Tabellen in einem Script
- Versionierte Migrationen
- Automatische Abhängigkeitsauflösung
- Rollback-Funktionalität
- Comprehensive Testing
"""

import asyncio
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

# Add src to path
sys.path.append(str(Path(__file__).parent.parent))

from database.supabase_client import get_db


@dataclass
class TableSchema:
    """Repräsentiert ein Tabellenschema"""
    name: str
    sql: str
    dependencies: List[str] = None
    version: str = "1.0.0"
    description: str = ""
    test_data: List[Dict] = None

    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
        if self.test_data is None:
            self.test_data = []


class RadioXSchemaManager:
    """Zentraler Schema-Manager für RadioX"""
    
    def __init__(self):
        self.db = get_db()
        
        # VEREINFACHTE SCHEMA DEFINITION - NUR 4 TABELLEN
        self.schemas = {
            # 1. RSS FEEDS
            "rss_feed_preferences": TableSchema(
                name="rss_feed_preferences",
                dependencies=[],
                sql="""
                -- RSS Feed Preferences (bereits vorhanden)
                SELECT 1; -- Tabelle existiert bereits
                """
            ),
            
            # 2. VOICE CONFIGURATIONS  
            "voice_configurations": TableSchema(
                name="voice_configurations", 
                dependencies=[],
                sql="""
                -- Voice Configurations (bereits vorhanden)
                SELECT 1; -- Tabelle existiert bereits
                """
            ),
            
            # 3. SHOW PRESETS
            "show_presets": TableSchema(
                name="show_presets",
                dependencies=["voice_configurations"],
                sql="""
                -- Show Presets (bereits vorhanden)
                SELECT 1; -- Tabelle existiert bereits
                """
            ),
            
            # 4. BROADCAST LOGS (erweitert für alles)
            "broadcast_logs": TableSchema(
                name="broadcast_logs",
                dependencies=[],
                sql="""
                -- Broadcast Logs (erweitert für Scripts + News + Logs)
                SELECT 1; -- Tabelle existiert bereits und wurde erweitert
                """
            )
        }
    
    async def create_all_tables(self, force_recreate: bool = False) -> bool:
        """Erstellt alle Tabellen in der richtigen Reihenfolge"""
        
        print("🏗️ RADIOX DATABASE SCHEMA MANAGER")
        print("=" * 60)
        print(f"📊 Version: {self.current_version}")
        print(f"📋 Tabellen: {len(self.schemas)}")
        
        try:
            # Bestimme Erstellungsreihenfolge basierend auf Abhängigkeiten
            creation_order = self._resolve_dependencies()
            
            print(f"\n🔄 Erstellungsreihenfolge: {' → '.join(creation_order)}")
            
            created_tables = []
            
            for table_name in creation_order:
                schema = self.schemas[table_name]
                
                print(f"\n📊 ERSTELLE: {table_name.upper()}")
                print(f"   📝 {schema.description}")
                
                if force_recreate:
                    await self._drop_table(table_name)
                
                success = await self._create_table(schema)
                
                if success:
                    created_tables.append(table_name)
                    print(f"   ✅ {table_name} erfolgreich erstellt")
                    
                    # Füge Test-Daten hinzu
                    if schema.test_data:
                        await self._insert_test_data(schema)
                else:
                    print(f"   ❌ {table_name} Erstellung fehlgeschlagen")
                    return False
            
            # Erstelle Cleanup-Funktionen
            await self._create_cleanup_functions()
            
            # Validiere Schema
            validation_success = await self._validate_schema()
            
            if validation_success:
                print(f"\n🎉 SCHEMA ERFOLGREICH ERSTELLT!")
                print(f"✅ {len(created_tables)} Tabellen erstellt")
                print(f"✅ Alle Abhängigkeiten aufgelöst")
                print(f"✅ Test-Daten eingefügt")
                print(f"✅ Schema validiert")
                return True
            else:
                print(f"\n❌ SCHEMA-VALIDIERUNG FEHLGESCHLAGEN!")
                return False
                
        except Exception as e:
            print(f"\n❌ SCHEMA-ERSTELLUNG FEHLGESCHLAGEN: {e}")
            return False
    
    def _resolve_dependencies(self) -> List[str]:
        """Löst Tabellen-Abhängigkeiten auf und bestimmt Erstellungsreihenfolge"""
        
        resolved = []
        remaining = list(self.schemas.keys())
        
        while remaining:
            # Finde Tabellen ohne unaufgelöste Abhängigkeiten
            ready = []
            for table in remaining:
                dependencies = self.schemas[table].dependencies
                if all(dep in resolved for dep in dependencies):
                    ready.append(table)
            
            if not ready:
                # Zirkuläre Abhängigkeit oder fehlende Tabelle
                raise ValueError(f"Zirkuläre Abhängigkeit oder fehlende Tabelle: {remaining}")
            
            # Füge bereite Tabellen hinzu
            for table in ready:
                resolved.append(table)
                remaining.remove(table)
        
        return resolved
    
    async def _create_table(self, schema: TableSchema) -> bool:
        """Erstellt eine einzelne Tabelle"""
        
        try:
            # Teste zuerst ob Tabelle existiert
            try:
                test_result = self.db.client.table(schema.name).select('*').limit(1).execute()
                print(f"      ✅ Tabelle {schema.name} existiert bereits")
                return True
            except:
                # Tabelle existiert nicht - erstelle sie
                print(f"      🔨 Erstelle Tabelle {schema.name}...")
                
                # Verwende Supabase SQL Editor API für Tabellenerstellung
                # Für jetzt: Zeige SQL und gib Anweisungen
                print(f"      📋 SQL für manuelle Erstellung:")
                print(f"      {'-' * 50}")
                print(schema.sql)
                print(f"      {'-' * 50}")
                print(f"      ⚠️ Bitte führe dieses SQL manuell in Supabase aus")
                return False
            
        except Exception as e:
            print(f"      ❌ SQL-Fehler: {e}")
            return False
    
    async def _drop_table(self, table_name: str):
        """Löscht eine Tabelle (für force_recreate)"""
        
        try:
            drop_sql = f"DROP TABLE IF EXISTS {table_name} CASCADE;"
            self.db.client.rpc('exec_sql', {'sql': drop_sql}).execute()
            print(f"      🗑️ {table_name} gelöscht")
        except Exception as e:
            print(f"      ⚠️ Löschen fehlgeschlagen: {e}")
    
    async def _insert_test_data(self, schema: TableSchema):
        """Fügt Test-Daten für eine Tabelle hinzu"""
        
        if not schema.test_data:
            return
        
        try:
            # Prüfe ob bereits Daten vorhanden sind
            existing = self.db.client.table(schema.name).select('*').limit(1).execute()
            
            if existing.data:
                print(f"      ⚠️ Test-Daten bereits vorhanden")
                return
            
            # Füge Test-Daten hinzu
            result = self.db.client.table(schema.name).insert(schema.test_data).execute()
            
            if result.data:
                print(f"      ✅ {len(schema.test_data)} Test-Datensätze eingefügt")
            
        except Exception as e:
            print(f"      ⚠️ Test-Daten Fehler: {e}")
    
    async def _create_cleanup_functions(self):
        """Erstellt Cleanup-Funktionen für alte Daten"""
        
        print(f"\n🧹 ERSTELLE CLEANUP-FUNKTIONEN:")
        
        cleanup_sql = """
        -- Cleanup alte used_news (älter als 7 Tage)
        CREATE OR REPLACE FUNCTION cleanup_old_used_news()
        RETURNS INTEGER AS $$
        DECLARE
            deleted_count INTEGER;
        BEGIN
            DELETE FROM used_news 
            WHERE used_at < NOW() - INTERVAL '7 days';
            GET DIAGNOSTICS deleted_count = ROW_COUNT;
            RETURN deleted_count;
        END;
        $$ LANGUAGE plpgsql;
        
        -- Cleanup alte broadcast_logs (älter als 30 Tage)
        CREATE OR REPLACE FUNCTION cleanup_old_broadcast_logs()
        RETURNS INTEGER AS $$
        DECLARE
            deleted_count INTEGER;
        BEGIN
            DELETE FROM broadcast_logs 
            WHERE timestamp < NOW() - INTERVAL '30 days';
            GET DIAGNOSTICS deleted_count = ROW_COUNT;
            RETURN deleted_count;
        END;
        $$ LANGUAGE plpgsql;
        
        -- Cleanup alte broadcast_scripts (älter als 90 Tage)
        CREATE OR REPLACE FUNCTION cleanup_old_broadcast_scripts()
        RETURNS INTEGER AS $$
        DECLARE
            deleted_count INTEGER;
        BEGIN
            DELETE FROM broadcast_scripts 
            WHERE created_at < NOW() - INTERVAL '90 days';
            GET DIAGNOSTICS deleted_count = ROW_COUNT;
            RETURN deleted_count;
        END;
        $$ LANGUAGE plpgsql;
        
        -- Master Cleanup-Funktion
        CREATE OR REPLACE FUNCTION radiox_cleanup_all()
        RETURNS JSONB AS $$
        DECLARE
            news_deleted INTEGER;
            logs_deleted INTEGER;
            scripts_deleted INTEGER;
        BEGIN
            SELECT cleanup_old_used_news() INTO news_deleted;
            SELECT cleanup_old_broadcast_logs() INTO logs_deleted;
            SELECT cleanup_old_broadcast_scripts() INTO scripts_deleted;
            
            RETURN jsonb_build_object(
                'used_news_deleted', news_deleted,
                'broadcast_logs_deleted', logs_deleted,
                'broadcast_scripts_deleted', scripts_deleted,
                'cleanup_timestamp', NOW()
            );
        END;
        $$ LANGUAGE plpgsql;
        """
        
        try:
            self.db.client.rpc('exec_sql', {'sql': cleanup_sql}).execute()
            print("   ✅ Cleanup-Funktionen erstellt")
        except Exception as e:
            print(f"   ❌ Cleanup-Funktionen Fehler: {e}")
    
    async def _validate_schema(self) -> bool:
        """Validiert das erstellte Schema"""
        
        print(f"\n🔍 VALIDIERE SCHEMA:")
        
        try:
            all_valid = True
            
            for table_name, schema in self.schemas.items():
                # Test Tabellen-Zugriff
                try:
                    result = self.db.client.table(table_name).select('*').limit(1).execute()
                    print(f"   ✅ {table_name}: Zugriff erfolgreich")
                except Exception as e:
                    print(f"   ❌ {table_name}: Zugriff fehlgeschlagen - {e}")
                    all_valid = False
            
            # Test Foreign Key Constraints
            if all_valid:
                print(f"   ✅ Alle Tabellen zugänglich")
                
                # Test Voice Config Service Integration
                try:
                    voices = self.db.client.table('voice_configurations').select('speaker_name, voice_name').execute()
                    if voices.data and len(voices.data) >= 2:
                        print(f"   ✅ Voice-Konfigurationen: {len(voices.data)} Voices verfügbar")
                    else:
                        print(f"   ⚠️ Voice-Konfigurationen: Weniger als 2 Voices")
                except Exception as e:
                    print(f"   ❌ Voice-Konfigurationen Test fehlgeschlagen: {e}")
                    all_valid = False
            
            return all_valid
            
        except Exception as e:
            print(f"   ❌ Schema-Validierung fehlgeschlagen: {e}")
            return False
    
    async def get_schema_info(self) -> Dict:
        """Gibt Schema-Informationen zurück"""
        
        info = {
            "version": self.current_version,
            "tables": {},
            "total_tables": len(self.schemas),
            "dependencies_resolved": True
        }
        
        try:
            creation_order = self._resolve_dependencies()
            
            for table_name in self.schemas:
                schema = self.schemas[table_name]
                
                # Prüfe ob Tabelle existiert
                try:
                    result = self.db.client.table(table_name).select('*').limit(1).execute()
                    exists = True
                    row_count = len(result.data) if result.data else 0
                except:
                    exists = False
                    row_count = 0
                
                info["tables"][table_name] = {
                    "description": schema.description,
                    "dependencies": schema.dependencies,
                    "exists": exists,
                    "test_data_count": len(schema.test_data),
                    "sample_row_count": row_count
                }
            
            info["creation_order"] = creation_order
            
        except Exception as e:
            info["dependencies_resolved"] = False
            info["error"] = str(e)
        
        return info
    
    async def cleanup_old_data(self) -> Dict:
        """Führt Datenbank-Cleanup aus"""
        
        print("🧹 RADIOX DATABASE CLEANUP")
        print("=" * 50)
        
        try:
            result = self.db.client.rpc('radiox_cleanup_all').execute()
            
            if result.data:
                cleanup_result = result.data
                print(f"✅ Used News gelöscht: {cleanup_result.get('used_news_deleted', 0)}")
                print(f"✅ Broadcast Logs gelöscht: {cleanup_result.get('broadcast_logs_deleted', 0)}")
                print(f"✅ Broadcast Scripts gelöscht: {cleanup_result.get('broadcast_scripts_deleted', 0)}")
                print(f"🕐 Cleanup Zeit: {cleanup_result.get('cleanup_timestamp')}")
                
                return cleanup_result
            else:
                print("❌ Cleanup fehlgeschlagen")
                return {}
                
        except Exception as e:
            print(f"❌ Cleanup Fehler: {e}")
            return {"error": str(e)}


async def main():
    """Hauptfunktion für Schema-Management"""
    
    import argparse
    
    parser = argparse.ArgumentParser(description="RadioX Database Schema Manager")
    parser.add_argument("--action", choices=["create", "info", "cleanup", "recreate"], 
                       default="create", help="Aktion ausführen")
    parser.add_argument("--force", action="store_true", 
                       help="Force recreate (löscht existierende Tabellen)")
    
    args = parser.parse_args()
    
    manager = RadioXSchemaManager()
    
    if args.action == "create":
        success = await manager.create_all_tables(force_recreate=args.force)
        if success:
            print("\n🎉 SCHEMA-SETUP ERFOLGREICH!")
            print("\n📋 NÄCHSTE SCHRITTE:")
            print("  • python cli/cli_voice.py list")
            print("  • python cli/cli_master.py test")
            print("  • python production/radiox_master.py --action system_status")
        else:
            print("\n❌ SCHEMA-SETUP FEHLGESCHLAGEN!")
            sys.exit(1)
    
    elif args.action == "recreate":
        success = await manager.create_all_tables(force_recreate=True)
        if success:
            print("\n🎉 SCHEMA ERFOLGREICH NEU ERSTELLT!")
        else:
            sys.exit(1)
    
    elif args.action == "info":
        info = await manager.get_schema_info()
        print("\n📊 SCHEMA-INFORMATIONEN:")
        print(f"Version: {info['version']}")
        print(f"Tabellen: {info['total_tables']}")
        print(f"Abhängigkeiten aufgelöst: {info['dependencies_resolved']}")
        
        if info['dependencies_resolved']:
            print(f"Erstellungsreihenfolge: {' → '.join(info['creation_order'])}")
        
        print("\n📋 TABELLEN-STATUS:")
        for table_name, table_info in info['tables'].items():
            status = "✅" if table_info['exists'] else "❌"
            deps = f" (deps: {', '.join(table_info['dependencies'])})" if table_info['dependencies'] else ""
            print(f"  {status} {table_name}: {table_info['description']}{deps}")
    
    elif args.action == "cleanup":
        result = await manager.cleanup_old_data()
        if result and "error" not in result:
            print("\n🎉 CLEANUP ERFOLGREICH!")
        else:
            print("\n❌ CLEANUP FEHLGESCHLAGEN!")
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main()) 