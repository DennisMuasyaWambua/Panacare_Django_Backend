from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import FCMDevice


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
@authentication_classes([TokenAuthentication])
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
