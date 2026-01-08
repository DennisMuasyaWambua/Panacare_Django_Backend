#!/usr/bin/env python
"""
Test script for CHP-Patient assignment and messaging endpoints
"""
import os
import sys
import django
import requests
import json
from django.test import TestCase
from django.contrib.auth import get_user_model

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'panacare.settings')
sys.path.append('/home/dennis/Desktop/projects/Panacare_healthcare_Backend_Django')
django.setup()

from users.models import User, Role, Patient, CommunityHealthProvider, CHPPatientMessage

def test_models():
    """Test that our models are properly defined"""
    print("Testing CHP-Patient Message model...")
    
    # Test CHPPatientMessage fields
    fields = [field.name for field in CHPPatientMessage._meta.get_fields()]
    expected_fields = ['id', 'sender', 'recipient', 'patient', 'chp', 'message', 'is_read', 'created_at', 'updated_at']
    
    print(f"CHPPatientMessage fields: {fields}")
    
    for field in expected_fields:
        if field in fields:
            print(f"✓ {field} field exists")
        else:
            print(f"✗ {field} field missing")
    
    print("\nModel test completed!")

def test_endpoints_availability():
    """Test if our new endpoints are properly registered"""
    print("Testing endpoint registration...")
    
    from django.urls import reverse
    from django.urls.exceptions import NoReverseMatch
    
    endpoints = [
        'admin-assign-chp-patient',
        'chp-patient-messages', 
    ]
    
    for endpoint in endpoints:
        try:
            url = reverse(endpoint)
            print(f"✓ {endpoint}: {url}")
        except NoReverseMatch:
            print(f"✗ {endpoint}: Not found")
        except Exception as e:
            print(f"✗ {endpoint}: Error - {e}")

def test_serializers():
    """Test that our serializers are properly defined"""
    print("Testing serializers...")
    
    from users.serializers import CHPPatientMessageSerializer, CHPAssignmentSerializer
    
    # Test CHPPatientMessageSerializer
    try:
        serializer = CHPPatientMessageSerializer()
        fields = serializer.fields.keys()
        print(f"✓ CHPPatientMessageSerializer fields: {list(fields)}")
    except Exception as e:
        print(f"✗ CHPPatientMessageSerializer error: {e}")
    
    # Test CHPAssignmentSerializer
    try:
        serializer = CHPAssignmentSerializer()
        fields = serializer.fields.keys()
        print(f"✓ CHPAssignmentSerializer fields: {list(fields)}")
    except Exception as e:
        print(f"✗ CHPAssignmentSerializer error: {e}")

if __name__ == '__main__':
    print("=" * 50)
    print("CHP-Patient Assignment & Messaging Test")
    print("=" * 50)
    
    test_models()
    print("\n" + "-" * 30)
    test_endpoints_availability()
    print("\n" + "-" * 30)
    test_serializers()
    
    print("\n" + "=" * 50)
    print("Test completed!")
    print("=" * 50)