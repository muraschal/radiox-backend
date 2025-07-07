#!/usr/bin/env python3
"""
🔑 KEY SERVICE CLIENT - RADIOX BACKEND
Zentraler Client für API Key Management
"""

import os
import httpx
import asyncio
from typing import Dict, Optional, Any
from loguru import logger

class KeyServiceClient:
    """Client für den zentralen Key Service"""
    
    def __init__(self):
        self.key_service_url = os.getenv("KEY_SERVICE_URL", "http://key-service:8001")
        self.api_keys: Dict[str, str] = {}
        self.keys_loaded = False
        self._client = None
        
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client"""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=10.0)
        return self._client
        
    async def load_api_keys(self) -> bool:
        """Lade API Keys vom Key Service"""
        try:
            client = await self._get_client()
            response = await client.get(f"{self.key_service_url}/keys")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"🔑 Loading {data.get('count', 0)} keys from Key Service")
                
                # Load individual keys
                for key_name in data.get('keys', {}):
                    key_response = await client.get(f"{self.key_service_url}/keys/{key_name}")
                    if key_response.status_code == 200:
                        key_data = key_response.json()
                        self.api_keys[key_name] = key_data['key_value']
                        
                        # Set as environment variable
                        env_var_name = key_name.upper()
                        os.environ[env_var_name] = key_data['key_value']
                        
                self.keys_loaded = True
                logger.info(f"✅ API Keys loaded: {list(self.api_keys.keys())}")
                return True
                
        except Exception as e:
            logger.warning(f"⚠️ Key Service unavailable: {e}")
            
        return False
    
    async def get_api_key(self, key_name: str) -> Optional[str]:
        """Hole einen spezifischen API Key"""
        if not self.keys_loaded:
            await self.load_api_keys()
            
        return self.api_keys.get(key_name) or os.getenv(key_name.upper())
    
    async def refresh_keys(self) -> bool:
        """Refresh API keys from service"""
        self.keys_loaded = False
        return await self.load_api_keys()
    
    async def close(self):
        """Close HTTP client"""
        if self._client:
            await self._client.aclose()
            self._client = None

# Global instance
_key_client: Optional[KeyServiceClient] = None

async def get_key_service_client() -> KeyServiceClient:
    """Get or create Key Service client"""
    global _key_client
    
    if _key_client is None:
        _key_client = KeyServiceClient()
        await _key_client.load_api_keys()
    
    return _key_client

async def get_api_key(key_name: str) -> Optional[str]:
    """Helper function to get API key"""
    client = await get_key_service_client()
    return await client.get_api_key(key_name)

async def close_key_service_client():
    """Close Key Service client"""
    global _key_client
    if _key_client:
        await _key_client.close()
        _key_client = None 