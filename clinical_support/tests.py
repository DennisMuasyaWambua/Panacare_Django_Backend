from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from users.models import User, Patient, Role
import uuid

class ClinicalDecisionSupportTests(TestCase):
    def setUp(self):
        # Create a test user and patient
        self.client = APIClient()
        self.patient_role = Role.objects.create(name='patient')
        self.test_user = User.objects.create_user(
            email='testpatient@example.com',
            password='testpassword123',
            first_name='Test',
            last_name='Patient',
            is_active=True
        )
        self.test_user.roles.add(self.patient_role)
        self.test_patient = Patient.objects.create(
            user=self.test_user,
            date_of_birth='1990-01-01',
            phone_number='1234567890'
        )
        self.client.force_authenticate(user=self.test_user)
        
        # Test data for clinical decision
        self.valid_payload = {
            "age": 45,
            "gender": "male",
            "weight": 80,
            "height": 175,
            "high_blood_pressure": True,
            "diabetes": False,
            "on_medication": True,
            "headache": True,
            "dizziness": False,
            "blurred_vision": False,
            "palpitations": True,
            "fatigue": True,
            "chest_pain": False,
            "frequent_thirst": False,
            "loss_of_appetite": False,
            "frequent_urination": False,
            "other_symptoms": "",
            "no_symptoms": False,
            "systolic_pressure": 145,
            "diastolic_pressure": 95,
            "blood_sugar": 95,
            "heart_rate": 85,
            "sleep_hours": 6,
            "exercise_minutes": 15,
            "eats_unhealthy": True,
            "smokes": False,
            "consumes_alcohol": True,
            "skips_medication": True
        }
    
    def test_clinical_decision_endpoint(self):
        """Test the clinical decision support endpoint"""
        response = self.client.post(
            reverse('clinical-decision'),
            self.valid_payload,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('analysis', response.data)
        self.assertIn('recommendations', response.data)
        self.assertIn('risk_level', response.data)
        self.assertIn('record_id', response.data)
        
        # Verify risk level calculation for this test case
        self.assertEqual(response.data['risk_level'], 'high')
    
    def test_clinical_history_endpoint(self):
        """Test retrieving clinical history"""
        # First create a record
        self.client.post(
            reverse('clinical-decision'),
            self.valid_payload,
            format='json'
        )
        
        # Then retrieve history
        response = self.client.get(reverse('clinical-history'))
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data) > 0)
        self.assertEqual(response.data[0]['patient'], str(self.test_patient.id))
