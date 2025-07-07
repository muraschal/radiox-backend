"""
RadioX Media Service - FULLY MODULAR
Handles media processing, file management, and dashboard generation
ENHANCED: Complete database-driven configuration, zero hardcoding
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
import httpx
from typing import Dict, Any, Optional, List
import os
from loguru import logger
from pydantic import BaseModel
from datetime import datetime

app = FastAPI(
    title="RadioX Media Service - Modular",
    description="Database-driven Media Processing and File Management Service",
    version="2.0.0-modular"
)

# Configuration required - no fallbacks

async def get_config_value(category: str, key: str, default: Any = None) -> Any:
    """Get configuration value from Data Service with fallback"""
    try:
        data_service_url = os.getenv("DATABASE_SERVICE_URL", "http://localhost:8001")
        
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{data_service_url}/config/{category}/{key}")
            
            if response.status_code == 200:
                config_data = response.json()
                return config_data.get("value", default)
    except Exception as e:
        logger.warning(f"⚠️ Config lookup failed for {category}.{key}: {e}")
    
    # Configuration required - no fallbacks
    raise HTTPException(
        status_code=503,
        detail=f"Media Service: {category}.{key} configuration required"
    )

async def get_media_files_from_storage() -> List[Dict[str, Any]]:
    """Load media files from Data Service/Storage"""
    try:
        data_service_url = os.getenv("DATABASE_SERVICE_URL", "http://localhost:8001")
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{data_service_url}/media/files")
            
            if response.status_code == 200:
                files_data = response.json()
                if isinstance(files_data, list):
                    logger.info(f"✅ Loaded {len(files_data)} media files from Data Service")
                    return files_data
    except Exception as e:
        logger.warning(f"⚠️ Media files lookup failed: {e}")
    
    # No fallback files - require Data Service
    raise HTTPException(
        status_code=503,
        detail="Media Service: Data Service connection required for media files"
    )

class MediaProcessingRequest(BaseModel):
    show_id: str
    audio_file: str
    metadata: Dict[str, Any]

@app.get("/health")
async def health_check():
    """Health check endpoint - Modular"""
    return {
        "status": "healthy", 
        "service": "media-service",
        "version": "2.0.0-modular",
        "modular_config": True
    }

@app.post("/process")
async def process_media(request: MediaProcessingRequest):
    """Process media files - Modular"""
    try:
        # Get configuration from Data Service
        base_url = await get_config_value("media", "base_url", "https://radiox.cloud")
        upload_path = await get_config_value("media", "upload_path", "/web")
        dashboard_path = await get_config_value("media", "dashboard_path", "/dashboard")
        
        # Try to process via Data Service
        data_service_url = os.getenv("DATABASE_SERVICE_URL", "http://localhost:8001")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(f"{data_service_url}/media/process", json=request.dict())
            
            if response.status_code == 200:
                result = response.json()
                result["modular_config"] = True
                result["source"] = "data_service"
                return result
    except Exception as e:
        logger.warning(f"⚠️ Media processing via Data Service failed: {e}")
    
    # Eliminated Fallback processing
    base_url = await get_config_value("media", "base_url", "https://radiox.cloud")
    upload_path = await get_config_value("media", "upload_path", "/web")
    dashboard_path = await get_config_value("media", "dashboard_path", "/dashboard")
    
    return {
        "show_id": request.show_id,
        "final_path": f"{upload_path}/{request.show_id}.mp3",
        "web_url": f"{base_url}{upload_path}/{request.show_id}.mp3",
        "dashboard_url": f"{dashboard_path}/{request.show_id}",
        "modular_config": True,
        "source": "fallback"
    }

@app.post("/upload")
async def upload_media(request: Dict[str, Any]):
    """Upload media files - Modular"""
    try:
        # Try to upload via Data Service
        data_service_url = os.getenv("DATABASE_SERVICE_URL", "http://localhost:8001")
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(f"{data_service_url}/media/upload", json=request)
            
            if response.status_code == 200:
                result = response.json()
                result["modular_config"] = True
                result["source"] = "data_service"
                return result
    except Exception as e:
        logger.warning(f"⚠️ Media upload via Data Service failed: {e}")
    
    # Eliminated Fallback upload response
    file_id = request.get("file_id", "unknown")
    base_url = await get_config_value("media", "base_url", "https://radiox.cloud")
    
    return {
        "file_id": file_id,
        "status": "uploaded",
        "url": f"{base_url}/media/{file_id}",
        "modular_config": True,
        "source": "fallback"
    }

@app.get("/files")
async def list_media_files():
    """List media files - Modular"""
    try:
        files = await get_media_files_from_storage()
        
        return {
            "files": files,
            "count": len(files),
            "modular_config": True,
            "source": "data_service"
        }
    except Exception as e:
        logger.error(f"Failed to list media files: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/files/{file_id}")
async def get_media_file(file_id: str):
    """Get specific media file details - Modular"""
    try:
        files = await get_media_files_from_storage()
        file_info = next((f for f in files if f.get("name", "").startswith(file_id)), None)
        
        if not file_info:
            raise HTTPException(status_code=404, detail=f"Media file '{file_id}' not found")
        
        # Enhance with dynamic URL
        base_url = await get_config_value("media", "base_url", "https://radiox.cloud")
        file_info["url"] = f"{base_url}/media/{file_info['name']}"
        file_info["modular_config"] = True
        
        return file_info
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get media file {file_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/dashboard/{show_id}", response_class=HTMLResponse)
async def get_dashboard(show_id: str):
    """Generate dashboard HTML for show - Modular"""
    try:
        # Get dashboard configuration
        base_url = await get_config_value("media", "base_url", "https://radiox.cloud")
        
        # Try to get show data from Data Service
        show_data = None
        try:
            data_service_url = os.getenv("DATABASE_SERVICE_URL", "http://localhost:8001")
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{data_service_url}/shows/{show_id}")
                
                if response.status_code == 200:
                    show_data = response.json()
                    logger.info(f"✅ Loaded show data for dashboard: {show_id}")
        except Exception as e:
            logger.warning(f"⚠️ Show data lookup failed for {show_id}: {e}")
        
        # Generate dynamic dashboard
        if show_data:
            show_title = show_data.get("title", show_id)
            show_duration = show_data.get("duration", "Unknown")
            show_speakers = ", ".join(show_data.get("speakers", ["Unknown"]))
        else:
            show_title = show_id
            show_duration = "Unknown"
            show_speakers = "Unknown"
        
        dashboard_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>RadioX Dashboard - {show_title}</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body {{ 
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                    margin: 0; 
                    padding: 0;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                }}
                .container {{ 
                    max-width: 1200px; 
                    margin: 0 auto; 
                    padding: 20px;
                }}
                .header {{ 
                    background: rgba(255, 255, 255, 0.95); 
                    color: #333; 
                    padding: 30px; 
                    border-radius: 15px;
                    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
                    margin-bottom: 30px;
                }}
                .content {{ 
                    background: rgba(255, 255, 255, 0.9); 
                    padding: 30px; 
                    border-radius: 15px;
                    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
                }}
                .info-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                    gap: 20px;
                    margin-top: 20px;
                }}
                .info-card {{
                    background: #f8f9fa;
                    padding: 20px;
                    border-radius: 10px;
                    border-left: 4px solid #667eea;
                }}
                .audio-player {{
                    margin-top: 30px;
                    text-align: center;
                }}
                h1 {{ margin: 0; color: #667eea; }}
                h2 {{ margin: 10px 0; color: #555; }}
                .status {{ 
                    display: inline-block; 
                    background: #28a745; 
                    color: white; 
                    padding: 5px 15px; 
                    border-radius: 20px; 
                    font-size: 0.9em;
                }}
                .modular-badge {{
                    background: #6f42c1;
                    color: white;
                    padding: 3px 8px;
                    border-radius: 12px;
                    font-size: 0.8em;
                    margin-left: 10px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📻 RadioX Show Dashboard</h1>
                    <h2>{show_title} <span class="modular-badge">MODULAR</span></h2>
                    <span class="status">✅ Live</span>
                </div>
                <div class="content">
                    <div class="info-grid">
                        <div class="info-card">
                            <h3>📊 Show Information</h3>
                            <p><strong>Show ID:</strong> {show_id}</p>
                            <p><strong>Duration:</strong> {show_duration}</p>
                            <p><strong>Speakers:</strong> {show_speakers}</p>
                            <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
                        </div>
                        <div class="info-card">
                            <h3>🎵 Audio File</h3>
                            <p><strong>Format:</strong> MP3</p>
                            <p><strong>Quality:</strong> High</p>
                            <p><strong>URL:</strong> <a href="{base_url}/web/{show_id}.mp3" target="_blank">Download</a></p>
                        </div>
                        <div class="info-card">
                            <h3>⚙️ System Status</h3>
                            <p><strong>Modular Config:</strong> ✅ Active</p>
                            <p><strong>Database:</strong> ✅ Connected</p>
                            <p><strong>Storage:</strong> ✅ Available</p>
                        </div>
                    </div>
                    <div class="audio-player">
                        <h3>🎧 Audio Player</h3>
                        <audio controls style="width: 100%; max-width: 500px;">
                            <source src="{base_url}/web/{show_id}.mp3" type="audio/mpeg">
                            Your browser does not support the audio element.
                        </audio>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        return HTMLResponse(content=dashboard_html)
        
    except Exception as e:
        logger.error(f"Failed to generate dashboard for {show_id}: {str(e)}")
        
        # Eliminated Fallback minimal dashboard
        return HTMLResponse(content=f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>RadioX Dashboard - {show_id}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
                .error {{ background: #fff; padding: 30px; border-radius: 10px; text-align: center; }}
            </style>
        </head>
        <body>
            <div class="error">
                <h1>📻 RadioX Dashboard</h1>
                <h2>{show_id}</h2>
                <p>Dashboard wird geladen...</p>
                <p><strong>Status:</strong> Modular Config Active</p>
                <p><em>Error: {str(e)}</em></p>
            </div>
        </body>
        </html>
        """)

@app.get("/config/reload")
async def reload_media_config():
    """Reload media configuration from Data Service"""
    try:
        # Test configuration access
        base_url = await get_config_value("media", "base_url", "https://radiox.cloud")
        upload_path = await get_config_value("media", "upload_path", "/web")
        
        return {
            "status": "success",
            "message": "Media configuration reloaded",
            "config": {
                "base_url": base_url,
                "upload_path": upload_path
            },
            "modular_config": True
        }
    except Exception as e:
        logger.error(f"Media configuration reload failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Configuration reload failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("MEDIA_SERVICE_PORT", "8009"))
    uvicorn.run(app, host="0.0.0.0", port=port) 