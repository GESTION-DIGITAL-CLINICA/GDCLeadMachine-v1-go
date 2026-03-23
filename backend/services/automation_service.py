import logging
from typing import Dict

logger = logging.getLogger(__name__)

class AutomationService:
    """
    Handles the automated pipeline:
    New Clinic → AI Scoring → Save to MongoDB → Sync to Notion → Queue Email + WhatsApp → Send
    """
    
    def __init__(self):
        self.db = None
        self.email_queue_service = None
        self.whatsapp_queue_service = None
        self.contact_history_service = None
    
    def initialize(self, db, email_queue_service, whatsapp_queue_service=None, contact_history_service=None):
        """Initialize with database and queue services"""
        self.db = db
        self.email_queue_service = email_queue_service
        self.whatsapp_queue_service = whatsapp_queue_service
        self.contact_history_service = contact_history_service
        logger.info("Automation service initialized with email, WhatsApp, Notion, and contact history")
    
    async def sync_to_notion(self, clinic_data: Dict) -> bool:
        """Sync clinic to Notion database"""
        try:
            from services.notion_service import notion_service
            
            if not notion_service.is_configured:
                return False
            
            notion_data = {
                "clinica": clinic_data.get("clinica", ""),
                "ciudad": clinic_data.get("ciudad", ""),
                "email": clinic_data.get("email", ""),
                "telefono": clinic_data.get("telefono", ""),
                "score": clinic_data.get("score"),
                "estado": clinic_data.get("estado", "Sin contactar"),
                "website": clinic_data.get("website", ""),
                "fuente": clinic_data.get("fuente", "Automático")
            }
            
            page_id = await notion_service.add_clinic(notion_data)
            
            if page_id:
                # Store Notion page ID in MongoDB for future updates
                if clinic_data.get("_id"):
                    await self.db.clinics.update_one(
                        {"_id": clinic_data["_id"]},
                        {"$set": {"notion_page_id": page_id}}
                    )
                logger.info(f"✅ Synced to Notion: {clinic_data.get('clinica')}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error syncing to Notion: {str(e)}")
            return False
    
    async def process_new_clinic(self, clinic_data: Dict, source: str = "Manual") -> Dict:
        """
        Complete automation pipeline for new clinic:
        1. Score with AI
        2. Save to MongoDB
        3. Sync to Notion CRM
        4. Queue email AND WhatsApp if score is good
        5. Track in contact history
        """
        from services.ai_scoring_service import ai_scoring_service
        
        try:
            logger.info(f"Processing new clinic: {clinic_data.get('clinica')}")
            
            # Step 1: AI Scoring
            scoring_result = await ai_scoring_service.score_clinic(clinic_data)
            clinic_data["score"] = scoring_result["score"]
            clinic_data["scoring_details"] = scoring_result["details"]
            clinic_data["fuente"] = source
            clinic_data["estado"] = "Sin contactar"
            
            logger.info(f"Scored {clinic_data.get('clinica')}: {scoring_result['score']}/10")
            
            # Step 2: Save to MongoDB
            if scoring_result["should_contact"]:
                result = await self.db.clinics.insert_one(clinic_data)
                clinic_id = str(result.inserted_id)
                clinic_data["_id"] = clinic_id
                
                # Step 3: Sync to Notion CRM
                notion_synced = await self.sync_to_notion(clinic_data)
                
                queued_channels = []
                
                # Step 4a: Queue email
                if self.email_queue_service:
                    await self.email_queue_service.add_to_queue(clinic_id, clinic_data)
                    queued_channels.append("email")
                    logger.info(f"Clinic added to email queue: {clinic_data.get('clinica')}")
                
                # Step 4b: Queue WhatsApp (if has phone)
                if self.whatsapp_queue_service and clinic_data.get('telefono'):
                    await self.whatsapp_queue_service.add_to_queue(clinic_id, clinic_data)
                    queued_channels.append("WhatsApp")
                    logger.info(f"Clinic added to WhatsApp queue: {clinic_data.get('clinica')}")
                
                # Step 5: Record initial state in contact history
                if self.contact_history_service:
                    for channel in queued_channels:
                        await self.contact_history_service.record_contact(
                            clinic_id=clinic_id,
                            method=channel.lower().replace("whatsapp", "whatsapp"),
                            status="pending",
                            details={"queued_at": clinic_data.get("_id")}
                        )
                
                channels_str = " y ".join(queued_channels)
                return {
                    "success": True,
                    "score": scoring_result["score"],
                    "message": f"Clínica procesada y añadida a colas de {channels_str} (Score: {scoring_result['score']}/10)",
                    "details": scoring_result["details"],
                    "queued_for_email": "email" in queued_channels,
                    "queued_for_whatsapp": "WhatsApp" in queued_channels,
                    "queued_channels": queued_channels,
                    "notion_synced": notion_synced
                }
            else:
                logger.info(f"Clinic rejected (low score): {clinic_data.get('clinica')}")
                return {
                    "success": False,
                    "score": scoring_result["score"],
                    "message": f"Clínica rechazada - score muy bajo ({scoring_result['score']}/10)",
                    "details": scoring_result["details"],
                    "queued_for_email": False,
                    "queued_for_whatsapp": False
                }
                
        except Exception as e:
            logger.error(f"Error processing clinic: {str(e)}")
            return {
                "success": False,
                "message": f"Error: {str(e)}",
                "queued_for_email": False,
                "queued_for_whatsapp": False
            }
    
    async def batch_process_clinics(self, clinics: list, source: str = "Bulk Import") -> Dict:
        """Process multiple clinics at once"""
        results = {
            "total": len(clinics),
            "processed": 0,
            "queued": 0,
            "rejected": 0,
            "errors": 0
        }
        
        for clinic in clinics:
            try:
                result = await self.process_new_clinic(clinic, source)
                results["processed"] += 1
                
                if result["success"]:
                    results["queued"] += 1
                else:
                    results["rejected"] += 1
                    
            except Exception as e:
                logger.error(f"Error processing clinic {clinic.get('clinica')}: {str(e)}")
                results["errors"] += 1
        
        return results

automation_service = AutomationService()
