#!/usr/bin/env python
"""
Test script to check production API and find CHP details
"""
import requests
import json

# Production server configuration
BASE_URL = "https://panacaredjangobackend-production.up.railway.app"
LOGIN_URL = f"{BASE_URL}/api/users/login/"

# CHP credentials
CHP_CREDENTIALS = {
    "email": "54bhyh6kgi@mrotzis.com", 
    "password": "dennis@123"
}

def test_chp_login():
    """Test if CHP can login to production"""
    print("🔐 Testing CHP login on production...")
    
    try:
        response = requests.post(LOGIN_URL, json=CHP_CREDENTIALS, timeout=30)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ CHP login successful!")
            print(f"Response data: {json.dumps(data, indent=2)}")
            
            # Get access token
            token = data.get('access_token') or data.get('access')
            if token:
                print(f"🎫 Access Token: {token[:50]}...")
                return token
            else:
                print("❌ No access token found")
                return None
        else:
            print(f"❌ Login failed: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except requests.RequestException as e:
        print(f"❌ Network error: {e}")
        return None

def get_user_profile(token):
    """Get the CHP's user profile"""
    print("\n👤 Getting user profile...")
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        profile_url = f"{BASE_URL}/api/profile/"
        
        response = requests.get(profile_url, headers=headers, timeout=30)
        
        print(f"Profile Status: {response.status_code}")
        
        if response.status_code == 200:
            profile = response.json()
            print("✅ Profile retrieved!")
            print(f"Profile data: {json.dumps(profile, indent=2)}")
            return profile
        else:
            print(f"❌ Profile fetch failed: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except requests.RequestException as e:
        print(f"❌ Error getting profile: {e}")
        return None

def test_patients_list(token):
    """Test if we can access patients list"""
    print("\n📋 Testing patients list access...")
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        patients_url = f"{BASE_URL}/api/patients/"
        
        response = requests.get(patients_url, headers=headers, timeout=30)
        
        print(f"Patients Status: {response.status_code}")
        
        if response.status_code == 200:
            patients = response.json()
            print("✅ Patients list accessible!")
            
            if isinstance(patients, list):
                print(f"Found {len(patients)} patients")
                if patients:
                    print("First patient:", json.dumps(patients[0], indent=2))
            elif isinstance(patients, dict):
                print(f"Patients response: {json.dumps(patients, indent=2)}")
                
            return patients
        else:
            print(f"❌ Patients access failed: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except requests.RequestException as e:
        print(f"❌ Error accessing patients: {e}")
        return None

def test_chp_patients_endpoint(token):
    """Test the CHP-specific patients endpoint"""
    print("\n🏥 Testing CHP patients endpoint...")
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        chp_patients_url = f"{BASE_URL}/api/chp/patients/"
        
        response = requests.get(chp_patients_url, headers=headers, timeout=30)
        
        print(f"CHP Patients Status: {response.status_code}")
        
        if response.status_code == 200:
            chp_patients = response.json()
            print("✅ CHP patients endpoint accessible!")
            print(f"CHP Patients: {json.dumps(chp_patients, indent=2)}")
            return chp_patients
        else:
            print(f"❌ CHP patients access failed: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except requests.RequestException as e:
        print(f"❌ Error accessing CHP patients: {e}")
        return None

def test_assignment_endpoint(token):
    """Test if assignment endpoint is accessible"""
    print("\n🔗 Testing assignment endpoint...")
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        assign_url = f"{BASE_URL}/api/admin/assign-chp-patient/"
        
        # Try with invalid data to see if endpoint exists
        test_data = {"chp_id": "test", "patient_id": "test"}
        response = requests.post(assign_url, json=test_data, headers=headers, timeout=30)
        
        print(f"Assignment Endpoint Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 403:
            print("⚠️  Endpoint exists but CHP doesn't have admin permissions")
        elif response.status_code == 400:
            print("⚠️  Endpoint exists but invalid data sent")
        elif response.status_code == 404:
            print("❌ Assignment endpoint not found")
        else:
            print(f"🤔 Unexpected response: {response.status_code}")
            
    except requests.RequestException as e:
        print(f"❌ Error testing assignment: {e}")

def main():
    """Main test process"""
    print("=" * 60)
    print("🧪 Testing Production API Access")
    print("=" * 60)
    print(f"🌐 Server: {BASE_URL}")
    print(f"👤 CHP Email: {CHP_CREDENTIALS['email']}")
    print()
    
    # Test login
    token = test_chp_login()
    if not token:
        print("❌ Cannot proceed without valid token")
        return
    
    # Test profile
    profile = get_user_profile(token)
    
    # Test patients access
    patients = test_patients_list(token)
    
    # Test CHP patients
    chp_patients = test_chp_patients_endpoint(token)
    
    # Test assignment endpoint
    test_assignment_endpoint(token)
    
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    print(f"✅ Login: {'Success' if token else 'Failed'}")
    print(f"✅ Profile: {'Success' if profile else 'Failed'}")
    print(f"✅ Patients: {'Success' if patients else 'Failed'}")
    print(f"✅ CHP Patients: {'Success' if chp_patients else 'Failed'}")

if __name__ == "__main__":
    main()