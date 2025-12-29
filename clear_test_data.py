#!/usr/bin/env python3

import os
import sys
import django

# Setup Django
sys.path.append('/home/dennis/Desktop/projects/Panacare_healthcare_Backend_Django')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'panacare.settings')
django.setup()

from django.contrib.auth import get_user_model
from users.models import Patient

User = get_user_model()

def clear_test_data():
    print("Clearing test data...")
    
    # Clear test patients and users
    test_patients = Patient.objects.filter(user__email__contains='example.com')
    test_users = User.objects.filter(email__contains='example.com').exclude(email='testchp@example.com')
    
    print(f"Found {test_patients.count()} test patients")
    print(f"Found {test_users.count()} test users")
    
    # Delete patients first (due to foreign key constraints)
    for patient in test_patients:
        print(f"Deleting patient: {patient.user.email}")
        patient.delete()
    
    # Then delete users
    for user in test_users:
        print(f"Deleting user: {user.email}")
        user.delete()
    
    print("Test data cleared!")

if __name__ == "__main__":
    clear_test_data()