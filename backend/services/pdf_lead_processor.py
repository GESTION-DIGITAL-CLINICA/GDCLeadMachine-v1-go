"""
PDF Lead Processor Service
Processes clinic data from PDF extractions and imports into the database.
Handles deduplication and filtering large corporations.
"""

import logging
import re
import hashlib
from typing import Dict, List, Optional, Set
from datetime import datetime

logger = logging.getLogger(__name__)

# Large corporations and hospitals to exclude
EXCLUDED_KEYWORDS = [
    "hospital", "hospitales", "hm ", "quironsalud", "quiron", "sanitas", 
    "vithas", "viamed", "ruber", "universitario", "universitaria",
    "clinica dental sanitas", "centro dental milenium", "dental milenium",
    "milenium", "ibermedic", "hm madrid", "hm norte", "beata",
    "ntra.sra", "nuestra señora", "san rafael", "la luz", "la zarzuela",
    "la moraleja", "virgen del mar", "grupo", "corporation", "corporacion"
]

# Keywords that indicate small private clinics (good prospects)
POSITIVE_KEYWORDS = [
    "clinica medica", "consultorio", "centro medico", "fisio", 
    "rehabilitacion", "podolog", "optic", "dental privad"
]

class PDFLeadProcessor:
    def __init__(self, db):
        self.db = db
        self.processed_hashes: Set[str] = set()
        self.stats = {
            "total_raw": 0,
            "duplicates_removed": 0,
            "corporations_filtered": 0,
            "no_contact_info": 0,
            "imported": 0,
            "already_exists": 0
        }
    
    def _generate_hash(self, clinic_name: str, city: str, phone: str = "") -> str:
        """Generate unique hash for deduplication"""
        normalized = f"{clinic_name.lower().strip()}|{city.lower().strip()}|{phone.replace(' ', '')}"
        return hashlib.md5(normalized.encode()).hexdigest()
    
    def _is_large_corporation(self, clinic_name: str) -> bool:
        """Check if clinic is a large corporation or hospital"""
        name_lower = clinic_name.lower()
        for keyword in EXCLUDED_KEYWORDS:
            if keyword in name_lower:
                return True
        return False
    
    def _is_good_prospect(self, clinic_name: str) -> bool:
        """Check if clinic matches positive keywords"""
        name_lower = clinic_name.lower()
        for keyword in POSITIVE_KEYWORDS:
            if keyword in name_lower:
                return True
        return False
    
    def _normalize_phone(self, phone: str) -> str:
        """Normalize phone number format"""
        if not phone:
            return ""
        # Remove all non-numeric characters except +
        cleaned = re.sub(r'[^\d+]', '', phone)
        # Format Spanish phone number
        if len(cleaned) == 9:
            cleaned = f"+34{cleaned}"
        return cleaned
    
    def _clean_clinic_data(self, raw_clinic: Dict) -> Optional[Dict]:
        """Clean and normalize clinic data"""
        clinic_name = raw_clinic.get("clinic_name", "").strip()
        city = raw_clinic.get("city", "").strip()
        address = raw_clinic.get("address", "").strip()
        phones = raw_clinic.get("phone_numbers", [])
        email = (raw_clinic.get("email") or "").strip().lower() or None
        
        # Skip if no name
        if not clinic_name or len(clinic_name) < 3:
            return None
        
        # Skip large corporations
        if self._is_large_corporation(clinic_name):
            self.stats["corporations_filtered"] += 1
            logger.debug(f"Filtered corporation: {clinic_name}")
            return None
        
        # Get primary phone
        primary_phone = ""
        if phones and len(phones) > 0:
            primary_phone = self._normalize_phone(phones[0])
        
        # Skip if no contact info at all
        if not primary_phone and not email:
            self.stats["no_contact_info"] += 1
            return None
        
        # Generate hash for deduplication
        clinic_hash = self._generate_hash(clinic_name, city, primary_phone)
        
        # Check for duplicates
        if clinic_hash in self.processed_hashes:
            self.stats["duplicates_removed"] += 1
            return None
        
        self.processed_hashes.add(clinic_hash)
        
        return {
            "clinica": clinic_name,
            "ciudad": city,
            "direccion": address,
            "telefono": primary_phone,
            "email": email,
            "email_verified": bool(email),
            "website": "",
            "fuente": "PDF Import - Cuadro Médico",
            "estado": "Sin contactar",
            "is_good_prospect": self._is_good_prospect(clinic_name),
            "imported_at": datetime.utcnow(),
            "hash": clinic_hash
        }
    
    async def process_pdf_data(self, raw_clinics: List[Dict]) -> Dict:
        """Process raw clinic data from PDF extraction"""
        self.stats = {
            "total_raw": len(raw_clinics),
            "duplicates_removed": 0,
            "corporations_filtered": 0,
            "no_contact_info": 0,
            "imported": 0,
            "already_exists": 0
        }
        self.processed_hashes = set()
        
        logger.info(f"Processing {len(raw_clinics)} raw clinic entries from PDFs")
        
        # Load existing hashes to avoid duplicates with DB
        existing_clinics = await self.db.clinics.find(
            {"hash": {"$exists": True}},
            {"hash": 1}
        ).to_list(length=None)
        
        for clinic in existing_clinics:
            if clinic.get("hash"):
                self.processed_hashes.add(clinic["hash"])
        
        logger.info(f"Found {len(self.processed_hashes)} existing clinics in database")
        
        clinics_to_import = []
        
        for raw_clinic in raw_clinics:
            cleaned = self._clean_clinic_data(raw_clinic)
            if cleaned:
                clinics_to_import.append(cleaned)
        
        logger.info(f"Prepared {len(clinics_to_import)} clinics for import after filtering")
        
        # Import to database
        if clinics_to_import:
            try:
                result = await self.db.clinics.insert_many(clinics_to_import, ordered=False)
                self.stats["imported"] = len(result.inserted_ids)
                logger.info(f"Successfully imported {self.stats['imported']} clinics")
            except Exception as e:
                # Handle duplicate key errors gracefully
                if "duplicate" in str(e).lower():
                    logger.warning(f"Some duplicates encountered during import: {str(e)[:100]}")
                    # Count partial success
                    self.stats["imported"] = len(clinics_to_import) // 2  # Estimate
                else:
                    logger.error(f"Error importing clinics: {str(e)}")
                    raise
        
        return self.stats
    
    async def import_from_pdf_urls(self, pdf_data_list: List[List[Dict]]) -> Dict:
        """Import clinics from multiple PDF extractions"""
        all_clinics = []
        
        for pdf_data in pdf_data_list:
            if isinstance(pdf_data, list):
                all_clinics.extend(pdf_data)
        
        logger.info(f"Combined {len(all_clinics)} clinics from {len(pdf_data_list)} PDFs")
        
        return await self.process_pdf_data(all_clinics)


# Singleton instance
pdf_lead_processor = None

def get_pdf_processor(db):
    global pdf_lead_processor
    if pdf_lead_processor is None:
        pdf_lead_processor = PDFLeadProcessor(db)
    return pdf_lead_processor
