"""
Lead Management System API Tests
Tests all CRUD operations and critical endpoints for the 24/7 lead generation system
"""

import pytest
import requests
import os

# Get BASE_URL from environment
BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestHealthAndStatus:
    """Health check and status endpoint tests"""
    
    def test_api_root_health(self):
        """Test API root endpoint returns running status"""
        response = requests.get(f"{BASE_URL}/api/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "running"
        assert "GDC Lead Management System" in data["message"]
        print(f"✓ API root health check passed: {data}")
    
    def test_automation_status(self):
        """Test 24/7 automation status endpoint"""
        response = requests.get(f"{BASE_URL}/api/automation/status")
        assert response.status_code == 200
        data = response.json()
        
        # Verify automation structure
        assert "automation_active" in data
        assert "discovery" in data
        assert "email_queue" in data
        assert "leads" in data
        
        # Verify discovery scheduler
        assert "is_running" in data["discovery"]
        assert "scheduler_active" in data["discovery"]
        assert "scheduled_jobs" in data["discovery"]
        
        # Verify email queue stats
        assert "pending" in data["email_queue"]
        assert "sent" in data["email_queue"]
        assert "accounts_active" in data["email_queue"]
        
        print(f"✓ Automation status: active={data['automation_active']}, scheduler={data['discovery']['scheduler_active']}")
        print(f"  Email queue: pending={data['email_queue']['pending']}, sent={data['email_queue']['sent']}")
    
    def test_notion_status(self):
        """Test Notion integration status (expected to show not configured)"""
        response = requests.get(f"{BASE_URL}/api/notion/status")
        assert response.status_code == 200
        data = response.json()
        
        # Verify status structure
        assert "configured" in data
        assert "api_key_present" in data
        assert "database_id_valid" in data
        assert "message" in data
        
        # Expected: not configured due to invalid database ID
        assert data["database_id_valid"] == False
        print(f"✓ Notion status: configured={data['configured']}, message={data['message'][:50]}...")


class TestDashboardStats:
    """Dashboard statistics endpoint tests"""
    
    def test_dashboard_stats(self):
        """Test dashboard stats endpoint returns all required metrics"""
        response = requests.get(f"{BASE_URL}/api/stats/dashboard")
        assert response.status_code == 200
        data = response.json()
        
        # Verify all required fields
        required_fields = ["total_leads", "emails_sent", "responded", "clients", 
                          "high_score", "pending_followups", "response_rate", "by_region"]
        for field in required_fields:
            assert field in data, f"Missing field: {field}"
        
        # Verify data types
        assert isinstance(data["total_leads"], int)
        assert isinstance(data["emails_sent"], int)
        assert isinstance(data["response_rate"], (int, float))
        assert isinstance(data["by_region"], list)
        
        print(f"✓ Dashboard stats: total_leads={data['total_leads']}, emails_sent={data['emails_sent']}")
        print(f"  High score leads: {data['high_score']}, Response rate: {data['response_rate']}%")


class TestClinicsAPI:
    """Clinics CRUD endpoint tests"""
    
    def test_get_clinics_list(self):
        """Test getting list of clinics with pagination"""
        response = requests.get(f"{BASE_URL}/api/clinics?skip=0&limit=10")
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "clinics" in data
        assert "total" in data
        assert "skip" in data
        assert "limit" in data
        
        # Verify clinic data structure
        if data["clinics"]:
            clinic = data["clinics"][0]
            assert "clinica" in clinic
            assert "ciudad" in clinic
            assert "email" in clinic
            
        print(f"✓ Clinics list: total={data['total']}, returned={len(data['clinics'])}")
    
    def test_get_clinics_with_limit(self):
        """Test clinics pagination with different limits"""
        response = requests.get(f"{BASE_URL}/api/clinics?skip=0&limit=5")
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["clinics"]) <= 5
        print(f"✓ Clinics pagination: requested 5, got {len(data['clinics'])}")
    
    def test_create_clinic(self):
        """Test creating a new clinic"""
        test_clinic = {
            "clinica": "TEST_Clinica Prueba Automatizada",
            "ciudad": "Madrid",
            "email": "test_automated@testclinic.es",
            "telefono": "+34600000000",
            "website": ""
        }
        
        response = requests.post(f"{BASE_URL}/api/clinics", json=test_clinic)
        assert response.status_code == 200
        data = response.json()
        
        # Verify clinic was created with scoring and queued
        assert "message" in data or "score" in data
        assert "queued_for_email" in data or "details" in data
        print(f"✓ Clinic created successfully: {data}")
    
    def test_bulk_import_clinics(self):
        """Test bulk importing clinics"""
        bulk_data = {
            "clinics": [
                {
                    "clinica": "TEST_Bulk Clinic 1",
                    "ciudad": "Barcelona",
                    "email": "bulk1@test.es",
                    "telefono": "+34600000001"
                },
                {
                    "clinica": "TEST_Bulk Clinic 2",
                    "ciudad": "Valencia",
                    "email": "bulk2@test.es",
                    "telefono": "+34600000002"
                }
            ],
            "source": "Automated Test"
        }
        
        response = requests.post(f"{BASE_URL}/api/clinics/bulk", json=bulk_data)
        assert response.status_code == 200
        data = response.json()
        
        print(f"✓ Bulk import completed: {data}")


class TestEmailAPI:
    """Email management endpoint tests"""
    
    def test_email_stats(self):
        """Test email statistics endpoint"""
        response = requests.get(f"{BASE_URL}/api/email/stats")
        assert response.status_code == 200
        data = response.json()
        
        # Verify required fields
        assert "total_sent" in data
        assert "pending" in data
        assert "failed" in data
        assert "active_accounts" in data
        
        # Verify data types
        assert isinstance(data["total_sent"], int)
        assert isinstance(data["pending"], int)
        assert isinstance(data["active_accounts"], int)
        
        print(f"✓ Email stats: sent={data['total_sent']}, pending={data['pending']}, accounts={data['active_accounts']}")
    
    def test_email_queue(self):
        """Test email queue endpoint"""
        response = requests.get(f"{BASE_URL}/api/email/queue")
        assert response.status_code == 200
        data = response.json()
        
        assert "queue" in data
        assert isinstance(data["queue"], list)
        
        # Verify queue item structure if items exist
        if data["queue"]:
            item = data["queue"][0]
            assert "status" in item
            assert "clinic_id" in item
        
        print(f"✓ Email queue: {len(data['queue'])} items")
    
    def test_email_queue_filtered(self):
        """Test email queue with status filter"""
        response = requests.get(f"{BASE_URL}/api/email/queue?status=pending")
        assert response.status_code == 200
        data = response.json()
        
        # All items should have pending status
        for item in data["queue"]:
            assert item["status"] == "pending"
        
        print(f"✓ Email queue (pending): {len(data['queue'])} items")
    
    def test_email_accounts(self):
        """Test email accounts endpoint"""
        response = requests.get(f"{BASE_URL}/api/email-accounts")
        assert response.status_code == 200
        data = response.json()
        
        assert "accounts" in data
        assert isinstance(data["accounts"], list)
        
        # Verify password is not exposed
        for account in data["accounts"]:
            assert "password" not in account
            assert "username" in account
        
        print(f"✓ Email accounts: {len(data['accounts'])} configured")


class TestContactsAPI:
    """Contact history endpoint tests"""
    
    def test_contacts_summary(self):
        """Test contacts summary endpoint"""
        response = requests.get(f"{BASE_URL}/api/contacts/summary")
        assert response.status_code == 200
        data = response.json()
        
        # Verify structure
        assert "contact_summary" in data
        assert "email_queue" in data
        assert "whatsapp_queue" in data
        
        print(f"✓ Contacts summary: {data['contact_summary']}")
    
    def test_recent_contacts(self):
        """Test recent contacts endpoint"""
        response = requests.get(f"{BASE_URL}/api/contacts/recent?limit=10")
        assert response.status_code == 200
        data = response.json()
        
        assert "contacts" in data
        assert "count" in data
        assert isinstance(data["contacts"], list)
        
        print(f"✓ Recent contacts: {data['count']} items")


class TestDiscoveryAPI:
    """Lead discovery endpoint tests"""
    
    def test_discovery_status(self):
        """Test discovery status endpoint"""
        response = requests.get(f"{BASE_URL}/api/discovery/status")
        assert response.status_code == 200
        data = response.json()
        
        assert "is_running" in data
        assert "scheduler_running" in data
        
        print(f"✓ Discovery status: running={data['is_running']}, scheduler={data['scheduler_running']}")
    
    def test_trigger_discovery(self):
        """Test triggering lead discovery"""
        response = requests.post(f"{BASE_URL}/api/discovery/trigger")
        assert response.status_code == 200
        data = response.json()
        
        assert "message" in data
        assert "status" in data
        
        print(f"✓ Discovery triggered: {data['message']}")


class TestPDFImportAPI:
    """PDF lead import endpoint tests"""
    
    def test_import_pdf_leads(self):
        """Test PDF lead import endpoint"""
        pdf_data = [
            {
                "clinic_name": "TEST_PDF Clinic Import",
                "city": "Sevilla",
                "address": "Calle Test 123",
                "phone_numbers": ["+34600000003"],
                "email": "pdftest@clinic.es"
            }
        ]
        
        response = requests.post(f"{BASE_URL}/api/leads/import-pdf", json=pdf_data)
        assert response.status_code == 200
        data = response.json()
        
        assert "success" in data
        assert "stats" in data
        
        print(f"✓ PDF import: success={data['success']}, stats={data['stats']}")


class TestWhatsAppAPI:
    """WhatsApp endpoint tests"""
    
    def test_bulk_whatsapp_endpoint(self):
        """Test bulk WhatsApp endpoint exists and responds"""
        response = requests.post(f"{BASE_URL}/api/whatsapp/bulk?score_threshold=10")
        # Should return 200 even if no leads match
        assert response.status_code == 200
        data = response.json()
        
        print(f"✓ WhatsApp bulk endpoint: {data}")


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
