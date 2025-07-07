#!/usr/bin/env python3
"""
🔑 KEY SERVICE - RADIOX BACKEND
Business Logic Service für API Key Management via Database Service
80/20 BEST PRACTICE: Environment config
"""

import os
import sys
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx

# Add parent directory to path for config import
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from config.service_config import config

# Logging Setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="RadioX Key Service", version="1.0.0")

class KeyService:
    """Business Logic Service für Key Management"""
    
    def __init__(self):
        self.database_client: Optional[httpx.AsyncClient] = None
        self.api_keys: Dict[str, str] = {}
        self.last_refresh = None
        
    async def initialize(self):
        """Initialisiere Database Service Client"""
        try:
            self.database_client = httpx.AsyncClient(
                base_url=config.DATABASE_URL,
                timeout=30.0
            )
            
            logger.info(f"🔗 Database Service client initialized: {config.DATABASE_URL}")
            
            # Test connection to Database Service
            try:
                health_response = await self.database_client.get("/health")
                health_response.raise_for_status()
                logger.info("✅ Database Service connection verified")
            except Exception as e:
                logger.error(f"❌ FAIL FAST: Database Service unreachable: {e}")
                raise Exception(f"Key Service REQUIRES Database Service connection: {e}")
            
            # Load API keys immediately
            await self.refresh_api_keys()
            
        except Exception as e:
            logger.error(f"❌ Key Service initialization failed: {e}")
            raise
    
    async def refresh_api_keys(self) -> Dict[str, str]:
        """Lade alle API Keys via Database Service"""
        try:
            if not self.database_client:
                raise Exception("Database Service client not initialized")
            
            # Get API keys from Database Service
            logger.info("🔍 Fetching API keys from Database Service...")
            response = await self.database_client.get("/api-keys")
            response.raise_for_status()
            
            keys_data = response.json()
            
            if not keys_data:
                logger.warning("⚠️ No API keys received from Database Service")
                return {}
            
            # Process keys - Business Logic Layer
            self.api_keys = {}
            for item in keys_data:
                key_name = item["name"]
                key_value = item["value"]
                
                # Business Logic: Set environment variable for other services
                env_var_name = key_name.upper()
                os.environ[env_var_name] = key_value
                self.api_keys[key_name] = key_value
            
            self.last_refresh = datetime.now()
            logger.info(f"✅ Loaded {len(self.api_keys)} API keys from Database Service: {list(self.api_keys.keys())}")
            
            return self.api_keys
            
        except httpx.HTTPStatusError as e:
            logger.error(f"❌ Database Service HTTP error: {e.response.status_code}")
            return {}
        except Exception as e:
            logger.error(f"❌ API keys refresh failed: {e}")
            return {}
    
    async def get_key(self, key_name: str) -> Optional[str]:
        """Hole einen spezifischen API Key - Business Logic"""
        # Business Logic: Auto-refresh every 5 minutes
        if not self.last_refresh or (datetime.now() - self.last_refresh).seconds > 300:
            await self.refresh_api_keys()
        
        return self.api_keys.get(key_name)
    
    async def get_all_keys(self) -> Dict[str, str]:
        """Hole alle API Keys - Business Logic"""
        # Business Logic: Auto-refresh check
        if not self.last_refresh or (datetime.now() - self.last_refresh).seconds > 300:
            await self.refresh_api_keys()
        
        # Business Logic: Return keys without values for security
        return {key: "***" for key in self.api_keys.keys()}
    
    async def close(self):
        """Cleanup Database Service client"""
        if self.database_client:
            await self.database_client.aclose()

# Initialize service
key_service = KeyService()

@app.on_event("startup")
async def startup_event():
    """Startup: Initialize Key Service with Database Service connection"""
    logger.info("🚀 Key Service starting...")
    await key_service.initialize()

@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown: Cleanup"""
    logger.info("🛑 Key Service shutting down...")
    await key_service.close()

# API Endpoints - Business Logic Layer
@app.get("/health")
async def health_check():
    """Health check endpoint with dependency validation"""
    try:
        # Test Database Service connection
        database_status = "unknown"
        if key_service.database_client:
            try:
                db_health = await key_service.database_client.get("/health")
                db_health.raise_for_status()
                database_status = "healthy"
            except:
                database_status = "unhealthy"
        
        overall_status = "healthy" if database_status == "healthy" else "unhealthy"
        
        return {
            "status": overall_status,
            "service": "key-service",
            "version": "1.0.0", 
            "timestamp": datetime.now().isoformat(),
            "keys_loaded": len(key_service.api_keys),
            "last_refresh": key_service.last_refresh.isoformat() if key_service.last_refresh else None,
            "dependencies": {
                "database_service": database_status
            },
            "port": 8002  # Updated port
        }
    except Exception as e:
        logger.error(f"❌ Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "service": "key-service",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/keys")
async def get_all_keys():
    """Get all available API keys (masked) - Business Logic"""
    keys = await key_service.get_all_keys()
    return {
        "keys": keys,
        "count": len(keys),
        "last_refresh": key_service.last_refresh.isoformat() if key_service.last_refresh else None
    }

@app.get("/keys/{key_name}")
async def get_key(key_name: str):
    """Get specific API key value - Business Logic"""
    key_value = await key_service.get_key(key_name)
    
    if not key_value:
        raise HTTPException(status_code=404, detail=f"API key '{key_name}' not found")
    
    return {
        "key_name": key_name,
        "key_value": key_value,
        "timestamp": datetime.now().isoformat()
    }

@app.post("/refresh")
async def refresh_keys():
    """Manually refresh API keys from Database Service - Business Logic"""
    try:
        # Business Logic: Clear cache in Database Service first
        if key_service.database_client:
            try:
                await key_service.database_client.post("/api-keys/refresh")
                logger.info("✅ Database Service cache cleared")
            except Exception as e:
                logger.warning(f"⚠️ Failed to clear Database Service cache: {e}")
        
        # Then refresh our keys
        keys = await key_service.refresh_api_keys()
        return {
            "success": True,
            "keys_loaded": len(keys),
            "keys": list(keys.keys()),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"❌ Key refresh failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Key refresh failed: {str(e)}")

@app.get("/env/{env_var}")
async def get_env_var(env_var: str):
    """Get environment variable value - Business Logic"""
    value = os.getenv(env_var)
    
    if not value:
        raise HTTPException(status_code=404, detail=f"Environment variable '{env_var}' not found")
    
    return {
        "env_var": env_var,
        "value": value,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/")
async def root():
    """Key Service root endpoint"""
    return {
        "service": "RadioX Key Service",
        "version": "1.0.0",
        "description": "Business Logic Service for API Key Management",
        "port": 8002,
        "dependencies": ["database-service:8001"],
        "endpoints": {
            "keys": "/keys",
            "refresh": "/refresh",
            "health": "/health"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)  # Port changed to 8002 