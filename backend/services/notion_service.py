import os
from notion_client import AsyncClient
from typing import List, Dict, Optional
import logging
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
ROOT_DIR = Path(__file__).parent.parent
load_dotenv(ROOT_DIR / '.env')

logger = logging.getLogger(__name__)

class NotionService:
    def __init__(self):
        api_key = os.environ.get('NOTION_API_KEY', '')
        self.client = None
        self.database_id = os.environ.get('NOTION_DATABASE_ID', '')
        self.is_configured = False
        
        # Only initialize if we have a valid API key format
        if api_key and api_key.startswith('secret_') or api_key.startswith('ntn_'):
            try:
                self.client = AsyncClient(auth=api_key)
                self.is_configured = self._is_valid_database_id()
                if self.is_configured:
                    logger.info("Notion service initialized successfully")
                else:
                    logger.warning(f"Notion database ID not properly configured: {self.database_id[:10]}...")
            except Exception as e:
                logger.warning(f"Notion client initialization failed: {str(e)}")
        else:
            logger.warning("Notion API key not configured or invalid format")
    
    def _is_valid_database_id(self) -> bool:
        """Check if database ID is a valid UUID format"""
        if not self.database_id:
            return False
        # Valid Notion database IDs are 32 chars (no hyphens) or 36 chars (with hyphens)
        clean_id = self.database_id.replace('-', '')
        return len(clean_id) == 32 and clean_id.isalnum()
    
    async def get_database_schema(self) -> Optional[Dict]:
        """Get the database schema to understand what properties are available"""
        if not self.is_configured or not self.client:
            return None
            
        try:
            response = await self.client.databases.retrieve(self.database_id)
            return response
        except Exception as e:
            logger.error(f"Error getting database schema: {str(e)}")
            return None
    
    async def add_clinic(self, clinic_data: Dict) -> Optional[str]:
        """Add a clinic to Notion database"""
        if not self.is_configured or not self.client:
            logger.debug("Notion not configured, skipping add_clinic")
            return None
            
        try:
            # First get the database schema to understand what properties exist
            schema = await self.get_database_schema()
            available_props = set(schema.get("properties", {}).keys()) if schema else set()
            
            # Build properties based on what exists in the database
            properties = {}
            
            # Title property (required - find the title property name)
            title_prop = None
            for prop_name, prop_config in (schema.get("properties", {}) if schema else {}).items():
                if prop_config.get("type") == "title":
                    title_prop = prop_name
                    break
            
            if title_prop:
                properties[title_prop] = {"title": [{"text": {"content": clinic_data.get("clinica", "")[:2000]}}]}
            else:
                # Fallback - try common title names
                properties["Nombre"] = {"title": [{"text": {"content": clinic_data.get("clinica", "")[:2000]}}]}
            
            # Add other properties only if they exist in the database
            if "Ciudad" in available_props:
                properties["Ciudad"] = {"rich_text": [{"text": {"content": clinic_data.get("ciudad", "")[:2000]}}]}
            
            if "Email" in available_props:
                email = clinic_data.get("email", "")
                if email:
                    properties["Email"] = {"email": email}
            
            if "Teléfono" in available_props:
                phone = clinic_data.get("telefono", "")
                if phone:
                    properties["Teléfono"] = {"phone_number": phone}
            
            if "Score" in available_props:
                score = clinic_data.get("score")
                if score is not None:
                    properties["Score"] = {"number": score}
            
            if "Estado" in available_props:
                properties["Estado"] = {"select": {"name": clinic_data.get("estado", "Sin contactar")}}
            
            if "Website" in available_props:
                website = clinic_data.get("website", "")
                if website:
                    properties["Website"] = {"url": website}
            
            if "Fuente" in available_props:
                properties["Fuente"] = {"rich_text": [{"text": {"content": clinic_data.get("fuente", "Manual")[:2000]}}]}
            
            response = await self.client.pages.create(
                parent={"database_id": self.database_id},
                properties=properties
            )
            
            logger.info(f"Added clinic to Notion: {clinic_data.get('clinica')}")
            return response["id"]
        except Exception as e:
            logger.error(f"Error adding clinic to Notion: {str(e)}")
            return None
    
    async def update_clinic(self, page_id: str, updates: Dict) -> bool:
        """Update clinic in Notion"""
        if not self.is_configured or not self.client:
            return False
            
        try:
            properties = {}
            
            if "score" in updates:
                properties["Score"] = {"number": updates["score"]}
            if "estado" in updates:
                properties["Estado"] = {"select": {"name": updates["estado"]}}
            if "email_sent" in updates:
                properties["Email Enviado"] = {"checkbox": updates["email_sent"]}
            if "last_email_date" in updates:
                properties["Último Email"] = {"date": {"start": updates["last_email_date"]}}
            
            await self.client.pages.update(
                page_id=page_id,
                properties=properties
            )
            logger.info(f"Updated clinic in Notion: {page_id}")
            return True
        except Exception as e:
            logger.error(f"Error updating clinic in Notion: {str(e)}")
            return False
    
    async def get_clinics(self, filter_dict: Optional[Dict] = None) -> List[Dict]:
        """Get clinics from Notion"""
        if not self.is_configured or not self.client:
            return []
            
        try:
            query_params = {"database_id": self.database_id}
            if filter_dict:
                query_params["filter"] = filter_dict
            
            response = await self.client.databases.query(**query_params)
            
            clinics = []
            for page in response["results"]:
                props = page["properties"]
                clinic = {
                    "id": page["id"],
                    "clinica": props.get("Nombre", {}).get("title", [{}])[0].get("text", {}).get("content", ""),
                    "ciudad": props.get("Ciudad", {}).get("rich_text", [{}])[0].get("text", {}).get("content", ""),
                    "email": props.get("Email", {}).get("email", ""),
                    "telefono": props.get("Teléfono", {}).get("phone_number", ""),
                    "score": props.get("Score", {}).get("number"),
                    "estado": props.get("Estado", {}).get("select", {}).get("name", ""),
                    "website": props.get("Website", {}).get("url", ""),
                }
                clinics.append(clinic)
            
            return clinics
        except Exception as e:
            logger.error(f"Error getting clinics from Notion: {str(e)}")
            return []
    
    async def test_connection(self) -> Dict:
        """Test the Notion connection and return status"""
        result = {
            "configured": self.is_configured,
            "api_key_present": bool(os.environ.get('NOTION_API_KEY')),
            "database_id_valid": self._is_valid_database_id(),
            "connection_working": False,
            "message": ""
        }
        
        if not result["api_key_present"]:
            result["message"] = "NOTION_API_KEY not set in environment"
            return result
            
        if not result["database_id_valid"]:
            result["message"] = f"NOTION_DATABASE_ID is not a valid UUID format. Current value: '{self.database_id}'. Please get the correct database ID from your Notion database URL."
            return result
        
        if self.client:
            try:
                # Try to retrieve the database to test connection
                await self.client.databases.retrieve(self.database_id)
                result["connection_working"] = True
                result["message"] = "Notion connection successful!"
            except Exception as e:
                result["message"] = f"Connection failed: {str(e)}"
        
        return result

notion_service = NotionService()
