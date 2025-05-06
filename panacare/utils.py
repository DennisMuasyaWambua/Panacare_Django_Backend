import logging
from rest_framework.views import exception_handler
from rest_framework.exceptions import AuthenticationFailed, NotAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.http import JsonResponse

logger = logging.getLogger(__name__)

def custom_exception_handler(exc, context):
    """
    Custom exception handler that provides more details for auth errors
    """
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)
    
    # If it's an authentication error, add more details
    if isinstance(exc, (AuthenticationFailed, NotAuthenticated)):
        if response is None:
            response = Response(
                {"error": "Authentication error occurred", "detail": str(exc)},
                status=status.HTTP_401_UNAUTHORIZED
            )
        else:
            response.data = {
                "error": "Unauthorized. Please login again.",
                "detail": str(exc)
            }
        
        # Log the request details for debugging
        request = context.get('request')
        if request:
            logger.error(f"Authentication error: {exc}")
            logger.error(f"Request headers: {request.headers}")
            auth_header = request.headers.get('Authorization')
            if auth_header:
                logger.error(f"Auth header present: {auth_header[:20]}...")
            else:
                logger.error("No Authorization header in request")
    
    return response

class DebugAuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        # Log auth headers for debugging
        if 'Authorization' in request.headers:
            logger.info(f"Auth header: {request.headers['Authorization'][:20]}...")
        elif 'HTTP_AUTHORIZATION' in request.META:
            logger.info(f"META Auth header: {request.META['HTTP_AUTHORIZATION'][:20]}...")
        else:
            logger.info("No auth header in request")
            
        response = self.get_response(request)
        return response


def verify_token_view(request):
    """A test view to verify JWT tokens from the frontend"""
    auth_header = request.headers.get('Authorization', '')
    
    if not auth_header:
        return JsonResponse({
            "status": "error",
            "message": "No Authorization header found",
            "headers": dict(request.headers)
        }, status=400)
    
    if not auth_header.startswith('Bearer '):
        return JsonResponse({
            "status": "error",
            "message": "Invalid authorization format. Must be Bearer <token>",
            "auth_header": auth_header
        }, status=400)
    
    token = auth_header.split(' ')[1]
    
    try:
        # Try to validate the token
        jwt_auth = JWTAuthentication()
        validated_token = jwt_auth.get_validated_token(token)
        user = jwt_auth.get_user(validated_token)
        
        return JsonResponse({
            "status": "success",
            "message": "Token is valid",
            "user_id": str(user.id),
            "username": user.username,
            "email": user.email,
            "roles": [role.name for role in user.roles.all()]
        })
    except Exception as e:
        return JsonResponse({
            "status": "error",
            "message": "Token validation failed",
            "error": str(e),
            "token_preview": token[:10] + "..." if token else "None"
        }, status=401)