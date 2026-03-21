import logging
from typing import Dict

logger = logging.getLogger(__name__)

class AutomationService:
    """
    Handles the automated pipeline:
    New Clinic → AI Scoring → Save to MongoDB → Queue Email → Send
    """
    
    def __init__(self):
        self.db = None
        self.email_queue_service = None
    
    def initialize(self, db, email_queue_service):
        """Initialize with database and email queue service"""
        self.db = db
        self.email_queue_service = email_queue_service
    
    async def process_new_clinic(self, clinic_data: Dict, source: str = "Manual") -> Dict:
        """
        Complete automation pipeline for new clinic:
        1. Score with AI
        2. Save to MongoDB
        3. Queue email if score is good
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
                
                # Step 3: Queue email
                if self.email_queue_service:
                    await self.email_queue_service.add_to_queue(clinic_id, clinic_data)
                    logger.info(f"Clinic added to queue: {clinic_data.get('clinica')}")
                
                return {
                    "success": True,
                    "score": scoring_result["score"],
                    "message": f"Clínica procesada y añadida a cola de emails (Score: {scoring_result['score']}/10)",
                    "details": scoring_result["details"],
                    "queued_for_email": True
                }
            else:
                logger.info(f"Clinic rejected (low score): {clinic_data.get('clinica')}")
                return {
                    "success": False,
                    "score": scoring_result["score"],
                    "message": f"Clínica rechazada - score muy bajo ({scoring_result['score']}/10)",
                    "details": scoring_result["details"],
                    "queued_for_email": False
                }
                
        except Exception as e:
            logger.error(f"Error processing clinic: {str(e)}")
            return {
                "success": False,
                "message": f"Error: {str(e)}",
                "queued_for_email": False
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
