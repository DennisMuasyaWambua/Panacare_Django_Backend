try:
    from firebase_admin import messaging
    FIREBASE_AVAILABLE = True
except ImportError:
    FIREBASE_AVAILABLE = False
    
from .models import FCMDevice, NotificationHistory, NotificationPreferences, TopicSubscription
from users.models import User, Role
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


class FCMNotificationService:
    """Service for sending FCM push notifications with history tracking"""
    
    @staticmethod
    def send_to_user(user, title, body, data=None, notification_type='general', sent_by=None, save_to_history=True):
        """
        Send notification to all devices of a specific user.
        
        Args:
            user: Django User instance
            title: Notification title
            body: Notification body
            data: Optional dict of custom data
            notification_type: Type of notification
            sent_by: User who sent the notification
            save_to_history: Whether to save to notification history
        
        Returns:
            dict: Results with success/failure counts
        """
        # Check user notification preferences
        try:
            preferences = user.notification_preferences
            if not preferences.can_send_push_notification(notification_type):
                logger.info(f"User {user.id} has disabled {notification_type} notifications")
                return {'success': 0, 'failure': 0, 'message': 'User has disabled this notification type'}
        except NotificationPreferences.DoesNotExist:
            # Create default preferences for user
            NotificationPreferences.objects.create(user=user)
        
        devices = FCMDevice.objects.filter(user=user, active=True)
        
        if not devices.exists():
            logger.warning(f"No active FCM devices for user {user.id}")
            if save_to_history:
                NotificationHistory.objects.create(
                    user=user,
                    title=title,
                    body=body,
                    notification_type=notification_type,
                    data=data or {},
                    status='failed',
                    sent_by=sent_by
                )
            return {'success': 0, 'failure': 0, 'message': 'No devices found'}
        
        results = {'success': 0, 'failure': 0, 'tokens': []}
        
        if not FIREBASE_AVAILABLE:
            logger.error("Firebase Admin SDK not available")
            if save_to_history:
                NotificationHistory.objects.create(
                    user=user,
                    title=title,
                    body=body,
                    notification_type=notification_type,
                    data=data or {},
                    status='failed',
                    sent_by=sent_by
                )
            return {'success': 0, 'failure': 1, 'message': 'Firebase not available'}
        
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
        
        # Save to notification history
        if save_to_history:
            status = 'sent' if results['success'] > 0 else 'failed'
            NotificationHistory.objects.create(
                user=user,
                title=title,
                body=body,
                notification_type=notification_type,
                data=data or {},
                status=status,
                sent_by=sent_by
            )
        
        return results
    
    @staticmethod
    def send_to_topic(topic, title, body, data=None, notification_type='general', sent_by=None):
        """
        Send notification to a topic (broadcast).
        
        Args:
            topic: Topic name (e.g., 'doctors', 'patients', 'all_users')
            title: Notification title
            body: Notification body
            data: Optional dict of custom data
            notification_type: Type of notification
            sent_by: User who sent the notification
        
        Returns:
            str: Message ID from FCM
        """
        if not FIREBASE_AVAILABLE:
            logger.error("Firebase Admin SDK not available")
            return None
        
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
            
            # Save to history for topic subscribers
            subscribers = TopicSubscription.objects.filter(topic=topic, subscribed=True)
            for subscription in subscribers:
                NotificationHistory.objects.create(
                    user=subscription.user,
                    title=title,
                    body=body,
                    notification_type=notification_type,
                    data=data or {},
                    status='sent',
                    sent_by=sent_by
                )
            
            return response
            
        except Exception as e:
            logger.error(f"Failed to send topic notification to '{topic}': {e}")
            raise
    
    @staticmethod
    def send_to_multiple_users(users, title, body, data=None, notification_type='general', sent_by=None, save_to_history=True):
        """
        Send notification to multiple users (batch).
        
        Args:
            users: List of Django User instances
            title: Notification title
            body: Notification body
            data: Optional dict of custom data
            notification_type: Type of notification
            sent_by: User who sent the notification
            save_to_history: Whether to save to notification history
        
        Returns:
            dict: Aggregated results
        """
        total_results = {'success': 0, 'failure': 0, 'user_results': []}
        
        for user in users:
            results = FCMNotificationService.send_to_user(
                user, title, body, data, notification_type, sent_by, save_to_history
            )
            total_results['success'] += results['success']
            total_results['failure'] += results['failure']
            total_results['user_results'].append({
                'user_id': str(user.id),
                'username': user.username,
                'result': results
            })
        
        return total_results
    
    @staticmethod
    def send_to_role(role_name, title, body, data=None, notification_type='general', sent_by=None, save_to_history=True):
        """
        Send notification to all users with a specific role.
        
        Args:
            role_name: Role name ('doctor', 'patient', 'admin')
            title: Notification title
            body: Notification body
            data: Optional dict of custom data
            notification_type: Type of notification
            sent_by: User who sent the notification
            save_to_history: Whether to save to notification history
        
        Returns:
            dict: Results with success/failure counts
        """
        try:
            role = Role.objects.get(name=role_name)
            users = User.objects.filter(roles=role, is_active=True)
            
            if not users.exists():
                logger.warning(f"No active users found with role '{role_name}'")
                return {'success': 0, 'failure': 0, 'message': f'No users with role {role_name}'}
            
            return FCMNotificationService.send_to_multiple_users(
                users, title, body, data, notification_type, sent_by, save_to_history
            )
            
        except Role.DoesNotExist:
            logger.error(f"Role '{role_name}' does not exist")
            return {'success': 0, 'failure': 0, 'message': f'Role {role_name} does not exist'}
    
    @staticmethod
    def send_to_all_users(title, body, data=None, notification_type='announcement', sent_by=None, save_to_history=True):
        """
        Send notification to all active users.
        
        Args:
            title: Notification title
            body: Notification body
            data: Optional dict of custom data
            notification_type: Type of notification
            sent_by: User who sent the notification
            save_to_history: Whether to save to notification history
        
        Returns:
            dict: Results with success/failure counts
        """
        users = User.objects.filter(is_active=True)
        
        if not users.exists():
            logger.warning("No active users found")
            return {'success': 0, 'failure': 0, 'message': 'No active users'}
        
        return FCMNotificationService.send_to_multiple_users(
            users, title, body, data, notification_type, sent_by, save_to_history
        )