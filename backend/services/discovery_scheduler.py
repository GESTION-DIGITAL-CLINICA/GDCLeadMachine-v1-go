import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
import logging
from services.high_quality_lead_generator import high_quality_generator

logger = logging.getLogger(__name__)

class DiscoveryScheduler:
    """
    Automated lead discovery scheduler
    Generates high-quality healthcare clinic leads every 6 hours
    """
    
    def __init__(self, automation_service, db):
        self.automation_service = automation_service
        self.db = db
        self.scheduler = AsyncIOScheduler()
        self.is_running = False
        logger.info("Discovery Scheduler initialized with high-quality lead generator")
    
    async def run_discovery_cycle(self):
        """
        Run one cycle of lead discovery
        Generates high-quality healthcare clinic leads
        """
        if self.is_running:
            logger.info("Discovery cycle already running, skipping...")
            return
        
        self.is_running = True
        
        try:
            logger.info("="*60)
            logger.info("🔍 STARTING LEAD DISCOVERY CYCLE")
            logger.info("="*60)
            
            # Check current lead count
            current_count = await self.db.clinics.count_documents({})
            logger.info(f"📊 Current leads in database: {current_count}")
            
            # Generate high-quality leads (50 per cycle)
            leads_to_generate = 50
            logger.info(f"🎯 Generating {leads_to_generate} high-quality leads...")
            
            # Generate leads
            discovered_leads = high_quality_generator.generate_leads(count=leads_to_generate)
            
            logger.info(f"✅ Generated {len(discovered_leads)} leads")
            
            # Process each lead through automation pipeline
            processed = 0
            queued = 0
            rejected = 0
            
            for lead in discovered_leads:
                try:
                    result = await self.automation_service.process_new_clinic(
                        lead,
                        source="Auto-Discovery"
                    )
                    
                    processed += 1
                    
                    if result.get("success"):
                        queued += 1
                        logger.info(f"✅ Queued: {lead['clinica']} (Score: {result.get('score')}/10)")
                    else:
                        rejected += 1
                        logger.debug(f"❌ Rejected: {lead['clinica']} (Score: {result.get('score')}/10)")
                    
                    # Small delay to avoid overwhelming the system
                    await asyncio.sleep(0.1)
                    
                except Exception as e:
                    logger.error(f"Error processing lead {lead.get('clinica')}: {str(e)}")
            
            # Final stats
            new_count = await self.db.clinics.count_documents({})
            
            logger.info("="*60)
            logger.info("📊 DISCOVERY CYCLE COMPLETE")
            logger.info(f"✅ Processed: {processed}")
            logger.info(f"🎯 Queued for contact: {queued}")
            logger.info(f"❌ Rejected (low score): {rejected}")
            logger.info(f"📈 Total leads in DB: {new_count}")
            logger.info("="*60)
            
        except Exception as e:
            logger.error(f"Error in discovery cycle: {str(e)}")
        finally:
            self.is_running = False
    
    def start(self):
        """Start the discovery scheduler - ENABLED for lead generation"""
        logger.info("="*60)
        logger.info("🚀 Starting Auto-Discovery Scheduler")
        logger.info("🔍 Will generate high-quality leads every 6 hours")
        logger.info("="*60)
        
        # Add scheduled job - run every 6 hours
        self.scheduler.add_job(
            self.run_discovery_cycle,
            IntervalTrigger(hours=6),
            id='lead_discovery',
            replace_existing=True
        )
        
        # Start the scheduler
        self.scheduler.start()
        logger.info("✅ Discovery scheduler started successfully")
    
    def stop(self):
        """Stop the scheduler"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Discovery scheduler stopped")
