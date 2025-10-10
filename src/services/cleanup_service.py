"""
Automatic cleanup service for expired temporary pages
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any
from src.services.temporary_pages_service import get_temp_pages_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CleanupService:
    """Service for automatic cleanup of expired temporary pages"""

    def __init__(self):
        self.temp_service = get_temp_pages_service()
        self.is_running = False

    async def start_cleanup_scheduler(self):
        """Start the cleanup scheduler"""
        self.is_running = True
        logger.info("🧹 Starting cleanup scheduler for temporary pages")

        while self.is_running:
            try:
                # Run cleanup
                deleted_count = await self._cleanup_expired_pages()
                if deleted_count > 0:
                    logger.info(f"🧹 Cleaned up {deleted_count} expired temporary pages")

                # Get statistics
                stats = self.temp_service.get_statistics()
                logger.info(f"📊 Current stats: {stats}")

                # Wait for 1 hour before next cleanup
                await asyncio.sleep(3600)  # 1 hour

            except Exception as e:
                logger.error(f"❌ Error in cleanup scheduler: {e}")
                # Wait 5 minutes before retry
                await asyncio.sleep(300)

    async def stop_cleanup_scheduler(self):
        """Stop the cleanup scheduler"""
        self.is_running = False
        logger.info("⏹️  Stopped cleanup scheduler")

    async def _cleanup_expired_pages(self) -> int:
        """Clean up expired temporary pages"""
        try:
            deleted_count = self.temp_service.cleanup_expired_pages()
            return deleted_count
        except Exception as e:
            logger.error(f"❌ Error cleaning up expired pages: {e}")
            return 0

    async def run_manual_cleanup(self) -> Dict[str, Any]:
        """Run manual cleanup and return results"""
        try:
            deleted_count = await self._cleanup_expired_pages()
            stats = self.temp_service.get_statistics()

            return {
                "success": True,
                "deleted_count": deleted_count,
                "timestamp": datetime.utcnow().isoformat(),
                "current_stats": stats
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

# Global instance
cleanup_service = CleanupService()

async def start_cleanup_service():
    """Start the cleanup service"""
    await cleanup_service.start_cleanup_scheduler()

async def stop_cleanup_service():
    """Stop the cleanup service"""
    await cleanup_service.stop_cleanup_scheduler()

# For standalone execution
async def main():
    """Main function for standalone execution"""
    logger.info("🧹 Starting standalone cleanup service")

    # Run one manual cleanup immediately
    result = await cleanup_service.run_manual_cleanup()
    logger.info(f"Initial cleanup result: {result}")

    # Start the scheduler
    await start_cleanup_service()

if __name__ == "__main__":
    asyncio.run(main())