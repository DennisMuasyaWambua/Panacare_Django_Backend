import firebase_admin
from firebase_admin import credentials, messaging
from django.conf import settings
import os
import logging
import json

logger = logging.getLogger(__name__)


def initialize_firebase():
    """Initialize Firebase Admin SDK with service account"""
    if not firebase_admin._apps:
        try:
            # Method 1: Use environment variables for Firebase credentials (Production - Railway)
            if all(key in os.environ for key in [
                'FIREBASE_PROJECT_ID', 'FIREBASE_PRIVATE_KEY', 'FIREBASE_CLIENT_EMAIL'
            ]):
                logger.info("Using Firebase credentials from environment variables")
                
                # Create credentials dict from environment variables
                firebase_creds = {
                    "type": "service_account",
                    "project_id": os.environ.get('FIREBASE_PROJECT_ID'),
                    "private_key_id": os.environ.get('FIREBASE_PRIVATE_KEY_ID', ''),
                    "private_key": os.environ.get('FIREBASE_PRIVATE_KEY').replace('\\n', '\n'),
                    "client_email": os.environ.get('FIREBASE_CLIENT_EMAIL'),
                    "client_id": os.environ.get('FIREBASE_CLIENT_ID', ''),
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                    "client_x509_cert_url": os.environ.get('FIREBASE_CLIENT_CERT_URL', ''),
                    "universe_domain": "googleapis.com"
                }
                
                cred = credentials.Certificate(firebase_creds)
                firebase_admin.initialize_app(cred)
                logger.info("Firebase Admin SDK initialized successfully from environment")
                return
            
            # Method 2: Use Firebase service account file (Development)
            cred_path = getattr(settings, 'FIREBASE_SERVICE_ACCOUNT_PATH', None)
            
            if cred_path and os.path.exists(cred_path):
                cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred)
                logger.info("Firebase Admin SDK initialized successfully from file")
                return
            
            # Method 3: Try alternative path in project root
            alt_path = os.path.join(settings.BASE_DIR, 'firebase-service-account.json')
            if os.path.exists(alt_path):
                cred = credentials.Certificate(alt_path)
                firebase_admin.initialize_app(cred)
                logger.info("Firebase Admin SDK initialized with alternative path")
                return
            
            # If none of the methods work
            logger.warning("Firebase service account credentials not found. FCM notifications will not work.")
            logger.warning("For production (Railway), set these environment variables:")
            logger.warning("FIREBASE_PROJECT_ID, FIREBASE_PRIVATE_KEY, FIREBASE_CLIENT_EMAIL")
            
        except Exception as e:
            logger.error(f"Failed to initialize Firebase Admin SDK: {e}")


# Initialize Firebase on module import
initialize_firebase()