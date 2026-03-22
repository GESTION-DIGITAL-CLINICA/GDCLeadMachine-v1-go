"""
HIGH-QUALITY Lead Generator for GDC LeadMachine
Generates realistic healthcare clinic leads for immediate testing and demonstration
"""

import logging
from typing import List, Dict
import random

logger = logging.getLogger(__name__)

class HighQualityLeadGenerator:
    """Generates realistic, high-quality healthcare clinic leads"""
    
    def __init__(self):
        self.generated_emails = set()
    
    def generate_leads(self, count: int = 50) -> List[Dict]:
        """
        Generate high-quality clinic leads
        
        Args:
            count: Number of leads to generate (default: 50)
        
        Returns:
            List of clinic dictionaries with complete data
        """
        leads = []
        
        # Real Spanish cities
        cities = [
            "Madrid", "Barcelona", "Valencia", "Sevilla", "Zaragoza",
            "Málaga", "Murcia", "Palma", "Las Palmas", "Bilbao",
            "Alicante", "Córdoba", "Valladolid", "Vigo", "Gijón",
            "L'Hospitalet", "Granada", "Vitoria", "Elche", "Oviedo",
            "Badalona", "Cartagena", "Terrassa", "Jerez", "Sabadell"
        ]
        
        # Realistic clinic name patterns
        dental_names = [
            "Clínica Dental {}", "Clínica Odontológica {}", "Centro Dental {}",
            "Dental {}", "Odontología {}", "Sonrisa {}", "Dentistas {}"
        ]
        
        fisio_names = [
            "Fisioterapia {}", "Centro de Fisioterapia {}", "Clínica {}",
            "Fisiocenter {}", "Rehabilitación {}", "Fisio {}"
        ]
        
        psicologia_names = [
            "Centro de Psicología {}", "Psicólogos {}", "Gabinete Psicológico {}",
            "Psicología {}", "Centro Psicológico {}"
        ]
        
        medical_names = [
            "Centro Médico {}", "Clínica {}", "Policlínica {}",
            "Centro de Salud {}", "Clínica Médica {}"
        ]
        
        veterinaria_names = [
            "Clínica Veterinaria {}", "Veterinaria {}", "Centro Veterinario {}",
            "Clínica Veterinaria {}", "Hospital Veterinario {}"
        ]
        
        dermatologia_names = [
            "Clínica Dermatológica {}", "Dermatología {}", "Centro Dermatológico {}",
            "Clínica de Dermatología {}"
        ]
        
        oftalmologia_names = [
            "Clínica Oftalmológica {}", "Centro de Oftalmología {}", "Oftalmología {}",
            "Clínica Ocular {}"
        ]
        
        # All name patterns by specialty
        specialties = {
            "dental": dental_names,
            "fisioterapia": fisio_names,
            "psicología": psicologia_names,
            "médico": medical_names,
            "veterinaria": veterinaria_names,
            "dermatología": dermatologia_names,
            "oftalmología": oftalmologia_names
        }
        
        # Location-specific names
        location_modifiers = [
            "Centro", "Norte", "Sur", "Este", "Oeste", "Plaza", "Avenida",
            "Barrio", "Zona", "Área", "Sector", "Distrito"
        ]
        
        # Generate leads
        specialty_keys = list(specialties.keys())
        
        for i in range(count):
            city = random.choice(cities)
            specialty_key = specialty_keys[i % len(specialty_keys)]
            name_pattern = random.choice(specialties[specialty_key])
            
            # Create clinic name
            if random.random() < 0.6:
                # With location modifier
                clinic_name = name_pattern.format(f"{city} {random.choice(location_modifiers)}")
            else:
                # Just city name
                clinic_name = name_pattern.format(city)
            
            # Generate realistic email
            email = self._generate_email(clinic_name, city)
            
            # Skip if duplicate
            if email in self.generated_emails:
                continue
            
            self.generated_emails.add(email)
            
            # Generate phone number (Spanish format)
            phone = self._generate_phone()
            
            leads.append({
                "clinica": clinic_name,
                "ciudad": city,
                "email": email,
                "telefono": phone if random.random() < 0.8 else "",  # 80% have phones
                "website": "",
                "source": "High-Quality Generator"
            })
        
        logger.info(f"✅ Generated {len(leads)} high-quality leads")
        return leads
    
    def _generate_email(self, clinic_name: str, city: str) -> str:
        """Generate realistic professional email"""
        # Clean clinic name
        clean_name = clinic_name.lower()
        clean_name = clean_name.replace("clínica", "").replace("centro", "")
        clean_name = clean_name.replace("de", "").strip()
        
        # Remove accents
        replacements = {
            'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
            'ñ': 'n', 'ü': 'u'
        }
        for old, new in replacements.items():
            clean_name = clean_name.replace(old, new)
        
        # Get first 2-3 words
        words = [w for w in clean_name.split() if len(w) > 2][:2]
        domain_part = "".join(words).replace(" ", "")[:15]
        
        # Email prefixes
        prefixes = ["info", "contacto", "citas", "recepcion", "admin"]
        prefix = random.choice(prefixes)
        
        # Domains (realistic Spanish domains)
        domains = [
            f"{domain_part}.com",
            f"{domain_part}.es",
            "gmail.com",
            "hotmail.es",
            "outlook.es"
        ]
        
        domain = random.choice(domains)
        
        return f"{prefix}@{domain}"
    
    def _generate_phone(self) -> str:
        """Generate realistic Spanish phone number"""
        # Spanish mobile: 6XX XXX XXX or 7XX XXX XXX
        # Spanish landline: 9XX XXX XXX
        
        if random.random() < 0.7:
            # Mobile
            first = random.choice(['6', '7'])
            return f"{first}{random.randint(10, 99)} {random.randint(100, 999)} {random.randint(100, 999)}"
        else:
            # Landline
            return f"9{random.randint(10, 99)} {random.randint(100, 999)} {random.randint(100, 999)}"

# Global instance
high_quality_generator = HighQualityLeadGenerator()
