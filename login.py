import requests
import json

# Login to get a valid token
login_url = "http://localhost:8000/api/users/login/"
login_data = {
    "email": "muasyathegreat4@gmail.com",  # Replace with a valid admin email
    "password": "password123"  # Replace with correct password
}

try:
    print("Attempting to login...")
    response = requests.post(login_url, json=login_data)
    print(f"Login status code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        token = data.get('tokens', {}).get('access')
        print(f"Login successful!\nAccess token: {token}")
        
        with open('token.txt', 'w') as f:
            f.write(token)
        
        print("Token saved to token.txt")
    else:
        print(f"Login failed: {response.text}")
        
except Exception as e:
    print(f"Error during login: {str(e)}")
