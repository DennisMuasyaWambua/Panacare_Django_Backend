#!/usr/bin/env python3
"""
Debug script to test Twilio configuration and token generation
"""

import os
import sys
import django
from pathlib import Path

# Add the project directory to Python path
project_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(project_dir))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'panacare.settings')
django.setup()

from django.conf import settings
from healthcare.twilio_utils import get_twilio_client, generate_twilio_token

def test_twilio_config():
    """Test Twilio configuration"""
    print("=" * 60)
    print("TWILIO CONFIGURATION TEST")
    print("=" * 60)
    
    # Check environment variables
    print("\n1. Environment Variables:")
    print(f"   TWILIO_ACCOUNT_SID: {'✓' if settings.TWILIO_ACCOUNT_SID else '✗'} {'(set)' if settings.TWILIO_ACCOUNT_SID else '(not set)'}")
    print(f"   TWILIO_AUTH_TOKEN: {'✓' if settings.TWILIO_AUTH_TOKEN else '✗'} {'(set)' if settings.TWILIO_AUTH_TOKEN else '(not set)'}")
    print(f"   TWILIO_API_KEY_SID: {'✓' if settings.TWILIO_API_KEY_SID else '✗'} {'(set)' if settings.TWILIO_API_KEY_SID else '(not set)'}")
    print(f"   TWILIO_API_KEY_SECRET: {'✓' if settings.TWILIO_API_KEY_SECRET else '✗'} {'(set)' if settings.TWILIO_API_KEY_SECRET else '(not set)'}")
    
    # Show partial values for debugging (masked for security)
    if settings.TWILIO_ACCOUNT_SID:
        print(f"   TWILIO_ACCOUNT_SID value: {settings.TWILIO_ACCOUNT_SID[:10]}...")
    if settings.TWILIO_AUTH_TOKEN:
        print(f"   TWILIO_AUTH_TOKEN value: {settings.TWILIO_AUTH_TOKEN[:10]}...")
    if settings.TWILIO_API_KEY_SID:
        print(f"   TWILIO_API_KEY_SID value: {settings.TWILIO_API_KEY_SID[:10]}...")
    if settings.TWILIO_API_KEY_SECRET:
        print(f"   TWILIO_API_KEY_SECRET value: {settings.TWILIO_API_KEY_SECRET[:10]}...")
    
    # Test client creation
    print("\n2. Twilio Client Test:")
    try:
        client = get_twilio_client()
        print("   ✓ Twilio client created successfully")
        
        # Try to get account info
        account = client.api.accounts(settings.TWILIO_ACCOUNT_SID).fetch()
        print(f"   ✓ Account SID verified: {account.sid}")
        print(f"   ✓ Account status: {account.status}")
        
    except Exception as e:
        print(f"   ✗ Error creating Twilio client: {str(e)}")
        return False
    
    # Test token generation
    print("\n3. Token Generation Test:")
    try:
        test_identity = "test-user-123"
        test_room = "test-room-456"
        
        token = generate_twilio_token(test_identity, test_room)
        print(f"   ✓ Token generated successfully")
        print(f"   ✓ Token length: {len(token)} characters")
        print(f"   ✓ Token preview: {token[:50]}...")
        
        # Decode and inspect the token
        import jwt
        try:
            decoded = jwt.decode(token, options={"verify_signature": False})
            print(f"   ✓ Token decoded successfully")
            print(f"   ✓ Token issuer: {decoded.get('iss', 'Not set')}")
            print(f"   ✓ Token subject: {decoded.get('sub', 'Not set')}")
            print(f"   ✓ Token identity: {decoded.get('identity', 'Not set')}")
            print(f"   ✓ Token grants: {decoded.get('grants', 'Not set')}")
            
            # Check if the issuer matches the API key
            if decoded.get('iss') == settings.TWILIO_API_KEY_SID:
                print("   ✓ Token issuer matches API key SID")
            else:
                print(f"   ✗ Token issuer mismatch: Expected {settings.TWILIO_API_KEY_SID}, got {decoded.get('iss')}")
                
        except Exception as jwt_error:
            print(f"   ✗ Error decoding token: {str(jwt_error)}")
            
    except Exception as e:
        print(f"   ✗ Error generating token: {str(e)}")
        return False
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print("✓ All Twilio configuration tests passed!")
    print("✓ Twilio integration appears to be working correctly")
    
    return True

def check_common_issues():
    """Check for common Twilio configuration issues"""
    print("\n" + "=" * 60)
    print("COMMON ISSUES CHECK")
    print("=" * 60)
    
    issues = []
    
    # Check if Account SID format is correct
    if settings.TWILIO_ACCOUNT_SID and not settings.TWILIO_ACCOUNT_SID.startswith('AC'):
        issues.append("Account SID should start with 'AC'")
    
    # Check if API Key SID format is correct
    if settings.TWILIO_API_KEY_SID and not settings.TWILIO_API_KEY_SID.startswith('SK'):
        issues.append("API Key SID should start with 'SK'")
    
    # Check if all required credentials are set
    if not all([settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN, 
                settings.TWILIO_API_KEY_SID, settings.TWILIO_API_KEY_SECRET]):
        issues.append("Not all required Twilio credentials are set")
    
    # Check if credentials are not placeholder values
    placeholder_values = ['your_twilio_account_sid', 'your_twilio_auth_token', 
                         'your_twilio_api_key_sid', 'your_twilio_api_key_secret']
    
    if any(getattr(settings, attr, '') in placeholder_values for attr in 
           ['TWILIO_ACCOUNT_SID', 'TWILIO_AUTH_TOKEN', 'TWILIO_API_KEY_SID', 'TWILIO_API_KEY_SECRET']):
        issues.append("Some credentials appear to be placeholder values")
    
    if issues:
        print("\n⚠️  Potential Issues Found:")
        for issue in issues:
            print(f"   - {issue}")
    else:
        print("\n✓ No common configuration issues detected")
    
    return issues

if __name__ == "__main__":
    print("Twilio Configuration Debug Script")
    print("=" * 60)
    
    try:
        # Test configuration
        config_ok = test_twilio_config()
        
        # Check for common issues
        issues = check_common_issues()
        
        if not config_ok or issues:
            print("\n🚨 TROUBLESHOOTING RECOMMENDATIONS:")
            print("1. Verify your Twilio credentials in the .env file")
            print("2. Make sure you have created an API Key in Twilio Console")
            print("3. Check that your Account SID starts with 'AC'")
            print("4. Check that your API Key SID starts with 'SK'")
            print("5. Ensure your account has Video API access enabled")
            print("6. Try regenerating your API Key if the issue persists")
            
        else:
            print("\n🎉 SUCCESS: Twilio configuration appears to be working correctly!")
            
    except Exception as e:
        print(f"\n❌ FATAL ERROR: {str(e)}")
        import traceback
        traceback.print_exc()