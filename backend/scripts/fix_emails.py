"""
Script to quarantine suspicious generated emails in the database.
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
import re
from dotenv import load_dotenv
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent
load_dotenv(ROOT_DIR.parent / '.env')
load_dotenv(ROOT_DIR / '.env')

async def fix_emails():
    # Connect to MongoDB
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://127.0.0.1:27017/')
    db_name = os.environ.get('DB_NAME', 'gdc_database')
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    # Get all clinics
    clinics = await db.clinics.find({}).to_list(None)
    
    blocked_count = 0
    for clinic in clinics:
        email = clinic.get('email', '')
        if not email:
            continue
        
        # Likely generated or otherwise suspicious business emails.
        suspicious_patterns = [
            r'^info@',
            r'^contacto@',
            r'^recepcion@',
            r'^hola@',
            r'@gmail\.com$',
            r'@hotmail\.',
            r'clnica',
            r'mdico',
            r'oftalmolgica',
        ]
        
        needs_fix = any(re.search(pattern, email, re.IGNORECASE) for pattern in suspicious_patterns)
        
        if needs_fix:
            # Mark as unverified and stop any pending send.
            await db.clinics.update_one(
                {"_id": clinic['_id']},
                {"$set": {"email_verified": False}}
            )
            
            # Also block in email queue if it exists.
            await db.email_queue.update_many(
                {"clinic_id": str(clinic['_id'])},
                {
                    "$set": {
                        "clinic_data.email_verified": False,
                        "status": "blocked_unverified",
                        "block_reason": "Suspicious generated email quarantined"
                    }
                }
            )
            
            print(f"Quarantined suspicious email: {email}")
            blocked_count += 1
    
    print(f"\nTotal suspicious emails quarantined: {blocked_count}")
    client.close()

if __name__ == "__main__":
    asyncio.run(fix_emails())
