import firebase_admin
from firebase_admin import credentials, messaging
from django.conf import settings
import os
import logging

logger = logging.getLogger(__name__)


def initialize_firebase():
    """Initialize Firebase Admin SDK with service account"""
    if not firebase_admin._apps:
        try:
            # Path to your Firebase service account JSON file
            cred_path = getattr(settings, 'FIREBASE_SERVICE_ACCOUNT_PATH', None)
            
            if cred_path and os.path.exists(cred_path):
                cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred)
                logger.info("Firebase Admin SDK initialized successfully")
            else:
                # Try alternative path in project root
                alt_path = os.path.join(settings.BASE_DIR, 'firebase-service-account.json')
                if os.path.exists(alt_path):
                    cred = credentials.Certificate(alt_path)
                    firebase_admin.initialize_app(cred)
                    logger.info("Firebase Admin SDK initialized with alternative path")
                else:
                    logger.warning("Firebase service account file not found. FCM notifications will not work.")
        except Exception as e:
            logger.error(f"Failed to initialize Firebase Admin SDK: {e}")


# Initialize Firebase on module import
initialize_firebase()