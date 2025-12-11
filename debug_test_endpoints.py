import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'panacare.settings')
django.setup()

import logging
from django.test import Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('django.db.backends')
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
logger.addHandler(handler)

# Get models
User = get_user_model()
from doctors.models import Doctor
from users.models import Patient

# Test creating a test patient
try:
    # Create a test user
    test_user = User.objects.create(
        username="testpatient",
        email="testpatient@example.com",
        is_verified=True
    )
    test_user.set_password("password123")
    test_user.save()
    
    # Create a test patient
    test_patient = Patient.objects.create(
        user=test_user,
        gender="male",
        active=True,
        blood_type="A+",
        allergies="None",
        medical_conditions="None",
        medications="None",
        emergency_contact_name="",
        emergency_contact_phone="",
        emergency_contact_relationship="",
        identifier_system="urn:test:patient",
        marital_status="S",
        language="en",
        insurance_provider="",
        insurance_policy_number="",
        insurance_group_number=""
    )
    print(f"Created test patient with ID: {test_patient.id}")
except Exception as e:
    print(f"Error creating test patient: {str(e)}")

# Get existing doctor ID
doctor_id = None
try:
    doctor = Doctor.objects.first()
    if doctor:
        doctor_id = doctor.id
        print(f"Found doctor with ID: {doctor_id}")
    else:
        print("No doctors found in database")
except Exception as e:
    print(f"Error getting doctor: {str(e)}")

# Create a client
client = Client()

# Get a valid token
try:
    admin_user = User.objects.filter(is_staff=True).first()
    if admin_user:
        refresh = RefreshToken.for_user(admin_user)
        token = str(refresh.access_token)
        print(f"Got token for admin user: {admin_user.username}")
    else:
        print("No admin user found")
except Exception as e:
    print(f"Error getting token: {str(e)}")

# Test endpoints
if 'test_patient' in locals() and test_patient:
    print("\nTesting GET /api/patients/{id}/")
    try:
        client.defaults['HTTP_AUTHORIZATION'] = f'Bearer {token}'
        response = client.get(f'/api/patients/{test_patient.id}/')
        print(f"Status code: {response.status_code}")
        if response.status_code != 200:
            print(f"Error: {response.content.decode()}")
    except Exception as e:
        print(f"Error testing patient endpoint: {str(e)}")

if doctor_id:
    print("\nTesting GET /api/doctors/{id}/")
    try:
        client.defaults['HTTP_AUTHORIZATION'] = f'Bearer {token}'
        response = client.get(f'/api/doctors/{doctor_id}/')
        print(f"Status code: {response.status_code}")
        if response.status_code != 200:
            print(f"Error: {response.content.decode()}")
    except Exception as e:
        print(f"Error testing doctor endpoint: {str(e)}")