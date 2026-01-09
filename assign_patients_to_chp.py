#!/usr/bin/env python
"""
Script to assign patients to a specific CHP
"""
import os
import sys
import django
import requests
import json

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'panacare.settings')
sys.path.append('/home/dennis/Desktop/projects/Panacare_healthcare_Backend_Django')
django.setup()

from users.models import User, Patient, CommunityHealthProvider

def assign_patients_to_chp():
    """Assign patients to the specified CHP"""
    
    # CHP details
    chp_email = "54bhyh6kgi@mrotzis.com"
    chp_id = "29282674-e223-4b17-89ec-4622e70022a1"
    
    # Patient IDs to assign
    patient_ids = [
        "3c653da8-2da4-4d8c-bdcf-3bc1d7d3b3da",  # John Doe
        "918a434e-5692-42ae-8d76-a396e5801607",  # Mustafa Alsayed
        "f2451e7b-db13-4790-9d70-848df1b78bdb",  # ogun shogun
        "409d45ca-3c68-4f34-bfeb-bf06cec33350",  # Fris Bee
        "05c12da2-1010-4af7-835b-2603efa110bf",  # Patient Zero
    ]
    
    print(f"Assigning {len(patient_ids)} patients to CHP: {chp_email}")
    print(f"CHP ID: {chp_id}")
    print("-" * 50)
    
    try:
        # Get CHP object
        chp = CommunityHealthProvider.objects.get(id=chp_id)
        print(f"✓ Found CHP: {chp.user.get_full_name()} ({chp.user.email})")
        
        assigned_count = 0
        failed_count = 0
        
        for patient_id in patient_ids:
            try:
                # Get patient
                patient = Patient.objects.get(id=patient_id)
                
                # Track previous assignment
                previous_chp = patient.created_by_chp
                previous_chp_name = previous_chp.user.get_full_name() if previous_chp else "None"
                
                # Assign CHP to patient
                patient.created_by_chp = chp
                patient.save()
                
                print(f"✓ Assigned {patient.user.get_full_name()} (ID: {patient_id})")
                print(f"  Email: {patient.user.email}")
                print(f"  Previous CHP: {previous_chp_name}")
                print(f"  New CHP: {chp.user.get_full_name()}")
                print()
                
                assigned_count += 1
                
            except Patient.DoesNotExist:
                print(f"✗ Patient not found: {patient_id}")
                failed_count += 1
            except Exception as e:
                print(f"✗ Error assigning patient {patient_id}: {e}")
                failed_count += 1
        
        print("=" * 50)
        print(f"Assignment Summary:")
        print(f"✓ Successfully assigned: {assigned_count} patients")
        print(f"✗ Failed assignments: {failed_count} patients")
        print(f"📊 CHP now has: {chp.created_patients.count()} total patients")
        
        # List all patients assigned to this CHP
        print("\nAll patients now assigned to this CHP:")
        for patient in chp.created_patients.all():
            print(f"- {patient.user.get_full_name()} ({patient.user.email})")
            
    except CommunityHealthProvider.DoesNotExist:
        print(f"✗ CHP not found with ID: {chp_id}")
    except Exception as e:
        print(f"✗ Unexpected error: {e}")

if __name__ == '__main__':
    assign_patients_to_chp()