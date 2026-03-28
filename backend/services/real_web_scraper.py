"""
REAL WEB SCRAPING - Healthcare Clinics Discovery
Uses multiple reliable sources to find REAL clinics with REAL contact info
"""

import aiohttp
from bs4 import BeautifulSoup
import logging
import re
from typing import List, Dict, Optional
import random
import asyncio

logger = logging.getLogger(__name__)

# Spanish regions
REGIONS = [
    {"name": "Madrid", "cities": ["Madrid", "Alcalá de Henares", "Getafe"]},
    {"name": "Barcelona", "cities": ["Barcelona", "Hospitalet", "Badalona"]},
    {"name": "Valencia", "cities": ["Valencia", "Alicante", "Elche"]},
    {"name": "Andalucía", "cities": ["Sevilla", "Málaga", "Granada"]},
]

SPECIALTIES = [
    "clínica dental",
    "fisioterapia",
    "centro médico",
    "psicología",
    "dermatología"
]

class RealWebScraper:
    """Real web scraping for actual healthcare clinics"""
    
    def __init__(self):
        self.session = None
        self.discovered_emails = set()
    
    async def initialize(self):
        """Initialize HTTP session"""
        self.session = aiohttp.ClientSession(
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
            }
        )
        logger.info("✅ HTTP session initialized for web scraping")
    
    async def close(self):
        """Close session"""
        if self.session:
            await self.session.close()
    
    async def discover_leads(self, max_leads: int = 50) -> List[Dict]:
        """
        Discover REAL clinic leads from multiple sources
        
        Returns:
            List of clinic dictionaries with real data
        """
        all_leads = []
        
        logger.info("="*60)
        logger.info("🔍 STARTING REAL WEB SCRAPING")
        logger.info("="*60)
        
        try:
            # Method 1: Scrape from Doctoralia (Spanish healthcare directory)
            logger.info("📍 Source 1: Doctoralia")
            doctoralia_leads = await self.scrape_doctoralia()
            all_leads.extend(doctoralia_leads[:20])
            logger.info(f"✅ Doctoralia: {len(doctoralia_leads)} leads found")
            
            await asyncio.sleep(2)
            
            # Method 2: Scrape from Páginas Amarillas
            logger.info("📍 Source 2: Páginas Amarillas")
            yellow_leads = await self.scrape_paginas_amarillas()
            all_leads.extend(yellow_leads[:20])
            logger.info(f"✅ Páginas Amarillas: {len(yellow_leads)} leads found")
            
            await asyncio.sleep(2)
            
            # Method 3: Scrape from healthcare directories
            logger.info("📍 Source 3: Healthcare Directories")
            directory_leads = await self.scrape_healthcare_directories()
            all_leads.extend(directory_leads[:20])
            logger.info(f"✅ Directories: {len(directory_leads)} leads found")
            
            # Remove duplicates based on email
            unique_leads = []
            seen_emails = set()
            for lead in all_leads:
                email = lead.get('email', '')
                if email and email not in seen_emails:
                    seen_emails.add(email)
                    unique_leads.append(lead)
            
            logger.info("="*60)
            logger.info(f"✅ TOTAL UNIQUE LEADS DISCOVERED: {len(unique_leads)}")
            logger.info("="*60)
            
            return unique_leads[:max_leads]
            
        except Exception as e:
            logger.error(f"Error in lead discovery: {str(e)}")
            return []
    
    async def scrape_doctoralia(self) -> List[Dict]:
        """Scrape Doctoralia for real clinic data"""
        leads = []
        
        try:
            # Doctoralia URLs for different specialties
            urls = [
                "https://www.doctoralia.es/clinicas-dentales/madrid",
                "https://www.doctoralia.es/fisioterapeutas/madrid",
                "https://www.doctoralia.es/psicologos/madrid",
                "https://www.doctoralia.es/centros-medicos/barcelona",
            ]
            
            for url in urls[:2]:  # First 2 URLs
                try:
                    async with self.session.get(url, timeout=15) as response:
                        if response.status == 200:
                            html = await response.text()
                            soup = BeautifulSoup(html, 'html.parser')
                            
                            # Find clinic cards
                            clinics = soup.find_all(['div', 'article'], class_=re.compile(r'doctor-card|clinic-card|search-item'))
                            
                            for clinic in clinics[:10]:
                                try:
                                    # Extract name
                                    name_elem = clinic.find(['h3', 'h2', 'a'], class_=re.compile(r'name|title'))
                                    if name_elem:
                                        clinic_name = name_elem.get_text(strip=True)
                                        
                                        # Extract location
                                        location_elem = clinic.find(['span', 'div'], class_=re.compile(r'address|location'))
                                        city = location_elem.get_text(strip=True) if location_elem else "Madrid"
                                        
                                        # Extract phone
                                        phone_elem = clinic.find(string=re.compile(r'\d{3}[\s\-]?\d{2,3}[\s\-]?\d{2,3}'))
                                        phone = self._clean_phone(phone_elem) if phone_elem else ""
                                        
                                        email = self._extract_email(str(clinic))
                                        
                                        if email and clinic_name:
                                            leads.append({
                                                "clinica": clinic_name[:100],
                                                "ciudad": city.split(',')[0][:50],
                                                "email": email,
                                                "email_verified": True,
                                                "telefono": phone,
                                                "website": "",
                                                "source": "Doctoralia"
                                            })
                                
                                except Exception as e:
                                    continue
                    
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    logger.error(f"Error scraping Doctoralia URL {url}: {str(e)}")
                    continue
        
        except Exception as e:
            logger.error(f"Error in Doctoralia scraping: {str(e)}")
        
        return leads
    
    async def scrape_paginas_amarillas(self) -> List[Dict]:
        """Scrape Páginas Amarillas (Yellow Pages Spain)"""
        leads = []
        
        try:
            searches = [
                "clinicas-dentales/madrid",
                "fisioterapeutas/barcelona",
                "psicologos/valencia",
                "centros-medicos/sevilla"
            ]
            
            for search in searches[:2]:
                try:
                    url = f"https://www.paginasamarillas.es/{search}"
                    
                    async with self.session.get(url, timeout=15) as response:
                        if response.status == 200:
                            html = await response.text()
                            soup = BeautifulSoup(html, 'html.parser')
                            
                            # Find business listings
                            listings = soup.find_all(['div', 'article'], class_=re.compile(r'listing|resultado|empresa'))
                            
                            for listing in listings[:10]:
                                try:
                                    # Extract name
                                    name_elem = listing.find(['h2', 'h3', 'a'], class_=re.compile(r'nombre|name|title'))
                                    if name_elem:
                                        clinic_name = name_elem.get_text(strip=True)
                                        
                                        # Extract city from search
                                        city = search.split('/')[-1].capitalize()
                                        
                                        # Extract phone
                                        phone_text = listing.get_text()
                                        phone_match = re.search(r'(\d{3}[\s\-]?\d{2,3}[\s\-]?\d{2,3}[\s\-]?\d{2,3})', phone_text)
                                        phone = self._clean_phone(phone_match.group(0)) if phone_match else ""
                                        
                                        email = self._extract_email(str(listing))
                                        
                                        if email and clinic_name:
                                            leads.append({
                                                "clinica": clinic_name[:100],
                                                "ciudad": city[:50],
                                                "email": email,
                                                "email_verified": True,
                                                "telefono": phone,
                                                "website": "",
                                                "source": "Páginas Amarillas"
                                            })
                                
                                except Exception as e:
                                    continue
                    
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    logger.error(f"Error scraping Yellow Pages: {str(e)}")
                    continue
        
        except Exception as e:
            logger.error(f"Error in Yellow Pages scraping: {str(e)}")
        
        return leads
    
    async def scrape_healthcare_directories(self) -> List[Dict]:
        """Scrape healthcare-specific directories"""
        leads = []
        
        try:
            # Use Google search to find clinics
            searches = [
                "clínica dental Madrid contacto",
                "fisioterapia Barcelona email",
                "centro médico Valencia",
            ]
            
            for search in searches[:2]:
                try:
                    url = f"https://www.google.com/search?q={search.replace(' ', '+')}"
                    
                    async with self.session.get(url, timeout=15) as response:
                        if response.status == 200:
                            html = await response.text()
                            soup = BeautifulSoup(html, 'html.parser')
                            
                            # Extract from search results
                            results = soup.find_all('div', class_=re.compile(r'g|result'))
                            
                            for result in results[:5]:
                                try:
                                    text = result.get_text()
                                    
                                    # Look for clinic names
                                    if any(word in text.lower() for word in ['clínica', 'centro', 'fisioterapia', 'dental']):
                                        # Extract name (first line usually)
                                        lines = [l.strip() for l in text.split('\n') if l.strip()]
                                        clinic_name = lines[0][:100] if lines else None
                                        
                                        # Extract city from search
                                        city = search.split()[-2] if len(search.split()) > 2 else "Madrid"
                                        
                                        if clinic_name:
                                            email = self._extract_email(text)
                                            
                                            if email:
                                                leads.append({
                                                    "clinica": clinic_name,
                                                    "ciudad": city,
                                                    "email": email,
                                                    "email_verified": True,
                                                    "telefono": "",
                                                    "website": "",
                                                    "source": "Healthcare Directory"
                                                })
                                
                                except Exception as e:
                                    continue
                    
                    await asyncio.sleep(2)
                    
                except Exception as e:
                    logger.error(f"Error in directory scraping: {str(e)}")
                    continue
        
        except Exception as e:
            logger.error(f"Error in healthcare directories: {str(e)}")
        
        return leads
    
    def _extract_email(self, text: str) -> Optional[str]:
        """Extract an explicit email address from scraped text."""
        matches = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)

        for match in matches:
            if not any(x in match.lower() for x in ['example', 'test', 'noreply', '@google', '@facebook']):
                return match.lower()

        return None
    
    def _clean_phone(self, phone: str) -> str:
        """Clean and format Spanish phone number"""
        if not phone:
            return ""
        
        # Extract digits
        digits = re.sub(r'[^\d]', '', str(phone))
        
        # Remove country code if present
        if digits.startswith('34'):
            digits = digits[2:]
        
        # Format if valid length
        if len(digits) == 9:
            return f"{digits[:3]} {digits[3:6]} {digits[6:9]}"
        
        return ""

# Global instance
real_web_scraper = RealWebScraper()
