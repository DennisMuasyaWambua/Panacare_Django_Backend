from users.models import User, Patient
from doctors.models import Doctor
import uuid
from rest_framework_simplejwt.tokens import RefreshToken
import json

print("Checking if tables have been correctly created and columns exist:")

# Check Patient model table columns
try:
    patient_columns = [f.name for f in Patient._meta.get_fields()]
    print(f"Patient model columns: {patient_columns}")
except Exception as e:
    print(f"Error checking Patient model: {str(e)}")

# Check Doctor model table columns
try:
    doctor_columns = [f.name for f in Doctor._meta.get_fields()]
    print(f"Doctor model columns: {doctor_columns}")
except Exception as e:
    print(f"Error checking Doctor model: {str(e)}")

# Create a test admin user for login
try:
    admin_user = User.objects.create_superuser(
        username="admintest",
        email="admintest@example.com",
        password="AdminTest123!",
        is_verified=True
    )
    admin_user.save()
    print(f"Created admin user: {admin_user.email}")
    
    # Generate JWT token for the admin user
    refresh = RefreshToken.for_user(admin_user)
    token = str(refresh.access_token)
    print(f"Admin token: {token}")
    
    # Save token to a file for testing
    with open('admin_token.txt', 'w') as f:
        f.write(token)
    print("Token saved to admin_token.txt")
    
except Exception as e:
    print(f"Error creating admin user: {str(e)}")

# Get list of patient IDs
try:
    patients = list(Patient.objects.all()[:5])
    print(f"Found {len(patients)} patients:")
    for p in patients:
        print(f"- {p.id}")
except Exception as e:
    print(f"Error listing patients: {str(e)}")

# Get list of doctor IDs
try:
    doctors = list(Doctor.objects.all()[:5])
    print(f"Found {len(doctors)} doctors:")
    for d in doctors:
        print(f"- {d.id}")
except Exception as e:
    print(f"Error listing doctors: {str(e)}")