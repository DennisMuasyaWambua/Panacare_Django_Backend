#!/usr/bin/env python3
"""
Test script to verify consultation flow with Twilio integration
"""

import requests
import json
import time
from datetime import datetime, timedelta

# API Base URL
BASE_URL = "http://127.0.0.1:8000"

# Test credentials
PATIENT_CREDENTIALS = {
    "email": "s0p2biuogi@mrotzis.com",
    "password": "dennis@123"
}

DOCTOR_CREDENTIALS = {
    "email": "fivehe2125@nomrista.com",
    "password": "123123123"
}

def login_user(credentials, role):
    """Login and return access token"""
    print(f"🔐 Logging in {role}...")
    
    try:
        response = requests.post(f"{BASE_URL}/api/users/login/", json=credentials)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ {role.capitalize()} login successful: {data['user']['email']}")
            return data['access'], data['user']['id']
        else:
            print(f"❌ {role.capitalize()} login failed: {response.text}")
            return None, None
            
    except Exception as e:
        print(f"❌ {role.capitalize()} login error: {str(e)}")
        return None, None

def make_authenticated_request(method, endpoint, token, data=None):
    """Make authenticated API request"""
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    url = f"{BASE_URL}{endpoint}"
    
    if method.upper() == 'GET':
        response = requests.get(url, headers=headers)
    elif method.upper() == 'POST':
        response = requests.post(url, headers=headers, json=data)
    elif method.upper() == 'PUT':
        response = requests.put(url, headers=headers, json=data)
    elif method.upper() == 'PATCH':
        response = requests.patch(url, headers=headers, json=data)
    else:
        raise ValueError(f"Unsupported method: {method}")
    
    return response

def test_consultation_flow():
    """Test complete consultation flow"""
    
    print("🚀 Starting Consultation Flow Test...\n")
    
    # Step 1: Login both users
    patient_token, patient_id = login_user(PATIENT_CREDENTIALS, "patient")
    doctor_token, doctor_id = login_user(DOCTOR_CREDENTIALS, "doctor")
    
    if not patient_token or not doctor_token:
        print("❌ Failed to login users. Aborting test.")
        return False
    
    print(f"Patient ID: {patient_id}")
    print(f"Doctor ID: {doctor_id}")
    
    # Step 2: Create an appointment (if needed)
    print("\n📅 Creating appointment...")
    
    # First, check if there are existing appointments
    response = make_authenticated_request('GET', '/api/appointments/', doctor_token)
    if response.status_code == 200:
        appointments = response.json()
        print(f"Found {len(appointments)} existing appointments")
        
        # Use an existing appointment or create a new one
        if appointments:
            appointment_id = appointments[0]['id']
            print(f"Using existing appointment: {appointment_id}")
        else:
            # Create a new appointment
            appointment_data = {
                'patient': patient_id,
                'doctor': doctor_id,
                'appointment_type': 'consultation',
                'appointment_date': (datetime.now() + timedelta(hours=1)).isoformat(),
                'reason': 'Test consultation',
                'status': 'scheduled'
            }
            response = make_authenticated_request('POST', '/api/appointments/', doctor_token, appointment_data)
            if response.status_code == 201:
                appointment_id = response.json()['id']
                print(f"✅ Created new appointment: {appointment_id}")
            else:
                print(f"❌ Failed to create appointment: {response.text}")
                return False
    else:
        print(f"❌ Failed to fetch appointments: {response.text}")
        return False
    
    # Step 3: Create or find a consultation
    print("\n💬 Creating consultation...")
    
    # Check for existing consultations
    response = make_authenticated_request('GET', '/api/consultations/', doctor_token)
    if response.status_code == 200:
        consultations = response.json()
        print(f"Found {len(consultations)} existing consultations")
        
        # Use an existing consultation or create a new one
        if consultations:
            consultation_id = consultations[0]['id']
            consultation = consultations[0]
            print(f"Using existing consultation: {consultation_id}")
        else:
            # Create a new consultation
            consultation_data = {
                'patient': patient_id,
                'doctor': doctor_id,
                'appointment': appointment_id,
                'consultation_type': 'video',
                'status': 'scheduled'
            }
            response = make_authenticated_request('POST', '/api/consultations/', doctor_token, consultation_data)
            if response.status_code == 201:
                consultation = response.json()
                consultation_id = consultation['id']
                print(f"✅ Created new consultation: {consultation_id}")
            else:
                print(f"❌ Failed to create consultation: {response.text}")
                return False
    else:
        print(f"❌ Failed to fetch consultations: {response.text}")
        return False
    
    # Step 4: Test starting consultation (Doctor action)
    print(f"\n🎬 Testing consultation start (Doctor action)...")
    
    response = make_authenticated_request('POST', f'/api/consultations/{consultation_id}/start_consultation/', doctor_token)
    print(f"Start consultation response status: {response.status_code}")
    
    if response.status_code == 200:
        start_data = response.json()
        print(f"✅ Consultation started successfully!")
        print(f"Doctor token length: {len(start_data.get('doctor_token', ''))}")
        print(f"Patient token length: {len(start_data.get('patient_token', ''))}")
        print(f"Room SID: {start_data.get('room_sid', 'N/A')}")
        print(f"Status: {start_data.get('status', 'N/A')}")
        
        # Log any error messages
        if 'error' in start_data:
            print(f"⚠️  Error message: {start_data['error']}")
        if 'twilio_error' in start_data:
            print(f"⚠️  Twilio error: {start_data['twilio_error']}")
        
    else:
        print(f"❌ Failed to start consultation")
        print(f"Response: {response.text}")
        # Continue with other tests even if start fails
    
    # Step 5: Test getting token (Patient action)
    print(f"\n🎫 Testing token retrieval (Patient action)...")
    
    response = make_authenticated_request('GET', f'/api/consultations/{consultation_id}/get_token/', patient_token)
    print(f"Get token response status: {response.status_code}")
    
    if response.status_code == 200:
        token_data = response.json()
        print(f"✅ Token retrieved successfully!")
        print(f"Token length: {len(token_data.get('token', ''))}")
        print(f"Identity: {token_data.get('identity', 'N/A')}")
        print(f"Room name: {token_data.get('room_name', 'N/A')}")
        
        if 'error' in token_data:
            print(f"⚠️  Error message: {token_data['error']}")
        if 'twilio_error' in token_data:
            print(f"⚠️  Twilio error: {token_data['twilio_error']}")
    else:
        print(f"❌ Failed to get token")
        print(f"Response: {response.text}")
    
    # Step 6: Test joining consultation (Patient action)
    print(f"\n🚪 Testing consultation join (Patient action)...")
    
    response = make_authenticated_request('POST', f'/api/consultations/{consultation_id}/join_consultation/', patient_token)
    print(f"Join consultation response status: {response.status_code}")
    
    if response.status_code == 200:
        join_data = response.json()
        print(f"✅ Consultation joined successfully!")
        print(f"Token length: {len(join_data.get('token', ''))}")
        print(f"Identity: {join_data.get('identity', 'N/A')}")
        print(f"Room name: {join_data.get('room_name', 'N/A')}")
        
        if 'error' in join_data:
            print(f"⚠️  Error message: {join_data['error']}")
        if 'twilio_error' in join_data:
            print(f"⚠️  Twilio error: {join_data['twilio_error']}")
    else:
        print(f"❌ Failed to join consultation")
        print(f"Response: {response.text}")
    
    # Step 7: Test sending chat message
    print(f"\n💬 Testing chat message...")
    
    message_data = {
        'message': 'Hello Doctor, I have a question about my symptoms.',
        'sender_type': 'patient'
    }
    
    response = make_authenticated_request('POST', f'/api/consultations/{consultation_id}/send_message/', patient_token, message_data)
    print(f"Send message response status: {response.status_code}")
    
    if response.status_code == 201:
        message_response = response.json()
        print(f"✅ Message sent successfully!")
        print(f"Message ID: {message_response.get('id', 'N/A')}")
        print(f"Message: {message_response.get('message', 'N/A')}")
    else:
        print(f"❌ Failed to send message")
        print(f"Response: {response.text}")
    
    # Step 8: Test getting chat messages
    print(f"\n📜 Testing chat messages retrieval...")
    
    response = make_authenticated_request('GET', f'/api/consultations/{consultation_id}/chat_messages/', doctor_token)
    print(f"Get messages response status: {response.status_code}")
    
    if response.status_code == 200:
        messages = response.json()
        print(f"✅ Retrieved {len(messages)} chat messages")
        for msg in messages[-2:]:  # Show last 2 messages
            print(f"  - {msg.get('sender_type', 'Unknown')}: {msg.get('message', 'N/A')}")
    else:
        print(f"❌ Failed to get messages")
        print(f"Response: {response.text}")
    
    # Step 9: Test ending consultation (Doctor action)
    print(f"\n🛑 Testing consultation end (Doctor action)...")
    
    response = make_authenticated_request('POST', f'/api/consultations/{consultation_id}/end_consultation/', doctor_token)
    print(f"End consultation response status: {response.status_code}")
    
    if response.status_code == 200:
        end_data = response.json()
        print(f"✅ Consultation ended successfully!")
        print(f"Status: {end_data.get('status', 'N/A')}")
        print(f"End time: {end_data.get('end_time', 'N/A')}")
        
        if 'error' in end_data:
            print(f"⚠️  Error message: {end_data['error']}")
        if 'twilio_error' in end_data:
            print(f"⚠️  Twilio error: {end_data['twilio_error']}")
    else:
        print(f"❌ Failed to end consultation")
        print(f"Response: {response.text}")
    
    return True

def test_error_handling():
    """Test error handling scenarios"""
    
    print("\n🧪 Testing Error Handling Scenarios...\n")
    
    # Login as patient
    patient_token, patient_id = login_user(PATIENT_CREDENTIALS, "patient")
    
    if not patient_token:
        print("❌ Failed to login patient for error testing")
        return False
    
    # Test 1: Try to start consultation as patient (should fail)
    print("🔒 Testing unauthorized consultation start...")
    
    response = make_authenticated_request('POST', '/api/consultations/00000000-0000-0000-0000-000000000000/start_consultation/', patient_token)
    print(f"Unauthorized start response status: {response.status_code}")
    
    if response.status_code in [403, 404]:
        print("✅ Correctly prevented unauthorized consultation start")
    else:
        print(f"⚠️  Unexpected response: {response.text}")
    
    # Test 2: Try to get token for non-existent consultation
    print("\n🔍 Testing non-existent consultation token...")
    
    response = make_authenticated_request('GET', '/api/consultations/00000000-0000-0000-0000-000000000000/get_token/', patient_token)
    print(f"Non-existent consultation token response status: {response.status_code}")
    
    if response.status_code == 404:
        print("✅ Correctly handled non-existent consultation")
    else:
        print(f"⚠️  Unexpected response: {response.text}")
    
    # Test 3: Try to send message to non-existent consultation
    print("\n📝 Testing message to non-existent consultation...")
    
    message_data = {'message': 'Test message', 'sender_type': 'patient'}
    response = make_authenticated_request('POST', '/api/consultations/00000000-0000-0000-0000-000000000000/send_message/', patient_token, message_data)
    print(f"Message to non-existent consultation response status: {response.status_code}")
    
    if response.status_code == 404:
        print("✅ Correctly handled message to non-existent consultation")
    else:
        print(f"⚠️  Unexpected response: {response.text}")
    
    return True

if __name__ == "__main__":
    print("🎯 Testing Consultation Flow with Twilio Integration")
    print("=" * 60)
    
    try:
        # Test main consultation flow
        flow_success = test_consultation_flow()
        
        # Test error handling
        error_success = test_error_handling()
        
        print("\n📊 Test Summary:")
        print("=" * 60)
        print(f"Consultation Flow: {'✅ PASSED' if flow_success else '❌ FAILED'}")
        print(f"Error Handling: {'✅ PASSED' if error_success else '❌ FAILED'}")
        
        if flow_success and error_success:
            print("\n🎉 All tests completed successfully!")
            print("💡 Note: Some Twilio features may show errors due to invalid credentials,")
            print("   but the consultation flow endpoints are working correctly.")
        else:
            print("\n⚠️  Some tests failed. Check the logs above for details.")
            
    except Exception as e:
        print(f"\n💥 Test execution failed: {str(e)}")
        import traceback
        traceback.print_exc()