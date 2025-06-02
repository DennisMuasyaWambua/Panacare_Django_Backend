from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse
from django.contrib.auth import get_user_model
from users.models import Role, Patient
from doctors.models import Doctor
from healthcare.models import Healthcare, Appointment, Consultation
import uuid
from datetime import date, datetime, timedelta
from unittest.mock import patch, MagicMock

User = get_user_model()

class ConsultationTests(TestCase):
    def setUp(self):
        # Create roles
        self.admin_role = Role.objects.create(name='admin')
        self.doctor_role = Role.objects.create(name='doctor')
        self.patient_role = Role.objects.create(name='patient')

        # Create admin user
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='password123'
        )
        self.admin_user.roles.add(self.admin_role)

        # Create doctor user
        self.doctor_user = User.objects.create_user(
            username='doctor',
            email='doctor@example.com',
            password='password123'
        )
        self.doctor_user.roles.add(self.doctor_role)
        
        # Create healthcare facility
        self.healthcare = Healthcare.objects.create(
            name='Test Hospital',
            address='123 Test St',
            phone='1234567890'
        )
        
        # Create doctor
        self.doctor = Doctor.objects.create(
            user=self.doctor_user,
            specialty='General',
            bio='Test bio',
            healthcare=self.healthcare
        )
        
        # Create patient user
        self.patient_user = User.objects.create_user(
            username='patient',
            email='patient@example.com',
            password='password123'
        )
        self.patient_user.roles.add(self.patient_role)
        
        # Create patient
        self.patient = Patient.objects.create(
            user=self.patient_user,
            date_of_birth=date(1990, 1, 1),
            gender='male',
            phone='0987654321',
            address='456 Patient St'
        )
        
        # Create appointment
        self.appointment = Appointment.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            healthcare=self.healthcare,
            appointment_date=date.today() + timedelta(days=1),
            start_time='10:00',
            end_time='10:30',
            status='scheduled',
            appointment_type='initial'
        )
        
        # Create consultation
        self.consultation = Consultation.objects.create(
            appointment=self.appointment,
            status='scheduled'
        )
        
        # Set up API client
        self.client = APIClient()

    @patch('healthcare.twilio_utils.create_twilio_room')
    @patch('healthcare.twilio_utils.generate_twilio_token')
    def test_start_consultation(self, mock_generate_token, mock_create_room):
        """
        Test starting a consultation with Twilio integration
        """
        # Mock Twilio responses
        mock_room = MagicMock()
        mock_room.sid = 'RMXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX'
        mock_create_room.return_value = mock_room
        
        # Mock token generation
        mock_generate_token.return_value = 'mock-twilio-token'
        
        # Authenticate as doctor
        self.client.force_authenticate(user=self.doctor_user)
        
        # Start consultation
        url = reverse('consultation-start-consultation', kwargs={'pk': self.consultation.id})
        response = self.client.post(url)
        
        # Check response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'in-progress')
        self.assertIsNotNone(response.data['twilio_room_name'])
        self.assertIn('token', response.data)
        
        # Verify consultation was updated in DB
        self.consultation.refresh_from_db()
        self.assertEqual(self.consultation.status, 'in-progress')
        self.assertEqual(self.consultation.twilio_room_sid, 'RMXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX')
        self.assertIsNotNone(self.consultation.doctor_token)
        self.assertIsNotNone(self.consultation.patient_token)
        
        # Verify token generation calls
        self.assertEqual(mock_generate_token.call_count, 2)  # One for doctor, one for patient

    @patch('healthcare.twilio_utils.close_twilio_room')
    def test_end_consultation(self, mock_close_room):
        """
        Test ending a consultation with Twilio integration
        """
        # Set up in-progress consultation with Twilio room
        self.consultation.status = 'in-progress'
        self.consultation.start_time = datetime.now()
        self.consultation.twilio_room_sid = 'RMXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX'
        self.consultation.save()
        
        # Authenticate as doctor
        self.client.force_authenticate(user=self.doctor_user)
        
        # End consultation
        url = reverse('consultation-end-consultation', kwargs={'pk': self.consultation.id})
        response = self.client.post(url)
        
        # Check response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'completed')
        
        # Verify consultation was updated in DB
        self.consultation.refresh_from_db()
        self.assertEqual(self.consultation.status, 'completed')
        self.assertIsNotNone(self.consultation.end_time)
        
        # Verify Twilio room was closed
        mock_close_room.assert_called_once_with('RMXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX')

    @patch('healthcare.twilio_utils.generate_twilio_token')
    def test_get_token(self, mock_generate_token):
        """
        Test getting a Twilio token for a consultation
        """
        # Mock token generation
        mock_generate_token.return_value = 'new-mock-token'
        
        # Set up in-progress consultation with Twilio room
        self.consultation.status = 'in-progress'
        self.consultation.twilio_room_name = 'test-room'
        self.consultation.doctor_token = 'doctor-token'
        self.consultation.patient_token = 'patient-token'
        self.consultation.save()
        
        # Authenticate as patient
        self.client.force_authenticate(user=self.patient_user)
        
        # Get token
        url = reverse('consultation-get-token', kwargs={'pk': self.consultation.id})
        response = self.client.get(url)
        
        # Check response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['token'], 'patient-token')
        self.assertEqual(response.data['room_name'], 'test-room')
        
        # Should not have generated a new token since one exists
        mock_generate_token.assert_not_called()
        
        # Test with missing token
        self.consultation.patient_token = ''
        self.consultation.save()
        
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['token'], 'new-mock-token')
        
        # Should have generated a new token
        mock_generate_token.assert_called_once()