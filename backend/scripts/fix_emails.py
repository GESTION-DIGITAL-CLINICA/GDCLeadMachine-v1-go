"""
Script to fix emails with missing accents in the database
This will transliterate Spanish characters properly in existing emails
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
import re
from dotenv import load_dotenv
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent
load_dotenv(ROOT_DIR / '.env')

async def fix_emails():
    # Connect to MongoDB
    mongo_url = os.environ['MONGO_URL']
    db_name = os.environ['DB_NAME']
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    # Transliteration map
    transliteration_map = {
        'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
        'Á': 'A', 'É': 'E', 'Í': 'I', 'Ó': 'O', 'Ú': 'U',
        'ñ': 'n', 'Ñ': 'N', 'ü': 'u', 'Ü': 'U'
    }
    
    # Get all clinics
    clinics = await db.clinics.find({}).to_list(None)
    
    fixed_count = 0
    for clinic in clinics:
        email = clinic.get('email', '')
        
        # Check if email has missing letters (likely due to accent removal)
        # Examples: clnicadental, centromdico, etc.
        suspicious_patterns = [
            r'clnica',  # should be clinica
            r'mdico',   # should be medico
            r'oftalmolgica',  # should be oftalmologica
            r'fisioter',  # could be fisioterapia
            r'psicologa',  # should be psicologia
        ]
        
        needs_fix = any(re.search(pattern, email, re.IGNORECASE) for pattern in suspicious_patterns)
        
        if needs_fix:
            # Try to regenerate from clinic name
            clinic_name = clinic.get('clinica', '')
            location = clinic.get('ciudad', '')
            
            # Apply transliteration
            transliterated_name = clinic_name.lower()
            transliterated_location = location.lower()
            
            for spanish_char, latin_char in transliteration_map.items():
                transliterated_name = transliterated_name.replace(spanish_char, latin_char)
                transliterated_location = transliterated_location.replace(spanish_char, latin_char)
            
            # Remove special characters and spaces
            clean_name = re.sub(r'[^a-z0-9]', '', transliterated_name)
            clean_location = re.sub(r'[^a-z0-9]', '', transliterated_location)
            
            # Generate new email (use same pattern as original)
            if '@gmail.com' in email:
                new_email = f"{clean_name}@gmail.com"
            elif '@hotmail.com' in email:
                new_email = f"{clean_name}{clean_location}@hotmail.com"
            elif 'info@' in email:
                new_email = f"info@{clean_name}.com"
            elif 'contacto@' in email:
                new_email = f"contacto@{clean_name}.es"
            else:
                new_email = f"{clean_name}@gmail.com"
            
            # Update in database
            await db.clinics.update_one(
                {"_id": clinic['_id']},
                {"$set": {"email": new_email[:50]}}
            )
            
            # Also update in email queue if exists
            await db.email_queue.update_many(
                {"clinic_id": str(clinic['_id'])},
                {"$set": {"clinic_data.email": new_email[:50]}}
            )
            
            print(f"Fixed: {email} → {new_email[:50]}")
            fixed_count += 1
    
    print(f"\nTotal emails fixed: {fixed_count}")
    client.close()

if __name__ == "__main__":
    asyncio.run(fix_emails())
