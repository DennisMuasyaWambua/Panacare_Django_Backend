#!/usr/bin/env python3
"""
Simple test script for CDSS endpoints using Django's test client
"""

import os
import sys
import django

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'panacare.settings')
django.setup()

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from users.models import Role, Patient, CommunityHealthProvider
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken
import json
from datetime import datetime

User = get_user_model()

class CDSSTestRunner:
    def __init__(self):
        self.client = APIClient()
        
    def create_test_users(self):
        """Create test users for CHP and Patient"""
        print("Creating test users...")
        
        # Create roles
        chp_role, _ = Role.objects.get_or_create(name='community_health_provider')
        patient_role, _ = Role.objects.get_or_create(name='patient')
        
        # Create CHP user
        timestamp = int(datetime.now().timestamp())
        self.chp_user = User.objects.create_user(
            username=f'test_chp_{timestamp}',
            email=f'chp_{timestamp}@test.com',
            password='testpass123',
            first_name='Test',
            last_name='CHP',
            is_verified=True
        )
        self.chp_user.roles.add(chp_role)
        
        # Create CHP profile
        self.chp_profile = CommunityHealthProvider.objects.create(
            user=self.chp_user,
            certification_number=f'CHP-{timestamp}',
            years_of_experience=3,
            specialization='Community Health'
        )
        
        # Create Patient user  
        self.patient_user = User.objects.create_user(
            username=f'test_patient_{timestamp}',
            email=f'patient_{timestamp}@test.com',
            password='testpass123',
            first_name='Test',
            last_name='Patient',
            is_verified=True
        )
        self.patient_user.roles.add(patient_role)
        
        # Create Patient profile
        self.patient_profile = Patient.objects.create(
            user=self.patient_user,
            date_of_birth='1985-05-15',
            gender='male',
            height_cm=175,
            weight_kg=80,
            created_by_chp=self.chp_profile
        )
        
        print(f"✅ Created CHP: {self.chp_user.email}")
        print(f"✅ Created Patient: {self.patient_user.email}")
        
    def test_general_cdss(self):
        """Test general CDSS endpoint for patients"""
        print("\n=== Testing General CDSS Endpoint ===")
        
        # Authenticate as patient
        token = AccessToken.for_user(self.patient_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        # Test data
        test_data = {
            "age": 38,
            "gender": "male",
            "weight": 80,
            "height": 175,
            "high_blood_pressure": True,
            "diabetes": False,
            "on_medication": True,
            "headache": True,
            "dizziness": False,
            "palpitations": True,
            "fatigue": True,
            "chest_pain": False,
            "systolic_pressure": 140,
            "diastolic_pressure": 90,
            "blood_sugar": 100,
            "heart_rate": 85,
            "sleep_hours": 7,
            "exercise_minutes": 30,
            "eats_unhealthy": False,
            "smokes": False,
            "consumes_alcohol": False,
            "skips_medication": False
        }
        
        response = self.client.post('/api/clinical-decision/', test_data, format='json')
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ General CDSS endpoint successful")
            print(f"Risk Level: {data.get('risk_level', 'N/A')}")
            print(f"Blood Pressure Status: {data.get('blood_pressure_status', 'N/A')}")
            print(f"Blood Sugar Status: {data.get('blood_sugar_status', 'N/A')}")
            print(f"Recommendations Count: {len(data.get('recommendations', []))}")
            
            # Show first recommendation
            recommendations = data.get('recommendations', [])
            if recommendations:
                print(f"First Recommendation: {recommendations[0]}")
                
            return True
        else:
            print(f"❌ Failed: {response.content.decode()}")
            return False
            
    def test_chp_cdss(self):
        """Test CHP CDSS endpoint"""
        print("\n=== Testing CHP CDSS Endpoint ===")
        
        # Authenticate as CHP
        token = AccessToken.for_user(self.chp_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        # Test data for CHP CDSS (includes patient_id)
        test_data = {
            "patient_id": str(self.patient_profile.id),
            "age": 38,
            "gender": "male",
            "weight": 82,
            "height": 175,
            "high_blood_pressure": True,
            "diabetes": False,
            "on_medication": True,
            "headache": True,
            "dizziness": True,
            "palpitations": True,
            "fatigue": True,
            "chest_pain": False,
            "systolic_bp": 145,  # Note different field name
            "diastolic_bp": 95,
            "blood_sugar": 110,
            "heart_rate": 88,
            "sleep_hours": 6,
            "exercise_minutes": 20,
            "eats_unhealthy": True,
            "smokes": False,
            "consumes_alcohol": True,
            "skips_medication": False
        }
        
        response = self.client.post('/api/chp/cdss/', test_data, format='json')
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ CHP CDSS endpoint successful")
            print(f"Analysis ID: {data.get('id', 'N/A')}")
            print(f"Risk Level: {data.get('risk_level', 'N/A')}")
            print(f"BMI: {data.get('bmi', 'N/A')}")
            print(f"BMI Category: {data.get('bmi_category', 'N/A')}")
            print(f"Blood Pressure Status: {data.get('blood_pressure_status', 'N/A')}")
            print(f"Blood Sugar Status: {data.get('blood_sugar_status', 'N/A')}")
            print(f"Heart Rate Status: {data.get('heart_rate_status', 'N/A')}")
            print(f"CHP Name: {data.get('chp_name', 'N/A')}")
            print(f"Patient Name: {data.get('patient_name', 'N/A')}")
            
            recommendations = data.get('recommendations', [])
            print(f"Recommendations Count: {len(recommendations)}")
            
            if recommendations:
                print("Sample recommendations:")
                for i, rec in enumerate(recommendations[:3]):
                    print(f"  {i+1}. {rec}")
                    
            return True
        else:
            print(f"❌ Failed: {response.content.decode()}")
            return False
            
    def test_clinical_history(self):
        """Test clinical history endpoint"""
        print("\n=== Testing Clinical History Endpoint ===")
        
        # Authenticate as patient
        token = AccessToken.for_user(self.patient_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        response = self.client.get('/api/clinical-history/')
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Clinical history endpoint successful")
            print(f"Total Records: {len(data)}")
            
            if data:
                latest = data[0]
                print(f"Latest Record: {latest.get('created_at', 'N/A')}")
                print(f"Latest Risk Level: {latest.get('risk_level', 'N/A')}")
                
            return True
        else:
            print(f"❌ Failed: {response.content.decode()}")
            return False
            
    def test_unauthorized_access(self):
        """Test unauthorized access"""
        print("\n=== Testing Unauthorized Access ===")
        
        # Clear credentials
        self.client.credentials()
        
        # Test general CDSS without auth
        response = self.client.post('/api/clinical-decision/', {"age": 30}, format='json')
        if response.status_code == 401:
            print("✅ General CDSS properly requires authentication")
        else:
            print(f"❌ Unexpected response: {response.status_code}")
            
        # Test CHP CDSS without auth
        response = self.client.post('/api/chp/cdss/', {"patient_id": str(self.patient_profile.id)}, format='json')
        if response.status_code == 401:
            print("✅ CHP CDSS properly requires authentication")
        else:
            print(f"❌ Unexpected response: {response.status_code}")
            
    def cleanup(self):
        """Clean up test data"""
        print("\n=== Cleanup ===")
        try:
            if hasattr(self, 'patient_user'):
                self.patient_user.delete()
                print("✅ Patient user deleted")
                
            if hasattr(self, 'chp_user'):
                self.chp_user.delete()
                print("✅ CHP user deleted")
        except Exception as e:
            print(f"⚠️ Cleanup warning: {e}")
            
    def run_all_tests(self):
        """Run all CDSS tests"""
        print("🏥 CDSS Endpoint Testing")
        print("=" * 50)
        
        try:
            # Setup
            self.create_test_users()
            
            # Run tests
            general_success = self.test_general_cdss()
            chp_success = self.test_chp_cdss()
            history_success = self.test_clinical_history()
            self.test_unauthorized_access()
            
            # Summary
            print("\n" + "=" * 50)
            print("🏥 Test Summary")
            print("=" * 50)
            
            if general_success:
                print("✅ General CDSS: WORKING")
            else:
                print("❌ General CDSS: FAILED")
                
            if chp_success:
                print("✅ CHP CDSS: WORKING")
            else:
                print("❌ CHP CDSS: FAILED")
                
            if history_success:
                print("✅ Clinical History: WORKING")
            else:
                print("❌ Clinical History: FAILED")
                
        except Exception as e:
            print(f"💥 Test failed: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.cleanup()

if __name__ == "__main__":
    runner = CDSSTestRunner()
    runner.run_all_tests()