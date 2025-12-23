#!/usr/bin/env python3
"""
Test script for the admin_add_doctor endpoint
Tests various scenarios including success cases and validation errors
"""

import os
import sys
import django
import json
import requests
from datetime import datetime

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'panacare.settings')
sys.path.append('/home/dennis/Desktop/projects/Panacare_healthcare_Backend_Django')

try:
    django.setup()
except Exception as e:
    print(f"Django setup failed: {e}")
    sys.exit(1)

from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from users.models import User, Role
from doctors.models import Doctor, Education

User = get_user_model()

class AdminAddDoctorTest:
    def __init__(self):
        self.client = APIClient()
        self.test_results = []
        self.admin_user = None
        self.admin_token = None
        
    def setup_test_data(self):
        """Create admin user and get authentication token"""
        print("Setting up test data...")
        
        try:
            # Create admin role if it doesn't exist
            admin_role, created = Role.objects.get_or_create(
                name='admin',
                defaults={'description': 'Administrator role'}
            )
            print(f"Admin role {'created' if created else 'found'}")
            
            # Create doctor role if it doesn't exist  
            doctor_role, created = Role.objects.get_or_create(
                name='doctor',
                defaults={'description': 'Doctor role'}
            )
            print(f"Doctor role {'created' if created else 'found'}")
            
            # Create admin user
            admin_email = 'test_admin@test.com'
            admin_username = 'test_admin_user'
            
            # Clean up existing test user
            User.objects.filter(email=admin_email).delete()
            User.objects.filter(username=admin_username).delete()
            
            self.admin_user = User.objects.create_user(
                username=admin_username,
                email=admin_email,
                password='testpass123',
                first_name='Admin',
                last_name='User',
                is_verified=True
            )
            self.admin_user.roles.add(admin_role)
            print(f"Created admin user: {self.admin_user.email}")
            
            # Get authentication token
            from rest_framework_simplejwt.tokens import RefreshToken
            refresh = RefreshToken.for_user(self.admin_user)
            self.admin_token = str(refresh.access_token)
            
            # Set authentication header
            self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.admin_token}')
            
            return True
            
        except Exception as e:
            print(f"Setup failed: {e}")
            return False
    
    def cleanup_test_data(self):
        """Clean up test data"""
        print("\nCleaning up test data...")
        try:
            # Remove test users and related objects
            test_emails = [
                'test_admin@test.com',
                'test_doctor@test.com', 
                'test_doctor2@test.com',
                'test_doctor3@test.com'
            ]
            
            for email in test_emails:
                try:
                    user = User.objects.get(email=email)
                    if hasattr(user, 'doctor'):
                        user.doctor.delete()
                    user.delete()
                    print(f"Deleted user: {email}")
                except User.DoesNotExist:
                    pass
                    
        except Exception as e:
            print(f"Cleanup error: {e}")
    
    def test_successful_creation(self):
        """Test successful doctor creation with all required fields"""
        print("\n=== Test 1: Successful Doctor Creation ===")
        
        test_data = {
            'username': 'test_doctor',
            'email': 'test_doctor@test.com',
            'password': 'doctorpass123',
            'first_name': 'John',
            'last_name': 'Doe',
            'phone_number': '+254123456789',
            'address': '123 Medical Center, Nairobi',
            'specialty': 'Cardiology',
            'license_number': 'MD123456',
            'experience_years': 10,
            'bio': 'Experienced cardiologist with 10 years of practice',
            'communication_languages': 'en,sw',
            'accepts_referrals': True,
            'consultation_modes': 'audio,video',
            'facility_name': 'Nairobi Heart Center',
            'education': {
                'level_of_education': 'Doctor of Medicine',
                'field': 'Medicine',
                'institution': 'University of Nairobi',
                'start_date': '2010-01-01',
                'end_date': '2014-12-31'
            }
        }
        
        try:
            url = '/api/doctors/admin_add_doctor/'
            response = self.client.post(url, test_data, format='json')
            
            result = {
                'test': 'Successful Creation',
                'status_code': response.status_code,
                'expected': 201,
                'passed': response.status_code == 201,
                'response_data': response.data if hasattr(response, 'data') else None,
                'errors': None
            }
            
            if response.status_code == 201:
                # Verify data in response
                data = response.data.get('data', {})
                doctor_data = data.get('doctor', {})
                user_data = data.get('user', {})
                
                result['doctor_created'] = doctor_data.get('id') is not None
                result['user_created'] = user_data.get('id') is not None
                result['doctor_verified'] = doctor_data.get('is_verified', False)
                result['user_verified'] = user_data.get('is_verified', False)
                
                print(f"✅ Doctor created successfully")
                print(f"   Doctor ID: {doctor_data.get('id')}")
                print(f"   User ID: {user_data.get('id')}")
                print(f"   Doctor verified: {doctor_data.get('is_verified')}")
                
            else:
                result['errors'] = response.data
                print(f"❌ Failed with status {response.status_code}")
                print(f"   Error: {response.data}")
                
        except Exception as e:
            result = {
                'test': 'Successful Creation',
                'status_code': None,
                'expected': 201,
                'passed': False,
                'response_data': None,
                'errors': str(e)
            }
            print(f"❌ Exception: {e}")
            
        self.test_results.append(result)
        return result
    
    def test_missing_required_fields(self):
        """Test validation for missing required fields"""
        print("\n=== Test 2: Missing Required Fields ===")
        
        test_cases = [
            {'data': {}, 'missing': 'all fields'},
            {'data': {'username': 'test'}, 'missing': 'email, password, etc.'},
            {'data': {'username': 'test', 'email': 'test@test.com'}, 'missing': 'password, names, etc.'},
            {'data': {
                'username': 'test_doctor2',
                'email': 'test_doctor2@test.com', 
                'password': 'pass123',
                'first_name': 'Jane'
            }, 'missing': 'last_name, specialty, license_number'}
        ]
        
        results = []
        
        for i, case in enumerate(test_cases):
            print(f"\nTesting case {i+1}: {case['missing']}")
            
            try:
                url = '/api/doctors/admin_add_doctor/'
                response = self.client.post(url, case['data'], format='json')
                
                result = {
                    'test': f'Missing Fields Case {i+1}',
                    'missing_fields': case['missing'],
                    'status_code': response.status_code,
                    'expected': 400,
                    'passed': response.status_code == 400,
                    'response_data': response.data if hasattr(response, 'data') else None
                }
                
                if response.status_code == 400:
                    print(f"✅ Correctly rejected with 400")
                    print(f"   Error: {response.data.get('error', 'No error message')}")
                else:
                    print(f"❌ Expected 400, got {response.status_code}")
                    
                results.append(result)
                
            except Exception as e:
                result = {
                    'test': f'Missing Fields Case {i+1}',
                    'missing_fields': case['missing'],
                    'status_code': None,
                    'expected': 400,
                    'passed': False,
                    'response_data': None,
                    'errors': str(e)
                }
                print(f"❌ Exception: {e}")
                results.append(result)
        
        self.test_results.extend(results)
        return results
    
    def test_duplicate_user(self):
        """Test duplicate email/username prevention"""
        print("\n=== Test 3: Duplicate User Prevention ===")
        
        # First create a doctor
        first_doctor_data = {
            'username': 'test_doctor3',
            'email': 'test_doctor3@test.com',
            'password': 'doctorpass123',
            'first_name': 'Alice',
            'last_name': 'Smith',
            'specialty': 'Pediatrics',
            'license_number': 'MD789012'
        }
        
        url = '/api/doctors/admin_add_doctor/'
        
        try:
            # Create first doctor
            response1 = self.client.post(url, first_doctor_data, format='json')
            
            if response1.status_code != 201:
                print(f"❌ Failed to create first doctor: {response1.data}")
                return
                
            print("✅ First doctor created successfully")
            
            # Try to create duplicate with same email
            duplicate_email_data = first_doctor_data.copy()
            duplicate_email_data['username'] = 'different_username'
            
            response2 = self.client.post(url, duplicate_email_data, format='json')
            
            result_email = {
                'test': 'Duplicate Email Prevention',
                'status_code': response2.status_code,
                'expected': 400,
                'passed': response2.status_code == 400,
                'response_data': response2.data if hasattr(response2, 'data') else None
            }
            
            if response2.status_code == 400:
                print("✅ Correctly rejected duplicate email")
                print(f"   Error: {response2.data.get('error', 'No error message')}")
            else:
                print(f"❌ Expected 400 for duplicate email, got {response2.status_code}")
            
            # Try to create duplicate with same username  
            duplicate_username_data = first_doctor_data.copy()
            duplicate_username_data['email'] = 'different@email.com'
            
            response3 = self.client.post(url, duplicate_username_data, format='json')
            
            result_username = {
                'test': 'Duplicate Username Prevention',
                'status_code': response3.status_code,
                'expected': 400,
                'passed': response3.status_code == 400,
                'response_data': response3.data if hasattr(response3, 'data') else None
            }
            
            if response3.status_code == 400:
                print("✅ Correctly rejected duplicate username")
                print(f"   Error: {response3.data.get('error', 'No error message')}")
            else:
                print(f"❌ Expected 400 for duplicate username, got {response3.status_code}")
                
            self.test_results.extend([result_email, result_username])
            
        except Exception as e:
            result = {
                'test': 'Duplicate Prevention',
                'status_code': None,
                'expected': 400,
                'passed': False,
                'errors': str(e)
            }
            print(f"❌ Exception: {e}")
            self.test_results.append(result)
    
    def test_authentication_required(self):
        """Test that admin authentication is required"""
        print("\n=== Test 4: Authentication Required ===")
        
        # Remove authentication
        self.client.credentials()
        
        test_data = {
            'username': 'test_doctor_unauth',
            'email': 'test_doctor_unauth@test.com',
            'password': 'doctorpass123',
            'first_name': 'Unauthorized',
            'last_name': 'Doctor',
            'specialty': 'General Practice',
            'license_number': 'MD999999'
        }
        
        try:
            url = '/api/doctors/admin_add_doctor/'
            response = self.client.post(url, test_data, format='json')
            
            result = {
                'test': 'Authentication Required',
                'status_code': response.status_code,
                'expected': 401,
                'passed': response.status_code == 401,
                'response_data': response.data if hasattr(response, 'data') else None
            }
            
            if response.status_code == 401:
                print("✅ Correctly rejected unauthenticated request")
            else:
                print(f"❌ Expected 401, got {response.status_code}")
                
            # Restore authentication for remaining tests
            self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.admin_token}')
            
            self.test_results.append(result)
            
        except Exception as e:
            result = {
                'test': 'Authentication Required',
                'status_code': None,
                'expected': 401,
                'passed': False,
                'errors': str(e)
            }
            print(f"❌ Exception: {e}")
            self.test_results.append(result)
    
    def generate_report(self):
        """Generate comprehensive test report"""
        print("\n" + "="*60)
        print("ADMIN ADD DOCTOR ENDPOINT TEST REPORT")
        print("="*60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result.get('passed', False))
        
        print(f"\nOVERALL RESULTS:")
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%")
        
        print(f"\nDETAILED RESULTS:")
        for i, result in enumerate(self.test_results, 1):
            status = "✅ PASS" if result.get('passed', False) else "❌ FAIL"
            print(f"\n{i}. {result.get('test', 'Unknown Test')} - {status}")
            print(f"   Status Code: {result.get('status_code', 'N/A')} (Expected: {result.get('expected', 'N/A')})")
            
            if result.get('errors'):
                print(f"   Errors: {result['errors']}")
            
            if not result.get('passed', False) and result.get('response_data'):
                print(f"   Response: {json.dumps(result['response_data'], indent=2)[:200]}...")
        
        print(f"\nEMNDPOINT FUNCTIONALITY ASSESSMENT:")
        
        # Check key functionality
        creation_test = next((r for r in self.test_results if 'Successful Creation' in r.get('test', '')), None)
        validation_tests = [r for r in self.test_results if 'Missing Fields' in r.get('test', '')]
        duplicate_tests = [r for r in self.test_results if 'Duplicate' in r.get('test', '')]
        auth_test = next((r for r in self.test_results if 'Authentication' in r.get('test', '')), None)
        
        print(f"✅ Doctor Creation: {'Working' if creation_test and creation_test.get('passed') else 'Failed'}")
        print(f"✅ Input Validation: {'Working' if all(t.get('passed', False) for t in validation_tests) else 'Failed'}")
        print(f"✅ Duplicate Prevention: {'Working' if all(t.get('passed', False) for t in duplicate_tests) else 'Failed'}")
        print(f"✅ Authentication: {'Working' if auth_test and auth_test.get('passed') else 'Failed'}")
        
        print(f"\nRECOMMENDATIONS:")
        if passed_tests == total_tests:
            print("🎉 All tests passed! The endpoint is working correctly.")
        else:
            print("⚠️  Some tests failed. Review the failed tests and fix issues.")
            
        print(f"\nTEST COMPLETED AT: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60)

    def run_all_tests(self):
        """Run all tests and generate report"""
        print("Starting Admin Add Doctor Endpoint Tests...")
        
        if not self.setup_test_data():
            print("Failed to setup test data. Exiting.")
            return
            
        try:
            # Run all test methods
            self.test_successful_creation()
            self.test_missing_required_fields()
            self.test_duplicate_user()
            self.test_authentication_required()
            
            # Generate final report
            self.generate_report()
            
        finally:
            self.cleanup_test_data()

if __name__ == '__main__':
    tester = AdminAddDoctorTest()
    tester.run_all_tests()