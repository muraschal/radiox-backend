#!/usr/bin/env python3
"""
🌐 RadioX Web Shows Synchronizer

Synchronisiert die neuesten Shows von outplay/ zu web/ für Vercel Publishing.
- Behält nur die letzten 10 Shows
- Erstellt shows.json für die Website
- Optimiert für GitHub + Vercel

Usage:
    python sync_web_shows.py
"""

import os
import json
import shutil
import re
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# Konfiguration
MAX_SHOWS = 10  # Maximal 10 Shows auf der Website
OUTPLAY_DIR = Path("outplay")
WEB_DIR = Path("web")

def get_show_files(directory: Path) -> List[Dict[str, Any]]:
    """Sammle alle Show-Dateien aus einem Verzeichnis."""
    
    show_files = {}
    pattern = re.compile(r'radiox_(\d{6}_\d{4})\.(html|mp3|png)')
    
    for file_path in directory.glob("radiox_*"):
        match = pattern.match(file_path.name)
        if match:
            timestamp = match.group(1)
            extension = match.group(2)
            
            if timestamp not in show_files:
                show_files[timestamp] = {
                    "timestamp": timestamp,
                    "files": {}
                }
            
            show_files[timestamp]["files"][extension] = {
                "path": file_path,
                "size": file_path.stat().st_size if file_path.exists() else 0
            }
    
    # Filtere nur vollständige Shows (mit HTML + MP3)
    complete_shows = []
    for timestamp, show_data in show_files.items():
        files = show_data["files"]
        if "html" in files and "mp3" in files:
            complete_shows.append({
                "timestamp": timestamp,
                "htmlFile": f"radiox_{timestamp}.html",
                "mp3File": f"radiox_{timestamp}.mp3",
                "pngFile": f"radiox_{timestamp}.png" if "png" in files else None,
                "size": files["html"]["size"],
                "audioSize": files["mp3"]["size"],
                "coverSize": files["png"]["size"] if "png" in files else 0,
                "files": files
            })
    
    # Sortiere nach Timestamp (neueste zuerst)
    complete_shows.sort(key=lambda x: x["timestamp"], reverse=True)
    return complete_shows

def clean_web_directory():
    """Bereinige web Verzeichnis von alten Shows."""
    
    if WEB_DIR.exists():
        for file_path in WEB_DIR.glob("radiox_*"):
            if file_path.is_file():
                file_path.unlink()
                print(f"🗑️ Gelöscht: {file_path.name}")

def copy_show_files(shows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Kopiere Show-Dateien zu web Verzeichnis."""
    
    WEB_DIR.mkdir(exist_ok=True)
    copied_shows = []
    
    for i, show in enumerate(shows[:MAX_SHOWS]):
        print(f"📂 Kopiere Show {i+1}/{min(len(shows), MAX_SHOWS)}: {show['timestamp']}")
        
        success = True
        copied_files = {}
        
        # Kopiere alle Dateien der Show
        for ext, file_info in show["files"].items():
            source_path = file_info["path"]
            target_path = WEB_DIR / source_path.name
            
            try:
                shutil.copy2(source_path, target_path)
                copied_files[ext] = {
                    "path": target_path,
                    "size": target_path.stat().st_size
                }
                print(f"  ✅ {source_path.name} → {target_path.name}")
            except Exception as e:
                print(f"  ❌ Fehler beim Kopieren von {source_path.name}: {e}")
                success = False
                break
        
        if success:
            # Update show info with web paths
            web_show = show.copy()
            web_show["files"] = copied_files
            copied_shows.append(web_show)
        else:
            # Cleanup bei Fehler
            for file_path in WEB_DIR.glob(f"radiox_{show['timestamp']}.*"):
                file_path.unlink()
    
    return copied_shows

def generate_shows_json(shows: List[Dict[str, Any]]):
    """Generiere shows.json für die Website."""
    
    # Bereite Daten für JSON vor (entferne Pfad-Objekte)
    json_shows = []
    for show in shows:
        json_show = {
            "timestamp": show["timestamp"],
            "htmlFile": show["htmlFile"],
            "mp3File": show["mp3File"],
            "pngFile": show["pngFile"],
            "size": show["size"],
            "audioSize": show["audioSize"],
            "coverSize": show["coverSize"]
        }
        json_shows.append(json_show)
    
    shows_data = {
        "lastUpdated": datetime.now().isoformat(),
        "totalShows": len(json_shows),
        "shows": json_shows
    }
    
    shows_json_path = WEB_DIR / "shows.json"
    with open(shows_json_path, 'w', encoding='utf-8') as f:
        json.dump(shows_data, f, indent=2, ensure_ascii=False)
    
    print(f"📄 Erstellt: {shows_json_path}")
    return shows_data

def print_summary(shows_data: Dict[str, Any]):
    """Zeige Zusammenfassung der Synchronisation."""
    
    total_shows = shows_data["totalShows"]
    if total_shows == 0:
        print("\n❌ Keine Shows gefunden!")
        return
    
    latest_show = shows_data["shows"][0]
    
    # Berechne Gesamtgröße
    total_size = sum(show["size"] + show["audioSize"] + show["coverSize"] 
                    for show in shows_data["shows"])
    total_size_mb = total_size / 1024 / 1024
    
    print(f"\n✅ Synchronisation abgeschlossen!")
    print(f"📊 {total_shows} Shows synchronisiert")
    print(f"🎵 Neueste Show: {latest_show['timestamp']}")
    print(f"📦 Gesamtgröße: {total_size_mb:.1f} MB")
    print(f"🌐 Bereit für Vercel Deployment: web/")
    
    if total_size_mb > 100:
        print(f"⚠️ Warnung: Große Repository-Größe ({total_size_mb:.1f} MB)")

def main():
    """Hauptfunktion."""
    
    print("🌐 RadioX Web Shows Synchronizer")
    print("=" * 40)
    
    # Prüfe ob outplay Verzeichnis existiert
    if not OUTPLAY_DIR.exists():
        print(f"❌ Outplay Verzeichnis nicht gefunden: {OUTPLAY_DIR}")
        return
    
    # Sammle Shows aus outplay
    print("📂 Sammle Shows aus outplay/...")
    all_shows = get_show_files(OUTPLAY_DIR)
    
    if not all_shows:
        print("❌ Keine vollständigen Shows gefunden!")
        return
    
    print(f"📊 {len(all_shows)} vollständige Shows gefunden")
    
    # Bereinige web Verzeichnis
    print("🧹 Bereinige web Verzeichnis...")
    clean_web_directory()
    
    # Kopiere neueste Shows
    print(f"📂 Kopiere maximal {MAX_SHOWS} neueste Shows...")
    copied_shows = copy_show_files(all_shows)
    
    if not copied_shows:
        print("❌ Keine Shows erfolgreich kopiert!")
        return
    
    # Generiere shows.json
    print("📄 Generiere shows.json...")
    shows_data = generate_shows_json(copied_shows)
    
    # Zeige Zusammenfassung
    print_summary(shows_data)

if __name__ == "__main__":
    main() 