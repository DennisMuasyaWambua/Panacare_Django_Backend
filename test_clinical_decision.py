import requests
import json
import os

# Get base URL from environment or use default
BASE_URL = os.environ.get('PANACARE_API_URL', 'http://localhost:8000')

# Login to get token
def get_auth_token():
    login_url = f"{BASE_URL}/api/users/login/"
    login_data = {
        "email": "your_test_email@example.com",  # Change this to a valid user email
        "password": "your_password"              # Change this to the correct password
    }
    
    response = requests.post(login_url, json=login_data)
    if response.status_code == 200:
        return response.json().get('access')
    else:
        print(f"Login failed: {response.text}")
        return None

# Test the clinical decision endpoint
def test_clinical_decision():
    token = get_auth_token()
    if not token:
        print("Authentication failed. Cannot proceed with test.")
        return
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    # Sample data for the clinical decision endpoint
    clinical_data = {
        "age": 45,
        "gender": "male",
        "weight": 80,
        "height": 175,
        "high_blood_pressure": True,
        "diabetes": False,
        "on_medication": True,
        "headache": True,
        "dizziness": False,
        "blurred_vision": False,
        "palpitations": True,
        "fatigue": True,
        "chest_pain": False,
        "frequent_thirst": False,
        "loss_of_appetite": False,
        "frequent_urination": False,
        "other_symptoms": "",
        "no_symptoms": False,
        "systolic_pressure": 145,
        "diastolic_pressure": 95,
        "blood_sugar": 95,
        "heart_rate": 85,
        "sleep_hours": 6,
        "exercise_minutes": 15,
        "eats_unhealthy": True,
        "smokes": False,
        "consumes_alcohol": True,
        "skips_medication": True
    }
    
    url = f"{BASE_URL}/api/clinical-decision/"
    response = requests.post(url, headers=headers, json=clinical_data)
    
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print("\nClinical Decision Result:")
        print(f"Risk Level: {result.get('risk_level')}")
        print(f"\nAnalysis:\n{result.get('analysis')}")
        print("\nRecommendations:")
        for rec in result.get('recommendations', []):
            print(f"- {rec}")
        print(f"\nRecord ID: {result.get('record_id')}")
    else:
        print(f"Error: {response.text}")
    
    # Test retrieving clinical history
    history_url = f"{BASE_URL}/api/clinical-history/"
    history_response = requests.get(history_url, headers=headers)
    
    print("\n\nClinical History:")
    print(f"Status Code: {history_response.status_code}")
    if history_response.status_code == 200:
        history = history_response.json()
        print(f"Total Records: {len(history)}")
        if history:
            print(f"Latest Record Date: {history[0].get('created_at')}")
    else:
        print(f"Error: {history_response.text}")

if __name__ == "__main__":
    test_clinical_decision()