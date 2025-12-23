from rest_framework.decorators import api_view, authentication_classes, permission_classes, action
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status, viewsets, permissions
from rest_framework_simplejwt.authentication import JWTAuthentication
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.utils import timezone
from django.shortcuts import get_object_or_404

from .models import (
    FCMDevice, NotificationHistory, NotificationPreferences, TopicSubscription
)
from .serializers import (
    FCMDeviceSerializer, NotificationHistorySerializer, NotificationPreferencesSerializer,
    TopicSubscriptionSerializer, SendNotificationSerializer, BulkNotificationResultSerializer
)
from .services import FCMNotificationService
from users.models import User, Role
from doctors.views import IsAdminUser


@swagger_auto_schema(
    method='post',
    operation_description="Register or update FCM token for authenticated user. Mobile app calls this after successful login.",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['token', 'platform'],
        properties={
            'token': openapi.Schema(type=openapi.TYPE_STRING, description="FCM device token"),
            'platform': openapi.Schema(type=openapi.TYPE_STRING, enum=['android', 'ios'], description="Device platform")
        }
    ),
    responses={
        200: openapi.Response("Token updated successfully", openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'status': openapi.Schema(type=openapi.TYPE_STRING, example="success"),
                'message': openapi.Schema(type=openapi.TYPE_STRING, example="FCM token registered successfully"),
                'created': openapi.Schema(type=openapi.TYPE_BOOLEAN, example=False)
            }
        )),
        201: openapi.Response("Token created successfully", openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'status': openapi.Schema(type=openapi.TYPE_STRING, example="success"),
                'message': openapi.Schema(type=openapi.TYPE_STRING, example="FCM token registered successfully"),
                'created': openapi.Schema(type=openapi.TYPE_BOOLEAN, example=True)
            }
        )),
        400: openapi.Response("Bad Request", openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'error': openapi.Schema(type=openapi.TYPE_STRING, example="Token is required")
            }
        )),
        401: openapi.Response("Unauthorized", openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'error': openapi.Schema(type=openapi.TYPE_STRING, example="Authentication required")
            }
        ))
    },
    tags=['FCM Notifications']
)
@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def register_fcm_token(request):
    """
    Register or update FCM token for authenticated user.
    Mobile app calls this after successful login.
    """
    token = request.data.get('token')
    platform = request.data.get('platform')
    
    # Validation
    if not token:
        return Response(
            {'error': 'Token is required'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if platform not in ['android', 'ios']:
        return Response(
            {'error': 'Platform must be android or ios'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Update or create device token
    device, created = FCMDevice.objects.update_or_create(
        user=request.user,
        token=token,
        defaults={
            'platform': platform,
            'active': True
        }
    )
    
    return Response({
        'status': 'success',
        'message': 'FCM token registered successfully',
        'created': created
    }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


class NotificationViewSet(viewsets.ViewSet):
    """
    ViewSet for notification management
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    
    @swagger_auto_schema(
        operation_description="Send notification to users (Admin only)",
        request_body=SendNotificationSerializer,
        responses={
            200: BulkNotificationResultSerializer,
            400: openapi.Response("Bad Request"),
            403: openapi.Response("Forbidden - Admin access required"),
        },
        tags=['Admin Notifications']
    )
    @action(detail=False, methods=['post'], permission_classes=[IsAdminUser])
    def send(self, request):
        """
        Send notification to users based on different targeting options.
        Supports sending to specific users, roles, topics, or all users.
        """
        serializer = SendNotificationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        title = data['title']
        body = data['body']
        notification_type = data.get('notification_type', 'general')
        custom_data = data.get('data', {})
        recipient_type = data['recipient_type']
        save_to_history = data.get('save_to_history', True)
        
        try:
            if recipient_type == 'user':
                # Send to specific user
                user = get_object_or_404(User, id=data['user_id'])
                results = FCMNotificationService.send_to_user(
                    user, title, body, custom_data, notification_type, request.user, save_to_history
                )
                total_recipients = 1
                
            elif recipient_type == 'users':
                # Send to multiple users
                users = User.objects.filter(id__in=data['user_ids'])
                results = FCMNotificationService.send_to_multiple_users(
                    users, title, body, custom_data, notification_type, request.user, save_to_history
                )
                total_recipients = users.count()
                
            elif recipient_type == 'role':
                # Send to all users with specific role
                results = FCMNotificationService.send_to_role(
                    data['role'], title, body, custom_data, notification_type, request.user, save_to_history
                )
                role = Role.objects.get(name=data['role'])
                total_recipients = User.objects.filter(roles=role, is_active=True).count()
                
            elif recipient_type == 'topic':
                # Send to topic subscribers
                results = FCMNotificationService.send_to_topic(
                    data['topic'], title, body, custom_data, notification_type, request.user
                )
                total_recipients = TopicSubscription.objects.filter(
                    topic=data['topic'], subscribed=True
                ).count()
                
            elif recipient_type == 'all':
                # Send to all active users
                results = FCMNotificationService.send_to_all_users(
                    title, body, custom_data, notification_type, request.user, save_to_history
                )
                total_recipients = User.objects.filter(is_active=True).count()
            
            # Prepare response
            notifications_sent = results.get('success', 0)
            notifications_failed = results.get('failure', 0)
            success_rate = (notifications_sent / max(total_recipients, 1)) * 100
            
            response_data = {
                'total_recipients': total_recipients,
                'notifications_sent': notifications_sent,
                'notifications_failed': notifications_failed,
                'success_rate': round(success_rate, 2),
                'details': results
            }
            
            return Response({
                'status': 'success',
                'message': 'Notification sent successfully',
                'data': response_data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'error': f'Failed to send notification: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @swagger_auto_schema(
        operation_description="Send notification to all doctors (Admin only)",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['title', 'body'],
            properties={
                'title': openapi.Schema(type=openapi.TYPE_STRING),
                'body': openapi.Schema(type=openapi.TYPE_STRING),
                'notification_type': openapi.Schema(type=openapi.TYPE_STRING, default='general'),
                'data': openapi.Schema(type=openapi.TYPE_OBJECT, default={})
            }
        ),
        responses={200: BulkNotificationResultSerializer},
        tags=['Admin Notifications']
    )
    @action(detail=False, methods=['post'], permission_classes=[IsAdminUser], url_path='send/doctors')
    def send_to_doctors(self, request):
        """Send notification to all doctors"""
        title = request.data.get('title')
        body = request.data.get('body')
        notification_type = request.data.get('notification_type', 'general')
        data = request.data.get('data', {})
        
        if not title or not body:
            return Response({
                'error': 'Title and body are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        results = FCMNotificationService.send_to_role(
            'doctor', title, body, data, notification_type, request.user
        )
        
        doctor_role = Role.objects.get(name='doctor')
        total_recipients = User.objects.filter(roles=doctor_role, is_active=True).count()
        
        return Response({
            'status': 'success',
            'message': 'Notification sent to all doctors',
            'data': {
                'total_recipients': total_recipients,
                'notifications_sent': results.get('success', 0),
                'notifications_failed': results.get('failure', 0),
                'details': results
            }
        })
    
    @swagger_auto_schema(
        operation_description="Send notification to all patients (Admin only)",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['title', 'body'],
            properties={
                'title': openapi.Schema(type=openapi.TYPE_STRING),
                'body': openapi.Schema(type=openapi.TYPE_STRING),
                'notification_type': openapi.Schema(type=openapi.TYPE_STRING, default='general'),
                'data': openapi.Schema(type=openapi.TYPE_OBJECT, default={})
            }
        ),
        responses={200: BulkNotificationResultSerializer},
        tags=['Admin Notifications']
    )
    @action(detail=False, methods=['post'], permission_classes=[IsAdminUser], url_path='send/patients')
    def send_to_patients(self, request):
        """Send notification to all patients"""
        title = request.data.get('title')
        body = request.data.get('body')
        notification_type = request.data.get('notification_type', 'general')
        data = request.data.get('data', {})
        
        if not title or not body:
            return Response({
                'error': 'Title and body are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        results = FCMNotificationService.send_to_role(
            'patient', title, body, data, notification_type, request.user
        )
        
        patient_role = Role.objects.get(name='patient')
        total_recipients = User.objects.filter(roles=patient_role, is_active=True).count()
        
        return Response({
            'status': 'success',
            'message': 'Notification sent to all patients',
            'data': {
                'total_recipients': total_recipients,
                'notifications_sent': results.get('success', 0),
                'notifications_failed': results.get('failure', 0),
                'details': results
            }
        })
    
    @swagger_auto_schema(
        operation_description="Get user's notification history",
        responses={200: NotificationHistorySerializer(many=True)},
        tags=['User Notifications']
    )
    @action(detail=False, methods=['get'])
    def history(self, request):
        """Get authenticated user's notification history"""
        notifications = NotificationHistory.objects.filter(user=request.user)
        
        # Filter by type if specified
        notification_type = request.query_params.get('type')
        if notification_type:
            notifications = notifications.filter(notification_type=notification_type)
        
        # Filter by read status if specified
        is_read = request.query_params.get('is_read')
        if is_read is not None:
            notifications = notifications.filter(is_read=is_read.lower() == 'true')
        
        serializer = NotificationHistorySerializer(notifications, many=True)
        return Response({
            'status': 'success',
            'data': serializer.data,
            'count': notifications.count()
        })
    
    @swagger_auto_schema(
        operation_description="Mark notification as read",
        responses={200: openapi.Response("Notification marked as read")},
        tags=['User Notifications']
    )
    @action(detail=True, methods=['patch'])
    def mark_read(self, request, pk=None):
        """Mark a specific notification as read"""
        try:
            notification = NotificationHistory.objects.get(
                id=pk, user=request.user
            )
            notification.mark_as_read()
            
            return Response({
                'status': 'success',
                'message': 'Notification marked as read'
            })
        except NotificationHistory.DoesNotExist:
            return Response({
                'error': 'Notification not found'
            }, status=status.HTTP_404_NOT_FOUND)
    
    @swagger_auto_schema(
        operation_description="Mark all notifications as read",
        responses={200: openapi.Response("All notifications marked as read")},
        tags=['User Notifications']
    )
    @action(detail=False, methods=['post'], url_path='mark-all-read')
    def mark_all_read(self, request):
        """Mark all user notifications as read"""
        updated_count = NotificationHistory.objects.filter(
            user=request.user,
            is_read=False
        ).update(
            is_read=True,
            read_at=timezone.now()
        )
        
        return Response({
            'status': 'success',
            'message': f'Marked {updated_count} notifications as read'
        })
    
    @swagger_auto_schema(
        operation_description="Get user's notification preferences",
        responses={200: NotificationPreferencesSerializer},
        tags=['User Notifications']
    )
    @action(detail=False, methods=['get'])
    def preferences(self, request):
        """Get user's notification preferences"""
        preferences, created = NotificationPreferences.objects.get_or_create(
            user=request.user
        )
        serializer = NotificationPreferencesSerializer(preferences)
        return Response({
            'status': 'success',
            'data': serializer.data
        })
    
    @swagger_auto_schema(
        operation_description="Update user's notification preferences",
        request_body=NotificationPreferencesSerializer,
        responses={200: NotificationPreferencesSerializer},
        tags=['User Notifications']
    )
    @action(detail=False, methods=['put'])
    def update_preferences(self, request):
        """Update user's notification preferences"""
        preferences, created = NotificationPreferences.objects.get_or_create(
            user=request.user
        )
        
        serializer = NotificationPreferencesSerializer(
            preferences, data=request.data, partial=True
        )
        
        if serializer.is_valid():
            serializer.save()
            return Response({
                'status': 'success',
                'message': 'Preferences updated successfully',
                'data': serializer.data
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TopicSubscriptionViewSet(viewsets.ViewSet):
    """
    ViewSet for managing topic subscriptions
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    
    @swagger_auto_schema(
        operation_description="Get user's topic subscriptions",
        responses={200: TopicSubscriptionSerializer(many=True)},
        tags=['Topic Subscriptions']
    )
    def list(self, request):
        """Get user's topic subscriptions"""
        subscriptions = TopicSubscription.objects.filter(user=request.user)
        serializer = TopicSubscriptionSerializer(subscriptions, many=True)
        return Response({
            'status': 'success',
            'data': serializer.data
        })
    
    @swagger_auto_schema(
        operation_description="Subscribe to a topic",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['topic'],
            properties={
                'topic': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    enum=[choice[0] for choice in TopicSubscription.TOPIC_CHOICES]
                )
            }
        ),
        responses={200: TopicSubscriptionSerializer},
        tags=['Topic Subscriptions']
    )
    @action(detail=False, methods=['post'])
    def subscribe(self, request):
        """Subscribe to a topic"""
        topic = request.data.get('topic')
        
        if not topic:
            return Response({
                'error': 'Topic is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        subscription, created = TopicSubscription.objects.update_or_create(
            user=request.user,
            topic=topic,
            defaults={'subscribed': True}
        )
        
        serializer = TopicSubscriptionSerializer(subscription)
        message = 'Subscribed to topic' if created else 'Updated subscription'
        
        return Response({
            'status': 'success',
            'message': message,
            'data': serializer.data
        })
    
    @swagger_auto_schema(
        operation_description="Unsubscribe from a topic",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['topic'],
            properties={
                'topic': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    enum=[choice[0] for choice in TopicSubscription.TOPIC_CHOICES]
                )
            }
        ),
        responses={200: openapi.Response("Unsubscribed from topic")},
        tags=['Topic Subscriptions']
    )
    @action(detail=False, methods=['post'])
    def unsubscribe(self, request):
        """Unsubscribe from a topic"""
        topic = request.data.get('topic')
        
        if not topic:
            return Response({
                'error': 'Topic is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        subscription, created = TopicSubscription.objects.update_or_create(
            user=request.user,
            topic=topic,
            defaults={'subscribed': False}
        )
        
        return Response({
            'status': 'success',
            'message': 'Unsubscribed from topic'
        })
