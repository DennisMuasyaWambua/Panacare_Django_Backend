from rest_framework.views import exception_handler
from rest_framework.exceptions import AuthenticationFailed, NotAuthenticated
from rest_framework.response import Response
from rest_framework import status

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
    
    return response