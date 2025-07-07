#!/usr/bin/env python3
"""
RadioX Database Schema Manager
==============================

UPDATED: Normalized Database Schema (Post-Migration)
Only manages existing tables - no legacy broadcast_logs references.

Current Tables:
- configuration       - System configuration & API keys
- elevenlabs_models   - Available AI voice models  
- rss_feed_preferences - RSS feed configuration
- show_presets       - Show generation templates
- shows              - Normalized show data (single source of truth)
- voice_configurations - Speaker voice settings
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
    dependencies: Optional[List[str]] = None
    version: str = "2.0.0"
    description: str = ""
    test_data: Optional[List[Dict]] = None

    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
        if self.test_data is None:
            self.test_data = []


class RadioXSchemaManager:
    """Normalized Schema Manager für RadioX Database (Post-Migration)"""
    
    def __init__(self):
        self.db = get_db()
        self.current_version = "2.0.0"  # Post-normalization version
        
        # ACTUAL EXISTING TABLES ONLY
        self.schemas = {
            # Core configuration
            "configuration": TableSchema(
                name="configuration",
                dependencies=[],
                description="System configuration and API keys",
                sql="-- Table exists and is managed"
            ),
            
            # Voice system
            "voice_configurations": TableSchema(
                name="voice_configurations", 
                dependencies=[],
                description="Speaker voice configurations for ElevenLabs",
                sql="-- Table exists and is managed"
            ),
            
            "elevenlabs_models": TableSchema(
                name="elevenlabs_models",
                dependencies=[],
                description="Available ElevenLabs AI voice models",
                sql="-- Table exists and is managed"
            ),
            
            # Show system
            "show_presets": TableSchema(
                name="show_presets",
                dependencies=["voice_configurations"],
                description="Show generation templates and presets",
                sql="-- Table exists and is managed"
            ),
            
            "shows": TableSchema(
                name="shows",
                dependencies=["show_presets"],
                description="Normalized show data (Single Source of Truth)",
                sql="-- Table exists with normalized schema"
            ),
            
            # RSS feeds
            "rss_feed_preferences": TableSchema(
                name="rss_feed_preferences",
                dependencies=[],
                description="RSS feed configuration and preferences",
                sql="-- Table exists and is managed"
            )
        }
    
    async def validate_existing_schema(self) -> bool:
        """Validate that all expected tables exist"""
        
        print("🔍 RADIOX NORMALIZED SCHEMA VALIDATION")
        print("=" * 60)
        print(f"📊 Version: {self.current_version}")
        print(f"📋 Expected Tables: {len(self.schemas)}")
        
        try:
            all_valid = True
            
            for table_name, schema in self.schemas.items():
                # Test table access
                try:
                    result = self.db.client.table(table_name).select('*').limit(1).execute()
                    print(f"   ✅ {table_name}: Accessible")
                except Exception as e:
                    print(f"   ❌ {table_name}: Access failed - {e}")
                    all_valid = False
            
            if all_valid:
                print(f"\n✅ All {len(self.schemas)} tables are accessible")
                
                # Test voice configurations specifically
                try:
                    voices = self.db.client.table('voice_configurations').select('speaker_name, voice_name').execute()
                    if voices.data and len(voices.data) >= 2:
                        print(f"   ✅ Voice configurations: {len(voices.data)} speakers available")
                    else:
                        print(f"   ⚠️ Voice configurations: Only {len(voices.data) if voices.data else 0} speakers")
                except Exception as e:
                    print(f"   ❌ Voice configurations test failed: {e}")
                    all_valid = False
                
                # Test shows table (normalized)
                try:
                    shows = self.db.client.table('shows').select('session_id').limit(5).execute()
                    show_count = len(shows.data) if shows.data else 0
                    print(f"   ✅ Shows table: {show_count} shows in database")
                except Exception as e:
                    print(f"   ❌ Shows table test failed: {e}")
                    all_valid = False
            
            return all_valid
            
        except Exception as e:
            print(f"\n❌ Schema validation failed: {e}")
            return False
    
    def _resolve_dependencies(self) -> List[str]:
        """Resolve table dependencies"""
        
        resolved = []
        remaining = list(self.schemas.keys())
        
        while remaining:
            ready = []
            for table in remaining:
                dependencies = self.schemas[table].dependencies or []
                if all(dep in resolved for dep in dependencies):
                    ready.append(table)
            
            if not ready:
                raise ValueError(f"Circular dependency or missing table: {remaining}")
            
            for table in ready:
                resolved.append(table)
                remaining.remove(table)
        
        return resolved
    
    async def get_schema_info(self) -> Dict:
        """Get current schema information"""
        
        info = {
            "version": self.current_version,
            "type": "normalized_post_migration",
            "tables": {},
            "total_tables": len(self.schemas),
            "dependencies_resolved": True
        }
        
        try:
            creation_order = self._resolve_dependencies()
            
            for table_name in self.schemas:
                schema = self.schemas[table_name]
                
                # Check if table exists
                try:
                    result = self.db.client.table(table_name).select('*').limit(1).execute()
                    exists = True
                    sample_count = len(result.data) if result.data else 0
                except:
                    exists = False
                    sample_count = 0
                
                info["tables"][table_name] = {
                    "description": schema.description,
                    "dependencies": schema.dependencies,
                    "exists": exists,
                    "sample_rows": sample_count
                }
            
            info["creation_order"] = creation_order
            
        except Exception as e:
            info["dependencies_resolved"] = False
            info["error"] = str(e)
        
        return info
    
    async def cleanup_old_data(self) -> Dict:
        """Clean up old data (shows older than 30 days)"""
        
        print("🧹 RADIOX NORMALIZED DATABASE CLEANUP")
        print("=" * 50)
        
        try:
            # Only cleanup shows table - it's the only one with time-based data
            from datetime import datetime, timedelta
            cutoff_date = (datetime.now() - timedelta(days=30)).isoformat()
            
            # Count shows that would be deleted
            old_shows = self.db.client.table('shows').select('session_id').lt('created_at', cutoff_date).execute()
            old_count = len(old_shows.data) if old_shows.data else 0
            
            if old_count > 0:
                # Delete old shows
                result = self.db.client.table('shows').delete().lt('created_at', cutoff_date).execute()
                deleted_count = len(result.data) if result.data else old_count
                
                print(f"✅ Old shows deleted: {deleted_count}")
                
                return {
                    "shows_deleted": deleted_count,
                    "cleanup_timestamp": datetime.now().isoformat()
                }
            else:
                print("✅ No old shows to delete")
                return {
                    "shows_deleted": 0,
                    "cleanup_timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            print(f"❌ Cleanup error: {e}")
            return {"error": str(e)}


async def main():
    """Main function for schema management"""
    
    import argparse
    
    parser = argparse.ArgumentParser(description="RadioX Normalized Schema Manager")
    parser.add_argument("--action", choices=["validate", "info", "cleanup"], 
                       default="validate", help="Action to perform")
    
    args = parser.parse_args()
    
    manager = RadioXSchemaManager()
    
    if args.action == "validate":
        success = await manager.validate_existing_schema()
        if success:
            print("\n🎉 SCHEMA VALIDATION SUCCESSFUL!")
        else:
            print("\n❌ SCHEMA VALIDATION FAILED!")
            sys.exit(1)
    
    elif args.action == "info":
        info = await manager.get_schema_info()
        print("\n📊 NORMALIZED SCHEMA INFORMATION:")
        print(f"Version: {info['version']} ({info['type']})")
        print(f"Tables: {info['total_tables']}")
        print(f"Dependencies resolved: {info['dependencies_resolved']}")
        
        if info['dependencies_resolved']:
            print(f"Table order: {' → '.join(info['creation_order'])}")
        
        print("\n📋 TABLE STATUS:")
        for table_name, table_info in info['tables'].items():
            status = "✅" if table_info['exists'] else "❌"
            deps = f" (deps: {', '.join(table_info['dependencies'])})" if table_info['dependencies'] else ""
            print(f"  {status} {table_name}: {table_info['description']}{deps}")
    
    elif args.action == "cleanup":
        result = await manager.cleanup_old_data()
        if result and "error" not in result:
            print("\n🎉 CLEANUP SUCCESSFUL!")
        else:
            print("\n❌ CLEANUP FAILED!")
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main()) 