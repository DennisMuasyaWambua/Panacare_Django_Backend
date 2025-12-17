from firebase_admin import messaging
from .models import FCMDevice
import logging

logger = logging.getLogger(__name__)


class FCMNotificationService:
    """Service for sending FCM push notifications"""
    
    @staticmethod
    def send_to_user(user, title, body, data=None):
        """
        Send notification to all devices of a specific user.
        
        Args:
            user: Django User instance
            title: Notification title
            body: Notification body
            data: Optional dict of custom data
        
        Returns:
            dict: Results with success/failure counts
        """
        devices = FCMDevice.objects.filter(user=user, active=True)
        
        if not devices.exists():
            logger.warning(f"No active FCM devices for user {user.id}")
            return {'success': 0, 'failure': 0, 'message': 'No devices found'}
        
        results = {'success': 0, 'failure': 0, 'tokens': []}
        
        for device in devices:
            try:
                message = messaging.Message(
                    notification=messaging.Notification(
                        title=title,
                        body=body,
                    ),
                    data=data or {},
                    token=device.token,
                )
                
                response = messaging.send(message)
                results['success'] += 1
                results['tokens'].append(device.token[:20] + '...')
                logger.info(f"Notification sent to {user.id}: {response}")
                
            except messaging.UnregisteredError:
                # Token is invalid, deactivate device
                device.active = False
                device.save()
                results['failure'] += 1
                logger.warning(f"Invalid token for user {user.id}, deactivated")
                
            except Exception as e:
                results['failure'] += 1
                logger.error(f"Failed to send to user {user.id}: {e}")
        
        return results
    
    @staticmethod
    def send_to_topic(topic, title, body, data=None):
        """
        Send notification to a topic (broadcast).
        
        Args:
            topic: Topic name (e.g., 'doctors', 'patients', 'all_users')
            title: Notification title
            body: Notification body
            data: Optional dict of custom data
        
        Returns:
            str: Message ID from FCM
        """
        try:
            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=body,
                ),
                data=data or {},
                topic=topic,
            )
            
            response = messaging.send(message)
            logger.info(f"Topic notification sent to '{topic}': {response}")
            return response
            
        except Exception as e:
            logger.error(f"Failed to send topic notification to '{topic}': {e}")
            raise
    
    @staticmethod
    def send_to_multiple_users(users, title, body, data=None):
        """
        Send notification to multiple users (batch).
        
        Args:
            users: List of Django User instances
            title: Notification title
            body: Notification body
            data: Optional dict of custom data
        
        Returns:
            dict: Aggregated results
        """
        total_results = {'success': 0, 'failure': 0}
        
        for user in users:
            results = FCMNotificationService.send_to_user(user, title, body, data)
            total_results['success'] += results['success']
            total_results['failure'] += results['failure']
        
        return total_results