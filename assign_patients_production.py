#!/usr/bin/env python
"""
Script to assign patients to CHP on production server using API endpoints
"""
import requests
import json
import time

# Production server configuration
BASE_URL = "https://panacaredjangobackend-production.up.railway.app"
LOGIN_URL = f"{BASE_URL}/api/users/login/"
ASSIGN_URL = f"{BASE_URL}/api/admin/assign-chp-patient/"

# CHP credentials and details
CHP_CREDENTIALS = {
    "email": "54bhyh6kgi@mrotzis.com",
    "password": "dennis@123"
}

# We need to find the CHP ID and patient IDs on production
# Let's use the same IDs we found locally, but they might be different on production

def get_admin_token():
    """Get admin token for API calls - you'll need admin credentials"""
    print("⚠️  Admin token needed for patient assignment")
    print("Please provide admin credentials for the production server:")
    
    admin_email = input("Admin email: ")
    admin_password = input("Admin password: ")
    
    admin_credentials = {
        "email": admin_email,
        "password": admin_password
    }
    
    try:
        print(f"🔐 Logging in admin to {LOGIN_URL}...")
        response = requests.post(LOGIN_URL, json=admin_credentials, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            token = data.get('access_token') or data.get('access')
            if token:
                print("✅ Admin login successful!")
                return token
            else:
                print("❌ No access token in response")
                print(f"Response: {response.text}")
                return None
        else:
            print(f"❌ Admin login failed: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except requests.RequestException as e:
        print(f"❌ Network error during admin login: {e}")
        return None

def verify_chp_exists(token):
    """Verify the CHP exists on production and get their ID"""
    print(f"🔍 Checking if CHP exists on production...")
    
    # Try to get CHP profile or list
    try:
        headers = {"Authorization": f"Bearer {token}"}
        
        # Try to get user list to find the CHP
        users_url = f"{BASE_URL}/api/users/"
        response = requests.get(users_url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            users = response.json()
            if isinstance(users, list):
                for user in users:
                    if user.get('email') == CHP_CREDENTIALS['email']:
                        print(f"✅ Found CHP user: {user}")
                        return user
            elif isinstance(users, dict) and 'results' in users:
                for user in users['results']:
                    if user.get('email') == CHP_CREDENTIALS['email']:
                        print(f"✅ Found CHP user: {user}")
                        return user
        
        print(f"❌ Could not find CHP with email {CHP_CREDENTIALS['email']}")
        print(f"Response: {response.text}")
        return None
        
    except requests.RequestException as e:
        print(f"❌ Error checking CHP: {e}")
        return None

def get_available_patients(token):
    """Get list of available patients on production"""
    print("📋 Getting available patients...")
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        patients_url = f"{BASE_URL}/api/patients/"
        
        response = requests.get(patients_url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            patients = response.json()
            
            if isinstance(patients, list):
                patient_list = patients[:5]  # Get first 5 patients
            elif isinstance(patients, dict) and 'results' in patients:
                patient_list = patients['results'][:5]  # Get first 5 patients
            else:
                patient_list = []
            
            print(f"✅ Found {len(patient_list)} patients for assignment")
            for i, patient in enumerate(patient_list, 1):
                patient_name = f"{patient.get('user', {}).get('first_name', '')} {patient.get('user', {}).get('last_name', '')}".strip()
                if not patient_name:
                    patient_name = patient.get('user', {}).get('email', 'Unknown')
                print(f"  {i}. {patient_name} (ID: {patient.get('id')})")
            
            return patient_list
        else:
            print(f"❌ Failed to get patients: {response.status_code}")
            print(f"Response: {response.text}")
            return []
            
    except requests.RequestException as e:
        print(f"❌ Error getting patients: {e}")
        return []

def assign_patient_to_chp(token, chp_id, patient_id, patient_name):
    """Assign a specific patient to the CHP"""
    print(f"🔗 Assigning {patient_name} to CHP...")
    
    try:
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        assignment_data = {
            "chp_id": chp_id,
            "patient_id": patient_id
        }
        
        response = requests.post(ASSIGN_URL, json=assignment_data, headers=headers, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Successfully assigned {patient_name}")
            return True
        else:
            print(f"❌ Failed to assign {patient_name}: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.RequestException as e:
        print(f"❌ Error assigning {patient_name}: {e}")
        return False

def main():
    """Main assignment process"""
    print("=" * 60)
    print("🏥 CHP Patient Assignment - Production Server")
    print("=" * 60)
    print(f"🌐 Server: {BASE_URL}")
    print(f"👤 CHP Email: {CHP_CREDENTIALS['email']}")
    print()
    
    # Step 1: Get admin token
    admin_token = get_admin_token()
    if not admin_token:
        print("❌ Cannot proceed without admin token")
        return
    
    print()
    print("-" * 40)
    
    # Step 2: Verify CHP exists
    chp_user = verify_chp_exists(admin_token)
    if not chp_user:
        print("❌ CHP not found on production server")
        print("💡 You may need to create the CHP account first")
        return
    
    # We need to find the CHP profile ID
    chp_user_id = chp_user.get('id')
    print(f"📝 CHP User ID: {chp_user_id}")
    
    print()
    print("-" * 40)
    
    # Step 3: Get available patients
    patients = get_available_patients(admin_token)
    if not patients:
        print("❌ No patients available for assignment")
        return
    
    print()
    print("-" * 40)
    
    # Step 4: Perform assignments
    print("🚀 Starting patient assignments...")
    print()
    
    successful_assignments = 0
    failed_assignments = 0
    
    # Note: We need the CHP profile ID, not the user ID
    # Let's try using the user ID first, and if it fails, we'll need to find the CHP profile ID
    
    for patient in patients:
        patient_id = patient.get('id')
        patient_name = f"{patient.get('user', {}).get('first_name', '')} {patient.get('user', {}).get('last_name', '')}".strip()
        if not patient_name:
            patient_name = patient.get('user', {}).get('email', 'Unknown Patient')
        
        # Try assignment with user ID first
        success = assign_patient_to_chp(admin_token, chp_user_id, patient_id, patient_name)
        
        if success:
            successful_assignments += 1
        else:
            failed_assignments += 1
        
        # Add small delay between requests
        time.sleep(1)
    
    print()
    print("=" * 60)
    print("📊 ASSIGNMENT SUMMARY")
    print("=" * 60)
    print(f"✅ Successful assignments: {successful_assignments}")
    print(f"❌ Failed assignments: {failed_assignments}")
    print(f"📈 Total attempts: {successful_assignments + failed_assignments}")
    
    if successful_assignments > 0:
        print()
        print("🎉 Patient assignments completed successfully!")
        print("💬 The CHP can now message their assigned patients")
    else:
        print()
        print("⚠️  No assignments were successful")
        print("💡 This might be due to:")
        print("   - Incorrect CHP ID format (need profile ID, not user ID)")
        print("   - Patients already assigned")
        print("   - Permission issues")
        print("   - API endpoint differences")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⏹️  Assignment process interrupted by user")
    except Exception as e:
        print(f"\n\n💥 Unexpected error: {e}")