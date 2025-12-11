#!/usr/bin/env python3
"""
Test script to verify Twilio API authentication and functionality
"""

import os
import sys
import django
from django.conf import settings

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath('.'))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'panacare.settings')
django.setup()

from healthcare.twilio_utils import get_twilio_client, create_twilio_room, generate_twilio_token
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_twilio_authentication():
    """Test Twilio API authentication"""
    try:
        logger.info("Testing Twilio authentication...")
        
        # Test 1: Check if credentials are configured
        logger.info("=== Checking Twilio Configuration ===")
        logger.info(f"TWILIO_ACCOUNT_SID: {'*' * 20 if settings.TWILIO_ACCOUNT_SID else 'NOT SET'}")
        logger.info(f"TWILIO_AUTH_TOKEN: {'*' * 20 if settings.TWILIO_AUTH_TOKEN else 'NOT SET'}")
        logger.info(f"TWILIO_API_KEY_SID: {'*' * 20 if settings.TWILIO_API_KEY_SID else 'NOT SET'}")
        logger.info(f"TWILIO_API_KEY_SECRET: {'*' * 20 if settings.TWILIO_API_KEY_SECRET else 'NOT SET'}")
        
        if not all([settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN, 
                   settings.TWILIO_API_KEY_SID, settings.TWILIO_API_KEY_SECRET]):
            logger.error("❌ Twilio credentials are not fully configured in settings!")
            return False
        
        # Test 2: Try to create a Twilio client
        logger.info("=== Testing Twilio Client Creation ===")
        client = get_twilio_client()
        logger.info("✅ Twilio client created successfully")
        
        # Test 3: Test API connectivity by fetching account info
        logger.info("=== Testing API Connectivity ===")
        account = client.api.accounts(settings.TWILIO_ACCOUNT_SID).fetch()
        logger.info(f"✅ Account fetched successfully: {account.friendly_name}")
        logger.info(f"Account Status: {account.status}")
        
        # Test 4: Test token generation
        logger.info("=== Testing Token Generation ===")
        test_identity = "test_user"
        test_room = "test_room"
        token = generate_twilio_token(test_identity, test_room)
        logger.info(f"✅ Token generated successfully for {test_identity} in room {test_room}")
        logger.info(f"Token length: {len(token)} characters")
        
        # Test 5: Test room creation
        logger.info("=== Testing Room Creation ===")
        room_name = f"test_room_{os.urandom(4).hex()}"
        room = create_twilio_room(room_name)
        logger.info(f"✅ Room created successfully: {room.unique_name}")
        logger.info(f"Room SID: {room.sid}")
        logger.info(f"Room Status: {room.status}")
        
        # Test 6: Close the test room
        logger.info("=== Testing Room Closure ===")
        from healthcare.twilio_utils import close_twilio_room
        closed_room = close_twilio_room(room.sid)
        logger.info(f"✅ Room closed successfully: {closed_room.status}")
        
        logger.info("\n🎉 All Twilio tests passed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Twilio authentication test failed: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        return False

def test_patient_doctor_login():
    """Test patient and doctor login with provided credentials"""
    try:
        logger.info("\n=== Testing Patient and Doctor Login ===")
        
        from users.models import User
        import requests
        
        # Use direct HTTP requests instead of Django test client
        base_url = "http://127.0.0.1:8000"
        
        # Test patient login
        patient_credentials = {
            "email": "s0p2biuogi@mrotzis.com",
            "password": "dennis@123"
        }
        
        logger.info("Testing patient login...")
        try:
            response = requests.post(f"{base_url}/api/users/login/", json=patient_credentials)
            logger.info(f"Patient login response status: {response.status_code}")
            
            if response.status_code == 200:
                patient_data = response.json()
                logger.info(f"✅ Patient login successful: {patient_data.get('user', {}).get('email')}")
                logger.info(f"Patient roles: {patient_data.get('roles', [])}")
                patient_token = patient_data.get('access')
            else:
                logger.error(f"❌ Patient login failed: {response.text}")
                patient_token = None
        except requests.exceptions.ConnectionError:
            logger.warning("⚠️  Django server not running. Skipping login test.")
            patient_token = None
        
        # Test doctor login
        doctor_credentials = {
            "email": "fivehe2125@nomrista.com",
            "password": "123123123"
        }
        
        logger.info("Testing doctor login...")
        try:
            response = requests.post(f"{base_url}/api/users/login/", json=doctor_credentials)
            logger.info(f"Doctor login response status: {response.status_code}")
            
            if response.status_code == 200:
                doctor_data = response.json()
                logger.info(f"✅ Doctor login successful: {doctor_data.get('user', {}).get('email')}")
                logger.info(f"Doctor roles: {doctor_data.get('roles', [])}")
                doctor_token = doctor_data.get('access')
            else:
                logger.error(f"❌ Doctor login failed: {response.text}")
                doctor_token = None
        except requests.exceptions.ConnectionError:
            logger.warning("⚠️  Django server not running. Skipping login test.")
            doctor_token = None
        
        return patient_token, doctor_token
        
    except Exception as e:
        logger.error(f"❌ Patient/Doctor login test failed: {str(e)}")
        return None, None

if __name__ == "__main__":
    print("🚀 Starting Twilio Authentication and User Login Tests...")
    
    # Test Twilio authentication
    twilio_success = test_twilio_authentication()
    
    # Test patient and doctor login
    patient_token, doctor_token = test_patient_doctor_login()
    
    print("\n📊 Test Summary:")
    print(f"Twilio Authentication: {'✅ PASSED' if twilio_success else '❌ FAILED'}")
    print(f"Patient Login: {'✅ PASSED' if patient_token else '❌ FAILED'}")
    print(f"Doctor Login: {'✅ PASSED' if doctor_token else '❌ FAILED'}")
    
    if twilio_success and patient_token and doctor_token:
        print("\n🎉 All tests passed! Ready to test consultation flow.")
    else:
        print("\n⚠️  Some tests failed. Check the logs above for details.")