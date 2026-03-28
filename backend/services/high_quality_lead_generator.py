"""
HIGH-QUALITY Lead Generator for GDC LeadMachine
Generates synthetic healthcare clinic leads for testing without fabricated email addresses
"""

import logging
from typing import List, Dict
import random

logger = logging.getLogger(__name__)

class HighQualityLeadGenerator:
    """Generates synthetic healthcare clinic leads without email fabrication."""
    
    def __init__(self):
        self.generated_leads = set()
    
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
            
            lead_key = f"{clinic_name}|{city}"
            
            # Skip if duplicate
            if lead_key in self.generated_leads:
                continue
            
            self.generated_leads.add(lead_key)
            
            # Generate phone number (Spanish format)
            phone = self._generate_phone()
            
            leads.append({
                "clinica": clinic_name,
                "ciudad": city,
                "email": None,
                "email_verified": False,
                "telefono": phone if random.random() < 0.8 else "",  # 80% have phones
                "website": "",
                "source": "High-Quality Generator"
            })
        
        logger.info(f"✅ Generated {len(leads)} high-quality leads")
        return leads
    
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
