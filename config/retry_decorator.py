"""
RadioX Retry Logic - 80/20 Best Practice
Simple retry decorator for unstable RSS feeds and external APIs
"""

import asyncio
import functools
from typing import Callable, Any
from loguru import logger

def retry_async(max_attempts: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """
    Simple async retry decorator with exponential backoff
    80/20 Best Practice: Handles RSS feed failures (301, 404, timeouts)
    
    Args:
        max_attempts: Maximum retry attempts
        delay: Initial delay in seconds
        backoff: Backoff multiplier for exponential delay
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            current_delay = delay
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    result = await func(*args, **kwargs)
                    if attempt > 0:
                        logger.info(f"✅ {func.__name__} succeeded on attempt {attempt + 1}")
                    return result
                    
                except Exception as e:
                    last_exception = e
                    attempt_num = attempt + 1
                    
                    if attempt_num < max_attempts:
                        logger.warning(f"⚠️ {func.__name__} failed (attempt {attempt_num}/{max_attempts}): {e}")
                        logger.info(f"🔄 Retrying in {current_delay:.1f}s...")
                        await asyncio.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(f"❌ {func.__name__} failed after {max_attempts} attempts: {e}")
            
            # All attempts failed
            raise last_exception
        
        return wrapper
    return decorator 