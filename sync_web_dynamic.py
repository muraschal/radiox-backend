#!/usr/bin/env python3
"""
Dynamic Web Sync - Automatisches Web-Update System
=================================================

Scannt automatisch das web/ Verzeichnis nach Shows und:
- Generiert dynamisch shows.json
- Aktualisiert index.html mit neuesten Shows
- Sortiert nach Timestamp (neueste zuerst)
- Unterscheidet zwischen Jinja2 und Legacy Shows
"""

import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any


def scan_web_directory() -> List[Dict[str, Any]]:
    """Scannt web/ Verzeichnis nach allen Show-Files"""
    web_dir = Path("web")
    shows = []
    
    # Finde alle HTML-Files
    html_files = list(web_dir.glob("radiox_*.html"))
    
    for html_file in html_files:
        # Extrahiere Timestamp aus Filename
        match = re.search(r'radiox_(\d{6}_\d{4})\.html', html_file.name)
        if not match:
            continue
            
        timestamp = match.group(1)
        base_name = f"radiox_{timestamp}"
        
        # Finde zugehörige Files
        mp3_file = web_dir / f"{base_name}.mp3"
        png_file = web_dir / f"{base_name}.png"
        
        # Bestimme Show-Typ
        show_type = "Unknown"
        system = "Unknown"
        
        if "dashboard_fancy" in html_file.name:
            system = "Legacy Dashboard"
            show_type = "Legacy Show"
        else:
            system = "Jinja2"
            # Versuche Show-Typ aus HTML zu extrahieren
            try:
                with open(html_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if "Global News Hot" in content:
                        show_type = "Global News Hot"
                    elif "Zurich Local News" in content:
                        show_type = "Zurich Local News"
                    elif "Public Transport" in content:
                        show_type = "Public Transport News"
                    else:
                        show_type = "Radio Show"
            except:
                show_type = "Radio Show"
        
        # Sammle File-Informationen
        show_info = {
            "timestamp": timestamp,
            "htmlFile": html_file.name,
            "mp3File": f"{base_name}.mp3" if mp3_file.exists() else None,
            "pngFile": f"{base_name}.png" if png_file.exists() else None,
            "size": html_file.stat().st_size,
            "audioSize": mp3_file.stat().st_size if mp3_file.exists() else 0,
            "coverSize": png_file.stat().st_size if png_file.exists() else 0,
            "type": show_type,
            "system": system,
            "created": datetime.fromtimestamp(html_file.stat().st_mtime).isoformat()
        }
        
        shows.append(show_info)
    
    # Sortiere nach Timestamp (neueste zuerst)
    shows.sort(key=lambda x: x["timestamp"], reverse=True)
    
    return shows


def generate_shows_json(shows: List[Dict[str, Any]]) -> None:
    """Generiert shows.json dynamisch"""
    shows_data = {
        "lastUpdated": datetime.now().isoformat(),
        "totalShows": len(shows),
        "shows": shows
    }
    
    with open("web/shows.json", "w", encoding="utf-8") as f:
        json.dump(shows_data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ shows.json generiert mit {len(shows)} Shows")


def update_index_html(shows: List[Dict[str, Any]]) -> None:
    """Aktualisiert index.html mit dynamischer Show-Liste"""
    
    # Erstelle CURRENT_SHOWS Array aus den neuesten 5 Shows
    current_shows = [show["htmlFile"] for show in shows[:5]]
    
    index_template = f'''<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RadioX AI • Weiterleitung...</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #0f0f0f 0%, #1a1a1a 50%, #0f0f0f 100%);
            color: #ffffff;
            margin: 0;
            padding: 0;
            height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            text-align: center;
        }}

        .container {{
            max-width: 500px;
            padding: 2rem;
        }}

        .title {{
            font-size: 3.5rem;
            font-weight: 900;
            margin-bottom: 0.3rem;
            letter-spacing: -0.05em;
            background: linear-gradient(135deg, #ffffff 0%, #c0c0c0 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            text-shadow: 0 0 30px rgba(255,255,255,0.3);
            position: relative;
            z-index: 2;
        }}

        .title .red-x {{
            color: #ff4444 !important;
            -webkit-text-fill-color: #ff4444 !important;
            background: none !important;
            background-clip: initial !important;
        }}
        
        .title .ai-sup {{
            font-size: 0.4em;
            color: #ffffff !important;
            -webkit-text-fill-color: #ffffff !important;
            background: none !important;
            background-clip: initial !important;
        }}
        
        .title {{
            transition: all 0.3s ease;
            cursor: pointer;
        }}
        
        .title:hover {{
            transform: scale(1.05);
            text-shadow: 0 0 40px rgba(255,255,255,0.5);
        }}

        .loading {{
            font-size: 1.2rem;
            color: #aaa;
            margin-bottom: 2rem;
        }}

        .spinner {{
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid rgba(102, 126, 234, 0.3);
            border-radius: 50%;
            border-top-color: #667eea;
            animation: spin 1s ease-in-out infinite;
            margin-left: 10px;
        }}

        @keyframes spin {{
            to {{ transform: rotate(360deg); }}
        }}

        .error {{
            color: #ff6b6b;
            font-size: 1rem;
            margin-bottom: 1rem;
        }}

        .manual-link {{
            color: #667eea;
            text-decoration: none;
            border-bottom: 1px solid #667eea;
            margin: 0.5rem;
            padding: 0.5rem 1rem;
            display: inline-block;
            border-radius: 4px;
            transition: all 0.2s ease;
        }}

        .manual-link:hover {{
            background: rgba(102, 126, 234, 0.1);
            color: #ffffff;
            border-bottom-color: #ffffff;
        }}

        .fallback-section {{
            margin-top: 2rem;
        }}

        .fallback-title {{
            font-size: 1.1rem;
            color: #888;
            margin-bottom: 1rem;
        }}
    </style>
</head>
<body>
    <div class="container">
        <a href="https://github.com/muraschal/radiox-backend" target="_blank" rel="noopener noreferrer" style="text-decoration: none;">
            <h1 class="title">RADIO<span class="red-x">X</span><sup class="ai-sup">AI</sup></h1>
        </a>
        <div class="loading" id="status">
            Suche neueste Show...
            <span class="spinner"></span>
        </div>
        <div id="error" class="error" style="display: none;"></div>
        <div id="fallback" class="fallback-section" style="display: none;">
            <div class="fallback-title">Verfügbare Shows:</div>
            <div id="show-links"></div>
        </div>
    </div>

    <script>
        // DYNAMISCH GENERIERT - Aktualisiert: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        const CURRENT_SHOWS = {json.dumps(current_shows, indent=12)};

        async function redirectToLatestShow() {{
            let latestShow = null;
            
            try {{
                // Versuche zuerst shows.json zu laden
                const response = await fetch('shows.json');
                
                if (response.ok) {{
                    const data = await response.json();
                    
                    if (data.shows && data.shows.length > 0) {{
                        latestShow = data.shows[0].htmlFile;
                        const showType = data.shows[0].type || 'Show';
                        document.getElementById('status').innerHTML = `Weiterleitung zu ${{showType}}... <span class="spinner"></span>`;
                    }}
                }}
            }} catch (error) {{
                console.log('shows.json Fehler:', error.message);
            }}
            
            // Fallback: Versuche hardcoded Shows
            if (!latestShow) {{
                document.getElementById('status').textContent = 'Suche verfügbare Shows...';
                
                for (const showFile of CURRENT_SHOWS) {{
                    try {{
                        const response = await fetch(showFile, {{ method: 'HEAD' }});
                        if (response.ok) {{
                            latestShow = showFile;
                            const timestamp = showFile.match(/(\\d{{6}}_\\d{{4}})/)?.[1] || 'neueste';
                            document.getElementById('status').innerHTML = `Weiterleitung zu ${{timestamp}}... <span class="spinner"></span>`;
                            break;
                        }}
                    }} catch (e) {{
                        console.log(`${{showFile}} nicht verfügbar:`, e.message);
                    }}
                }}
            }}
            
            // Erfolgreiche Weiterleitung
            if (latestShow) {{
                setTimeout(() => {{
                    window.location.href = latestShow;
                }}, 1000);
                return;
            }}
            
            // Fallback: Zeige alle verfügbaren Shows
            await showAllAvailableShows();
        }}
        
        async function showAllAvailableShows() {{
            document.getElementById('status').style.display = 'none';
            
            const errorEl = document.getElementById('error');
            errorEl.textContent = 'Automatische Weiterleitung fehlgeschlagen.';
            errorEl.style.display = 'block';
            
            const fallbackEl = document.getElementById('fallback');
            const linksEl = document.getElementById('show-links');
            
            // Versuche alle Shows aus CURRENT_SHOWS zu laden
            for (const showFile of CURRENT_SHOWS) {{
                try {{
                    const response = await fetch(showFile, {{ method: 'HEAD' }});
                    if (response.ok) {{
                        const link = document.createElement('a');
                        link.href = showFile;
                        link.className = 'manual-link';
                        
                        const timestamp = showFile.match(/(\\d{{6}}_\\d{{4}})/)?.[1] || showFile;
                        const showType = showFile.includes('dashboard_fancy') ? 'Legacy' : 'Jinja2';
                        link.textContent = `${{timestamp}} (${{showType}})`;
                        
                        linksEl.appendChild(link);
                    }}
                }} catch (e) {{
                    console.log(`${{showFile}} nicht verfügbar:`, e.message);
                }}
            }}
            
            fallbackEl.style.display = 'block';
        }}

        // Starte Weiterleitung
        redirectToLatestShow();
    </script>
</body>
</html>'''
    
    with open("web/index.html", "w", encoding="utf-8") as f:
        f.write(index_template)
    
    print(f"✅ index.html aktualisiert mit {len(current_shows)} Shows")


def main():
    """Hauptfunktion - Scannt und aktualisiert Web-Files"""
    print("🔄 Dynamisches Web-Sync gestartet...")
    
    # Scanne alle Shows
    shows = scan_web_directory()
    print(f"📊 {len(shows)} Shows gefunden")
    
    if shows:
        # Zeige neueste Shows
        print("\n🎯 Neueste Shows:")
        for i, show in enumerate(shows[:3]):
            print(f"   {i+1}. {show['timestamp']} - {show['type']} ({show['system']})")
        
        # Generiere JSON und HTML
        generate_shows_json(shows)
        update_index_html(shows)
        
        print(f"\n✅ Web-Sync abgeschlossen!")
        print(f"🌐 Latest Show: {shows[0]['htmlFile']}")
        print(f"🎭 Type: {shows[0]['type']}")
    else:
        print("❌ Keine Shows gefunden!")


if __name__ == "__main__":
    main() 