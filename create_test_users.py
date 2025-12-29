#!/usr/bin/env python3

import os
import sys
import django

# Setup Django
sys.path.append('/home/dennis/Desktop/projects/Panacare_healthcare_Backend_Django')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'panacare.settings')
django.setup()

from django.contrib.auth import get_user_model
from users.models import CommunityHealthProvider, Role
from doctors.models import Doctor

User = get_user_model()

def create_test_users():
    print("Creating test users...")
    
    # Create CHP role if it doesn't exist
    chp_role, created = Role.objects.get_or_create(
        name='community_health_provider',
        defaults={'description': 'Community health provider role for testing'}
    )
    print(f"CHP Role: {chp_role} (created: {created})")

    # Create test CHP user
    try:
        user = User.objects.create_user(
            username='testchp',
            email='testchp@example.com',
            password='testpass123',
            first_name='Test',
            last_name='CHP',
            is_verified=True
        )
        user.roles.add(chp_role)
        
        # Create CHP profile
        chp = CommunityHealthProvider.objects.create(
            user=user,
            certification_number='TEST123',
            specialization='General Practice',
            service_area='Test Area'
        )
        print(f"Created CHP user: {user.email} with CHP profile: {chp.id}")
    except Exception as e:
        try:
            user = User.objects.get(email='testchp@example.com')
            user.is_verified = True
            user.save()
            print(f"CHP user already exists: {user.email} (verified)")
        except Exception as e2:
            print(f"Error with CHP user: {e}")
        
    # Create a test doctor
    try:
        doctor_user = User.objects.create_user(
            username='testdoctor',
            email='testdoctor@example.com',
            password='testpass123',
            first_name='Test',
            last_name='Doctor'
        )
        
        doctor = Doctor.objects.create(
            user=doctor_user,
            license_number='DOC123',
            specialty='General Medicine',
            is_verified=True,
            is_available=True
        )
        print(f"Created doctor: {doctor_user.email} with doctor profile: {doctor.id}")
    except Exception as e:
        print(f"Doctor might already exist: {e}")

if __name__ == "__main__":
    create_test_users()