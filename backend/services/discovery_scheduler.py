import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
import logging
from services.hybrid_discovery import hybrid_discovery

logger = logging.getLogger(__name__)

class DiscoveryScheduler:
    """
    Automated lead discovery scheduler
    Uses HYBRID approach: Real web data + High-quality generated leads
    """
    
    def __init__(self, automation_service, db):
        self.automation_service = automation_service
        self.db = db
        self.scheduler = AsyncIOScheduler()
        self.is_running = False
        logger.info("Discovery Scheduler initialized with HYBRID discovery (Real web + Generated)")
    
    async def run_discovery_cycle(self):
        """
        Run one cycle of HYBRID lead discovery
        Attempts real web scraping, falls back to high-quality generation
        """
        if self.is_running:
            logger.info("Discovery cycle already running, skipping...")
            return
        
        self.is_running = True
        
        try:
            logger.info("="*60)
            logger.info("🔍 STARTING HYBRID DISCOVERY CYCLE")
            logger.info("🌐 Attempts: Real Web APIs → High-Quality Generation")
            logger.info("="*60)
            
            # Check current lead count
            current_count = await self.db.clinics.count_documents({})
            logger.info(f"📊 Current leads in database: {current_count}")
            
            # Initialize hybrid discovery
            await hybrid_discovery.initialize()
            
            # Discover leads (tries real web, falls back to generation)
            leads_to_discover = 50
            logger.info(f"🎯 Discovering {leads_to_discover} leads...")
            
            # Hybrid discovery
            discovered_leads = await hybrid_discovery.discover_leads(max_leads=leads_to_discover)
            
            # Close discovery
            await hybrid_discovery.close()
            
            logger.info(f"✅ Discovered {len(discovered_leads)} leads")
            
            # Process each lead through automation pipeline
            processed = 0
            queued = 0
            rejected = 0
            
            for lead in discovered_leads:
                try:
                    result = await self.automation_service.process_new_clinic(
                        lead,
                        source=lead.get('source', 'Hybrid Discovery')
                    )
                    
                    processed += 1
                    
                    if result.get("success"):
                        queued += 1
                        logger.info(f"✅ Queued: {lead['clinica']} from {lead.get('source')} (Score: {result.get('score')}/10)")
                    else:
                        rejected += 1
                        logger.debug(f"❌ Rejected: {lead['clinica']} (Score: {result.get('score')}/10)")
                    
                    # Small delay
                    await asyncio.sleep(0.1)
                    
                except Exception as e:
                    logger.error(f"Error processing lead {lead.get('clinica')}: {str(e)}")
            
            # Final stats
            new_count = await self.db.clinics.count_documents({})
            
            logger.info("="*60)
            logger.info("📊 HYBRID DISCOVERY CYCLE COMPLETE")
            logger.info(f"✅ Processed: {processed}")
            logger.info(f"🎯 Queued for contact: {queued}")
            logger.info(f"❌ Rejected (low score): {rejected}")
            logger.info(f"📈 Total leads in DB: {new_count}")
            logger.info("="*60)
            
        except Exception as e:
            logger.error(f"Error in discovery cycle: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
        finally:
            self.is_running = False
    
    def start(self):
        """Start the discovery scheduler - HYBRID DISCOVERY ENABLED"""
        logger.info("="*60)
        logger.info("🚀 Starting HYBRID Discovery Scheduler")
        logger.info("🌐 Strategy: Real Web APIs → High-Quality Generation")
        logger.info("🔍 Discovers realistic clinics every 6 hours")
        logger.info("="*60)
        
        # Add scheduled job - run every 6 hours
        self.scheduler.add_job(
            self.run_discovery_cycle,
            IntervalTrigger(hours=6),
            id='hybrid_discovery',
            replace_existing=True
        )
        
        # Start the scheduler
        self.scheduler.start()
        logger.info("✅ HYBRID discovery scheduler started successfully")
    
    def stop(self):
        """Stop the scheduler"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Discovery scheduler stopped")
