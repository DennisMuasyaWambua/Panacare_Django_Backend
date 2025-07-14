from django.conf import settings
from twilio.jwt.access_token import AccessToken
from twilio.jwt.access_token.grants import VideoGrant
from twilio.rest import Client
import logging

logger = logging.getLogger(__name__)

def get_twilio_client():
    """
    Returns a Twilio client instance.
    """
    # try:
        # Validate credentials are set
    account_sid = getattr(settings, 'TWILIO_ACCOUNT_SID', None)
    auth_token = getattr(settings, 'TWILIO_AUTH_TOKEN', None)


    print("This is the account SID: ", account_sid)
    print("This is the account auth_token: ", auth_token)

    if not account_sid or not auth_token:
        raise ValueError("TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN must be set in settings.py")

    return Client(account_sid, auth_token)

    # except Exception as e:
    #     logger.error(f"Error creating Twilio client: {e}")
    #     raise


def create_twilio_room(room_name):
    """
    Creates a Twilio video room
    
    Args:
        room_name (str): The name for the room
        
    Returns:
        room: The Twilio room object
    """
    try:
        client = get_twilio_client()
        print("we are here......")
        room = client.video.v1.rooms.create(
            unique_name=room_name,
            record_participants_on_connect=False
        )
        return room
    
    except Exception as e:
        logger.error(f"Error creating Twilio room: {str(e)}")
        raise

def close_twilio_room(room_sid):
    """
    Closes a Twilio video room
    
    Args:
        room_sid (str): The SID of the room to close
    """
    try:
        client = get_twilio_client()
        room = client.video.v1.rooms(room_sid).update(status='completed')
        return room
    except Exception as e:
        logger.error(f"Error closing Twilio room: {str(e)}")
        raise

def generate_twilio_token(identity, room_name):
    """
    Generates a Twilio access token for a user
    
    Args:
        identity (str): The user's identity (e.g., user ID)
        room_name (str): The room name the token is for
        
    Returns:
        str: The generated token
    """
    try:
        # Validate JWT credentials are set
        if not settings.TWILIO_ACCOUNT_SID or not settings.TWILIO_API_KEY_SID or not settings.TWILIO_API_KEY_SECRET:
            raise ValueError("JWT does not have a signing key configured. Please set TWILIO_ACCOUNT_SID, TWILIO_API_KEY_SID, and TWILIO_API_KEY_SECRET")

        logger.info(f"TWILIO_API_KEY_SID: { settings.TWILIO_API_KEY_SID}")  
        logger.info(f"TWILIO_API_KEY_SECRET: { settings.TWILIO_API_KEY_SECRET}")
        # Create access token with the user identity
        token = AccessToken(
            settings.TWILIO_ACCOUNT_SID,
            settings.TWILIO_API_KEY_SID,
            settings.TWILIO_API_KEY_SECRET,
            identity=identity
        )

        logger.info(f"Token generated: {token}")

        # Create a Video grant and add to the token
        video_grant = VideoGrant(room=room_name)
        token.add_grant(video_grant)
        
        # Return the token as string
        return token.to_jwt()
    except Exception as e:
        logger.error(f"Error generating Twilio token: {str(e)}")
        raise