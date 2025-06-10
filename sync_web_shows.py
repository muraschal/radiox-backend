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
    
    # Patterns für neue und alte Dateien
    pattern_new = re.compile(r'radiox_dashboard_fancy_(\d{6}_\d{4})\.html')
    pattern_media = re.compile(r'radiox_(\d{6}_\d{4})\.(mp3|png)')
    
    # Sammle neue Dashboard-Dateien
    for file_path in directory.glob("radiox_dashboard_fancy_*.html"):
        match = pattern_new.match(file_path.name)
        if match:
            timestamp = match.group(1)
            
            if timestamp not in show_files:
                show_files[timestamp] = {
                    "timestamp": timestamp,
                    "files": {}
                }
            
            show_files[timestamp]["files"]["html"] = {
                "path": file_path,
                "size": file_path.stat().st_size if file_path.exists() else 0
            }
    
    # Sammle Media-Dateien (MP3, PNG)
    for file_path in directory.glob("radiox_*.mp3"):
        match = pattern_media.match(file_path.name)
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
    
    for file_path in directory.glob("radiox_*.png"):
        match = pattern_media.match(file_path.name)
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
    
    # Erstelle vollständige Shows (nur Dashboard ist Pflicht)
    complete_shows = []
    for timestamp, show_data in show_files.items():
        files = show_data["files"]
        if "html" in files:  # Dashboard ist Pflicht
            complete_shows.append({
                "timestamp": timestamp,
                "htmlFile": f"radiox_dashboard_fancy_{timestamp}.html",
                "mp3File": f"radiox_{timestamp}.mp3" if "mp3" in files else None,
                "pngFile": f"radiox_{timestamp}.png" if "png" in files else None,
                "size": files["html"]["size"],
                "audioSize": files["mp3"]["size"] if "mp3" in files else 0,
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
            
            # Bestimme Ziel-Namen
            if ext == "html":
                target_name = f"radiox_dashboard_fancy_{show['timestamp']}.html"
            else:
                target_name = f"radiox_{show['timestamp']}.{ext}"
            
            target_path = WEB_DIR / target_name
            
            try:
                shutil.copy2(source_path, target_path)
                copied_files[ext] = {
                    "path": target_path,
                    "size": target_path.stat().st_size
                }
                print(f"  ✅ {source_path.name} → {target_name}")
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
            for file_path in WEB_DIR.glob(f"radiox*{show['timestamp']}.*"):
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
    
    # Also update index.html if it exists and needs updating
    update_index_page(shows_data)
    
    return shows_data

def update_index_page(shows_data: Dict[str, Any]):
    """Aktualisiere index.html mit neuesten Show-Daten."""
    
    index_path = WEB_DIR / "index.html"
    
    # Prüfe ob index.html existiert
    if not index_path.exists():
        print("ℹ️ index.html nicht gefunden - wird bei Bedarf automatisch generiert")
        return
    
    try:
        # Lese aktuelle index.html
        with open(index_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Update hardcoded Shows mit aktuellen Shows
        if shows_data.get("shows"):
            current_shows = []
            for show in shows_data["shows"][:5]:  # Top 5 Shows
                html_file = show.get("htmlFile")
                if html_file:
                    current_shows.append(f"'{html_file}'")
            
            if current_shows:
                import re
                shows_array = ',\n            '.join(current_shows)
                new_shows_const = f"""const CURRENT_SHOWS = [
            {shows_array}
        ];"""
                
                # Replace CURRENT_SHOWS array
                content = re.sub(
                    r'const CURRENT_SHOWS = \[[^\]]*\];',
                    new_shows_const,
                    content,
                    flags=re.MULTILINE | re.DOTALL
                )
        
        # Schreibe aktualisierte index.html zurück
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"📄 index.html aktualisiert mit {len(shows_data.get('shows', []))} Shows")
        
    except Exception as e:
        print(f"⚠️ Fehler beim Aktualisieren der index.html: {e}")
        # Don't fail if index update fails

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
    
    # Sammle Shows direkt aus web (Dashboard werden bereits dort generiert)
    if not WEB_DIR.exists():
        print(f"❌ Web Verzeichnis nicht gefunden: {WEB_DIR}")
        return
    
    print("📂 Sammle Shows aus web/...")
    all_shows = get_show_files(WEB_DIR)
    
    if not all_shows:
        print("❌ Keine Shows gefunden!")
        return
    
    print(f"📊 {len(all_shows)} Shows gefunden")
    
    # Bereinige alte Shows (behalte nur die neuesten MAX_SHOWS)
    print(f"🧹 Bereinige alte Shows (behalte {MAX_SHOWS} neueste)...")
    cleanup_old_shows(all_shows)
    
    # Aktualisiere Shows-Liste nach Bereinigung
    cleaned_shows = get_show_files(WEB_DIR)
    
    # Generiere shows.json
    print("📄 Generiere shows.json...")
    shows_data = generate_shows_json(cleaned_shows)
    
    # Zeige Zusammenfassung
    print_summary(shows_data)

def cleanup_old_shows(shows: List[Dict[str, Any]]):
    """Bereinige alte Shows im web Verzeichnis (behalte nur die neuesten MAX_SHOWS)."""
    
    if len(shows) <= MAX_SHOWS:
        print(f"ℹ️ Nur {len(shows)} Shows vorhanden, keine Bereinigung nötig")
        return
    
    # Sortiere nach Timestamp (neueste zuerst)
    shows.sort(key=lambda x: x["timestamp"], reverse=True)
    
    # Lösche alte Shows
    shows_to_delete = shows[MAX_SHOWS:]
    
    for show in shows_to_delete:
        timestamp = show["timestamp"]
        for file_path in WEB_DIR.glob(f"*{timestamp}*"):
            if file_path.is_file():
                file_path.unlink()
                print(f"🗑️ Gelöscht: {file_path.name}")
    
    print(f"✅ {len(shows_to_delete)} alte Shows bereinigt")

if __name__ == "__main__":
    main() 