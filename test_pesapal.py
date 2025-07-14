#!/usr/bin/env python
import os
import django
from django.conf import settings

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'panacare.settings')
django.setup()

from healthcare.pesapal_client import PesapalClient

def test_pesapal_authentication():
    """Test Pesapal authentication"""
    print("Testing Pesapal Integration...")
    print(f"Environment: {'Sandbox' if settings.PESAPAL_SANDBOX else 'Production'}")
    print(f"Consumer Key: {settings.PESAPAL_CONSUMER_KEY[:10]}...")
    
    client = PesapalClient()
    
    # Test authentication
    print("\n1. Testing Authentication...")
    auth_success = client.authenticate()
    
    if auth_success:
        print("✅ Authentication successful!")
        print(f"Access Token: {client.access_token[:20]}...")
    else:
        print("❌ Authentication failed!")
        return False
    
    # Test IPN list retrieval
    print("\n2. Testing IPN List Retrieval...")
    ipn_response = client.get_ipn_list()
    
    if "error" in ipn_response:
        print(f"❌ IPN List retrieval failed: {ipn_response['error']}")
    else:
        print("✅ IPN List retrieved successfully!")
        print(f"Response: {ipn_response}")
    
    # Test order submission with minimal data
    print("\n3. Testing Order Submission...")
    test_order = {
        "id": "TEST_ORDER_12345",
        "currency": "KES",
        "amount": 100.00,
        "description": "Test subscription payment",
        "callback_url": "https://example.com/callback",
        "billing_address": {
            "email_address": "test@example.com",
            "phone_number": "+254700000000",
            "country_code": "KE",
            "first_name": "Test",
            "last_name": "User",
            "line_1": "Test Address",
            "line_2": "",
            "city": "Nairobi",
            "state": "",
            "postal_code": "",
            "zip_code": ""
        }
    }
    
    order_response = client.submit_order_request(test_order)
    
    if "error" in order_response:
        print(f"❌ Order submission failed: {order_response['error']}")
    else:
        print("✅ Order submission successful!")
        print(f"Order Tracking ID: {order_response.get('order_tracking_id', 'N/A')}")
        print(f"Redirect URL: {order_response.get('redirect_url', 'N/A')}")
    
    return True

if __name__ == "__main__":
    test_pesapal_authentication()