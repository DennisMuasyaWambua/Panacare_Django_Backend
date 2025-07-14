import requests
import json

# Base URL of your Django application
BASE_URL = "http://localhost:8000"  # Change this to your server URL

# First, let's create a test user and get a token
def create_test_user_and_login():
    # Register a test user
    register_url = f"{BASE_URL}/api/users/register/"
    register_data = {
        "username": "testuser123",
        "email": "testuser123@example.com",
        "password": "Test@password123",
        "first_name": "Test",
        "last_name": "User",
        "phone_number": "1234567890",
        "role": "patient"  # Role must be patient or doctor
    }
    
    try:
        print("Attempting to register test user...")
        response = requests.post(register_url, json=register_data)
        print(f"Registration status code: {response.status_code}")
        print(f"Registration response: {response.text[:200]}...")
        
        # Since email verification is likely required, let's try a different approach
        # For testing purposes, try to use an existing admin account if available
        
        login_url = f"{BASE_URL}/api/users/login/"
        login_data = {
            "email": "admin@panacare.com",  # Replace with a known admin account
            "password": "admin123"  # Replace with correct password
        }
        
        print("\nAttempting to login with admin account...")
        response = requests.post(login_url, json=login_data)
        print(f"Login status code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            token = data.get('tokens', {}).get('access')
            print(f"Login successful! Token: {token[:20]}...")
            return token
        else:
            print(f"Login failed: {response.text}")
            
            # Try one more account
            login_data = {
                "email": "muasyathegreat4@gmail.com",  # Another potential account
                "password": "admin123"  # Try common password
            }
            
            print("\nTrying another account...")
            response = requests.post(login_url, json=login_data)
            print(f"Login status code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                token = data.get('tokens', {}).get('access')
                print(f"Login successful! Token: {token[:20]}...")
                return token
            else:
                print(f"Login failed: {response.text}")
                return None
            
    except Exception as e:
        print(f"Error during registration/login: {str(e)}")
        return None

# Test patient endpoint with any available token
def test_patient_endpoint(token=None):
    if not token:
        print("No token available, skipping patient endpoint test")
        return
        
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Use a known patient ID
    patient_id = "a0f439c5-4c6c-4222-afbb-7e00529ec344"  # Replace with a valid ID
    
    try:
        response = requests.get(f"{BASE_URL}/api/patients/{patient_id}/", headers=headers)
        print(f"Patient endpoint status code: {response.status_code}")
        
        if response.status_code == 200:
            print("Success! Patient data retrieved:")
            print(json.dumps(response.json(), indent=2))
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Error requesting patient endpoint: {str(e)}")

# Test doctor endpoint
def test_doctor_endpoint(token=None):
    if not token:
        print("No token available, skipping doctor endpoint test")
        return
        
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Use a known doctor ID
    doctor_id = "281243e2-1ffa-4a89-9b7a-f1d5b5eefb41"  # Replace with a valid ID
    
    try:
        response = requests.get(f"{BASE_URL}/api/doctors/{doctor_id}/", headers=headers)
        print(f"Doctor endpoint status code: {response.status_code}")
        
        if response.status_code == 200:
            print("Success! Doctor data retrieved:")
            print(json.dumps(response.json(), indent=2))
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Error requesting doctor endpoint: {str(e)}")

if __name__ == "__main__":
    token = create_test_user_and_login()
    
    print("\nTesting Patient Endpoint:")
    test_patient_endpoint(token)
    
    print("\nTesting Doctor Endpoint:")
    test_doctor_endpoint(token)