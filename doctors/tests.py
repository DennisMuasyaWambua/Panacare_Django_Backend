from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from users.models import User, Role
from doctors.models import Doctor, Education
import json

User = get_user_model()

@override_settings(ALLOWED_HOSTS=['*'])
class AdminAddDoctorTestCase(APITestCase):
    """Test cases for admin_add_doctor endpoint"""
    
    def setUp(self):
        """Set up test data"""
        # Create roles
        self.admin_role, _ = Role.objects.get_or_create(
            name='admin',
            defaults={'description': 'Administrator role'}
        )
        self.doctor_role, _ = Role.objects.get_or_create(
            name='doctor',
            defaults={'description': 'Doctor role'}
        )
        
        # Create admin user
        self.admin_user = User.objects.create_user(
            username='admin_test',
            email='admin@test.com',
            password='adminpass123',
            first_name='Admin',
            last_name='User',
            is_verified=True
        )
        self.admin_user.roles.add(self.admin_role)
        
        self.url = '/api/doctors/admin_add_doctor/'
        
        # Base test data for successful creation
        self.valid_doctor_data = {
            'username': 'test_doctor',
            'email': 'test_doctor@test.com',
            'password': 'doctorpass123',
            'first_name': 'John',
            'last_name': 'Doe',
            'specialty': 'Cardiology',
            'license_number': 'MD123456',
        }
    
    def test_successful_doctor_creation(self):
        """Test successful doctor creation with required fields"""
        self.client.force_authenticate(user=self.admin_user)
        
        response = self.client.post(self.url, self.valid_doctor_data, format='json')
        
        print(f"Response status: {response.status_code}")
        print(f"Response data: {response.data}")
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], 'success')
        
        # Verify doctor was created in database
        doctor_data = response.data['data']['doctor']
        doctor = Doctor.objects.get(id=doctor_data['id'])
        self.assertEqual(doctor.specialty, 'Cardiology')
        self.assertTrue(doctor.is_verified)
        
        print("✅ Test successful doctor creation PASSED")
    
    def test_missing_required_fields(self):
        """Test validation for missing required fields"""
        self.client.force_authenticate(user=self.admin_user)
        
        # Test with empty data
        response = self.client.post(self.url, {}, format='json')
        print(f"Empty data response: {response.status_code} - {response.data}")
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertIn('Missing required fields', response.data['error'])
        
        print("✅ Test missing required fields PASSED")
    
    def test_admin_permission_required(self):
        """Test that admin permission is required"""
        # Test without authentication
        response = self.client.post(self.url, self.valid_doctor_data, format='json')
        print(f"Unauthenticated response: {response.status_code}")
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        print("✅ Test admin permission required PASSED")
    
    def test_duplicate_email_prevention(self):
        """Test duplicate email prevention"""
        self.client.force_authenticate(user=self.admin_user)
        
        # Create first doctor
        response1 = self.client.post(self.url, self.valid_doctor_data, format='json')
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)
        print(f"First doctor created: {response1.data['data']['user']['email']}")
        
        # Try to create duplicate with same email
        duplicate_data = self.valid_doctor_data.copy()
        duplicate_data['username'] = 'different_username'
        
        response2 = self.client.post(self.url, duplicate_data, format='json')
        print(f"Duplicate email response: {response2.status_code} - {response2.data}")
        
        self.assertEqual(response2.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('already exists', response2.data['error'])
        
        print("✅ Test duplicate email prevention PASSED")
    
    def test_duplicate_username_prevention(self):
        """Test duplicate username prevention"""
        self.client.force_authenticate(user=self.admin_user)
        
        # First create a doctor with unique email
        first_data = self.valid_doctor_data.copy()
        first_data['email'] = 'first_doctor@test.com'
        response1 = self.client.post(self.url, first_data, format='json')
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)
        print(f"First doctor created: {response1.data['data']['user']['username']}")
        
        # Try to create duplicate with same username but different email
        duplicate_data = self.valid_doctor_data.copy()
        duplicate_data['email'] = 'different_doctor@test.com'
        
        response2 = self.client.post(self.url, duplicate_data, format='json')
        print(f"Duplicate username response: {response2.status_code} - {response2.data}")
        
        self.assertEqual(response2.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('already exists', response2.data['error'])
        
        print("✅ Test duplicate username prevention PASSED")
    
    def test_custom_education_data(self):
        """Test creating doctor with custom education data"""
        self.client.force_authenticate(user=self.admin_user)
        
        data_with_education = self.valid_doctor_data.copy()
        data_with_education.update({
            'email': 'doctor_with_education@test.com',
            'username': 'doctor_with_education',
            'education': {
                'level_of_education': 'Doctor of Medicine',
                'field': 'Cardiology',
                'institution': 'University of Nairobi',
                'start_date': '2015-01-01',
                'end_date': '2019-12-31'
            }
        })
        
        response = self.client.post(self.url, data_with_education, format='json')
        print(f"Custom education response: {response.status_code}")
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify education details
        education_details = response.data['data']['doctor']['education_details']
        self.assertEqual(education_details['level_of_education'], 'Doctor of Medicine')
        self.assertEqual(education_details['field'], 'Cardiology')
        self.assertEqual(education_details['institution'], 'University of Nairobi')
        
        print("✅ Test custom education data PASSED")
    
    def test_response_structure(self):
        """Test that response has correct structure and data"""
        self.client.force_authenticate(user=self.admin_user)
        
        test_data = self.valid_doctor_data.copy()
        test_data.update({
            'email': 'structure_test@test.com',
            'username': 'structure_test',
            'bio': 'Test biography',
            'facility_name': 'Test Hospital',
            'phone_number': '+254700123456',
            'address': 'Test Address, Nairobi'
        })
        
        response = self.client.post(self.url, test_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify response structure
        self.assertIn('status', response.data)
        self.assertIn('data', response.data)
        self.assertIn('message', response.data)
        self.assertEqual(response.data['status'], 'success')
        
        # Verify data structure
        data = response.data['data']
        self.assertIn('doctor', data)
        self.assertIn('user', data)
        
        # Verify doctor data
        doctor_data = data['doctor']
        required_doctor_fields = ['id', 'specialty', 'license_number', 'is_verified', 'is_available']
        for field in required_doctor_fields:
            self.assertIn(field, doctor_data)
        
        # Verify user data
        user_data = data['user']
        required_user_fields = ['id', 'email', 'first_name', 'last_name', 'is_verified', 'roles']
        for field in required_user_fields:
            self.assertIn(field, user_data)
        
        # Verify doctor is verified and available by default
        self.assertTrue(doctor_data['is_verified'])
        self.assertTrue(doctor_data['is_available'])
        self.assertTrue(user_data['is_verified'])
        
        # Verify role assignment
        self.assertTrue(any(role['name'] == 'doctor' for role in user_data['roles']))
        
        print("✅ Test response structure PASSED")
