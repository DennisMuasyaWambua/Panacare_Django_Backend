#!/usr/bin/env python3
"""
Test Twilio token validation from frontend perspective
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
from healthcare.twilio_utils import generate_twilio_token
import jwt
import json
import time

def validate_token_for_frontend(token, expected_identity=None, expected_room=None):
    """
    Validate a token as the frontend/Twilio SDK would
    """
    print(f"Validating token...")
    
    try:
        # First, decode without verification to inspect structure
        decoded = jwt.decode(token, options={"verify_signature": False})
        print(f"✓ Token decoded successfully")
        
        # Check expiration
        exp = decoded.get('exp')
        if exp:
            if time.time() > exp:
                print(f"✗ Token expired (exp: {exp}, current: {time.time()})")
                return False
            else:
                print(f"✓ Token not expired (exp: {exp}, current: {time.time()})")
        
        # Check issuer
        iss = decoded.get('iss')
        if iss:
            if iss == settings.TWILIO_API_KEY_SID:
                print(f"✓ Issuer matches API Key SID: {iss}")
            else:
                print(f"✗ Issuer mismatch: Expected {settings.TWILIO_API_KEY_SID}, got {iss}")
                return False
        else:
            print(f"✗ No issuer (iss) in token")
            return False
        
        # Check subject
        sub = decoded.get('sub')
        if sub:
            if sub == settings.TWILIO_ACCOUNT_SID:
                print(f"✓ Subject matches Account SID: {sub}")
            else:
                print(f"✗ Subject mismatch: Expected {settings.TWILIO_ACCOUNT_SID}, got {sub}")
                return False
        else:
            print(f"✗ No subject (sub) in token")
            return False
        
        # Check grants
        grants = decoded.get('grants', {})
        if not grants:
            print(f"✗ No grants in token")
            return False
        
        # Check identity grant
        identity = grants.get('identity')
        if identity:
            print(f"✓ Identity grant: {identity}")
            if expected_identity and identity != expected_identity:
                print(f"⚠️  Identity mismatch: Expected {expected_identity}, got {identity}")
        else:
            print(f"✗ No identity grant")
            return False
        
        # Check video grant
        video = grants.get('video')
        if video:
            room = video.get('room')
            if room:
                print(f"✓ Video room grant: {room}")
                if expected_room and room != expected_room:
                    print(f"⚠️  Room mismatch: Expected {expected_room}, got {room}")
            else:
                print(f"✗ No room in video grant")
                return False
        else:
            print(f"✗ No video grant")
            return False
        
        print(f"✓ Token validation passed")
        return True
        
    except Exception as e:
        print(f"✗ Token validation failed: {str(e)}")
        return False

def test_token_validation_scenarios():
    """Test various token validation scenarios"""
    print("=" * 60)
    print("FRONTEND TOKEN VALIDATION TEST")
    print("=" * 60)
    
    # Test 1: Valid token
    print("\n1. Testing valid token:")
    try:
        token = generate_twilio_token("test-user", "test-room")
        is_valid = validate_token_for_frontend(token, "test-user", "test-room")
        print(f"Result: {'✓ VALID' if is_valid else '✗ INVALID'}")
    except Exception as e:
        print(f"Error generating token: {e}")
    
    # Test 2: Token with different API key (simulating wrong issuer)
    print("\n2. Testing token with wrong issuer:")
    try:
        # Save original settings
        original_api_key = settings.TWILIO_API_KEY_SID
        original_secret = settings.TWILIO_API_KEY_SECRET
        
        # Create token with different API key
        settings.TWILIO_API_KEY_SID = "SK" + "x" * 32  # Fake API key
        settings.TWILIO_API_KEY_SECRET = "y" * 32  # Fake secret
        
        token = generate_twilio_token("test-user", "test-room")
        
        # Restore original settings for validation
        settings.TWILIO_API_KEY_SID = original_api_key
        settings.TWILIO_API_KEY_SECRET = original_secret
        
        is_valid = validate_token_for_frontend(token, "test-user", "test-room")
        print(f"Result: {'✓ VALID' if is_valid else '✗ INVALID'}")
        
    except Exception as e:
        print(f"Error in test: {e}")
        # Restore settings
        settings.TWILIO_API_KEY_SID = original_api_key
        settings.TWILIO_API_KEY_SECRET = original_secret
    
    # Test 3: Token with different Account SID (simulating wrong subject)
    print("\n3. Testing token with wrong subject:")
    try:
        # Save original settings
        original_account_sid = settings.TWILIO_ACCOUNT_SID
        
        # Create token with different Account SID
        settings.TWILIO_ACCOUNT_SID = "AC" + "x" * 32  # Fake Account SID
        
        token = generate_twilio_token("test-user", "test-room")
        
        # Restore original settings for validation
        settings.TWILIO_ACCOUNT_SID = original_account_sid
        
        is_valid = validate_token_for_frontend(token, "test-user", "test-room")
        print(f"Result: {'✓ VALID' if is_valid else '✗ INVALID'}")
        
    except Exception as e:
        print(f"Error in test: {e}")
        # Restore settings
        settings.TWILIO_ACCOUNT_SID = original_account_sid

def test_token_with_twilio_sdk_simulation():
    """Simulate how Twilio SDK would validate the token"""
    print("\n" + "=" * 60)
    print("TWILIO SDK VALIDATION SIMULATION")
    print("=" * 60)
    
    try:
        # Generate a token
        identity = "doctor-123"
        room = "consultation-room-456"
        token = generate_twilio_token(identity, room)
        
        print(f"Generated token for identity: {identity}")
        print(f"Generated token for room: {room}")
        print(f"Token: {token[:50]}...")
        
        # Decode and check all critical fields
        decoded = jwt.decode(token, options={"verify_signature": False})
        
        print(f"\nToken payload:")
        print(f"  iss (issuer): {decoded.get('iss')}")
        print(f"  sub (subject): {decoded.get('sub')}")
        print(f"  exp (expiration): {decoded.get('exp')}")
        print(f"  iat (issued at): {decoded.get('iat')}")
        print(f"  jti (JWT ID): {decoded.get('jti')}")
        print(f"  grants: {decoded.get('grants')}")
        
        # Check if this matches what Twilio expects
        expected_checks = [
            ("Issuer is API Key SID", decoded.get('iss') == settings.TWILIO_API_KEY_SID),
            ("Subject is Account SID", decoded.get('sub') == settings.TWILIO_ACCOUNT_SID),
            ("Has expiration", 'exp' in decoded),
            ("Has JWT ID", 'jti' in decoded),
            ("Has grants", 'grants' in decoded),
            ("Has identity grant", 'identity' in decoded.get('grants', {})),
            ("Has video grant", 'video' in decoded.get('grants', {})),
            ("Video grant has room", 'room' in decoded.get('grants', {}).get('video', {}))
        ]
        
        print(f"\nTwilio SDK expectations:")
        all_passed = True
        for check_name, passed in expected_checks:
            status = "✓" if passed else "✗"
            print(f"  {status} {check_name}")
            if not passed:
                all_passed = False
        
        print(f"\nOverall result: {'✓ VALID' if all_passed else '✗ INVALID'}")
        
        # Additional debugging info
        print(f"\nDebugging info:")
        print(f"  Current Account SID: {settings.TWILIO_ACCOUNT_SID}")
        print(f"  Current API Key SID: {settings.TWILIO_API_KEY_SID}")
        print(f"  Token issuer: {decoded.get('iss')}")
        print(f"  Token subject: {decoded.get('sub')}")
        
        return all_passed
        
    except Exception as e:
        print(f"Error in SDK simulation: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Twilio Frontend Token Validation Test")
    print("=" * 60)
    
    try:
        test_token_validation_scenarios()
        sdk_valid = test_token_with_twilio_sdk_simulation()
        
        print("\n" + "=" * 60)
        print("FINAL SUMMARY")
        print("=" * 60)
        
        if sdk_valid:
            print("✓ All tests passed - Token should work with Twilio SDK")
            print("✓ No 'Invalid Access Token issuer/subject' error expected")
        else:
            print("✗ Some tests failed - Token might not work with Twilio SDK")
            print("✗ 'Invalid Access Token issuer/subject' error possible")
            
        print("\n📝 RECOMMENDATIONS:")
        print("1. Verify that your Twilio API Key is correctly configured")
        print("2. Ensure the API Key belongs to the same Account SID")
        print("3. Check that the API Key has Video API permissions")
        print("4. Make sure you're using the correct API Key SID and Secret")
        print("5. If using environment variables, ensure they're loaded correctly")
        
    except Exception as e:
        print(f"\n❌ FATAL ERROR: {str(e)}")
        import traceback
        traceback.print_exc()