"""
RadioX Graceful Shutdown - 80/20 Best Practice
Simple signal handler for clean service shutdown
"""

import signal
import asyncio
from typing import Callable, List
from loguru import logger

class GracefulShutdown:
    """Simple graceful shutdown handler for RadioX services"""
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.shutdown_handlers: List[Callable] = []
        self.is_shutting_down = False
        
    def add_shutdown_handler(self, handler: Callable):
        """Add a shutdown handler function"""
        self.shutdown_handlers.append(handler)
    
    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown (80/20 Best Practice)"""
        def signal_handler(signum, frame):
            if not self.is_shutting_down:
                logger.info(f"🛑 {self.service_name} received signal {signum} - graceful shutdown initiated")
                self.is_shutting_down = True
                asyncio.create_task(self._shutdown())
        
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)
        logger.info(f"✅ {self.service_name} graceful shutdown handlers registered")
    
    async def _shutdown(self):
        """Execute all shutdown handlers"""
        logger.info(f"🔄 {self.service_name} executing {len(self.shutdown_handlers)} shutdown handlers...")
        
        for handler in self.shutdown_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler()
                else:
                    handler()
                logger.info(f"✅ Shutdown handler executed: {handler.__name__}")
            except Exception as e:
                logger.error(f"❌ Shutdown handler failed: {handler.__name__}: {e}")
        
        logger.info(f"🛑 {self.service_name} graceful shutdown complete")

# Global instance for easy import
shutdown_manager = GracefulShutdown("RadioX Service") 