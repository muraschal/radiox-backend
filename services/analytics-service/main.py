"""
RadioX Analytics Service - FULLY MODULAR
Handles metrics, performance tracking, and analytics data
ENHANCED: Complete database-driven configuration, zero hardcoding
"""

from fastapi import FastAPI, HTTPException
import httpx
from typing import Dict, Any, Optional, List
import os
from datetime import datetime, timedelta
from loguru import logger
from pydantic import BaseModel
import json

app = FastAPI(
    title="RadioX Analytics Service - Modular",
    description="Database-driven Metrics and Performance Tracking Service",
    version="2.0.0-modular"
)

# Eliminated Fallback configuration

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
    
    # Eliminated Fallback to hardcoded config
    return None

async def get_analytics_data_from_database() -> Dict[str, Any]:
    """Load analytics data from Data Service"""
    try:
        data_service_url = os.getenv("DATABASE_SERVICE_URL", "http://localhost:8001")
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{data_service_url}/analytics/shows")
            
            if response.status_code == 200:
                analytics_data = response.json()
                if isinstance(analytics_data, dict):
                    logger.info("✅ Loaded analytics data from Data Service")
                    return analytics_data
    except Exception as e:
        logger.warning(f"⚠️ Analytics data lookup failed: {e}")
    
    return {
        "error": "Analytics data unavailable",
        "status": "data_service_error", 
        "message": "Unable to connect to Data Service for analytics",
        "source": "configuration_error",
        "timestamp": datetime.now().isoformat()
    }

class ShowAnalytics(BaseModel):
    show_id: str
    preset: Optional[str]
    duration: int
    speakers: List[str]
    news_count: int
    generated_at: str

@app.get("/health")
async def health_check():
    """Health check endpoint - Modular"""
    return {
        "status": "healthy", 
        "service": "analytics-service",
        "version": "2.0.0-modular",
        "modular_config": True
    }

@app.post("/shows")
async def store_show_analytics(analytics: ShowAnalytics):
    """Store show analytics data - Modular"""
    try:
        # Try to store in Data Service
        data_service_url = os.getenv("DATABASE_SERVICE_URL", "http://localhost:8001")
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(f"{data_service_url}/analytics/shows", json=analytics.dict())
            
            if response.status_code == 200:
                return {
                    "message": "Analytics stored successfully",
                    "modular_config": True,
                    "storage": "data_service"
                }
    except Exception as e:
        logger.warning(f"⚠️ Failed to store in Data Service: {e}")
    
    # No fallback storage - require Data Service
    raise HTTPException(
        status_code=503,
        detail="Analytics Service: Data Service connection required for analytics storage"
    )

@app.get("/shows")
async def get_show_analytics(days: Optional[int] = None):
    """Get show analytics for the last N days - Modular"""
    try:
        # Get default period if not specified
        if days is None:
            days = await get_config_value("analytics", "default_period_days", 7)
        
        analytics_data = await get_analytics_data_from_database()
        
        # Update period if custom days requested
        if days != 7 and days is not None:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            analytics_data["period"] = {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
                "days": days
            }
        
        analytics_data["modular_config"] = True
        return analytics_data
        
    except Exception as e:
        logger.error(f"Failed to get show analytics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/performance")
async def get_performance_metrics():
    """Get system performance metrics - Modular"""
    try:
        # Try to get real performance data from Data Service
        data_service_url = os.getenv("DATABASE_SERVICE_URL", "http://localhost:8001")
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{data_service_url}/analytics/performance")
            
            if response.status_code == 200:
                performance_data = response.json()
                performance_data["modular_config"] = True
                performance_data["source"] = "data_service"
                return performance_data
    except Exception as e:
        logger.warning(f"⚠️ Performance data lookup failed: {e}")
    
    # No fallback performance data - require Data Service
    raise HTTPException(
        status_code=503,
        detail="Analytics Service: Data Service connection required for performance metrics"
    )

@app.get("/usage")
async def get_usage_statistics():
    """Get usage statistics - Modular"""
    try:
        # Try to get real usage data from Data Service
        data_service_url = os.getenv("DATABASE_SERVICE_URL", "http://localhost:8001")
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{data_service_url}/analytics/usage")
            
            if response.status_code == 200:
                usage_data = response.json()
                usage_data["modular_config"] = True
                usage_data["source"] = "data_service"
                return usage_data
    except Exception as e:
        logger.warning(f"⚠️ Usage data lookup failed: {e}")
    
    # No fallback usage data - require Data Service
    raise HTTPException(
        status_code=503,
        detail="Analytics Service: Data Service connection required for usage statistics"
    )

@app.get("/stats")
async def get_analytics_stats():
    """Get comprehensive analytics statistics - Modular"""
    try:
        # Combine multiple data sources
        show_analytics = await get_show_analytics()
        performance = await get_performance_metrics()
        usage = await get_usage_statistics()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "show_analytics": show_analytics,
            "performance": performance,
            "usage": usage,
            "modular_config": True,
            "comprehensive": True
        }
    except Exception as e:
        logger.error(f"Failed to get comprehensive stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/config/reload")
async def reload_analytics_config():
    """Reload analytics configuration from Data Service"""
    try:
        # Test configuration access
        cache_ttl = await get_config_value("analytics", "cache_ttl", 86400)
        default_days = await get_config_value("analytics", "default_period_days", 7)
        
        return {
            "status": "success",
            "message": "Analytics configuration reloaded",
            "config": {
                "cache_ttl": cache_ttl,
                "default_period_days": default_days
            },
            "modular_config": True
        }
    except Exception as e:
        logger.error(f"Analytics configuration reload failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Configuration reload failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("ANALYTICS_SERVICE_PORT", "8006"))
    uvicorn.run(app, host="0.0.0.0", port=port) 