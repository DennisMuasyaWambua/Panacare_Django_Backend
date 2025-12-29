#!/usr/bin/env python3
"""
Test script for Community Health Provider (CHP) Clinical Decision Support System (CDSS) endpoints
"""

import os
import sys
import django

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'panacare.settings')
django.setup()

import requests
import json
from datetime import datetime
import uuid
from django.contrib.auth import get_user_model
from users.models import Role, Patient, CommunityHealthProvider
from django.test import TestCase

User = get_user_model()

class CDSSEndpointTester:
    """Test class for CDSS endpoints"""
    
    def __init__(self, base_url='http://localhost:8000'):
        self.base_url = base_url
        self.chp_token = None
        self.patient_token = None
        self.test_patient_id = None
        self.test_chp_user = None
        self.test_patient_user = None
        
    def setup_test_data(self):
        """Create test CHP and Patient users"""
        print("Setting up test data...")
        
        # Get or create roles
        chp_role, _ = Role.objects.get_or_create(name='community_health_provider')
        patient_role, _ = Role.objects.get_or_create(name='patient')
        
        # Create CHP user
        chp_email = f'test_chp_{int(datetime.now().timestamp())}@example.com'
        self.test_chp_user = User.objects.create_user(
            username=f'test_chp_{int(datetime.now().timestamp())}',
            email=chp_email,
            password='testpass123',
            first_name='Test',
            last_name='CHP',
            is_verified=True
        )
        self.test_chp_user.roles.add(chp_role)
        
        # Create CHP profile
        CommunityHealthProvider.objects.create(
            user=self.test_chp_user,
            certification_number='CHP-TEST-001',
            years_of_experience=5,
            specialization='Primary Healthcare',
            service_area='Nairobi Central',
            languages_spoken='English, Swahili'
        )
        
        # Create Patient user
        patient_email = f'test_patient_{int(datetime.now().timestamp())}@example.com'
        self.test_patient_user = User.objects.create_user(
            username=f'test_patient_{int(datetime.now().timestamp())}',
            email=patient_email,
            password='testpass123',
            first_name='Test',
            last_name='Patient',
            is_verified=True
        )
        self.test_patient_user.roles.add(patient_role)
        
        # Create Patient profile
        patient_profile = Patient.objects.create(
            user=self.test_patient_user,
            date_of_birth='1980-01-15',
            gender='male',
            height_cm=175,
            weight_kg=80.5,
            blood_type='O+',
            allergies='None known',
            medical_conditions='Hypertension',
            created_by_chp=self.test_chp_user.community_health_provider
        )
        
        self.test_patient_id = str(patient_profile.id)
        
        print(f"Created CHP user: {self.test_chp_user.email}")
        print(f"Created Patient user: {self.test_patient_user.email}")
        print(f"Patient ID: {self.test_patient_id}")
    
    def get_auth_token(self, email, password):
        """Get authentication token for user"""
        login_url = f"{self.base_url}/api/users/login/"
        login_data = {
            "email": email,
            "password": password
        }
        
        response = requests.post(login_url, json=login_data)
        if response.status_code == 200:
            return response.json().get('access')
        else:
            print(f"Login failed for {email}: {response.text}")
            return None
    
    def test_chp_authentication(self):
        """Test CHP authentication"""
        print("\n=== Testing CHP Authentication ===")
        
        self.chp_token = self.get_auth_token(self.test_chp_user.email, 'testpass123')
        if self.chp_token:
            print("✅ CHP authentication successful")
            return True
        else:
            print("❌ CHP authentication failed")
            return False
    
    def test_patient_authentication(self):
        """Test Patient authentication"""
        print("\n=== Testing Patient Authentication ===")
        
        self.patient_token = self.get_auth_token(self.test_patient_user.email, 'testpass123')
        if self.patient_token:
            print("✅ Patient authentication successful")
            return True
        else:
            print("❌ Patient authentication failed")
            return False
    
    def test_general_cdss_endpoint(self):
        """Test the general CDSS endpoint (for patients)"""
        print("\n=== Testing General CDSS Endpoint ===")
        
        if not self.patient_token:
            print("❌ No patient token available")
            return False
        
        headers = {
            'Authorization': f'Bearer {self.patient_token}',
            'Content-Type': 'application/json'
        }
        
        # Test data for CDSS analysis
        cdss_data = {
            "age": 43,
            "gender": "male",
            "weight": 80.5,
            "height": 175,
            "high_blood_pressure": True,
            "diabetes": False,
            "on_medication": True,
            "headache": True,
            "dizziness": False,
            "blurred_vision": False,
            "palpitations": True,
            "fatigue": True,
            "chest_pain": False,
            "frequent_thirst": False,
            "loss_of_appetite": False,
            "frequent_urination": False,
            "other_symptoms": "",
            "no_symptoms": False,
            "systolic_pressure": 145,
            "diastolic_pressure": 95,
            "blood_sugar": 95,
            "heart_rate": 88,
            "sleep_hours": 6.5,
            "exercise_minutes": 20,
            "eats_unhealthy": True,
            "smokes": False,
            "consumes_alcohol": True,
            "skips_medication": False
        }
        
        url = f"{self.base_url}/api/clinical-decision/"
        response = requests.post(url, headers=headers, json=cdss_data)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ General CDSS endpoint successful")
            print(f"Risk Level: {result.get('risk_level')}")
            print(f"BMI Analysis: Available in response")
            print(f"Blood Pressure Status: {result.get('blood_pressure_status')}")
            print(f"Blood Sugar Status: {result.get('blood_sugar_status')}")
            print(f"Record ID: {result.get('record_id')}")
            
            # Print a sample of recommendations
            recommendations = result.get('recommendations', [])
            if recommendations:
                print(f"Sample Recommendations ({len(recommendations)} total):")
                for i, rec in enumerate(recommendations[:3]):  # Show first 3
                    print(f"  {i+1}. {rec}")
            
            return True
        else:
            print(f"❌ General CDSS endpoint failed: {response.text}")
            return False
    
    def test_chp_cdss_endpoint(self):
        """Test the CHP-specific CDSS endpoint"""
        print("\n=== Testing CHP CDSS Endpoint ===")
        
        if not self.chp_token:
            print("❌ No CHP token available")
            return False
        
        if not self.test_patient_id:
            print("❌ No test patient ID available")
            return False
        
        headers = {
            'Authorization': f'Bearer {self.chp_token}',
            'Content-Type': 'application/json'
        }
        
        # CHP CDSS data includes patient_id
        chp_cdss_data = {
            "patient_id": self.test_patient_id,
            "age": 43,
            "gender": "male", 
            "weight": 80.5,
            "height": 175,
            "high_blood_pressure": True,
            "diabetes": False,
            "on_medication": True,
            "headache": True,
            "dizziness": True,
            "blurred_vision": False,
            "palpitations": True,
            "fatigue": True,
            "chest_pain": False,
            "frequent_thirst": False,
            "loss_of_appetite": False,
            "frequent_urination": False,
            "other_symptoms": "Mild shortness of breath during exercise",
            "no_symptoms": False,
            "systolic_bp": 150,  # Note: Different field name in CHP endpoint
            "diastolic_bp": 98,
            "blood_sugar": 110,
            "heart_rate": 92,
            "sleep_hours": 6,
            "exercise_minutes": 15,
            "eats_unhealthy": True,
            "smokes": False,
            "consumes_alcohol": True,
            "skips_medication": True
        }
        
        url = f"{self.base_url}/api/chp/cdss/"
        response = requests.post(url, headers=headers, json=chp_cdss_data)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ CHP CDSS endpoint successful")
            print(f"Analysis ID: {result.get('id')}")
            print(f"Risk Level: {result.get('risk_level')}")
            print(f"BMI: {result.get('bmi')}")
            print(f"BMI Category: {result.get('bmi_category')}")
            print(f"Blood Pressure Status: {result.get('blood_pressure_status')}")
            print(f"Blood Sugar Status: {result.get('blood_sugar_status')}")
            print(f"Heart Rate Status: {result.get('heart_rate_status')}")
            print(f"CHP Name: {result.get('chp_name')}")
            print(f"Patient Name: {result.get('patient_name')}")
            
            # Print some recommendations
            recommendations = result.get('recommendations', [])
            if recommendations:
                print(f"Recommendations ({len(recommendations)} total):")
                for i, rec in enumerate(recommendations[:5]):  # Show first 5
                    print(f"  {i+1}. {rec}")
            
            # Print analysis excerpt
            analysis = result.get('analysis', '')
            if analysis:
                print(f"Analysis (first 200 chars): {analysis[:200]}...")
            
            return True
        else:
            print(f"❌ CHP CDSS endpoint failed: {response.text}")
            return False
    
    def test_clinical_history_endpoint(self):
        """Test the clinical history endpoint"""
        print("\n=== Testing Clinical History Endpoint ===")
        
        if not self.patient_token:
            print("❌ No patient token available")
            return False
        
        headers = {
            'Authorization': f'Bearer {self.patient_token}',
            'Content-Type': 'application/json'
        }
        
        url = f"{self.base_url}/api/clinical-history/"
        response = requests.get(url, headers=headers)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            history = response.json()
            print("✅ Clinical history endpoint successful")
            print(f"Total Records: {len(history)}")
            
            if history:
                latest_record = history[0]
                print(f"Latest Record ID: {latest_record.get('id')}")
                print(f"Latest Record Date: {latest_record.get('created_at')}")
                print(f"Latest Risk Level: {latest_record.get('risk_level')}")
            
            return True
        else:
            print(f"❌ Clinical history endpoint failed: {response.text}")
            return False
    
    def test_unauthorized_access(self):
        """Test unauthorized access scenarios"""
        print("\n=== Testing Unauthorized Access ===")
        
        # Test CDSS without authentication
        url = f"{self.base_url}/api/clinical-decision/"
        response = requests.post(url, json={"age": 30, "gender": "male", "weight": 70, "height": 170})
        
        if response.status_code == 401:
            print("✅ Unauthorized access properly rejected for general CDSS")
        else:
            print(f"❌ Unexpected response for unauthorized general CDSS: {response.status_code}")
        
        # Test CHP CDSS without authentication
        url = f"{self.base_url}/api/chp/cdss/"
        response = requests.post(url, json={"patient_id": self.test_patient_id, "age": 30, "gender": "male"})
        
        if response.status_code == 401:
            print("✅ Unauthorized access properly rejected for CHP CDSS")
        else:
            print(f"❌ Unexpected response for unauthorized CHP CDSS: {response.status_code}")
    
    def cleanup_test_data(self):
        """Clean up test data"""
        print("\n=== Cleaning up test data ===")
        try:
            if self.test_patient_user:
                self.test_patient_user.delete()
                print("✅ Test patient user deleted")
            
            if self.test_chp_user:
                self.test_chp_user.delete() 
                print("✅ Test CHP user deleted")
        except Exception as e:
            print(f"⚠️  Warning during cleanup: {e}")
    
    def run_all_tests(self):
        """Run all CDSS tests"""
        print("🏥 Starting CDSS Endpoint Testing")
        print("=" * 50)
        
        try:
            # Setup
            self.setup_test_data()
            
            # Authentication tests
            chp_auth_success = self.test_chp_authentication()
            patient_auth_success = self.test_patient_authentication()
            
            # Only proceed with endpoint tests if authentication is successful
            if chp_auth_success:
                chp_cdss_success = self.test_chp_cdss_endpoint()
            
            if patient_auth_success:
                general_cdss_success = self.test_general_cdss_endpoint()
                history_success = self.test_clinical_history_endpoint()
            
            # Security tests
            self.test_unauthorized_access()
            
            print("\n" + "=" * 50)
            print("🏥 CDSS Testing Summary")
            print("=" * 50)
            
            if chp_auth_success and chp_cdss_success:
                print("✅ CHP CDSS functionality: WORKING")
            else:
                print("❌ CHP CDSS functionality: FAILED")
            
            if patient_auth_success and general_cdss_success:
                print("✅ Patient CDSS functionality: WORKING")
            else:
                print("❌ Patient CDSS functionality: FAILED")
                
        except Exception as e:
            print(f"💥 Test execution failed: {e}")
        finally:
            self.cleanup_test_data()

if __name__ == "__main__":
    # Check if server is running
    try:
        response = requests.get('http://localhost:8000/api/', timeout=5)
        print("🚀 Server is running, starting tests...\n")
    except requests.exceptions.RequestException:
        print("❌ Server is not running on localhost:8000")
        print("Please start the Django development server with: python manage.py runserver")
        sys.exit(1)
    
    # Run tests
    tester = CDSSEndpointTester()
    tester.run_all_tests()