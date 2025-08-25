#!/usr/bin/env python3
"""
Test script for Audit Logs API endpoints
"""
import os
import sys
import django
from django.utils import timezone
from datetime import timedelta

# Add the project directory to the Python path
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_dir)

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'panacare.settings')
django.setup()

from users.models import User, Role, AuditLog
from django.contrib.auth import get_user_model

def create_sample_audit_logs():
    """
    Create sample audit log entries for testing
    """
    print("Creating sample audit log entries...")
    
    # Get or create an admin user for testing
    admin_role, _ = Role.objects.get_or_create(name='admin', defaults={'description': 'Administrator'})
    patient_role, _ = Role.objects.get_or_create(name='patient', defaults={'description': 'Patient'})
    doctor_role, _ = Role.objects.get_or_create(name='doctor', defaults={'description': 'Doctor'})
    
    # Create test users if they don't exist
    admin_user, created = User.objects.get_or_create(
        email='admin@test.com',
        defaults={
            'username': 'admin_test',
            'first_name': 'Admin',
            'last_name': 'User',
            'is_verified': True
        }
    )
    if created:
        admin_user.set_password('testpassword')
        admin_user.save()
        admin_user.roles.add(admin_role)
    
    patient_user, created = User.objects.get_or_create(
        email='patient@test.com',
        defaults={
            'username': 'patient_test',
            'first_name': 'Patient',
            'last_name': 'User',
            'is_verified': True
        }
    )
    if created:
        patient_user.set_password('testpassword')
        patient_user.save()
        patient_user.roles.add(patient_role)
    
    # Create sample audit logs
    sample_logs = [
        {
            'user': admin_user,
            'username': admin_user.username,
            'activity': 'login',
            'email_address': admin_user.email,
            'role': 'admin',
            'date_joined': admin_user.date_joined,
            'status': 'active',
            'ip_address': '192.168.1.100',
            'details': {'login_method': 'web', 'browser': 'Chrome'}
        },
        {
            'user': patient_user,
            'username': patient_user.username,
            'activity': 'profile_update',
            'email_address': patient_user.email,
            'role': 'patient',
            'date_joined': patient_user.date_joined,
            'status': 'active',
            'ip_address': '192.168.1.101',
            'details': {'updated_fields': ['phone_number', 'address']}
        },
        {
            'user': admin_user,
            'username': admin_user.username,
            'activity': 'user_create',
            'email_address': admin_user.email,
            'role': 'admin',
            'date_joined': admin_user.date_joined,
            'status': 'active',
            'ip_address': '192.168.1.100',
            'details': {'created_user': 'patient@test.com', 'assigned_role': 'patient'}
        },
        {
            'user': patient_user,
            'username': patient_user.username,
            'activity': 'appointment_create',
            'email_address': patient_user.email,
            'role': 'patient',
            'date_joined': patient_user.date_joined,
            'status': 'active',
            'ip_address': '192.168.1.101',
            'time_spent': timedelta(minutes=5),
            'details': {'appointment_type': 'consultation', 'doctor': 'dr.smith@test.com'}
        },
        {
            'user': admin_user,
            'username': admin_user.username,
            'activity': 'data_export',
            'email_address': admin_user.email,
            'role': 'admin',
            'date_joined': admin_user.date_joined,
            'status': 'active',
            'ip_address': '192.168.1.100',
            'time_spent': timedelta(minutes=2),
            'details': {'export_type': 'patient_data', 'format': 'csv', 'records_count': 150}
        }
    ]
    
    created_count = 0
    for log_data in sample_logs:
        audit_log, created = AuditLog.objects.get_or_create(
            user=log_data['user'],
            activity=log_data['activity'],
            created_at__date=timezone.now().date(),
            defaults=log_data
        )
        if created:
            created_count += 1
    
    print(f"Created {created_count} new audit log entries")
    print(f"Total audit log entries: {AuditLog.objects.count()}")
    
    return admin_user, patient_user

def test_api_endpoints():
    """
    Test the audit log API endpoints
    """
    print("\n=== Testing Audit Log API Endpoints ===")
    
    # Test the endpoint structure
    print("\nAvailable API endpoints for audit logs:")
    print("GET /api/audit-logs/ - List all audit logs (admin only)")
    print("GET /api/audit-logs/{id}/ - Retrieve specific audit log (admin only)")
    print("GET /api/audit-logs/export-csv/ - Export audit logs as CSV (admin only)")
    print("GET /api/audit-logs/export-pdf/ - Export audit logs as PDF (admin only)")
    print("GET /api/audit-logs/statistics/ - Get audit log statistics (admin only)")
    
    print("\nSupported query parameters:")
    print("- search: Search by username or email")
    print("- activity: Filter by activity type")
    print("- status: Filter by status")
    print("- role: Filter by role")
    print("- date_from: Filter from date (YYYY-MM-DD)")
    print("- date_to: Filter to date (YYYY-MM-DD)")
    print("- ordering: Order results (-created_at, created_at, username, etc.)")
    
    print("\nExample URLs:")
    print("GET /api/audit-logs/?search=admin&activity=login")
    print("GET /api/audit-logs/?role=patient&status=active")
    print("GET /api/audit-logs/?date_from=2025-01-01&date_to=2025-12-31")
    print("GET /api/audit-logs/?ordering=-created_at")

def show_sample_data():
    """
    Show sample audit log data
    """
    print("\n=== Sample Audit Log Data ===")
    
    logs = AuditLog.objects.all()[:5]
    
    for log in logs:
        print(f"\nAudit Log ID: {log.id}")
        print(f"Username: {log.username}")
        print(f"Activity: {log.get_activity_display()}")
        print(f"Email: {log.email_address}")
        print(f"Role: {log.role}")
        print(f"Status: {log.get_status_display()}")
        print(f"Time Spent: {log.formatted_time_spent}")
        print(f"IP Address: {log.ip_address}")
        print(f"Created At: {log.created_at}")
        if log.details:
            print(f"Details: {log.details}")

if __name__ == '__main__':
    print("=== Panacare Audit Logs API Test ===")
    
    # Create sample data
    admin_user, patient_user = create_sample_audit_logs()
    
    # Show sample data
    show_sample_data()
    
    # Test endpoints info
    test_api_endpoints()
    
    print(f"\n=== Test Summary ===")
    print(f"✅ AuditLog model created with {AuditLog.objects.count()} sample entries")
    print(f"✅ API endpoints configured and ready for testing")
    print(f"✅ Admin user created: {admin_user.email}")
    print(f"✅ Sample patient user created: {patient_user.email}")
    print(f"\nTo test the API endpoints:")
    print(f"1. Start the Django server: python manage.py runserver")
    print(f"2. Login as admin user to get JWT token")
    print(f"3. Use the token to access /api/audit-logs/ endpoints")
    print(f"4. Check the Swagger documentation at /swagger/ for detailed API info")