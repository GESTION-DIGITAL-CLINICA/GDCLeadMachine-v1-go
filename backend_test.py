#!/usr/bin/env python3
"""
Backend API Testing for GDC Lead Management System
Tests all critical endpoints after deployment fixes
"""

import requests
import json
import sys
import os
from datetime import datetime

# Get backend URL from frontend .env
def get_backend_url():
    try:
        with open('/app/frontend/.env', 'r') as f:
            for line in f:
                if line.startswith('REACT_APP_BACKEND_URL='):
                    return line.split('=', 1)[1].strip()
    except Exception as e:
        print(f"Error reading frontend .env: {e}")
        return None

# Test configuration
BACKEND_URL = get_backend_url()
if not BACKEND_URL:
    print("ERROR: Could not get REACT_APP_BACKEND_URL from frontend/.env")
    sys.exit(1)

API_BASE = f"{BACKEND_URL}/api"
print(f"Testing backend at: {API_BASE}")

# Test results tracking
test_results = {
    "passed": 0,
    "failed": 0,
    "errors": []
}

def log_test(endpoint, status, message, response_data=None):
    """Log test results"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    status_symbol = "✅" if status == "PASS" else "❌"
    print(f"[{timestamp}] {status_symbol} {endpoint}: {message}")
    
    if status == "PASS":
        test_results["passed"] += 1
    else:
        test_results["failed"] += 1
        test_results["errors"].append({
            "endpoint": endpoint,
            "message": message,
            "response": response_data
        })

def test_endpoint(endpoint, expected_status=200, method="GET", data=None, check_fields=None):
    """Test a single endpoint"""
    url = f"{API_BASE}{endpoint}"
    
    try:
        if method == "GET":
            response = requests.get(url, timeout=10)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=10)
        else:
            log_test(endpoint, "FAIL", f"Unsupported method: {method}")
            return None
            
        # Check status code
        if response.status_code != expected_status:
            log_test(endpoint, "FAIL", 
                    f"Expected {expected_status}, got {response.status_code}. Response: {response.text[:200]}")
            return None
            
        # Try to parse JSON
        try:
            response_data = response.json()
        except json.JSONDecodeError:
            log_test(endpoint, "FAIL", "Invalid JSON response")
            return None
            
        # Check required fields if specified
        if check_fields:
            missing_fields = []
            for field in check_fields:
                if field not in response_data:
                    missing_fields.append(field)
            
            if missing_fields:
                log_test(endpoint, "FAIL", f"Missing fields: {missing_fields}")
                return None
                
        log_test(endpoint, "PASS", f"Status {response.status_code}, valid JSON response")
        return response_data
        
    except requests.exceptions.RequestException as e:
        log_test(endpoint, "FAIL", f"Request failed: {str(e)}")
        return None
    except Exception as e:
        log_test(endpoint, "FAIL", f"Unexpected error: {str(e)}")
        return None

def test_projections(endpoint, response_data, expected_fields):
    """Test that projections are working (only expected fields returned)"""
    if not response_data:
        return False
        
    # Get the data array from response
    data_key = None
    if "clinics" in response_data:
        data_key = "clinics"
    elif "queue" in response_data:
        data_key = "queue"
    
    if not data_key or not response_data[data_key]:
        log_test(endpoint, "FAIL", f"No data found in response for projection test")
        return False
        
    # Check first item for field projection
    first_item = response_data[data_key][0]
    actual_fields = set(first_item.keys())
    expected_fields_set = set(expected_fields)
    
    # Check if we have only expected fields (projections working)
    extra_fields = actual_fields - expected_fields_set
    if extra_fields:
        log_test(endpoint, "FAIL", f"Projection not working - extra fields found: {extra_fields}")
        return False
    else:
        log_test(endpoint, "PASS", f"Projections working - only expected fields returned: {list(actual_fields)}")
        return True

def main():
    """Run all backend tests"""
    print("=" * 60)
    print("GDC LEAD MANAGEMENT SYSTEM - BACKEND API TESTS")
    print("=" * 60)
    print(f"Backend URL: {BACKEND_URL}")
    print(f"API Base: {API_BASE}")
    print("=" * 60)
    
    # Test 1: Health check
    print("\n🔍 Testing Health Check...")
    health_data = test_endpoint("/", check_fields=["message", "status"])
    if health_data:
        print(f"   Health status: {health_data.get('status')}")
    
    # Test 2: Clinics endpoint with projections
    print("\n🔍 Testing Clinics Endpoint...")
    clinics_data = test_endpoint("/clinics?skip=0&limit=5", check_fields=["clinics", "total"])
    if clinics_data:
        print(f"   Total clinics: {clinics_data.get('total', 0)}")
        print(f"   Returned: {len(clinics_data.get('clinics', []))}")
        
        # Test projections
        expected_clinic_fields = [
            "_id", "clinica", "ciudad", "email", "telefono", "website", 
            "score", "estado", "comunidad_autonoma", "scoring_details", "fuente"
        ]
        test_projections("/clinics", clinics_data, expected_clinic_fields)
    
    # Test 3: Email queue endpoint with projections
    print("\n🔍 Testing Email Queue Endpoint...")
    queue_data = test_endpoint("/email/queue", check_fields=["queue"])
    if queue_data:
        print(f"   Queue items: {len(queue_data.get('queue', []))}")
        
        # Test projections if queue has items
        if queue_data.get('queue'):
            expected_queue_fields = [
                "_id", "clinic_id", "status", "added_at", "sent_at", "attempts", "clinic_data"
            ]
            test_projections("/email/queue", queue_data, expected_queue_fields)
    
    # Test 4: Email statistics
    print("\n🔍 Testing Email Statistics...")
    stats_data = test_endpoint("/email/stats", check_fields=["total_sent", "pending", "failed", "active_accounts"])
    if stats_data:
        print(f"   Total sent: {stats_data.get('total_sent', 0)}")
        print(f"   Pending: {stats_data.get('pending', 0)}")
        print(f"   Failed: {stats_data.get('failed', 0)}")
        print(f"   Active accounts: {stats_data.get('active_accounts', 0)}")
    
    # Test 5: Email accounts
    print("\n🔍 Testing Email Accounts...")
    accounts_data = test_endpoint("/email-accounts", check_fields=["accounts"])
    if accounts_data:
        print(f"   Email accounts: {len(accounts_data.get('accounts', []))}")
    
    # Test 6: Dashboard statistics
    print("\n🔍 Testing Dashboard Statistics...")
    dashboard_data = test_endpoint("/stats/dashboard", check_fields=["total_leads", "emails_sent"])
    if dashboard_data:
        print(f"   Total leads: {dashboard_data.get('total_leads', 0)}")
        print(f"   Emails sent: {dashboard_data.get('emails_sent', 0)}")
        print(f"   Response rate: {dashboard_data.get('response_rate', 0)}%")
    
    # Test 7: Discovery status
    print("\n🔍 Testing Discovery Status...")
    discovery_data = test_endpoint("/discovery/status", check_fields=["is_running", "scheduler_running"])
    if discovery_data:
        print(f"   Discovery running: {discovery_data.get('is_running', False)}")
        print(f"   Scheduler running: {discovery_data.get('scheduler_running', False)}")
    
    # Print final results
    print("\n" + "=" * 60)
    print("TEST RESULTS SUMMARY")
    print("=" * 60)
    print(f"✅ Passed: {test_results['passed']}")
    print(f"❌ Failed: {test_results['failed']}")
    print(f"📊 Success Rate: {(test_results['passed'] / (test_results['passed'] + test_results['failed']) * 100):.1f}%")
    
    if test_results["errors"]:
        print("\n🚨 FAILED TESTS:")
        for error in test_results["errors"]:
            print(f"   • {error['endpoint']}: {error['message']}")
    
    print("\n" + "=" * 60)
    
    # Return exit code based on results
    return 0 if test_results["failed"] == 0 else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)