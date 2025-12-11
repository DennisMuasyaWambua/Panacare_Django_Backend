from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

@csrf_exempt
def test_cors(request):
    """
    A simple view to test CORS headers
    """
    # Log the request method and headers
    print(f"Request method: {request.method}")
    print(f"Request headers: {request.headers}")
    
    # Handle preflight OPTIONS request
    if request.method == 'OPTIONS':
        response = JsonResponse({'message': 'CORS preflight successful'})
        response["Access-Control-Allow-Origin"] = "*"
        response["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        response["Access-Control-Allow-Headers"] = "Authorization, Content-Type, X-Requested-With"
        return response
        
    # Return a test response with request details
    response_data = {
        'message': 'CORS test successful',
        'method': request.method,
        'headers': dict(request.headers),
        'body': json.loads(request.body) if request.body else None,
        'metadata': {
            'path': request.path,
            'GET': dict(request.GET),
            'url': request.build_absolute_uri(),
        },
    }
    
    # Add CORS headers to the response
    response = JsonResponse(response_data)
    response["Access-Control-Allow-Origin"] = "*"
    response["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response["Access-Control-Allow-Headers"] = "Authorization, Content-Type, X-Requested-With"
    
    return response