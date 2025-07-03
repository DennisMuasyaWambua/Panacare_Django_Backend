import requests
import json
from datetime import datetime, timedelta
from typing import Dict, Optional, Any
from django.conf import settings
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)


class PesapalClient:
    """
    Pesapal API client for handling authentication and payment processing.
    Supports both sandbox and production environments.
    """
    
    def __init__(self):
        self.consumer_key = settings.PESAPAL_CONSUMER_KEY
        self.consumer_secret = settings.PESAPAL_CONSUMER_SECRET
        self.sandbox = getattr(settings, 'PESAPAL_SANDBOX', True)
        
        if self.sandbox:
            self.base_url = "https://cybqa.pesapal.com/pesapalv3"
        else:
            self.base_url = "https://pay.pesapal.com/v3"
            
        self.access_token = None
        self.token_expiry = None
    
    def _get_headers(self, include_auth: bool = True) -> Dict[str, str]:
        """Get request headers with optional authentication."""
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        
        if include_auth and self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
            
        return headers
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None, 
                     include_auth: bool = True) -> Dict[str, Any]:
        """Make HTTP request to Pesapal API with error handling."""
        url = f"{self.base_url}{endpoint}"
        headers = self._get_headers(include_auth)
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=headers, params=data)
            else:
                response = requests.post(url, headers=headers, json=data)
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Pesapal API request failed: {e}")
            if hasattr(e, 'response') and e.response:
                try:
                    error_data = e.response.json()
                    return {"error": error_data}
                except:
                    return {"error": {"message": str(e)}}
            return {"error": {"message": str(e)}}
    
    def authenticate(self) -> bool:
        """
        Authenticate with Pesapal API and get access token.
        Tokens are cached for 4 minutes to avoid frequent re-authentication.
        """
        # Check cached token first
        cached_token = cache.get('pesapal_access_token')
        if cached_token:
            self.access_token = cached_token
            return True
        
        auth_data = {
            "consumer_key": self.consumer_key,
            "consumer_secret": self.consumer_secret
        }
        
        response = self._make_request("POST", "/api/Auth/RequestToken", auth_data, include_auth=False)
        
        if "error" in response:
            logger.error(f"Pesapal authentication failed: {response['error']}")
            return False
        
        if "token" in response:
            self.access_token = response["token"]
            # Cache token for 4 minutes (tokens expire after 5 minutes)
            cache.set('pesapal_access_token', self.access_token, 240)
            logger.info("Pesapal authentication successful")
            return True
        
        logger.error("Pesapal authentication failed: No token in response")
        return False
    
    def submit_order_request(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Submit order request to Pesapal for payment processing.
        
        Args:
            order_data: Dictionary containing order details including:
                - id: Unique order identifier
                - currency: Currency code (e.g., "KES")
                - amount: Payment amount
                - description: Order description
                - callback_url: URL for payment completion callback
                - notification_id: IPN notification ID
                - billing_address: Customer billing information
                - account_number: Optional account number for subscriptions
                - subscription_details: Optional subscription configuration
        """
        if not self.access_token and not self.authenticate():
            return {"error": {"message": "Authentication failed"}}
        
        response = self._make_request("POST", "/api/Transactions/SubmitOrderRequest", order_data)
        
        # If authentication expired, retry once
        if "error" in response and "unauthorized" in str(response["error"]).lower():
            if self.authenticate():
                response = self._make_request("POST", "/api/Transactions/SubmitOrderRequest", order_data)
        
        return response
    
    def get_transaction_status(self, order_tracking_id: str) -> Dict[str, Any]:
        """
        Get transaction status from Pesapal.
        
        Args:
            order_tracking_id: Pesapal order tracking ID
        """
        if not self.access_token and not self.authenticate():
            return {"error": {"message": "Authentication failed"}}
        
        params = {"orderTrackingId": order_tracking_id}
        response = self._make_request("GET", "/api/Transactions/GetTransactionStatus", params)
        
        # If authentication expired, retry once
        if "error" in response and "unauthorized" in str(response["error"]).lower():
            if self.authenticate():
                response = self._make_request("GET", "/api/Transactions/GetTransactionStatus", params)
        
        return response
    
    def register_ipn_url(self, ipn_url: str, notification_type: str = "GET") -> Dict[str, Any]:
        """
        Register IPN URL with Pesapal for payment notifications.
        
        Args:
            ipn_url: Your IPN endpoint URL
            notification_type: "GET" or "POST"
        """
        if not self.access_token and not self.authenticate():
            return {"error": {"message": "Authentication failed"}}
        
        ipn_data = {
            "url": ipn_url,
            "ipn_notification_type": notification_type
        }
        
        response = self._make_request("POST", "/api/URLSetup/RegisterIPN", ipn_data)
        
        # If authentication expired, retry once
        if "error" in response and "unauthorized" in str(response["error"]).lower():
            if self.authenticate():
                response = self._make_request("POST", "/api/URLSetup/RegisterIPN", ipn_data)
        
        return response
    
    def get_ipn_list(self) -> Dict[str, Any]:
        """Get list of registered IPN URLs."""
        if not self.access_token and not self.authenticate():
            return {"error": {"message": "Authentication failed"}}
        
        response = self._make_request("GET", "/api/URLSetup/GetIpnList")
        
        # If authentication expired, retry once
        if "error" in response and "unauthorized" in str(response["error"]).lower():
            if self.authenticate():
                response = self._make_request("GET", "/api/URLSetup/GetIpnList")
        
        return response
    
    def create_subscription_order(self, patient_id: str, package_id: str, amount: float,
                                 currency: str = "KES", frequency: str = "MONTHLY",
                                 start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a subscription order with Pesapal.
        
        Args:
            patient_id: Patient identifier
            package_id: Package identifier
            amount: Subscription amount
            currency: Currency code
            frequency: Subscription frequency (DAILY, WEEKLY, MONTHLY, YEARLY)
            start_date: Subscription start date (ISO format)
            end_date: Subscription end date (ISO format)
        """
        order_id = f"SUB_{patient_id}_{package_id}_{int(datetime.now().timestamp())}"
        
        order_data = {
            "id": order_id,
            "currency": currency,
            "amount": amount,
            "description": f"Healthcare subscription - Package {package_id}",
            "callback_url": f"{settings.FRONTEND_URL}/payment/callback",
            "notification_id": getattr(settings, 'PESAPAL_IPN_ID', None),
            "account_number": f"PAT_{patient_id}",
            "billing_address": {
                "email_address": "",  # Will be filled by calling code
                "phone_number": "",   # Will be filled by calling code
                "country_code": "KE",
                "first_name": "",     # Will be filled by calling code
                "last_name": "",      # Will be filled by calling code
                "line_1": "",
                "line_2": "",
                "city": "",
                "state": "",
                "postal_code": "",
                "zip_code": ""
            }
        }
        
        # Add subscription details if provided
        if start_date or end_date or frequency:
            subscription_details = {
                "frequency": frequency
            }
            if start_date:
                subscription_details["start_date"] = start_date
            if end_date:
                subscription_details["end_date"] = end_date
            
            order_data["subscription_details"] = subscription_details
        
        return self.submit_order_request(order_data)