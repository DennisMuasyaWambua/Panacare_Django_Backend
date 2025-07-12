#!/usr/bin/env python3
"""
Simple Twilio authentication test without Django
"""

import os
from dotenv import load_dotenv
from twilio.rest import Client
from twilio.jwt.access_token import AccessToken
from twilio.jwt.access_token.grants import VideoGrant

# Load environment variables
load_dotenv()

# Get Twilio credentials from environment
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_API_KEY_SID = os.getenv('TWILIO_API_KEY_SID')
TWILIO_API_KEY_SECRET = os.getenv('TWILIO_API_KEY_SECRET')

def test_twilio_auth():
    print("🔍 Testing Twilio Authentication...")
    
    print(f"Account SID: {TWILIO_ACCOUNT_SID[:10]}..." if TWILIO_ACCOUNT_SID else "NOT SET")
    print(f"Auth Token: {TWILIO_AUTH_TOKEN[:10]}..." if TWILIO_AUTH_TOKEN else "NOT SET")
    print(f"API Key SID: {TWILIO_API_KEY_SID[:10]}..." if TWILIO_API_KEY_SID else "NOT SET")
    print(f"API Key Secret: {TWILIO_API_KEY_SECRET[:10]}..." if TWILIO_API_KEY_SECRET else "NOT SET")
    
    if not all([TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN]):
        print("❌ Missing basic Twilio credentials!")
        return False
    
    try:
        # Test basic authentication
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        print("✅ Twilio client created successfully")
        
        # Test API access
        account = client.api.accounts(TWILIO_ACCOUNT_SID).fetch()
        print(f"✅ Account fetched: {account.friendly_name}")
        print(f"Account Status: {account.status}")
        
        # Test Video service access
        try:
            rooms = client.video.rooms.list(limit=1)
            print(f"✅ Video service accessible, found {len(rooms)} rooms")
        except Exception as e:
            print(f"⚠️  Video service error: {e}")
        
        # Test token generation (if API key credentials are available)
        if TWILIO_API_KEY_SID and TWILIO_API_KEY_SECRET:
            try:
                token = AccessToken(
                    TWILIO_ACCOUNT_SID,
                    TWILIO_API_KEY_SID,
                    TWILIO_API_KEY_SECRET,
                    identity="test_user"
                )
                video_grant = VideoGrant(room="test_room")
                token.add_grant(video_grant)
                jwt_token = token.to_jwt()
                print(f"✅ JWT token generated: {len(jwt_token)} characters")
            except Exception as e:
                print(f"❌ Token generation failed: {e}")
        else:
            print("⚠️  API Key credentials not available for token generation")
        
        return True
        
    except Exception as e:
        print(f"❌ Twilio authentication failed: {e}")
        return False

if __name__ == "__main__":
    success = test_twilio_auth()
    if success:
        print("\n🎉 Twilio authentication successful!")
    else:
        print("\n💥 Twilio authentication failed!")