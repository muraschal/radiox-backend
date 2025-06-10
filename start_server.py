#!/usr/bin/env python3
"""
Robuster HTTP-Server für RadioX Dashboard Testing
Behandelt BrokenPipe und andere HTTP-Fehler elegant
"""

import http.server
import socketserver
import os
import sys
from pathlib import Path

class QuietHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """HTTP Request Handler der störende Errors unterdrückt"""
    
    def log_message(self, format, *args):
        """Unterdrücke normale HTTP-Logs - zeige nur wichtige Meldungen"""
        # Nur 4xx und 5xx Fehler loggen, nicht die normalen 200/304 requests
        if len(args) >= 2 and isinstance(args[1], str):
            status_code = args[1].split()[0] if args[1].split() else ""
            if status_code.startswith(('4', '5')):
                super().log_message(format, *args)
    
    def end_headers(self):
        """Zusätzliche Headers für bessere Kompatibilität"""
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        super().end_headers()
    
    def handle_one_request(self):
        """Behandle einzelne Requests mit Fehlerbehandlung"""
        try:
            super().handle_one_request()
        except (ConnectionResetError, BrokenPipeError, OSError):
            # Client hat Verbindung abgebrochen - ignorieren
            pass
        except Exception as e:
            # Andere Fehler loggen aber nicht crashen
            print(f"⚠️ HTTP Request Error: {e}")

class RobustTCPServer(socketserver.TCPServer):
    """TCP Server mit robusterer Fehlerbehandlung"""
    
    allow_reuse_address = True
    
    def handle_error(self, request, client_address):
        """Behandle Server-Fehler elegant"""
        exc_type, exc_value, exc_tb = sys.exc_info()
        if isinstance(exc_value, (ConnectionResetError, BrokenPipeError)):
            # Diese Fehler ignorieren - Client hat einfach Verbindung geschlossen
            pass
        else:
            # Andere Fehler kurz loggen
            print(f"⚠️ Server Error von {client_address}: {exc_value}")

def start_server(port=8080, directory="web"):
    """Starte robusten HTTP-Server"""
    
    # Wechsle in das angegebene Verzeichnis
    web_dir = Path(__file__).parent / directory
    if not web_dir.exists():
        print(f"❌ Verzeichnis {web_dir} existiert nicht!")
        return
    
    os.chdir(web_dir)
    
    try:
        with RobustTCPServer(("", port), QuietHTTPRequestHandler) as httpd:
            print(f"🌐 RadioX HTTP-Server gestartet auf Port {port}")
            print(f"📁 Serving: {web_dir.absolute()}")
            print(f"🔗 URL: http://localhost:{port}")
            print("💡 Drücke Ctrl+C zum Beenden")
            print("")
            
            httpd.serve_forever()
            
    except KeyboardInterrupt:
        print("\n🛑 Server gestoppt")
    except OSError as e:
        if e.errno == 48:  # Address already in use
            print(f"❌ Port {port} ist bereits belegt!")
            print("💡 Versuche einen anderen Port oder stoppe den bestehenden Server")
        else:
            print(f"❌ Server-Fehler: {e}")
    except Exception as e:
        print(f"❌ Unerwarteter Fehler: {e}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="RadioX Dashboard HTTP-Server")
    parser.add_argument("--port", "-p", type=int, default=8080, help="Server Port (default: 8080)")
    parser.add_argument("--dir", "-d", default="web", help="Verzeichnis zum Servieren (default: web)")
    
    args = parser.parse_args()
    start_server(args.port, args.dir) 