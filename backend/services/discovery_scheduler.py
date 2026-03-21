import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
import logging

logger = logging.getLogger(__name__)

class DiscoveryScheduler:
    """Schedules continuous lead discovery"""
    
    def __init__(self, automation_service, db):
        self.automation_service = automation_service
        self.db = db
        self.scheduler = AsyncIOScheduler()
        self.is_running = False
    
    async def run_discovery_cycle(self):
        """Run one discovery cycle"""
        if self.is_running:
            logger.info("Discovery cycle already running, skipping...")
            return
        
        self.is_running = True
        logger.info("="*60)
        logger.info("STARTING LEAD DISCOVERY CYCLE")
        logger.info("="*60)
        
        try:
            from services.lead_discovery_service import lead_discovery_service
            
            result = await lead_discovery_service.continuous_discovery(
                self.automation_service,
                self.db
            )
            
            logger.info("="*60)
            logger.info("DISCOVERY CYCLE COMPLETE")
            logger.info(f"✓ Total discovered: {result['total_discovered']}")
            logger.info(f"✓ Total queued for email: {result['total_queued']}")
            logger.info(f"✓ Regions covered: {result['regions_covered']}")
            logger.info("="*60)
            
        except Exception as e:
            logger.error(f"Error in discovery cycle: {str(e)}")
        finally:
            self.is_running = False
    
    def start(self):
        """Start the discovery scheduler"""
        # Run discovery every 2 hours
        self.scheduler.add_job(
            self.run_discovery_cycle,
            IntervalTrigger(hours=2),
            id='lead_discovery_cycle',
            replace_existing=True
        )
        
        # Also run immediately on startup (after 30 seconds delay)
        self.scheduler.add_job(
            self.run_discovery_cycle,
            'date',
            run_date=None,
            id='initial_discovery',
            replace_existing=True
        )
        
        self.scheduler.start()
        logger.info("Lead discovery scheduler started - running every 2 hours")
    
    def stop(self):
        """Stop the scheduler"""
        self.scheduler.shutdown()
        logger.info("Lead discovery scheduler stopped")

discovery_scheduler = None
