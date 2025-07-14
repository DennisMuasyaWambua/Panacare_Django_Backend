import requests
import json

# Base URL of your Django application
BASE_URL = "http://localhost:8000"  # Change this to your server URL

# Read the admin token
try:
    with open('admin_token.txt', 'r') as f:
        token = f.read().strip()
    print(f"Using admin token: {token[:20]}...")
except Exception as e:
    print(f"Error reading token: {str(e)}")
    token = None

# Test patient endpoint
def test_patient_endpoint(token):
    if not token:
        print("No token available, skipping patient endpoint test")
        return
        
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Use the patient ID we found in the diagnostic script
    patient_id = "a0f439c5-4c6c-4222-afbb-7e00529ec344"
    
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
def test_doctor_endpoint(token):
    if not token:
        print("No token available, skipping doctor endpoint test")
        return
        
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Use the doctor ID we found in the diagnostic script
    doctor_id = "281243e2-1ffa-4a89-9b7a-f1d5b5eefb41"
    
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
    print("Testing Patient Endpoint:")
    test_patient_endpoint(token)
    
    print("\nTesting Doctor Endpoint:")
    test_doctor_endpoint(token)